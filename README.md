# AI retrieval, agent and self-evaluation demo

This demo will address a Technical Assessment by building the following features:

1. A simple chat loop that responds and also uses token-level streaming to display metrics around prompt token usage, total cost and round-trip latency for each turn.
2. Ingest, embed, and index documents for retrieval-augmented QA.
3. Build an autonomous trip planning agent with tool use calling external services, constraint handling, and structured JSON output.
4. Build a self-healing code generation loop with test-driven retries.
5. [Optional] Containerised evaluation dashboard for latency, cost, retrieval accuracy, and agent performance.

## How to use
**Task 3.1:**

From project root, run `python chat.py` and start a conversation. Confirm running context by stating your first name and asking the LLM to recall your name a few messages later.

## Intentional choices
**Global**
* Commits direct to main instead of branch/rebase solely to avoid unnecessary ceremony
* Data storage mechanisms matching data use case
  * SQLite for chat and other relational storage
  * Chroma for vectors only 
* Avoid more production-ready Postgres + pgvector (which could do both) to make stretch task Docker setup simpler

**Task 3.1**
* Chat database is stored in project root rather than in a directory to avoid permission problems for the assessor
* LLM $ rates per million are hard coded in chat.py but would ideally be abstracted out to a dict so changing model would not require business logic change.

## Potential improvements
* In a production system, we might consider a rolling summary buffer so earlier context than N is not completely omitted from future prompts.
* Postgres/pgvector for both relational and vector storage.