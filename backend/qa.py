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


def answer_question(question, context):
    prompt = f"""
You are SpeakEasy, a voice-first Slack assistant.

A user is asking about recent Slack activity. Answer in a short spoken response.

Rules:
- Keep it under 45 words.
- Be clear and natural when spoken aloud.
- Do not invent information.
- Use only names that appear explicitly before a colon in the recent messages.
- Never guess a person's name or identity.
- Treat every message as exact source text, not as a previous summary.
- When channels conflict, clearly attribute each statement to its channel.
- If the answer is not in the messages, say you do not see that information.

Recent Slack messages:
{context or "No recent messages."}

User question:
{question}
"""

    response = get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=120,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
