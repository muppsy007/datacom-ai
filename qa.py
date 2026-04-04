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

dotenv.load_dotenv()
console = Console()
prompt = Prompt()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)

def main():
    # Ask endless questions until exit is requested
    try:
        while True:
            question = prompt.ask("\n[bold cyan]Ask me a question (or 'exit' to quit)")
            if question.strip().lower() in ("quit", "exit"):
                console.print("[bold red]User exited. Goodbye")
                break
        
            start = time.time()
            results = retrieve(question)
            retrieve_ms = (time.time() - start) * 1000

            if not results["documents"] or not results["metadatas"]:
                console.print("[red]No results found[/red]")
                return

            # We have the results from our vector db. Build context for LLM
            context = ""
            for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                context += f"[{i+1}] {meta['title']} (chunk {meta['chunk_index']}):\n{doc}\n\n"

            # Make the LLM request and get the response
            start = time.time()

            system_prompt = (
                "You are a helpful assistant. Answer the question provided by the user"
                "If the answer cannot be found in the context, say "
                "'I don't have enough information in my corpus to answer that question.' "
                "Do not use any knowledge outside the provided context."
            )
            
            response = client.chat.completions.create(
                model=os.environ["MODEL_NAME"],
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n {context}\n\nQuestion: {question}",
                    },
                ]
            )
            llm_ms = (time.time() - start) * 1000
            
            # Output LLM answers
            answer = response.choices[0].message.content
            console.print(f"[bold green]Answer: {answer}")

            # Output sources
            console.print("\n[bold]Sources:[/bold]")
            for i, meta in enumerate(results["metadatas"][0]):
                console.print(f"  [{i+1}] {meta['title']}, chunk {meta['chunk_index']}")

            # Output timings
            console.print(f"\nRetrieval: {retrieve_ms:.0f}ms | LLM: {llm_ms:.0f}ms", style="dim")
    except KeyboardInterrupt:                                                                                                                     
      console.print("\n[bold red]User exited. Goodbye")


if __name__ == "__main__":
    main()