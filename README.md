# AI retrieval, agent and self-evaluation demo

This demo will address a Technical Assessment by building the following features:

1. A simple chat loop that responds and also uses token-level streaming to display metrics around prompt token usage, total cost and round-trip latency for each turn.
2. Ingest, embed, and index documents for retrieval-augmented QA.
3. Build an autonomous trip planning agent with tool use calling external services, constraint handling, and structured JSON output.
4. Build a self-healing code generation loop with test-driven retries.
5. [Optional] Containerised evaluation dashboard for latency, cost, retrieval accuracy, and agent performance.

## How to use
### Task 3.1

* From project root, run `python chat.py` and start a conversation. 
* Note usage data after each reply. 
* Confirm sliding window context by stating your first name and asking the LLM to recall your name a few messages later.

### Task 3.2

**Step 1 - Fetch corpus documents**

```
python fetch.py
```
**Step 2 - Ingest corpus into vector DB**

```
python ingest.py
```

**Step 3 - Query the corpus and get an answer from the LLM**

```
python qa.py
```

Example questions based on corpus
> What is the optimal tyre pressure for a Holden Colorado?

> Which dictionary does the US government adhere to for official spelling?

> What was the name of the ship in Moby Dick?

**Supplementary - evaluate retreival pipeline (Recall@5)**

```
python evaluate.py
```

### Task 3.3

```
python travel_planner.py
```

Enter a natural language trip request including a budget, e.g.:
> Plan a 2-day trip to Auckland from Christchurch, departing 2025-06-01 and returning 2025-06-03, for under NZ$500

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

**Task 3.2**
* Example document "Star Wars — Revenge of the Sith" is partially hidden behind a login. 
* I had to free e-books from Project Gutenberg (https://gutenberg.org/) and large PDF docs from US govt sources to find 50M of corpus
* Use sentence-transformers local all-MiniLM-L6-v2 model for embeddings for initial development (zero cost, but slower)
* Building OpenAI client is done in a couple of places. In a larger system this would go in a factory
* Chunk size is 1000 chars with 200 char overlap to preserve context at boundaries

**Task 3.3**
* There were a number of ways scratchpad could be handled, including LangChain. But I went with manual implementation
* `reasoning` field on every tool schema forces the model to emit `steps_scratchpad` tool/reasoning pairs
* Store log record with scratchpad, itinerary cost, tokens used and token cost in `metrics.db`
* Budget enforcement is handled by the `calculate_total` tool rather than the model's arithmetic

## Potential improvements
* In a production system, we might consider a rolling summary buffer so earlier context than N is not completely omitted from future prompts.
* Postgres/pgvector for both relational and vector storage.

## Corpus Documents
- Car Manual - Holden Colorado MY19 User Manual
- Novel - The Fellowship of the Ring
- Govt Policy - GPO Style Manual 2016
- Govt Policy - GPO Style Manual 2008
- Govt Policy - GPO Style Manual 2000
- Novel - Don Quixote
- Novel - Complete Works of Shakespeare
- Novel - War and Peace
- Novel - Moby Dick
- Novel - Middlemarch
- Novel - Bleak House
- Novel - Great Expectations
- Novel - A Tale of Two Cities
- Novel - Pride and Prejudice
- Novel - The Adventures of Sherlock Holmes
- Novel - Les Misérables
- Religion - The King James Bible
- Novel - David Copperfield
- Novel - The Brothers Karamazov
- Novel - Crime and Punishment