'''
Task 3.1 - RAG QA
The main file ingester for the system. This is where we read documents, chunk them and embed
We don't read the document store direct. We use the manifest file to get the files we need to store.
This reads each file, chunks it, create embeddings and stores them in Chroma
'''
import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.types import Metadata
from pypdf import PdfReader
from rich.console import Console
from sentence_transformers import SentenceTransformer

# Supress the HF warning about not being authenticated
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

console = Console()
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parent / "data" / "chroma"))

def main():
    manifest_file = Path(__file__).resolve().parent / "data" / "corpus_manifest.json"
    manifest_json = load_manifest(path=manifest_file)

    # Chroma collection for embeddings
    collection = chroma_client.get_or_create_collection(
        name="book_corpus",
        metadata={"hnsw:space": "cosine"},
    )

    for manifest_entry in manifest_json:

        # Idempotency check. Bail if we've already processed this file
        existing = collection.get(ids=[f"{manifest_entry['id']}_0"])
        if existing["ids"]:
            console.print(f"{manifest_entry['title']}: already ingested, skipping")
            continue

        # Extract the text and build chunks
        document_text = extract_doc_text(manifest_entry=manifest_entry)
        chunks = chunk_text(document_text)

        # Make embeddings
        embeddings = model.encode(chunks, show_progress_bar=True) # type: ignore

        # Store embeddings in the Chroma collection
        # Running in batches of 5000 as Chroma has a default batch size limit of 5461
        batch_size = 5000
        for start in range(0, len(chunks), batch_size):
            end = start + batch_size
            batch_ids = [f"{manifest_entry['id']}_{i}" for i in range(start, min(end, len(chunks)))]
            batch_chunks = chunks[start:end]
            batch_embeddings = embeddings.tolist()[start:end]
            batch_metadatas: list[Metadata] = [
                {
                    "source_id": manifest_entry["id"],
                    "title": manifest_entry["title"],
                    "chunk_index": i,
                }
                for i in range(start, min(end, len(chunks)))
            ]
            collection.add(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
            )

        # Batches complete. Output the chunk and embedding spec    
        console.print(
            f"{manifest_entry['title']}: {len(chunks)} chunks, embeddings shape {embeddings.shape}"
        )
    
    console.print(f"[bold cyan]Total chunks stored: {collection.count()}")

# Read the manifest file and return a list
def load_manifest(path: Path) -> list[dict[str, Any]]:
    with open(path) as f:
        return json.load(f)
    
# Extract the text from a given document based on the manifest entry for it
def extract_doc_text(manifest_entry: dict[str, Any]):
    file_path = manifest_entry["path"]
    file_extension = manifest_entry["file_extension"]
    text = ""

    if file_path:
        if file_extension == ".pdf":
            reader = PdfReader(file_path)
            text = " ".join([page.extract_text() or "" for page in reader.pages])
        elif file_extension == ".txt":
            text = Path(manifest_entry["path"]).read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
    else:
        raise ValueError("empty file_path in manifest record")
    
    return text

# Chunk a full document text and return a list of string chunks
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunk = text[i : i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

if __name__ == "__main__":
    main()