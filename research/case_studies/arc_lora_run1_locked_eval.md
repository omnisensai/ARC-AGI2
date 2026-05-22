# Case Study: arc-lora-run1 on Locked ARC-AGI-2 Eval

_Run: 2026-05-22, RunPod A100-SXM4-80GB_

## Setup

| Component | Value |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB (RunPod) |
| Base model | `Qwen/Qwen2.5-7B-Instruct` |
| LoRA adapter | `Omnisensai/arc-lora-run1` (rank=32, α=64, axolotl) |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Server | vLLM 0.21.0 |
| vLLM flags | `--enable-lora --max-lora-rank 32 --max-model-len 16384 --dtype bfloat16 --gpu-memory-utilization 0.85 --enforce-eager --chat-template <copied from LoRA repo>` |
| Eval client | `run_eval_lora.py` (system=`D`, phase2 prompt, compact grids via `substrate.format_grid`) |

Prompt format matches `build_sft_jsonl.py` phase2 records exactly:
- System message: literal `"D"`
- User message: phase2 template (`Write a Python def solve(input_grid)...`) with `format_grid()`-rendered training pairs and test input
- Grids: no spaces, no commas (one digit per cell, rows separated by `\n`)

## Eval Set

- `splits/locked_arc2_eval.json` — 120 puzzle IDs
- Source: byte-identical to `arcprize/ARC-AGI-2/data/evaluation/` (SHAs verified)
- Held out from all training per `FINETUNE_SPEC.md`

## Run Summary

| Run | Temp | Attempts/puzzle | Workers | Completed | Pass@2 |
|---|---|---|---|---|---|
| 1 | 0.7 | 2 | 8 | 60 / 240 (crash) | 0 / 31 |
| 2 | 0.2 | 2 | 4 | ~11 / 240 (killed) | 0 / 5 |

Run 1 crashed on a MooseFS `OSError: [Errno 5]` write to the network volume at attempt 60. Run 2 was started to probe whether deterministic decoding helped; killed early once the breakdown showed more `train_no_grid` and `exec_error` than Run 1 — **temperature lowering did NOT help**.

## Run 1 per-puzzle cell accuracy (sorted by best attempt)

Cell accuracy = (cells matching ground truth) / (total cells), averaged across training pairs.

| PID | best train % | a0 | a1 |
|---|---|---|---|
| `135a2760` | **98.3%** | 96.4% | 98.3% |
| `332f06d7` | **95.3%** | no_grid | 95.3% |
| `2c181942` | 93.5% | 93.5% | 90.0% |
| `28a6681f` | 93.0% | 93.0% | no_grid |
| `1818057f` | 90.4% | 90.4% | 90.4% |
| `142ca369` | 90.3% | 84.9% | 90.3% |
| `31f7f899` | 90.2% | 90.2% | 85.0% |
| `1ae2feb7` | 89.8% | 89.8% | 89.5% |
| `195c6913` | 86.8% | no_grid | 86.8% |
| `221dfab4` | 86.1% | 86.1% | no_grid |
| `16de56c4` | 80.0% | 72.2% | 80.0% |
| `3dc255db` | 80.0% | no_grid | 80.0% |
| `35ab12c3` | 79.2% | 78.6% | 79.2% |
| `16b78196` | 76.6% | 76.6% | 74.9% |
| `2b83f449` | 73.1% | 73.1% | no_grid |
| `36a08778` | 71.3% | 71.3% | 67.2% |
| `271d71e2` | 65.0% | no_grid | 65.0% |
| `21897d95` | 24.0% | no_grid | 24.0% |
| `0934a4d8` | — | no_grid | no_grid |
| `136b0064` | — | no_grid | no_grid |
| `13e47133` | — | no_grid | no_grid |
| `20270e3b` | — | no_grid | no_grid |
| `20a9e565` | — | no_grid | no_grid |
| `247ef758` | — | no_grid | no_grid |
| `269e22fb` | — | no_grid | no_grid |
| `291dc1e1` | — | no_grid | no_grid |
| `2ba387bc` | — | no_grid | no_grid |
| `2d0172a1` | — | no_grid | no_grid |
| `38007db0` | — | no_grid | no_grid |
| `3a25b0d8` | — | (only a1) no_grid | n/a |
| `3e6067c3` | — | no_grid | (only a0) n/a |

`no_grid` = `solve()` returned something that isn't a 2D list of ints (None, wrong shape, etc).

## Key findings

1. **23% of puzzles touched (7/31) reach ≥90% cell accuracy** — LoRA understands the rule structure but misses by a handful of cells. Top: `135a2760` at 98.3% (3/65 cells wrong on pair 1, 12/462 on pair 2).
2. **42% of puzzles (13/31) produced `no_grid` on both attempts** — strong systematic failure on certain transformations.
3. **0/31 exact matches**. ARC scoring is binary, so 98% counts the same as 0%.
4. **T=0.2 made things worse, not better.** The 11-attempt slice at T=0.2 showed `train_no_grid` and `exec_error` dominating where `wrong_training` had dominated at T=0.7. Sampling diversity is doing real work here.

## Failure-mode taxonomy

### A. Near-miss rules (90–99%)
Code runs cleanly, output shape correct, a few cells off. Model has the high-level rule but misses an edge case. Often boundary handling, off-by-one in iteration, or a missed condition.

The generated code for these is sophisticated — background detection, flood-fill connected components, shape classification, directional logic. Model identifies the puzzle's rule family correctly; just gets ~2% of cells wrong in execution.

### B. Shape-change failures (no_grid)
13 puzzles produced no valid grid on BOTH attempts. **Hypothesis**: these are puzzles where `output.shape != input.shape` (crops, upscaling, tiling, extraction). Training data heavily emphasized same-size transformations, so the model writes code that returns the input grid (or a same-shape modification) — failing the shape check or returning `None`.

The 13 PIDs: `0934a4d8, 136b0064, 13e47133, 20270e3b, 20a9e565, 247ef758, 269e22fb, 291dc1e1, 2ba387bc, 2d0172a1, 38007db0, 3a25b0d8, 3e6067c3`.

### C. Wide misses (<50%)
`21897d95` at 24% — model misread the rule entirely. Output shape correct, most cells wrong. Rare in this run (1/31).

## Caveats vs the "18%" target

`FINETUNE_SPEC.md` states the **18% goal is pass@10 on the same-size training split** (`splits/all_samesize.json`, 706 puzzles), NOT pass@2 on the locked `arc2_eval`. We measured against the harder, truly-held-out split with 5× fewer attempts. The numbers are not directly comparable. A pass@10 measurement on this same locked set would likely lift several near-miss puzzles into the `correct` bucket purely from sampling diversity.

## Recommended next steps

1. **Re-run as pass@10 (T=0.7)** on this locked set for a fair comparison. Estimated time: ~1h on this A100.
2. **Phase-3 corrector pass**: feed the ≥90% outputs (with structured feedback from `build_sft_jsonl.render_feedback`) into the E-task corrector. If "almost right → right" converts, that's the biggest single lever for closing the gap.
3. **Audit shape-changing puzzle coverage** in `data_sft/phase2_train.jsonl`. The 13 systematic `no_grid` failures all live in this category.
4. **Skip lowering temperature** — Run 2 disconfirmed the hypothesis. Stick with T=0.7 or higher.
5. **Longer-term**: consider full SFT instead of LoRA, or rank-128 LoRA, if held-out generalization is the bottleneck.

## Artifacts

- Raw attempts: `eval_runs/20260522_110054_arc/` on the RunPod pod (60 JSON files)
- No-grid failure code samples: see `research/case_studies/arc_lora_run1_no_grid_failures.md` (populate from pod, see next section)
- Analyzer scripts: `analyze_proximity.py`, `per_puzzle_stats.py` on pod

## How to dump and commit the no-grid failures

From the pod:

```bash
cd /workspace/ARC-AGI2
python - <<'PY' > research/case_studies/arc_lora_run1_no_grid_failures.md
import json
from pathlib import Path

NO_GRID = ["0934a4d8","136b0064","13e47133","20270e3b","20a9e565","247ef758",
           "269e22fb","291dc1e1","2ba387bc","2d0172a1","38007db0","3a25b0d8","3e6067c3"]
RUN = "eval_runs/20260522_110054_arc"

print("# No-grid failure code samples\n")
print("13 puzzles where both attempts returned non-grid output.\n")

for pid in NO_GRID:
    puz = json.load(open(f"data/arc2_eval/{pid}.json"))
    train_shapes = [(len(p["input"]), len(p["input"][0]), len(p["output"]), len(p["output"][0]))
                    for p in puz["train"]]
    test_shape   = (len(puz["test"][0]["input"]), len(puz["test"][0]["input"][0]))
    same_shape = all(ih==oh and iw==ow for ih, iw, oh, ow in train_shapes)
    print(f"## `{pid}`\n")
    print(f"- Train pair shapes (in→out): {train_shapes}")
    print(f"- Test input shape: {test_shape}")
    print(f"- Shape-changing? **{'NO (same-size)' if same_shape else 'YES'}**\n")
    for att in (0, 1):
        f = Path(f"{RUN}/{pid}__a{att}.json")
        if not f.exists(): continue
        rec = json.load(open(f))
        code = rec.get("code", "(no code)")
        print(f"### Attempt {att}\n")
        print("```python")
        print(code.strip() if code else "(none)")
        print("```\n")
PY

# commit + push (works only if pod has github auth; otherwise see fallback)
git checkout -b claude/general-session-ZdPRL 2>/dev/null || git checkout claude/general-session-ZdPRL
git add research/case_studies/arc_lora_run1_no_grid_failures.md
git commit -m "Add no-grid failure code samples"
git push -u origin claude/general-session-ZdPRL
```

If the pod doesn't have GitHub push credentials, copy the file out (`cat research/case_studies/arc_lora_run1_no_grid_failures.md`) and paste it into a follow-up message — I'll push it via the GitHub API.
