
'''
Task 3.2 - RAG QA
The main query file. Use a question to retrieve closest matches from the corpus
'''
import logging
import time

import chromadb
from chromadb.api.types import QueryResult
from rich.console import Console
from sentence_transformers import SentenceTransformer

# Supress the HF warning about not being authenticated
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

console = Console()
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="data/chroma")

def retrieve(query: str, n_results: int = 5) -> QueryResult:
    collection = chroma_client.get_collection(name="book_corpus")

    embedding: list[float] = model.encode(query).tolist() # type: ignore
    results = collection.query(query_embeddings=[embedding], n_results=n_results)
    return results

def main():
    start = time.time()
    results = retrieve("Did Ahab ever catch the whale?")
    console.print(f"Query time: {(time.time() - start) * 1000:.0f}ms")  
    console.print(results)

if __name__ == "__main__":
    main()