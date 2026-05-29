# Run 1 Post-Run Decisions

Read this AFTER Run 1's eval is in hand. Each section below is a decision
that's open during Run 1 and resolves based on the eval read-out.

---

## 1. The `apply_T` lock-in problem (GPT, pre-train)

### The architectural critique

Locking the **same-size `apply_T` body** into the SYSTEM prompt is fine for
Run 1 (same-size only) but blocks diff-size cleanly when we extend.

Three levels of invariance:

| level | shape | breaks when |
|---|---|---|
| Substrate truth | `solve: grid → grid` | never |
| Run 1 scaffold | `solve = infer_T + apply_T` | switching to a non-T representation |
| Run 1 implementation | `apply_T = copy + overwrite` | shapes differ (crop / scale / tile / extract) |

The Run 1 SYSTEM bakes level 3 into the contract. That's correct for the
same-size corpus we're training (every target uses bit-identical level 3),
but it commits the model to a scaffold that doesn't generalize.

### Why ship Run 1 as-is anyway

- Every L2 same-size target in the training corpus IS the level-3 body.
- SYSTEM-as-shown matches ASSISTANT-as-emitted exactly.
- The model learns one grammar cleanly. No corpus drift cost.

### Run 2 contract (adopt when adding diff-size)

```python
def solve(input_grid):
    latent = infer_T(input_grid)        # latent shape varies by task family
    return execute(input_grid, latent)  # task-family-specific renderer
```

- `execute` body varies by family (same-size: copy+overwrite; diff-size: build fresh)
- Two SYSTEM prompts (same/diff) but BOTH share the abstract `infer → execute`
- Rename happens in: 740 same-size canonical solvers, 3 diff pilots, SYSTEM strings
- Optional: keep `apply_T` as a backwards-compatible alias to `execute`

### Decision trigger

Run 1 bucket 3 (cold diff-size) failure-mode distribution decides:

| bucket 3 dominant mode | implication |
|---|---|
| `SHAPE_MISMATCH` everywhere | model is forcing same-size shape on diff-size — lock-in confirmed; Run 2 must adopt `execute` to unblock |
| `WRONG_OUTPUT` with correct shape | partial generalization; lighter Run 2 changes might suffice |
| `EMPTY/RUNTIME` | model has no diff-size representation at all; Run 2 needs new training data AND new SYSTEM |

---

## 2. L1 micro — keep set aside or revisit?

Run 1 trains on L2 only. L1 micro (43 families × 180 = 7,740 records) was
written in-conversation; rules aren't human-verified.

### Decision trigger

If Run 1 bucket 2 solve rate is **low (< 30%)**:
  - L2-only didn't transfer; the operator coverage was the missing piece
  - Audit L1 micro families (one-by-one rule review), drop buggy ones, include in Run 2

If Run 1 bucket 2 solve rate is **high (> 60%)**:
  - L2 alone is sufficient for the same-size grammar; L1 is unnecessary
  - Keep L1 set aside; don't burn audit time

---

## 3. L2 augmentation — full 40 vs smaller cap

Run 1 augments 8 D4 × 5 color perms (up to 40 per puzzle, ~15 accepted on
average). This gave ~22% truly canonical (31-40 accepted), 65% brittle (1-10).

### Decision trigger

If brittle-solver puzzles (1-10 accepted) underperform in bucket 1 eval:
  - The augmentation gate is filtering OUT the model's actual learning signal
    for those solvers — they only see 1-3 surface forms
  - Run 2 should bypass the gate for those solvers (accept all 40), OR
    rewrite the brittle canonical solvers to be surface-invariant

If brittle puzzles match canonical puzzles in eval:
  - Augmentation diversity matters less than expected; cap can stay low

---

## 4. Phase 3 repair — DPO vs SFT contrastive

Playbook listed both. Run 1's bucket 2 + bucket 3 failures determine which.

### DPO (preferred)

- Each (prompt, wrong_code, correct_code) triple is a DPO pair
- Wrong = model's own output, correct = canonical solver source
- Trains the Run 1 LoRA further to **prefer** correct over wrong

### SFT contrastive

- Each (prompt, wrong_code, correct_code) becomes a record where assistant
  starts with the wrong code and is **corrected** to the right code
- Teaches the model to FIX wrong code rather than to prefer it

### Decision trigger

| Run 1 failure profile | choose |
|---|---|
| Failures are **plausible but subtly wrong** (off-by-one, wrong color pick) | DPO |
| Failures are **structurally wrong** (no `def solve`, hardcoded output, wrong grammar) | SFT contrastive (need to teach the correct shape, not just rank) |

---

## 5. Held-out diversity — bucket 2 small?

Bucket 2 is 43 same-size puzzles (43 raw → ~645 augmented eval prompts).
We accepted this for Run 1.

### Decision trigger

If bucket 2 solve rate is **noisy across operators** (some operators 100%, others 0%):
  - 43 isn't enough to fairly sample operator transfer
  - Run 2 reshuffles: move 100 from training → bucket 2 (training ~27.5k, bucket 2 ~2.1k augmented)

If bucket 2 distribution is **smooth across operators**:
  - 43 was sufficient; keep training size maximized

---

## Pinning these decisions

After Run 1 eval lands:
1. Fill in the actual bucket distributions next to each "decision trigger"
2. Annotate each section with the chosen path
3. This doc + the eval report becomes the Run 2 spec
