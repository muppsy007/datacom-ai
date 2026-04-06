"""
Task 3.1 - Conversational Core
This is the main chat interface - run by calling `python chat.py` and typing your message
Uses OPENAI_BASE_URL, OPENAI_API_KEY and MODEL_NAME for calls to LLM (see .env)
Conversations are stored in a SQLite database located at MAIN_DB_PATH
"""
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console
from rich.prompt import Prompt

console = Console()
prompt = Prompt()

@dataclass
class Config:
    db_path: str
    model_name: str

# Pull out env variables. Return OpenAI client and a custom Config object for other Config
def bootstrap() -> tuple[OpenAI, Config]:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("MODEL_NAME")

    # Exit early if required env vars are not present
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY is not set. See .env.example")
    if not base_url:
        sys.exit("Error: OPENAI_BASE_URL is not set. See .env.example")
    if not model_name:
        sys.exit("Error: MODEL_NAME is not set. See .env.example")

    default_db_path = str(Path(__file__).resolve().parent.parent / "metrics.db")
    db_path = os.getenv("MAIN_DB_PATH") or default_db_path

    client = OpenAI(api_key=api_key, base_url=base_url)
    config = Config(db_path=db_path, model_name=model_name)

    return client, config

# Connect and prime the database
def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
       CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            role TEXT,
            content TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            cost_usd REAL,
            latency_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# Save a message to the database
def save_message(
    conn: sqlite3.Connection,
    role: str,
    content: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    cost_usd: float | None = None,
    latency_ms: float | None = None,
) -> None:
    conn.execute(
        "INSERT INTO messages (role, content, prompt_tokens, completion_tokens, cost_usd, latency_ms) VALUES (?, ?, ?, ?, ?, ?)",
        (role, content, prompt_tokens, completion_tokens, cost_usd, latency_ms),
    )
    conn.commit()

# Load the last n messages from the database to send as context with the prompt
def load_messages(conn: sqlite3.Connection, limit: int = 10) -> list[ChatCompletionMessageParam]:
    cursor = conn.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    
    # We got the most recent n records, but we must flip that so they are in chronological order
    rows.reverse()

    return [{"role": row[0], "content": row[1]} for row in rows]

SYSTEM_PROMPT = (
    "You are an exuberant and helpful chat assistant. "
    "Keep your responses short and concise"
)


def send_message(
    client: OpenAI,
    config: Config,
    conn: sqlite3.Connection,
    user_input: str,
) -> dict:
    """Send a message to the LLM and return the response with usage metrics.

    Returns a dict with keys: response, prompt_tokens, completion_tokens, cost, latency_ms
    """
    # Save the user message
    save_message(conn, "user", user_input)

    # Get the message history
    message_history = load_messages(conn)

    # Build the system prompt
    messages: list[ChatCompletionMessageParam] = [{
        "role": "system",
        "content": SYSTEM_PROMPT,
    }]
    messages += message_history

    # Start recording time for latency
    start = time.perf_counter()

    # Setup the OpenAI stream
    stream = client.chat.completions.create(
        model=config.model_name,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True}
    )  # type: ignore[call-overload]

    response = ""
    usage = None
    for chunk in stream:
        if not chunk.choices:
            if chunk.usage:
                usage = chunk.usage
            continue
        token = chunk.choices[0].delta.content
        if token is not None:
            response += token

    # Get total time spent with LLM request
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Work out cost based on fixed per/million cost
    # Refer https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
    prompt_tokens = usage.prompt_tokens if usage else None
    completion_tokens = usage.completion_tokens if usage else None
    cost = None
    if usage:
        # In a situation where we have multiple models, these prices should go in a dict
        cost = (usage.prompt_tokens * 2.50 + usage.completion_tokens * 10.00) / 1_000_000

    # Save the assistant message
    save_message(
        conn, "assistant", response,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        latency_ms=elapsed_ms,
    )

    return {
        "response": response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": cost,
        "latency_ms": elapsed_ms,
    }


def main():
    client, config = bootstrap()
    conn = init_db(config.db_path)

    try:
        while True:
            user_input = prompt.ask("[cyan]You")
            if user_input.strip().lower() in ("quit", "exit"):
                console.print("[bold red]User exited. Goodbye")
                break

            console.print("[yellow]ChatBot: ", end="")
            result = send_message(client, config, conn, user_input)
            console.print(result["response"], markup=False)

            if result["cost"] is not None:
                stats = (
                    f"[stats] prompt={result['prompt_tokens']} "
                    f"completion={result['completion_tokens']} "
                    f"cost=USD${result['cost']:.6f} "
                    f"latency={result['latency_ms']:.0f}ms"
                )
                console.print(stats, style="dim")

            console.print()
    except KeyboardInterrupt:
        # Graceful exit on ctrl-c
        console.print("\n[bold red]User exited. Goodbye")

if __name__ == "__main__":
    main()
