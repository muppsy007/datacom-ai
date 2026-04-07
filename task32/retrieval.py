'''
Task 3.2 - RAG QA
The main query file. Use a question to retrieve closest matches from the corpus
'''
import json
import logging
import os
import sqlite3
import time
from pathlib import Path

import chromadb
from chromadb.api.types import QueryResult
from dotenv import load_dotenv
from rich.console import Console
from sentence_transformers import SentenceTransformer

load_dotenv()

# Supress the HF warning about not being authenticated
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

console = Console()
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parent / "data" / "chroma"))


def init_retrieval_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS retrieval_runs (
            id INTEGER PRIMARY KEY,
            query TEXT,
            latency_ms REAL,
            source TEXT,
            passed INTEGER,
            returned_sources TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


_default_db_path = str(Path(__file__).resolve().parent.parent / "metrics.db")


def save_retrieval_run(
    query: str,
    latency_ms: float,
    source: str = "qa",
    passed: int | None = None,
    returned_sources: str | None = None,
) -> None:
    """Write a retrieval run record to the database."""
    conn = init_retrieval_db(os.getenv("DB_PATH") or _default_db_path)
    conn.execute(
        "INSERT INTO retrieval_runs (query, latency_ms, source, passed, returned_sources) "
        "VALUES (?, ?, ?, ?, ?)",
        (query, latency_ms, source, passed, returned_sources),
    )
    conn.commit()


def retrieve(query: str, n_results: int = 5) -> tuple[QueryResult, float]:
    start = time.perf_counter()

    collection = chroma_client.get_collection(name="book_corpus")
    embedding: list[float] = model.encode(query).tolist() # type: ignore
    results = collection.query(query_embeddings=[embedding], n_results=n_results)

    latency_ms = (time.perf_counter() - start) * 1000

    return results, latency_ms

def main():
    results, latency_ms = retrieve("Did Ahab ever catch the whale?")
    returned_source_ids = [meta["source_id"] for meta in results["metadatas"][0]]
    save_retrieval_run(
        query="Did Ahab ever catch the whale?",
        latency_ms=latency_ms,
        returned_sources=json.dumps(returned_source_ids),
    )
    console.print(f"Query time: {latency_ms:.0f}ms")
    console.print(results)

if __name__ == "__main__":
    main()