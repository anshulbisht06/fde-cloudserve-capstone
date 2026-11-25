"""The one place that calls the language model.

Groq and OpenRouter both offer an OpenAI-compatible API, so a single client works for either.
Fallback between providers and response caching are added when the generation step is built.
"""
from __future__ import annotations

import time

from openai import OpenAI

from src import config


def client_for(settings: config.ProviderSettings, timeout: float = 30.0, max_retries: int = 3) -> OpenAI:
    """OpenAI-compatible client. The SDK retries rate limits (429), timeouts and 5xx errors with backoff."""
    return OpenAI(api_key=settings.api_key, base_url=settings.base_url,
                  timeout=timeout, max_retries=max_retries)


def chat(messages: list[dict], *, provider_name: str | None = None, temperature: float = 0.0,
         max_tokens: int = 512, timeout: float = 30.0) -> dict:
    """Send one chat request and return the reply text with the details needed for logging."""
    settings = config.provider(provider_name)
    client = client_for(settings, timeout=timeout)
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=settings.model, messages=messages, temperature=temperature, max_tokens=max_tokens,
    )
    return {
        "text": response.choices[0].message.content or "",
        "provider": settings.name,
        "model": response.model or settings.model,
        "latency_s": round(time.perf_counter() - started, 3),
        "usage": response.usage.model_dump() if response.usage else None,
    }
