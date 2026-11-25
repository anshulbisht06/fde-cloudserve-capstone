# Design decisions

One entry per decision: what was chosen, what else was considered, and why. The report's architecture
section draws on this file.

## D-001 Model provider: Groq, with OpenRouter as an optional fallback

- **Chosen:** Groq's free tier, model `llama-3.1-8b-instant`, through its OpenAI-compatible API.
- **Considered:** OpenRouter free models (the pack's default), a local model.
- **Why:** a full validation run needs roughly 160–240 model calls (80 tickets, 2–3 calls each). In
  November 2026 OpenRouter's free models allowed 50 requests a day on an account that has never bought
  credits, which cannot fit one run. Groq's free tier allowed far more requests per day for this model;
  its tokens-per-minute limit is the one to design around (throttling, retries, caching). A local model
  would make the assessor install and run it too, which puts the gate at risk.
- **Consequence:** the code reads the provider from `.env`, so switching to OpenRouter is a configuration
  change.

## D-002 Embeddings: all-MiniLM-L6-v2 through Chroma's built-in ONNX runtime

- **Chosen:** Chroma's default embedding function, which runs all-MiniLM-L6-v2 with ONNX Runtime.
- **Considered:** `sentence-transformers` (the pack's choice).
- **Why:** it is the same model the brief specifies, without installing PyTorch. The environment installs
  in about 20 seconds and runs on every major platform, including Intel Macs.

## D-003 Python 3.11 and fully pinned dependencies

- **Chosen:** Python 3.11 (3.12 also tested); every package pinned in `requirements.txt`.
- **Why:** the pack's `requirements.txt` cannot be installed (conflicting pins, and versions with no builds
  for Python 3.12). The new file was resolved and checked for macOS (Intel and Apple Silicon), Linux and
  Windows, using prebuilt packages only. `onnxruntime` is held at 1.23.2, the last release with Intel-Mac
  builds (macOS 13 or newer).

## D-004 Decision log in SQLite

- **Chosen:** SQLite through Python's standard library.
- **Considered:** PostgreSQL.
- **Why:** nothing to install or run; the setup guide calls it entirely adequate at this scale.
