import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv("secrets.env")

API_KEY = (os.getenv("API_KEY"))

client = OpenAI(
    base_url="https://api.tokenfactory.us-central1.nebius.com/v1/",
    api_key=API_KEY
)

CONVERSATION_FILE = Path("conversation.json")


def read_conversation(
    file_path: str | Path = CONVERSATION_FILE,
) -> list[dict[str, Any]]:
    """Read the conversation history, returning an empty history if needed."""
    path = Path(file_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as conversation_file:
        contents = conversation_file.read().strip()

    if not contents:
        return []

    try:
        conversation = json.loads(contents)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} contains invalid JSON") from error

    if not isinstance(conversation, list):
        raise ValueError(f"{path} must contain a JSON list of messages")
    if not all(isinstance(message, dict) for message in conversation):
        raise ValueError(f"{path} must contain message objects")

    return conversation


def write_message(
    role: str,
    content: str,
    file_path: str | Path = CONVERSATION_FILE,
) -> dict[str, str]:
    """Append a message to the conversation history and save it to disk."""
    if role not in {"system", "user", "assistant"}:
        raise ValueError("role must be 'system', 'user', or 'assistant'")

    message = {"role": role, "content": content}
    conversation = read_conversation(file_path)
    conversation.append(message)

    path = Path(file_path)
    with path.open("w", encoding="utf-8") as conversation_file:
        json.dump(conversation, conversation_file, indent=2, ensure_ascii=False)
        conversation_file.write("\n")

    return message


def retrieve_response(
    file_path: str | Path = CONVERSATION_FILE,
    model: str = "Qwen/Qwen3.5-397B-A17B",
) -> str:
    """Send the saved conversation to the model and save its response."""
    conversation = read_conversation(file_path)
    response = client.chat.completions.create(
        model=model,
        temperature=0.6,
        top_p=0.95,
        messages=conversation,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty response")

    write_message("assistant", content, file_path)
    return content


def chat() -> None:
    """Run an interactive conversation in the terminal."""
    print("Chat started. Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not user_input:
            continue

        write_message("user", user_input)
        print(f"Assistant: {retrieve_response()}")


if __name__ == "__main__":
    chat()
