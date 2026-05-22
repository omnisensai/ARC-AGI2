#!/usr/bin/env bash
# Preflight setup for vLLM + LoRA eval on RunPod.
# Idempotent: safe to re-run; skips already-completed steps.
#
# See docs/runbook_vllm_eval.md for the lessons baked in here.

set -e

# ----------------------------------------------------------------------
# PHASE 1: env — redirect caches OFF the overlay disk BEFORE any download
# ----------------------------------------------------------------------
mkdir -p /workspace/hf_cache/huggingface/hub
mkdir -p /workspace/tmp
mkdir -p /root/eval_runs
mkdir -p /root/.tmux_tmp && chmod 700 /root/.tmux_tmp

cat > /root/.env_eval <<'EOF'
export HF_HOME=/workspace/hf_cache/huggingface
export HUGGINGFACE_HUB_CACHE=/workspace/hf_cache/huggingface/hub
export TRANSFORMERS_CACHE=/workspace/hf_cache/huggingface/hub
export TMPDIR=/workspace/tmp
export TMUX_TMPDIR=/root/.tmux_tmp
export HF_HUB_DISABLE_XET=1
export PYTHONUNBUFFERED=1
EOF
grep -q 'source /root/.env_eval' ~/.bashrc || echo 'source /root/.env_eval' >> ~/.bashrc
source /root/.env_eval

echo "=== env ==="
env | grep -E '^(HF_|HUGGINGFACE|TRANSFORMERS|TMPDIR|TMUX|PYTHONUNBUFFERED)' | sort
echo "=== disks ==="
df -h / /workspace

# ----------------------------------------------------------------------
# PHASE 2: system packages
# ----------------------------------------------------------------------
apt-get update -y >/dev/null && apt-get install -y git tmux >/dev/null
echo "=== tools installed ==="

# ----------------------------------------------------------------------
# PHASE 3: Python deps
# ----------------------------------------------------------------------
pip install --upgrade pip >/dev/null
pip install -U vllm peft transformers huggingface_hub requests 2>&1 | tail -3
python -c "import vllm; print('vllm', vllm.__version__)"

# ----------------------------------------------------------------------
# PHASE 4: HF auth (interactive)
# ----------------------------------------------------------------------
if ! hf auth whoami >/dev/null 2>&1; then
  echo "=== HF login (paste token when prompted) ==="
  hf auth login
fi
python - <<'PY'
from huggingface_hub import HfApi
api = HfApi()
print("Token user:", api.whoami()["name"])
info = api.repo_info("Omnisensai/arc-lora-run1")
print("LoRA access OK:", info.modelId, "files:", len(info.siblings))
PY

# ----------------------------------------------------------------------
# PHASE 5: clone repo + pull upstream eval JSONs
# ----------------------------------------------------------------------
cd /workspace
[ -d ARC-AGI2 ] || git clone https://github.com/omnisensai/ARC-AGI2.git
cd ARC-AGI2
git fetch origin
git checkout claude/general-session-ZdPRL || git checkout -b claude/general-session-ZdPRL origin/claude/general-session-ZdPRL

mkdir -p /workspace/upstream && cd /workspace/upstream
[ -d ARC-AGI-2 ] || git clone --depth 1 --filter=blob:none --no-checkout https://github.com/arcprize/ARC-AGI-2.git
cd ARC-AGI-2
git sparse-checkout init --cone 2>/dev/null
git sparse-checkout set data/evaluation
git checkout
mkdir -p /workspace/ARC-AGI2/data/arc2_eval
cp -n data/evaluation/*.json /workspace/ARC-AGI2/data/arc2_eval/
COUNT=$(ls /workspace/ARC-AGI2/data/arc2_eval | wc -l)
echo "=== eval puzzles: $COUNT (expect 120) ==="
[ "$COUNT" = "120" ] || { echo "FAIL: wrong puzzle count"; exit 1; }

# ----------------------------------------------------------------------
# PHASE 6: chat template (from LoRA repo)
# ----------------------------------------------------------------------
python - <<'PY'
from huggingface_hub import hf_hub_download
import shutil
shutil.copy(hf_hub_download("Omnisensai/arc-lora-run1", "chat_template.jinja"),
            "/workspace/chat_template.jinja")
print("chat template ready")
PY

# ----------------------------------------------------------------------
# PHASE 7: symlink eval_runs to fast local disk
# ----------------------------------------------------------------------
cd /workspace/ARC-AGI2
rm -rf eval_runs
ln -s /root/eval_runs eval_runs
ls -la eval_runs

# ----------------------------------------------------------------------
# PHASE 8: GPU sanity + kill stale processes
# ----------------------------------------------------------------------
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv
pkill -9 -f 'vllm serve' 2>/dev/null || true
pkill -9 -f 'VLLM::EngineCore' 2>/dev/null || true
pkill -9 -f 'run_eval_lora' 2>/dev/null || true
pkill -9 -f 'eval_collect_failures' 2>/dev/null || true
sleep 2
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader

# ----------------------------------------------------------------------
# PHASE 9: create HF dataset repo for live backup
# ----------------------------------------------------------------------
python - <<'PY'
from huggingface_hub import HfApi, create_repo
api = HfApi()
try:
    info = api.repo_info("Omnisensai/arc-lora-eval-runs", repo_type="dataset")
    print("dataset exists:", info.id)
except Exception:
    create_repo("Omnisensai/arc-lora-eval-runs", repo_type="dataset", private=True)
    print("created Omnisensai/arc-lora-eval-runs (private)")
PY

echo ""
echo "=================================================="
echo "PREFLIGHT COMPLETE."
echo "=================================================="
df -h / /workspace
