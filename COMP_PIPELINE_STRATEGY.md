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
