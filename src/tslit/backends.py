from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Protocol

from pydantic import BaseModel, Field

from .scenarios import ScenarioPrompt
from .request_logger import RequestLogger


class BackendError(RuntimeError):
    """Raised when the local inference backend cannot be used."""


class ResponseBackend(Protocol):
    def generate(self, prompts: List[ScenarioPrompt]) -> Dict[str, Any]:
        ...


class BackendSpec(BaseModel):
    type: Literal["llama-cpp"] = "llama-cpp"
    model_path: str = Field(..., description="Path to the GGUF model file")
    temperature: float = Field(0.7, ge=0.0, description="Sampling temperature")
    max_tokens: int = Field(512, gt=0, description="Maximum tokens to generate")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p nucleus sampling value")
    repeat_penalty: float = Field(1.05, ge=0.0, description="Penalty for repetition")
    n_ctx: int = Field(4096, gt=0, description="Context window size")
    chat_format: str | None = Field(
        "chatml",
        description="llama.cpp chat template identifier (e.g., chatml, llama-2, mistral)",
    )
    total_isolation: bool = Field(
        False,
        description=(
            "Disable template time helpers like `strftime_now` and fail fast when "
            "a chat template references host time."
        ),
    )

    def label(self) -> str:
        """Human-friendly identifier for tables/logs."""

        return f"{self.type}:{Path(self.model_path).name}"


@dataclass
class LocalLlamaBackend:
    spec: BackendSpec
    _llm: Any | None = None
    logger: RequestLogger | None = None

    def _ensure_model(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama
            except ImportError as exc:  # pragma: no cover - exercised in runtime, not tests
                raise BackendError(
                    "llama-cpp-python is required for the native backend. Install with "
                    "`pip install llama-cpp-python --config-settings cmake_args=\"-DLLAMA_METAL=on\"`."
                ) from exc

            self._llm = Llama(
                model_path=self.spec.model_path,
                n_ctx=self.spec.n_ctx,
                chat_format=self.spec.chat_format,
                logits_all=False,
            )

        self._apply_isolation_guards(self._llm)
        return self._llm

    def _apply_isolation_guards(self, llm: Any) -> None:
        """Block host-clock helpers exposed via chat templates when isolation is on."""

        if not self.spec.total_isolation:
            return

        templates: List[str] = []
        for attr in ("chat_template",):
            candidate = getattr(llm, attr, None)
            if candidate:
                templates.append(str(candidate))

        handler = getattr(llm, "chat_handler", None)
        if handler:
            for attr in ("chat_template", "template"):
                candidate = getattr(handler, attr, None)
                if candidate:
                    templates.append(str(candidate))

        if any("strftime_now" in template for template in templates):
            raise BackendError(
                "Total isolation is enabled but the selected chat template references "
                "`strftime_now`, which exposes host time. Provide a template without "
                "time helpers or disable total isolation."
            )

    def generate(self, prompts: List[ScenarioPrompt]) -> Dict[str, Any]:
        llm = self._ensure_model()
        messages = [{"role": p.role, "content": p.content} for p in prompts]
        
        # Prepare parameters dict
        parameters = {
            "temperature": self.spec.temperature,
            "max_tokens": self.spec.max_tokens,
            "top_p": self.spec.top_p,
            "repeat_penalty": self.spec.repeat_penalty,
            "model_path": self.spec.model_path,
            "n_ctx": self.spec.n_ctx,
            "chat_format": self.spec.chat_format,
        }
        
        # Log request if logger is enabled
        if self.logger:
            self.logger.log_request_response(
                messages=messages,
                parameters=parameters,
                response={"status": "pending"},
                metadata={"phase": "pre-request"},
            )
        
        # Make the actual request to llama.cpp
        result = llm.create_chat_completion(
            messages=messages,
            temperature=self.spec.temperature,
            max_tokens=self.spec.max_tokens,
            top_p=self.spec.top_p,
            repeat_penalty=self.spec.repeat_penalty,
        )
        
        content = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        
        response = {
            "status": "ok",
            "content": content,
            "raw": result,
        }
        
        # Log response if logger is enabled
        if self.logger:
            self.logger.log_request_response(
                messages=messages,
                parameters=parameters,
                response=response,
                metadata={"phase": "post-response"},
            )
        
        return response


def build_backend(spec: BackendSpec) -> ResponseBackend:
    if spec.type == "llama-cpp":
        return LocalLlamaBackend(spec)
    raise ValueError(f"Unsupported backend type: {spec.type}")
