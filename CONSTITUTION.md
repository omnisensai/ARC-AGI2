# ARC-AGI Framework Constitution

The principles that drive this fine-tuning pipeline. Operating details live
in `README.md`, `research/Fintune.md`, and `research/Phase1_Substrate_Spec.md`;
this document is for the ideas that survive across pipeline rewrites.

If you delete every Python file in this repo, this is what should be true of
whatever you build next.

## Core philosophy

Iter-1 is roulette. Don't try to control where the model lands. Strip the
seed prompt to the minimum that's still well-formed and accept the variance.

Iter-N feedback is the lever. The model has prior code and a validation
result; this is where the framework can do real work by deciding whether
the rule is wrong or the code is wrong, and emitting one targeted hint that
addresses exactly that.

Generic hints buried in long diagnostic dumps do not bind to specific bugs.
Targeted hints generated from the actual error pattern do.

Iteration count is more important than feedback richness. The framework's
job is to keep iterations productive, not to front-load every diagnostic
into iter-1.

## Phases

| Term | Meaning |
|---|---|
| **Comprehension phase** | Iter 1. Model has no prior code. Must derive the rule from training pairs. |
| **Refinement phase** | Iter 2+. Model has prior code + feedback. Editing or rewriting toward correct. |
| **Submit-eligible** | Training pairs all pass. Eligible to submit; answer may still be wrong on test. |

## Every model invocation runs in a fresh context

Same-chat continuation is retired. The data showed continuation iters anchor
the model in defensive patching: it edits code while standing inside its
prior interpretation, and can't discard the abstraction even when the
abstraction is what failed.

R1 uses the seed prompt. R⟨N≥2⟩ uses a fresh feedback prompt built from
R⟨N-1⟩'s code + structured pass/fail. Hedge solves use the seed prompt
again. No continuation, ever.

**Empirical anchor:** 13e47133 went FAIL → FAIL (false-confident submit,
124/1800 wrong) in 3 continuation iters under GPT, then FAIL → exact match
(1800/1800) in 2 iters with one fresh refinement. Same model, same iter-1
code, no content hints leaked. The framework only changed the question being
asked.

## Interpretation vs computation

Iter failures decompose into two independent spaces:

- **Interpretation:** what is the transformation rule?
- **Computation:** does the code implement the stated rule?

Fresh refinement forces a judgment first: pick A (rule correct, patch code)
or B (rule wrong, replace abstraction). Each iter then prunes one space:

- Pick A → narrow implementation, interpretation held fixed
- Pick B → discard one rule from interpretation, restart implementation

This is why fresh refinement scales like search rather than like noise.

The same asymmetry holds for small base models. Raw Qwen-2.5-7B-Instruct
produced 0/99 correct codes on 10 same-size eval puzzles, but the code it
wrote was structurally correct code for a wrong rule — perception fails, not
coding. This diagnosis motivates the substrate training approach (Phase 1 of
the fine-tuning pipeline): teach the model to see the change pattern
explicitly before asking it to write code.

## The substrate is a training signal, not a prompt scaffold

Earlier versions of this framework injected transformation-grid substrates
into iter-1 prompts as a "physics layer." Empirically this didn't reliably
improve iter-1 code quality — substrate noise is decoration once the model
already understands the rule, and the model usually does for simple puzzles.

The current framing: the substrate's value is as a **training-data
representation**, not a prompt-time injection. Phase 1 of the fine-tune
teaches the model to compute the substrate (`(input, output) → substrate`)
and apply it (`(input, substrate) → output`) as deterministic functions.
The hypothesis is that internalizing these functions sharpens the
perception step that Phase 2 (`pairs → code`) depends on.

If empirical results show Phase 1 doesn't transfer to better Phase 2 code,
we drop the substrate. The substrate is a hypothesis, not a religion.

## Comp-clean invariant

Every signal we put into a model prompt must be derivable from data the
puzzle hands to a real competitor — namely `train`, `test[i].input`, and
the model's own prior code. **No signal derived from `test[i].output` may
enter a model prompt.**

**Allowed in prompts:** training pair pass/fail, training cell-diff counts
and diff grids, the model's own stated rule, the model's own prior code,
structural diffs between training pairs, bug-class fingerprints computed
on training-pair errors, process scaffolding (judge-then-repair,
no-special-cases constraints).

**Forbidden in prompts:** per-cell diff on test, "your test output is off
by N cells", error-region locations on the test grid, ground-truth-derived
hints of any kind.

This invariant is what lets us run research mode and competition mode off
the same loop: if the loop holds the invariant, research-mode adds outcome
labeling visible to humans but invisible to the model.

Concretely in code: the **competition validator** runs on training pairs
only. The **research validator** runs on training AND test pairs. Both
produce identical per-pair diagnostic outputs; only the latter ever sees
test truth. Feedback prompts for R2 are constructed from the competition
validator's output only.

## Trust the observation, not the prescribed fix

When a feedback prompt includes a detector's structural diagnosis ("errors
concentrate inside a non-rectangular chamber that wraps around interior
walls"), include the observation but not the detector's guess about how to
fix it.

Detectors are local pattern matchers. Their observation is a fact about the
error geometry; their prescription is a guess about the right repair, and
that guess biases the model toward A-pick (small code fix) even when the
correct move is B (replace the abstraction).

Empirical: on 13e47133, surfacing a detector's prescribed fix pushed
continuation chats into 2 more failed iters. The fresh-refinement path with
observation only let the model judge B and write the right rule.

## Fine-tuning corpus principles

Code attempts partition into three buckets, each with distinct training value:

| Bucket | Definition | Training use |
|---|---|---|
| `correct` | All training + test pairs pass | Phase 2 SFT target |
| `wrong_test` | Training all pass, test fails | DPO `rejected` (paired with `correct` on same puzzle) |
| `wrong_training` | At least one training pair fails | Phase 3 corrector SFT input |

`wrong_test` is the rarest and most valuable label — the model overfit a
rule that survived the visible examples but didn't generalize. DPO pairs
where `chosen = correct` and `rejected = wrong_test` (same puzzle, same
prompt) teach the hard distinction between "passes training" and "actually
generalizes."

`wrong_training` is more abundant but its signal is weaker because the
wrong code fails for visible-example reasons the corrector can directly
address from training-pair feedback alone.

The corpus is a post-hoc training artifact, never a feedback signal during
iteration. Records are immutable once written; new attempts append, never
overwrite.

## Falsification criteria

This framework is not religious. It loses if:

- Targeted iter-N+1 feedback does not measurably outperform raw "you failed
  pair X" feedback across ≥10 puzzles. The bug-class library is decoration
  if so.
- The minimal seed prompt causes iter-1 solve rate to drop sharply vs a
  scaffolded prompt. We accepted some loss; we did not accept catastrophe.
- Substrate-trained models do not solve more eval puzzles than baseline
  models when given the same inference setup. The substrate framing is
  decoration if so.
- Cell-level correctness on training pairs does not separate `correct`
  from `wrong_test` outcomes in calibration data.

When any of these is observed empirically, the framework is wrong and we
redesign. The framework is the SET of choices listed in this document.
Discarding any one of them in response to falsifying data is the intended
response, not an exception.
