import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from qa import answer_question
from summarizer import summarize_message
from priority import is_priority_message

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


def enabled_channels():
    store = load_store()
    channels = {}

    for value in store.get("alerts", {}).values():
        if not value.get("enabled"):
            continue

        channel_id = value.get("channel_id")
        if not channel_id:
            continue

        channel_name = value.get("channel_name") or channel_id
        channels[channel_id] = {
            "id": channel_id,
            "name": channel_name.lstrip("#"),
        }

    return sorted(channels.values(), key=lambda channel: channel["name"].lower())


def verify_slack_signature(req):
    timestamp = req.headers.get("X-Slack-Request-Timestamp", "")
    signature = req.headers.get("X-Slack-Signature", "")

    if not timestamp or not signature:
        return False

    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False

    if abs(time.time() - timestamp_value) > 60 * 5:
        return False

    body = req.get_data(as_text=True)
    base = f"v0:{timestamp}:{body}".encode()
    digest = hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        base,
        hashlib.sha256,
    ).hexdigest()
    expected = f"v0={digest}"
    return hmac.compare_digest(expected, signature)


def handle_speak_alerts_command(command):
    text = command.get("text", "").strip().lower()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    channel_name = command.get("channel_name") or channel_id
    key = f"{user_id}:{channel_id}"

    store = load_store()

    if text == "on":
        store["alerts"][key] = {
            "enabled": True,
            "user_id": user_id,
            "channel_id": channel_id,
            "channel_name": channel_name,
        }
        save_store(store)
        return "SpeakEasy alerts are now ON for this channel."
    elif text == "off":
        store["alerts"][key] = {
            "enabled": False,
            "user_id": user_id,
            "channel_id": channel_id,
            "channel_name": channel_name,
        }
        save_store(store)
        return "SpeakEasy alerts are now OFF for this channel."
    elif text == "status":
        enabled = store["alerts"].get(key, {}).get("enabled", False)
        return f"SpeakEasy alerts are currently {'ON' if enabled else 'OFF'} for this channel."
    else:
        return "Use `/speak-alerts on`, `/speak-alerts off`, or `/speak-alerts status`."


@bolt_app.command("/speak-alerts")
def speak_alerts_command(ack, command):
    ack(handle_speak_alerts_command(command))


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

    priority = is_priority_message(text)

    try:
        summary = summarize_message(text, channel,priority)

    except Exception as e:
        print("Summarization failed:", e)
        summary = text[:120]

    store = load_store()
    store["summaries"].append({
        "channel": channel,
        "original_text": text,
        "summary": summary,
        "priority": priority,
        "ts": event.get("ts")
    })
    save_store(store)
    print(f"Summary: {summary}")
    if priority:
        print("Priority: True")


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if request.mimetype == "application/x-www-form-urlencoded":
        request.get_data(as_text=True)
        if not verify_slack_signature(request):
            return jsonify({"error": "Invalid Slack signature."}), 401

        if request.form.get("command") == "/speak-alerts":
            message = handle_speak_alerts_command(request.form)
            return jsonify({"response_type": "ephemeral", "text": message})

    data = request.get_json(silent=True) or {}
    if data.get("type") == "url_verification" and data.get("challenge"):
        return data["challenge"], 200, {"Content-Type": "text/plain"}

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


@flask_app.route("/api/enabled-channels")
def active_channels():
    return jsonify({"channels": enabled_channels()})


@flask_app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Ask a question about recent Slack activity."}), 400

    store = load_store()
    recent_messages = store.get("raw_messages", [])[-20:]
    context = "\n".join([
        f"{message.get('user')}: {message.get('text')}"
        for message in recent_messages
    ])

    try:
        answer = answer_question(question, context)
    except Exception as e:
        print("Question answering failed:", e)
        if recent_messages:
            answer = "I could not reach the assistant model, but I found recent Slack activity."
        else:
            answer = "I do not see any recent Slack messages yet."

    return jsonify({"answer": answer})


if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
