# Architecture

```text
Slack workspace
  -> /speak-alerts slash command
  -> message events
  -> ngrok HTTPS tunnel
  -> Flask + Slack Bolt backend
  -> backend/store.json
  -> Groq summarizer
  -> /api/latest-summary
  -> browser companion app
  -> Web Speech API
```

## Components

- Slack app: owns `/speak-alerts`, message events, signing secret, and bot token.
- Flask backend: receives Slack requests at `/slack/events` and exposes `/health` plus `/api/latest-summary`.
- Slack Bolt: verifies Slack request signatures and routes slash commands/events.
- Store: local ignored `backend/store.json` containing alert preferences, raw messages, and generated summaries.
- Summarizer: `backend/summarizer.py` calls Groq for short spoken summaries.
- Frontend companion: polls the backend and speaks new summaries aloud.

## Data Flow

1. User runs `/speak-alerts on`.
2. Backend stores that alerts are enabled for the Slack user.
3. Slack sends message events to `/slack/events`.
4. Backend stores raw message metadata and creates a spoken summary.
5. Frontend polls `/api/latest-summary`.
6. Browser reads the latest summary aloud.

## Security Notes

- Real credentials live only in `backend/.env`, which is ignored by Git.
- Runtime message data lives in `backend/store.json`, which is ignored by Git.
- Slack request signing remains enabled.
- Slack token startup verification is disabled so local development can start without calling Slack during app boot.
