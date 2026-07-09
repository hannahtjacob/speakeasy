import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from summarizer import summarize_message

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

bolt_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    token_verification_enabled=False,
)

flask_app = Flask(__name__)
CORS(flask_app)
handler = SlackRequestHandler(bolt_app)

STORE_PATH = Path(__file__).with_name("store.json")


def default_store():
    return {"alerts": {}, "raw_messages": [], "summaries": []}


def load_store():
    if not STORE_PATH.exists():
        return default_store()
    with open(STORE_PATH, "r") as f:
        if not f.read().strip():
            return default_store()
        f.seek(0)
        try:
            store = json.load(f)
        except json.JSONDecodeError:
            return default_store()
    store.setdefault("alerts", {})
    store.setdefault("raw_messages", [])
    store.setdefault("summaries", [])
    return store


def save_store(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def channel_has_alerts_enabled(channel_id):
    store = load_store()
    alerts = store.get("alerts", {})
    return any(
        value.get("channel_id") == channel_id and value.get("enabled")
        for value in alerts.values()
    )


@bolt_app.command("/speak-alerts")
def speak_alerts_command(ack, respond, command):
    ack()

    text = command.get("text", "").strip().lower()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    key = f"{user_id}:{channel_id}"

    store = load_store()

    if text == "on":
        store["alerts"][key] = {
            "enabled": True,
            "user_id": user_id,
            "channel_id": channel_id
        }
        save_store(store)
        respond("SpeakEasy alerts are now ON for this channel.")
    elif text == "off":
        store["alerts"][key] = {
            "enabled": False,
            "user_id": user_id,
            "channel_id": channel_id
        }
        save_store(store)
        respond("SpeakEasy alerts are now OFF for this channel.")
    elif text == "status":
        enabled = store["alerts"].get(key, {}).get("enabled", False)
        respond(f"SpeakEasy alerts are currently {'ON' if enabled else 'OFF'} for this channel.")
    else:
        respond("Use `/speak-alerts on`, `/speak-alerts off`, or `/speak-alerts status`.")


@bolt_app.event("message")
def handle_message_events(event, say):
    if event.get("subtype") is not None:
        return
    user = event.get("user")
    text = event.get("text", "")
    channel = event.get("channel")
    if not text:
        return
    if not channel_has_alerts_enabled(channel):
        return

    store = load_store()
    store["raw_messages"].append({
        "user": user,
        "channel": channel,
        "text": text,
        "ts": event.get("ts")
    })
    save_store(store)
    print(f"New message in {channel}: {text}")

    try:
        summary = summarize_message(text, channel)
    except Exception as e:
        print("Summarization failed:", e)
        summary = text[:120]

    store = load_store()
    store["summaries"].append({
        "channel": channel,
        "original_text": text,
        "summary": summary,
        "ts": event.get("ts")
    })
    save_store(store)
    print(f"Summary: {summary}")


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/health")
def health():
    return jsonify({"ok": True})


@flask_app.route("/api/latest-summary")
def latest_summary():
    store = load_store()
    summaries = store.get("summaries", [])

    if not summaries:
        return jsonify({"summary": None})

    return jsonify(summaries[-1])


if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
