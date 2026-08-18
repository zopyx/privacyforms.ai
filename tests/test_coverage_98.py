"""Extra tests to push coverage to 98% - hit all remaining branches."""

import hashlib
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock

import click
import llm
import pytest
from click.testing import CliRunner

from privacyforms_ai.ai import AI
from privacyforms_ai.cli import cli

# ── AI._get_provider branches ──────────────────────────────────────────────


class TestGetProvider:
    def test_openai_module(self):
        class Fake:
            pass

        Fake.__module__ = "llm.default_plugins.openai_models"
        assert AI._get_provider(Fake()) == "openai"

    def test_llm_prefix(self):
        class Fake:
            pass

        Fake.__module__ = "llm_anthropic"
        assert AI._get_provider(Fake()) == "anthropic"

        Fake.__module__ = "llm_moonshot"
        assert AI._get_provider(Fake()) == "moonshot"

    def test_dotted_module_stripping_models(self):
        class Fake:
            pass

        Fake.__module__ = "some.plugin.foo_models"
        assert AI._get_provider(Fake()) == "foo"

    def test_dotted_module_no_strip(self):
        class Fake:
            pass

        Fake.__module__ = "some.plugin.foobar"
        assert AI._get_provider(Fake()) == "foobar"

    def test_unknown_provider(self):
        class Fake:
            pass

        Fake.__module__ = ""
        assert AI._get_provider(Fake()) == "unknown"

    def test_no_module_attr(self):
        # This edge is already covered by test_unknown_provider (empty module => unknown)
        # Keep a trivial check to ensure the method handles missing module gracefully
        class Fake:
            pass

        Fake.__module__ = ""
        assert AI._get_provider(Fake()) == "unknown"


# ── AI.create_attachment branches ───────────────────────────────────────────


class TestCreateAttachment:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            AI.create_attachment("/nonexistent/path/file.pdf")

    def test_from_path_branch(self, tmp_path, monkeypatch):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.7")
        sentinel = object()
        fake_cls = MagicMock()
        fake_cls.from_path = MagicMock(return_value=sentinel)
        # patch llm.Attachment to have from_path
        monkeypatch.setattr(llm, "Attachment", fake_cls)
        result = AI.create_attachment(str(f))
        assert result is sentinel
        fake_cls.from_path.assert_called_once_with(str(f))

    def test_fallback_first_builder_succeeds(self, tmp_path, monkeypatch):
        f = tmp_path / "hello.txt"
        f.write_bytes(b"hello")

        # Ensure from_path not present, fallback used
        orig_att = llm.Attachment
        # create a fake class that has no from_path and whose __call__ works for first builder
        # The fallback uses llm.Attachment directly; we need to make it succeed on path=...
        # Default Attachment does that, so just ensure from_path absent -> fallback succeeds
        if hasattr(orig_att, "from_path"):
            monkeypatch.delattr(llm.Attachment, "from_path", raising=False)
        # Remove attribute if mocked elsewhere
        # Now create_attachment should use fallback and succeed via first builder
        att = AI.create_attachment(str(f))
        assert isinstance(att, llm.Attachment)
        assert att.path == str(f)

    def test_fallback_loop_with_type_errors(self, tmp_path, monkeypatch):
        f = tmp_path / "data.bin"
        f.write_bytes(b"abc")
        # custom Attachment that fails on first 2 builders then succeeds
        call_log = []

        class FailingAttachment:
            def __init__(self, *args, **kwargs):
                call_log.append((args, kwargs))
                # fail first two calls
                if len(call_log) <= 2:
                    raise TypeError("bad sig")
                self.path = kwargs.get("path")
                self.data = args

        monkeypatch.setattr(llm, "Attachment", FailingAttachment)
        # Ensure no from_path
        if hasattr(FailingAttachment, "from_path"):
            monkeypatch.delattr(FailingAttachment, "from_path", raising=False)
        result = AI.create_attachment(str(f))
        assert isinstance(result, FailingAttachment)
        # Should have tried 3 times (2 failures + success)
        assert len(call_log) == 3

    def test_fallback_all_fail_raises_value_error(self, tmp_path, monkeypatch):
        f = tmp_path / "data2.bin"
        f.write_bytes(b"xyz")

        class AlwaysFail:
            def __init__(self, *a, **kw):
                raise TypeError("nope")

        monkeypatch.setattr(llm, "Attachment", AlwaysFail)
        with pytest.raises(ValueError, match="Could not create attachment"):
            AI.create_attachment(str(f))

    def test_mime_type_auto_detect(self, tmp_path, monkeypatch):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF")
        # default attachment path builder doesn't check mime_type, but _detect_mime_type is called
        # Just verify file creation doesn't error when mime_type None
        if hasattr(llm.Attachment, "from_path"):
            monkeypatch.delattr(llm.Attachment, "from_path", raising=False)
        att = AI.create_attachment(str(f), mime_type=None)
        assert att.path == str(f)


# ── AI.send_conversation_prompt with attachments ────────────────────────────


class TestSendConversationPrompt:
    def test_send_conversation_prompt_with_attachments(self, caplog):
        caplog.set_level(logging.INFO)

        class MockConv:
            system = "sys"
            model = type("M", (), {"model_id": "gpt-4o"})()

            def prompt(self, prompt, attachments=None):
                return MagicMock(text="ok")

        AI.send_conversation_prompt(MockConv(), "hello", attachments=[b"data"])  # type: ignore[arg-type]
        # check payload contains attachments
        records = [r for r in caplog.records if r.message.startswith(AI._LOG_PREFIX)]
        assert records
        payload = json.loads(records[-1].message[len(AI._LOG_PREFIX) :])
        assert payload["kind"] == "conversation"
        assert payload["attachments"][0]["kind"] == "binary"

    def test_send_conversation_prompt_without_attachments(self):
        class MockConv:
            system = None
            model = None

            def prompt(self, prompt, attachments=None):
                assert attachments is None or attachments == []
                m = MagicMock()
                m.text = "hi"
                return m

        resp = AI.send_conversation_prompt(MockConv(), "hi")  # type: ignore[arg-type]
        assert resp.text == "hi"

    def test_extract_response_text_callable_and_attr(self):
        class R1:
            def text(self):
                return "callable"

        assert AI.extract_response_text(R1()) == "callable"

        class R2:
            text = "attr"

        assert AI.extract_response_text(R2()) == "attr"


# ── AI._summarize_prompt_input branches ────────────────────────────────────


class TestSummarizePromptInput:
    def test_bytes_branch(self):
        data = b"abc"
        s = AI._summarize_prompt_input(data)
        assert s["kind"] == "binary"
        assert s["size_bytes"] == 3

    def test_bytearray_branch(self):
        data = bytearray(b"abc")
        s = AI._summarize_prompt_input(data)
        assert s["kind"] == "binary"

    def test_memoryview_branch(self):
        data = memoryview(b"abc")
        s = AI._summarize_prompt_input(data)
        assert s["kind"] == "binary"

    def test_str_branch(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_bytes(b"hi")
        s = AI._summarize_prompt_input(str(f))
        assert s["kind"] == "attachment"
        assert s["name"] == "a.txt"

    def test_path_branch(self, tmp_path):
        f = tmp_path / "b.txt"
        f.write_bytes(b"hi")
        s = AI._summarize_prompt_input(f)
        assert s["kind"] == "attachment"
        assert s["name"] == "b.txt"

    def test_path_attr_branch(self, tmp_path):
        f = tmp_path / "c.pdf"
        f.write_bytes(b"%PDF")
        obj = MagicMock()
        obj.path = str(f)
        obj.type = "application/pdf"
        # obj has no url/content, so path branch triggers
        s = AI._summarize_prompt_input(obj)
        assert s["kind"] == "attachment"
        assert s["name"] == "c.pdf"

    def test_url_branch_with_content(self):
        content = b"hello url"
        obj = type(
            "O",
            (),
            {"url": "https://example.com/file.pdf", "type": "application/pdf", "content": content},
        )()
        s = AI._summarize_prompt_input(obj)
        assert s["url"] == "https://example.com/file.pdf"
        assert s["mime_type"] == "application/pdf"
        assert s["size_bytes"] == len(content)

    def test_url_branch_without_mime(self):
        obj = type("O", (), {"url": "https://example.com/x", "type": None, "content": None})()
        s = AI._summarize_prompt_input(obj)
        assert s["url"] == "https://example.com/x"
        assert "mime_type" not in s

    def test_url_branch_with_mime_no_content(self):
        obj = type(
            "O", (), {"url": "https://example.com/x", "type": "text/plain", "content": None}
        )()
        s = AI._summarize_prompt_input(obj)
        assert s["mime_type"] == "text/plain"

    def test_content_branch_with_mime(self):
        content = b"raw data"
        obj = type("O", (), {"url": None, "content": content, "type": "image/png"})()
        s = AI._summarize_prompt_input(obj)
        # _summarize_binary_payload overwrites kind to "binary" (see implementation)
        assert s["size_bytes"] == len(content)
        assert s["mime_type"] == "image/png"
        # kind is overwritten by binary payload - this is actual behaviour
        assert s["kind"] == "binary"

    def test_content_branch_without_mime(self):
        obj = type("O", (), {"url": None, "content": b"xyz", "type": None})()
        s = AI._summarize_prompt_input(obj)
        assert s["size_bytes"] == 3
        assert "mime_type" not in s
        assert s["kind"] == "binary"

    def test_fallback_type_name(self):
        obj = type("MyObj", (), {})()
        s = AI._summarize_prompt_input(obj)
        assert s == {"kind": "attachment", "type_name": "MyObj"}

    def test_content_zero_length(self):
        obj = type("O", (), {"url": None, "content": b"", "type": None})()
        # empty bytes is falsy? b"" is falsy? In code: if content is not None -> b"" passes
        s = AI._summarize_prompt_input(obj)
        assert s["size_bytes"] == 0


class TestSummarizeFileReference:
    def test_missing_file(self, tmp_path):
        p = tmp_path / "nonexistent.pdf"
        s = AI._summarize_file_reference(p)
        assert s["missing"] is True
        assert s["name"] == "nonexistent.pdf"

    def test_os_error_via_mock(self, tmp_path, monkeypatch):
        f = tmp_path / "exists.txt"
        f.write_bytes(b"hi")

        # monkeypatch Path.stat to raise OSError
        def fake_stat(self):
            raise OSError("disk gone")

        monkeypatch.setattr(Path, "stat", fake_stat)
        s = AI._summarize_file_reference(f)
        assert s["missing"] is True

    def test_existing_file(self, tmp_path):
        f = tmp_path / "ok.txt"
        f.write_bytes(b"hello")
        s = AI._summarize_file_reference(f)
        assert s["size_bytes"] == 5
        assert s["mime_type"] == "text/plain"

    def test_mime_type_param_overrides(self, tmp_path):
        f = tmp_path / "ok.unknown"
        f.write_bytes(b"hi")
        s = AI._summarize_file_reference(f, mime_type="custom/type")
        assert s["mime_type"] == "custom/type"


class TestSummarizeBinaryPayload:
    def test_binary_payload(self):
        data = b"abc"
        s = AI._summarize_binary_payload(data)
        assert s == {
            "kind": "binary",
            "size_bytes": 3,
            "sha256": hashlib.sha256(data).hexdigest()[:12],
        }


# ── CLI verbose branches ───────────────────────────────────────────────────


class TestCliVerbose:
    def test_verbose_info(self, runner, mock_models, monkeypatch):
        # invoke with -v should set INFO level
        result = runner.invoke(cli, ["-v", "models"])
        assert result.exit_code == 0

    def test_verbose_debug(self, runner, mock_models):
        result = runner.invoke(cli, ["-vv", "models"])
        assert result.exit_code == 0

    def test_no_verbose(self, runner, mock_models):
        result = runner.invoke(cli, ["models"])
        assert result.exit_code == 0


class TestCliPromptErrorBranches:
    def test_prompt_generic_exception(self, runner, monkeypatch):
        def raise_generic(key):
            raise RuntimeError("boom generic")

        monkeypatch.setattr("llm.get_model", raise_generic)
        result = runner.invoke(cli, ["prompt", "gpt-4o", "hi"])
        assert result.exit_code != 0
        assert "boom generic" in result.output

    def test_prompt_model_error_is_click_exception(self, runner, monkeypatch):
        def raise_model_error(key):
            raise llm.errors.ModelError("not found")

        monkeypatch.setattr("llm.get_model", raise_model_error)
        result = runner.invoke(cli, ["prompt", "any", "hi"])
        assert result.exit_code != 0


class TestCliChatErrorBranches:
    def test_chat_generic_exception_on_start(self, runner, monkeypatch):
        def raise_generic(key):
            raise RuntimeError("start boom")

        monkeypatch.setattr("llm.get_model", raise_generic)
        result = runner.invoke(cli, ["chat", "gpt-4o"])
        assert result.exit_code != 0
        assert "start boom" in result.output

    def test_chat_abort(self, runner, monkeypatch, mock_conversation):
        class MockModel:
            def conversation(self, system=None):
                return mock_conversation()

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())
        # monkeypatch click.prompt to raise Abort
        monkeypatch.setattr("click.prompt", lambda *a, **kw: (_ for _ in ()).throw(click.Abort()))
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="")
        assert result.exit_code == 0
        assert "Goodbye!" in result.output

    def test_chat_clear_model_error(self, runner, monkeypatch, mock_conversation):
        call_count = [0]

        class MockModel:
            def conversation(self, system=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_conversation(responses=["hi"])
                raise llm.errors.ModelError("clear failed model")

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="hello\n/clear\n/quit\n")
        assert result.exit_code == 0
        assert "clear failed model" in result.output or "Error" in result.output

    def test_chat_clear_generic_error(self, runner, monkeypatch, mock_conversation):
        call_count = [0]

        class MockModel:
            def conversation(self, system=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_conversation(responses=["hi"])
                raise RuntimeError("clear generic boom")

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="hello\n/clear\n/quit\n")
        assert result.exit_code == 0
        assert "clear generic boom" in result.output or "Error" in result.output

    def test_chat_send_model_error(self, runner, monkeypatch, mock_conversation):
        class BadConv(mock_conversation):
            def prompt(self, prompt, attachments=None):
                raise llm.errors.ModelError("send failed")

        class MockModel:
            def conversation(self, system=None):
                return BadConv(responses=["hi"])

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="hello\n/quit\n")
        assert result.exit_code == 0
        assert "send failed" in result.output

    def test_chat_send_generic_error(self, runner, monkeypatch, mock_conversation):
        class BadConv(mock_conversation):
            def prompt(self, prompt, attachments=None):
                raise RuntimeError("send generic boom")

        class MockModel:
            def conversation(self, system=None):
                return BadConv(responses=["hi"])

        monkeypatch.setattr("llm.get_model", lambda key: MockModel())
        result = runner.invoke(cli, ["chat", "gpt-4o"], input="hello\n/quit\n")
        assert result.exit_code == 0
        assert "send generic boom" in result.output


@pytest.fixture
def runner():
    return CliRunner()
