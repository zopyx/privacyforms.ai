# PrivacyForms AI

A Python CLI tool for interacting with Large Language Models (LLMs) via Simon Willison's `llm` library. Supports multiple providers including OpenAI, Anthropic, Moonshot, and Ollama.

## Features

- 🔧 **Simple CLI** - Easy-to-use command-line interface
- 💬 **Interactive Chat** - Multi-turn conversations with context/memory
- 🚀 **Multiple Providers** - Works with OpenAI, Anthropic, Moonshot, Ollama, and more
- 🧪 **Well Tested** - Comprehensive test coverage
- ⚡ **Fast** - Built with modern Python tooling

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/zopyx/privacyforms.ai.git
cd privacyforms.ai

# Install with uv
uv sync

# Or install in development mode
uv sync --all-extras --dev
```

### Using pip

```bash
pip install privacyforms-ai
```

## Configuration

Set your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-key"

# Anthropic
export ANTHROPIC_API_KEY="your-key"

# Moonshot
export MOONSHOT_API_KEY="your-key"
```

For Ollama, make sure the Ollama server is running locally.

## Usage

### List Available Models

```bash
privacyforms-ai models

# JSON output
privacyforms-ai models --json
```

### Send a Single Prompt

```bash
# Basic prompt
privacyforms-ai prompt gpt-4o-mini "What is the capital of France?"

# With system prompt
privacyforms-ai prompt gpt-4o-mini "Explain recursion" --system "You are a computer science tutor"
```

### Interactive Chat

Start an interactive chat session with conversation history:

```bash
# Basic chat
privacyforms-ai chat moonshot/kimi-k2.5

# With system prompt
privacyforms-ai chat gpt-4o-mini -s "You are a helpful coding assistant"
```

**Chat Commands:**
- `/quit`, `/exit`, `/q` - End the chat session
- `/clear` - Clear conversation history
- `/model` - Show current model

Example session:
```
Starting chat with model: moonshot/kimi-k2.5
Type /quit, /exit, or /q to end the session. Type /clear to reset history.
--------------------------------------------------

You: Hello!

AI: Hello! How can I help you today?

You: What can you do?

AI: I can help with a variety of tasks including...

You: /quit

Goodbye!
```

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/zopyx/privacyforms.ai.git
cd privacyforms.ai
uv sync --all-extras --dev
source .venv/bin/activate
```

### Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=privacyforms_ai --cov-report=term

# Verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Lint
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Type check
uv run ty check --python-version 3.12 src/
```

### Build Package

```bash
uv run python -m build
```

## API Design

See [API_DESIGN.md](API_DESIGN.md) for the REST API and WebSocket design specification for multi-chat server functionality.

## Project Structure

```
privacyforms.ai/
├── src/privacyforms_ai/
│   ├── __init__.py
│   ├── ai.py              # AI class for LLM interactions
│   └── cli.py             # Click CLI commands
├── tests/
│   ├── conftest.py        # Pytest fixtures
│   ├── test_ai.py         # AI class tests
│   └── test_cli.py        # CLI tests
├── pyproject.toml         # Project configuration
├── uv.lock               # Locked dependencies
└── README.md
```

## CI/CD

GitHub Actions workflow runs on:
- Python 3.12, 3.13, 3.14, 3.14t (free-threaded)
- Ubuntu Linux

Jobs:
- **test** - Run pytest with coverage
- **lint** - ruff (formatting, linting) and ty (type checking)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all checks pass (`uv run ruff format --check . && uv run ruff check . && uv run ty check src/ && uv run pytest`)
5. Submit a pull request

## Acknowledgments

- Built on top of [Simon Willison's llm](https://github.com/simonw/llm) library
- Uses [Astral's uv](https://github.com/astral-sh/uv) for fast Python package management
