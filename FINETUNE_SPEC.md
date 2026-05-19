# Hand-off Spec: Fine-tune Qwen-2.5-7B-Instruct on ARC-AGI-2

## Background

I'm building a fine-tuned Qwen-2.5-7B-Instruct model to solve ARC-AGI-2 puzzles. ARC-AGI-2 is the Abstraction and Reasoning Corpus benchmark — each puzzle is a few input/output grid pairs that demonstrate a transformation rule; the model must figure out the rule and apply it to a held-out test input. Solutions are submitted as Python functions `def solve(input_grid) -> output_grid`.

**Repo**: https://github.com/omnisensai/ARC-AGI2 (public, all data + scripts there)

## Baseline

Pre-fine-tune Qwen-2.5-7B-Instruct (via OpenRouter, temp=0.7, 10 samples per puzzle):
- **0.3% pass@1** average (24 correct out of 7060 runs)
- **1.4% pass@10** (10 puzzles solved at least once out of 706 same-size puzzles)
- Baseline solved trivial puzzles only (shifts, recolors). Fails on anything requiring pattern recognition.

Goal: post-fine-tune target ≥ **25% pass@10** on same-size held-out, then test on the official 114-puzzle arc2_eval benchmark (held out from all training).

## Training data (built and committed)

Three JSONL files in `data_sft/`:

### phase1_train.jsonl — substrate tasks (180,728 records, gzipped on Github)
Teaches the model the grid format and basic spatial reasoning.
- Task tag `A` (encode): "Convert this pixel grid to substrate format"
- Task tag `B` (decode): inverse of A
- Task tag `H` (hierarchy): mark salient regions

Plus `phase1_dev.jsonl` (20,008 dev records). Built by `gen_phase1_data.py`. **Note: phase1_train.jsonl is committed as `.gz` — `gunzip` before loading.**

### phase2_train.jsonl — 730 records (puzzle → right_code)
The bread-and-butter SFT data. One record per (puzzle, correct_solution) pair.

Each record:
```json
{
  "prompt": "<full puzzle: all train pairs + test input>",
  "completion": "def solve(input_grid):\n    ...\n    return output"
}
```

Right codes come from:
- Claude agent corpus (705 puzzles, hand-validated via Python execution)
- 24 lucky Qwen baseline hits

### phase3_train.jsonl — 7261 records (puzzle + wrong + feedback → right)
The corrector-style data. Each record shows the model: here's a puzzle, here's a wrong attempt (and how wrong it was), here's the right answer. Teaches self-correction.

Each record:
```json
{
  "prompt": "<puzzle>\nPrevious attempt:\n<wrong_code>\nFailed: train 0 had cell_diff=9, train 1 had cell_diff=5, ...",
  "completion": "def solve(input_grid):\n    ...correct version...\n    return output"
}
```

Wrong codes from the baseline Qwen run — including the model's own mistakes, with concrete validation feedback (cell-by-cell diff counts or exec error messages).

### phase3_dpo.jsonl — 7261 pairs (chosen=right, rejected=wrong)
Same data formatted for Direct Preference Optimization, if you want to do RLHF-style training instead of (or in addition to) SFT.

## Held-out

`data/arc2_eval/` — 114 puzzles, **never** touched during training. Final benchmark.

`bulk_collect.py` only searches `data/arc1_train`, `data/arc1_eval`, `data/arc2_train` to guarantee no leakage.

## What I want from you

1. **Recommend a fine-tuning approach**: LoRA vs full SFT, what trainer (HF TRL / unsloth / axolotl?), what hardware (single 4090, A100, rented?).
2. **Training schedule**: Phase1 first → phase2 → phase3? Or all mixed? Epochs? LR?
3. **A concrete recipe**: pip install, config files, launch command. I can run on rented GPU.
4. **Eval loop**: After fine-tuning, how do I re-run `bulk_collect.py` to measure pass@10 on same-size train set vs arc2_eval?

## Useful files in repo

- `bulk_collect.py` — runs any OpenRouter model on a split, validates code by exec, buckets results. This is also our eval harness.
- `research/agent_corpus/by_puzzle/<pid>.json` — per-puzzle ground truth (right_codes + wrong_codes with failure_mode tags)
- `STATUS.md` / `STATUS.csv` — current corpus state
- `splits/all_samesize.json` — 706 puzzle IDs (the training set)
- `splits/baseline_qwen_run.json` — 10-puzzle smoke test set
- `research/qwen_baseline_solved.md` — pre-fine-tune metrics

## Key constraints

- All wrong_codes come paired with structured feedback (`failure_mode`: "exec_error" with message, or "wrong_training" with per-pair cell_diff). Feedback is short, factual, and exec-grounded — no synthetic critique.
- The model only needs to output a `def solve(input_grid):` function in a ```python ... ``` code fence. No chain-of-thought required (we don't have CoT data).
- We have 0 puzzles in arc2_eval touched. Want zero leakage in any test.
