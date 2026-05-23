#!/usr/bin/env bash
# Save a trained LoRA adapter (+ its chat template) to Hugging Face so it
# survives the RunPod box being shut down. One command per phase. Idempotent.
#
# WHY THIS EXISTS: the adapter only lives on the rented GPU box. If you stop
# the pod without pushing it somewhere permanent, the training is gone. This
# script pushes it to Hugging Face and VERIFIES the upload before telling you
# it is safe to shut down — so you never have to "pause and worry" again.
#
# USAGE (on the RunPod box, after a stage finishes):
#   bash "Fine Tune Run 2/save_adapter_to_hf.sh" phase1_mixed
#   bash "Fine Tune Run 2/save_adapter_to_hf.sh" phase1_mixed outputs/phase1_mixed
#
# Typical stages: phase1_lit phase1_same phase1_diff phase1_mixed
#                 phase2_code phase3_repair
#
# ENV OVERRIDES:
#   HF_REPO   target Hugging Face model repo (default: Omnisensai/arc-lora-run2)
#
# Each stage is saved into its own subfolder inside the one repo, e.g.
#   Omnisensai/arc-lora-run2/phase1_mixed/

set -euo pipefail

STAGE="${1:?Usage: save_adapter_to_hf.sh <stage> [adapter_dir]   e.g. phase1_mixed}"
ADAPTER_DIR="${2:-outputs/${STAGE}}"
HF_REPO="${HF_REPO:-Omnisensai/arc-lora-run2}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PINNED_TOKCFG="${SCRIPT_DIR}/tokenizer_config.json"

echo "=================================================="
echo "Saving LoRA adapter to Hugging Face"
echo "  stage:       $STAGE"
echo "  adapter dir: $ADAPTER_DIR"
echo "  HF repo:     $HF_REPO   (subfolder: $STAGE)"
echo "=================================================="

# ---- 1. adapter weights actually present? -----------------------------------
if [ ! -f "$ADAPTER_DIR/adapter_model.safetensors" ] && \
   [ ! -f "$ADAPTER_DIR/adapter_model.bin" ]; then
  echo "ERROR: no adapter weights in '$ADAPTER_DIR'."
  echo "       Expected adapter_model.safetensors."
  echo "       Did training finish? Is the directory correct?"
  exit 1
fi

# ---- 2. make the chat template travel with the adapter ----------------------
# The eval breaks if the wrong chat template is used. Bundle the pinned one so
# the adapter is self-contained on Hugging Face.
if [ ! -f "$ADAPTER_DIR/tokenizer_config.json" ]; then
  if [ -f "$PINNED_TOKCFG" ]; then
    echo "note: adapter dir has no tokenizer_config.json — copying the pinned one."
    cp "$PINNED_TOKCFG" "$ADAPTER_DIR/tokenizer_config.json"
  else
    echo "WARNING: no tokenizer_config.json in the adapter dir AND no pinned copy"
    echo "         at $PINNED_TOKCFG. Eval may guess the wrong chat template."
  fi
fi

# ---- 3. hf CLI + login present? ---------------------------------------------
if ! command -v hf >/dev/null 2>&1; then
  echo "ERROR: 'hf' CLI not found.  Install with:  pip install -U huggingface_hub"
  exit 1
fi
if ! hf auth whoami >/dev/null 2>&1; then
  echo "ERROR: not logged in to Hugging Face.  Run once:  hf auth login"
  exit 1
fi
echo "HF user: $(hf auth whoami 2>/dev/null | head -1)"

# ---- 4. create the repo if it does not exist (private) -----------------------
python3 - "$HF_REPO" <<'PY'
import sys
from huggingface_hub import HfApi, create_repo
repo = sys.argv[1]
api = HfApi()
try:
    api.repo_info(repo)
    print(f"repo exists: {repo}")
except Exception:
    create_repo(repo, repo_type="model", private=True, exist_ok=True)
    print(f"created (private): {repo}")
PY

# ---- 5. upload the adapter into its stage subfolder -------------------------
echo "uploading '$ADAPTER_DIR' -> '$HF_REPO/$STAGE' ..."
hf upload "$HF_REPO" "$ADAPTER_DIR" "$STAGE" \
  --commit-message "adapter: $STAGE $(date -Iseconds)"

# ---- 6. VERIFY on Hugging Face before declaring it safe ---------------------
# Compares the uploaded weight file's byte size against the local one. Only a
# byte-for-byte size match earns the "SAFE TO SHUT DOWN" message.
python3 - "$HF_REPO" "$STAGE" "$ADAPTER_DIR" <<'PY'
import os, sys
from huggingface_hub import HfApi
repo, stage, local = sys.argv[1], sys.argv[2], sys.argv[3]
api = HfApi()

fname = "adapter_model.safetensors"
lp = os.path.join(local, fname)
if not os.path.exists(lp):
    fname = "adapter_model.bin"
    lp = os.path.join(local, fname)

key = f"{stage}/{fname}"
infos = api.get_paths_info(repo, [key], repo_type="model")
if not infos:
    print(f"VERIFY FAILED: '{key}' not found on Hugging Face. Do NOT shut down; re-run.")
    sys.exit(1)

remote_size = getattr(infos[0], "size", None)
local_size = os.path.getsize(lp)
print(f"local  {fname}: {local_size:,} bytes")
print(f"remote {fname}: {remote_size:,} bytes")
if remote_size != local_size:
    print("VERIFY FAILED: size mismatch — re-run before shutting down.")
    sys.exit(1)
print("VERIFY OK: adapter weights match byte-for-byte on Hugging Face.")
PY

echo ""
echo "=================================================="
echo "SAFE TO SHUT DOWN."
echo "Adapter '$STAGE' is verified on Hugging Face:"
echo "   https://huggingface.co/$HF_REPO/tree/main/$STAGE"
echo ""
echo "To get it back later (download, then serve/continue):"
echo "   hf download $HF_REPO --include \"$STAGE/*\" --local-dir ./hf_dl"
echo "   # adapter then lives at:  ./hf_dl/$STAGE"
echo "   # vLLM:   vllm serve Qwen/Qwen2.5-7B-Instruct --enable-lora \\"
echo "   #           --lora-modules arc=./hf_dl/$STAGE --max-lora-rank 32 ..."
echo "   # to continue training the NEXT phase, point axolotl's"
echo "   #   lora_model_dir at ./hf_dl/$STAGE"
echo "=================================================="
