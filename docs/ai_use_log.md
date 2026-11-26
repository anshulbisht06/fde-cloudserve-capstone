# AI-use log

The course requires every use of AI tools to be declared, and any code not written by me to be attributed.
This log feeds the AI-use declaration in the report. Fill in the last column yourself.

| Date | Tool | What it helped with | What I checked, changed or overrode |
|---|---|---|---|
| 2026-11-26 | Claude (Anthropic) | Summarised the capstone pack; profiled the datasets (counts, outcomes by segment); found that the supplied `requirements.txt` cannot be installed | |
| 2026-11-26 | Claude (Anthropic) | Produced the pinned `requirements.txt` (tested on Python 3.11 and 3.12 for macOS, Linux and Windows), the repository skeleton, `src/config.py`, `src/llm.py`, `scripts/check_model.py`, `tests/test_setup.py` and the CI workflow | |
| 2026-11-26 | Claude (Anthropic) | Switched the default model to `openai/gpt-oss-20b` after Groq's 404 for `llama-3.1-8b-instant`; added reasoning settings, `scripts/list_models.py` and tests | |
| 2026-11-27 | Claude (Anthropic) | Wrote `scripts/discovery_stats.py` and its tests: counts and tables for the Stage 1 workbook (headline figures, outcomes by group, volume against time, data-quality checks) | |
