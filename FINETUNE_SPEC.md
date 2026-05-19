# Hand-off Spec: Fine-tune Qwen-2.5-7B-Instruct on ARC-AGI-2

## Background

I'm building a fine-tuned Qwen-2.5-7B-Instruct model to solve ARC-AGI-2 puzzles. ARC-AGI-2 is the Abstraction and Reasoning Corpus benchmark — each puzzle is a few input/output grid pairs that demonstrate a transformation rule; the model must figure out the rule and apply it to a held-out test input. Solutions are submitted as Python functions `def solve(input_grid) -> output_grid`.

**Repo**: https://github.com/omnisensai/ARC-AGI2 (public, all data + scripts there)

## Baseline (pre-fine-tune)

Qwen-2.5-7B-Instruct via OpenRouter, temp=0.7, 10 samples per puzzle:
- **0.3% pass@1** (24 correct out of 7060 runs)
- **1.4% pass@10** (10 puzzles solved at least once out of 706 same-size puzzles)
- Baseline solved only trivial puzzles (shifts, recolors). Fails on anything requiring pattern recognition.

Note: baseline was measured with space-separated grids in the prompt. Training now uses compact format (no spaces between cells). A fresh baseline on compact prompts is optional — we mainly care about absolute post-fine-tune pass@10, not delta from old baseline.

**Goal**: post-fine-tune target ≥ **25% pass@10** on same-size training set, then final benchmark on `data/arc2_eval/` (114 puzzles, held out from all training).

## Training data — full inventory (committed in `data_sft/`)

7 SFT tasks tagged by single-letter system messages, plus DPO pairs. Total **226,909 training records**.

| Tag | Task | Records | Purpose |
|-----|------|---------|---------|
| **A** | `phase1a` — pair → substrate | 40,352 | Per-pair "what changed" perception |
| **B** | `phase1b` — substrate + input → output | 40,352 | Decode substrate back to grid |
| **H** | `phase1a_hierarchy` — grid → hierarchy substrate | 120,032 | Foreground vs background marking |
| **M** | `phase1_multi_pair` — all pairs → all substrates | 9,664 | Cross-pair rule consistency (the key invariant) |
| **C** | `phase1_substrate_to_code` — substrates + test → code | 1,257 | Substrate-as-scratchpad → code |
| **D** | `phase2` — full puzzle → code | 730 | End-to-end puzzle solving (the actual task) |
| **E** | `phase3` — puzzle + wrong code + feedback → right code | 7,261 | Self-correction from validation feedback |

DPO format: `phase3_dpo.jsonl` (7,261 chosen/rejected pairs).

### Substrate format (used by A/B/M/C tasks)

**Compact** — each cell is one character, no spaces between cells. Cuts grid token count ~30% vs space-separated. 3 symbols only:
- `.` background → background (both bg)
- `=` non-bg cell unchanged (input value == output value, not bg)
- `0`-`9` cell changed → write the output digit

Example: `..=4=.` not `. . = 4 = .`

Hierarchy substrate (task H) uses different symbols:
- `.` most common color (background-ish)
- `#` second-most common color
- `S` everything else

Background = `background_of()` heuristic (most common color if it dominates, defaults to 0).

### Chat format (all SFT files)

```json
{
  "task": "<phase1a|phase1b|phase1a_hierarchy|phase1_multi_pair|phase1_substrate_to_code|phase2|phase3>",
  "puzzle_id": "<8-char hex>",
  "messages": [
    {"role": "system", "content": "<single letter A-E,H,M>"},
    {"role": "user", "content": "<task-specific prompt>"},
    {"role": "assistant", "content": "<target output>"}
  ]
}
```

Phase 2 records also have `right_code_source`. Phase 3 records have `wrong_code_source` and `right_code_source`.

### Files in `data_sft/`
- `phase1_train.jsonl.gz` — 190,549 records (gzipped, 8.8MB)
- `phase1_dev.jsonl` — 21,108 records held out for encode/decode accuracy monitoring
- `phase1_train_sample.jsonl` — 100 records (uncompressed, for quick browsing on Github)
- `phase2_train.jsonl` — 730 records
- `phase3_train.jsonl` — 7,261 records
- `phase3_dpo.jsonl` — 7,261 records

## Augmentations

Phase 1 (A/B/H/M tasks): D4 symmetries (8 rotations/flips) baked in. Color permutations optional via `--color-perms N` flag (currently 0).

Phase 1 task C and Phase 2/3: no augmentation (code is orientation-specific).

## Held-out

`data/arc2_eval/` — 114 official ARC-AGI-2 benchmark puzzles. **Never** touched during training.

`bulk_collect.py` (our eval harness) only searches `data/arc1_train`, `data/arc1_eval`, `data/arc2_train` to guarantee no leakage. Training universe also explicitly excludes arc2_eval pids.

## What I want from you (GPT)

1. **Recommend a fine-tuning approach**: LoRA vs full SFT, what trainer (HF TRL / unsloth / axolotl?), what hardware (single 4090, A100, rented?).
2. **Training schedule / curriculum**: do we mix all 7 tasks together, or stage them (phase1 → phase2 → phase3)? Epochs? LR? Effective batch size?
3. **A concrete recipe**: pip install lines, config file (yaml/json), launch command. I can run on rented GPU (Lambda / Vast / RunPod).
4. **Eval loop**: After fine-tuning, how do I re-run `bulk_collect.py` on:
   - same-size training set (sanity check, expect pass@10 lift from baseline 1.4%)
   - `data/arc2_eval` (final benchmark, expect strong lift if it generalized)

Note: `bulk_collect.py` takes any OpenAI-compatible API model. For a local fine-tuned model, I can serve via vLLM and point bulk_collect at the local endpoint.

## Useful files in repo

- `bulk_collect.py` — runs any model on a split via OpenAI-compat API, validates code by exec, buckets results. Doubles as our eval harness.
- `research/agent_corpus/by_puzzle/<pid>.json` — canonical per-puzzle data: `right_codes` + `wrong_codes` with failure_mode tags
- `STATUS.md` / `STATUS.csv` — current corpus state
- `splits/all_samesize.json` — 706 puzzle IDs (training set)
- `splits/baseline_qwen_run.json` — 10-puzzle smoke test set
- `research/qwen_baseline_solved.md` — pre-fine-tune metrics (the 10 puzzles Qwen got right)
- `gen_phase1_data.py` — regenerates all phase1 JSONLs from corpus + data dirs
- `build_sft_jsonl.py` — regenerates phase2/3 JSONLs from corpus

## Key constraints

- All wrong_codes come paired with structured feedback (`failure_mode`: "exec_error" with message, or "wrong_training" with per-pair cell_diff). Feedback is short, factual, exec-grounded — no synthetic critique.
- The model only needs to output `def solve(input_grid):` in a ```python ... ``` code fence. No CoT data available.
- Single-letter system tags are intentional: at inference the caller picks the sub-task by setting `system="A"` or `"D"` etc. This lets one fine-tuned model handle all 7 capabilities.
- Zero arc2_eval leakage in any data file. Confirmed.

## Future iterations (if pass@10 stalls)

- **Rule descriptions** (natural-language one-liner per puzzle from Claude/GPT-4o, train as another task) — high cost, high signal.
- **More wrong codes** — re-run Qwen baseline at higher N and merge to inflate phase3.
- **Iterative self-improvement** — after first fine-tune, run the fine-tuned model on the same puzzles and merge its wrong codes back as new phase3 pairs.
