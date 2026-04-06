'''
Task 3.2 - RAG QA
The primary Question Answering service.  Given a question, this retrieves the most relevant passages
from the corpus. Then we will send the question with passages to our LLM to generate an answer
with citations.
'''
import os
import time

import dotenv
from openai import OpenAI
from rich.console import Console
from rich.prompt import Prompt

from retrieval import retrieve

console = Console()
prompt = Prompt()

QA_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the question provided by the user"
    "If the answer cannot be found in the context, say "
    "'I don't have enough information in my corpus to answer that question.' "
    "Do not use any knowledge outside the provided context."
)


def create_client() -> OpenAI:
    """Create an OpenAI client from environment variables."""
    dotenv.load_dotenv()
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )


def ask_question(question: str, client: OpenAI) -> dict:
    """Answer a question using RAG retrieval and an LLM.

    Returns a dict with keys: answer, sources, retrieve_ms, llm_ms
    """
    start = time.time()
    results = retrieve(question)
    retrieve_ms = (time.time() - start) * 1000

    if not results["documents"] or not results["metadatas"]:
        return {
            "answer": "No results found",
            "sources": [],
            "retrieve_ms": retrieve_ms,
            "llm_ms": 0.0,
        }

    # We have the results from our vector db. Build context for LLM
    context = ""
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        context += f"[{i+1}] {meta['title']} (chunk {meta['chunk_index']}):\n{doc}\n\n"

    # Make the LLM request and get the response
    start = time.time()

    response = client.chat.completions.create(
        model=os.environ["MODEL_NAME"],
        messages=[
            {
                "role": "system",
                "content": QA_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"Context:\n {context}\n\nQuestion: {question}",
            },
        ]
    )
    llm_ms = (time.time() - start) * 1000

    answer = response.choices[0].message.content
    sources = [
        {"title": meta["title"], "chunk_index": meta["chunk_index"]}
        for meta in results["metadatas"][0]
    ]

    return {
        "answer": answer,
        "sources": sources,
        "retrieve_ms": retrieve_ms,
        "llm_ms": llm_ms,
    }


def main():
    client = create_client()

    # Ask endless questions until exit is requested
    try:
        while True:
            question = prompt.ask("\n[bold cyan]Ask me a question (or 'exit' to quit)")
            if question.strip().lower() in ("quit", "exit"):
                console.print("[bold red]User exited. Goodbye")
                break

            result = ask_question(question, client)

            if not result["sources"]:
                console.print("[red]No results found[/red]")
                continue

            console.print(f"[bold green]Answer: {result['answer']}")

            console.print("\n[bold]Sources:[/bold]")
            for i, src in enumerate(result["sources"], 1):
                console.print(f"  [{i}] {src['title']}, chunk {src['chunk_index']}")

            console.print(
                f"\nRetrieval: {result['retrieve_ms']:.0f}ms | LLM: {result['llm_ms']:.0f}ms",
                style="dim",
            )
    except KeyboardInterrupt:
      console.print("\n[bold red]User exited. Goodbye")


if __name__ == "__main__":
    main()