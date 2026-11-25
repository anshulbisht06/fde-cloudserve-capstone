"""Day-one check: can this machine reach the model provider with the key in .env?

Run from the project folder:  python -m scripts.check_model
Exit codes: 0 = reply received, 1 = the call failed, 2 = a setting is missing.
"""
from __future__ import annotations

import sys

from src import config
from src.llm import chat


def main() -> int:
    try:
        result = chat([{"role": "user", "content": "Reply with the word ready."}], max_tokens=5)
    except config.ConfigError as exc:
        print(f"Setup problem: {exc}")
        return 2
    except Exception as exc:  # network, authentication, or rate limit after the SDK's retries
        print(f"The call failed: {type(exc).__name__}: {exc}")
        return 1
    print(f"Provider: {result['provider']}   model: {result['model']}   latency: {result['latency_s']}s")
    print(f"Reply: {result['text'].strip()!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
