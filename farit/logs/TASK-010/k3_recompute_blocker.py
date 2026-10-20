#!/usr/bin/env python3
"""K3 verification of TASK-010 (Qwen3.5-2B thinking blocker), independent recompute.

Checks:
  V1. Frozen-path behavior: call the frozen `score_page_mlx` (default chat template,
      enable_thinking not passed) for sds_01/product_name pages 1..9 (native) and
      compare to the K2 log band 0.9669..0.9831 (mean 0.974) — and to the earlier
      K3 log value 0.985043 for p1.
  V2. Greedy generation under the default template starts with thinking, not Yes/No.
  V3. apply_chat_template(..., enable_thinking=False) closes the thinking channel;
      greedy answers `Yes…` on the gold page.
  V4. Logits dtype is bfloat16 (TASK-009 fp16 ladder claims do not transfer).
Run from repo root: ~/ds_env/bin/python farit/logs/TASK-010/k3_recompute_blocker.py
"""
import json
import sys
import time

sys.path.insert(0, ".")
from farit.src.retrieval import llm_reranker as rr  # frozen module, read-only

MODEL = "mlx-community/Qwen3.5-2B-MLX-4bit"
DOC, FIELD = "sds_01.pdf", "product_name"

pages = {}
for line in open("farit/data/corpus/units_native.jsonl"):
    u = json.loads(line)
    if u["document"] == DOC and u["layer"] == "native":
        pages[u["page"]] = u["text"]
assert sorted(pages) == list(range(1, 10)), sorted(pages)

print(f"MODEL={MODEL}")
t0 = time.time()
model, tokenizer = rr.load_mlx_model(MODEL)
print(f"loaded in {time.time()-t0:.1f}s")

# V1: frozen score path for all 9 pages
prompts = {p: rr.build_prompt(DOC, FIELD, p, pages[p]) for p in sorted(pages)}
scores = {p: rr.score_page_mlx(model, tokenizer, prompts[p]) for p in sorted(pages)}
vals = [scores[p] for p in sorted(scores)]
print("\n[V1] frozen score_page_mlx, sds_01/product_name, native p1..p9")
for p in sorted(scores):
    print(f"  p{p}: {scores[p]:.6f}")
print(f"  min={min(vals):.4f} max={max(vals):.4f} mean={sum(vals)/len(vals):.4f}")

# V2: default-template greedy (40 tokens)
from mlx_lm import generate
import mlx.core as mx

messages = [{"role": "user", "content": prompts[1]}]
chat_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print("\n[V2] default template tail:", repr(chat_prompt[-40:]))
out = generate(model, tokenizer, prompt=chat_prompt, max_tokens=40, verbose=False)
print(f"[V2] greedy(default) 40 tokens: {out!r}")

# V3: enable_thinking=False template tail + greedy
chat_prompt_b = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
)
print("\n[V3] enable_thinking=False tail:", repr(chat_prompt_b[-40:]))
out_b = generate(model, tokenizer, prompt=chat_prompt_b, max_tokens=10, verbose=False)
print(f"[V3] greedy(no-thinking) 10 tokens: {out_b!r}")

# V4: logits dtype
tokens = tokenizer.encode(chat_prompt, add_special_tokens=False)
logits = model(mx.array(tokens)[None])
print(f"\n[V4] logits dtype: {logits.dtype}")
