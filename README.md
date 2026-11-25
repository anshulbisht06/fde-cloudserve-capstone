# CloudServe support system — FDE capstone

Capstone project for the Forward Deployed AI Engineering course: an AI-assisted customer-support system for
CloudServe Solutions, a fictional client.

**Status:** setup stage. The six components (ingest, classify, retrieve, route, generate, validate) and the
evaluation harness are added during the build, and this README is updated as each one lands.

## What you need

- Python 3.11 (3.12 also works). Install it from [python.org](https://www.python.org/downloads/) or with
  Homebrew: `brew install python@3.11`.
- Git.
- A free Groq API key from <https://console.groq.com/keys>.
- About 1 GB of disk space, and internet access.

Supported: macOS (Intel on macOS 13 or newer, and Apple Silicon), Linux and Windows. Every package installs
from a prebuilt build; nothing is compiled and PyTorch is not needed.

## Setup on macOS or Linux

Run these from the project folder:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` and replace `your_groq_key_here` with your Groq key.

## Setup on Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

Then open `.env` and replace `your_groq_key_here` with your Groq key.

Activate the environment (`source .venv/bin/activate`, or `.venv\Scripts\Activate.ps1` on Windows) in every
new terminal before running anything below.

## Check the model connection

```bash
python -m scripts.check_model
```

A working setup prints the provider, model and latency, then `Reply: 'ready'` (or similar).
If it prints `Setup problem`, the key is missing from `.env`. If it says the model is not available, it
lists the models your key can use; you can also list them with:

```bash
python -m scripts.list_models
```

Providers retire models: Groq shut down `llama-3.1-8b-instant` on 16 August 2026, which is why the default
is now `openai/gpt-oss-20b`.

## Run the tests

```bash
python -m pytest
```

The tests never call the model provider, so they run without an API key.

## Project layout

```
README.md            setup and run instructions
requirements.in      top-level dependencies
requirements.txt     every dependency pinned (generated from requirements.in)
.env.example         every setting, placeholder values only
src/                 application code
  config.py          settings, read from .env
  llm.py             the one place that calls the language model
scripts/
  check_model.py     day-one check that the model provider answers
  list_models.py     lists the models your key can use
prompts/             versioned prompt library (build/ and evaluation/)
tests/               automated tests, run with python -m pytest
evaluation/          evaluation harness and dated results (results/)
docs/                architecture notes, design decisions, AI-use log
data/                the course datasets (see data/README.md)
storage/             created at runtime; never committed
.github/workflows/   continuous integration
```

## Configuration

All settings live in `.env` (copied from `.env.example`):

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `groq` (default) or `openrouter` |
| `GROQ_API_KEY`, `GROQ_BASE_URL`, `GROQ_MODEL` | Groq connection; default model `openai/gpt-oss-20b` |
| `LLM_REASONING_EFFORT` | how much a reasoning model thinks first: `low` (default), `medium` or `high` |
| `LLM_TEMPERATURE` | optional; sent only when set |
| `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL` | optional fallback provider |
| `EMBEDDING_MODEL` | embedding model for retrieval (`all-MiniLM-L6-v2`) |
| `CHROMA_PATH`, `DATABASE_PATH` | where the vector store and decision log are kept |
| `RETRIEVAL_TOP_K` | how many passages retrieval returns |
| `CONFIDENCE_THRESHOLD` | routing threshold; to be set from the development data |
| `LOG_LEVEL` | logging detail |

## Data

`data/` holds the four course datasets: 500 development tickets, 80 validation tickets, 200 reference
answers and the 29 knowledge-base articles. The hidden 120-ticket assessment set is not included; the
evaluation harness will take any file with the same schema through its `--input` argument.

## AI assistance and attribution

Parts of this repository were drafted with AI assistance (Claude, by Anthropic). Each use is recorded in
`docs/ai_use_log.md`, and the project report contains the full declaration.
