# AI retrieval, agent and self-evaluation demo

This demo will address a Technical Assessment by building the following features:

1. A simple chat loop that responds and also uses token-level streaming to display metrics around prompt token usage, total cost and round-trip latency for each turn.
2. Ingest, embed, and index documents for retrieval-augmented QA.
3. Build an autonomous trip planning agent with tool use calling external services, constraint handling, and structured JSON output.
4. Build a self-healing code generation loop with test-driven retries.
5. [Optional] Containerised evaluation dashboard for latency, cost, retrieval accuracy, and agent performance.

## How to use

### Setup

1. `git clone git@github.com:muppsy007/datacom-ai.git`
2. Setup .env. `cp .env.sample .env` and add your OPENAI_BASE_URL and OPENAI_API_KEY
3. TBC - Docker setup for stretch goal (and likely Rust container)

### Run tests

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

### Task 3.1

```
python task31/chat.py
```

* Start a conversation. 
* Note usage data after each reply. 
* Confirm sliding window context by stating your first name and asking the LLM to recall your name a few messages later.

### Task 3.2

**Step 1 - Fetch corpus documents**

```
python task32/fetch.py
```
**Step 2 - Ingest corpus into vector DB**

```
python task32/ingest.py
```

**Step 3 - Query the corpus and get an answer from the LLM**

```
python task32/qa.py
```

Example questions based on corpus
```
What is the optimal tyre pressure for a Holden Colorado?
```

```
Which dictionary does the US government adhere to for official spelling?
```

```
How many books are in the New Testament?
```

**Supplementary - evaluate retreival pipeline (Recall@5)**

```
python task32/evaluate.py
```

### Task 3.3

```
python task33/travel_planner.py
```

Enter a natural language trip request including a budget, e.g.:
```
Plan a 2-day trip to Auckland from Christchurch, departing 2025-06-01 and returning 2025-06-03, for under NZ$500
```

### Task 3.4

```
python task34/code_assistant.py --force-fail
```

Enter a Rust coding task:
```
write a Rust struct called Matrix that supports 2x2 matrix multiplication, with tests
``` 

You will find your generated code in `task34/tmp/attempt_x`


## Intentional choices
**Global**
* Commits direct to main solely to avoid unnecessary branch ceremony
* Data storage mechanisms matching data use case
  * SQLite for chat and other relational storage
  * Chroma for vectors only 

**Task 3.1**
* LLM $ rates per million are hard coded in chat.py but would ideally be abstracted out to a dict so changing model would not require business logic change.

**Task 3.2**
* Example document "Star Wars — Revenge of the Sith" is partially hidden behind a login. 
* Used Project Gutenberg (https://gutenberg.org/) and large PDF docs to find 50M of corpus
* Use `sentence-transformers` local all-MiniLM-L6-v2 model for embeddings (zero cost, but slower)
* Building OpenAI client is done in a couple of places. In a larger system this would go in a factory
* Chunk size is 1000 chars with 200 char overlap to preserve context at boundaries

**Task 3.3**
* There were a number of ways scratchpad could be handled, including LangChain. But I went with manual implementation
* `reasoning` field on every tool schema forces the model to emit `steps_scratchpad` tool/reasoning pairs
* Store log record with scratchpad, itinerary cost, tokens used and token cost in `metrics.db`
* Budget enforcement is handled by `calculate_total` tool rather than the model's arithmetic

**Task 3.3**
* gtp-4o is prett=y good at coding tasks. Rather than try and find a prompt that reliably fails, I introduced the `--force-fail` arg to the `code-assistant.py` entrypoint. This will always fail the first time by adding a syntax error, to demonstrate retries

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