# AI retrieval, agent and self-evaluation demo

This demo will address a Technical Assessment by building the following features:

1. A simple chat loop that responds and also uses token-level streaming to display metrics around prompt token usage, total cost and round-trip latency for each turn.
2. Ingest, embed, and index documents for retrieval-augmented QA.
3. Build an autonomous trip planning agent with tool use calling external services, constraint handling, and structured JSON output.
4. Build a self-healing code generation loop with test-driven retries.
5. [Optional] Containerised evaluation dashboard for latency, cost, retrieval accuracy, and agent performance.

## How to use
TBC

## Intentional choices
* Data storage mechanisms matching data use case
  * SQLite for chat and other relational storage
  * Chroma for vectors only
  * Avoid Postgres and pgvector (which could do both) to make stretch task Docker setup simpler 

## Potential improvements
* In a production system, we might consider a rolling summary buffer so earlier context than N is not completely omitted from future prompts.
* Postgres/pgvector for both relational and vector storage.