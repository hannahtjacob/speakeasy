# SpeakEasy

SpeakEasy is a voice-first Slack assistant for hands-free Slack alerts. The MVP lets a user control alerts per channel, hear Groq-generated summaries, and ask questions about recent channel activity through a browser companion app.

## Current Stack

- Backend: Python, Flask, Slack Bolt
- LLM summaries: Groq
- Frontend: static HTML/CSS/JS with browser speech synthesis
- Local tunnel: ngrok
- Runtime store: `backend/store.json` generated locally and ignored by Git

## Local Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `backend/.env`:

```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
GROQ_API_KEY=your-groq-api-key
PORT=3000
```

Run the backend:

```bash
cd backend
source .venv/bin/activate
python app.py
```

Expose it to Slack:

```bash
ngrok http 3000
```

Set the Slack slash command and event request URL to:

```text
https://YOUR-NGROK-URL/slack/events
```

Open the frontend:

```text
frontend/index.html
```

## Slack App Requirements

- Slash command: `/speak-alerts`
- Slash command URL: `/slack/events`
- Event subscription URL: `/slack/events`
- Bot scopes: `commands`, `chat:write`, `channels:history`, `channels:read`, and `users:read`
- Subscribe to message events needed for the demo workspace/channel
- Reinstall the Slack app after changing commands, scopes, or events

## Tests

Run the automated backend tests without contacting Slack or Groq:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests
```

## Current Status

- Done: backend health endpoint
- Done: `/speak-alerts on`, `/speak-alerts off`, and `/speak-alerts status`
- Done: local JSON store helpers
- Done: channel-scoped Slack message capture and history cleanup
- Done: active Slack bot and Groq-powered Q&A
- Done: companion page speaking every exact Slack message with channel and sender names
- Done: channel-scoped and all-channel Q&A with spoken summaries
- Done: automated backend tests

## Next TODOs

- Test the complete Slack-to-browser demo flow three times
- Add priority alert detection
- Polish the companion interface for the recorded demo
- Finalize architecture diagram, demo video, and Devpost writeup
