#!/usr/bin/env bash
# Launch vLLM serving Qwen-2.5-7B-Instruct + Omnisensai/arc-lora-run1.
# Uses the proven config that survives the silent 90s warmup.

set -e
source /root/.env_eval 2>/dev/null || true

# Kill any stale vLLM
pkill -9 -f 'vllm serve' 2>/dev/null || true
pkill -9 -f 'VLLM::EngineCore' 2>/dev/null || true
sleep 2
rm -f /workspace/vllm.log

cd /workspace/ARC-AGI2
nohup vllm serve Qwen/Qwen2.5-7B-Instruct \
  --enable-lora \
  --lora-modules arc=Omnisensai/arc-lora-run1 \
  --max-lora-rank 32 \
  --max-loras 1 \
  --max-model-len 16384 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.85 \
  --chat-template /workspace/chat_template.jinja \
  --enforce-eager \
  --port 8000 > /workspace/vllm.log 2>&1 &
VLLM_PID=$!
echo "vllm pid=$VLLM_PID"
disown

# Readiness probe — vLLM has a SILENT 90s warmup after weights load.
# Poll /v1/models for up to 5 minutes.
echo "Waiting for vLLM (expect ~3 min for download + load + warmup)..."
for i in $(seq 1 60); do
  if curl -s --max-time 3 localhost:8000/v1/models 2>/dev/null | grep -q '"id":"arc"'; then
    echo "vLLM READY after $((i*5))s"
    curl -s localhost:8000/v1/models \
      | python -c "import sys,json; d=json.load(sys.stdin); print('models:', [m['id'] for m in d['data']])"
    exit 0
  fi
  if ! ps -p $VLLM_PID >/dev/null 2>&1; then
    echo "FAIL: vllm process died. Last 40 log lines:"
    tail -40 /workspace/vllm.log
    exit 1
  fi
  sleep 5
done

echo "FAIL: vllm did not become ready in 5 minutes. Last 60 log lines:"
tail -60 /workspace/vllm.log
exit 1
