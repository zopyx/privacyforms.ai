"""Tests for the AI class."""

import pytest

from privacyforms_ai.ai import AI


class TestAI:
    """Test cases for the AI class."""

    def test_get_models_returns_list(self, mock_models):
        """Test that get_models returns a list."""
        models = AI.get_models()
        assert isinstance(models, list)

    def test_get_models_returns_dicts_with_required_keys(self, mock_models):
        """Test that get_models returns dicts with 'key' and 'name' keys."""
        models = AI.get_models()
        assert len(models) == 3

        for model in models:
            assert isinstance(model, dict)
            assert "key" in model
            assert "name" in model
            assert isinstance(model["key"], str)
            assert isinstance(model["name"], str)

    def test_get_models_content(self, mock_models):
        """Test that get_models returns expected model data."""
        models = AI.get_models()

        expected = [
            {"key": "gpt-4o", "name": "TestModel: GPT-4 Omni"},
            {"key": "claude-3-opus", "name": "TestModel: Claude 3 Opus"},
            {"key": "llama2", "name": "TestModel: Llama 2"},
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
