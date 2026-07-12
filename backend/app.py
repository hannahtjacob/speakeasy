import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from qa import answer_question

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


def clear_channel_history(store, channel_id):
    store["raw_messages"] = [
        message for message in store["raw_messages"]
        if message.get("channel") != channel_id
    ]
    store["summaries"] = [
        summary for summary in store["summaries"]
        if summary.get("channel") != channel_id
    ]


def get_channel_name(client, channel_id):
    try:
        response = client.conversations_info(channel=channel_id)
        return response["channel"].get("name") or channel_id
    except Exception as e:
        print("Could not resolve channel name:", e)
        return channel_id


def get_user_name(client, user_id):
    try:
        user = client.users_info(user=user_id)["user"]
        profile = user.get("profile", {})
        return (
            profile.get("display_name")
            or profile.get("real_name")
            or user.get("real_name")
            or user.get("name")
            or "Someone"
        )
    except Exception as e:
        print("Could not resolve user name:", e)
        return "Someone"


def add_missing_user_names(messages, client):
    resolved_names = {}
    changed = False
    for message in messages:
        if message.get("user_name"):
            continue
        user_id = message.get("user")
        if user_id:
            if user_id not in resolved_names:
                resolved_names[user_id] = get_user_name(client, user_id)
            message["user_name"] = resolved_names[user_id]
            changed = True
    return changed


@bolt_app.command("/speak-alerts")
def speak_alerts_command(ack, respond, command):
    ack()

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
            "channel_name": channel_name
        }
        save_store(store)
        respond("SpeakEasy alerts are now ON for this channel.")
    elif text == "off":
        store["alerts"][key] = {
            "enabled": False,
            "user_id": user_id,
            "channel_id": channel_id,
            "channel_name": channel_name
        }
        history_cleared = not any(
            alert.get("channel_id") == channel_id and alert.get("enabled")
            for alert in store["alerts"].values()
        )
        if history_cleared:
            clear_channel_history(store, channel_id)
        save_store(store)
        if history_cleared:
            respond("SpeakEasy alerts are now OFF for this channel, and its history was cleared.")
        else:
            respond("SpeakEasy alerts are now OFF for you in this channel.")
    elif text == "status":
        enabled = store["alerts"].get(key, {}).get("enabled", False)
        respond(f"SpeakEasy alerts are currently {'ON' if enabled else 'OFF'} for this channel.")
    else:
        respond("Use `/speak-alerts on`, `/speak-alerts off`, or `/speak-alerts status`.")


@bolt_app.event("message")
def handle_message_events(event, client):
    if event.get("subtype") is not None:
        return
    user = event.get("user")
    text = event.get("text", "")
    channel = event.get("channel")
    if not text:
        return
    if not channel_has_alerts_enabled(channel):
        return

    channel_name = get_channel_name(client, channel)
    user_name = get_user_name(client, user)

    store = load_store()
    store["raw_messages"].append({
        "user": user,
        "user_name": user_name,
        "channel": channel,
        "channel_name": channel_name,
        "text": text,
        "ts": event.get("ts")
    })
    save_store(store)
    print(f"New message from {user_name} in #{channel_name}: {text}")


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


@flask_app.route("/api/alerts")
def alerts():
    after = request.args.get("after", "")
    messages = sorted(
        load_store().get("raw_messages", []),
        key=lambda message: message.get("ts", ""),
    )
    unseen = [
        message for message in messages
        if str(message.get("ts", "")) > after
    ]
    latest_ts = str(messages[-1].get("ts", "")) if messages else ""
    return jsonify({"alerts": unseen, "latest_ts": latest_ts})


@flask_app.route("/api/channels")
def channels():
    channels_by_id = {}
    try:
        response = bolt_app.client.conversations_list(
            exclude_archived=True,
            limit=200,
            types="public_channel",
        )
        channels_by_id.update({
            channel["id"]: channel["name"]
            for channel in response.get("channels", [])
        })
    except Exception as e:
        print("Could not load Slack channels:", e)

    for alert in load_store().get("alerts", {}).values():
        channel_id = alert.get("channel_id")
        channel_name = alert.get("channel_name")
        if channel_id and channel_name:
            channels_by_id.setdefault(channel_id, channel_name)

    channel_options = [
        {"id": channel_id, "name": channel_name}
        for channel_id, channel_name in sorted(
            channels_by_id.items(), key=lambda item: item[1].lower()
        )
    ]
    return jsonify({"channels": channel_options})


@flask_app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    requested_channel = (data.get("channel") or data.get("channel_id") or "").strip()

    if not question:
        return jsonify({"answer": "Ask a question about recent Slack activity."}), 400
    if not requested_channel:
        return jsonify({"answer": "Choose a Slack channel to ask about."}), 400

    store = load_store()
    channel_key = requested_channel.removeprefix("#").lower()
    all_messages = store.get("raw_messages", [])
    if channel_key == "all":
        recent_messages = all_messages[-20:]
    else:
        recent_messages = [
            message for message in all_messages
            if channel_key in {
                str(message.get("channel", "")).lower(),
                str(message.get("channel_name", "")).lower(),
            }
        ][-20:]
    if add_missing_user_names(recent_messages, bolt_app.client):
        save_store(store)
    context = "\n".join([
        f"#{message.get('channel_name', message.get('channel'))} - "
        f"{message.get('user_name') or 'Someone'}: {message.get('text')}"
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

    return jsonify({"answer": answer, "channel": requested_channel})


if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
