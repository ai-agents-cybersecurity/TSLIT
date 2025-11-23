from __future__ import annotations

import types
import sys

import pytest

from tslit.backends import BackendError, BackendSpec, LocalLlamaBackend
from tslit.scenarios import ScenarioPrompt


class _DummyLlama:
    def __init__(self, chat_template: str | None = None, **_: object):
        self.chat_template = chat_template

    def create_chat_completion(self, *args, **kwargs):
        return {"choices": [{"message": {"content": "ok"}}]}


def _patch_llama(monkeypatch: pytest.MonkeyPatch, llama_cls: type[_DummyLlama]) -> None:
    monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace(Llama=llama_cls))


def test_total_isolation_blocks_strftime_templates(monkeypatch: pytest.MonkeyPatch) -> None:
    class StrftimeLlama(_DummyLlama):
        def __init__(self, **kwargs):
            super().__init__("{{ strftime_now('%Y-%m-%d') }}", **kwargs)

    _patch_llama(monkeypatch, StrftimeLlama)
    backend = LocalLlamaBackend(BackendSpec(model_path="model.gguf", total_isolation=True))

    with pytest.raises(BackendError):
        backend.generate([ScenarioPrompt(content="hi")])


def test_total_isolation_allows_safe_templates(monkeypatch: pytest.MonkeyPatch) -> None:
    class SafeLlama(_DummyLlama):
        def __init__(self, **kwargs):
            super().__init__("{{ messages }}", **kwargs)

    _patch_llama(monkeypatch, SafeLlama)
    backend = LocalLlamaBackend(BackendSpec(model_path="model.gguf", total_isolation=True))

    result = backend.generate([ScenarioPrompt(content="hi")])

    assert result["content"] == "ok"
