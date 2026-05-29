# Phase2_V2 Training Strategy (sealed)

Master doc for the LoRA training program. Covers thesis, corpus, runs,
ordering, and the criteria that decide what happens next.

Authority: this doc + `SOLVER_LORA_PLAYBOOK.md` (locked) + `run1/POSTRUN_DECISIONS.md`.
Where they conflict, the playbook wins.

---

## Thesis

ARC task = **latent operator graph → code**. We train a LoRA so that, given
ARC-style example pairs, the model emits an executable Python solver:

```python
def solve(input_grid):
    ...
    return output_grid
```

We teach via a **scaffolded grammar**: the model never emits the output
directly, it emits code whose execution produces the output. Two reasons:

1. Code is verifiable (exact-match eval, AST audit for hardcoding).
2. Code is the operator made explicit — the LoRA learns to extract operators
   from `T` evidence rather than memorize input→output patterns.

---

## The grammar (Run 1 contract)

### Same-size (the only thing Run 1 sees)

```python
def infer_T(input_grid):
    # extract the rule from input_grid alone
    return T  # dict[(r, c) -> new_colour]

def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out

def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

- `T` = per-cell change map. `.` = unchanged, digit = new colour.
- `apply_T` body is **bit-identical across all 740 canonical solvers**.
- Only `infer_T` body varies per puzzle.

### Diff-size (deferred to Run 2+; see POSTRUN_DECISIONS.md §1)

Different `T` semantics (geometry + content), different `apply_T` body
(build fresh canvas). The substrate `solve = infer + execute` survives;
only the level-3 implementation changes.

---

## Corpus

### What's in Run 1

| layer | records | source | trust |
|---|---:|---|---|
| L2 original | 2,081 | 740 human-vetted canonical solvers, 1 record per (puzzle, variant) | HIGH |
| L2 augmented | 29,645 | D4 × color perms × gate-filter (~15 accepted per puzzle) | HIGH (inherits L2) |
| **Total** | **31,726** | 739 unique puzzles | |

Augmentation gate: each transformed pair-set re-runs the ORIGINAL canonical
solver via `canonical_gate.accept`. Only solver-passes get written. Same code,
many surface forms = the invariance signal.

### What's NOT in Run 1 (deliberate)

- **L1 micro same-size** (43 families, 7,740 records) — set aside. Rules
  written in-conversation, not human-verified. Revisit per POSTRUN_DECISIONS §2.
- **L1 micro diff-size** (3 families, 540 records) — same reason.
- **L2 diff-size** (3 pilots) — diff-size deferred entirely.
- **L4 synthetic repair** (7,221 DPO pairs) — replaced by real failures
  collected from Run 1 itself. Better distribution (see §"Phase 3" below).

### Held-out (zero-contamination)

| bucket | name | raw puzzles | augmented (~) | role |
|---:|---|---:|---:|---|
| 1 | trained sample | 200 | n/a | sanity ("did the LoRA learn its own training set?") |
| 2 | held-out same-size | 43 | ~645 | transfer signal; Phase 3 same-size corpus |
| 3 | cold diff-size | 364 | ~5,500 | gap diagnosis; Phase 3 diff-size corpus |

**Zero overlap** between any held-out bucket and training (verified at corpus
build time).

---

## Run 1 — train

### Model + LoRA hyperparams

- Base: `Qwen/Qwen2.5-7B-Instruct` (trusted; full pipeline wired)
- LoRA: r=32, alpha=64, dropout=0.05
- Target modules: q/k/v/o/gate/up/down projections (full attention + MLP)
- Optim: AdamW, lr=2e-4, cosine schedule, 3% warmup
- Loss: **completion-only** (mask SYSTEM + USER, loss only on ASSISTANT)
- Epochs: 3, batch 4 × grad_accum 4 (effective 16)
- Max seq: 4096 tokens (long-tail truncated right)

Config in `Phase2_V2/run1/train_config.py` (importable as Python).

### Trainer driver

Lives in the GPU/RunPod environment, NOT in repo. Expected interface:
- Reads JSONL files from `train_config.Run1Config.train_files`
- Filters records whose `meta.puzzle` is in `load_heldout_ids()` (defensive;
  the corpus is already clean of held-out IDs but the filter is belt-and-suspenders)
- Applies completion-only masking

---

## Run 1 — eval

`Phase2_V2/run1/eval_harness.py` runs the LoRA against the 3 buckets,
classifies every emission, and writes one JSONL per bucket.

### Failure modes (auto-classified)

| mode | meaning | Phase 3 use |
|---|---|---|
| `PASS` | model code, run on test, exact match | — |
| `WRONG_OUTPUT` | runs, shape ok, cells wrong | high-signal (rule was off by something specific) |
| `SHAPE_MISMATCH` | output shape ≠ expected | key signal for bucket 3 (proves diff-size lock-in) |
| `RUNTIME_ERROR` | code raised | mid-signal (often surface mistakes) |
| `TIMEOUT` | 3s wall cap exceeded | low signal (often infinite loops in degenerate cases) |
| `EMPTY_OR_INVALID` | no `def solve`, syntax error | very low signal (model didn't try) |
| `HARDCODED` | passes via fingerprint / big literal / eq_grid | adversarial signal (model cheated) |

### Augmentation at eval time

Eval buckets are augmented via the same D4 × color script. This multiplies
small held-out sets:
- bucket 2: 43 → ~645 augmented prompts
- bucket 3: 364 → ~5,500 augmented prompts

Each augmented prompt is independent; the LoRA emits separate code for each.
The aggregate solve rate is the transfer/cold-probe metric.

### Expected solve rates

| bucket | expected | what under means |
|---|---:|---|
| 1 (trained) | ~97% | reasonable LoRA convergence |
| 2 (held-out same-size) | 20-40% | the transfer story; the playbook's main signal |
| 3 (cold diff-size) | < 10% | by design — we never trained the diff-size grammar |

Far-under (e.g. bucket 1 at 80%): something broke (data, masking, hyperparams).
Far-over (e.g. bucket 3 at 30%): model surprised us — diff-size generalizes
better than thought.

---

## Phase 3 — repair (driven by Run 1 failures)

For every non-PASS record in buckets 2 and 3, save:

```json
{
  "prompt": "<SYSTEM + USER>",
  "wrong_code": "<exact LoRA emission>",
  "correct_code": "<canonical solver>",
  "failure_mode": "<auto-classified>",
  "meta": { "puzzle": "...", "augment": "...", "bucket": 2 or 3 }
}
```

These become the **Phase 3 training corpus**. Two implementation paths
(decided per POSTRUN_DECISIONS §4):

### DPO

Each triple = a DPO pair. Trains the Run 1 LoRA further to prefer correct
over wrong. Best when failures are subtly wrong (plausible code, off-by-one,
wrong color pick).

### SFT contrastive

Each triple = an SFT record where the assistant is the correct code, and the
prompt includes the wrong code as anti-evidence. Best when failures are
structurally wrong (no `def solve`, hardcoded output, wrong grammar entirely).

### Why this beats synthetic perturbations

The playbook's original Layer 4 plan was "perturb canonical solvers to make
wrong code." That signal is biased toward whatever the perturbation script
knows how to break. **Real failures from the trained LoRA are exactly the
distribution we need to fix.** Tight feedback loop, no synthetic gap.

---

## Run 2 — adding diff-size (provisional)

Triggered by bucket 3's failure profile (see POSTRUN_DECISIONS §1).

### If bucket 3 is dominated by `SHAPE_MISMATCH`

- Adopt the abstract substrate: `solve = infer_T + execute`
- Rename `apply_T → execute` in all canonical solvers + SYSTEM strings
- Add diff-size SYSTEM (different `T` semantics: geometry + content rule)
- Mix corpus: same-size + diff-size in one training run
- LoRA may be stacked on Run 1 or fresh

### If bucket 3 has substantive non-PASS but reasonable shapes

- Lighter approach: keep `apply_T` name, add diff-size SYSTEM as a second
  grammar the model selects from via prompt cues
- Smaller corpus expansion sufficient

### Diff-size corpus assembly (for either path)

1. Write 20-30 more L2 diff-size canonical solvers (agent swarm via
   `canonical/diff_pilot/_AGENT_SPEC_DIFF.md`)
2. Augment them (D4 × color × gate) → ~2-3k records
3. Optionally include audited L1 micro_diff (3 families, 540 records)

---

## What's intentionally NOT in Run 1

| skipped | why | revisit when |
|---|---|---|
| L1 micro | unaudited rules; trust risk | bucket 2 weak (< 30%) per POSTRUN §2 |
| Diff-size training | no clean corpus + grammar lock-in risk | after bucket 3 diagnosis |
| Synthetic repair | distribution mismatch with real failures | never; replaced by Phase 3 |
| Composed L2 generators | depth question; needs L1 transfer signal first | Run 2 or later |
| 5-bucket eval (playbook) | held-out-family eval (#5) requires L1 | Run 3+ |

---

## Decision criteria summary

Read after Run 1 eval is in hand:

| trigger | choice |
|---|---|
| bucket 1 < 90% | something broke in training. Investigate before continuing |
| bucket 2 < 30% | L2-only transfer weak. POSTRUN §2 → audit + include L1 in Run 2 |
| bucket 2 30-60% | normal range. Phase 3 fixes the long tail |
| bucket 2 > 60% | L2 sufficient. Skip L1 audit; focus Phase 3 on bucket 3 |
| bucket 3 SHAPE_MISMATCH > 80% | grammar lock confirmed. Run 2 adopts `infer + execute` (POSTRUN §1) |
| bucket 3 SHAPE_MISMATCH 30-80% | partial generalization. Lighter Run 2 fix |
| bucket 3 EMPTY/RUNTIME > 50% | no diff-size representation. Run 2 needs new corpus + new SYSTEM |

---

## Files

| path | role |
|---|---|
| `canonical/sft/real_samesize_original.jsonl` | L2 original training records |
| `canonical/sft/real_samesize_augmented_shard0[0-3].jsonl` | L2 augmented training records |
| `run1/train_config.py` | LoRA + data config; importable |
| `run1/eval_harness.py` | bucket runner + classifier |
| `run1/splits/bucket{1,2,3}*.txt` | held-out puzzle id lists |
| `run1/POSTRUN_DECISIONS.md` | decisions pending Run 1 eval read-out |
| `SOLVER_LORA_PLAYBOOK.md` | the playbook (locked principles) |
| `TRAINING_STRATEGY.md` | this doc |

---

## One-line summary

**Train Qwen2.5-7B + LoRA on 31,726 same-size SFT records. Eval 3 buckets.
Use the failures as Phase 3 input. Decide Run 2's grammar from bucket 3's
shape-mismatch signal.**
