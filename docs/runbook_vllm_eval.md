# Runbook: vLLM + LoRA eval on RunPod

_Last updated: 2026-05-22. Tested on A100-SXM4-80GB, vLLM 0.21.0, Qwen-2.5-7B-Instruct + Omnisensai/arc-lora-run1 (rank=32)._

This is the **dry path** for re-running an ARC eval. The first time we did this it took ~3 hours of debugging; with this runbook it's ~10 minutes (5 min preflight + 3 min vLLM startup + eval).

## TL;DR — three commands

```bash
# 1. preflight (~5 min: deps + downloads + sanity)
bash <(curl -s https://raw.githubusercontent.com/omnisensai/ARC-AGI2/claude/general-session-ZdPRL/scripts/preflight.sh)

# 2. start vLLM serving (~3 min)
bash /workspace/ARC-AGI2/scripts/launch_vllm.sh

# 3. run the diagnostic eval
bash /workspace/ARC-AGI2/scripts/run_diagnostic_eval.sh
```

Or step through manually using the rest of this doc.

---

## Hard-won lessons (in order of how painful they were the first time)

### 1. HF cache MUST go to `/workspace`, set BEFORE any download

RunPod containers have a small overlay disk at `/` (typically 20 GB) and a large network volume at `/workspace`. The Qwen-7B weights are ~15 GB. By default HuggingFace caches everything under `~/.cache/huggingface` (= `/root/.cache/...` = overlay disk) and **fills it during the first download**.

Fix: set these env vars **before** running anything that downloads:

```bash
export HF_HOME=/workspace/hf_cache/huggingface
export HUGGINGFACE_HUB_CACHE=/workspace/hf_cache/huggingface/hub
export TRANSFORMERS_CACHE=/workspace/hf_cache/huggingface/hub
export TMPDIR=/workspace/tmp
export HF_HUB_DISABLE_XET=1   # see lesson #2
```

Persist them in `~/.bashrc` AND in a sourced file so subprocesses inherit them.

### 2. Disable HF's Xet cache (`HF_HUB_DISABLE_XET=1`)

Newer `huggingface_hub` uses Xet (a content-addressable chunk store) on top of the normal cache. The chunk store is a **second copy** of model weights — Qwen-7B downloaded once became 18 GB on disk (8 GB normal cache + 10 GB Xet chunks), tripping per-pod quotas.

Setting `HF_HUB_DISABLE_XET=1` keeps just the normal cache.

### 3. Eval outputs go to `/root`, NOT `/workspace`

`/workspace` is MooseFS (a network filesystem). It throws intermittent `OSError: [Errno 5] Input/output error` on writes, especially during high-frequency small-file writes. Our first eval crashed at attempt 60/240 from this.

`/root` is the local overlay disk — fast, reliable, no MooseFS. 240 eval JSONs is ~40 MB, fits easily.

Fix: symlink `eval_runs` to `/root`:
```bash
rm -rf /workspace/ARC-AGI2/eval_runs
ln -s /root/eval_runs /workspace/ARC-AGI2/eval_runs
```

Downside: when the pod is deleted, `/root` goes with it. Mitigation: HF dataset sync loop (lesson #4).

### 4. Auto-sync eval outputs to an HF dataset repo

Last time the pod was stopped and then couldn't restart → all eval data lost. Fix: a background loop that uploads `/root/eval_runs/` to a HuggingFace dataset every 60 seconds. Even if the pod dies, you lose ≤60 seconds of progress.

Setup is a one-time `create_repo("Omnisensai/arc-lora-eval-runs", repo_type="dataset", private=True)`. Sync loop:

```bash
nohup bash -c '
  source /root/.env_eval
  while true; do
    hf upload Omnisensai/arc-lora-eval-runs /root/eval_runs eval_runs \
      --repo-type dataset --commit-message "auto $(date -Iseconds)" 2>&1 | tail -2
    sleep 60
  done
' > /workspace/backup.log 2>&1 &
disown
```

### 5. vLLM has a SILENT 90-second warmup after weights load

The log line `Loading weights took 14 seconds` is followed by ~90 seconds of nothing while vLLM profiles KV cache memory. **This is not a hang.** Last time we kept Ctrl-C'ing during this phase, killing perfectly good launches.

Fix: a polling loop on `/v1/models` with up to a 5-minute timeout:

```bash
for i in $(seq 1 60); do
  if curl -s --max-time 3 localhost:8000/v1/models 2>/dev/null | grep -q '"id":"arc"'; then
    echo "vLLM READY after $((i*5))s"
    break
  fi
  sleep 5
done
```

Expected timing on A100:
- Banner + non-default args: 5 s
- Model download (first run, ~15 GB): 60–120 s
- Safetensors load: 15 s
- **Silent KV warmup: ~90 s** ← this is the bit we kept giving up on
- `Application startup complete`

Total first-launch: ~3–4 min. Subsequent (cached model): ~2 min.

### 6. vLLM flags that actually work

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --enable-lora \
  --lora-modules arc=Omnisensai/arc-lora-run1 \
  --max-lora-rank 32 \               # match the adapter's rank exactly
  --max-loras 1 \
  --max-model-len 16384 \            # NOT 8192 — long ARC puzzles need it
  --dtype bfloat16 \
  --gpu-memory-utilization 0.85 \    # 0.90 risks OOM on warmup, 0.85 safe
  --chat-template /workspace/chat_template.jinja \  # pulled from LoRA repo
  --enforce-eager \                  # skip CUDA graph compile (faster startup, no hang)
  --port 8000
```

- `--max-model-len 16384` — 8192 triggered context-limit errors on the largest puzzles (input + 4096 max_tokens output > 8192).
- `--enforce-eager` — skips torch.compile + CUDA graph capture, which silently hung us once. Tradeoff: ~10% slower inference. Worth it for stability.
- `--max-lora-rank 32` — must be ≥ adapter rank. For rank-32 LoRA, set 32. For unknown rank, look at `adapter_config.json["r"]` first.
- The chat template comes from the LoRA repo (`hf_hub_download(...,"chat_template.jinja")`); vLLM's auto-detected one may not match training.

### 7. `pkill -9 -f 'vllm serve'` MISSES the engine subprocess

vLLM spawns two processes: the API server (matches `vllm serve`) and the engine worker (named `VLLM::EngineCore`). Killing only the parent leaves the engine holding GPU memory. Always kill both:

```bash
pkill -9 -f 'vllm serve' 2>/dev/null
pkill -9 -f 'VLLM::EngineCore' 2>/dev/null
sleep 2
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader   # should be empty
```

### 8. `PYTHONUNBUFFERED=1` everywhere

Python's stdout is block-buffered when piped (eg. `> /workspace/eval.log`). Without `PYTHONUNBUFFERED=1` you stare at an empty log file thinking the eval is dead when it's actually mid-run.

### 9. Background a process properly: `nohup ... &` + `disown`

Just `&` is not enough — the process is still attached to the shell job table. Ctrl-C in the same terminal kills it. Even `nohup` alone isn't fully detached on RunPod terminals. Use both:

```bash
nohup python long_thing.py > /workspace/long.log 2>&1 &
disown
```

Then Ctrl-C in the parent shell only kills `tail -f`, not the actual process.

### 10. tmux on RunPod needs `TMUX_TMPDIR` on overlay fs

tmux defaults to `/tmp` for its socket, and `/tmp` may inherit weird permissions on RunPod. We hit `directory has unsafe permissions` on MooseFS. Fix:

```bash
mkdir -p /root/.tmux_tmp && chmod 700 /root/.tmux_tmp
export TMUX_TMPDIR=/root/.tmux_tmp
```

(Actually, we ended up not using tmux at all — `nohup + disown` was enough and survives terminal disconnects.)

### 11. HF tokens need the right scopes

For private LoRA repos, fine-grained tokens need:
- **Repositories** → "Only select repositories" → add `Omnisensai/arc-lora-run1`
- **Repository permissions** → **Contents: Read**

For writing the eval dataset:
- Add `Omnisensai/arc-lora-eval-runs` to the selected repos (create it first or via API)
- **Contents: Read and Write**

Classic tokens are simpler (just check `read` scope at minimum) but grant broader access.

Last time we hit a 404 because the token didn't have access to the private LoRA repo — looked like a missing-repo error but was an auth-scope error.

### 12. GitHub auth on the pod = Personal Access Token

Password auth doesn't work since 2021. For cloning a private repo:

1. https://github.com/settings/personal-access-tokens/new
2. Fine-grained, select `omnisensai/ARC-AGI2`, **Contents: Read** (Write if pushing)
3. Username: `omnisensai`, Password: paste the `github_pat_...` token
4. Optional: `git config --global credential.helper store` to avoid re-prompting

### 13. The CLI is now `hf`, not `huggingface-cli`

Newer `huggingface_hub` prints `Warning: huggingface-cli is deprecated. Use hf instead.`. Use `hf auth login`, `hf upload`, `hf download`. Old commands still work but emit a warning.

### 14. Jupyter Terminal > notebook cells for setup

Long bash blocks, heredocs, and interactive auth prompts work cleanly in a Jupyter Terminal (`File → New → Terminal`). Notebook cells with `%%bash` or `!...` mangle multi-line content and don't handle heredocs.

### 15. `data/arc2_eval/` isn't in this repo — fetch from upstream

The 120 locked puzzles come from `arcprize/ARC-AGI-2/data/evaluation/`. Sparse-checkout to avoid cloning the whole upstream repo:

```bash
git clone --depth 1 --filter=blob:none --no-checkout https://github.com/arcprize/ARC-AGI-2.git
cd ARC-AGI-2
git sparse-checkout init --cone
git sparse-checkout set data/evaluation
git checkout
```

Then copy the 120 JSONs into `data/arc2_eval/`. Byte-identical to the locked split (SHAs verified).

---

## Symptoms → causes cheat sheet

| Symptom | Likely cause |
|---|---|
| `OSError: [Errno 122] Disk quota exceeded` on download | HF cache landed on overlay disk OR xet duplicated weights — set `HF_HOME` + `HF_HUB_DISABLE_XET=1` BEFORE running |
| vLLM hangs after `Loading weights took N seconds` | Normal 90 s KV cache warmup — wait for it |
| `RuntimeError: Engine core initialization failed` (wrapper, no root cause) | Real error is higher in log — `grep Traceback /workspace/vllm.log \| head -30` |
| GPU still has 15 GB used after `pkill -9 -f 'vllm serve'` | EngineCore subprocess survived — `pkill -9 -f 'VLLM::EngineCore'` |
| `400 Client Error: max context length` during eval | Bump `--max-model-len` from 8192 to 16384 |
| Eval crashes mid-run with `OSError: [Errno 5] I/O error` | Writing to `/workspace` (MooseFS) — symlink `eval_runs → /root/eval_runs` |
| `python: can't open file '/workspace/analyze_X.py'` | Wrong cwd — `cd /workspace/ARC-AGI2` first; `substrate.py` import needs repo root on sys.path |
| `bash: command not found` for `Counter`, `deque` etc. | You pasted a Python file into bash, not a bash block |
| Jupyter terminal vanishes mid-run | Browser/WebSocket disconnect — background processes survive, open new terminal and re-attach to logs |
| `RepositoryNotFoundError: 404` on a private HF repo | Token doesn't have access to that specific repo — fix token scope |
| `tmux new -s X` exits immediately | tmux can't write its socket — `mkdir -p /root/.tmux_tmp && chmod 700 /root/.tmux_tmp && export TMUX_TMPDIR=/root/.tmux_tmp` |

---

## Files in this repo to use

- `scripts/preflight.sh` — runs lessons #1, 2, 3, 7, 11, 15 idempotently
- `scripts/launch_vllm.sh` — runs lesson #5, 6 with the readiness probe
- `scripts/run_diagnostic_eval.sh` — kicks off `eval_collect_failures.py` with the auto-backup loop
- `scripts/eval_collect_failures.py` — diagnostic eval per Phase-2 spec (failure traces, not score)
- `run_eval_lora.py` — older / simpler eval client (pass@k scoring)
- `scripts/analyze_proximity.py`, `scripts/per_puzzle_stats.py` — post-hoc analyzers
- `research/case_studies/arc_lora_run1_*.md` — written analysis of the first eval run
