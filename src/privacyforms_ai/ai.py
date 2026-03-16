"""AI module for managing LLM models."""

import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import llm


class AI:
    """AI class for interacting with LLM models via the llm library."""

    _LOG_PREFIX = "[privacyforms-ai] prompt "

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
        attachment_factory = cast(Any, attachment_cls)
        candidates = [
            lambda: attachment_factory(path=str(path)),
            lambda: attachment_factory(data, mime_type, filename),
            lambda: attachment_factory(filename, data, mime_type),
            lambda: attachment_factory(data, filename=filename, mimetype=mime_type),
            lambda: attachment_factory(filename=filename, content=data, type=mime_type),
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
    def send_prompt(
        model: llm.models.Model,
        prompt: str,
        system: str | None = None,
        attachments: Sequence[Any] | None = None,
    ) -> Any:
        """Send a prompt to a model after logging it to the console."""
        AI._log_prompt(
            kind="model",
            prompt=prompt,
            system=system,
            attachments=attachments,
            model_key=getattr(model, "model_id", None),
        )
        prompt_kwargs: dict[str, Any] = {}
        if system is not None:
            prompt_kwargs["system"] = system
        if attachments:
            prompt_kwargs["attachments"] = list(attachments)
        return model.prompt(prompt, **prompt_kwargs)

    @staticmethod
    def send_conversation_prompt(
        conversation: llm.models.Conversation,
        prompt: str,
        attachments: Sequence[Any] | None = None,
    ) -> Any:
        """Send a prompt to a conversation after logging it to the console."""
        AI._log_prompt(
            kind="conversation",
            prompt=prompt,
            system=getattr(conversation, "system", None),
            attachments=attachments,
            model_key=getattr(getattr(conversation, "model", None), "model_id", None),
        )
        prompt_kwargs: dict[str, Any] = {}
        if attachments:
            prompt_kwargs["attachments"] = list(attachments)
        return conversation.prompt(prompt, **prompt_kwargs)

    @staticmethod
    def extract_response_text(response: Any) -> str:
        """Extract text from llm responses that expose text as attr or method."""
        return response.text() if callable(response.text) else response.text

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
    def _log_prompt(
        kind: str,
        prompt: str,
        system: str | None = None,
        attachments: Sequence[Any] | None = None,
        model_key: str | None = None,
    ) -> None:
        """Log the outbound prompt payload to stderr."""
        payload: dict[str, Any] = {"kind": kind, "text": prompt}
        if model_key:
            payload["model"] = model_key
        if system is not None:
            payload["system"] = system
        if attachments:
            payload["attachments"] = [AI._summarize_prompt_input(item) for item in attachments]
        print(
            f"{AI._LOG_PREFIX}{json.dumps(payload, sort_keys=True)}",
            file=sys.stderr,
            flush=True,
        )

    @staticmethod
    def _summarize_prompt_input(item: Any) -> dict[str, Any]:
        """Summarize attachments or binary prompt payloads for console logging."""
        if isinstance(item, bytes | bytearray | memoryview):
            return AI._summarize_binary_payload(bytes(item))

        if isinstance(item, str | Path):
            return AI._summarize_file_reference(Path(item))

        path = getattr(item, "path", None)
        if path:
            return AI._summarize_file_reference(Path(path), mime_type=getattr(item, "type", None))

        url = getattr(item, "url", None)
        content = getattr(item, "content", None)
        mime_type = getattr(item, "type", None)

        if url:
            summary: dict[str, Any] = {"kind": "attachment", "url": url}
            if mime_type:
                summary["mime_type"] = mime_type
            if content is not None:
                summary.update(AI._summarize_binary_payload(content))
            return summary

        if content is not None:
            summary = {"kind": "attachment"}
            if mime_type:
                summary["mime_type"] = mime_type
            summary.update(AI._summarize_binary_payload(content))
            return summary

        return {
            "kind": "attachment",
            "type_name": type(item).__name__,
        }

    @staticmethod
    def _summarize_file_reference(
        path: Path,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        """Summarize a file attachment without dumping its content."""
        summary: dict[str, Any] = {
            "kind": "attachment",
            "name": path.name,
        }
        if mime_type is None:
            mime_type = AI._detect_mime_type(path)
        summary["mime_type"] = mime_type
        try:
            summary["size_bytes"] = path.stat().st_size
        except OSError:
            summary["missing"] = True
        return summary

    @staticmethod
    def _summarize_binary_payload(data: bytes) -> dict[str, Any]:
        """Summarize binary data without writing raw content to the console."""
        return {
            "kind": "binary",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()[:12],
        }

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
        response = AI.send_prompt(model, prompt, attachments=[attachment])
        return AI.extract_response_text(response)
