#!/usr/bin/env bash
# =============================================================================
# One-shot bootstrap + heavy-run driver for the GPU hub (NVIDIA / vLLM).
#
# It does everything: clone/update the repo, build a venv, install deps, rebuild
# the retrieval corpus from the tracked PDFs + annotations, launch (or connect to)
# a vLLM OpenAI-compatible server, run a smoke test, then the requested jobs, and
# collect every artifact into $OUT_DIR for easy retrieval.
#
# Everything is idempotent: re-running picks up where it left off. Results are
# cached under farit/data/llm_cache/ (gitignored) keyed by (backend, model,
# prompt, ...), so a warm re-run is free and never mixes hub vs local scores.
#
# Quick start (hub has internet + a GPU, vLLM servable):
#
#     JOB=all bash farit/hub/run_on_hub.sh
#
# If a vLLM server is already running elsewhere, skip launching:
#
#     BASE_URL=http://127.0.0.1:8000 JOB=battery bash farit/hub/run_on_hub.sh
#
# See farit/hub/README.md for the full matrix and how to pull results back.
# =============================================================================
set -euo pipefail

# ----------------------------------------------------------------------------
# Configuration (override via environment)
# ----------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/FaritSharafutdinov/Evidence-Grounded-Document-Extraction-for-Regulated-Workflows.git}"
BRANCH="${BRANCH:-farit_dev}"
COMMIT="${COMMIT:-}"                      # optional: pin to an exact commit
REPO_DIR="${REPO_DIR:-}"                      # override; auto-detected below
# Innopolis IDH Online-IDE keeps ONLY persistent_volume/ after the session ends,
# so put everything there when it exists (20 GB budget); fall back to $HOME.
if [ -z "${WORKDIR:-}" ]; then
  for cand in "$PWD/persistent_volume" "$HOME/persistent_volume" /home/jovyan/persistent_volume "/content/persistent_volume"; do
    if [ -d "$cand" ]; then WORKDIR="$cand/sds-hub"; break; fi
  done
  WORKDIR="${WORKDIR:-$HOME/sds-hub}"
fi
# Model + tokenizer downloads must survive the session -> keep HF cache local too.
export HF_HOME="${HF_HOME:-$WORKDIR/hf}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
MODEL="${MODEL:-Qwen/Qwen3.5-2B}"         # HF id served by vLLM (bf16)
SERVED_NAME="${SERVED_NAME:-$MODEL}"      # name our client sends in "model"
PORT="${PORT:-8000}"
BASE_URL="${BASE_URL:-}"                  # set -> do NOT launch vLLM, use this
JOB="${JOB:-smoke}"                       # smoke | battery | judge | all
LAYER="${LAYER:-both}"                    # native | ocr | both
ALL_METHODS="M1,M2,M3,M4,M5,M6"
METHODS="${METHODS:-$ALL_METHODS}"        # subset to (re)run, e.g. METHODS=M6
PYTHON="${PYTHON:-python3}"
VENV="${VENV:-$WORKDIR/venv}"
LAUNCH_VLLM="${LAUNCH_VLLM:-auto}"        # auto | always | never
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"
PIP_EXTRA="${PIP_EXTRA:-}"
SKIP_TESTS="${SKIP_TESTS:-0}"

REPO_NAME="$(basename "$REPO_URL" .git)"
# If we are already inside the checkout (this script lives at farit/hub/), use it;
# otherwise clone into $WORKDIR. REPO_DIR overrides the detection entirely.
if [ -z "$REPO_DIR" ]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  if [ -d "$HERE/.git" ] && [ -f "$HERE/farit/hub/run_on_hub.sh" ]; then
    REPO_DIR="$HERE"
  else
    REPO_DIR="$WORKDIR/$REPO_NAME"
  fi
fi
LOG_DIR="$WORKDIR/logs"
OUT_DIR="$WORKDIR/out"
mkdir -p "$WORKDIR" "$LOG_DIR" "$OUT_DIR"

log() { printf '\n\033[1;34m[huh]\033[0m %s\n' "$*" >&2; }
die() { printf '\n\033[1;31m[hub:error]\033[0m %s\n' "$*" >&2; exit 1; }

# ----------------------------------------------------------------------------
# 1. Clone or update the repository
# ----------------------------------------------------------------------------
log "1/7 repo -> $REPO_DIR (branch $BRANCH @ ${COMMIT:-HEAD})"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" fetch origin "$BRANCH"
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH" || true
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi
if [ -n "$COMMIT" ]; then
  git -C "$REPO_DIR" checkout "$COMMIT"
fi
cd "$REPO_DIR"
log "    HEAD = $(git rev-parse --short HEAD) ($(git log -1 --pretty=%s))"

# ----------------------------------------------------------------------------
# 2. Python environment
# ----------------------------------------------------------------------------
log "2/7 venv -> $VENV"
if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel >/dev/null
# Base deps are pinned; pymupdf==1.28.2 MUST NOT change (gold bboxes depend on it).
pip install $PIP_EXTRA -r requirements.txt
pip install $PIP_EXTRA -r farit/requirements.txt
pip install $PIP_EXTRA pytest   # dev gate; not in the pinned runtime requirements

# ----------------------------------------------------------------------------
# 3. Regenerate the retrieval corpus (PDFs + annotations -> farit/data/corpus)
# ----------------------------------------------------------------------------
log "3/7 building corpus"
python farit/src/retrieval/build_corpus.py

if [ "$SKIP_TESTS" != "1" ]; then
  log "    regression tests (expect 68 passed)"
  if ! python -m pytest tests/ -q 2>&1 | tail -3; then
    if [ "${STRICT_TESTS:-0}" = "1" ]; then
      die "tests failed — env is not clean"
    fi
    log "    WARNING: regression tests did not pass; continuing (STRICT_TESTS=1 to abort)"
  fi
fi

# ----------------------------------------------------------------------------
# 4. Launch / connect to vLLM
# ----------------------------------------------------------------------------
if [ -z "$BASE_URL" ]; then
  BASE_URL="http://127.0.0.1:$PORT"
fi

server_up() {
  curl -sf "$BASE_URL/v1/models" >/dev/null 2>&1
}

if [ "$LAUNCH_VLLM" = "never" ] || { [ "$LAUNCH_VLLM" = "auto" ] && server_up; }; then
  log "4/7 using existing server at $BASE_URL"
else
  if ! command -v vllm >/dev/null 2>&1; then
    if [ "${INSTALL_VLLM:-0}" = "1" ]; then
      log "installing vllm (this can take a few minutes)"
      pip install vllm
    else
      die "vllm not found; run 'pip install vllm', set INSTALL_VLLM=1, or set BASE_URL"
    fi
  fi
  log "4/7 launching vLLM: $MODEL -> $BASE_URL (log: $LOG_DIR/vllm.log)"
  # --trust-remote-code + modest context: the model's native 262144 ctx would
  # otherwise demand the whole KV budget. Text-only use of a VL arch works.
  nohup vllm serve "$MODEL" \
    --served-model-name "$SERVED_NAME" \
    --trust-remote-code \
    --port "$PORT" \
    --max-model-len "${MAX_MODEL_LEN:-32768}" \
    --gpu-memory-utilization "${GPU_MEM_UTIL:-0.90}" \
    $VLLM_EXTRA_ARGS >"$LOG_DIR/vllm.log" 2>&1 &
  echo $! > "$LOG_DIR/vllm.pid"
  log "    waiting for $SERVED_NAME ..."
  for i in $(seq 1 120); do
    if server_up; then break; fi
    if ! kill -0 "$(cat "$LOG_DIR/vllm.pid")" 2>/dev/null; then
      tail -40 "$LOG_DIR/vllm.log" >&2
      die "vLLM died during startup"
    fi
    sleep 5
  done
  server_up || die "vLLM did not become ready in time"
fi

# ----------------------------------------------------------------------------
# 5. Smoke test — fail fast before the full run
# ----------------------------------------------------------------------------
run_battery() {  # $1 = methods, $2 = extra args
  # shellcheck disable=SC2086
  python farit/src/extraction/run_battery.py \
    --backend openai --model "$SERVED_NAME" --base-url "$BASE_URL" \
    --layer "$LAYER" --methods "$1" $2
}

evaluate_battery() {
  log "    scoring battery -> farit/results/s4_battery_goldv13.{json,md}"
  python farit/src/extraction/evaluate_battery.py --tag goldv13
}

log "5/7 smoke (1 doc, both layers, all methods)"
run_battery "$ALL_METHODS" "--docs sds_05.pdf --smoke"

# Sanity: the smoke must produce citations, not just fields. A wrong
# chat_template_kwargs (thinking channel) or a prompt/schema mismatch (the
# 2026-10-26 incident: M1 returned `evidence: null`) shows up here first.
python - "$REPO_DIR" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
files = sorted((root / "farit" / "data" / "predictions").glob("s4_M*_*_smoke.json"))
if not files:
    sys.exit("smoke produced no prediction files")
fields = cites = 0
per_method = {}
for p in files:
    method = p.name.split("_")[1]
    d = json.loads(p.read_text())
    m_fields = m_cites = 0
    for doc in d.get("documents", []):
        for f in (doc.get("fields") or {}).values():
            m_fields += 1
            if f.get("evidence") or f.get("premises"):
                m_cites += 1
    fields += m_fields
    cites += m_cites
    per_method[method] = per_method.get(method, 0) + m_cites
if fields == 0:
    sys.exit("smoke produced no fields — check chat_template_kwargs / model id")
# M1 and M2 must each cite; if they don't, the full run is pointless.
for required in ("M1", "M2"):
    if per_method.get(required, 0) == 0:
        sys.exit(
            f"smoke: {required} produced ZERO citations — prompt/schema mismatch "
            "(evidence:null). Do NOT run the full battery; fix methods.py templates first."
        )
print(f"    smoke ok: {fields} fields, {cites} with citations  ({per_method})")
PY

# ----------------------------------------------------------------------------
# 6. Jobs
# ----------------------------------------------------------------------------
case "$JOB" in
  smoke)   log "6/7 job=smoke (nothing more to run)" ;;
  battery)
    log "6/7 job=battery (methods=$METHODS, $LAYER)"
    run_battery "$METHODS" ""
    evaluate_battery ;;
  judge)
    log "6/7 job=judge (pointwise judge via vLLM logprobs)"
    python farit/src/retrieval/llm_reranker.py \
      --backend openai --model "$SERVED_NAME" --base-url "$BASE_URL" \
      --layer "$LAYER" --score-mode v2 --out-tag "hub_${SERVED_NAME//\//_}_v2" \
      || die "judge run failed (needs the --backend openai path; see README)" ;;
  all)
    log "6/7 job=all: battery(methods=$METHODS) + judge"
    run_battery "$METHODS" ""
    evaluate_battery
    python farit/src/retrieval/llm_reranker.py \
      --backend openai --model "$SERVED_NAME" --base-url "$BASE_URL" \
      --layer "$LAYER" --score-mode v2 --out-tag "hub_${SERVED_NAME//\//_}_v2" \
      || die "judge run failed (needs the --backend openai path; see README)" ;;
  *) die "unknown JOB=$JOB (smoke|battery|judge|all)" ;;
esac

# ----------------------------------------------------------------------------
# 7. Collect artifacts
# ----------------------------------------------------------------------------
log "7/7 collecting artifacts -> $OUT_DIR"
mkdir -p "$OUT_DIR"
# Verify the battery table we ship was computed from THIS run's predictions, not a
# stale copy (2026-10-26: out/ shipped an mlx table from the local run).
if [ -f farit/results/s4_battery_goldv13.json ]; then
  python - <<'PY'
import json, sys
d = json.load(open("farit/results/s4_battery_goldv13.json"))
backends = {v.get("backend") for v in d.get("cost", {}).values() if v}
want = "openai" if any(b == "openai" for b in backends) else "mlx"
llm = [k for k in d.get("methods", {}) if not k.startswith("M4")]
print(f"    battery table backends: {sorted(b for b in backends if b)}")
if want != "openai" and llm:
    print("    WARNING: battery table looks like a LOCAL mlx run, not the hub run — verify before sharing")
PY
fi
cp -f farit/results/s4_battery_goldv13.json "$OUT_DIR"/ 2>/dev/null || true
cp -f farit/results/s4_battery_goldv13.md   "$OUT_DIR"/ 2>/dev/null || true
# merge prediction JSONs + metas written by this run
tar -czf "$OUT_DIR/predictions-$(date +%Y%m%dT%H%M%S).tgz" \
  -C farit/data/predictions . 2>/dev/null || true
# judge cache/outputs
cp -f farit/results/llm_reranker_hub_*.json "$OUT_DIR"/ 2>/dev/null || true
cp -f farit/results/llm_reranker_hub_*.md   "$OUT_DIR"/ 2>/dev/null || true
git -C "$REPO_DIR" rev-parse HEAD > "$OUT_DIR/HEAD.txt"

log "done. Artifacts in $OUT_DIR — pull them back with:"
log "    scp -r <hub>:$OUT_DIR ./hub-out"