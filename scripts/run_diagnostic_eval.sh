#!/usr/bin/env bash
# Run the diagnostic failure-trace eval on the locked 120-puzzle set.
# Outputs land in /root/eval_runs/<ts>_failure_probe/ (eval_runs symlinks to /root).
# An HF auto-backup loop mirrors the outputs to Omnisensai/arc-lora-eval-runs every 60s.

set -e
source /root/.env_eval

LIMIT="${1:-120}"        # default full set
ATTEMPTS="${2:-2}"
TEMP="${3:-0.7}"
WORKERS="${4:-4}"

TS=$(date +%Y%m%d_%H%M%S)
OUT=eval_runs/${TS}_failure_probe

# Sanity: vLLM up?
if ! curl -s --max-time 3 localhost:8000/v1/models 2>/dev/null | grep -q '"id":"arc"'; then
  echo "vLLM not serving 'arc'. Run scripts/launch_vllm.sh first."
  exit 1
fi

# Kill any old eval/backup loops
pkill -9 -f 'eval_collect_failures' 2>/dev/null || true
pkill -9 -f 'arc-lora-eval-runs' 2>/dev/null || true
sleep 1

# Start HF auto-backup loop in background (mirrors /root/eval_runs every 60s)
nohup bash -c '
  source /root/.env_eval
  while true; do
    hf upload Omnisensai/arc-lora-eval-runs /root/eval_runs eval_runs \
      --repo-type dataset --commit-message "auto $(date -Iseconds)" 2>&1 | tail -2
    sleep 60
  done
' > /workspace/backup.log 2>&1 &
echo "backup pid=$!"
disown

# Run the eval
cd /workspace/ARC-AGI2
nohup python scripts/eval_collect_failures.py \
  --model arc \
  --limit $LIMIT --attempts $ATTEMPTS --temperature $TEMP --workers $WORKERS \
  --out $OUT > /workspace/probe.log 2>&1 &
EVAL_PID=$!
echo "eval pid=$EVAL_PID, out=/workspace/ARC-AGI2/$OUT"
disown
sleep 3
echo ""
echo "=== eval starting (live log: tail -f /workspace/probe.log) ==="
tail -20 /workspace/probe.log
echo ""
echo "Monitor with:"
echo "  tail -f /workspace/probe.log"
echo "  ls $OUT/attempts | wc -l    # progress out of $(($LIMIT * $ATTEMPTS))"
echo "  tail /workspace/backup.log  # backup health"
