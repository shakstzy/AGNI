#!/usr/bin/env python3
"""Minimal native macOS Remote Host CLI over pinned Tailscale SSH for HADES."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

HOST_PATTERN = re.compile(
    r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+ts\.net\Z"
)
USER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}\Z")

CONFIG_FILE = Path.home() / ".config" / "hades" / "apple" / "apple-config.json"


class MacOSError(RuntimeError):
    """Raised when remote macOS execution fails."""
    pass


def resolve_connection(environment: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environment is None else environment
    host = env.get("MACOS_HOST", "").strip()
    user = env.get("MACOS_USER", "").strip()
    known_hosts = env.get("MACOS_KNOWN_HOSTS", "").strip()
    identity = env.get("MACOS_IDENTITY", "").strip()

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
        "MACOS_HOST": host,
        "MACOS_USER": user,
        "MACOS_KNOWN_HOSTS": known_hosts,
        "MACOS_IDENTITY": identity,
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
        host = conn.get("MACOS_HOST", "")
        user = conn.get("MACOS_USER", "")
        if not HOST_PATTERN.fullmatch(host):
            raise MacOSError(f"MACOS_HOST must be a tailnet .ts.net hostname, got: '{host}'")
        if not USER_PATTERN.fullmatch(user):
            raise MacOSError(f"MACOS_USER is invalid: '{user}'")

        self.host = host
        self.user = user
        known_hosts_val = conn.get("MACOS_KNOWN_HOSTS", "")
        if not known_hosts_val:
            raise MacOSError("MACOS_KNOWN_HOSTS is required")
        self.known_hosts = self._owner_only_file(known_hosts_val, "MACOS_KNOWN_HOSTS")
        identity = conn.get("MACOS_IDENTITY", "")
        self.identity = self._owner_only_file(identity, "MACOS_IDENTITY") if identity else None
        self.runner = runner
        self.timeout = timeout

    @staticmethod
    def _owner_only_file(value: str, name: str) -> Path:
        path = Path(value)
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise MacOSError(f"{name} is missing: {path}") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise MacOSError(f"{name} must be a regular file: {path}")
        if metadata.st_mode & 0o077:
            raise MacOSError(f"{name} must be owner-only (mode 0600): {path}")
        return path

    def _base_ssh_command(self) -> list[str]:
        command = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={self.known_hosts}",
            "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
        ]
        if self.identity is not None:
            command.extend(["-o", "IdentitiesOnly=yes", "-i", str(self.identity)])
        return command

    def exec_raw(self, remote_cmd: str, timeout: float | None = None) -> subprocess.CompletedProcess:
        """Run a command inside a login zsh shell on the remote macOS host."""
        cmd = self._base_ssh_command() + [f"{self.user}@{self.host}", f"zsh -l -c {subprocess.list2cmdline([remote_cmd])}"]
        try:
            return self.runner(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise MacOSError(f"remote macOS command timed out after {timeout or self.timeout}s") from error
        except OSError as error:
            raise MacOSError(f"could not start SSH: {error}") from error

    def status(self) -> dict[str, Any]:
        """Probe remote Mac host status and developer toolchain."""
        proc = self.exec_raw(
            "uname -a; which xcodebuild xcrun fastlane pod node npm brew 2>/dev/null || true",
            timeout=15,
        )
        if proc.returncode != 0:
            return {
                "ok": False,
                "host": self.host,
                "user": self.user,
                "error": proc.stderr.strip() or f"exit status {proc.returncode}",
            }

        lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
        os_info = lines[0] if lines else "Unknown"
        tool_paths = lines[1:] if len(lines) > 1 else []

        tools_found = {}
        for p in tool_paths:
            name = Path(p).name
            tools_found[name] = p

        return {
            "ok": True,
            "host": self.host,
            "user": self.user,
            "os": os_info,
            "tools": tools_found,
            "xcodebuild": tools_found.get("xcodebuild"),
            "fastlane": tools_found.get("fastlane"),
            "pod": tools_found.get("pod"),
            "node": tools_found.get("node"),
        }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="macos",
        description="Remote macOS Host CLI over pinned Tailscale SSH for HADES.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # status
    p_stat = sub.add_parser("status", help="Check remote Mac SSH connectivity and toolchain")
    p_stat.add_argument("--json", action="store_true", help="Output JSON format")

    # exec
    p_exec = sub.add_parser("exec", help="Execute command in login shell on remote Mac")
    p_exec.add_argument("cmd", help="Command string to execute")
    p_exec.add_argument("--timeout", type=float, default=60, help="Command timeout in seconds")

    # which
    p_which = sub.add_parser("which", help="Locate executable binary on remote Mac")
    p_which.add_argument("binary", help="Binary name to find")

    # xcodebuild
    p_xc = sub.add_parser("xcodebuild", help="Execute xcodebuild command on remote Mac")
    p_xc.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to xcodebuild")

    return p


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    if raw_args and raw_args[0] == "xcodebuild":
        try:
            client = Client()
            xc_args = raw_args[1:]
            xc_cmd = f"xcodebuild {' '.join(xc_args)}" if xc_args else "xcodebuild -version"
            proc = client.exec_raw(xc_cmd, timeout=300)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            return proc.returncode
        except MacOSError as e:
            print(f"macos error: {e}", file=sys.stderr)
            return 1

    args = parser().parse_args(raw_args)
    try:
        client = Client()
        if args.command == "status":
            stat_data = client.status()
            if args.json:
                print(json.dumps(stat_data, indent=2))
            else:
                if stat_data.get("ok"):
                    print(f"macOS Host: {stat_data['user']}@{stat_data['host']} [ONLINE]")
                    print(f"  OS: {stat_data.get('os')}")
                    print("  Tools:")
                    for t, path in stat_data.get("tools", {}).items():
                        print(f"    - {t}: {path}")
                else:
                    print(f"macOS Host: {stat_data['user']}@{stat_data['host']} [OFFLINE]")
                    print(f"  Error: {stat_data.get('error')}")
                    return 1
            return 0 if stat_data.get("ok") else 1

        elif args.command == "exec":
            proc = client.exec_raw(args.cmd, timeout=args.timeout)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            return proc.returncode

        elif args.command == "which":
            proc = client.exec_raw(f"which {args.binary}", timeout=10)
            out = proc.stdout.strip()
            if out:
                print(out)
                return 0
            else:
                print(f"Tool '{args.binary}' not found on remote macOS host", file=sys.stderr)
                return 1

        elif args.command == "xcodebuild":
            xc_cmd = f"xcodebuild {' '.join(args.args)}" if args.args else "xcodebuild -version"
            proc = client.exec_raw(xc_cmd, timeout=300)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            return proc.returncode

    except MacOSError as e:
        print(f"macos error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"unexpected error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
