"""Tests for the AI class."""

import hashlib
import json
import logging
from pathlib import Path

import pytest

from privacyforms_ai.ai import AI


def parse_prompt_log(caplog) -> dict[str, object]:
    """Parse the most recent prompt log line from captured log records."""
    records = [r for r in caplog.records if r.message.startswith(AI._LOG_PREFIX)]
    assert records, "Expected at least one prompt log line"
    return json.loads(records[-1].message[len(AI._LOG_PREFIX) :])


class TestAI:
    """Test cases for the AI class."""

    def test_get_models_returns_list(self, mock_models):
        """Test that get_models returns a list."""
        models = AI.get_models()
        assert isinstance(models, list)

    def test_get_models_returns_dicts_with_required_keys(self, mock_models):
        """Test that get_models returns dicts with the expected fields."""
        models = AI.get_models()
        assert len(models) == 3

        for model in models:
            assert isinstance(model, dict)
            assert "key" in model
            assert "name" in model
            assert "provider" in model
            assert isinstance(model["key"], str)
            assert isinstance(model["name"], str)
            assert isinstance(model["provider"], str)

    def test_get_models_content(self, mock_models):
        """Test that get_models returns expected model data."""
        models = AI.get_models()

        expected = [
            {"key": "gpt-4o", "name": "TestModel: GPT-4 Omni", "provider": "conftest"},
            {"key": "claude-3-opus", "name": "TestModel: Claude 3 Opus", "provider": "conftest"},
            {"key": "llama2", "name": "TestModel: Llama 2", "provider": "conftest"},
        ]
        assert models == expected

    def test_get_models_empty_list(self, monkeypatch):
        """Test that get_models handles empty model list."""
        monkeypatch.setattr("llm.get_models", lambda: [])
        models = AI.get_models()
        assert models == []


class TestGetModel:
    """Test cases for the get_model method."""

    def test_get_model_success(self, monkeypatch):
        """Test successful model retrieval."""
        mock_model = type("MockModel", (), {"model_id": "gpt-4o"})()

        def mock_get_model(key):
            if key == "gpt-4o":
                return mock_model
            raise Exception("Model not found")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        result = AI.get_model("gpt-4o")
        assert result.model_id == "gpt-4o"

    def test_get_model_not_found(self, monkeypatch):
        """Test that get_model raises exception for invalid key."""

        def mock_get_model(key):
            raise Exception("Model not found")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        with pytest.raises(Exception, match="Model not found"):
            AI.get_model("invalid-model")


class TestGetConversation:
    """Test cases for the get_conversation method."""

    def test_get_conversation_success(self, monkeypatch):
        """Test successful conversation creation."""

        class MockConversation:
            def __init__(self, model):
                self.model = model

        class MockModel:
            model_id = "gpt-4o"

            def conversation(self):
                return MockConversation(self)

        def mock_get_model(key):
            if key == "gpt-4o":
                return MockModel()
            raise Exception("Model not found")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        conversation = AI.get_conversation("gpt-4o")
        assert isinstance(conversation, MockConversation)
        assert conversation.model.model_id == "gpt-4o"

    def test_get_conversation_with_system(self, monkeypatch):
        """Test conversation creation with system prompt."""

        class MockConversation:
            def __init__(self, model):
                self.model = model
                self.system = None

        class MockModel:
            model_id = "gpt-4o"

            def conversation(self):
                return MockConversation(self)

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        conversation = AI.get_conversation("gpt-4o", system="Be helpful")
        assert conversation.system == "Be helpful"

    def test_get_conversation_model_error(self, monkeypatch):
        """Test conversation creation with invalid model."""

        def mock_get_model(key):
            raise Exception("Model not found: test-model")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        with pytest.raises(Exception, match="Model not found"):
            AI.get_conversation("invalid-model")


class TestPromptLogging:
    """Test cases for prompt logging helpers."""

    def test_send_prompt_logs_text_and_system(self, caplog):
        """Test that model prompts are always logged."""
        caplog.set_level(logging.INFO)
        prompt_calls = []

        class MockResponse:
            text = "Hello back!"

        class MockModel:
            model_id = "gpt-4o"

            def prompt(self, prompt, system=None):
                prompt_calls.append((prompt, system))
                return MockResponse()

        response = AI.send_prompt(MockModel(), "Hello", system="Be helpful")
        assert response.text == "Hello back!"
        assert prompt_calls == [("Hello", "Be helpful")]

        payload = parse_prompt_log(caplog)
        assert payload == {
            "kind": "model",
            "model": "gpt-4o",
            "system": "Be helpful",
            "text": "Hello",
        }

    def test_send_prompt_logs_binary_payload_in_short_form(self, caplog):
        """Test that binary payloads are summarized instead of printed raw."""
        caplog.set_level(logging.INFO)
        payload_bytes = b"\x00\x01\x02"
        prompt_calls = []

        class MockResponse:
            text = "Binary accepted"

        class MockModel:
            model_id = "gpt-4o"

            def prompt(self, prompt, attachments=None):
                prompt_calls.append((prompt, attachments))
                return MockResponse()

        AI.send_prompt(MockModel(), "Inspect this", attachments=[payload_bytes])
        assert prompt_calls == [("Inspect this", [payload_bytes])]

        payload = parse_prompt_log(caplog)
        assert payload == {
            "attachments": [
                {
                    "kind": "binary",
                    "sha256": hashlib.sha256(payload_bytes).hexdigest()[:12],
                    "size_bytes": len(payload_bytes),
                }
            ],
            "kind": "model",
            "model": "gpt-4o",
            "text": "Inspect this",
        }

    def test_prompt_with_attachment_logs_short_attachment_summary(self, caplog, tmp_path):
        """Test that file attachments are logged with concise metadata only."""
        caplog.set_level(logging.INFO)
        file_path = tmp_path / "sample.pdf"
        file_path.write_bytes(b"%PDF-1.7")
        prompt_calls = []

        class MockResponse:
            def text(self):
                return "Processed attachment"

        class MockModel:
            model_id = "gpt-4o"

            def prompt(self, prompt, attachments=None):
                prompt_calls.append((prompt, attachments))
                return MockResponse()

        result = AI.prompt_with_attachment(MockModel(), "Review this file", file_path)
        assert result == "Processed attachment"
        assert prompt_calls[0][0] == "Review this file"
        assert len(prompt_calls[0][1]) == 1

        payload = parse_prompt_log(caplog)
        assert payload == {
            "attachments": [
                {
                    "kind": "attachment",
                    "mime_type": "application/pdf",
                    "name": "sample.pdf",
                    "size_bytes": file_path.stat().st_size,
                }
            ],
            "kind": "model",
            "model": "gpt-4o",
            "text": "Review this file",
        }


class TestMimeTypeDetection:
    """Test cases for MIME type detection."""

    def test_detect_mime_type_known_extension(self):
        """Test that known extensions map to the correct MIME type."""
        assert AI._detect_mime_type(Path("document.pdf")) == "application/pdf"
        assert AI._detect_mime_type(Path("image.PNG")) == "image/png"
        assert AI._detect_mime_type(Path("data.json")) == "application/json"

    def test_detect_mime_type_unknown_extension(self):
        """Test that unknown extensions fall back to octet-stream."""
        assert AI._detect_mime_type(Path("archive.unknown")) == "application/octet-stream"
        assert AI._detect_mime_type(Path("no_extension")) == "application/octet-stream"
