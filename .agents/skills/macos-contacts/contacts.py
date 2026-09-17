#!/usr/bin/env python3
"""Minimal native macOS Contacts CLI over pinned SSH for HADES."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable

HOST_PATTERN = re.compile(
    r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+ts\.net\Z"
)
USER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}\Z")
CONTACT_ID_PATTERN = re.compile(r"[A-Za-z0-9:._-]{1,255}\Z")
PHONE_DIGITS_PATTERN = re.compile(r"\d{10}|1\d{10}\Z")

CONFIG_FILE = Path.home() / ".config" / "hades" / "apple" / "apple-config.json"


class ContactsError(RuntimeError):
    pass


def require_value(value: str, description: str) -> str:
    if not value or len(value) > 255 or any(ord(character) < 32 for character in value):
        raise ContactsError(f"{description} must be non-empty plain text")
    return value


def applescript_literal(value: str) -> str:
    require_value(value, "contact value")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def normalize_phone(value: str) -> str:
    raw = str(value or "").strip()
    digits = "".join(character for character in raw if character.isdigit())
    if raw.startswith("+") and not raw.startswith("+1"):
        raise ContactsError("phone must be a North American number")
    if len(digits) == 10:
        digits = "1" + digits
    if not PHONE_DIGITS_PATTERN.fullmatch(digits) or len(digits) != 11:
        raise ContactsError("phone must be a North American 10-digit or +1 number")
    return "+" + digits


def resolve_connection(environment: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environment is None else environment
    host = env.get("MACOS_CONTACTS_HOST", "").strip()
    user = env.get("MACOS_CONTACTS_USER", "").strip()
    known_hosts = env.get("MACOS_CONTACTS_KNOWN_HOSTS", "").strip()
    identity = env.get("MACOS_CONTACTS_IDENTITY", "").strip()

    if CONFIG_FILE.is_file():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            host = host or data.get("MACOS_HOST", "").strip()
            user = user or data.get("MACOS_USER", "").strip()
            known_hosts = known_hosts or data.get("MACOS_KNOWN_HOSTS", "").strip()
            identity = identity or data.get("MACOS_IDENTITY", "").strip()
        except Exception:
            pass

    return {
        "MACOS_CONTACTS_HOST": host,
        "MACOS_CONTACTS_USER": user,
        "MACOS_CONTACTS_KNOWN_HOSTS": known_hosts,
        "MACOS_CONTACTS_IDENTITY": identity,
    }


class Client:
    def __init__(
        self,
        environment: dict[str, str] | None = None,
        *,
        runner: Callable = subprocess.run,
        timeout: float = 30,
    ):
        conn = resolve_connection(environment)
        host = conn.get("MACOS_CONTACTS_HOST", "")
        user = conn.get("MACOS_CONTACTS_USER", "")
        if not HOST_PATTERN.fullmatch(host):
            raise ContactsError("MACOS_CONTACTS_HOST must be a tailnet .ts.net hostname")
        if not USER_PATTERN.fullmatch(user):
            raise ContactsError("MACOS_CONTACTS_USER is invalid")
        if not 1 <= timeout <= 30:
            raise ContactsError("timeout must be between 1 and 30 seconds")
        self.host = host
        self.user = user
        known_hosts_val = conn.get("MACOS_CONTACTS_KNOWN_HOSTS", "")
        if not known_hosts_val:
            raise ContactsError("MACOS_CONTACTS_KNOWN_HOSTS is required")
        self.known_hosts = self._owner_only_file(
            known_hosts_val,
            "MACOS_CONTACTS_KNOWN_HOSTS",
        )
        identity = conn.get("MACOS_CONTACTS_IDENTITY", "")
        self.identity = (
            self._owner_only_file(identity, "MACOS_CONTACTS_IDENTITY")
            if identity
            else None
        )
        self.runner = runner
        self.timeout = timeout

    @staticmethod
    def _owner_only_file(value: str, name: str) -> Path:
        path = Path(value)
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise ContactsError(f"{name} is missing: {path}") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise ContactsError(f"{name} must be a regular file: {path}")
        if metadata.st_mode & 0o077:
            raise ContactsError(f"{name} must be owner-only (mode 0600): {path}")
        return path

    def _command(self) -> list[str]:
        command = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={self.known_hosts}",
            "-o",
            "GlobalKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=15",
        ]
        if self.identity is not None:
            command.extend(
                [
                    "-o",
                    "IdentitiesOnly=yes",
                    "-i",
                    str(self.identity),
                ]
            )
        command.extend(
            [
                f"{self.user}@{self.host}",
                "/usr/bin/osascript",
                "-",
            ]
        )
        return command

    def _run(self, script: str) -> str:
        script = 'do shell script "/usr/bin/open -gj -a Contacts"\ndelay 1\n' + script
        try:
            result = self.runner(
                self._command(),
                input=script,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ContactsError("remote Contacts command timed out") from error
        except OSError as error:
            raise ContactsError(f"could not start SSH: {error}") from error
        if result.returncode:
            detail = result.stderr.strip() or f"exit status {result.returncode}"
            raise ContactsError(f"remote Contacts command failed: {detail}")
        return result.stdout.rstrip("\n")

    def status(self) -> str:
        return self._run('tell application "Contacts" to return "ready"')

    def get(self, contact_id: str) -> dict[str, str]:
        self._validate_contact_id(contact_id)
        output = self._run(self._person_script(contact_id))
        fields = output.split("\x1f")
        if len(fields) != 3:
            raise ContactsError("Contacts returned an invalid contact record")
        return {"id": fields[0], "first_name": fields[1], "last_name": fields[2]}

    def rename(self, contact_id: str, first_name: str, last_name: str) -> dict[str, str]:
        self._validate_contact_id(contact_id)
        require_value(first_name, "first name")
        require_value(last_name, "last name")
        script = self._person_script(
            contact_id,
            f"set first name of targetPerson to {applescript_literal(first_name)}\n"
            f"set last name of targetPerson to {applescript_literal(last_name)}\n"
            "save\n"
            "return \"updated\"",
        )
        if self._run(script) != "updated":
            raise ContactsError("Contacts did not confirm the rename")
        return self.get(contact_id)

    def find_all_by_phone(self, phone: str) -> list[dict[str, object]]:
        normalized = normalize_phone(phone)
        output = self._run(self._phone_search_script(normalized))
        if not output:
            return []
        rows = output.splitlines()
        contacts = []
        for row in rows:
            fields = row.split("\x1f")
            if len(fields) != 4 or fields[3] != normalized:
                raise ContactsError("Contacts returned an invalid phone match")
            contacts.append({
                "id": fields[0],
                "first_name": fields[1],
                "last_name": fields[2],
                "phones": [fields[3]],
            })
        return sorted(contacts, key=lambda contact: str(contact["id"]))

    def find_by_phone(self, phone: str) -> dict[str, object] | None:
        contacts = self.find_all_by_phone(phone)
        if len(contacts) > 1:
            raise ContactsError("multiple contacts have the exact phone number")
        return contacts[0] if contacts else None

    def create(self, first_name: str, phone: str) -> dict[str, object]:
        require_value(first_name, "first name")
        normalized = normalize_phone(phone)
        existing = self.find_by_phone(normalized)
        if existing:
            return {**existing, "action": "existing"}
        script = f'''tell application "Contacts"
set newPerson to make new person with properties {{first name:{applescript_literal(first_name)}}}
make new phone at end of phones of newPerson with properties {{label:"mobile", value:{applescript_literal(normalized)}}}
save
return id of newPerson as text
end tell'''
        contact_id = self._run(script)
        self._validate_contact_id(contact_id)
        created = self.find_by_phone(normalized)
        if not created or created["id"] != contact_id:
            raise ContactsError("Contacts did not confirm the created contact")
        return {**created, "action": "created"}

    @staticmethod
    def _validate_contact_id(contact_id: str) -> None:
        if not CONTACT_ID_PATTERN.fullmatch(contact_id):
            raise ContactsError("contact ID is invalid")

    @staticmethod
    def _person_script(contact_id: str, action: str | None = None) -> str:
        literal = applescript_literal(contact_id)
        if action is None:
            action = (
                'return (id of targetPerson as text) & (ASCII character 31) & '
                '(first name of targetPerson as text) & (ASCII character 31) & '
                '(last name of targetPerson as text)'
            )
        return f'''tell application "Contacts"
set matchingPeople to every person whose id is {literal}
if (count of matchingPeople) is not 1 then error "Contact was not found"
set targetPerson to item 1 of matchingPeople
{action}
end tell'''

    def search(self, query: str) -> list[dict[str, str]]:
        require_value(query, "search query")
        output = self._run(self._name_search_script(query))
        if not output:
            return []
        rows = output.splitlines()
        contacts = []
        for row in rows:
            fields = row.split("\x1f")
            if len(fields) >= 3:
                contacts.append({
                    "id": fields[0],
                    "first_name": fields[1],
                    "last_name": fields[2],
                })
        return contacts

    @staticmethod
    def _name_search_script(query: str) -> str:
        literal = applescript_literal(query)
        return f'''tell application "Contacts"
set matchingPeople to every person whose name contains {literal}
set resultRows to {{}}
repeat with candidatePerson in matchingPeople
    set end of resultRows to (id of candidatePerson as text) & (ASCII character 31) & (first name of candidatePerson as text) & (ASCII character 31) & (last name of candidatePerson as text)
end repeat
end tell
set AppleScript's text item delimiters to ASCII character 10
return resultRows as text'''

    @staticmethod
    def _phone_search_script(phone: str) -> str:
        return f'''set wantedPhone to {applescript_literal(phone)}
set resultRows to {{}}
tell application "Contacts"
set matchingPeople to every person whose value of phones contains wantedPhone
repeat with candidatePerson in matchingPeople
set end of resultRows to (id of candidatePerson as text) & (ASCII character 31) & (first name of candidatePerson as text) & (ASCII character 31) & (last name of candidatePerson as text) & (ASCII character 31) & {applescript_literal(phone)}
end repeat
end tell
set AppleScript's text item delimiters to ASCII character 10
return resultRows as text'''


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Use native macOS Contacts over SSH")
    root.add_argument("--timeout", type=float, default=30)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    get = commands.add_parser("get")
    get.add_argument("contact_id")
    rename = commands.add_parser("rename")
    rename.add_argument("contact_id")
    rename.add_argument("first_name")
    rename.add_argument("last_name")
    find = commands.add_parser("find-by-phone")
    find.add_argument("phone")
    find_all = commands.add_parser("find-all-by-phone")
    find_all.add_argument("phone")
    search_cmd = commands.add_parser("search")
    search_cmd.add_argument("query")
    create = commands.add_parser("create")
    create.add_argument("first_name")
    create.add_argument("phone")
    return root


def main(arguments: list[str] | None = None) -> int:
    args = parser().parse_args(sys.argv[1:] if arguments is None else arguments)
    try:
        client = Client(timeout=args.timeout)
        if args.command == "status":
            print(json.dumps({"status": client.status()}))
        elif args.command == "search":
            print(json.dumps(client.search(args.query), indent=2, sort_keys=True))
        elif args.command == "get":
            print(json.dumps(client.get(args.contact_id), sort_keys=True))
        elif args.command == "rename":
            print(json.dumps(client.rename(args.contact_id, args.first_name, args.last_name), sort_keys=True))
        elif args.command == "find-by-phone":
            print(json.dumps(client.find_by_phone(args.phone), sort_keys=True))
        elif args.command == "find-all-by-phone":
            print(json.dumps(client.find_all_by_phone(args.phone), sort_keys=True))
        else:
            print(json.dumps(client.create(args.first_name, args.phone), sort_keys=True))
        return 0
    except ContactsError as error:
        print(f"macos-contacts: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
