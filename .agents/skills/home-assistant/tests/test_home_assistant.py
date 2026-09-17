#!/usr/bin/env python3
"""Automated tests for Home Assistant REST client and CLI adapter."""

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from home_assistant import (
    ALIASES,
    ClientError,
    HomeAssistantClient,
    entity_id,
    format_brief,
    identifier,
    json_object,
    parse_intent,
    redact,
    sanitize,
    timeout,
)


class MockHomeAssistantHandler(BaseHTTPRequestHandler):
    MOCK_STATES: dict[str, Any] = {
        "light.kitchen": "on",
        "fan.ceiling_fan": "off",
        "fan.fan": "off",
        "light.ceiling_fan": "on",
        "light.fan": "on",
        "switch.living_room": "off",
        "switch.kitchen": "off",
        "switch.countertop": "off",
        "camera.casco_doorbell_live_view": "idle",
        "weather.forecast_home": {
            "entity_id": "weather.forecast_home",
            "state": "sunny",
            "attributes": {"temperature": 92, "humidity": 55, "temperature_unit": "°F"},
        },
        "person.shakestate": {
            "entity_id": "person.shakestate",
            "state": "home",
            "attributes": {"friendly_name": "Shak"},
        },
        "zone.home": {
            "entity_id": "zone.home",
            "state": "1",
            "attributes": {"friendly_name": "SHAKESTATE"},
        },
        "media_player.shaku": "idle",
        "button.upstairs_pan_left": "unknown",
    }

    def log_message(self, format, *args):
        pass  # Quiet logs during test runs

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        if auth != "Bearer test-secret-token":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"message": "Unauthorized"}')
            return

        if self.path == "/api/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": "API running."}).encode())
        elif self.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"location_name": "Test Home"}).encode())
        elif self.path == "/api/states":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            states = [
                {"entity_id": "light.kitchen", "state": "on"},
                {"entity_id": "fan.ceiling_fan", "state": "off"},
                {"entity_id": "weather.forecast_home", "state": "sunny", "attributes": {"temperature": 92}},
                {"entity_id": "person.shakestate", "state": "home", "attributes": {"friendly_name": "Shak"}},
                {"entity_id": "zone.home", "state": "1"},
            ]
            self.wfile.write(json.dumps(states).encode())
        elif self.path.startswith("/api/camera_proxy/"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            self.wfile.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        elif self.path.startswith("/api/states/"):
            eid = self.path[len("/api/states/"):]
            if eid in self.MOCK_STATES:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                val = self.MOCK_STATES[eid]
                if isinstance(val, dict):
                    self.wfile.write(json.dumps(val).encode())
                else:
                    self.wfile.write(json.dumps({"entity_id": eid, "state": val}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == "/api/services":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([{"domain": "light", "services": {"turn_on": {}}}]).encode())
        elif self.path == "/api/error_log":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"No errors logged.")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        auth = self.headers.get("Authorization", "")
        if auth != "Bearer test-secret-token":
            self.send_response(401)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if self.path.startswith("/api/services/"):
            # Update dynamic state if entity_id is provided
            try:
                payload = json.loads(body.decode("utf-8"))
                target_eid = payload.get("entity_id")
                svc = self.path.split("/")[-1]
                if target_eid in self.MOCK_STATES:
                    if svc == "turn_on":
                        self.MOCK_STATES[target_eid] = "on"
                    elif svc == "turn_off":
                        self.MOCK_STATES[target_eid] = "off"
                    elif svc == "toggle":
                        curr = self.MOCK_STATES.get(target_eid, "off")
                        self.MOCK_STATES[target_eid] = "off" if curr == "on" else "on"
            except Exception:
                pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([{"entity_id": "light.kitchen"}]).encode())
        elif self.path == "/api/config/core/check_config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"result": "valid"}).encode())
        else:
            self.send_response(404)
            self.end_headers()


class TestHomeAssistantAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MockHomeAssistantHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.token = "test-secret-token"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.client = HomeAssistantClient(self.base_url, self.token, timeout_seconds=5.0)

    def test_status(self):
        status = self.client.status()
        self.assertEqual(status["api"]["message"], "API running.")
        self.assertEqual(status["config"]["location_name"], "Test Home")

    def test_config(self):
        config = self.client.config()
        self.assertEqual(config["location_name"], "Test Home")

    def test_state_single(self):
        state = self.client.state("light.kitchen")
        self.assertEqual(state["entity_id"], "light.kitchen")
        self.assertEqual(state["state"], "on")

    def test_state_upstairs(self):
        res = self.client.state("upstairs")
        self.assertIn("fan.ceiling_fan", res)
        self.assertIn("light.ceiling_fan", res)

    def test_states_filtered(self):
        states = self.client.states(domain_filter="light")
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["entity_id"], "light.kitchen")

    def test_call_service(self):
        res = self.client.call("light", "turn_on", "light.kitchen", {"brightness_pct": 80})
        self.assertIn("service_result", res)
        self.assertEqual(res["state"]["entity_id"], "light.kitchen")

    def test_errors(self):
        log = self.client.errors()
        self.assertEqual(log, "No errors logged.")

    def test_redaction(self):
        secret = "super-secret-xyz"
        text = f"Connection failed with token: {secret}"
        self.assertEqual(redact(text, secret), "Connection failed with token: [redacted]")

    def test_sanitize(self):
        secret = "secret123"
        nested = {
            "token": "secret123",
            "items": ["prefix-secret123", {"field": "secret123"}],
        }
        res = sanitize(nested, secret)
        self.assertEqual(res["token"], "[redacted]")
        self.assertEqual(res["items"][0], "prefix-[redacted]")
        self.assertEqual(res["items"][1]["field"], "[redacted]")

    def test_validators(self):
        self.assertEqual(identifier("turn_on"), "turn_on")
        self.assertEqual(entity_id("light.kitchen"), "light.kitchen")
        self.assertEqual(entity_id("upstairs"), "upstairs")
        self.assertEqual(entity_id("downstairs"), "downstairs")
        self.assertEqual(entity_id("kitchen"), "kitchen")
        self.assertEqual(timeout("10"), 10.0)
        self.assertEqual(json_object('{"key": 1}'), {"key": 1})

        with self.assertRaises(Exception):
            identifier("invalid-id!")
        with self.assertRaises(Exception):
            entity_id("invalid entity with spaces")
        with self.assertRaises(Exception):
            json_object('{"entity_id": "bad"}')

    def test_state_downstairs(self):
        res = self.client.state("downstairs")
        self.assertIn("switch.living_room", res)
        self.assertIn("switch.kitchen", res)

    def test_downstairs_action(self):
        res = self.client.downstairs("off")
        self.assertIn("switch.living_room", res)
        self.assertIn("switch.kitchen", res)

    def test_toggle_target_alias(self):
        res = self.client.toggle_target("off", "kitchen")
        self.assertEqual(res["state"]["entity_id"], "switch.kitchen")

    def test_format_brief(self):
        brief = format_brief("state", {"entity_id": "switch.kitchen", "state": "off"})
        self.assertEqual(brief, "switch.kitchen: off")
        multi = format_brief("state", {
            "switch.living_room": {"state": "off"},
            "switch.kitchen": {"state": "off"}
        })
        self.assertIn("switch.living_room: off", multi)
        self.assertIn("switch.kitchen: off", multi)

    def test_sync_index(self):
        res = self.client.sync_index()
        self.assertGreater(res["total_devices"], 0)
        self.assertIn("total_aliases", res)

    def test_parse_intent(self):
        action, targets = parse_intent("turn on upstairs fan and upstairs fan light")
        self.assertEqual(action, "on")
        self.assertEqual(targets, ["upstairs fan", "upstairs fan light"])

        action, targets = parse_intent("turn off kitchen and countertop")
        self.assertEqual(action, "off")
        self.assertEqual(targets, ["kitchen", "countertop"])

        action, targets = parse_intent("toggle desk")
        self.assertEqual(action, "toggle")
        self.assertEqual(targets, ["desk"])

        action, targets = parse_intent("lower upstairs fan speed")
        self.assertEqual(action, "decrease")
        self.assertEqual(targets, ["upstairs fan"])

        action, targets = parse_intent("increase upstairs fan speed")
        self.assertEqual(action, "increase")
        self.assertEqual(targets, ["upstairs fan"])

        action, targets = parse_intent("dim the kitchen lights")
        self.assertEqual(action, "decrease")
        self.assertEqual(targets, ["kitchen lights"])

        action, targets = parse_intent("set upstairs fan to 50%")
        self.assertEqual(action, "set:50")
        self.assertEqual(targets, ["upstairs fan"])

        action, targets = parse_intent("what's the weather")
        self.assertEqual(action, "weather")

        action, targets = parse_intent("who is home")
        self.assertEqual(action, "presence")

        action, targets = parse_intent("take snapshot of doorbell")
        self.assertEqual(action, "snapshot")
        self.assertEqual(targets, ["doorbell"])

        action, targets = parse_intent("pause tv")
        self.assertEqual(action, "pause")
        self.assertEqual(targets, ["tv"])

        action, targets = parse_intent("turn upstairs light blue")
        self.assertEqual(action, "color:blue")
        self.assertEqual(targets, ["upstairs light"])

    def test_toggle_targets_multi(self):
        res = self.client.toggle_targets("on", ["upstairs_fan", "upstairs_fan_light"])
        self.assertIn("fan.ceiling_fan", res)
        self.assertIn("light.ceiling_fan", res)
        self.assertTrue(res["fan.ceiling_fan"]["verified"])
        self.assertTrue(res["light.ceiling_fan"]["verified"])

    def test_act(self):
        res = self.client.act("turn on upstairs fan and upstairs fan light")
        self.assertIn("fan.ceiling_fan", res)
        self.assertIn("light.ceiling_fan", res)

        res_lower = self.client.act("lower upstairs fan speed")
        self.assertEqual(res_lower["state"]["entity_id"], "fan.ceiling_fan")

        res_speed = self.client.adjust_targets("decrease", ["upstairs_fan"])
        self.assertEqual(res_speed["state"]["entity_id"], "fan.ceiling_fan")

        res_level = self.client.set_level_targets(50, ["upstairs_fan"])
        self.assertEqual(res_level["state"]["entity_id"], "fan.ceiling_fan")

        res_snap = self.client.act("take snapshot of doorbell")
        self.assertEqual(res_snap["entity_id"], "camera.casco_doorbell_live_view")

        res_weather = self.client.act("what's the weather")
        self.assertEqual(res_weather["state"], "sunny")

        res_presence = self.client.act("who is home")
        self.assertIn("persons", res_presence)

    def test_snapshot_method(self):
        snap = self.client.snapshot("doorbell")
        self.assertEqual(snap["entity_id"], "camera.casco_doorbell_live_view")
        self.assertTrue(os.path.exists(snap["file_path"]))
        os.remove(snap["file_path"])

    def test_weather_and_presence(self):
        w = self.client.weather()
        self.assertEqual(w["state"], "sunny")

        p = self.client.presence()
        self.assertTrue(len(p["persons"]) > 0)
        self.assertEqual(p["home_zone"]["state"], "1")

    def test_media_and_ptz(self):
        m = self.client.media("pause", "tv")
        self.assertIn("service_result", m)

        ptz = self.client.ptz("upstairs", "left")
        self.assertIn("service_result", ptz)

    def test_color_method(self):
        c = self.client.color("lamp", "blue")
        self.assertIn("service_result", c)

    def test_preset_method(self):
        p = self.client.preset("fan", "sleep")
        self.assertIn("service_result", p)

    def test_state_targets_multi(self):
        res = self.client.state_targets(["upstairs_fan", "kitchen"])
        self.assertIn("fan.ceiling_fan", res)
        self.assertIn("switch.kitchen", res)

    def test_format_brief_verified(self):
        single = format_brief("on", {
            "state": {"entity_id": "fan.ceiling_fan", "state": "on"},
            "verified": True,
        })
        self.assertEqual(single, "fan.ceiling_fan: on (verified)")

        multi = format_brief("on", {
            "fan.ceiling_fan": {"state": "on", "verified": True},
            "light.ceiling_fan": {"state": "on", "verified": False},
        })
        self.assertIn("fan.ceiling_fan: on (verified)", multi)
        self.assertIn("light.ceiling_fan: on (unconfirmed)", multi)

        snap_fmt = format_brief("snapshot", {
            "entity_id": "camera.casco_doorbell_live_view",
            "file_path": "/tmp/test.jpg",
            "size_kb": 33.7,
        })
        self.assertIn("snapshot saved to /tmp/test.jpg", snap_fmt)

        w_fmt = format_brief("weather", {
            "entity_id": "weather.forecast_home",
            "state": "sunny",
            "attributes": {"temperature": 92, "temperature_unit": "°F", "humidity": 55},
        })
        self.assertIn("sunny, 92°F", w_fmt)

    def test_fallback_urls(self):
        # Client pointing to an unreachable port first, then falling back to mock server
        fallback_client = HomeAssistantClient(
            "http://127.0.0.1:1",
            "test-secret-token",
            timeout_seconds=0.5,
            fallback_urls=[f"http://127.0.0.1:{self.port}"],
        )
        res = fallback_client.status()
        self.assertEqual(res["api"]["message"], "API running.")
        self.assertEqual(fallback_client.api_root, f"http://127.0.0.1:{self.port}/api")


if __name__ == "__main__":
    unittest.main()
