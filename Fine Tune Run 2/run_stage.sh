#!/usr/bin/env bash
# Launch a Phase 1 training stage DETACHED (nohup), so it survives a
# disconnect / laptop-close WITHOUT the fragile Ctrl-Z -> bg -> disown dance
# that has bitten us (suspending mid dataset-save wedged the run twice).
#
# Why this exists: every manual launch we've done has had a failure mode —
# wrong working directory ("/workspace" vs the repo root), Ctrl-Z deadlocks,
# or accidentally starting a second trainer on the same GPU. This script
# removes all three.
#
# Usage (from anywhere):
#   bash "Fine Tune Run 2/run_stage.sh" diff_lit
#
# Stages: same_lit diff_lit same_rule diff_rule mixed
#
# After it launches, watch with:
#   tail -f outputs/<stage>_run.log     # the loss staircase
#   nvidia-smi                          # GPU ~40GB used = training
# It is safe to close the laptop once nvidia-smi shows the model loaded.
set -euo pipefail

STAGE="${1:?Usage: run_stage.sh <stage>   e.g. diff_lit}"

# Always operate from the repo root, regardless of the caller's cwd — this is
# what fixes the "/workspace vs /workspace/ARC-AGI2" relative-path failures.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CFG="Fine Tune Run 2/phase1_${STAGE}_axolotl.yaml"
LOG="outputs/${STAGE}_run.log"

if [ ! -f "$CFG" ]; then
  echo "ERROR: no config at '$CFG' (stage typo? must be one of: same_lit diff_lit same_rule diff_rule mixed)" >&2
  exit 1
fi

# Refuse to double-launch: a second trainer on the same GPU = instant OOM, and
# it's the kind of mess we hit with leftover/zombie processes.
if pgrep -f "axolotl.cli.train" >/dev/null 2>&1; then
  echo "ERROR: an axolotl training process is already running." >&2
  echo "       Check it (nvidia-smi / tail -f $LOG). If it's dead/stuck:" >&2
  echo "         pkill -9 -f axolotl   (then re-run this)" >&2
  exit 1
fi

mkdir -p outputs
echo "=================================================="
echo "Launching stage '$STAGE' (detached)"
echo "  config: $CFG"
echo "  log:    $LOG"
echo "=================================================="
nohup axolotl train "$CFG" > "$LOG" 2>&1 &
PID=$!
sleep 1
echo "Launched. PID $PID — detached (survives disconnect; no Ctrl-Z needed)."
echo ""
echo "Monitor:"
echo "  tail -f $LOG     # watch the loss staircase (Ctrl-C stops viewing, not training)"
echo "  nvidia-smi       # a python proc using ~40GB = it reached the GPU and is training"
echo ""
echo "Give it ~1-2 min to prep data + load the model before the GPU lights up."
echo "Once nvidia-smi shows the model loaded, it is SAFE TO CLOSE THE LAPTOP."
