"""Day-one check: can this machine reach the model provider with the key in .env?

Run from the project folder:  python -m scripts.check_model
Exit codes: 0 = reply received, 1 = the call failed, 2 = a setting is missing.
"""
from __future__ import annotations

import sys

from openai import NotFoundError

from src import config
from src.llm import available_models, chat


def main() -> int:
    try:
        # Reasoning models spend part of the token allowance thinking, so leave room for the answer
        result = chat([{"role": "user", "content": "Reply with the word ready."}], max_tokens=256)
    except config.ConfigError as exc:
        print(f"Setup problem: {exc}")
        return 2
    except NotFoundError as exc:
        print(f"The model set in .env is not available to this key: {exc}")
        try:
            print("Models this key can use:\n  " + "\n  ".join(available_models()))
        except Exception as list_exc:  # listing is a convenience; never hide the original problem
            print(f"(Could not list models: {type(list_exc).__name__}: {list_exc})")
        return 1
    except Exception as exc:  # network, authentication, or rate limit after the SDK's retries
        print(f"The call failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"Provider: {result['provider']}   model: {result['model']}   latency: {result['latency_s']}s")
    text = result["text"].strip()
    if not text:
        print(f"The reply was empty (finish_reason={result['finish_reason']!r}). If that says 'length', "
              "the model used its whole allowance thinking: set LLM_REASONING_EFFORT=low in .env.")
        return 1
    print(f"Reply: {text!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
