# AI retrieval, agent and self-evaluation demo

This demo will address a Technical Assessment by building the following features:

1. A simple chat loop that responds and also uses token-level streaming to display metrics around prompt token usage, total cost and round-trip latency for each turn.
2. Ingest, embed, and index documents for retrieval-augmented QA.
3. Build an autonomous trip planning agent with tool use calling external services, constraint handling, and structured JSON output.
4. Build a self-healing code generation loop with test-driven retries.
5. [Optional] Containerised evaluation dashboard for latency, cost, retrieval accuracy, and agent performance.

## How to use

### Setup

1. Clone the repo
```bash
git clone git@github.com:muppsy007/datacom-ai.git
cd datacom-ai
```

2. Create `.env` from the sample and add your credentials
```bash
cp .env.sample .env
```

3. Create a virtual environment and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run tests
```bash
pytest -q
```

### Ingest corpus (required for Task 3.2 QA)

This downloads ~50MB of text and generates embeddings. Takes approximately 5–7 minutes. Performing this in Docker (E.G. with a Streamlit button) was very slow and would likely produce variable results depending on individual users' Docker resource allocation.

```bash
python task32/fetch.py
python task32/ingest.py
```

### Run Streamlit UI via Docker
```bash
docker compose up --build
```

Visit: http://localhost:8501/

> Note: The corpus must be ingested locally before starting Docker. Docker mounts the data directory from your local machine.

## All tasks can also be run from CLI

```bash
# Task 3.1 - Chat
python task31/chat.py

# Task 3.2 - Corpus QA
python task32/fetch.py
python task32/ingest.py
python task32/qa.py
python task32/evaluate.py

# Task 3.3 - Travel Agent
python task33/travel_planner.py

# Task 3.4 - Rust code assistant
python task34/code_assistant.py
```

## Intentional choices
**Global**
* Commits direct to main solely to avoid unnecessary branch ceremony
* Data storage mechanisms matching data use case
  * SQLite for chat and other relational storage
  * Chroma for vectors only 

**Task 3.1**
* LLM $ rates per million are hard coded in chat.py but would ideally be abstracted out to a dict so changing model would not require business logic change.

**Task 3.2**
* Chroma over FAISS/pgvector for dev speed and simplicity. Runs locally and compatible with Docker volume mounts
* Example document "Star Wars — Revenge of the Sith" is partially hidden behind a login. 
* Used Project Gutenberg (https://gutenberg.org/) and large PDF docs to find 50M of corpus
* Use `sentence-transformers` local all-MiniLM-L6-v2 model for embeddings (zero cost, but slower)
* Building OpenAI client is done in a couple of places. In a larger system this would go in a factory
* Chunk size is 1000 chars with 200 char overlap to preserve context at boundaries
* Raw data has idempotency based on file size thresholds. Re-running `task32/fetch.py` will only download missing or corrupt files

**Task 3.3**
* Mocked all APIs. Aside from most requiring account setup, this offered deterministic results and testable outcomes
* There were a number of ways scratchpad could be handled, including LangChain. But I went with manual implementation
* `reasoning` field on every tool schema forces the model to emit `steps_scratchpad` tool/reasoning pairs
* Store log record with scratchpad, itinerary cost, tokens used and token cost in `metrics.db`
* Budget enforcement is handled by `calculate_total` tool rather than the model's arithmetic

**Task 3.4**
* GTP-4o is pretty good at coding tasks. Rather than try and find a prompt that reliably fails, I introduced the `--force-fail` arg to the `code-assistant.py` entrypoint. This will always fail the first time by adding a syntax error, to demonstrate retries
* Locally, the code assistant spins up a docker container for Rust, but via the Docker/Streamlit app, it uses native installation to avoid Docker-in-Docker problems

## Potential improvements
* In a production system, we might consider a rolling summary buffer to preserve long chat context without unbounded token growth
* Postgres/pgvector for both relational and vector storage. This would consolidate two storage engines, simplifying deployment/backup/observability
* Using faster (but not free) model for corpus ingest, such as OpenAI `text-embedding-3-small`
* Async/streaming for the Streamlit UI or async frontend in general
* More robust error handling, retry and circuit breaker logic for rate limits and failures
* Eval beyond Recall@5. Task 3.2 would likely benefit from LLM-as-judge eval

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