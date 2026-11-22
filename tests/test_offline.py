"""Offline tests for the PetoiX pipeline — no robot and no API key needed.

The serial port is replaced with a fake that records what would be sent, and
OPENROUTER_API_KEY is cleared so the deterministic keyword-rule planner runs.

    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

os.environ["OPENROUTER_API_KEY"] = ""          # force the rule-based path
os.environ["INTERACTION_LOG_PATH"] = os.devnull  # don't write logs during tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402

JOINT_REPLY = (
    "ICM: -5.43 -1.71  8.72 -353.6  -31.6  -10.4\tup\n"
    "0\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\t14\t15\t\n"
    "5\t-10\t0\t0\t0\t0\t0\t0\t30\t30\t30\t30\t-20\t-20\t-20\t-20\t\n"
    "j\n"
)


class FakeSerial:
    """Stands in for SerialManager: records commands instead of writing to a port."""

    def __init__(self):
        self.sent = []

    @property
    def connected(self):
        return True

    def send(self, cmd, wait_for_ack=True, until=None):
        self.sent.append(cmd)
        if cmd == "j":
            return {"success": True, "response": JOINT_REPLY}
        return {"success": True, "response": cmd.lstrip("k")}

    def health_check(self):
        return {"ok": True}

    def scan_ports(self):
        return []


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSerial()
        self.patches = [
            mock.patch.object(server, "serial_mgr", self.fake),
            mock.patch.object(server.time, "sleep", lambda *_: None),
        ]
        for p in self.patches:
            p.start()
        self.client = server.app.test_client()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    # Stage 2-5: interpret -> map -> validate -> execute
    def test_chained_prompt_maps_to_two_skills(self):
        data = self.client.post("/api/command", json={"text": "sit then wave"}).get_json()
        self.assertEqual(data["trace"]["steps"], ["sit", "wave"])
        self.assertEqual(data["commands"], ["ksit", "khi"])
        self.assertEqual(data["trace"]["planner_source"], "rule")
        self.assertEqual(self.fake.sent, ["ksit", "khi"])

    def test_direct_skill_name_uses_rules(self):
        data = self.client.post("/api/command", json={"text": "sit"}).get_json()
        self.assertEqual(data["commands"], ["ksit"])
        self.assertEqual(data["trace"]["confidence"], 1.0)

    def test_negated_request_sends_nothing(self):
        data = self.client.post("/api/command", json={"text": "don't walk forward"}).get_json()
        self.assertEqual(data["commands"], [])
        self.assertEqual(self.fake.sent, [])

    def test_non_action_question_sends_nothing(self):
        data = self.client.post("/api/command", json={"text": "what is my name?"}).get_json()
        self.assertEqual(data["commands"], [])

    def test_plan_never_exceeds_three_steps(self):
        data = self.client.post(
            "/api/command", json={"text": "sit, then wave, then stand, then rest, then stretch"}
        ).get_json()
        self.assertLessEqual(len(data["trace"]["steps"]), server.MAX_PLAN_STEPS)

    # Stage 4: allowlist
    def test_manual_quick_actions_are_allowed(self):
        self.assertEqual(len(server.MANUAL_QUICK_ACTIONS), 19)
        for cmd in server.MANUAL_QUICK_ACTIONS:
            res = self.client.post("/api/direct", json={"cmd": cmd})
            self.assertEqual(res.status_code, 200, cmd)

    def test_calibration_command_is_rejected(self):
        for cmd in ["c", "s", "K", "a", "m0 500"]:
            res = self.client.post("/api/direct", json={"cmd": cmd})
            self.assertEqual(res.status_code, 403, cmd)
        self.assertEqual(self.fake.sent, [])

    # Manual Mode joint readout
    def test_joint_table_parsing(self):
        joints = server.parse_joint_angles(JOINT_REPLY)
        self.assertEqual(joints[0], 5)
        self.assertEqual(joints[1], -10)
        self.assertEqual(joints[15], -20)
        self.assertIsNone(server.parse_joint_angles("ICM: 1 2 3\tup"))

    def test_joints_endpoint(self):
        data = self.client.get("/api/joints").get_json()
        self.assertEqual(data["joints"]["8"], 30)

    # Static files: never expose .env or logs
    def test_only_ui_files_are_served(self):
        self.assertEqual(self.client.get("/app.js").status_code, 200)
        self.assertEqual(self.client.get("/.env").status_code, 404)
        self.assertEqual(self.client.get("/server.py").status_code, 404)
        self.assertEqual(self.client.get("/interaction_logs.jsonl").status_code, 404)

    # WebSockets: live trace + camera tracking
    def test_websocket_pushes_pipeline_events(self):
        ws = server.socketio.test_client(server.app)
        self.assertTrue(ws.is_connected())
        ws.get_received()  # drop the initial status event
        self.client.post("/api/command", json={"text": "sit then wave"})
        names = [e["name"] for e in ws.get_received()]
        self.assertIn("plan", names)
        self.assertEqual(names.count("command_progress"), 2)
        self.assertIn("command_complete", names)
        ws.disconnect()

    def test_websocket_tracking_validates_joint_limits(self):
        ws = server.socketio.test_client(server.app)
        ack = ws.emit("track", {"pan": 20, "tilt": 10}, callback=True)
        self.assertTrue(ack["success"])
        self.assertEqual(self.fake.sent[-1], "i0 20 1 10")
        ack = ws.emit("track", {"pan": 999, "tilt": 0}, callback=True)
        self.assertFalse(ack["success"])
        ws.disconnect()


if __name__ == "__main__":
    unittest.main()
