import re

from llm import call_llm, create_user_message, create_assistant_message, build_messages
from config import langfuse


def extract_final_answer(raw: str) -> str:
    """Extract the last clean paragraph block as the final answer."""
    # Remove chain-of-thought / thinking blocks
    text = re.sub(r"<think>.*?", "", raw, flags=re.DOTALL | re.IGNORECASE)
    # Split into paragraphs (blank-line separated)
    lines = text.split("\n")
    paragraphs = []
    current = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []
    if current:
        paragraphs.append(" ".join(current))
    # Return the last paragraph — the actual answer
    return paragraphs[-1] if paragraphs else raw.strip()


def chat():
    history = []
    print("Rampage Chatbot is here to help you")
    print("Type 'exit' to quit.\n")

    while True:
        user_msg = input("You: ").strip()
        if user_msg.lower() in ("exit", "quit"):
            break
        if not user_msg:
            continue

        try:
            messages = build_messages(history, user_msg)
            raw_reply = call_llm(messages)
            reply = extract_final_answer(raw_reply)
            history.append(create_user_message(user_msg))
            history.append(create_assistant_message(reply))
            print(f"\nRampage: {reply}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    langfuse.flush()


if __name__ == "__main__":
    chat()
