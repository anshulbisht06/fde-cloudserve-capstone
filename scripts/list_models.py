"""List the model IDs your key can use, as the provider reports them.

Run from the project folder:  python -m scripts.list_models
Useful when a provider retires a model: pick a replacement from this list and set it in .env.
"""
from __future__ import annotations

import sys

from src import config
from src.llm import available_models


def main() -> int:
    try:
        models = available_models()
    except config.ConfigError as exc:
        print(f"Setup problem: {exc}")
        return 2
    except Exception as exc:
        print(f"Could not list models: {type(exc).__name__}: {exc}")
        return 1
    print("\n".join(models))
    return 0


if __name__ == "__main__":
    sys.exit(main())
