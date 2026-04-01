"""
Task 3.1 - Conversational Core
This is the main chat interface - run by calling `python chat.py` and typing your message
Uses OPENAI_BASE_URL, OPENAI_API_KEY and MODEL_NAME for calls to LLM (see .env)
Conversations are stored in a SQLite database located at CHAT_DB_PATH
"""
import os
import sqlite3
import sys
import time
from dataclasses import dataclass

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

def main():
    client, config = bootstrap()
    conn = init_db(config.db_path)
    
    while True :
        user_input = prompt.ask("[cyan]You")
        if user_input.strip().lower() in ("quit", "exit"):
            console.print("[bold red]User exited. Goodbye")
            break
        
        # Save the user message
        save_message(conn, "user", user_input)
        
        # Get the message history
        message_history = load_messages(conn)

        # Build the system prompt
        messages: list[ChatCompletionMessageParam] = [{
            "role": "system", 
            "content": (
                "You are an exuberant and helpful chat assistant. "
                "Keep your responses short and concise"
            ),
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
        ) #type: ignore[call-overload]

        response = ""
        usage = None
        console.print("[yellow]ChatBot: ", end="")
        for chunk in stream:
            if not chunk.choices:
                if chunk.usage:
                    usage = chunk.usage
                continue
            token = chunk.choices[0].delta.content
            if token is not None:
                console.print(token, end="", markup=False)
                response += token

        # Get total time spent with LLM request
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Work out cost based on fixed per/million cost
        # Refer https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
        if usage:
            # In a situation where we have multiple models, these prices should go in a dict
            cost = (usage.prompt_tokens * 2.50 + usage.completion_tokens * 10.00) / 1_000_000

            # Build the usage line and output
            stats = (
                f"[stats] prompt={usage.prompt_tokens} "
                f"completion={usage.completion_tokens} "
                f"cost=USD${cost:.6f} "
                f"latency={elapsed_ms:.0f}ms"
            )
            console.print(stats, style="dim")

        # Save the message and print and empty line for the next "You:" prompt
        save_message(conn, "assistant", response)
        console.print()

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

    # DEFAULT - if env value for db path is not set, use "chat.db"
    db_path = os.getenv("CHAT_DB_PATH") or "chat.db"

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )              
    """)
    conn.commit()
    return conn

# Save a message to the database
def save_message(conn: sqlite3.Connection, role: str, content: str) -> None:
    conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
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


if __name__ == "__main__":
    main()
