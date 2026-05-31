import re
import requests
from langfuse import observe

from config import MINIMAX_URL, MODEL, MINIMAX_API_KEY

SYSTEM_PROMPT = (
    "You are a helpful assistant. Give clear, concise answers without mentioning "
    "word counts, token counts, or internal annotations. Do not include meta-commentary."
)


def create_system_message(content: str) -> dict:
    return {"role": "system", "content": content}


def create_user_message(content: str) -> dict:
    return {"role": "user", "content": content}


def create_assistant_message(content: str) -> dict:
    return {"role": "assistant", "content": content}


def build_messages(history: list[dict], user_msg: str) -> list[dict]:
    """Build the full message list for the LLM, including a system prompt."""
    messages = [create_system_message(SYSTEM_PROMPT)]
    messages.extend(history)
    messages.append(create_user_message(user_msg))
    return messages


@observe(capture_input=True, capture_output=True)
def call_llm(messages: list[dict], max_tokens: int = 1024) -> str:
    """Call the LLM API."""
    res = requests.post(
        MINIMAX_URL,
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        json={"model": MODEL, "messages": messages, "max_tokens": max_tokens},
        timeout=30,
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]


def format_response(text: str) -> str:
    """Clean up and structure the LLM response."""
    # Remove annotations like "67 words", "103 words", "Let's count", "Count words:", etc.
    text = re.sub(r"Let's count.*?(?=\n\n|\n[A-Z]|$)", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"Count words?.*?(?=\n\n|\n[A-Z]|$)", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\bWe have \d+ words?\b.*?(?=\n\n|\n[A-Z]|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"\b\d+\s+words?\b", "", text, flags=re.IGNORECASE)
    # Remove numbered counting sequences (lines that are just a number followed by a word)
    text = re.sub(r"^\d+\s+\S+\s*\n?", "", text, flags=re.MULTILINE)
    # Remove parenthetical artifacts like (K8s), (1), etc. in counting contexts
    text = re.sub(r"\([A-Z0-9][\w\-/]*\)", lambda m: m.group(0) if len(m.group(0)) > 5 else "", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text