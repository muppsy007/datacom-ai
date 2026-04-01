"""
Task 3.1 - Conversational Core
This is the main chat interface - run by calling `python chat.py` and typing your message
Uses OPENAI_BASE_URL, OPENAI_API_KEY and MODEL_NAME for calls to LLM (see .env)
Conversations are stored in a SQLite database located at CHAT_DB_PATH
"""
import os
import sqlite3
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

console = Console()

@dataclass
class Config:
    db_path: str
    model_name: str

def main():
    client, config = bootstrap()
    conn = init_db(config.db_path)
    
    while True :
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit"):
            console.print("[bold red]User exited. Goodbye")
            break

        save_message(conn, "user", user_input)
        message_history = load_messages(conn)

        console.print(message_history)

# Pull out env variables. Return OpenAI client and a custom Config object for other Config
def bootstrap() -> tuple[OpenAI, Config]:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("MODEL_NAME")

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
def load_messages(conn: sqlite3.Connection, limit: int = 10) -> list[dict[str, str]]:
    cursor = conn.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    
    # We got the most recent n records, but we must flip that so they are in chronological order
    rows.reverse()

    return [{"role": row[0], "content": row[1]} for row in rows]


if __name__ == "__main__":
    main()
