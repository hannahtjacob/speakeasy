import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def summarize_message(text, channel_name=None):
    prompt = f"""
You are SpeakEasy, a voice-first Slack safety assistant.

Summarize this Slack message in one short spoken sentence.
The user may be driving, visually impaired, or unable to look at a screen.

Rules:
- Keep it under 20 words.
- Sound natural when read aloud.
- Mention urgency if the message seems urgent.
- Do not include markdown.
- Do not say "Slack message says."

Channel: {channel_name or "unknown"}
Message: {text}
"""

    response = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=80,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()
