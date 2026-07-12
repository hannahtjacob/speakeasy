# Architecture

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

## Components

- Slack app: owns `/speak-alerts`, message events, signing secret, and bot token.
- Flask backend: receives Slack requests at `/slack/events` and exposes `/health`, `/api/latest-summary`, and `/api/ask`.
- Slack Bolt: verifies Slack request signatures and routes slash commands/events.
- Store: local ignored `backend/store.json` containing alert preferences (per user + channel), raw messages, and generated summaries.
- Summarizer: `backend/summarizer.py` calls Groq for short spoken summaries.
- Priority detection: `backend/priority.py` flags messages containing urgency keywords; flagged summaries get a spoken "Urgent"/"Important" prefix.
- Q&A: `backend/qa.py` calls Groq to answer free-form questions about recent channel activity.
- Frontend companion: a phone/watch-styled page that polls the backend, speaks new summaries aloud, offers a Driving Mode toggle (mutes spoken alerts when off), and lets the user ask questions by voice.

## Data Flow

1. User runs `/speak-alerts on` for a channel.
2. Backend stores that alerts are enabled for that user + channel pair.
3. Slack sends message events to `/slack/events`; the backend ignores messages for channels without alerts enabled.
4. Backend stores raw message metadata, runs priority detection, and generates a spoken summary via Groq.
5. Frontend polls `/api/latest-summary` and speaks new summaries aloud (unless Driving Mode is off).
6. User can also type a question into "Ask SpeakEasy," which posts to `/api/ask` and speaks back a Groq-generated answer grounded in recent messages.

## Security Notes

- Real credentials live only in `backend/.env`, which is ignored by Git.
- Runtime message data lives in `backend/store.json`, which is ignored by Git.
- Slack request signing remains enabled.
- Slack token startup verification is disabled so local development can start without calling Slack during app boot.
