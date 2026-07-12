PRIORITY_KEYWORDS = [
    "urgent",
    "asap",
    "deadline",
    "blocked",
    "production",
    "broken",
    "review",
    "today",
    "tomorrow",
    "important"
]


def is_priority_message(text):
    lower = text.lower()
    return any(keyword in lower for keyword in PRIORITY_KEYWORDS)
