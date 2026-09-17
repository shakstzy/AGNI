#!/usr/bin/env python3
"""Apple Reminders CLI over pinned SSH to the personal Mac for HADES."""

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
REMINDER_ID_PATTERN = re.compile(r"x-apple-reminder://[A-Za-z0-9-]{1,80}\Z")
LIST_NAME_PATTERN = re.compile(r"[^\x00-\x1f]{1,80}\Z")
TODAY_SOFT_CAP = 3
PROTECTED_LISTS = {"Inbox", "Today", "Someday"}

CONFIG_FILE = Path.home() / ".config" / "hades" / "apple" / "apple-config.json"


class RemindersError(RuntimeError):
    pass


def require_value(value: str, description: str) -> str:
    if not value or len(value) > 255 or any(ord(character) < 32 for character in value):
        raise RemindersError(f"{description} must be non-empty plain text")
    return value


def require_list_name(value: str) -> str:
    if not LIST_NAME_PATTERN.fullmatch(value or ""):
        raise RemindersError("list name is invalid")
    return value


def require_reminder_id(value: str) -> str:
    if not REMINDER_ID_PATTERN.fullmatch(value or ""):
        raise RemindersError("reminder ID is invalid")
    return value


def applescript_literal(value: str) -> str:
    require_value(value, "Reminders value")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_rows(output: str, fields: int) -> list[list[str]]:
    if not output:
        return []
    rows = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != fields:
            raise RemindersError("Reminders returned an invalid record")
        rows.append(parts)
    return rows


def resolve_connection(environment: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environment is None else environment
    host = env.get("MACOS_REMINDERS_HOST", "").strip()
    user = env.get("MACOS_REMINDERS_USER", "").strip()
    known_hosts = env.get("MACOS_REMINDERS_KNOWN_HOSTS", "").strip()
    identity = env.get("MACOS_REMINDERS_IDENTITY", "").strip()

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
        "MACOS_REMINDERS_HOST": host,
        "MACOS_REMINDERS_USER": user,
        "MACOS_REMINDERS_KNOWN_HOSTS": known_hosts,
        "MACOS_REMINDERS_IDENTITY": identity,
    }


class Client:
    def __init__(
        self,
        environment: dict[str, str] | None = None,
        *,
        runner: Callable = subprocess.run,
        timeout: float = 45,
    ):
        conn = resolve_connection(environment)
        host = conn.get("MACOS_REMINDERS_HOST", "")
        user = conn.get("MACOS_REMINDERS_USER", "")
        if not HOST_PATTERN.fullmatch(host):
            raise RemindersError("MACOS_REMINDERS_HOST must be a tailnet .ts.net hostname")
        if not USER_PATTERN.fullmatch(user):
            raise RemindersError("MACOS_REMINDERS_USER is invalid")
        if not 1 <= timeout <= 60:
            raise RemindersError("timeout must be between 1 and 60 seconds")
        self.host = host
        self.user = user
        known_hosts_val = conn.get("MACOS_REMINDERS_KNOWN_HOSTS", "")
        if not known_hosts_val:
            raise RemindersError("MACOS_REMINDERS_KNOWN_HOSTS is required")
        self.known_hosts = self._owner_only_file(
            known_hosts_val,
            "MACOS_REMINDERS_KNOWN_HOSTS",
        )
        identity = conn.get("MACOS_REMINDERS_IDENTITY", "")
        self.identity = (
            self._owner_only_file(identity, "MACOS_REMINDERS_IDENTITY") if identity else None
        )
        self.runner = runner
        self.timeout = timeout

    @staticmethod
    def _owner_only_file(value: str, name: str) -> Path:
        path = Path(value)
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise RemindersError(f"{name} is missing: {path}") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise RemindersError(f"{name} must be a regular file: {path}")
        if metadata.st_mode & 0o077:
            raise RemindersError(f"{name} must be owner-only (mode 0600): {path}")
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
            command.extend(["-o", "IdentitiesOnly=yes", "-i", str(self.identity)])
        command.extend([f"{self.user}@{self.host}", "/usr/bin/osascript", "-"])
        return command

    def _run(self, script: str) -> str:
        script = 'do shell script "/usr/bin/open -gj -a Reminders"\ndelay 1\n' + script
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
            raise RemindersError("remote Reminders command timed out") from error
        except OSError as error:
            raise RemindersError(f"could not start SSH: {error}") from error
        if result.returncode:
            detail = result.stderr.strip() or f"exit status {result.returncode}"
            raise RemindersError(f"remote Reminders command failed: {detail}")
        return result.stdout.rstrip("\n")

    def status(self) -> dict[str, object]:
        output = self._run(
            """tell application "Reminders"
set totalOpen to 0
repeat with aList in lists
set totalOpen to totalOpen + (count of (reminders of aList whose completed is false))
end repeat
return (count of lists as text) & (ASCII character 31) & (totalOpen as text)
end tell"""
        )
        parts = output.split("\x1f")
        list_count = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        open_count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return {
            "status": "ready",
            "lists": list_count,
            "open": open_count,
        }

    def lists(self) -> list[dict[str, object]]:
        output = self._run(
            """tell application "Reminders"
set rows to {}
repeat with targetList in lists
set openCount to count of (reminders of targetList whose completed is false)
set end of rows to (name of targetList as text) & (ASCII character 31) & (id of targetList as text) & (ASCII character 31) & (openCount as text)
end repeat
set AppleScript's text item delimiters to ASCII character 10
return rows as text
end tell"""
        )
        rows = []
        for name, list_id, open_count in parse_rows(output, 3):
            rows.append({"name": name, "id": list_id, "open": int(open_count)})
        return rows

    def show(self, list_name: str, *, completed: bool = False) -> list[dict[str, str]]:
        require_list_name(list_name)
        whose = "" if completed else " whose completed is false"
        output = self._run(
            f"""tell application "Reminders"
if not (exists list {applescript_literal(list_name)}) then error "List was not found"
set rows to {{}}
tell list {applescript_literal(list_name)}
repeat with targetReminder in (reminders{whose})
set end of rows to (id of targetReminder as text) & (ASCII character 31) & (name of targetReminder as text) & (ASCII character 31) & {applescript_literal(list_name)}
end repeat
end tell
set AppleScript's text item delimiters to ASCII character 10
return rows as text
end tell"""
        )
        return [
            {"id": reminder_id, "title": title, "list": listed}
            for reminder_id, title, listed in parse_rows(output, 3)
        ]

    def today_open_count(self) -> int:
        output = self._run(
            """tell application "Reminders"
if not (exists list "Today") then error "List was not found"
return (count of (reminders of list "Today" whose completed is false)) as text
end tell"""
        )
        try:
            return int(output)
        except ValueError as error:
            raise RemindersError("Reminders returned an invalid Today count") from error

    def now(self) -> dict[str, object]:
        open_count = self.today_open_count()
        next_items = self.show("Today")[:TODAY_SOFT_CAP] if 0 < open_count <= TODAY_SOFT_CAP else []
        return {
            "list": "Today",
            "open": open_count,
            "cap": TODAY_SOFT_CAP,
            "overflow": max(0, open_count - TODAY_SOFT_CAP),
            "next": next_items,
        }

    def add(
        self,
        title: str,
        *,
        list_name: str = "Inbox",
        notes: str = "",
    ) -> dict[str, str]:
        require_list_name(list_name)
        require_value(title, "title")
        if notes and (len(notes) > 2000 or any(ord(character) < 32 and character not in "\n\t" for character in notes)):
            raise RemindersError("notes must be plain text")
        notes = notes.replace("\r", "\n")
        properties = f"name:{applescript_literal(title)}"
        if notes:
            properties += f", body:{applescript_literal(notes)}"
        reminder_id = self._run(
            f"""tell application "Reminders"
if not (exists list {applescript_literal(list_name)}) then error "List was not found"
set newReminder to make new reminder in list {applescript_literal(list_name)} with properties {{{properties}}}
return id of newReminder as text
end tell"""
        )
        require_reminder_id(reminder_id)
        return {"id": reminder_id, "title": title, "list": list_name, "action": "created"}

    def capture(self, title: str, notes: str = "") -> dict[str, str]:
        created = self.add(title, list_name="Inbox", notes=notes)
        created["action"] = "captured"
        return created

    def complete(self, reminder_id: str) -> dict[str, str]:
        require_reminder_id(reminder_id)
        output = self._run(
            f"""tell application "Reminders"
set targetReminder to reminder id {applescript_literal(reminder_id)}
set completed of targetReminder to true
return (id of targetReminder as text) & (ASCII character 31) & (name of targetReminder as text)
end tell"""
        )
        rows = parse_rows(output, 2)
        return {"id": rows[0][0], "title": rows[0][1], "action": "completed"}

    def delete(self, reminder_id: str) -> dict[str, str]:
        require_reminder_id(reminder_id)
        output = self._run(
            f"""tell application "Reminders"
set targetReminder to reminder id {applescript_literal(reminder_id)}
set reminderName to name of targetReminder as text
delete targetReminder
return {applescript_literal(reminder_id)} & (ASCII character 31) & reminderName
end tell"""
        )
        rows = parse_rows(output, 2)
        return {"id": rows[0][0], "title": rows[0][1], "action": "deleted"}

    def move(self, reminder_id: str, list_name: str) -> dict[str, str]:
        require_reminder_id(reminder_id)
        require_list_name(list_name)
        output = self._run(
            f"""tell application "Reminders"
if not (exists list {applescript_literal(list_name)}) then error "List was not found"
set targetReminder to reminder id {applescript_literal(reminder_id)}
move targetReminder to list {applescript_literal(list_name)}
return (id of targetReminder as text) & (ASCII character 31) & (name of targetReminder as text) & (ASCII character 31) & {applescript_literal(list_name)}
end tell"""
        )
        rows = parse_rows(output, 3)
        return {"id": rows[0][0], "title": rows[0][1], "list": rows[0][2], "action": "moved"}

    def promote(self, reminder_id: str, *, force: bool = False) -> dict[str, object]:
        today_count = self.today_open_count()
        if today_count >= TODAY_SOFT_CAP and not force:
            raise RemindersError(
                f"Today already has {today_count} open items (cap {TODAY_SOFT_CAP}); park extras or pass --force"
            )
        moved: dict[str, object] = dict(self.move(reminder_id, "Today"))
        moved["open_today"] = today_count + 1
        return moved

    def park(self, reminder_id: str) -> dict[str, str]:
        return self.move(reminder_id, "Someday")

    def create_list(self, list_name: str) -> dict[str, str]:
        require_list_name(list_name)
        output = self._run(
            f"""tell application "Reminders"
if (exists list {applescript_literal(list_name)}) then error "List already exists"
make new list with properties {{name:{applescript_literal(list_name)}}}
return {applescript_literal(list_name)}
end tell"""
        )
        if output != list_name:
            raise RemindersError("Reminders did not confirm the new list")
        return {"list": list_name, "action": "created"}

    def delete_list(self, list_name: str) -> dict[str, str]:
        require_list_name(list_name)
        if list_name in PROTECTED_LISTS:
            raise RemindersError(f"{list_name} is a protected ADHD list")
        output = self._run(
            f"""tell application "Reminders"
if not (exists list {applescript_literal(list_name)}) then error "List was not found"
delete list {applescript_literal(list_name)}
return {applescript_literal(list_name)}
end tell"""
        )
        if output != list_name:
            raise RemindersError("Reminders did not confirm the list delete")
        return {"list": list_name, "action": "deleted"}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Use Apple Reminders over SSH for HADES")
    root.add_argument("--timeout", type=float, default=45)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("lists")
    commands.add_parser("now")
    show = commands.add_parser("show")
    show.add_argument("list_name")
    show.add_argument("--completed", action="store_true")
    add = commands.add_parser("add")
    add.add_argument("title")
    add.add_argument("--list", dest="list_name", default="Inbox")
    add.add_argument("--notes", default="")
    capture = commands.add_parser("capture")
    capture.add_argument("title")
    capture.add_argument("--notes", default="")
    complete = commands.add_parser("complete")
    complete.add_argument("reminder_id")
    delete = commands.add_parser("delete")
    delete.add_argument("reminder_id")
    delete.add_argument("--force", action="store_true")
    move = commands.add_parser("move")
    move.add_argument("reminder_id")
    move.add_argument("--list", dest="list_name", required=True)
    promote = commands.add_parser("promote")
    promote.add_argument("reminder_id")
    promote.add_argument("--force", action="store_true")
    park = commands.add_parser("park")
    park.add_argument("reminder_id")
    create_list = commands.add_parser("create-list")
    create_list.add_argument("list_name")
    delete_list = commands.add_parser("delete-list")
    delete_list.add_argument("list_name")
    delete_list.add_argument("--force", action="store_true")
    return root


def main(arguments: list[str] | None = None) -> int:
    args = parser().parse_args(sys.argv[1:] if arguments is None else arguments)
    try:
        client = Client(timeout=args.timeout)
        if args.command == "status":
            print(json.dumps(client.status(), sort_keys=True))
        elif args.command == "lists":
            print(json.dumps(client.lists(), sort_keys=True))
        elif args.command == "now":
            print(json.dumps(client.now(), sort_keys=True))
        elif args.command == "show":
            print(json.dumps(client.show(args.list_name, completed=args.completed), sort_keys=True))
        elif args.command == "add":
            print(json.dumps(client.add(args.title, list_name=args.list_name, notes=args.notes), sort_keys=True))
        elif args.command == "capture":
            print(json.dumps(client.capture(args.title, notes=args.notes), sort_keys=True))
        elif args.command == "complete":
            print(json.dumps(client.complete(args.reminder_id), sort_keys=True))
        elif args.command == "delete":
            if not args.force:
                raise RemindersError("delete requires --force")
            print(json.dumps(client.delete(args.reminder_id), sort_keys=True))
        elif args.command == "move":
            print(json.dumps(client.move(args.reminder_id, args.list_name), sort_keys=True))
        elif args.command == "promote":
            print(json.dumps(client.promote(args.reminder_id, force=args.force), sort_keys=True))
        elif args.command == "park":
            print(json.dumps(client.park(args.reminder_id), sort_keys=True))
        elif args.command == "create-list":
            print(json.dumps(client.create_list(args.list_name), sort_keys=True))
        else:
            if not args.force:
                raise RemindersError("delete-list requires --force")
            print(json.dumps(client.delete_list(args.list_name), sort_keys=True))
        return 0
    except RemindersError as error:
        print(f"apple-reminders: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
