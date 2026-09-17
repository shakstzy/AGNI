#!/usr/bin/env python3
"""BlueBubbles REST API CLI adapter for HADES."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

CONFIG_FILE = Path.home() / ".config" / "hades" / "bluebubbles.json"


class BlueBubblesError(RuntimeError):
    pass


def encode_multipart(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = f"----hades-bluebubbles-{uuid.uuid4().hex}"
    marker = boundary.encode("ascii")
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                b"--" + marker + b"\r\n",
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            b"--" + marker + b"\r\n",
            (
                f'Content-Disposition: form-data; name="attachment"; '
                f'filename="{file_path.name}"\r\nContent-Type: {mime_type}\r\n\r\n'
            ).encode(),
            file_path.read_bytes(),
            b"\r\n--" + marker + b"--\r\n",
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def redact(value: str, password: str) -> str:
    if not password:
        return value
    for secret in (
        password,
        quote(password, safe=""),
        urlencode({"password": password}).partition("=")[2],
    ):
        value = value.replace(secret, "[redacted]")
    return value


def sanitize_response(body: bytes, password: str) -> str:
    text = body.decode(errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return redact(text, password)

    def scrub(value):
        if isinstance(value, str):
            return redact(value, password)
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        return value

    return json.dumps(scrub(parsed), indent=2, sort_keys=True)


def positive_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("limit must be an integer") from error
    if not 1 <= parsed <= 500:
        raise argparse.ArgumentTypeError("limit must be between 1 and 500")
    return parsed


def load_credentials() -> tuple[str, str]:
    """Resolves BlueBubbles server URL and password from env, ~/.config/hades, or legacy config."""
    url = os.environ.get("BLUEBUBBLES_URL", "").strip()
    password = os.environ.get("BLUEBUBBLES_PASSWORD", "").strip()

    if url and password:
        return url, password

    if CONFIG_FILE.is_file():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            url = url or data.get("BLUEBUBBLES_URL", "").strip()
            password = password or data.get("BLUEBUBBLES_PASSWORD", "").strip()
        except Exception:
            pass

    if url and password:
        return url, password

    raise BlueBubblesError(
        "BlueBubbles credentials missing. Provide BLUEBUBBLES_URL and "
        "BLUEBUBBLES_PASSWORD via environment or ~/.config/hades/bluebubbles.json"
    )


class Client:
    def __init__(self, url: str | None = None, password: str | None = None, timeout: float = 30):
        if not url or not password:
            resolved_url, resolved_password = load_credentials()
            url = url or resolved_url
            password = password or resolved_password

        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BlueBubblesError("BLUEBUBBLES_URL must be an http or https URL")
        if not password:
            raise BlueBubblesError("BLUEBUBBLES_PASSWORD is required")
        self.url = url.rstrip("/")
        self.password = password
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        *,
        body: bytes | None = None,
        content_type: str | None = None,
    ) -> bytes:
        if not path.startswith("/") or urlsplit(path).scheme:
            raise BlueBubblesError("API path must be relative")
        if payload is not None and body is not None:
            raise BlueBubblesError("request cannot include both JSON and raw content")
        separator = "&" if "?" in path else "?"
        target = f"{self.url}{path}{separator}{urlencode({'password': self.password})}"
        data = json.dumps(payload).encode() if payload is not None else body
        headers = {"Accept": "application/json", "User-Agent": "HADES-BlueBubbles/1.0"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        elif content_type is not None:
            headers["Content-Type"] = content_type
        try:
            with urlopen(
                Request(target, data=data, headers=headers, method=method),
                timeout=self.timeout,
            ) as response:
                return response.read()
        except HTTPError as error:
            detail = error.read().decode(errors="replace").strip() or str(error.reason)
            raise BlueBubblesError(
                f"BlueBubbles returned HTTP {error.code}: {redact(detail, self.password)}"
            ) from None
        except URLError as error:
            raise BlueBubblesError(
                f"Could not reach BlueBubbles: {redact(str(error.reason), self.password)}"
            ) from None


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Call the BlueBubbles REST API in HADES")
    root.add_argument("--timeout", type=float, default=30)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    chats = commands.add_parser("chats")
    chats.add_argument("--limit", type=positive_limit, default=50)
    recent = commands.add_parser("recent-messages")
    recent.add_argument("--limit", type=positive_limit, default=5)
    recent.add_argument("--attachments", action="store_true")
    messages = commands.add_parser("messages")
    messages.add_argument("chat_guid")
    messages.add_argument("--limit", type=positive_limit, default=50)
    messages.add_argument("--after", type=int)
    messages.add_argument("--sort", choices=["ASC", "DESC"], default="DESC")
    messages.add_argument("--attachments", action="store_true")
    message_status = commands.add_parser("message-status")
    message_status.add_argument("message_guid")
    contacts = commands.add_parser("contacts")
    contacts.add_argument("addresses", nargs="*")
    direct_chat = commands.add_parser("direct-chat")
    direct_chat.add_argument("address")
    send_direct = commands.add_parser("send-direct")
    send_direct.add_argument("address")
    send_direct.add_argument("message")
    send_direct.add_argument("--service", choices=["iMessage", "SMS"], default="iMessage")
    send_text = commands.add_parser("send-text")
    send_text.add_argument("chat_guid")
    send_text.add_argument("message")
    send_text.add_argument("--recipient-type", choices=["direct", "group"], required=True)
    send_file = commands.add_parser("send-file")
    send_file.add_argument("chat_guid")
    send_file.add_argument("file", type=Path)
    send_file.add_argument("--recipient-type", choices=["direct", "group"], required=True)
    attachment_download = commands.add_parser("attachment-download")
    attachment_download.add_argument("attachment_guid")
    attachment_download.add_argument("output", type=Path)
    attachment_download.add_argument("--original", action="store_true")
    return root


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    args = parser().parse_args(arguments)
    try:
        client = Client(timeout=args.timeout)
        if args.command == "status":
            print(sanitize_response(client.request("GET", "/api/v1/ping"), client.password))
            return 0
        if args.command == "chats":
            print(sanitize_response(client.request("POST", "/api/v1/chat/query", {
                "limit": args.limit,
                "sort": "lastmessage",
            }), client.password))
            return 0
        if args.command == "recent-messages":
            payload = {
                "limit": args.limit,
                "sort": "DESC",
            }
            if args.attachments:
                payload["with"] = ["attachments", "attachments.metadata"]
            print(sanitize_response(client.request("POST", "/api/v1/message/query", payload), client.password))
            return 0
        if args.command == "messages":
            payload = {
                "chatGuid": args.chat_guid,
                "limit": args.limit,
                "sort": args.sort,
            }
            if args.after is not None:
                payload["after"] = args.after
            if args.attachments:
                payload["with"] = ["attachments", "attachments.metadata"]
            print(sanitize_response(client.request("POST", "/api/v1/message/query", payload), client.password))
            return 0
        if args.command == "message-status":
            path = f"/api/v1/message/{quote(args.message_guid, safe='')}"
            print(sanitize_response(client.request("GET", path), client.password))
            return 0
        if args.command == "contacts":
            if args.addresses:
                response = client.request(
                    "POST", "/api/v1/contact/query", {"addresses": args.addresses}
                )
            else:
                response = client.request("GET", "/api/v1/contact")
            print(sanitize_response(response, client.password))
            return 0
        if args.command == "direct-chat":
            print(sanitize_response(client.request("POST", "/api/v1/chat/query", {
                "guid": f"any;-;{args.address}",
                "limit": 1,
            }), client.password))
            return 0
        if args.command == "send-direct":
            print(sanitize_response(client.request("POST", "/api/v1/chat/new", {
                "addresses": [args.address],
                "message": args.message,
                "service": args.service,
                "method": "private-api",
            }), client.password))
            return 0
        if args.command == "send-text":
            marker = ";+;" if args.recipient_type == "group" else ";-;"
            if marker not in args.chat_guid:
                raise BlueBubblesError(
                    f"chat GUID does not match recipient type {args.recipient_type}"
                )
            print(sanitize_response(client.request("POST", "/api/v1/message/text", {
                "chatGuid": args.chat_guid,
                "message": args.message,
                "method": "private-api",
            }), client.password))
            return 0
        if args.command == "send-file":
            if not args.file.is_absolute() or not args.file.is_file():
                raise BlueBubblesError(f"file must be an existing absolute path: {args.file}")
            marker = ";+;" if args.recipient_type == "group" else ";-;"
            if marker not in args.chat_guid:
                raise BlueBubblesError(
                    f"chat GUID does not match recipient type {args.recipient_type}"
                )
            body, content_type = encode_multipart(
                {
                    "chatGuid": args.chat_guid,
                    "name": args.file.name,
                    "method": "private-api",
                },
                args.file,
            )
            print(
                sanitize_response(
                    client.request(
                        "POST",
                        "/api/v1/message/attachment",
                        body=body,
                        content_type=content_type,
                    ),
                    client.password,
                )
            )
            return 0
        if args.command == "attachment-download":
            if not args.output.is_absolute():
                raise BlueBubblesError("output must be an absolute path")
            if args.output.exists():
                raise BlueBubblesError(f"output already exists: {args.output}")
            if not args.output.parent.is_dir():
                raise BlueBubblesError(f"output directory does not exist: {args.output.parent}")
            query = "?original=true" if args.original else ""
            data = client.request(
                "GET",
                f"/api/v1/attachment/{quote(args.attachment_guid, safe='')}/download{query}",
            )
            args.output.write_bytes(data)
            print(json.dumps({"status": 200, "data": {"path": str(args.output), "bytes": len(data)}}))
            return 0
        raise BlueBubblesError("unknown command")
    except BlueBubblesError as error:
        print(f"bluebubbles: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
