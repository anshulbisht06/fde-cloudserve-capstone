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


def is_reasoning_model(model: str) -> bool:
    return model.startswith("openai/gpt-oss")


def request_options(settings: config.ProviderSettings, *, max_tokens: int,
                    temperature: float | None = None, reasoning_effort: str | None = None) -> dict:
    """Provider-specific request arguments, kept separate so they can be tested without a network call."""
    options: dict = {"model": settings.model}
    if settings.name == "groq":
        options["max_completion_tokens"] = max_tokens
        if is_reasoning_model(settings.model):
            options["reasoning_effort"] = reasoning_effort or config.REASONING_EFFORT
            # Groq-specific: leave the model's reasoning out of the reply, so content holds only the answer
            options["extra_body"] = {"include_reasoning": False}
    else:
        options["max_tokens"] = max_tokens
    if temperature is not None:
        options["temperature"] = temperature
    return options


def chat(messages: list[dict], *, provider_name: str | None = None, max_tokens: int = 1024,
         temperature: float | None = None, timeout: float = 30.0) -> dict:
    """Send one chat request and return the reply text with the details needed for logging."""
    settings = config.provider(provider_name)
    client = client_for(settings, timeout=timeout)
    if temperature is None:
        temperature = config.TEMPERATURE
    started = time.perf_counter()
    response = client.chat.completions.create(
        messages=messages, **request_options(settings, max_tokens=max_tokens, temperature=temperature),
    )
    choice = response.choices[0]
    return {
        "text": choice.message.content or "",
        "finish_reason": choice.finish_reason,
        "provider": settings.name,
        "model": response.model or settings.model,
        "latency_s": round(time.perf_counter() - started, 3),
        "usage": response.usage.model_dump() if response.usage else None,
    }


def available_models(provider_name: str | None = None) -> list[str]:
    """Model IDs that the configured key can use, as the provider reports them."""
    settings = config.provider(provider_name)
    return sorted(model.id for model in client_for(settings).models.list())
