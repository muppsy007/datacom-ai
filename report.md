# Design decisions and trade-offs

## Build strategy

Core logic was built and tested as standalone CLI modules first, then wrapped in a Streamlit UI. I did this to keep each task independently testable and ensure the presentation layer was decoupled from business logic. The Streamlit app imports task modules directly, no API layer sits between them.

## Storage

A SQLite database handles chat history, QA telemetry, and trip agent runs. Chroma handles vector storage. Two engines for two jobs. SQLite is stdlib, file-based, and fits relational queries. Chroma is file-based, serverless, and built for embeddings. Consolidating into pgvector would be the wise production choice, but adds infrastructure overhead that I felt wasn't justified here.

## Chat (Task 3.1)

One thing of note here is the context window is 10 messages, not 10 turns. The spec says last N=10 messages. I queried whether that meant 10 messages or 10 turns but didn't get clarification. Ultimately, either proves rolling context, so I went with 10 messages.

## RAG pipeline (Task 3.2)

The corpus is 20 documents (~55MB) sourced from Project Gutenberg and public PDFs. I substituted with equivalent-size texts across fiction, government docs, and my own car manual to test retrieval across diverse content.

Embeddings use `all-MiniLM-L6-v2` locally via `sentence-transformers`. Zero API cost and no external dependency, but slower than a hosted model like OpenAI's `text-embedding-3-small`. For a production system with frequent re-ingestion, the hosted model would be worth the spend.

Chunking is 1000 characters with 200 character overlap. The overlap preserves context at chunk boundaries, which matters for questions that span paragraph breaks.

Evaluation uses Recall@5 against 32 graded questions. This tells me whether the right source document lands in the top 5 results. It does not evaluate answer quality however, and an LLM-as-judge layer would address that gap.

## Agent design (Task 3.3)

The travel planner uses a manual ReAct loop rather than LangChain. This gave me full visibility into the message flow and made the scratchpad trivial to implement. Each tool schema includes a `reasoning` field that forces the model to explain its thinking before acting.

Budget enforcement lives in the `calculate_total` tool, not the model. LLMs can be unreliable with arithmetic. The tool handles overage by removing attraction items until the constraint is met.

All external APIs are mocked. Real APIs would require account setup and produce non-deterministic results, making the agent only testable using mocks anyway.

## Code assistant (Task 3.4)

Rust execution is sandboxed in Docker when running locally. Inside the Streamlit Docker container, a native Rust toolchain is installed instead via Dockerfile. I explored Docker-in-Docker out of interest but it was too slow to be usable. 

GPT-4o is really good at producing code. So much so, getting a failure to demo the retry loop was far too rare to rely on. The `--force-fail` flag deliberately corrupts the first attempt to demonstrate the retry loop. This is surfaced in the UI as a checkbox.

## What I'd change

The README section "Potential improvements" covers this in detail, but the short version: Postgres+pgvector to consolidate storage, async streaming in the UI, hosted embeddings for faster ingest, summary buffer for chat, and richer evaluation beyond Recall@5.