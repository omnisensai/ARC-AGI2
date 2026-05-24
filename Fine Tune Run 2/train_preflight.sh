#!/usr/bin/env bash
# One-command environment setup for training Phase 1 on a fresh RunPod box.
#
# Run from the repo root AFTER cloning:
#   bash "Fine Tune Run 2/train_preflight.sh"
#
# Idempotent and self-contained. Bundles every fix we discovered the hard way
# (see RUNBOOK §2.5 P0/P-INSTALL/P-AXVER) so there is NO debugging on a fresh
# pod — just run it. The only interactive step is `hf auth login` at the end
# (it tells you if you still need to).
#
# What it does, in order:
#   1. Redirect HF/tmp caches off the small overlay disk + telemetry opt-out
#   2. pip install axolotl (if missing)
#   3. Remove torchvision/torchaudio (orphaned when axolotl bumps torch -> crash)
#   4. Drop in axolotl's missing telemetry whitelist.yaml (packaging bug)
#   5. Install flash-attn (fast attention; avoids the eager-attention 25x slowdown)
#   6. Verify everything + check HF login + run the data verifier

set +e  # keep going on individual step hiccups; we verify at the end

echo "=================================================="
echo "Phase 1 train preflight"
echo "=================================================="

# ---- 1. caches off the overlay disk + env -----------------------------------
# Pick a writable base for caches/tmp. Default /workspace (the persistent
# volume), but if it's full or unwritable — we've hit glitched RunPod volumes
# that report 100% full while completely empty — fall back to /root on the
# container disk. Override explicitly with TRAIN_BASE=/some/path.
BASE="${TRAIN_BASE:-/workspace}"
if ! ( mkdir -p "$BASE" 2>/dev/null && touch "$BASE/.wtest" 2>/dev/null && rm -f "$BASE/.wtest" ); then
  echo "  (note: $BASE is full/unwritable — falling back to /root on the container disk)"
  BASE=/root
fi
cat > /root/.env_train <<EOF
export HF_HOME=$BASE/hf_cache/huggingface
export HUGGINGFACE_HUB_CACHE=$BASE/hf_cache/huggingface/hub
export TRANSFORMERS_CACHE=$BASE/hf_cache/huggingface/hub
export TMPDIR=$BASE/tmp
export HF_HUB_DISABLE_XET=1
export AXOLOTL_DO_NOT_TRACK=1
export DO_NOT_TRACK=1
export PYTHONUNBUFFERED=1
EOF
grep -q 'source /root/.env_train' ~/.bashrc || echo 'source /root/.env_train' >> ~/.bashrc
source /root/.env_train
mkdir -p "$BASE/hf_cache/huggingface/hub" "$BASE/tmp"
echo "[1/6] env + caches set (BASE=$BASE, HF_HOME=$HF_HOME)"

# ---- 2. axolotl -------------------------------------------------------------
if axolotl --help >/dev/null 2>&1; then
  echo "[2/6] axolotl already installed — skipping"
else
  echo "[2/6] installing axolotl (a few minutes)…"
  pip install --no-cache-dir axolotl 2>&1 | tail -3
fi

# ---- 3. remove torchvision/torchaudio (orphaned by torch bump) --------------
pip uninstall -y torchvision torchaudio >/dev/null 2>&1
echo "[3/6] removed torchvision/torchaudio (not needed; they crash on torch mismatch)"

# ---- 4. telemetry whitelist (axolotl packaging bug) -------------------------
AXO=$(python -c "import axolotl,os;print(os.path.dirname(axolotl.__file__))" 2>/dev/null)
if [ -n "$AXO" ] && [ ! -f "$AXO/telemetry/whitelist.yaml" ]; then
  curl -fsSL https://raw.githubusercontent.com/axolotl-ai-cloud/axolotl/v0.16.1/src/axolotl/telemetry/whitelist.yaml \
    -o "$AXO/telemetry/whitelist.yaml" 2>/dev/null || printf '{}\n' > "$AXO/telemetry/whitelist.yaml"
  echo "[4/6] telemetry whitelist.yaml installed"
else
  echo "[4/6] telemetry whitelist present (or axolotl not found)"
fi

# ---- 5. flash-attn ----------------------------------------------------------
if python -c "import flash_attn" >/dev/null 2>&1; then
  echo "[5/6] flash-attn already installed — skipping"
else
  echo "[5/6] installing flash-attn (compiles; several minutes)…"
  pip install flash-attn --no-build-isolation 2>&1 | tail -3
fi

# ---- 6. verify --------------------------------------------------------------
echo "=================================================="
echo "[6/6] checks:"
axolotl --help >/dev/null 2>&1 && echo "  axolotl       OK" || echo "  axolotl       FAIL"
python -c "import flash_attn,sys;print('  flash-attn    OK', flash_attn.__version__)" 2>/dev/null || echo "  flash-attn    MISSING (set flash_attention:false to run without it)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | sed 's/^/  gpu           /'
if hf auth whoami >/dev/null 2>&1; then
  echo "  hugging face  logged in"
else
  echo "  hugging face  NOT logged in -> run:  hf auth login"
fi
python3 "Fine Tune Run 2/verify_records.py" 2>&1 | tail -1 | sed 's/^/  data          /'
echo "=================================================="
echo "Preflight done. If HF says NOT logged in, run: hf auth login"
echo "Then launch training, e.g.:"
echo "  axolotl train \"Fine Tune Run 2/phase1_same_lit_axolotl.yaml\""
echo "=================================================="
