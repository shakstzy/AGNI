#!/usr/bin/env python3
"""Apple Notes CLI over pinned SSH to the personal Mac for HADES."""

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
NOTE_ID_PATTERN = re.compile(
    r"x-coredata://[A-Za-z0-9-]+/(?:ICNote|ICFolder|IMAPNote|IMAPFolder)/p\d{1,12}\Z"
)
NAME_PATTERN = re.compile(r"[^\x00-\x1f]{1,80}\Z")
PROTECTED_FOLDERS = {"Notes", "archive", "Imported Notes"}
HTML_TAG = re.compile(r"<[^>]+>")

CONFIG_FILE = Path.home() / ".config" / "hades" / "apple" / "apple-config.json"


class NotesError(RuntimeError):
    pass


def require_value(value: str, description: str) -> str:
    if not value or len(value) > 255 or any(ord(character) < 32 for character in value):
        raise NotesError(f"{description} must be non-empty plain text")
    return value


def require_name(value: str, description: str) -> str:
    if not NAME_PATTERN.fullmatch(value or ""):
        raise NotesError(f"{description} is invalid")
    return value


def require_note_id(value: str) -> str:
    if not NOTE_ID_PATTERN.fullmatch(value or ""):
        raise NotesError("note ID is invalid")
    return value


def require_body(value: str) -> str:
    if not value or len(value) > 8000:
        raise NotesError("body must be plain text up to 8000 characters")
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise NotesError("body must be plain text")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def applescript_literal(value: str) -> str:
    if not value or len(value) > 8000:
        raise NotesError("Notes value must be non-empty plain text")
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise NotesError("Notes value must be plain text")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_rows(output: str, fields: int) -> list[list[str]]:
    if not output:
        return []
    rows = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != fields:
            raise NotesError("Notes returned an invalid record")
        rows.append(parts)
    return rows


def plaintext(html: str) -> str:
    text = HTML_TAG.sub("\n", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def resolve_connection(environment: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environment is None else environment
    host = env.get("MACOS_NOTES_HOST", "").strip()
    user = env.get("MACOS_NOTES_USER", "").strip()
    known_hosts = env.get("MACOS_NOTES_KNOWN_HOSTS", "").strip()
    identity = env.get("MACOS_NOTES_IDENTITY", "").strip()

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
        "MACOS_NOTES_HOST": host,
        "MACOS_NOTES_USER": user,
        "MACOS_NOTES_KNOWN_HOSTS": known_hosts,
        "MACOS_NOTES_IDENTITY": identity,
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
        host = conn.get("MACOS_NOTES_HOST", "")
        user = conn.get("MACOS_NOTES_USER", "")
        if not HOST_PATTERN.fullmatch(host):
            raise NotesError("MACOS_NOTES_HOST must be a tailnet .ts.net hostname")
        if not USER_PATTERN.fullmatch(user):
            raise NotesError("MACOS_NOTES_USER is invalid")
        if not 1 <= timeout <= 60:
            raise NotesError("timeout must be between 1 and 60 seconds")
        self.host = host
        self.user = user
        known_hosts_val = conn.get("MACOS_NOTES_KNOWN_HOSTS", "")
        if not known_hosts_val:
            raise NotesError("MACOS_NOTES_KNOWN_HOSTS is required")
        self.known_hosts = self._owner_only_file(
            known_hosts_val,
            "MACOS_NOTES_KNOWN_HOSTS",
        )
        identity = conn.get("MACOS_NOTES_IDENTITY", "")
        self.identity = self._owner_only_file(identity, "MACOS_NOTES_IDENTITY") if identity else None
        self.runner = runner
        self.timeout = timeout

    @staticmethod
    def _owner_only_file(value: str, name: str) -> Path:
        path = Path(value)
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise NotesError(f"{name} is missing: {path}") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise NotesError(f"{name} must be a regular file: {path}")
        if metadata.st_mode & 0o077:
            raise NotesError(f"{name} must be owner-only (mode 0600): {path}")
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
        script = 'do shell script "/usr/bin/open -gj -a Notes"\ndelay 1\n' + script
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
            raise NotesError("remote Notes command timed out") from error
        except OSError as error:
            raise NotesError(f"could not start SSH: {error}") from error
        if result.returncode:
            detail = result.stderr.strip() or f"exit status {result.returncode}"
            raise NotesError(f"remote Notes command failed: {detail}")
        return result.stdout.rstrip("\n")

    def status(self) -> dict[str, object]:
        folders = self.folders()
        return {
            "status": "ready",
            "folders": len(folders),
            "notes": sum(int(item["notes"]) for item in folders),
        }

    def folders(self) -> list[dict[str, object]]:
        output = self._run(
            """tell application "Notes"
set rows to {}
repeat with targetFolder in folders
set end of rows to (name of targetFolder as text) & (ASCII character 31) & (id of targetFolder as text) & (ASCII character 31) & ((count of notes of targetFolder) as text)
end repeat
set AppleScript's text item delimiters to ASCII character 10
return rows as text
end tell"""
        )
        rows = []
        for name, folder_id, count in parse_rows(output, 3):
            rows.append({"name": name, "id": folder_id, "notes": int(count)})
        return rows

    def notes(self, folder_name: str) -> list[dict[str, str]]:
        require_name(folder_name, "folder name")
        output = self._run(
            f"""tell application "Notes"
if not (exists folder {applescript_literal(folder_name)}) then error "Folder was not found"
set rows to {{}}
tell folder {applescript_literal(folder_name)}
repeat with targetNote in notes
set end of rows to (id of targetNote as text) & (ASCII character 31) & (name of targetNote as text)
end repeat
end tell
set AppleScript's text item delimiters to ASCII character 10
return rows as text
end tell"""
        )
        return [{"id": note_id, "title": title, "folder": folder_name} for note_id, title in parse_rows(output, 2)]

    def get(self, note_id: str) -> dict[str, str]:
        require_note_id(note_id)
        output = self._run(
            f"""tell application "Notes"
set targetNote to note id {applescript_literal(note_id)}
return (id of targetNote as text) & (ASCII character 31) & (name of targetNote as text) & (ASCII character 31) & (body of targetNote as text)
end tell"""
        )
        parts = output.split("\x1f", 2)
        if len(parts) != 3:
            raise NotesError("Notes returned an invalid note record")
        return {
            "id": parts[0],
            "title": parts[1],
            "body": plaintext(parts[2]),
        }

    def create(self, title: str, body: str, *, folder_name: str = "Notes") -> dict[str, str]:
        require_name(title, "title")
        require_name(folder_name, "folder name")
        require_body(body)
        html_body = "".join(f"<div>{line}</div>" if line else "<div><br></div>" for line in body.split("\n"))
        note_id = self._run(
            f"""tell application "Notes"
if not (exists folder {applescript_literal(folder_name)}) then error "Folder was not found"
set newNote to make new note at folder {applescript_literal(folder_name)} with properties {{name:{applescript_literal(title)}, body:{applescript_literal(html_body)}}}
return id of newNote as text
end tell"""
        )
        require_note_id(note_id)
        created = self.get(note_id)
        created["folder"] = folder_name
        created["action"] = "created"
        return created

    def append(self, note_id: str, body: str) -> dict[str, str]:
        require_note_id(note_id)
        require_body(body)
        html_body = "".join(f"<div>{line}</div>" if line else "<div><br></div>" for line in body.split("\n"))
        output = self._run(
            f"""tell application "Notes"
set targetNote to note id {applescript_literal(note_id)}
set body of targetNote to (body of targetNote) & {applescript_literal(html_body)}
return id of targetNote as text
end tell"""
        )
        require_note_id(output)
        updated = self.get(output)
        updated["action"] = "appended"
        return updated

    def delete(self, note_id: str) -> dict[str, str]:
        require_note_id(note_id)
        output = self._run(
            f"""tell application "Notes"
set targetNote to note id {applescript_literal(note_id)}
set noteName to name of targetNote as text
delete targetNote
return {applescript_literal(note_id)} & (ASCII character 31) & noteName
end tell"""
        )
        rows = parse_rows(output, 2)
        return {"id": rows[0][0], "title": rows[0][1], "action": "deleted"}

    def create_folder(self, folder_name: str) -> dict[str, str]:
        require_name(folder_name, "folder name")
        output = self._run(
            f"""tell application "Notes"
if (exists folder {applescript_literal(folder_name)}) then error "Folder already exists"
make new folder with properties {{name:{applescript_literal(folder_name)}}}
return {applescript_literal(folder_name)}
end tell"""
        )
        if output != folder_name:
            raise NotesError("Notes did not confirm the new folder")
        return {"folder": folder_name, "action": "created"}

    def delete_folder(self, folder_name: str) -> dict[str, str]:
        require_name(folder_name, "folder name")
        if folder_name in PROTECTED_FOLDERS:
            raise NotesError(f"{folder_name} is a protected Notes folder")
        output = self._run(
            f"""tell application "Notes"
if not (exists folder {applescript_literal(folder_name)}) then error "Folder was not found"
delete folder {applescript_literal(folder_name)}
return {applescript_literal(folder_name)}
end tell"""
        )
        if output != folder_name:
            raise NotesError("Notes did not confirm the folder delete")
        return {"folder": folder_name, "action": "deleted"}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Use Apple Notes over SSH")
    root.add_argument("--timeout", type=float, default=45)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("folders")
    notes = commands.add_parser("notes")
    notes.add_argument("folder_name")
    get = commands.add_parser("get")
    get.add_argument("note_id")
    create = commands.add_parser("create")
    create.add_argument("title")
    create.add_argument("--body", required=True)
    create.add_argument("--folder", dest="folder_name", default="Notes")
    append = commands.add_parser("append")
    append.add_argument("note_id")
    append.add_argument("--body", required=True)
    delete = commands.add_parser("delete")
    delete.add_argument("note_id")
    delete.add_argument("--force", action="store_true")
    create_folder = commands.add_parser("create-folder")
    create_folder.add_argument("folder_name")
    delete_folder = commands.add_parser("delete-folder")
    delete_folder.add_argument("folder_name")
    delete_folder.add_argument("--force", action="store_true")
    return root


def main(arguments: list[str] | None = None) -> int:
    args = parser().parse_args(sys.argv[1:] if arguments is None else arguments)
    try:
        client = Client(timeout=args.timeout)
        if args.command == "status":
            print(json.dumps(client.status(), sort_keys=True))
        elif args.command == "folders":
            print(json.dumps(client.folders(), sort_keys=True))
        elif args.command == "notes":
            print(json.dumps(client.notes(args.folder_name), sort_keys=True))
        elif args.command == "get":
            print(json.dumps(client.get(args.note_id), sort_keys=True))
        elif args.command == "create":
            print(json.dumps(client.create(args.title, args.body, folder_name=args.folder_name), sort_keys=True))
        elif args.command == "append":
            print(json.dumps(client.append(args.note_id, args.body), sort_keys=True))
        elif args.command == "delete":
            if not args.force:
                raise NotesError("delete requires --force")
            print(json.dumps(client.delete(args.note_id), sort_keys=True))
        elif args.command == "create-folder":
            print(json.dumps(client.create_folder(args.folder_name), sort_keys=True))
        else:
            if not args.force:
                raise NotesError("delete-folder requires --force")
            print(json.dumps(client.delete_folder(args.folder_name), sort_keys=True))
        return 0
    except NotesError as error:
        print(f"apple-notes: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
