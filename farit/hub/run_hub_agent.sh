#!/usr/bin/env bash
# =============================================================================
# Put the OpenCode hub-runner agent on the IDH hub and launch it headless.
#
#   bash farit/hub/run_hub_agent.sh
#
# Requires a provider config so the agent has a model. Provide YOUR local
# opencode.jsonc either as a file (upload it to the hub) or inline:
#
#   OPENCODE_CONFIG_SRC=/path/to/opencode.jsonc bash farit/hub/run_hub_agent.sh
#   OPENCODE_CONFIG_JSON='{"$schema":"https://opencode.ai/config.json", ...}' \
#       bash farit/hub/run_hub_agent.sh
#
# If neither is given and a global config already exists, that is used as-is.
# The agent model defaults to alibaba-cloud/deepseek-v4.1-flash; override with
# HUB_AGENT_MODEL. Pick a provider the hub can actually reach (alibaba-cloud,
# mws-gpt, mercury, ...). Never commit the config: it carries API keys.
# =============================================================================
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
HUB_AGENT_MODEL="${HUB_AGENT_MODEL:-alibaba-cloud/deepseek-v4.1-flash}"
PROMPT_FILE="$REPO_DIR/farit/hub/HUB_RUNNER_PROMPT.md"

log() { printf '\n\033[1;34m[agent]\033[0m %s\n' "$*" >&2; }
die() { printf '\n\033[1;31m[agent:error]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. OpenCode CLI (V2 required) ------------------------------------------
export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
need_install=1
if command -v opencode >/dev/null 2>&1; then
  major="$(opencode --version 2>/dev/null | sed -n 's/.*v\{0,1\}\([0-9]\+\)\..*/\1/p' | head -1)"
  if [ -n "$major" ] && [ "$major" -ge 2 ] 2>/dev/null; then need_install=0; fi
fi
if [ "$need_install" = 1 ]; then
  log "installing/upgrading OpenCode CLI to V2 (hub had a V1 build)"
  command -v npm >/dev/null 2>&1 && npm install -g opencode-ai@latest || true
  # user-local installer, no sudo; newest release wins
  curl -fsSL https://opencode.ai/install | bash || die "opencode install failed"
  export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
  hash -r 2>/dev/null || true
fi
command -v opencode >/dev/null 2>&1 || die "opencode still not on PATH"
log "opencode: $(opencode --version 2>&1 | head -1)  [$(command -v opencode)]"

# --- 2. Provider config (keys live here; do not commit) ----------------------
mkdir -p "$CONF_DIR/agents"
if [ -n "${OPENCODE_CONFIG_SRC:-}" ]; then
  [ -f "$OPENCODE_CONFIG_SRC" ] || die "OPENCODE_CONFIG_SRC not found: $OPENCODE_CONFIG_SRC"
  cp "$OPENCODE_CONFIG_SRC" "$CONF_DIR/opencode.jsonc"
  log "config <- $OPENCODE_CONFIG_SRC"
elif [ -n "${OPENCODE_CONFIG_JSON:-}" ]; then
  printf '%s' "$OPENCODE_CONFIG_JSON" > "$CONF_DIR/opencode.jsonc"
  log "config <- OPENCODE_CONFIG_JSON (inline)"
elif [ -f "$CONF_DIR/opencode.jsonc" ] || [ -f "$CONF_DIR/opencode.json" ]; then
  log "config already present in $CONF_DIR"
else
  die "no provider config: set OPENCODE_CONFIG_SRC (upload your local opencode.jsonc) or OPENCODE_CONFIG_JSON"
fi

# --- 3. Install the hub-runner agent -----------------------------------------
cp "$REPO_DIR/.opencode/agents/hub-runner.md" "$CONF_DIR/agents/hub-runner.md"
log "agent installed -> $CONF_DIR/agents/hub-runner.md"

# --- 4. Launch headless ------------------------------------------------------
[ -f "$PROMPT_FILE" ] || die "missing mission file: $PROMPT_FILE"
log "launching hub-runner ($HUB_AGENT_MODEL) ..."
cd "$REPO_DIR"
opencode run \
  --agent hub-runner \
  --model "$HUB_AGENT_MODEL" \
  --auto \
  --title "hub-run $(date +%Y-%m-%dT%H:%M)" \
  "$(cat "$PROMPT_FILE")"