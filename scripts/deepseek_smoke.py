#!/usr/bin/env python3
"""Smoke test for a custom OpenAI-compatible endpoint (DeepSeek).

Reads the API key from ``deepseekv4.token`` in the repository root and
exercises the custom-endpoint API of the privacyforms_ai package:

1. Single prompt via ``AI.get_custom_model()`` + ``AI.send_prompt()``
2. Multi-turn conversation via ``AI.get_custom_conversation()``

Usage:
    uv run python scripts/deepseek_smoke.py

Requires network access and a valid DeepSeek API key. The key is read from
``deepseekv4.token`` in the repository root, or from the path given in the
``DEEPSEEK_TOKEN_FILE`` environment variable.
Exits 0 on success, 1 on failure.
"""

import os
import sys
from pathlib import Path

from privacyforms_ai import AI

API_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-v4-pro"
TOKEN_FILE = Path(
    os.environ.get(
        "DEEPSEEK_TOKEN_FILE",
        Path(__file__).resolve().parent.parent / "deepseekv4.token",
    )
)


def main() -> int:
    """Run the smoke test. Returns 0 on success, 1 on failure."""
    if not TOKEN_FILE.exists():
        print(f"ERROR: token file not found: {TOKEN_FILE}", file=sys.stderr)
        print("Create it with: echo 'sk-...' > deepseekv4.token", file=sys.stderr)
        return 1

    api_key = TOKEN_FILE.read_text().strip()
    if not api_key:
        print(f"ERROR: token file is empty: {TOKEN_FILE}", file=sys.stderr)
        return 1

    print(f"Endpoint : {API_URL}")
    print(f"Model    : {MODEL_NAME}")
    print("-" * 50)

    # 1. Single prompt
    print("\n[1/2] Single prompt ...")
    try:
        model = AI.get_custom_model(
            model_name=MODEL_NAME,
            api_url=API_URL,
            api_key=api_key,
        )
        response = AI.send_prompt(model, "Reply with exactly: OK")
        text = AI.extract_response_text(response)
        print(f"Response : {text}")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1

    # 2. Multi-turn conversation with system prompt
    print("\n[2/2] Conversation ...")
    try:
        conversation = AI.get_custom_conversation(
            model_name=MODEL_NAME,
            api_url=API_URL,
            api_key=api_key,
            system="You are a concise assistant. Answer in one short sentence.",
        )
        response = AI.send_conversation_prompt(conversation, "What is 2 + 2?")
        print(f"Turn 1   : {AI.extract_response_text(response)}")
        response = AI.send_conversation_prompt(conversation, "And multiplied by 10?")
        print(f"Turn 2   : {AI.extract_response_text(response)}")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1

    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
