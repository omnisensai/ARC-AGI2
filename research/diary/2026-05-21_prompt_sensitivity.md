# Fine-tune diary

A chronological log of what we found while training and evaluating the
ARC-AGI-2 LoRA. Each entry is a single observation that changed the project's
direction, written when it was still fresh.

---

## 2026-05-21 — Prompt format sensitivity is everything

### Context

Run 1 complete. LoRA trained on Qwen-2.5-7B-Instruct, 1 epoch, ~210K example
exposures across 7 tasks (A/B/H/M/C/D/E). Final eval_loss 0.0078 on the
held-out 2% — looked excellent on paper.

Pulled the LoRA from HuggingFace, started vLLM, ran `bulk_collect.py` on the
10-puzzle smoke set (`splits/baseline_qwen_run.json` — the 10 puzzles base
Qwen could solve at baseline). Expected: ~100% pass@10 (these are the easy ones).

### What actually happened

| Run | pass@1 | pass@10 | Code quality |
|-----|--------|---------|--------------|
| Run 1 (broken eval) | 1.0% | 1/10 (10%) | Sophisticated 50-line solvers with bugs |

The model was writing complex code — bounding boxes, center-finding loops,
symmetry checks — but for the wrong abstraction. It treated trivial mirror
puzzles as if they needed geometric transformations. Looked like the
fine-tune had learned to over-engineer everything.

I started writing the failure analysis: "the LoRA learned Claude's complex
coding style but not when to apply which rule, expect mediocre pass@10 on
trivial puzzles..."

### The actual bug

The user pushed back: "Let's inspect manually." Found three format
mismatches in `bulk_collect.py`:

1. **Grid format:** `bulk_collect.py` joined cells with spaces (`"0 0 3 0 0"`).
   Training data used the **compact format** (`"00300"`). Different tokens,
   different look.

2. **No system message:** `bulk_collect.py` sent only `{"role": "user", ...}`.
   Training records all had `{"role": "system", "content": "D"}` to tag the
   task. Without it, the model couldn't tell what mode it should be in.

3. **Different prompt wording:** `bulk_collect.py` said "Solve this ARC-AGI
   puzzle. Identify the transformation rule..." vs training's
   "Write a Python `def solve(input_grid):` function that produces the
   correct output...".

None of these changes look big in isolation. The puzzle content was identical.
Same grids, same train pairs, same test input. But the *format wrapping* the
content was different from what the model trained on.

### What happened after the fix

Patched the three issues. Re-ran the same 10-puzzle smoke set with the same
model. Watched the first 20 attempts:

```
[  1/100] 0f63c0b9 run_02 -> CORRECT
[  2/100] 0f63c0b9 run_03 -> CORRECT
... (all 10 attempts of puzzle 1 correct)
[  9/100] 23581191 run_00 -> CORRECT
[ 10/100] 23581191 run_01 -> CORRECT
... (all 10 attempts of puzzle 2 correct)
```

**20/20 CORRECT after the fix. 1/20 CORRECT before.** Same model. Same
weights. Same puzzles. The only thing that changed was the prompt's surface
appearance: compact instead of spaced grids, system tag added, wording
matched.

### The lesson

The model's output distribution is *narrowly concentrated* on the format it
trained on. Move the input distribution even slightly off — three small
cosmetic changes — and the model falls off a cliff. Not just degraded
performance, but **fundamentally different behavior** (over-engineered
substitute-rule guesses instead of correct trivial solutions).

This matters for two related reasons:

**1. Prompt sensitivity is a property of the trained model.**

When we say "the model can solve X puzzles," we always mean "*given prompts
shaped exactly like the training distribution*". The same model with
the same weights produces fundamentally different code if the prompt looks
slightly different. Format isn't packaging around the content — it's part of
the content.

This means at inference time, the prompt template must match the training
template *byte-for-byte*. Off-by-one whitespace, wrong system tag, swapped
greeting — any of these silently degrades the model from "trained behavior"
to "untrained behavior."

**2. Substrate engineering is the load-bearing structure.**

The "substrate" (the encode/decode language, the compact grid format, the
single-letter task tags) isn't decoration. It's the deterministic perceptual
scaffolding that *makes the model's behavior conditional on which task it's
doing*. Without the system tag, the model can't tell A from D from E. Without
the compact format, the rows look like prose to the model instead of grid
structure. Without the matched user-message wording, the trained behavior
doesn't fire.

If we hadn't engineered the substrate carefully, the model would have
learned a single "do something to the grid" behavior that fires regardless
of intent. The substrate is what lets us train 7 distinct skills into one
LoRA *and* invoke them selectively at inference. Removing any one piece
collapses that selectivity.

### Practical takeaways

1. **At inference time, prompts must match training prompts byte-for-byte.**
   Whitespace, tags, wording. All of it. This includes:
   - System message exactly as trained (single letter D/E/C/A/B/H/M)
   - User-message phrasing exactly as trained
   - Grid format exactly as trained (compact, no spaces)
   - Chat template applied identically

2. **When eval looks suddenly bad, suspect the pipeline first.**
   A trained model rarely "just gets worse." Format/tag/template mismatches
   silently destroy performance. Inspect what bytes are actually going into
   the model before concluding anything about the model's capability.

3. **Substrate engineering is a real research contribution.**
   Compactness, task tags, deterministic encoding — these aren't ergonomics.
   They're the structural primitives that make multi-task fine-tuning
   *behave* as multi-task at inference. Without them you get one model that
   averages all behaviors instead of selecting between them.

4. **Cosmetic differences become semantic differences.**
   The model has no way to know that `0 0 3 0 0` and `00300` mean the same
   grid. To the model they're different sequences of tokens. The training
   distribution defines what looks "right." Inference must stay inside that
   distribution.

### What we don't know yet

This smoke-set result (10 trivial puzzles base Qwen already solves) only
confirms the model didn't regress on easy capability. The actual signal
comes from:

- The augmented set (D4+color-permuted variants the model never saw) — does
  it generalize?
- The 706-puzzle broad set — does pass@10 jump meaningfully above baseline
  1.4%?
- arc2_eval (sacred 120-puzzle held-out) — the real competition number.

Run those next, then we'll know if the substrate hypothesis actually
transfers to code generation or if it stays locked in the substrate tasks.

But that's a separate finding. The finding *today* is: format matters more
than I would have guessed before seeing 1/20 → 20/20 from cosmetic changes.

---
