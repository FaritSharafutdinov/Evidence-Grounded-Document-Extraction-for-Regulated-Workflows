"""The OpenAI/vLLM backend must keep the settings that DEC-004/TASK-010 require.

Guards two regressions:
  * the thinking channel reopening on the hub (missing `enable_thinking: false`),
  * non-deterministic sampling (missing temperature 0 / seed 0).
and the graceful retry when a server rejects the optional request fields.
"""
import urllib.error

import backends


def _capture(backend, responses):
    seen: list[dict] = []

    def fake_post(body, timeout=900.0):
        seen.append(dict(body))
        out = responses[len(seen) - 1]
        if isinstance(out, Exception):
            raise out
        return out

    backend._post = fake_post
    return seen


def _ok_response():
    return {
        "choices": [{"message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1},
    }


def test_openai_backend_disables_thinking_and_pins_sampling():
    backend = backends.OpenAiBackend("Qwen/Qwen3.5-2B", "http://localhost:8000")
    seen = _capture(backend, [_ok_response()])
    backend.generate([{"role": "user", "content": "hi"}])
    body = seen[0]
    assert body["temperature"] == 0
    assert body["seed"] == 0
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_openai_backend_retries_without_optional_fields_on_400():
    backend = backends.OpenAiBackend("Qwen/Qwen3.5-2B", "http://localhost:8000")
    seen = _capture(
        backend,
        [urllib.error.HTTPError("u", 400, "bad", {}, None), _ok_response()],
    )
    backend.generate([{"role": "user", "content": "hi"}], json_schema={"type": "object"})
    assert "response_format" in seen[0] and "chat_template_kwargs" in seen[0]
    assert "response_format" not in seen[1] and "chat_template_kwargs" not in seen[1]