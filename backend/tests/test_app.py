import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test-signing-secret")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


class SpeakEasyTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_store_path = app.STORE_PATH
        app.STORE_PATH = Path(self.temp_directory.name) / "store.json"

    def tearDown(self):
        app.STORE_PATH = self.original_store_path
        self.temp_directory.cleanup()

    def command(self, text, user_id="U1", channel_id="C1"):
        responses = []
        app.speak_alerts_command(
            lambda: None,
            responses.append,
            {
                "text": text,
                "user_id": user_id,
                "channel_id": channel_id,
                "channel_name": "speakeasy-demo",
            },
        )
        return responses[-1]

    def test_off_clears_history_after_last_listener(self):
        self.command("on", "U1")
        self.command("on", "U2")
        store = app.load_store()
        store["raw_messages"] = [{"channel": "C1", "text": "update"}]
        store["summaries"] = [{"channel": "C1", "summary": "summary"}]
        app.save_store(store)

        self.command("off", "U1")
        self.assertEqual(len(app.load_store()["raw_messages"]), 1)

        response = self.command("off", "U2")
        self.assertEqual(app.load_store()["raw_messages"], [])
        self.assertEqual(app.load_store()["summaries"], [])
        self.assertIn("history was cleared", response)

    def test_message_stores_readable_channel_name(self):
        self.command("on")
        slack_client = unittest.mock.Mock()
        slack_client.conversations_info.return_value = {
            "channel": {"name": "speakeasy-demo"}
        }
        slack_client.users_info.return_value = {
            "user": {"profile": {"display_name": "prisha"}}
        }

        app.handle_message_events(
            {"user": "U2", "channel": "C1", "text": "Hello", "ts": "123"},
            slack_client,
        )

        store = app.load_store()
        self.assertEqual(store["raw_messages"][0]["channel_name"], "speakeasy-demo")
        self.assertEqual(store["raw_messages"][0]["user_name"], "prisha")
        self.assertEqual(store["raw_messages"][0]["text"], "Hello")
        self.assertEqual(store["summaries"], [])

    def test_alert_feed_returns_every_unseen_exact_message(self):
        store = app.default_store()
        store["raw_messages"] = [
            {
                "channel": "C1",
                "channel_name": "social",
                "user_name": "prisha",
                "text": "Bring cookies to the roundtable.",
                "ts": "100.1",
            },
            {
                "channel": "C2",
                "channel_name": "demo",
                "user_name": "hannah",
                "text": "Do not bring cookies.",
                "ts": "100.2",
            },
        ]
        app.save_store(store)

        response = app.flask_app.test_client().get("/api/alerts?after=100.0")
        alerts = response.get_json()["alerts"]

        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["text"], "Bring cookies to the roundtable.")
        self.assertEqual(alerts[1]["text"], "Do not bring cookies.")

    def test_ask_uses_only_requested_channel(self):
        store = app.default_store()
        store["raw_messages"] = [
            {"user": "U1", "channel": "C1", "channel_name": "demo", "text": "Demo update"},
            {"user": "U2", "channel": "C2", "channel_name": "private", "text": "Private update"},
        ]
        app.save_store(store)

        with (
            patch.object(app, "get_user_name", return_value="prisha"),
            patch.object(app, "answer_question", return_value="Demo answer") as answer,
        ):
            response = app.flask_app.test_client().post(
                "/api/ask",
                json={"channel": "demo", "question": "What happened?"},
            )

        context = answer.call_args.args[1]
        self.assertEqual(response.status_code, 200)
        self.assertIn("Demo update", context)
        self.assertNotIn("Private update", context)

    def test_ask_all_channels_uses_exact_messages_without_user_ids(self):
        store = app.default_store()
        store["raw_messages"] = [
            {
                "user": "U123",
                "user_name": "prisha",
                "channel": "C1",
                "channel_name": "social",
                "text": "Bring cookies to the roundtable.",
            },
            {
                "user": "U456",
                "channel": "C2",
                "channel_name": "demo",
                "text": "The meeting is tomorrow.",
            },
        ]
        app.save_store(store)

        with (
            patch.object(app, "get_user_name", return_value="hannah"),
            patch.object(app, "answer_question", return_value="Answer") as answer,
        ):
            response = app.flask_app.test_client().post(
                "/api/ask",
                json={"channel": "all", "question": "What was said?"},
            )

        context = answer.call_args.args[1]
        self.assertEqual(response.status_code, 200)
        self.assertIn("prisha: Bring cookies", context)
        self.assertIn("hannah: The meeting", context)
        self.assertNotIn("U123", context)
        self.assertNotIn("U456", context)

    def test_channels_endpoint_lists_slack_channels(self):
        response_data = {
            "channels": [
                {"id": "C2", "name": "social"},
                {"id": "C1", "name": "demo"},
            ]
        }
        with patch.object(
            app.bolt_app.client,
            "conversations_list",
            return_value=response_data,
        ):
            response = app.flask_app.test_client().get("/api/channels")

        self.assertEqual(
            response.get_json()["channels"],
            [{"id": "C1", "name": "demo"}, {"id": "C2", "name": "social"}],
        )

    def test_health_and_empty_latest_summary(self):
        client = app.flask_app.test_client()
        self.assertEqual(client.get("/health").get_json(), {"ok": True})
        self.assertEqual(client.get("/api/latest-summary").get_json(), {"summary": None})


if __name__ == "__main__":
    unittest.main()
