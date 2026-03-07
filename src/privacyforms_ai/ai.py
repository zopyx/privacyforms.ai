"""AI module for managing LLM models."""

import llm


class AI:
    """AI class for interacting with LLM models via the llm library."""

    @staticmethod
    def get_models() -> list[dict[str, str]]:
        """Get a list of all registered LLM models.

        Returns:
            A list of dictionaries, each containing:
                - "key": The model identifier (e.g., "gpt-4o", "anthropic/claude-3-opus-latest")
                - "name": The human-readable model name (e.g., "OpenAI Chat: gpt-4o")
        """
        models = llm.get_models()
        result = []
        for model in models:
            # model_id is the key, repr gives a human-readable name
            name = str(model).strip("<>")  # Convert <OpenAI Chat: gpt-4o> to OpenAI Chat: gpt-4o
            result.append(
                {
                    "key": model.model_id,
                    "name": name,
                }
            )
        return result

    @staticmethod
    def get_model(key: str) -> llm.models.Model:
        """Get a specific model by its key.

        Args:
            key: The model identifier (e.g., "gpt-4o")

        Returns:
            The model instance.

        Raises:
            llm.errors.ModelError: If the model is not found.
        """
        return llm.get_model(key)

    @staticmethod
    def get_conversation(model_key: str, system: str | None = None) -> llm.models.Conversation:
        """Create a new conversation with a model.

        Args:
            model_key: The model identifier (e.g., "gpt-4o")
            system: Optional system prompt to set the conversation context

        Returns:
            A Conversation object for maintaining dialog state.

        Raises:
            llm.errors.ModelError: If the model is not found.
        """
        model = llm.get_model(model_key)
        conversation = model.conversation()
        if system:
            conversation.system = system  # type: ignore[attr-defined]
        return conversation
