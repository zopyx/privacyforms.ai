"""Tests for the CLI."""

import json
import logging
from typing import Any

import pytest
from click.testing import CliRunner

from privacyforms_ai import __version__
from privacyforms_ai.ai import AI
from privacyforms_ai.cli import cli


def parse_prompt_logs(caplog) -> list[dict[str, Any]]:
    """Parse prompt logs from captured log records."""
    return [
        json.loads(record.message[len(AI._LOG_PREFIX) :])
        for record in caplog.records
        if record.message.startswith(AI._LOG_PREFIX)
    ]


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for the Click CLI runner."""
    return CliRunner()


class TestModelsCommand:
    """Test cases for the models command."""

    def test_models_list_default_output(self, runner, mock_models):
        """Test models command with default table output."""
        result = runner.invoke(cli, ["models"])
        assert result.exit_code == 0
        assert "Found 3 models" in result.output
        assert "gpt-4o" in result.output
        assert "claude-3-opus" in result.output
        assert "llama2" in result.output

    def test_models_list_json_output(self, runner, mock_models):
        """Test models command with JSON output."""
        result = runner.invoke(cli, ["models", "--json-output"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 3
        assert all("key" in item and "name" in item for item in data)

    def test_models_list_empty(self, runner, monkeypatch):
        """Test models command when no models are available."""
        monkeypatch.setattr("llm.get_models", lambda: [])
        result = runner.invoke(cli, ["models"])
        assert result.exit_code == 0
        assert "No models found" in result.output


class TestPromptCommand:
    """Test cases for the prompt command."""

    def test_prompt_success(self, runner, monkeypatch, mock_response, mock_model):
        """Test successful prompt execution."""
        monkeypatch.setattr(
            "llm.get_model",
            lambda key: (
                mock_model("Hello, world!") if key == "gpt-4o" else Exception("Model not found")
            ),
        )

        result = runner.invoke(cli, ["prompt", "gpt-4o", "Hello!"])
        assert result.exit_code == 0
        assert "Hello, world!" in result.output

    def test_prompt_with_system(self, runner, monkeypatch, mock_response, mock_model, caplog):
        """Test prompt with system message."""
        caplog.set_level(logging.INFO)
        system_received = []

        class TrackingModel(mock_model):
            def prompt(self, prompt, system=None, attachments=None):
                system_received.append(system)
                return mock_response("Response with system")

        monkeypatch.setattr("llm.get_model", lambda key: TrackingModel())

        result = runner.invoke(cli, ["prompt", "gpt-4o", "Hello!", "--system", "Be helpful"])
        assert result.exit_code == 0
        assert system_received == ["Be helpful"]

        prompt_logs = parse_prompt_logs(caplog)
        assert prompt_logs == [
            {
                "kind": "model",
                "model": "gpt-4o",
                "text": "Hello!",
                "system": "Be helpful",
            }
        ]

    def test_prompt_model_error(self, runner, monkeypatch):
        """Test prompt with invalid model."""
        import llm

        def mock_get_model(key):
            raise llm.errors.ModelError("Model not found: test-model")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        result = runner.invoke(cli, ["prompt", "invalid-model", "Hello!"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Model not found" in result.output


class TestCLI:
    """Test cases for general CLI functionality."""

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "privacyforms-ai" in result.output
        assert __version__ in result.output

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PrivacyForms AI" in result.output


class TestChatCommand:
    """Test cases for the chat command."""

    def test_chat_basic_conversation(self, runner, monkeypatch, mock_conversation):
        """Test basic chat session with a few exchanges."""

        class MultiTurnConversation(mock_conversation):
            def __init__(self):
                super().__init__(responses=["Hello!", "I can help with that.", "Goodbye!"])

        class MockModel:
            model_id = "gpt-4o"

            def conversation(self, system=None):
                return MultiTurnConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        # Simulate a conversation: user inputs "Hi", then "Help", then "/quit"
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="Hi\nHelp\n/quit\n")
        assert result.exit_code == 0
        assert "Starting chat with model: gpt-4o" in result.output
        assert "Hello!" in result.output
        assert "I can help with that." in result.output
        assert "Goodbye!" in result.output

    def test_chat_with_system_prompt(
        self, runner, monkeypatch, mock_response, mock_conversation, caplog
    ):
        """Test chat with a system prompt."""
        caplog.set_level(logging.INFO)
        system_set = []

        class SystemConversation(mock_conversation):
            def __init__(self):
                self._system = None
                self.responses = ["Understood!"]
                self.index = 0

            @property
            def system(self):
                return self._system

            @system.setter
            def system(self, value):
                self._system = value
                system_set.append(value)

            def prompt(self, prompt, attachments=None):
                response = self.responses[self.index % len(self.responses)]
                self.index += 1
                return mock_response(response)

        class MockModel:
            def conversation(self):
                return SystemConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(
            cli, ["chat", "gpt-4o", "--system", "Be helpful"], input="Hello\n/quit\n"
        )
        assert result.exit_code == 0
        assert "System prompt: Be helpful" in result.output
        assert system_set == ["Be helpful"]

        prompt_logs = parse_prompt_logs(caplog)
        assert prompt_logs == [
            {
                "kind": "conversation",
                "system": "Be helpful",
                "text": "Hello",
            }
        ]

    def test_chat_clear_command(self, runner, monkeypatch, mock_conversation):
        """Test the /clear command."""
        conversation_count = [0]

        class CountingConversation(mock_conversation):
            def __init__(self):
                super().__init__()
                conversation_count[0] += 1

        class MockModel:
            def conversation(self):
                return CountingConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(cli, ["chat", "gpt-4o"], input="Hello\n/clear\nHi\n/quit\n")
        assert result.exit_code == 0
        assert "Conversation history cleared." in result.output
        assert conversation_count[0] == 2  # Initial + after clear

    def test_chat_model_command(self, runner, monkeypatch, mock_conversation):
        """Test the /model command."""

        class MockModel:
            def conversation(self, system=None):
                return mock_conversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(cli, ["chat", "gpt-4o"], input="/model\n/quit\n")
        assert result.exit_code == 0
        assert "Current model: gpt-4o" in result.output

    def test_chat_quit_variants(self, runner, monkeypatch, mock_conversation):
        """Test various quit commands."""

        class MockModel:
            def conversation(self, system=None):
                return mock_conversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        for quit_cmd in ["/quit", "/exit", "/q"]:
            result = runner.invoke(cli, ["chat", "gpt-4o"], input=f"{quit_cmd}\n")
            assert result.exit_code == 0
            assert "Goodbye!" in result.output

    def test_chat_model_error(self, runner, monkeypatch):
        """Test chat with invalid model."""
        import llm

        def mock_get_model(key):
            raise llm.errors.ModelError("Model not found: invalid-model")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        result = runner.invoke(cli, ["chat", "invalid-model"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Model not found" in result.output

    def test_chat_empty_input(self, runner, monkeypatch, mock_conversation):
        """Test that empty input is ignored."""
        prompt_count = [0]

        class CountingConversation(mock_conversation):
            def prompt(self, prompt, attachments=None):
                prompt_count[0] += 1
                return super().prompt(prompt, attachments)

        class MockModel:
            def conversation(self, system=None):
                return CountingConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        # Empty line should be ignored, then /quit
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="\n\n/quit\n")
        assert result.exit_code == 0
        assert prompt_count[0] == 0  # No prompts sent for empty input
