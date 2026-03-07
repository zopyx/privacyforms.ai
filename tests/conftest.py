"""Pytest fixtures and configuration."""

import pytest


@pytest.fixture
def mock_models(monkeypatch):
    """Fixture to mock llm.get_models() for testing."""

    class MockModel:
        def __init__(self, model_id, name):
            self.model_id = model_id
            self._name = name

        def __str__(self):
            return f"<TestModel: {self._name}>"

    def _make_mock_models():
        return [
            MockModel("gpt-4o", "GPT-4 Omni"),
            MockModel("claude-3-opus", "Claude 3 Opus"),
            MockModel("llama2", "Llama 2"),
        ]

    monkeypatch.setattr("llm.get_models", _make_mock_models)
    return _make_mock_models
