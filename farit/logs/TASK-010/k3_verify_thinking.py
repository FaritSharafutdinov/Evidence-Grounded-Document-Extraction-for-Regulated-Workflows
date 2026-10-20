"""K3 independent verification of TASK-010 blocker claim (thinking-mode default).

Reproduces, with the frozen code path where applicable:
1. Default chat template tail (what score_page_mlx uses) -> opens <think>?
2. Greedy continuation under default template -> thinking text or Yes/No?
3. enable_thinking=False template tail + greedy continuation.
4. Frozen score_page_mlx score on sds_01/product_name page 1 (K2 reported 0.9831).
5. Logits dtype.

Run from repo root: ~/ds_env/bin/python farit/logs/TASK-010/k3_verify_thinking.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import mlx.core as mx  # noqa: E402
from mlx_lm import load  # noqa: E402

from farit.src.retrieval.llm_reranker import (  # noqa: E402
    build_prompt,
    score_page_mlx,
)

MODEL = "mlx-community/Qwen3.5-2B-MLX-4bit"


def greedy(model, tokenizer, prompt: str, n: int = 15) -> str:
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    for _ in range(n):
        logits = model(mx.array(ids)[None])
        nxt = int(mx.argmax(logits[0, -1, :]).item())
        ids.append(nxt)
        if nxt == tokenizer.eos_token_id:
            break
    return tokenizer.decode(ids[-n:])


def main() -> None:
    model, tokenizer = load(MODEL)

    prompt = build_prompt("sds_01.pdf", "product_name", 1, "REDUR AD 04\nSafety data sheet")

    messages = [{"role": "user", "content": prompt}]

    default_tpl = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    print("=== DEFAULT TEMPLATE TAIL ===")
    print(repr(default_tpl[-120:]))
    print("=== GREEDY (default template) ===")
    print(repr(greedy(model, tokenizer, default_tpl)))

    try:
        no_think_tpl = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        print("=== enable_thinking=False TAIL ===")
        print(repr(no_think_tpl[-120:]))
        print("=== GREEDY (enable_thinking=False) ===")
        print(repr(greedy(model, tokenizer, no_think_tpl)))
    except TypeError as e:
        print(f"enable_thinking kwarg rejected: {e}")

    ids = tokenizer.encode(default_tpl, add_special_tokens=False)
    logits = model(mx.array(ids)[None])
    print("=== LOGITS DTYPE ===")
    print(logits.dtype)

    score = score_page_mlx(model, tokenizer, prompt)
    print(f"=== FROZEN score_page_mlx sds_01/product_name p1: {score:.6f} (K2 reported 0.983085/0.9831) ===")


if __name__ == "__main__":
    main()
