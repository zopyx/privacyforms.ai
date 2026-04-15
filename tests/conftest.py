"""Pytest fixtures and configuration."""

import logging
import sys
from typing import Any

import pytest


def pytest_configure() -> None:
    """Configure logging so prompt logs are emitted to stderr without extra formatting."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("privacyforms_ai")
    logger.setLevel(logging.DEBUG)
    if not any(
        isinstance(h, logging.StreamHandler) and h.stream is sys.stderr for h in logger.handlers
    ):
        logger.addHandler(handler)


@pytest.fixture
def mock_models(monkeypatch) -> None:
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


@pytest.fixture
def mock_response() -> Any:
    """Fixture providing a mock response class."""

    class MockResponse:
        def __init__(self, text="Hello!"):
            self._text = text

        def text(self):
            return self._text

    return MockResponse


@pytest.fixture
def mock_model(mock_response) -> Any:
    """Fixture providing a mock model class."""

    class MockModel:
        model_id = "gpt-4o"

        def __init__(self, response_text="Hello!"):
            self._response_text = response_text

        def prompt(self, prompt, system=None, attachments=None):
            return mock_response(self._response_text)

    return MockModel


@pytest.fixture
def mock_conversation(mock_response) -> Any:
    """Fixture providing a mock conversation class."""

    class MockConversation:
        def __init__(self, responses=None, system=None):
            self.system = system
            self.responses = responses if responses is not None else ["Hello!"]
            self.index = 0

        def prompt(self, prompt, attachments=None):
            response = self.responses[self.index % len(self.responses)]
            self.index += 1
            return mock_response(response)

    return MockConversation
