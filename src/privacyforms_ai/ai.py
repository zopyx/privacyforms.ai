"""AI module for managing LLM models."""

from pathlib import Path
from typing import Any

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

    @staticmethod
    def create_attachment(file_path: str | Path, mime_type: str | None = None) -> Any:
        """Create an attachment for use with LLM prompts.

        Args:
            file_path: Path to the file to attach
            mime_type: Optional MIME type (auto-detected if not provided)

        Returns:
            An llm.Attachment object

        Raises:
            ImportError: If llm module is not available
            FileNotFoundError: If the file does not exist
            ValueError: If attachment creation fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect MIME type if not provided
        if mime_type is None:
            mime_type = AI._detect_mime_type(path)

        # Use llm.Attachment.from_path if available (newer versions)
        if hasattr(llm, "Attachment") and hasattr(llm.Attachment, "from_path"):
            return llm.Attachment.from_path(str(path))

        # Fallback: try various attachment constructors
        data = path.read_bytes()
        filename = path.name

        attachment_cls = llm.Attachment
        candidates = [
            lambda: attachment_cls(path=str(path)),
            lambda: attachment_cls(data, mime_type, filename),
            lambda: attachment_cls(filename, data, mime_type),
            lambda: attachment_cls(data, filename=filename, mimetype=mime_type),
            lambda: attachment_cls(filename=filename, content=data, type=mime_type),
        ]

        for builder in candidates:
            try:
                return builder()
            except TypeError:
                continue

        # Last resort: use inspect to match signature
        import inspect

        sig = inspect.signature(attachment_cls)
        kwargs = {}
        for name in sig.parameters:
            if name in ("data", "content", "body", "bytes"):
                kwargs[name] = data
            elif name in ("filename", "name", "file_name"):
                kwargs[name] = filename
            elif name in ("path", "file", "file_path"):
                kwargs[name] = str(path)
            elif name in ("mime_type", "mimetype", "content_type", "type"):
                kwargs[name] = mime_type

        if kwargs:
            return attachment_cls(**kwargs)

        raise ValueError("Could not create attachment with available constructors")

    @staticmethod
    def _detect_mime_type(path: Path) -> str:
        """Detect MIME type from file extension.

        Args:
            path: Path to the file

        Returns:
            MIME type string
        """
        extension_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".odt": "application/vnd.oasis.opendocument.text",
            ".html": "text/html",
            ".htm": "text/html",
            ".txt": "text/plain",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".json": "application/json",
            ".xml": "application/xml",
            ".csv": "text/csv",
            ".md": "text/markdown",
        }
        return extension_map.get(path.suffix.lower(), "application/octet-stream")

    @staticmethod
    def prompt_with_attachment(
        model: llm.models.Model,
        prompt: str,
        file_path: str | Path,
        mime_type: str | None = None,
    ) -> str:
        """Send a prompt with a file attachment to the model.

        Args:
            model: The LLM model instance
            prompt: The text prompt
            file_path: Path to the file to attach
            mime_type: Optional MIME type

        Returns:
            The model's response text

        Raises:
            ImportError: If llm module is not available
            FileNotFoundError: If the file does not exist
        """
        attachment = AI.create_attachment(file_path, mime_type)
        response = model.prompt(prompt, attachments=[attachment])
        return response.text() if callable(response.text) else response.text
