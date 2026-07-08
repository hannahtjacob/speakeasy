import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from summarizer import summarize_message

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

bolt_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

STORE_PATH = Path("store.json")


def load_store():
    if not STORE_PATH.exists():
        return {"alerts": {}, "summaries": []}
    with open(STORE_PATH, "r") as f:
        if not f.read().strip():
            return {"alerts": {}, "summaries": []}
        f.seek(0)
        return json.load(f)


def save_store(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


@bolt_app.command("/speak-alerts")
def speak_alerts_command(ack, respond, command):
    ack()

    text = command.get("text", "").strip()
    user_id = command["user_id"]

    if text == "on":
        store = load_store()
        store["alerts"][user_id] = {"enabled": True}
        save_store(store)
        respond("SpeakEasy alerts are now ON for you.")
    elif text == "off":
        store = load_store()
        store["alerts"][user_id] = {"enabled": False}
        save_store(store)
        respond("SpeakEasy alerts are now OFF for you.")
    else:
        respond("Use `/speak-alerts on` or `/speak-alerts off`.")


@bolt_app.event("message")
def handle_message_events(event, say):
    if event.get("subtype") is not None:
        return
    user = event.get("user")
    text = event.get("text", "")
    channel = event.get("channel")
    if not text:
        return
    store = load_store()
    store.setdefault("raw_messages", [])
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
    store.setdefault("summaries", [])
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


if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
