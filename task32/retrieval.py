
'''
Task 3.2 - RAG QA
The main query file. Use a question to retrieve closest matches from the corpus
'''
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


_default_db_path = str(Path(__file__).resolve().parent.parent / "metrics.db")
conn = init_retrieval_db(os.getenv("DB_PATH") or _default_db_path)


def retrieve(query: str, n_results: int = 5, source: str = "qa") -> QueryResult:
    start = time.perf_counter()

    collection = chroma_client.get_collection(name="book_corpus")
    embedding: list[float] = model.encode(query).tolist() # type: ignore
    results = collection.query(query_embeddings=[embedding], n_results=n_results)

    latency_ms = (time.perf_counter() - start) * 1000
    conn.execute(
        "INSERT INTO retrieval_runs (query, latency_ms, source) VALUES (?, ?, ?)",
        (query, latency_ms, source),
    )
    conn.commit()

    return results

def main():
    start = time.time()
    results = retrieve("Did Ahab ever catch the whale?")
    console.print(f"Query time: {(time.time() - start) * 1000:.0f}ms")  
    console.print(results)

if __name__ == "__main__":
    main()