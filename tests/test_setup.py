"""Setup checks: the data is in place and missing configuration fails clearly. No network needed."""
import json

import pytest

from src import config

EXPECTED_RECORDS = {
    "development_tickets.json": 500,
    "validation_tickets.json": 80,
    "ground_truth_responses.json": 200,
    "documentation.json": 29,
}


@pytest.mark.parametrize("filename,count", EXPECTED_RECORDS.items())
def test_dataset_is_present_and_complete(filename, count):
    records = json.loads((config.DATA_DIR / filename).read_text(encoding="utf-8"))
    assert len(records) == count


def test_missing_key_gives_a_clear_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(config.ConfigError, match="GROQ_API_KEY"):
        config.provider()


def test_placeholder_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "your_groq_key_here")
    with pytest.raises(config.ConfigError):
        config.provider("groq")


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nonsense")
    with pytest.raises(config.ConfigError, match="LLM_PROVIDER"):
        config.provider()


def test_provider_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    settings = config.provider("groq")
    assert settings.base_url.startswith("https://")
    assert settings.model == "openai/gpt-oss-20b"
    assert "test-key" not in repr(settings)


def test_groq_reasoning_model_gets_reasoning_options():
    from src.llm import request_options

    settings = config.ProviderSettings("groq", "k", "https://api.groq.com/openai/v1", "openai/gpt-oss-20b")
    options = request_options(settings, max_tokens=256)
    assert options["max_completion_tokens"] == 256
    assert options["reasoning_effort"] in {"low", "medium", "high"}
    assert options["extra_body"] == {"include_reasoning": False}
    assert "temperature" not in options


def test_openrouter_uses_plain_options():
    from src.llm import request_options

    settings = config.ProviderSettings("openrouter", "k", "https://openrouter.ai/api/v1", "some/model:free")
    options = request_options(settings, max_tokens=100, temperature=0.2)
    assert options == {"model": "some/model:free", "max_tokens": 100, "temperature": 0.2}


def test_check_model_reports_a_missing_key(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from scripts import check_model

    assert check_model.main() == 2
    assert "GROQ_API_KEY" in capsys.readouterr().out
