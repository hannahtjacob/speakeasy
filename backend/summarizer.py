import os
from groq import Groq

client = None


def get_client():
    global client
    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        client = Groq(api_key=api_key)
    return client


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

    response = get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=80,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
