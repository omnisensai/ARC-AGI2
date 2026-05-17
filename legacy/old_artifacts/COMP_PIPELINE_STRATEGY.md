# Competition Pipeline Strategy

Notes captured during substrate validation. NOT implemented — these are decisions
to apply when we eventually build the actual ARC-AGI competition submission pipeline.

## Submission strategy by training-pair count (N)

ARC gives 2 attempts per test pair. False-positive risk on the SUBMIT verdict
scales inversely with N (more training pairs = stronger constraint = lower risk
that training-pass code fails on test).

| N    | Constraint strength       | Submission strategy                                                                 |
|------|---------------------------|-------------------------------------------------------------------------------------|
| 2    | Low (false positives common) | Force iter >= 2. Submit iter-K SUBMIT solution AND a structurally different alternate as the 2 ARC attempts. |
| 3    | Medium                    | Single SUBMIT usually fine. Hedge with a 2nd candidate if iter-2 disagrees with iter-1 on test output. |
| 4-6  | High                      | Single SUBMIT. Use 2nd attempt as exact duplicate or trivial perturbation.          |

Implementation hook: when `run_feedback.py` returns SUBMIT at iter K on N=2,
prompt the model with "solve this again using a structurally different
algorithm" and ship both as the two ARC attempts.

## Puzzle ordering (which to attempt first)

Solve in priority order:

1. **Same-size puzzles first** (output dims == input dims). These are pure
   in-place transformations; no shape inference required. The substrate
   feedback (transformation grid, diff map) is most informative when grids
   align cell-for-cell.
2. **Shrink/expand puzzles last** (output dims != input dims). These add a
   shape-inference layer on top of the cell-rule layer. Substrate currently
   assumes cell-aligned grids; the diff map and transformation grid don't
   render cleanly when dims differ. Defer until we build dim-aware feedback.

Rationale: time per solved puzzle is much lower on same-size puzzles, both
because the problem is structurally simpler and because our feedback machinery
is already optimized for it. Hit the easy wins first, accumulate operation-menu
entries, then tackle the harder shape class once we've built the menu.

## Candidate clustering for the 2 ARC attempts

The substrate gate (training-pass) gives no information about test correctness
when the test answer is hidden. Two failure cases break the gate:

1. **False positive**: an iter passes all training pairs but is wrong on test
   (e.g., Gemini's MDL solver on 135a2760 — algorithmically wrong, but the
   training pairs didn't expose the bug).
2. **False negative**: an iter fails training but is right on test
   (e.g., Claude iter 1 on 135a2760 — correct algorithm, fails 1 training
   pair due to a tie-breaking degeneracy that the test doesn't trigger).

A false negative is especially dangerous: feedback forces the model to "fix"
training, which often means overfitting to the specific training corruptions
and breaking the test. Iter K+1 passes training but is wrong on test.

**The hedge: cluster all saved iter outputs by test-input prediction.**

Comp-pipeline submission logic:

1. After all iters complete, run each saved `solve()` on the test input.
2. Cluster iters by their test-output (cells that match exactly).
3. Submit the 2 most-different clusters as the 2 ARC attempts.
4. Tiebreak preferences:
   - Cluster representative: prefer the iter that passed training.
   - Second slot: prefer the cluster whose test output differs most
     (e.g., maximum cell-Hamming distance from cluster 1's output).

This catches the false-negative case: iter 1's test output (correct) and
iter 2's test output (4 cells different) form 2 clusters. Both submitted.
Win on attempt 1.

Doesn't catch: all iters producing the same wrong test output. That's the
limit of unhedgeability — if no iter ever produces the right answer, no
submission strategy can recover.

Implementation note: `auto_iter.py` already saves every iter's response;
the comp pipeline only needs to add the post-hoc clustering step before
submission.

## Dual-candidate hedge (code + hand grid, every iter)

PRIMARY hedge — runs every iter on every puzzle, no extra LLM call.

The substrate prompt asks for BOTH:
1. `def solve(input_grid)` — validated against training pairs.
2. `TEST_OUTPUT = [...]` — model's hand-written best-guess test output.

Code generation and pattern recognition are separable skills. Models can
succeed at one and fail at the other:

- Gemini on 135a2760: hand-wrote correct test output, but its code produced
  43 cells wrong on test (iter 2) and 8 cells wrong (iter 3). Pattern
  recognition succeeded; code generation failed. Submitting only the code
  would lose the puzzle. Submitting the hand grid wins.
- Grok on 135a2760: code is a hardcoded dispatcher. Hand grid would be the
  same as the code's output (same memorized cells). Redundant but no harm.
- GPT iter 4 on 135a2760: code correct, hand would be correct. Redundant.
- Claude iter 2 on 135a2760: code correct, hand would be correct. Redundant.

The Gemini case is the win. The others are redundant — also fine, since
ARC takes max over the two attempts.

### Submission slots (comp pipeline)

For each test pair, submit:
- Slot 1: `solve(test_input)` — code-computed
- Slot 2: hand-written TEST_OUTPUT from the same iter

Both candidates from a single LLM call. No extra cost.

### Hand grid validation (substrate validation only, NOT in feedback)

During substrate validation we have test ground truth (it's in the
puzzle.json file). `auto_iter.py` validates the hand grid against ground
truth and prints the result for analysis:

```
Hand grid vs test ground truth (analysis only, not in feedback):
  N/total cells wrong (MATCH | no match)
```

CRITICAL: this validation result is NEVER added to the feedback sent to
the model. Including it would leak the test answer into the loop and
break the substrate gate. The validation is purely for our scoreboard
and analysis — to track when models hand-grid right but code-wrong (the
Gemini class) and how often this happens.

In real comp: no hand grid validation possible (no test ground truth).
We just submit both candidates as the two ARC slots.

### Why dual-candidate beats structural-diversity as the primary hedge

| Property | Structural-diversity hedge | Dual-candidate hedge |
|---|---|---|
| Extra LLM calls | +1 per N=2 puzzle | 0 |
| Catches Gemini case (right pattern, wrong code) | partial (43 → 8 wrong) | full (hand grid was 0 wrong) |
| Catches all-wrong case | no | no |
| Catches model-disagrees-with-itself | n/a | yes (code ≠ hand → genuine diversity) |

Use both. Dual-candidate runs every iter; structural-diversity hedge runs
once per N=2 puzzle as additional pool.

## N=2 forced hedge iteration (validated)

For puzzles with N=2 training pairs, automatically run an extra "hedge"
iteration AFTER the model returns SUBMIT, before submission. Goal:
generate a structurally different second candidate that also passes
training, so we submit two algorithmically-diverse solutions instead of
two copies of one solution.

The hedge is the only hedge available for N=2 false-positives. Without
ground truth on the test, we have no signal to discriminate "training-pass
because correct" from "training-pass because under-constrained." Forcing
algorithmic diversity is the only structural lever.

### Hedge prompt (truthful framing — do not lie about test failure)

```
EDGE-CASE HEDGE ITERATION (auto-triggered for N=2 puzzles)

Status: training 2/2 passed. Verdict: SUBMIT-ELIGIBLE.

Because this puzzle has only 2 training pairs, the validator runs a hedge
iteration before submission. Goal: produce a STRUCTURALLY DIFFERENT solver
that ALSO passes both training pairs. We will submit both your current
solver and the hedge solver as the two ARC attempts.

The 2 training pairs may not have exposed all edge cases relevant to the
test input. Review your current code and consider:

1. What edge cases of the underlying rule are NOT exercised by the 2
   training pairs?
2. What happens when the test grid has dimensions, color distributions,
   or panel counts unlike anything in training?
3. Are there parameter choices in your code (period bounds, cost
   coefficients, tie-breaks, magic constants) that could go a different
   way on the test? Pick the OTHER way.
4. Is there a structurally different algorithm that would also produce
   correct output on both training pairs? Write that.

REQUIREMENTS:
- Return an UPDATED def solve(input_grid) function.
- It MUST still pass both training pairs (we will validate).
- It SHOULD differ structurally from your current solver — different
  algorithmic approach, different parameter regime, different cost
  function, etc. Trivial reformatting does not count.
- The two solvers will be submitted as the two ARC attempts.

Do NOT respond with prose only. Return the def solve(input_grid).
```

Why truthful framing: lying ("your test failed") makes the model doubt
its diagnosis and produce confused output. Stating the policy ("we hedge
on N=2") gives the model a sensible reason to vary its approach.

### Validation result (135a2760, Gemini)

| | Iter 2 (original SUBMIT) | Iter 3 (hedge) |
|---|---|---|
| Training | 2/2 pass | 2/2 pass |
| Test cells wrong | 43 | 8 |
| Output differs from iter 2 | — | 43 cells |

Iter 3 isn't a true solve (8 cells short of exact match), but the hedge:
- Produced real algorithmic diversity (43-cell Hamming distance between outputs)
- Moved toward ground truth (5× error reduction, 43 → 8 wrong cells)
- Did so via a small targeted change (cost coefficient 1× → 2× on the
  errors term), shifting period selection on the test grid

### What the hedge can and can't catch

CAN catch:
- Magic-constant overfit: model picked one parameter value, hedge tries
  the other side. If the original was wrong direction, hedge corrects.
- Algorithmic class wrong: hedge might switch to a different decomposition
  (e.g., bounding-box → separator-based panel split).
- Tie-break degeneracies: original picked one of several equally-scoring
  options on training; hedge picks a different one.

CAN'T catch:
- Both candidates wrong with the same wrong test output (hedge produced
  near-identical code).
- Both candidates wrong with different test outputs that are both wrong
  (hedge produced diversity but neither lands on truth).
- Model ignores the hedge prompt and resubmits same code.

### Why the hedge is pure upside

ARC takes max over the two attempts: if any submission matches, you win
the puzzle. So:

- Original was correct → candidate 1 wins, hedge doesn't matter.
- Original was wrong, hedge is correct → candidate 2 wins.
- Original wrong, hedge wrong → lose either way; hedge cost was one extra
  iter (~$0.10).

Hedge never strictly hurts. Only failure mode is wasted iter cost when
neither candidate is right.

## The actual binding constraint

Empirically (substrate validation, 8f3a5a89 + 135a2760, all 5 models):

- 100% solve rate within 10 iters when models produce real algorithmic
  code. The substrate + feedback loop converges.
- The framework's only failure mode is the false-positive case where
  training passes, the test answer is wrong, AND the hedge fails to
  produce a candidate that lands on the truth.

This is why the candidate-clustering hedge exists. It's not a guarantee;
it's the structural maximum we can do without test-side ground truth.

The cases where the hedge IS NOT enough (Gemini-style: algorithmically
wrong but training-passing, hedge produces a different-but-still-wrong
solution) are the irreducible loss budget. We accept those as the cost
of operating on hidden test data.
