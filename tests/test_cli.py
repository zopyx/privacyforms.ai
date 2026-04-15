"""Tests for the CLI."""

import json

import pytest
from click.testing import CliRunner

from privacyforms_ai.cli import cli

PROMPT_LOG_PREFIX = "[privacyforms-ai] prompt "


def parse_prompt_logs(output: str) -> list[dict[str, object]]:
    """Parse prompt logs from the combined CLI output stream."""
    return [
        json.loads(line[len(PROMPT_LOG_PREFIX) :])
        for line in output.splitlines()
        if line.startswith(PROMPT_LOG_PREFIX)
    ]


@pytest.fixture
def runner():
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

    def test_prompt_success(self, runner, monkeypatch):
        """Test successful prompt execution."""

        class MockResponse:
            def text(self):
                return "Hello, world!"

        class MockModel:
            def prompt(self, prompt, system=None):
                return MockResponse()

        def mock_get_model(key):
            if key == "gpt-4o":
                return MockModel()
            raise Exception("Model not found")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        result = runner.invoke(cli, ["prompt", "gpt-4o", "Hello!"])
        assert result.exit_code == 0
        assert "Hello, world!" in result.output

    def test_prompt_with_system(self, runner, monkeypatch):
        """Test prompt with system message."""
        system_received = []

        class MockResponse:
            def text(self):
                return "Response with system"

        class MockModel:
            def prompt(self, prompt, system=None):
                system_received.append(system)
                return MockResponse()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(cli, ["prompt", "gpt-4o", "Hello!", "--system", "Be helpful"])
        assert result.exit_code == 0
        assert system_received == ["Be helpful"]

        prompt_logs = parse_prompt_logs(result.output)
        assert prompt_logs == [
            {
                "kind": "model",
                "text": "Hello!",
                "system": "Be helpful",
            }
        ]

    def test_prompt_model_error(self, runner, monkeypatch):
        """Test prompt with invalid model."""

        def mock_get_model(key):
            raise Exception("Model not found: test-model")

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
        assert "0.1.2" in result.output

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PrivacyForms AI" in result.output


class TestChatCommand:
    """Test cases for the chat command."""

    def test_chat_basic_conversation(self, runner, monkeypatch):
        """Test basic chat session with a few exchanges."""

        class MockResponse:
            def __init__(self, text):
                self._text = text

            def text(self):
                return self._text

        class MockConversation:
            def __init__(self, system=None):
                self.system = system
                self.responses = ["Hello!", "I can help with that.", "Goodbye!"]
                self.index = 0

            def prompt(self, prompt):
                response = self.responses[self.index % len(self.responses)]
                self.index += 1
                return MockResponse(response)

        class MockModel:
            model_id = "gpt-4o"

            def conversation(self, system=None):
                return MockConversation(system=system)

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        # Simulate a conversation: user inputs "Hi", then "Help", then "/quit"
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="Hi\nHelp\n/quit\n")
        assert result.exit_code == 0
        assert "Starting chat with model: gpt-4o" in result.output
        assert "Hello!" in result.output
        assert "I can help with that." in result.output
        assert "Goodbye!" in result.output

    def test_chat_with_system_prompt(self, runner, monkeypatch):
        """Test chat with a system prompt."""
        system_set = []

        class MockResponse:
            def text(self):
                return "Understood!"

        class MockConversation:
            def __init__(self):
                self._system = None

            @property
            def system(self):
                return self._system

            @system.setter
            def system(self, value):
                self._system = value
                system_set.append(value)

            def prompt(self, prompt):
                return MockResponse()

        class MockModel:
            def conversation(self):
                return MockConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(
            cli, ["chat", "gpt-4o", "--system", "Be helpful"], input="Hello\n/quit\n"
        )
        assert result.exit_code == 0
        assert "System prompt: Be helpful" in result.output
        assert system_set == ["Be helpful"]

        prompt_logs = parse_prompt_logs(result.output)
        assert prompt_logs == [
            {
                "kind": "conversation",
                "system": "Be helpful",
                "text": "Hello",
            }
        ]

    def test_chat_clear_command(self, runner, monkeypatch):
        """Test the /clear command."""
        conversation_count = [0]

        class MockResponse:
            def text(self):
                return "Response"

        class MockConversation:
            def __init__(self):
                self.system = None
                conversation_count[0] += 1

            def prompt(self, prompt):
                return MockResponse()

        class MockModel:
            def conversation(self):
                return MockConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(cli, ["chat", "gpt-4o"], input="Hello\n/clear\nHi\n/quit\n")
        assert result.exit_code == 0
        assert "Conversation history cleared." in result.output
        assert conversation_count[0] == 2  # Initial + after clear

    def test_chat_model_command(self, runner, monkeypatch):
        """Test the /model command."""

        class MockResponse:
            def text(self):
                return "Response"

        class MockConversation:
            def prompt(self, prompt):
                return MockResponse()

        class MockModel:
            def conversation(self, system=None):
                return MockConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        result = runner.invoke(cli, ["chat", "gpt-4o"], input="/model\n/quit\n")
        assert result.exit_code == 0
        assert "Current model: gpt-4o" in result.output

    def test_chat_quit_variants(self, runner, monkeypatch):
        """Test various quit commands."""

        class MockConversation:
            pass

        class MockModel:
            def conversation(self, system=None):
                return MockConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        for quit_cmd in ["/quit", "/exit", "/q"]:
            result = runner.invoke(cli, ["chat", "gpt-4o"], input=f"{quit_cmd}\n")
            assert result.exit_code == 0
            assert "Goodbye!" in result.output

    def test_chat_model_error(self, runner, monkeypatch):
        """Test chat with invalid model."""

        def mock_get_model(key):
            raise Exception("Model not found: invalid-model")

        monkeypatch.setattr("llm.get_model", mock_get_model)

        result = runner.invoke(cli, ["chat", "invalid-model"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Model not found" in result.output

    def test_chat_empty_input(self, runner, monkeypatch):
        """Test that empty input is ignored."""
        prompt_count = [0]

        class MockResponse:
            def text(self):
                return "Response"

        class MockConversation:
            def prompt(self, prompt):
                prompt_count[0] += 1
                return MockResponse()

        class MockModel:
            def conversation(self, system=None):
                return MockConversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())

        # Empty line should be ignored, then /quit
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="\n\n/quit\n")
        assert result.exit_code == 0
        assert prompt_count[0] == 0  # No prompts sent for empty input
