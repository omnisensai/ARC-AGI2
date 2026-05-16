# Fine-Tuning Strategy — STRATEGY.md

**Status:** Active plan. Collection pipeline in progress. First fine-tune target: $5 and a weekend.

---

## Core insight

Models solve ARC puzzles ~10% of the time raw. The correct algorithm exists in the model's weight space — it's a roulette wheel. Fine-tuning doesn't add capability. It weights the wheel so the model lands on the correct slot more reliably.

Empirical proof: on puzzle 13e47133, 12 runs across GPT and Grok produced accuracy ranging from 62% to 100%. Same models, same puzzle, different runs. The 100% solve used the exact same BFS-from-boundary algorithm that appeared in the 93.8% solves — it just also got the 8-connectivity propagation right. One line difference, 56 errors.

**Fine-tuning target:** not "teach the model to solve ARC" but "shift the probability distribution so correct algorithmic choices become the default path."

---

## Model choice

**Qwen-2.5-7B-Instruct**

- OpenRouter: `qwen/qwen-2.5-7b-instruct` ($0.04/$0.10 per 1M tokens)
- HuggingFace: `Qwen/Qwen2.5-7B-Instruct` (free download, LoRA trainable)
- Same weights on both platforms. Collect failures on OpenRouter, fine-tune the same model on Colab.
- Fits on free Colab T4 with 4-bit quantization.

Why not a "Coder" variant: Qwen 2.5 base already has strong coding. The base instruct model is available on OpenRouter and directly fine-tunable. No transfer gap.

---

## What to train: three phases

### Phase 1 — Rule identification (free, ~9,000 examples)

Teach the model to see transformation patterns using the `+ = - . ~` notation.

**Training tasks (all ground truth from `transformation_grid.py`):**

- **Substrate encoding:** (input grid, output grid) → transformation grid
- **Substrate decoding:** (input grid, transformation grid) → output grid
- **Cross-pair pattern:** 2-3 transformation grids from training pairs → 1-sentence rule description

**Data:** 2,240 puzzles × ~4 pairs each = ~9,000 examples. Augment with rotations, flips, color permutations to ~50,000. Pure Python generation, zero API cost.

**Empirical status of transformation grids:** tested on puzzle 13e47133 across 12 runs. Substrate prompt vs raw prompt was within noise — run 1 substrate won (93.8% vs 83.2%), run 2 raw won (93.8% vs 83.2%). Transformation grids did not reliably steer models toward better first-pass code. Their value may be as a training representation (teaching the model to see patterns) rather than as a prompt component. Test this empirically in Phase 1 before committing.

### Phase 2 — Rule → code (free to ~$5, ~100,000+ examples)

Teach the model: "when the transformation grid looks like THIS, the correct code pattern is THIS."

**Data sources (free):**

| Source | Examples | Status |
|---|---|---|
| Hodel's arc-dsl (400 training puzzles, DSL format) | Translate to Python via API (~$2) then augment × 100 | Available now |
| cristianoc's ARC-AGI-2 solvers (120 puzzles, plain Python) | Clone and use directly | Available now |
| Your existing true_solves/ (verified Python) | Use directly + augment | ~12 puzzles, growing |
| bulk_collect.py correct codes | Harvest from collection runs | After Step 1 runs |

**Augmentation:** each correct solver × 100 variants (color permutation, rotation, flip, translation). The same `solve()` works on all variants because it uses variables not hardcoded colors. One puzzle = one rule = one code pattern × 100 augmented grid variants.

**Format:**
```json
{"messages": [
  {"role": "system", "content": "You solve ARC puzzles. Given training pairs, write a solve() function."},
  {"role": "user", "content": "PAIR 1: Input: [...] Output: [...]\nPAIR 2: Input: [...] Output: [...]"},
  {"role": "assistant", "content": "def solve(input_grid):\n    ..."}
]}
```

### Phase 3 — Code correction ($4.50, ~22,000 examples)

The highest-value phase. Teach the model to fix its own mistakes.

**Data from `bulk_collect.py`:**
- Run Qwen-2.5-7B 10× on each of 2,240 puzzles via OpenRouter
- ~5% correct, ~95% wrong = ~21,000 wrong codes + ~1,100 correct codes
- Cost: ~$4.50 total
- Time: overnight with 20 parallel workers

**SFT format (wrong → right):**
```json
{"messages": [
  {"role": "system", "content": "You fix ARC puzzle solvers. You receive wrong code with error counts. Output the corrected solve() function."},
  {"role": "user", "content": "PUZZLE: [training pairs]\nWRONG CODE: def solve(...):\n  ring = min(r-rmin...)\nERRORS: 56/900 cells, diagonal turns at box corners"},
  {"role": "assistant", "content": "def solve(...):\n  # BFS 8-conn from boundary\n  for dr,dc in dirs8:..."}
]}
```

**DPO format (subtle wrong vs correct):**
For puzzles with both `correct` and `wrong_test` (passes training, fails test):
- Same prompt
- Chosen: correct code
- Rejected: wrong_test code (the overfit solution)

This teaches the hard distinction between "passes training" and "actually generalizes."

---

## Bug-pattern library

Recurring failure modes across models and puzzles. Fine-tuning penalizes these specific patterns.

| Pattern | Signature | Frequency | Fix |
|---|---|---|---|
| `cluster_vs_cell_granularity` | missed activations inside edge-touching cluster | High | Lift property test to cluster level with `any()` |
| `diagonal_vs_square_turn` | off-by-one color at box corners in concentric rings | High (5/12 runs) | Use 8-conn (Chebyshev) for distance propagation, not 4-conn |
| `bounding_box_vs_bfs` | wrong colors in non-rectangular wraparound regions | High (5/12 runs) | BFS from actual boundary, not min(r-rmin, rmax-r, ...) |
| `wrong_connectivity_4_vs_8` | diagonal halo cells missing | Medium | Switch boundary detection to dirs8 |
| `hardcoded_grid_dimensions` | all training pairs fail on different-sized grids | High | Use H, W variables not literal numbers |
| `over_extended_scoped_fix` | regression on passing pair after fixing failing pair | High | Additive condition, not rewrite |
| `identical_code_resubmission` | byte-equal code across iterations | Medium | Detect and force actual changes |
| `generic_perimeter_framing` | output has border ring regardless of seed position | Medium | BFS from anchor, not grid perimeter |

**Training examples per pattern:** inject each bug into 50+ correct solvers, generate feedback, pair with the fix. ~400 examples per bug pattern × 8 patterns = ~3,200 bug-specific training examples.

---

## Data generation pipeline

### What already exists

| Component | Location | Status |
|---|---|---|
| `transformation_grid.py` | repo root | Working — computes `+ = - . ~` grids |
| `mechanistic_feedback_generator.py` | repo root | Working — cluster analysis, error classification |
| `paste_helper.py` | repo root | Working — extracts code, validates, saves artifacts |
| `finetune_corpus.py` | repo root | Working — JSONL corpus with correct/wrong_test/wrong_training buckets |
| `backfill_finetune_corpus.py` | repo root | Working — sweeps existing Model Results into corpus |
| `research/finetune_corpus/` | corpus directory | 13 records across 3 puzzles (growing) |

### What to build

| Script | Purpose | Status |
|---|---|---|
| `bulk_collect.py` | Automated API collection loop — runs Qwen-7B on all puzzles via OpenRouter | Instructions ready for Claude Code |
| `build_training_data.py` | Converts corpus JSONL into SFT/DPO training format | Part of bulk_collect instructions |
| `data_generator.py` | Generates Phase 1 + Phase 2 data from puzzles + transformation_grid.py | To build |

### External data (free, clone from GitHub)

| Source | What | Puzzles | Format |
|---|---|---|---|
| `michaelhodel/arc-dsl` | Correct solvers for 400 training puzzles | ARC-AGI-1 training | Custom DSL (needs Python translation) |
| `michaelhodel/re-arc` | 1,000 verified variants per puzzle + generators | ARC-AGI-1 training | JSON input/output pairs |
| `cristianoc/arc-agi-2-abstraction-dataset` | 120 Python solvers | ARC-AGI-2 | Plain Python `solve()` functions |
| `fchollet/ARC-AGI` | Official puzzle JSONs | 800 ARC-AGI-1 | JSON |

---

## Data volume estimates

| Category | Examples | Source | Cost |
|---|---|---|---|
| Substrate fluency (Phase 1) | ~50,000 | transformation_grid.py + augmentation | $0 |
| Rule → code (Phase 2) | ~100,000 | Hodel translation + augmentation | ~$2 |
| Code correction SFT (Phase 3) | ~20,000 | bulk_collect.py wrong→right pairs | ~$4.50 |
| DPO pairs (Phase 3) | ~800 | wrong_test vs correct | $0 (subset of collected) |
| Bug-pattern examples | ~3,200 | Programmatic mutation of correct solvers | $0 |
| **Total** | **~174,000** | | **~$7** |

---

## Infrastructure

```
Your MacBook Air = just a browser. Everything heavy is cloud.

Collection:   OpenRouter API → JSONL on your laptop        ~$4.50
Training:     Google Colab free T4 → LoRA adapters          $0
Storage:      HuggingFace Hub → adapter weights (50MB)      $0 (free account)
Inference:    Colab again, or HuggingFace Inference API     $0-9/mo

                     Your laptop
                         │
                     browser tab
                    ╱          ╲
         OpenRouter API     Google Colab
         (collect data)     (train model)
               │                │
          Qwen-7B runs     downloads Qwen-7B
          returns code     from HuggingFace
               │           trains LoRA on GPU
               ↓           saves adapter to HF
          JSONL corpus          │
               │                ↓
               └──→ training data → fine-tuned model
```

---

## Execution sequence

### Step 1: Build collection pipeline (1-2 days)
- Give Claude Code the `bulk_collect.py` instructions
- Test on 3 puzzles × 2 runs
- Verify records land in `finetune_corpus.py` buckets correctly

### Step 2: Run bulk collection (overnight, ~$4.50)
- `python bulk_collect.py --model qwen/qwen-2.5-7b-instruct --runs 10`
- Wake up to ~22,000 labeled code attempts

### Step 3: Generate Phase 1+2 data (1 day, free)
- Clone Hodel's arc-dsl, translate 400 solvers to Python (~$2)
- Run `data_generator.py` to produce substrate fluency + rule→code examples
- Generate augmented variants

### Step 4: Build training data (hours, free)
- Run `build_training_data.py` to format everything as SFT JSONL
- Extract DPO pairs from wrong_test vs correct

### Step 5: Train on Colab (4-8 hours, free)
- Open Colab notebook
- Load Qwen-2.5-7B-Instruct with 4-bit quantization
- Attach LoRA (r=16, targeting all projection layers)
- Train on combined dataset
- Save adapter to HuggingFace

### Step 6: Evaluate (1 day, free)
- Run fine-tuned model on 50 held-out puzzles
- Compare solve rate vs base Qwen-7B
- Compare error patterns: do bug-library patterns decrease?
- If signal positive → scale up data, consider 32B model
- If signal null → examine which phase's data helped least, revise

### Total: ~1 week, ~$7

---

## What's novel about this approach

No public dataset of plain Python ARC solvers exists. Everyone generates code at runtime and discards it after scoring. The `research/finetune_corpus/` with verified Python solvers, paired with wrong-code attempts and error classifications, is the first structured dataset of its kind.

The corrector framing (Phase 3) is distinct from training a solver from scratch. Instead of "here's a puzzle, write perfect code" (roulette), it's "here's wrong code and what's wrong with it, fix it" (constrained search). Debugging is a smaller search space than creation.

The three-phase pipeline (see → write → fix) trains the full reasoning chain that competition requires: identify the rule, implement it, verify against training pairs, correct if wrong.

---

## Per-puzzle notes

Each `<puzzle_id>.md` file in this directory contains:
1. Canonical rule discovered
2. Per-model iteration arc
3. Failure modes observed (mapped to bug-pattern library)
4. What unlocked the fix
5. Concrete fine-tuning signals contributed

### Index

| Puzzle | File | Models solved | Key failure modes |
|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [8f3a5a89.md](8f3a5a89.md) | GPT(2), Grok(3), Gemini(5), Opus(2), Sonnet(9) | cluster_vs_cell, wrong_connectivity, hardcoded_dims, over_extended_fix |
| [13e47133](https://arcprize.org/tasks/13e47133) | [13e47133.md](13e47133.md) | GPT(2), Grok(2), Claude(1) | diagonal_vs_square_turn, bounding_box_vs_bfs |

Revise this document whenever a new puzzle is cataloged or a recurring pattern crystallizes.

---

## Open questions

- Does transformation grid training (Phase 1) actually improve code quality, or is it noise? Today's 12-run experiment was inconclusive.
- What's the minimum dataset size for measurable Phase 3 (corrector) gain? Hypothesis: 5K examples.
- Can DPO on wrong_test vs correct teach the "passes training but overfits" distinction? Theory says yes, untested.
- Should Phase 2 train on Hodel's DSL notation or only plain Python? DSL is the existing verified format but the model must output Python.
- At what model size does the corrector saturate? 7B may be enough for correction even if insufficient for first-pass solving.
