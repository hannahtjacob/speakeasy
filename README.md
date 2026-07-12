# SpeakEasy

SpeakEasy is a hands-free Slack assistant that reads important messages aloud, summarizes channel activity, and answers questions by voice so users do not need to look at their screen in unsafe or inaccessible situations.

## Why it matters

Distracted driving and notification overload create real safety risks. SpeakEasy helps drivers, visually impaired users, people with limited mobility, and hands-busy workers stay connected without touching or reading a screen.

## Features

- `/speak-alerts on/off/status` Slack command, scoped per user and channel
- Slack message listener
- LLM-generated spoken summaries (Groq)
- Priority alert detection with an "Urgent" spoken prefix
- Browser-based text-to-speech companion app styled as a phone/watch companion
- Simulated Driving Mode toggle (mutes spoken alerts when off)
- Voice-friendly Q&A over recent Slack messages ("Ask SpeakEasy")

## Current Stack

- Backend: Python, Flask, Slack Bolt
- LLM summaries + Q&A: Groq
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

## Architecture

```text
Slack message or slash command
       |
       v
Slack Events API / Slash Command
       |
       v
Python Slack Bolt backend (Flask)
       |
       v
Preference store + recent message store (backend/store.json)
       |
       v
Groq summarization / priority detection / Q&A
       |
       v
Companion web app (/api/latest-summary, /api/ask)
       |
       v
Browser text-to-speech (Web Speech API)
```

## Current Status

- Done: backend health endpoint
- Done: `/speak-alerts on`, `/speak-alerts off`, `/speak-alerts status`
- Done: local JSON store helpers
- Done: Slack message capture, gated by per-channel alert preference
- Done: Groq summarization path with priority detection
- Done: companion page polling latest summary and speaking it
- Done: "Ask SpeakEasy" voice Q&A over recent messages
- Done: phone/watch-style companion UI with a Driving Mode toggle

## Next TODOs

- Tighten `backend/priority.py` keyword list (common words like "today"/"tomorrow" currently cause false positives)
- Resolve Slack channel IDs to human-readable names in the frontend instead of a static demo label
- Finalize demo video and Devpost writeup
