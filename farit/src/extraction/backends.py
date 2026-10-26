#!/usr/bin/env python3
"""Backends for the S4 extraction battery (TASK-015).

One interface, two engines:

    generate(messages, json_schema=None, max_tokens=...) -> (text, usage)

- ``mlx``    — local M2 model via ``mlx_lm``. Non-thinking chat template
               (``enable_thinking=False``, ``TypeError`` fallback, exactly as in
               ``farit/src/retrieval/llm_reranker.py`` v2 / DEC-004). JSON-schema
               output is not enforced by the engine; callers parse + repair.
- ``openai`` — the GPU hub through an OpenAI-compatible ``/v1/chat/completions``.
               ``response_format`` is attempted and silently dropped on HTTP 400.

``usage`` is ``(prompt_tokens, completion_tokens, latency_s)`` so S6 cost
accounting has what it needs. Every generation is cached by
``sha256(backend, model, messages, max_tokens, schema)`` under
``farit/data/llm_cache/s4/`` — a warm re-run is free and returns the cached
text and token counts (latency 0). The cache namespace is disjoint from the
frozen judge caches (``reranker_*__v2.jsonl``), so those are never touched.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = REPO_ROOT / "farit" / "data" / "llm_cache" / "s4"

DEFAULT_MAX_TOKENS = 3000


@dataclass
class Usage:
    """Token and latency accounting for one backend generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    cached: bool = False


@dataclass
class Generation:
    text: str
    usage: Usage


class Backend(Protocol):
    name: str
    model: str

    def generate(
        self,
        messages: list[dict],
        json_schema: dict | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Generation:  # pragma: no cover - protocol
        ...


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _messages_digest(messages: list[dict]) -> str:
    return hashlib.sha256(
        json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def cache_key(
    backend: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    json_schema: dict | None,
) -> str:
    """sha256 over (backend, model, messages, max_tokens, schema digest).

    Isolates model and backend, isolates the prompt, and additionally pins the
    requested output length and schema so two different calls can never share a
    slot.
    """
    digest = hashlib.sha256()
    for piece in (
        backend,
        model,
        _messages_digest(messages),
        str(max_tokens),
        hashlib.sha256(
            json.dumps(json_schema, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if json_schema is not None
        else "-",
    ):
        digest.update(piece.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _cache_path(key: str, cache_dir: Path) -> Path:
    return cache_dir / f"{key}.json"


def _read_cache(key: str, cache_dir: Path) -> dict | None:
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(key: str, payload: dict, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(_cache_path(key, cache_dir), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MLX backend
# ---------------------------------------------------------------------------


class MlxBackend:
    """Local Apple-Silicon inference through ``mlx_lm`` (load once, reuse)."""

    name = "mlx"

    def __init__(self, model: str) -> None:
        self.model = model
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_lm import load

            self._model, self._tokenizer = load(self.model)

    @staticmethod
    def _apply_template(tokenizer, messages: list[dict]) -> str:
        """Non-thinking template; TypeError fallback for models without the kwarg."""
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

    def generate(
        self,
        messages: list[dict],
        json_schema: dict | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Generation:
        from mlx_lm import generate as mlx_generate
        from mlx_lm.sample_utils import make_sampler

        self._ensure_loaded()
        prompt = self._apply_template(self._tokenizer, messages)
        prompt_tokens = len(self._tokenizer.encode(prompt, add_special_tokens=False))
        started = time.perf_counter()
        text = mlx_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=make_sampler(temp=0.0),
        )
        latency = time.perf_counter() - started
        completion_tokens = len(self._tokenizer.encode(text, add_special_tokens=False))
        return Generation(
            text=text,
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_s=latency,
            ),
        )


# ---------------------------------------------------------------------------
# OpenAI-compatible backend (GPU hub, Phase B)
# ---------------------------------------------------------------------------


class OpenAiBackend:
    """Hub inference through ``POST {base_url}/v1/chat/completions``."""

    name = "openai"

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = "sk-noauth",
        non_thinking: bool = True,
        seed: int = 0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.non_thinking = non_thinking
        self.seed = seed

    def _post(self, body: dict, timeout: float = 900.0) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate(
        self,
        messages: list[dict],
        json_schema: dict | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Generation:
        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0,
            "seed": self.seed,
        }
        if self.non_thinking:
            # vLLM forwards ``chat_template_kwargs`` to the HF chat template; this
            # closes Qwen3.5's thinking channel, matching the MLX path (DEC-004).
            # Without it the first generated token is a thinking token and any
            # score read off it is noise (TASK-010 blocker).
            body["chat_template_kwargs"] = {"enable_thinking": False}
        if json_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "output", "schema": json_schema},
            }
        started = time.perf_counter()
        try:
            payload = self._post(body)
        except urllib.error.HTTPError as error:
            if error.code not in (400, 404, 422):
                raise
            # Some servers reject response_format and/or chat_template_kwargs;
            # retry without the optional fields before giving up.
            if "response_format" in body or "chat_template_kwargs" in body:
                body.pop("response_format", None)
                body.pop("chat_template_kwargs", None)
                payload = self._post(body)
            else:
                raise
        latency = time.perf_counter() - started
        choice = (payload.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        usage = payload.get("usage") or {}
        return Generation(
            text=text,
            usage=Usage(
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                latency_s=latency,
            ),
        )


# ---------------------------------------------------------------------------
# Caching wrapper
# ---------------------------------------------------------------------------


class CachedBackend:
    """Wrap a backend with a reproducible sha256 cache.

    A cache hit returns the stored text and token counts with ``latency_s=0``
    and ``cached=True``; the prediction content (driven by the text) is
    therefore bit-identical across cold and warm runs.
    """

    def __init__(self, backend: Backend, cache_dir: Path = CACHE_DIR) -> None:
        self._backend = backend
        self.cache_dir = cache_dir
        self.name = backend.name
        self.model = backend.model

    def generate(
        self,
        messages: list[dict],
        json_schema: dict | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Generation:
        key = cache_key(self.name, self.model, messages, max_tokens, json_schema)
        cached = _read_cache(key, self.cache_dir)
        if cached is not None:
            return Generation(
                text=cached.get("text", ""),
                usage=Usage(
                    prompt_tokens=int(cached.get("prompt_tokens", 0)),
                    completion_tokens=int(cached.get("completion_tokens", 0)),
                    latency_s=0.0,
                    cached=True,
                ),
            )
        generation = self._backend.generate(messages, json_schema, max_tokens)
        _write_cache(
            key,
            {
                "backend": self.name,
                "model": self.model,
                "text": generation.text,
                "prompt_tokens": generation.usage.prompt_tokens,
                "completion_tokens": generation.usage.completion_tokens,
                "latency_s": generation.usage.latency_s,
            },
            self.cache_dir,
        )
        return generation


def make_backend(
    kind: str,
    model: str,
    base_url: str | None = None,
    cache_dir: Path = CACHE_DIR,
    use_cache: bool = True,
) -> CachedBackend | Backend:
    """Build the requested backend, wrapped in the cache unless disabled."""
    if kind == "mlx":
        backend: Backend = MlxBackend(model)
    elif kind == "openai":
        if not base_url:
            raise ValueError("--backend openai requires --base-url")
        backend = OpenAiBackend(model, base_url)
    else:
        raise ValueError(f"unknown backend {kind!r}")
    return CachedBackend(backend, cache_dir) if use_cache else backend