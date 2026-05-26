# ARC Research — insight dump (for future paper writing)

Raw, unpolished collection of ideas/observations from the Run 2 work. Not a
paper — a quarry to mine when writing one. Evidence is from our own runs unless
noted. Organized by theme; quotable framings at the end.

---

## 1. Core thesis — the grounding problem

LLMs face a **grounding problem**: they can generate plausible patterns/code/
explanations but cannot *certify their own correctness*. So the architecture
separates roles:

```
model proposes  →  substrate constrains  →  validator checks  →  diff localizes error  →  model repairs
```

- The **substrate** is not the reasoning engine; it narrows the search space
  (raw grid → structured transformation representation → rule → code/output).
- The **model** is not the truth engine.
- The **validator** (code execution against the real output) is the only authority.

This makes stochastic navigation happen inside a smaller, structured space rather
than over arbitrary code.

---

## 2. THE FREEHAND-RENDERING CEILING (headline empirical insight)

**Claim:** an autoregressive LLM cannot reliably *render* an exact 2D grid as a
token stream beyond a modest size, even when it has correctly inferred the rule.

**Mechanism (human vs machine):**
- A human *perceives* the grid holistically — sees the whole 2D field, grasps the
  transformation, places cells by spatial reasoning, and can re-check the whole.
- The LLM has **no 2D working memory**. It emits the grid one cell at a time,
  left-to-right / top-to-bottom, as 1D tokens. Two failure sources:
  1. **No global view** — it can't "step back and look at the whole grid."
  2. **Error compounding** — one inserted/omitted cell shifts everything after;
     alignment is lost. More cells → more slip chances → worse.

**Evidence:**
- Our probes: the model produces the *right structure* but drifts on exact
  placement — e.g. expected `.2..2..2..`, got `.2..2...2.` (stripe off by a
  column); thin/sparse edits dropped entirely; occasional stray cell.
- Operator report (hand-tested): **slipping begins past ~10×10 matrices.**
- decode (apply sparse changes to a copy) >> encode (draw the full diff grid):
  ~51% vs ~2% exact at 1 epoch — i.e. the *drawing* is the hard part, not the
  *understanding*.

**Consequence / the key move:** do NOT try to make freehand grid output
pixel-perfect — that fights a fundamental seq-model limitation. Instead **route
around it with code**: a 5-line rule renders any-size grid exactly via execution,
with no per-cell counting. Freehand exactness is a non-goal; rule *understanding*
is the goal.

---

## 3. Architecture: substrate scaffold + code as truth + repair

- **Substrate** (the "T"): a structured transformation representation. Two
  flavors dispatched per pair:
  - same-size → **pixel T** (per-cell, lossless: `.`=keep, digit=new color)
  - diff-size → **aggregate facts** (SIZE/BG/PALETTE/ROWS/COLS/BBOX; lossy, no
    decoder)
  - Role: a *reasoning scaffold* that forces the model to commit to structure
    (e.g. output shape) before producing an answer.
- **Code** (`def solve(input_grid)`): the actual solve mechanism. Expresses the
  rule abstractly; execution yields pixel-perfect output regardless of grid size.
  This is what sidesteps the rendering ceiling.
- **Repair** (validator feedback → corrected code): "code feedback fixes the
  rest." Near-miss code (off-by-one in a loop, etc.) + a diff map of which cells
  differ → the model fixes the *code*, not the grid.

**Reframing of "95% → code fixes the rest":** code does NOT patch a 95%-correct
grid. It (a) replaces freehand drawing with abstract rule-expression (drift
gone), and (b) repairs near-miss *code* from validator diffs. The substrate's
cell-accuracy is a **proxy for whether the model perceived the rule** — high
enough understanding ⇒ it can write/repair correct code ⇒ 100% via execution.

---

## 4. Observed failure taxonomy (Phase-1 substrate, 1-epoch)

Three independent causes — important to separate, because they have different fixes:

1. **Positional drift** — `.2..2..2..` → `.2..2...2.`. Spatial alignment /
   autoregressive rendering. Fix: partly more training; fundamentally → code.
2. **Dropped sparse/thin edits** — `...2...\n...2...\n.33.` → `.......\n.......\n.33.`
   (keeps obvious `33`, drops the thin vertical `2`). Weak *changed-cell recall*.
   Fix: oversample sparse/thin-edit examples (single cell, lines, endpoints).
3. **`.` vs `0` confusion** — emits `0` where `.` expected. **NOT a symbol-
   recognition problem** (they're distinct tokens). It's a *reasoning/tracking*
   problem: a black output cell is `.` if it was already black (unchanged) or `0`
   if it changed to black — the model must compare input vs output at that exact
   position. Renaming `.`→`K` does NOT fix the reasoning (would just confuse
   `K` vs `0`). The real lever is contrast data that teaches "already-0 keep" vs
   "changed-to-0". (Speculative pro-`K` argument: pretraining treats `.` as
   low-information filler, so a content letter might get more deliberate
   emission — unproven, secondary.)

4. **Counting/magnitude slips in the diff-size facts block** (Run 2 stage 2,
   diff_lit, 3-epoch, held-out probe). On the aggregate facts-T (SIZE/BG/PALETTE/
   ROWS/COLS/BBOX), held-out **cell-accuracy 95.7% but exact-match only 21%**.
   Pulling the per-failure diffs: **every miss is a counting/arithmetic slip, none
   structural.** The model nails SIZE, BG, field structure, dominant colors, and
   mostly the ×/÷/Δ relation tags — but miscounts magnitudes (e.g. a color present
   165× → it emits 169; a per-row non-bg count 8 → 9), and a wrong count flips the
   derived relation tag. This is the **facts-block analogue of positional drift**:
   the LLM grasps the transformation structure but cannot *count* exactly,
   especially on large/dense grids (failures cluster on the biggest puzzles).
   Notably the model's emitted facts can be internally inconsistent (count + tag
   disagree), confirming it pattern-completes the format rather than computing.
   **Why it's benign here:** facts-T is a lossy reasoning *scaffold*, not the
   answer — code execution is the Phase-2 truth, so an off-by-4 count doesn't
   break the solve. **Fix is NOT more SFT** (can't teach an LLM to count 165 cells
   exactly, same ceiling as freehand rendering); the lever is to design the
   substrate around what the model gets right (relations/structure) and
   de-emphasize raw exact counts. General lesson: **a substrate that asks the
   model to reproduce exact counts is asking for its single weakest skill** —
   prefer relational/structural facts the model can produce reliably.

---

## 5. Measurement insights (these matter for any ARC SFT paper)

- **eval_loss ≠ generalization.** A 2% val-carve sliced *after augmentation* can
  contain sibling augmentations of trained puzzles → optimistically low loss
  (we saw ~0.0078 / ppl ~1.008 "brilliant" numbers that meant *fit the training
  distribution*, not *generalizes*). The honest metric is a **held-out probe**
  (whole puzzles never trained, no augmentation). Don't be fooled by shiny
  in-distribution loss.
- **Exact-match is too blunt** for grid outputs — all-or-nothing; one wrong cell
  in a 10×10 scores 0 even at 99% cells correct. Report instead:
  `cell_accuracy`, `changed_cell_recall` (catches dropped sparse edits — a 90%
  cell-acc example was only 50% changed-recall), `changed_cell_precision`,
  `zero_dot_confusion`.
- **Split metrics by grid size (≤10×10 vs >10×10).** Disambiguates the two very
  different diagnoses: *small high / large low* = understanding is fine, only
  rendering drifts (→ rely on code, move on); *small also low* = genuine
  understanding gap (→ more training/data). This operationalizes the rendering-
  ceiling insight into the gate.
- **Proposed gate:** Phase-1 success = **small-grid cell-accuracy / understanding
  metrics**, NOT large-grid freehand exact-match. The real headline is the
  Phase-2 *code* solve rate on held-out (and the frozen-eval set).

---

## 6. Training dynamics (subtle, worth a methods paragraph)

- **`sample_packing` collapses the optimizer step count.** Packing ~14 short
  records into each 8192-token sequence turned "1 epoch" into only ~37 steps
  (vs ~422 in a less-packed run). Same *data seen*, far fewer *weight updates* →
  under-convergence. `steps_per_epoch = packed_sequences / effective_batch`.
- Distinguish **data exposure (epochs)** from **weight updates (steps)**: a model
  can see all data once yet be badly under-trained if packing made that one pass
  ~37 updates. Levers to add updates at ~fixed wall-clock: lower
  `gradient_accumulation_steps` (smaller effective batch, more steps); or more
  epochs (more wall-clock).
- **Attention backend dominated by model size, not attention, at these scales:**
  flash-attn vs eager was ~30% on a 7B LoRA at 8192 (the 7B fwd+bwd +
  gradient-checkpointing dominate), but eager+packing was *also numerically
  wrong* (bad packed-mask handling inflated baseline loss 3.5 vs the correct
  0.58). Lesson: `sample_packing` really wants flash-attn (varlen), both for
  speed and correctness.

---

## 7. Curriculum design notes

- **Per-pair deterministic substrate dispatch** (same→pixel, diff→facts) means
  the training target mapping is never ambiguous; the model can't be trained on
  the "wrong" representation.
- **Teach alphabets in isolation, reunite at the end:** same_lit → diff_lit →
  same_rule → diff_rule → mixed. Pure separation risks catastrophic forgetting
  in the middle stages; mitigated by (a) probes between stages, (b) a small
  same-alphabet literacy carry in rule stages, (c) reconsolidation in `mixed`.
- **Hold-out discipline:** whole-puzzle held-outs (probe / api_eval / frozen
  final) by augmentation parent — every augmented variant of a held-out puzzle
  is held out, verifiable by a one-line manifest grep.

---

## 8. Open questions / hypotheses to test

- Does more training (300–500 steps vs 37) lift held-out **cell-accuracy** and
  drop **zero_dot_confusion**? (Tests under-training vs ceiling.)
- Does **grid-size-split** show small-grid understanding is already high while
  large-grid is rendering-bound? (If yes, strong support for "gate on
  understanding, solve with code.")
- Does **sparse-edit / contrast data** specifically lift changed-cell recall and
  the `.`/`0` distinction, beyond what more epochs gives?
- Is there a freehand size threshold (e.g. ~10×10) above which *no* amount of SFT
  yields reliable exact rendering — quantify it.
- Does substrate scaffolding measurably improve Phase-2 **code** correctness vs
  raw-grid → code (the substrate's real payoff)?
- TTT (test-time training) on top of the substrate vocabulary — later.

---

## 9. Quotable framings (for the paper narrative)

- "The model is not failing the language; it is failing exact spatial placement."
- "Humans see and immediately know; the model must express the grid token by
  token, and each token can be off a little — so cells scatter even when the
  underlying rule is coherent."
- "Don't make the LLM hand-draw the answer. Make it *describe the rule*, and let
  code draw the answer."
- "eval_loss measures how well the model fits its own training distribution.
  The held-out probe measures whether it learned anything. They are not the
  same number, and the gap is the whole story."
- "Exact-match is a cliff; cell-accuracy is a slope. On a cliff you can't see
  whether you're climbing."

---

## Provenance
Run 2 Phase 1, 2026-05-24. See `research/diary/2026-05-24_run2_phase1_undertraining.md`
for the operational session log, `Fine Tune Run 2/SFT_Strategy.md` for the full
strategy, and `Fine Tune Run 2/run_probe.py` for the metric implementations.
