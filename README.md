# SpeakEasy

SpeakEasy is a voice-first Slack assistant for hands-free Slack alerts. The MVP lets a user turn `/speak-alerts` on or off, captures Slack messages, summarizes them with Groq, and exposes the latest summary to a small browser companion app that speaks it aloud with the Web Speech API.

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
- Subscribe to message events needed for the demo workspace/channel
- Reinstall the Slack app after changing commands, scopes, or events

## Current Status

- Done: backend health endpoint
- Done: `/speak-alerts on` and `/speak-alerts off`
- Done: local JSON store helpers
- Done: Slack message capture
- Done: Groq summarization path
- Done: companion page polling latest summary and speaking it
- Blocked: current local Slack bot token is inactive and must be replaced or the Slack app must be restored

## Next TODOs

- Replace `backend/.env` with active Slack app credentials and a Groq key
- Recreate or restore the Slack app if the previous app was deleted
- Verify `/speak-alerts` and Slack event subscriptions with ngrok
- Scope spoken alerts to enabled users/channels instead of summarizing whenever any user has alerts enabled
- Add voice query support
- Finalize architecture diagram, demo video, and Devpost writeup
