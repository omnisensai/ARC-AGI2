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
