#!/usr/bin/env python3
"""Home Assistant REST API client and CLI adapter for HADES."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

CONFIG_FILE = Path.home() / ".config" / "hades" / "home-assistant.json"
INDEX_FILE = Path(os.environ.get("HOME_ASSISTANT_INDEX_FILE", str(Path.home() / ".config" / "hades" / "devices.json")))

UPSTAIRS_ENTITIES = (
    ("fan", "fan.ceiling_fan"),
    ("light", "light.ceiling_fan"),
)

DOWNSTAIRS_ENTITIES = (
    ("switch", "switch.living_room"),
    ("switch", "switch.kitchen"),
)

DEFAULT_INDEX: dict[str, Any] = {
    "aliases": {
        "kitchen": "switch.kitchen",
        "kitchen_switch": "switch.kitchen",
        "kitchen_light": "switch.kitchen",
        "kitchen_lights": "switch.kitchen",
        "living_room": "switch.living_room",
        "living-room": "switch.living_room",
        "living_room_light": "switch.living_room",
        "living_room_lights": "switch.living_room",
        "countertop": "switch.countertop",
        "countertop_light": "switch.countertop",
        "countertop_lights": "switch.countertop",
        "desk": "switch.desk_socket_1",
        "pc_desk": "switch.pc_desk",
        "spiral": "switch.spiral_socket_1",
        "outdoor": "switch.outdoor",
        "outdoor_light": "switch.outdoor",
        "fan_light": "light.ceiling_fan",
        "upstairs_fan": "fan.ceiling_fan",
        "upstairs_ceiling_fan": "fan.ceiling_fan",
        "upstairs_fan_light": "light.ceiling_fan",
        "upstairs_light": "light.ceiling_fan",
        "downstairs_fan": "fan.fan",
        "downstairs_fan_light": "light.fan",
        "downstairs_light": "light.fan",
        "ceiling_fan": "fan.ceiling_fan",
        "fan": "fan.fan",
        "lamp": "light.lamp",
        "corner": "light.corner",
        "wled": "light.wled",
        "wled_2": "light.wled_2",
        # Cameras
        "doorbell": "camera.casco_doorbell_live_view",
        "doorbell_camera": "camera.casco_doorbell_live_view",
        "backyard_camera": "camera.casco_backyard_live_view",
        "backyard_cam": "camera.casco_backyard_live_view",
        "backyard": "camera.casco_backyard_live_view",
        "front_camera": "camera.casco_front_live_view",
        "front_cam": "camera.casco_front_live_view",
        "upstairs_camera": "camera.upstairs_live_view",
        "upstairs_cam": "camera.upstairs_live_view",
        "downstairs_camera": "camera.downstairs_live_view",
        "downstairs_cam": "camera.downstairs_live_view",
        # Media Players
        "tv": "media_player.shaku",
        "roku": "media_player.shaku",
        "soundbar": "media_player.shaksurround",
        "google_tv": "media_player.googletv9852",
        # Sirens
        "backyard_siren": "siren.casco_backyard_siren",
        "front_siren": "siren.casco_front_siren",
        # Environmental / Person
        "weather": "weather.forecast_home",
        "shak": "person.shakestate",
    },
    "groups": {
        "downstairs": [
            "switch.living_room",
            "switch.kitchen",
        ],
        "upstairs": [
            "fan.ceiling_fan",
            "light.ceiling_fan",
        ],
        "fans": [
            "fan.ceiling_fan",
            "fan.fan",
        ],
        "fan_lights": [
            "light.ceiling_fan",
            "light.fan",
        ],
        "all_fans": [
            "fan.ceiling_fan",
            "fan.fan",
        ],
        "all_lights": [
            "light.ceiling_fan",
            "light.fan",
            "light.kitchen",
            "light.corner",
            "light.lamp",
            "light.wled",
            "light.wled_2",
        ],
        "kitchen": [
            "switch.kitchen",
        ],
    },
    "devices": {
        "switch.kitchen": {"domain": "switch", "name": "Kitchen"},
        "switch.living_room": {"domain": "switch", "name": "Living Room"},
        "switch.countertop": {"domain": "switch", "name": "Countertop"},
        "switch.desk_socket_1": {"domain": "switch", "name": "DESK Socket 1"},
        "switch.pc_desk": {"domain": "switch", "name": "PC Desk"},
        "switch.spiral_socket_1": {"domain": "switch", "name": "SPIRAL Socket 1"},
        "switch.outdoor": {"domain": "switch", "name": "Outdoor"},
        "fan.ceiling_fan": {"domain": "fan", "name": "Ceiling Fan"},
        "light.ceiling_fan": {"domain": "light", "name": "Ceiling Fan"},
        "fan.fan": {"domain": "fan", "name": "Fan"},
        "light.fan": {"domain": "light", "name": "Fan"},
        "light.corner": {"domain": "light", "name": "Corner"},
        "light.lamp": {"domain": "light", "name": "Lamp"},
        "light.wled": {"domain": "light", "name": "WLED"},
        "light.wled_2": {"domain": "light", "name": "WLED 2"},
    },
}

ALIASES: dict[str, tuple[str, str]] = {
    "kitchen": ("switch", "switch.kitchen"),
    "living_room": ("switch", "switch.living_room"),
    "living-room": ("switch", "switch.living_room"),
    "countertop": ("switch", "switch.countertop"),
    "desk": ("switch", "switch.desk_socket_1"),
    "pc_desk": ("switch", "switch.pc_desk"),
    "spiral": ("switch", "switch.spiral_socket_1"),
    "outdoor": ("switch", "switch.outdoor"),
    "upstairs_fan": ("fan", "fan.ceiling_fan"),
    "upstairs_fan_light": ("light", "light.ceiling_fan"),
    "downstairs_fan": ("fan", "fan.fan"),
    "downstairs_fan_light": ("light", "light.fan"),
    "corner": ("light", "light.corner"),
    "lamp": ("light", "light.lamp"),
    "wled": ("light", "light.wled"),
    "wled_2": ("light", "light.wled_2"),
}


def load_device_index() -> dict[str, Any]:
    if INDEX_FILE.is_file():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("aliases", {})
                    data.setdefault("groups", {})
                    data.setdefault("devices", {})
                    for g, members in DEFAULT_INDEX["groups"].items():
                        if g not in data["groups"]:
                            data["groups"][g] = members
                    for a, eid in DEFAULT_INDEX["aliases"].items():
                        if a not in data["aliases"]:
                            data["aliases"][a] = eid
                    for d, info in DEFAULT_INDEX["devices"].items():
                        if d not in data["devices"]:
                            data["devices"][d] = info
                    return data
        except Exception:
            pass
    save_device_index(DEFAULT_INDEX)
    return DEFAULT_INDEX.copy()


def save_device_index(index: dict[str, Any]) -> None:
    try:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, sort_keys=True)
            f.write("\n")
        INDEX_FILE.chmod(0o600)
    except Exception:
        pass


IDENTIFIER = re.compile(r"^[a-z0-9_]+$")


class ClientError(RuntimeError):
    """User-actionable client error."""


def redact(value: str, secret: str) -> str:
    return value.replace(secret, "[redacted]") if secret else value


def timeout(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed <= 300:
        raise argparse.ArgumentTypeError("timeout must be greater than 0 and at most 300")
    return parsed


def identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "must contain only lowercase letters, digits, and underscores"
        )
    return value


def entity_id(value: str) -> str:
    val = value.strip().lower()
    index = load_device_index()
    if val in index.get("groups", {}) or val in index.get("aliases", {}):
        return val
    domain, separator, name = val.partition(".")
    if separator and "." not in name and IDENTIFIER.fullmatch(domain) and IDENTIFIER.fullmatch(name):
        return val
    # Allow alphanumeric identifier / alias as target for auto-discovery
    if IDENTIFIER.fullmatch(val.replace("-", "_")):
        return val
    raise argparse.ArgumentTypeError(f"must be an entity ID such as light.kitchen or valid alias: {value}")


def json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"invalid JSON: {error.msg}") from error
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("JSON data must be an object")
    if "entity_id" in parsed:
        raise argparse.ArgumentTypeError("JSON data must not contain entity_id; use --entity")
    return parsed


def target_arg(value: str) -> str:
    val = value.strip()
    if not val:
        raise argparse.ArgumentTypeError("Target cannot be empty")
    return val


def parse_intent(phrase: str) -> tuple[str, list[str]]:
    """Parse a natural English action phrase into action and target names."""
    text = phrase.strip().lower()
    action = None
    remainder = text

    # Quick environmental and presence queries
    if any(text == w or text == f"what's the {w}" or text == f"how's the {w}" or text == f"what is the {w}" for w in ("weather", "forecast")):
        return "weather", ["forecast_home"]
    if any(text == p for p in ("who is home", "who's home", "presence", "is anyone home", "is shak home")):
        return "presence", ["home"]

    # Camera snapshot
    m_snap = re.search(r"\b(?:take\s+(?:a\s+)?snapshot\s+(?:of\s+)?|snapshot\s+(?:of\s+)?|capture\s+(?:camera\s+)?)(.+)", text)
    if m_snap:
        raw_tgt = m_snap.group(1).strip()
        cleaned_tgt = re.sub(r"\b(?:the|camera|feed|live\s+view)\b", " ", raw_tgt).strip()
        cleaned_tgt = " ".join(cleaned_tgt.split())
        return "snapshot", [cleaned_tgt or "doorbell"]

    # Media controls
    if text.startswith("pause "):
        return "pause", [text[6:].strip()]
    if text.startswith("play ") or text.startswith("resume "):
        pfx = "play " if text.startswith("play ") else "resume "
        return "play", [text[len(pfx):].strip()]
    if text.startswith("stop ") and any(m in text for m in ("tv", "music", "roku", "soundbar", "player", "speaker")):
        return "stop", [text[5:].strip()]
    if text.startswith("mute "):
        return "mute", [text[5:].strip()]
    if text.startswith("unmute "):
        return "unmute", [text[7:].strip()]

    # Color changes
    m_col = re.search(r"\b(?:set|turn)\s+(.+?)\s+(?:to\s+)?(red|green|blue|yellow|orange|purple|cyan|magenta|pink|warm\s+white|cool\s+white|daylight|white)\b", text)
    if m_col:
        tgt = m_col.group(1).strip()
        col = m_col.group(2).strip()
        return f"color:{col}", [tgt]

    # First check for setting specific levels (e.g., "set upstairs fan to 50%", "fan to 40%")
    m_set = re.search(r"\b(?:set\s+)?(.+?)\s+(?:to\s+|at\s+)(\d{1,3})\s*%", text)
    if not m_set:
        m_set = re.search(r"\bset\s+(.+?)\s+to\s+(\d{1,3})\b", text)

    if m_set:
        target_part = m_set.group(1).strip()
        level_val = int(m_set.group(2))
        action = f"set:{level_val}"
        remainder = target_part
    elif text.startswith("turn on") or text.startswith("switch on"):
        action = "on"
        remainder = text[7:].strip()
    elif text.startswith("turn off") or text.startswith("switch off"):
        action = "off"
        remainder = text[8:].strip()
    elif text.startswith("toggle ") or text == "toggle":
        action = "toggle"
        remainder = text[6:].strip()
    elif text.startswith("on "):
        action = "on"
        remainder = text[3:].strip()
    elif text.startswith("off "):
        action = "off"
        remainder = text[4:].strip()
    elif any(text.startswith(p) for p in ("lower ", "decrease ", "dim ", "turn down ", "slow down ", "drop ")):
        action = "decrease"
        for p in ("lower ", "decrease ", "dim ", "turn down ", "slow down ", "drop "):
            if text.startswith(p):
                remainder = text[len(p):].strip()
                break
    elif any(text.startswith(p) for p in ("raise ", "increase ", "brighten ", "turn up ", "speed up ", "boost ")):
        action = "increase"
        for p in ("raise ", "increase ", "brighten ", "turn up ", "speed up ", "boost "):
            if text.startswith(p):
                remainder = text[len(p):].strip()
                break
    else:
        m_on = re.search(r"\b(turn on|switch on|enable|start)\b", text)
        m_off = re.search(r"\b(turn off|switch off|disable|stop)\b", text)
        m_tog = re.search(r"\b(toggle|flip)\b", text)
        m_dec = re.search(r"\b(lower|decrease|dim|turn down|slow down|drop)\b", text)
        m_inc = re.search(r"\b(raise|increase|brighten|turn up|speed up|boost)\b", text)
        if m_on:
            action = "on"
            remainder = (text[:m_on.start()] + " " + text[m_on.end():]).strip()
        elif m_off:
            action = "off"
            remainder = (text[:m_off.start()] + " " + text[m_off.end():]).strip()
        elif m_tog:
            action = "toggle"
            remainder = (text[:m_tog.start()] + " " + text[m_tog.end():]).strip()
        elif m_dec:
            action = "decrease"
            remainder = (text[:m_dec.start()] + " " + text[m_dec.end():]).strip()
        elif m_inc:
            action = "increase"
            remainder = (text[:m_inc.start()] + " " + text[m_inc.end():]).strip()
        else:
            raise ClientError(f"Could not infer action from phrase: '{phrase}'")

    raw_targets = re.split(r"\b(?:and|as well as|with)\b|[,&+]", remainder)
    raw_cleaned: list[str] = []
    for t in raw_targets:
        clean = re.sub(r"\b(?:the|my|all|both|please|speed|level|brightness)\b", " ", t).strip()
        clean = " ".join(clean.split())
        if clean:
            raw_cleaned.append(clean)

    if not raw_cleaned:
        raise ClientError(f"Could not identify target devices from phrase: '{phrase}'")

    # Contextual location propagation (e.g., "upstairs fan and [fan] light")
    index = load_device_index()
    aliases = index.get("aliases", {})
    groups = index.get("groups", {})
    known_locations = ("upstairs", "downstairs", "living_room", "kitchen", "outdoor", "desk")

    targets: list[str] = []
    last_location = None
    last_had_fan = False

    for t in raw_cleaned:
        t_slug = t.replace(" ", "_").replace("-", "_")
        found_loc = next((loc for loc in known_locations if loc in t_slug), None)
        if found_loc:
            last_location = found_loc
            last_had_fan = "fan" in t_slug
            targets.append(t)
            continue

        # If no explicit location, but previous target had a location
        if last_location:
            candidate = f"{last_location}_{t_slug}"
            candidate_fan = f"{last_location}_fan_{t_slug}" if last_had_fan and "fan" not in t_slug else None
            if candidate_fan and (candidate_fan in aliases or candidate_fan in groups):
                targets.append(candidate_fan)
                continue
            if candidate in aliases or candidate in groups:
                targets.append(candidate)
                continue

        targets.append(t)

    return action, targets


def load_credentials() -> tuple[str, str]:
    """Resolves Home Assistant base URL and token from env, config file, or legacy profile."""
    url = os.environ.get("HOME_ASSISTANT_URL", "").strip()
    token = os.environ.get("HOME_ASSISTANT_TOKEN", "").strip()

    if url and token:
        return url, token

    # Check ~/.config/hades/home-assistant.json
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = url or data.get("HOME_ASSISTANT_URL", "").strip()
                token = token or data.get("HOME_ASSISTANT_TOKEN", "").strip()
        except Exception:
            pass

    if not url or not token:
        raise ClientError(
            "Home Assistant credentials missing. Provide HOME_ASSISTANT_URL and "
            "HOME_ASSISTANT_TOKEN via environment or ~/.config/hades/home-assistant.json"
        )

    return url, token


def load_fallback_urls() -> list[str]:
    raw = os.environ.get("HOME_ASSISTANT_FALLBACK_URLS") or os.environ.get("HOME_ASSISTANT_FALLBACK_URL", "")
    urls = [u.strip() for u in raw.split(",") if u.strip()]
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                fb = data.get("HOME_ASSISTANT_FALLBACK_URL") or data.get("HOME_ASSISTANT_FALLBACK_URLS")
                if isinstance(fb, list):
                    urls.extend(str(u).strip() for u in fb if str(u).strip())
                elif isinstance(fb, str) and fb.strip():
                    urls.extend(u.strip() for u in fb.split(",") if u.strip())
        except Exception:
            pass
    return list(dict.fromkeys(urls))


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str, timeout_seconds: float = 30.0, fallback_urls: list[str] | None = None):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ClientError("HOME_ASSISTANT_URL must be an http or https URL")
        if parsed.query or parsed.fragment:
            raise ClientError("HOME_ASSISTANT_URL must not contain a query or fragment")
        if not token:
            raise ClientError("HOME_ASSISTANT_TOKEN is required")
        self.base_url = base_url.rstrip("/")
        self.api_root = f"{self.base_url}/api"
        self.token = token
        self.timeout = timeout_seconds
        self.fallback_urls = [u.rstrip("/") for u in (fallback_urls or []) if u and u.rstrip("/") != self.base_url]

    def request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> Any:
        if not endpoint.startswith("/") or urlsplit(endpoint).scheme:
            raise ClientError("API endpoint must begin with / and cannot be an absolute URL")
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "HADES-Home-Assistant/1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"

        urls_to_try = [self.api_root] + [f"{fb}/api" for fb in self.fallback_urls]
        last_error = None

        for api_root in urls_to_try:
            try:
                with urlopen(
                    Request(f"{api_root}{endpoint}", data=body, headers=headers, method=method),
                    timeout=self.timeout,
                ) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                self.api_root = api_root
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw
            except HTTPError as error:
                detail = redact(error.read().decode("utf-8", errors="replace").strip(), self.token)[:1000]
                suffix = f": {detail}" if detail else ""
                raise ClientError(f"Home Assistant returned HTTP {error.code}{suffix}") from None
            except URLError as error:
                last_error = error
                continue

        if last_error:
            raise ClientError(
                f"Could not reach Home Assistant: {redact(str(last_error.reason), self.token)}"
            ) from None

    def status(self) -> dict[str, Any]:
        return {"api": self.request("GET", "/"), "config": self.request("GET", "/config")}

    def config(self) -> dict[str, Any]:
        return self.request("GET", "/config")

    def resolve_target(self, target: str, auto_discover: bool = True) -> list[tuple[str, str]]:
        index = load_device_index()
        aliases = index.get("aliases", {})
        groups = index.get("groups", {})
        devices = index.get("devices", {})

        target_clean = target.lower().strip().replace(" ", "_").replace("-", "_")

        # 1. Check groups
        if target_clean in groups:
            res = []
            for eid in groups[target_clean]:
                dom = devices.get(eid, {}).get("domain") or eid.split(".", 1)[0]
                res.append((dom, eid))
            return res

        # 2. Check aliases
        if target_clean in aliases:
            eid = aliases[target_clean]
            dom = devices.get(eid, {}).get("domain") or eid.split(".", 1)[0]
            return [(dom, eid)]

        # 2b. Check singular/plural variations or stripping common suffixes
        for suffix in ("_lights", "_light", "_switches", "_switch", "_fans", "_fan"):
            if target_clean.endswith(suffix):
                stem = target_clean[:-len(suffix)]
                if stem in aliases:
                    eid = aliases[stem]
                    dom = devices.get(eid, {}).get("domain") or eid.split(".", 1)[0]
                    return [(dom, eid)]
                if stem in groups:
                    res = []
                    for eid in groups[stem]:
                        dom = devices.get(eid, {}).get("domain") or eid.split(".", 1)[0]
                        res.append((dom, eid))
                    return res

        # 3. Check exact entity_id with domain
        if "." in target:
            dom, _, _ = target.partition(".")
            return [(dom, target)]

        # 4. Check friendly name match in local devices
        for eid, info in devices.items():
            name = (info.get("name") or "").lower().replace(" ", "_").replace("-", "_")
            if target_clean == name:
                dom = info.get("domain") or eid.split(".", 1)[0]
                return [(dom, eid)]

        # 4b. Check controllable domain substring match
        controllable_domains = {"light", "switch", "fan", "climate", "media_player", "cover", "lock"}
        for eid, info in devices.items():
            dom = info.get("domain") or eid.split(".", 1)[0]
            if dom in controllable_domains:
                name = (info.get("name") or "").lower().replace(" ", "_").replace("-", "_")
                if target_clean in name or name in target_clean:
                    return [(dom, eid)]

        # 5. On-demand search from Home Assistant if not found locally
        if auto_discover:
            try:
                all_states = self.states()
                matched_eid = None
                matched_domain = None
                matched_name = None

                for s in all_states:
                    eid = s.get("entity_id", "")
                    fname = (s.get("attributes", {}).get("friendly_name") or "").lower()
                    dom = eid.split(".", 1)[0]
                    short = eid.split(".", 1)[-1].lower()

                    if target_clean in {eid.lower(), short}:
                        matched_eid = eid
                        matched_domain = dom
                        matched_name = s.get("attributes", {}).get("friendly_name") or eid
                        break
                    if fname and target_clean == fname.replace(" ", "_").replace("-", "_"):
                        matched_eid = eid
                        matched_domain = dom
                        matched_name = s.get("attributes", {}).get("friendly_name") or eid
                        break

                if not matched_eid:
                    for s in all_states:
                        eid = s.get("entity_id", "")
                        fname = (s.get("attributes", {}).get("friendly_name") or "").lower()
                        dom = eid.split(".", 1)[0]
                        short = eid.split(".", 1)[-1].lower()
                        if dom in controllable_domains and (target_clean in short or (fname and target_clean in fname)):
                            matched_eid = eid
                            matched_domain = dom
                            matched_name = s.get("attributes", {}).get("friendly_name") or eid
                            break

                if matched_eid:
                    if target_clean not in {"light", "lights", "fan", "fans", "switch", "switches"} and matched_domain in controllable_domains:
                        index["aliases"][target_clean] = matched_eid
                        index["devices"][matched_eid] = {
                            "domain": matched_domain,
                            "name": matched_name,
                        }
                        save_device_index(index)
                    return [(matched_domain, matched_eid)]
            except Exception:
                pass

        raise ClientError(f"Unknown device, group, or alias: '{target}'. Run 'ha sync' or 'ha devices'.")

    def state(self, entity: str) -> dict[str, Any]:
        targets = self.resolve_target(entity, auto_discover=True)
        if len(targets) == 1:
            _, eid = targets[0]
            return self.request("GET", f"/states/{eid}")
        return {
            eid: self.request("GET", f"/states/{eid}")
            for _, eid in targets
        }

    def state_targets(self, targets: list[str]) -> dict[str, Any]:
        resolved_pairs: list[tuple[str, str]] = []
        for t in targets:
            pairs = self.resolve_target(t, auto_discover=True)
            for pair in pairs:
                if pair not in resolved_pairs:
                    resolved_pairs.append(pair)
        if len(resolved_pairs) == 1:
            _, eid = resolved_pairs[0]
            return self.request("GET", f"/states/{eid}")
        return {
            eid: self.request("GET", f"/states/{eid}")
            for _, eid in resolved_pairs
        }

    def states(self, domain_filter: str | None = None) -> list[dict[str, Any]]:
        all_states = self.request("GET", "/states")
        if not isinstance(all_states, list):
            return []
        if domain_filter:
            return [s for s in all_states if s.get("entity_id", "").split(".", 1)[0] == domain_filter]
        return all_states

    def services(self) -> list[dict[str, Any]]:
        return self.request("GET", "/services")

    def errors(self) -> str:
        return self.request("GET", "/error_log")

    def check_config(self) -> dict[str, Any]:
        return self.request("POST", "/config/core/check_config")

    def wait_for_state(
        self,
        entity: str,
        expected_state: str,
        timeout_seconds: float = 3.0,
        poll_interval: float = 0.15,
    ) -> tuple[dict[str, Any], bool]:
        start_time = time.time()
        last_state: dict[str, Any] = {}
        while True:
            try:
                last_state = self.request("GET", f"/states/{entity}")
                if isinstance(last_state, dict) and last_state.get("state") == expected_state:
                    return last_state, True
            except Exception:
                pass
            if time.time() - start_time >= timeout_seconds:
                break
            time.sleep(poll_interval)
        return last_state, False

    def call(
        self,
        domain: str,
        service: str,
        entity: str,
        data: dict[str, Any] | None = None,
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        payload = {**(data or {}), "entity_id": entity}
        result = self.request("POST", f"/services/{domain}/{service}", payload)
        verified = None
        if verify and service in {"turn_on", "turn_off"}:
            expected = "on" if service == "turn_on" else "off"
            new_state, verified = self.wait_for_state(entity, expected, timeout_seconds=verify_timeout)
        else:
            new_state = self.request("GET", f"/states/{entity}")
        res: dict[str, Any] = {"service_result": result, "state": new_state}
        if verified is not None:
            res["verified"] = verified
        return res

    def upstairs(self, action: str, verify: bool = True) -> dict[str, Any]:
        if action not in {"on", "off"}:
            raise ClientError("Action for upstairs must be 'on' or 'off'")
        return self.toggle_targets(action, ["upstairs"], verify=verify)

    def downstairs(self, action: str, verify: bool = True) -> dict[str, Any]:
        if action not in {"on", "off"}:
            raise ClientError("Action for downstairs must be 'on' or 'off'")
        return self.toggle_targets(action, ["downstairs"], verify=verify)

    def _resolve_target_pairs(self, targets: list[str]) -> list[tuple[str, str]]:
        resolved_pairs: list[tuple[str, str]] = []
        for t in targets:
            pairs = self.resolve_target(t, auto_discover=True)
            for pair in pairs:
                if pair not in resolved_pairs:
                    resolved_pairs.append(pair)
        if not resolved_pairs:
            raise ClientError(f"No valid entities resolved from targets: {targets}")
        return resolved_pairs

    def toggle_targets(
        self,
        action: str,
        targets: list[str],
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        if action not in {"on", "off", "toggle"}:
            raise ClientError("Action must be 'on', 'off', or 'toggle'")
        service = "toggle" if action == "toggle" else f"turn_{action}"

        resolved_pairs = self._resolve_target_pairs(targets)

        if len(resolved_pairs) == 1:
            domain, eid = resolved_pairs[0]
            return self.call(domain, service, eid, verify=verify, verify_timeout=verify_timeout)

        results: dict[str, Any] = {}
        def _call_one(d: str, e: str) -> tuple[str, dict[str, Any]]:
            return e, self.call(d, service, e, verify=verify, verify_timeout=verify_timeout)

        with ThreadPoolExecutor(max_workers=min(len(resolved_pairs), 8)) as pool:
            futures = [pool.submit(_call_one, d, e) for d, e in resolved_pairs]
            for f in futures:
                eid, res = f.result()
                results[eid] = res
        return results

    def adjust_targets(
        self,
        direction: str,
        targets: list[str],
        step: int = 20,
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        resolved_pairs = self._resolve_target_pairs(targets)
        results: dict[str, Any] = {}
        for domain, eid in resolved_pairs:
            old_state = {}
            try:
                old_state = self.request("GET", f"/states/{eid}")
            except Exception:
                pass
            old_pct = old_state.get("attributes", {}).get("percentage") if isinstance(old_state, dict) else None

            if domain == "fan":
                feat = old_state.get("attributes", {}).get("supported_features", 0) if isinstance(old_state, dict) else 0
                if feat and not (feat & 1):
                    modes = old_state.get("attributes", {}).get("preset_modes", [])
                    raise ClientError(f"Fan '{eid}' does not support variable speed adjustment (supported presets: {modes})")
                srv = "decrease_speed" if direction == "decrease" else "increase_speed"
                res = self.call("fan", srv, eid, data={"percentage_step": step}, verify=False)
            elif domain == "light":
                step_pct = -step if direction == "decrease" else step
                res = self.call("light", "turn_on", eid, data={"brightness_step_pct": step_pct}, verify=False)
            else:
                srv = "turn_off" if direction == "decrease" else "turn_on"
                res = self.call(domain, srv, eid, verify=verify, verify_timeout=verify_timeout)

            new_st = old_state
            start_t = time.time()
            while time.time() - start_t < 1.5:
                time.sleep(0.25)
                try:
                    new_st = self.request("GET", f"/states/{eid}")
                    new_pct = new_st.get("attributes", {}).get("percentage") if isinstance(new_st, dict) else None
                    if new_pct != old_pct:
                        break
                except Exception:
                    pass
            res["state"] = new_st
            results[eid] = res

        if len(resolved_pairs) == 1:
            return results[resolved_pairs[0][1]]
        return results

    def set_level_targets(
        self,
        level: int,
        targets: list[str],
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        resolved_pairs = self._resolve_target_pairs(targets)
        results: dict[str, Any] = {}
        for domain, eid in resolved_pairs:
            old_state = {}
            try:
                old_state = self.request("GET", f"/states/{eid}")
            except Exception:
                pass

            if domain == "fan":
                feat = old_state.get("attributes", {}).get("supported_features", 0) if isinstance(old_state, dict) else 0
                if feat and not (feat & 1):
                    modes = old_state.get("attributes", {}).get("preset_modes", [])
                    raise ClientError(f"Fan '{eid}' does not support variable percentage speeds (supported presets: {modes})")
                if level <= 0:
                    res = self.call("fan", "turn_off", eid, verify=verify, verify_timeout=verify_timeout)
                else:
                    res = self.call("fan", "set_percentage", eid, data={"percentage": level}, verify=False)
            elif domain == "light":
                if level <= 0:
                    res = self.call("light", "turn_off", eid, verify=verify, verify_timeout=verify_timeout)
                else:
                    res = self.call("light", "turn_on", eid, data={"brightness_pct": level}, verify=False)
            else:
                srv = "turn_on" if level > 0 else "turn_off"
                res = self.call(domain, srv, eid, verify=verify, verify_timeout=verify_timeout)

            new_st = old_state
            start_t = time.time()
            while time.time() - start_t < 1.5:
                time.sleep(0.25)
                try:
                    new_st = self.request("GET", f"/states/{eid}")
                    new_pct = new_st.get("attributes", {}).get("percentage") if isinstance(new_st, dict) else None
                    if new_pct == level:
                        break
                except Exception:
                    pass
            res["state"] = new_st
            results[eid] = res

        if len(resolved_pairs) == 1:
            return results[resolved_pairs[0][1]]
        return results

    def snapshot(self, target: str = "doorbell", output_path: str | None = None) -> dict[str, Any]:
        resolved = self.resolve_target(target, auto_discover=True)
        cam_pair = next(((d, e) for d, e in resolved if d == "camera"), None)
        if not cam_pair:
            cam_pair = resolved[0] if resolved else ("camera", target if "." in target else f"camera.{target}")

        domain, entity_id = cam_pair
        short_name = entity_id.replace("camera.", "").replace("_live_view", "").replace("casco_", "")

        if not output_path:
            ts = int(time.time())
            output_dir = Path("/tmp")
            output_path = str(output_dir / f"hades_{short_name}_{ts}.jpg")

        out_file = Path(output_path).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        url = f"{self.api_root}/camera_proxy/{entity_id}"
        req = Request(url, headers={"Authorization": f"Bearer {self.token}"})

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                out_file.write_bytes(data)
        except Exception as e:
            raise ClientError(f"Failed to capture snapshot from {entity_id}: {e}")

        size_kb = round(len(data) / 1024, 1)
        return {
            "entity_id": entity_id,
            "file_path": str(out_file),
            "size_bytes": len(data),
            "size_kb": size_kb,
            "format": "jpeg",
        }

    def ptz(self, target: str, direction: str) -> dict[str, Any]:
        dir_clean = direction.lower().strip()
        if dir_clean not in {"left", "right", "up", "down"}:
            raise ClientError(f"PTZ direction must be 'left', 'right', 'up', or 'down', got '{direction}'")

        cam_target = target.lower().strip().replace("_camera", "").replace("_cam", "")
        btn_name = f"button.{cam_target}_pan_{dir_clean}" if dir_clean in {"left", "right"} else f"button.{cam_target}_tilt_{dir_clean}"
        return self.call("button", "press", btn_name, verify=False)

    def press(self, target: str) -> dict[str, Any]:
        resolved = self.resolve_target(target, auto_discover=True)
        btn_pair = next(((d, e) for d, e in resolved if d == "button"), None)
        if not btn_pair:
            btn_pair = resolved[0] if resolved else ("button", target if "." in target else f"button.{target}")
        domain, eid = btn_pair
        return self.call(domain, "press", eid, verify=False)

    def preset(self, target: str, mode: str) -> dict[str, Any]:
        resolved = self.resolve_target(target, auto_discover=True)
        fan_pair = next(((d, e) for d, e in resolved if d == "fan"), None)
        if not fan_pair:
            fan_pair = resolved[0] if resolved else ("fan", target if "." in target else f"fan.{target}")
        domain, eid = fan_pair
        res = self.call("fan", "set_preset_mode", eid, data={"preset_mode": mode}, verify=False)
        time.sleep(0.5)
        try:
            res["state"] = self.request("GET", f"/states/{eid}")
        except Exception:
            pass
        return res

    def media(self, action: str, target: str = "tv", value: Any = None) -> dict[str, Any]:
        resolved = self.resolve_target(target, auto_discover=True)
        mp_pair = next(((d, e) for d, e in resolved if d == "media_player"), None)
        if not mp_pair:
            mp_pair = resolved[0] if resolved else ("media_player", target if "." in target else f"media_player.{target}")
        domain, eid = mp_pair

        act_clean = action.lower().strip()
        data: dict[str, Any] = {}
        if act_clean in {"play", "resume"}:
            svc = "media_play"
        elif act_clean == "pause":
            svc = "media_pause"
        elif act_clean == "play_pause":
            svc = "media_play_pause"
        elif act_clean == "stop":
            svc = "media_stop"
        elif act_clean in {"next", "skip"}:
            svc = "media_next_track"
        elif act_clean in {"prev", "previous", "back"}:
            svc = "media_previous_track"
        elif act_clean == "mute":
            svc = "volume_mute"
            data["is_volume_muted"] = True
        elif act_clean == "unmute":
            svc = "volume_mute"
            data["is_volume_muted"] = False
        elif act_clean in {"volume_up", "volup"}:
            svc = "volume_up"
        elif act_clean in {"volume_down", "voldown"}:
            svc = "volume_down"
        elif act_clean in {"volume", "set_volume"}:
            if value is None:
                raise ClientError("Volume level required (0-100, 'up', or 'down')")
            val_str = str(value).lower().strip()
            if val_str in {"up", "higher"}:
                svc = "volume_up"
            elif val_str in {"down", "lower"}:
                svc = "volume_down"
            elif val_str.rstrip("%").isdigit():
                svc = "volume_set"
                pct = max(0, min(100, int(val_str.rstrip("%"))))
                data["volume_level"] = pct / 100.0
            else:
                raise ClientError(f"Invalid volume value '{value}'. Use 0-100, 'up', or 'down'.")
        else:
            raise ClientError(f"Unsupported media action '{action}'. Use play, pause, stop, next, prev, mute, unmute, volume.")

        return self.call("media_player", svc, eid, data=data, verify=False)

    def color(self, target: str, color_val: str, verify: bool = True) -> dict[str, Any]:
        resolved = self._resolve_target_pairs([target])
        results: dict[str, Any] = {}
        color_clean = color_val.strip().lower()

        for domain, eid in resolved:
            data: dict[str, Any] = {}
            if color_clean.startswith("#") and len(color_clean) in (4, 7):
                hex_str = color_clean.lstrip("#")
                if len(hex_str) == 3:
                    hex_str = "".join([c * 2 for c in hex_str])
                r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
                data["rgb_color"] = [r, g, b]
            elif color_clean in {"warm_white", "warm white"}:
                data["color_temp_kelvin"] = 2700
            elif color_clean in {"cool_white", "cool white"}:
                data["color_temp_kelvin"] = 5000
            elif color_clean in {"daylight", "natural"}:
                data["color_temp_kelvin"] = 4000
            else:
                data["color_name"] = color_clean

            res = self.call(domain, "turn_on", eid, data=data, verify=verify)
            results[eid] = res

        if len(resolved) == 1:
            return results[resolved[0][1]]
        return results

    def weather(self) -> dict[str, Any]:
        try:
            return self.request("GET", "/states/weather.forecast_home")
        except Exception:
            states = self.states("weather")
            if states:
                return states[0]
            raise ClientError("No weather entity found in Home Assistant")

    def presence(self) -> dict[str, Any]:
        persons = self.states("person")
        zones = self.states("zone")
        home_zone = next((z for z in zones if z.get("entity_id") == "zone.home"), None)
        return {
            "persons": persons,
            "home_zone": home_zone,
        }

    def toggle_target(
        self,
        action: str,
        target: str,
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        return self.toggle_targets(action, [target], verify=verify, verify_timeout=verify_timeout)

    def act(
        self,
        phrase: str,
        verify: bool = True,
        verify_timeout: float = 3.0,
    ) -> dict[str, Any]:
        action, targets = parse_intent(phrase)
        if action in {"on", "off", "toggle"}:
            return self.toggle_targets(action, targets, verify=verify, verify_timeout=verify_timeout)
        elif action in {"decrease", "lower", "dim"}:
            return self.adjust_targets("decrease", targets, verify=verify, verify_timeout=verify_timeout)
        elif action in {"increase", "raise", "brighten"}:
            return self.adjust_targets("increase", targets, verify=verify, verify_timeout=verify_timeout)
        elif action.startswith("set:"):
            level = int(action.split(":")[1])
            return self.set_level_targets(level, targets, verify=verify, verify_timeout=verify_timeout)
        elif action == "snapshot":
            tgt = targets[0] if targets else "doorbell"
            return self.snapshot(tgt)
        elif action in {"play", "pause", "stop", "mute", "unmute"}:
            tgt = targets[0] if targets else "tv"
            return self.media(action, tgt)
        elif action.startswith("color:"):
            col = action.split(":", 1)[1]
            return self.color(targets[0], col, verify=verify)
        elif action == "weather":
            return self.weather()
        elif action == "presence":
            return self.presence()
        raise ClientError(f"Unsupported action '{action}' parsed from phrase: '{phrase}'")

    def sync_index(self) -> dict[str, Any]:
        all_states = self.states()
        index = load_device_index()
        devices = index.setdefault("devices", {})
        aliases = index.setdefault("aliases", {})
        groups = index.setdefault("groups", {})

        count_added = 0
        for s in all_states:
            eid = s.get("entity_id", "")
            if not eid or "." not in eid:
                continue
            dom, _, short_name = eid.partition(".")
            fname = s.get("attributes", {}).get("friendly_name")
            devices[eid] = {
                "domain": dom,
                "name": fname or short_name,
            }
            if short_name not in aliases:
                aliases[short_name] = eid
                count_added += 1
            if fname:
                slug = re.sub(r"[^a-z0-9_]+", "_", fname.lower()).strip("_")
                if slug and slug not in aliases:
                    aliases[slug] = eid
                    count_added += 1

        save_device_index(index)
        return {
            "total_devices": len(devices),
            "total_aliases": len(aliases),
            "total_groups": len(groups),
            "new_aliases_added": count_added,
            "index_path": str(INDEX_FILE),
        }


def sanitize(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return redact(value, secret)
    if isinstance(value, list):
        return [sanitize(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, secret) for key, item in value.items()}
    return value


def format_brief(command: str, result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        lines = []
        for item in result:
            if isinstance(item, dict) and "entity_id" in item:
                eid = item.get("entity_id", "")
                st = item.get("state", "")
                name = item.get("attributes", {}).get("friendly_name")
                name_str = f" ({name})" if name else ""
                lines.append(f"{eid}: {st}{name_str}")
            else:
                lines.append(str(item))
        return "\n".join(lines) if lines else "No entities found."
    if isinstance(result, dict):
        def _extract_summary(st_obj: Any, verified: bool | None = None) -> str:
            st = st_obj
            attrs: dict[str, Any] = {}
            if isinstance(st_obj, dict):
                attrs = st_obj.get("attributes", {})
                st = st_obj.get("state", "")
            details = []
            pct = attrs.get("percentage")
            bri = attrs.get("brightness")
            preset = attrs.get("preset_mode")
            if pct is not None:
                details.append(f"speed {pct}%")
            if bri is not None:
                bri_pct = round(bri / 255 * 100)
                details.append(f"brightness {bri_pct}%")
            if preset is not None:
                details.append(f"preset {preset}")
            det_str = f" ({', '.join(details)})" if details else ""
            if verified is True:
                return f"{st}{det_str} (verified)"
            elif verified is False:
                return f"{st}{det_str} (unconfirmed)"
            return f"{st}{det_str}"

        # Snapshot result
        if "file_path" in result and "size_kb" in result:
            eid = result.get("entity_id", "camera")
            return f"{eid}: snapshot saved to {result['file_path']} ({result['size_kb']} KB)"

        # Weather result
        if result.get("entity_id", "").startswith("weather."):
            attrs = result.get("attributes", {})
            st = result.get("state", "unknown")
            temp = attrs.get("temperature", "--")
            unit = attrs.get("temperature_unit", "°F")
            hum = attrs.get("humidity", "--")
            uv = attrs.get("uv_index", "--")
            wind = attrs.get("wind_speed", "--")
            wind_u = attrs.get("wind_speed_unit", "mph")
            return f"Weather: {st}, {temp}{unit}, {hum}% humidity, UV {uv}, wind {wind} {wind_u}"

        # Presence result
        if "persons" in result and "home_zone" in result:
            lines = []
            for p in result.get("persons", []):
                name = p.get("attributes", {}).get("friendly_name") or p.get("entity_id")
                st = p.get("state", "unknown")
                lines.append(f"{name}: {st}")
            zone_st = result.get("home_zone", {}).get("state", "0") if result.get("home_zone") else "0"
            lines.append(f"Zone Home: {zone_st} present")
            return " | ".join(lines)

        # Multi-entity results (upstairs, downstairs, multi on/off, act)
        if result and all(isinstance(v, dict) for v in result.values()):
            lines = []
            for k, v in sorted(result.items()):
                st_val = v.get("state")
                ver = v.get("verified")
                lines.append(f"{k}: {_extract_summary(st_val, ver)}")
            return "\n".join(lines)
        # Single entity call result: {"service_result": ..., "state": {"entity_id": ..., "state": ...}}
        if "state" in result and isinstance(result["state"], dict):
            eid = result["state"].get("entity_id", "")
            st_val = result["state"]
            ver = result.get("verified")
            return f"{eid}: {_extract_summary(st_val, ver)}"
        # Single entity state: {"entity_id": ..., "state": ...}
        if "entity_id" in result and "state" in result:
            return f"{result['entity_id']}: {_extract_summary(result)}"
        return json.dumps(result, indent=2, sort_keys=True)
    return str(result)


def format_devices(index: dict[str, Any], domain_filter: str | None = None) -> str:
    aliases = index.get("aliases", {})
    groups = index.get("groups", {})
    devices = index.get("devices", {})

    lines = ["=== HADES Device Index ===", ""]
    if not domain_filter and groups:
        lines.append("Groups:")
        for g, members in sorted(groups.items()):
            lines.append(f"  {g:15} -> {', '.join(members)}")
        lines.append("")

    lines.append("Common Aliases:")
    for a, eid in sorted(aliases.items()):
        dom = devices.get(eid, {}).get("domain") or eid.split(".", 1)[0]
        if domain_filter and dom != domain_filter:
            continue
        dev_name = devices.get(eid, {}).get("name", "")
        desc = f" ({dev_name})" if dev_name else ""
        lines.append(f"  {a:20} -> {eid}{desc}")

    lines.append("")
    lines.append(f"Total: {len(devices)} devices, {len(aliases)} aliases | File: {INDEX_FILE}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--timeout", type=timeout, default=30.0, help="Request timeout in seconds")
    common.add_argument("--json", action="store_true", help="Print full JSON output instead of concise summary")
    common.add_argument("--brief", "-b", action="store_true", help="Print brief summary (default for actions)")

    root = argparse.ArgumentParser(
        prog="ha",
        parents=[common],
        description="HADES Home Assistant REST API CLI",
    )

    sub = root.add_subparsers(dest="command", required=True)

    sub.add_parser("status", parents=[common], help="Check Home Assistant connectivity and server info")
    sub.add_parser("config", parents=[common], help="Get Home Assistant configuration")

    p_devs = sub.add_parser("devices", parents=[common], help="List indexed devices, aliases, and groups")
    p_devs.add_argument("--domain", type=identifier, default=None, help="Filter devices by domain")

    sub.add_parser("sync", parents=[common], help="Sync and index all devices from Home Assistant")

    p_alias = sub.add_parser("alias", parents=[common], help="View or bind custom aliases")
    p_alias.add_argument("name", nargs="?", default=None, help="Alias name (e.g. lamp, porch)")
    p_alias.add_argument("target", nargs="?", default=None, help="Target entity ID (e.g. switch.living_room)")

    p_state = sub.add_parser("state", parents=[common], help="Get state of an entity, group, or alias")
    p_state.add_argument("targets", nargs="+", type=target_arg, help="Target entity ID(s), group(s), or alias(es)")

    p_states = sub.add_parser("states", parents=[common], help="List all states, optionally filtered by domain")
    p_states.add_argument("--domain", type=identifier, default=None, help="Domain filter (e.g. light, fan)")

    sub.add_parser("services", parents=[common], help="List available services")
    sub.add_parser("errors", parents=[common], help="Read Home Assistant error logs")
    sub.add_parser("check-config", parents=[common], help="Run Home Assistant configuration verification")

    p_call = sub.add_parser("call", parents=[common], help="Call a service and read back new state")
    p_call.add_argument("domain", type=identifier, help="Service domain (e.g. light, fan, switch)")
    p_call.add_argument("service", type=identifier, help="Service name (e.g. turn_on, turn_off, toggle)")
    p_call.add_argument("--entity", required=True, dest="entity_id", type=entity_id, help="Target entity ID")
    p_call.add_argument("--data", type=json_object, default={}, help="Optional JSON data object")
    p_call.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_up = sub.add_parser("upstairs", parents=[common], help="Control upstairs ceiling fan and light shortcut")
    p_up.add_argument("action", choices=["on", "off", "state"], help="Action to perform")
    p_up.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_down = sub.add_parser("downstairs", parents=[common], help="Control downstairs switches shortcut")
    p_down.add_argument("action", choices=["on", "off", "state"], help="Action to perform")
    p_down.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_on = sub.add_parser("on", parents=[common], help="Turn on entity, group, or alias (with auto-verification)")
    p_on.add_argument("targets", nargs="+", type=target_arg, help="Target entity ID(s), group(s), or alias(es)")
    p_on.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_off = sub.add_parser("off", parents=[common], help="Turn off entity, group, or alias (with auto-verification)")
    p_off.add_argument("targets", nargs="+", type=target_arg, help="Target entity ID(s), group(s), or alias(es)")
    p_off.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_toggle = sub.add_parser("toggle", parents=[common], help="Toggle entity, group, or alias (with auto-verification)")
    p_toggle.add_argument("targets", nargs="+", type=target_arg, help="Target entity ID(s), group(s), or alias(es)")
    p_toggle.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_speed = sub.add_parser("speed", parents=[common], help="Adjust speed of a fan or dimmer")
    p_speed.add_argument("target", type=target_arg, help="Entity ID or alias (e.g. upstairs_fan)")
    p_speed.add_argument("level", help="Action ('lower', 'raise') or target percentage (0-100)")
    p_speed.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_act = sub.add_parser("act", parents=[common], help="Parse natural action phrase and execute deterministically")
    p_act.add_argument("phrase", nargs="+", help="Natural action phrase, e.g. 'turn on upstairs fan and fan light'")
    p_act.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    p_snap = sub.add_parser("snapshot", parents=[common], help="Capture camera snapshot")
    p_snap.add_argument("target", nargs="?", default="doorbell", help="Camera entity ID or alias (default: doorbell)")
    p_snap.add_argument("output", nargs="?", default=None, help="Optional destination file path")

    p_ptz = sub.add_parser("ptz", parents=[common], help="Pan or tilt camera")
    p_ptz.add_argument("target", help="Camera name (e.g. upstairs, downstairs)")
    p_ptz.add_argument("direction", choices=["left", "right", "up", "down"], help="Direction")

    p_med = sub.add_parser("media", parents=[common], help="Control media players")
    p_med.add_argument("action", help="Action: play, pause, stop, next, prev, mute, unmute, volume")
    p_med.add_argument("target", nargs="?", default="tv", help="Target media player (e.g. tv, soundbar)")
    p_med.add_argument("value", nargs="?", default=None, help="Optional value for volume")

    p_col = sub.add_parser("color", parents=[common], help="Change light color or color temperature")
    p_col.add_argument("target", help="Light entity ID or alias")
    p_col.add_argument("color", help="Color name (e.g. red, blue, warm_white) or #HEX")
    p_col.add_argument("--no-verify", action="store_true", help="Skip programmatic state verification")

    sub.add_parser("weather", parents=[common], help="Get current local weather and forecast")
    sub.add_parser("presence", parents=[common], help="Check presence and location of occupants")

    p_press = sub.add_parser("press", parents=[common], help="Press a button entity")
    p_press.add_argument("target", help="Button entity ID or alias")

    p_pre = sub.add_parser("preset", parents=[common], help="Set fan preset mode (e.g. sleep, smart, nature, fresh)")
    p_pre.add_argument("target", help="Fan entity ID or alias")
    p_pre.add_argument("mode", help="Preset mode name")

    return root


def main(arguments: list[str] | None = None) -> int:
    args_list = sys.argv[1:] if arguments is None else arguments

    # Handle natural phrasing shortcuts, e.g. "ha turn on upstairs fan and fan light"
    if args_list and args_list[0] in {
        "turn", "turn_on", "turn_off", "switch",
        "lower", "decrease", "raise", "increase",
        "dim", "brighten", "slow"
    }:
        args_list = ["act", " ".join(args_list)]
    elif args_list and args_list[0] == "speed" and (len(args_list) > 3 or any(k in args_list for k in ("and", "&", "the", "upstairs", "downstairs"))):
        args_list = ["act", " ".join(args_list)]
    elif args_list and args_list[0] in {"on", "off", "toggle"} and len(args_list) > 2 and any(k in args_list for k in ("and", "&", "the")):
        args_list = ["act", " ".join(args_list)]
    elif args_list and args_list[0] in {"pause", "play", "stop", "mute", "unmute"}:
        target = args_list[1] if len(args_list) > 1 else "tv"
        args_list = ["media", args_list[0], target]

    try:
        parser = build_parser()
        args = parser.parse_args(args_list)

        if args.command == "devices":
            index = load_device_index()
            if getattr(args, "brief", False):
                lines = [f"{a}: {eid}" for a, eid in sorted(index.get("aliases", {}).items())]
                print("\n".join(lines))
            else:
                print(format_devices(index, args.domain))
            return 0

        if args.command == "alias":
            index = load_device_index()
            if args.name and args.target:
                index.setdefault("aliases", {})[args.name.lower().strip()] = args.target
                save_device_index(index)
                print(f"Bound alias '{args.name}' -> {args.target}")
            else:
                for a, eid in sorted(index.get("aliases", {}).items()):
                    print(f"{a} -> {eid}")
            return 0

        url, token = load_credentials()
        fallback_urls = load_fallback_urls()
        client = HomeAssistantClient(url, token, args.timeout, fallback_urls=fallback_urls)
        verify = not getattr(args, "no_verify", False)

        if args.command == "sync":
            result = client.sync_index()
            if getattr(args, "brief", False):
                print(f"Synced {result['total_devices']} devices ({result['new_aliases_added']} new) to {result['index_path']}")
            else:
                print(json.dumps(result, indent=2))
            return 0
        elif args.command == "status":
            result = client.status()
        elif args.command == "config":
            result = client.config()
        elif args.command == "state":
            expanded = []
            for t in args.targets:
                for sub_t in t.replace(",", " ").split():
                    if sub_t:
                        expanded.append(sub_t)
            if len(expanded) == 1:
                result = client.state(expanded[0])
            else:
                result = client.state_targets(expanded)
        elif args.command == "states":
            result = client.states(args.domain)
        elif args.command == "services":
            result = client.services()
        elif args.command == "errors":
            result = client.errors()
        elif args.command == "check-config":
            result = client.check_config()
        elif args.command == "call":
            result = client.call(args.domain, args.service, args.entity_id, args.data, verify=verify)
        elif args.command == "upstairs":
            if args.action == "state":
                result = client.state("upstairs")
            else:
                result = client.upstairs(args.action, verify=verify)
        elif args.command == "downstairs":
            if args.action == "state":
                result = client.state("downstairs")
            else:
                result = client.downstairs(args.action, verify=verify)
        elif args.command in {"on", "off", "toggle"}:
            expanded = []
            for t in args.targets:
                for sub_t in t.replace(",", " ").split():
                    if sub_t:
                        expanded.append(sub_t)
            result = client.toggle_targets(args.command, expanded, verify=verify)
        elif args.command == "speed":
            lvl = args.level.lower().strip()
            if lvl in {"lower", "down", "decrease"}:
                result = client.adjust_targets("decrease", [args.target], verify=verify)
            elif lvl in {"raise", "up", "increase", "higher"}:
                result = client.adjust_targets("increase", [args.target], verify=verify)
            elif lvl.rstrip("%").isdigit():
                val = max(0, min(100, int(lvl.rstrip("%"))))
                result = client.set_level_targets(val, [args.target], verify=verify)
            else:
                raise ClientError(f"Unknown speed level '{args.level}'. Use 'lower', 'raise', or 0-100.")
        elif args.command == "act":
            phrase = " ".join(args.phrase)
            result = client.act(phrase, verify=verify)
        elif args.command == "snapshot":
            result = client.snapshot(args.target, args.output)
        elif args.command == "ptz":
            result = client.ptz(args.target, args.direction)
        elif args.command == "media":
            result = client.media(args.action, args.target, args.value)
        elif args.command == "color":
            result = client.color(args.target, args.color, verify=verify)
        elif args.command == "weather":
            result = client.weather()
        elif args.command == "presence":
            result = client.presence()
        elif args.command == "press":
            result = client.press(args.target)
        elif args.command == "preset":
            result = client.preset(args.target, args.mode)
        else:
            raise ClientError(f"Unknown command: {args.command}")

        sanitized = sanitize(result, token)
        is_action_cmd = args.command in {
            "on", "off", "toggle", "upstairs", "downstairs",
            "act", "state", "speed", "snapshot", "ptz",
            "media", "color", "weather", "presence", "press", "preset"
        }
        wants_json = getattr(args, "json", False)

        if wants_json:
            if isinstance(sanitized, str):
                print(sanitized)
            else:
                print(json.dumps(sanitized, indent=2, sort_keys=True))
        elif is_action_cmd or getattr(args, "brief", False):
            print(format_brief(args.command, sanitized))
        elif isinstance(sanitized, str):
            print(sanitized)
        else:
            print(json.dumps(sanitized, indent=2, sort_keys=True))
        return 0

    except ClientError as e:
        print(f"ha error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
