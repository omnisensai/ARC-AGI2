# Phase 1 Substrate Training — Spec for External Review

**Context.** We're fine-tuning Qwen-2.5-7B-Instruct to solve ARC-AGI puzzles by generating Python `solve()` functions. This spec covers Phase 1 of the training plan: teaching the model to perceive transformations explicitly via an intermediate "substrate" representation. We're soliciting external review before writing the data generator.

---

## Empirical baseline (motivating the design)

We ran raw Qwen-2.5-7B single-shot on 10 ARC-AGI-2 training puzzles (same-size only — input.shape == output.shape across all pairs), 10 attempts per puzzle, temperature 0.7, no scaffolding.

**Result: 0/99 correct.** ~89% of runs produced executable but wrong code; ~11% crashed.

**Failure-mode analysis (manual read of 89 wrong-code runs):**
- When Qwen articulated a rule in prose, the code faithfully implemented the (wrong) rule.
- Most failures are *wrong rule identified*, not *correct rule + buggy code*.
- Example: puzzle `f3e62deb`'s rule is "move shape to top of grid." Qwen wrote correct, well-commented code for "find first non-zero row, dedupe consecutive duplicates." Two completely different operations. Code is fine; perception is wrong.
- Cell-diff magnitudes correlate with rule-distance: when Qwen named a rule in the right "neighborhood" (lines/positions/shapes), diffs were 12–36 cells; when it skipped articulation, diffs were 90–165 cells.

**Diagnosis: bottleneck is rule perception, not code generation.** The classic "wrong code → right code" corrector framing has limited leverage because the wrong code is *structurally correct code for a wrong rule*.

---

## Proposed solution: substrate as training signal

Train the model to first perceive *what changed* between input and output via an explicit symbolic "substrate" representation. The substrate is an intermediate between (input, output) and (rule, code).

**Two-phase curriculum:**
- **Phase 1a:** `(input, output) → substrate` — teach the model to extract the change pattern.
- **Phase 1b:** `(input, substrate) → output` — teach the model to apply changes given a substrate (validates that the substrate carries enough information to reconstruct outputs; also reinforces the change semantics).
- **Phase 2 (later, separate spec):** `(input, substrate) → code` and/or `(input, pairs) → code`. Out of scope for this review.

---

## Substrate specification

**Per-cell alphabet:**

| Symbol | Meaning |
|---|---|
| `.` | background → background (bg = most common color in input) |
| `=` | non-bg cell preserved (output color == input color) |
| `<digit>` | bg → this non-bg color (was empty, now contains this color, 0–9) |
| `~<digit>` | non-bg → different non-bg (one color transformed into another) |
| `-` | non-bg → bg (cell emptied) |

**Lossless property:** given `input` and `substrate`, the `output` is uniquely determined. Reconstruction rule:
- `.` → bg color from input
- `=` → input[r,c]
- `<digit>` → that digit
- `~<digit>` → that digit
- `-` → bg color

**Background convention:** `bg = most_common_color(input_grid)`. Computed deterministically per puzzle. If there's a tie, take the smallest color value (deterministic).

---

## Worked example — puzzle `14b8e18c`

Rule (from inspection of 3 training pairs + 1 test pair): **square shapes — hollow or solid — get color-2 markers at the orthogonally-adjacent cells outside their corners. Non-square shapes get nothing.**

**Pair 0 input** (bg = 7):
```
7 7 7 7 7 7 7 7 7 7
7 6 6 6 6 7 7 7 6 7
7 6 7 7 6 7 7 6 7 7
7 6 7 7 6 7 7 7 7 7
7 6 6 6 6 7 7 7 7 7
7 7 7 7 7 7 7 7 7 7
7 7 7 7 7 7 7 7 7 7
7 7 6 7 7 6 6 6 6 7
7 6 7 7 7 6 6 6 6 7
7 7 7 7 7 7 7 7 7 7
```

**Pair 0 output:**
```
7 2 7 7 2 7 7 7 7 7
2 6 6 6 6 2 7 7 6 7
7 6 7 7 6 7 7 6 7 7
7 6 7 7 6 7 7 7 7 7
2 6 6 6 6 2 7 7 7 7
7 2 7 7 2 7 7 7 7 7
7 7 7 7 7 7 7 7 7 7
7 7 6 7 7 6 6 6 6 7
7 6 7 7 7 6 6 6 6 7
7 7 7 7 7 7 7 7 7 7
```

**Pair 0 substrate:**
```
. 2 . . 2 . . . . .
2 = = = = 2 . . = .
. = . . = . . = . .
. = . . = . . . . .
2 = = = = 2 . . . .
. 2 . . 2 . . . . .
. . . . . . . . . .
. . = . . = = = = .
. = . . . = = = = .
. . . . . . . . . .
```

**Observations on this substrate:**
- ~70% of cells are `.` (high "negative space"); signal is concentrated in <30% of positions.
- Only 3 symbols used (`.`, `=`, `2`); most puzzles use 2–4 symbols. Sparse alphabet per puzzle.
- The substrate explicitly shows the *absence* of change in rows 7–8 (the non-square 2×4 solid block remains unmarked). Negative evidence built in.
- Visually parseable as "halo ring rows" (0, 5), "halo-flanked shape rows" (1, 4), "shape interior" (2, 3), "irregular shape without halo" (7, 8).

---

## Training data shape

**Phase 1a JSONL example:**
```json
{"messages": [
  {"role": "system", "content": "You produce ARC transformation substrates. Given an input grid and an output grid, write the substrate that describes the per-cell transformation using symbols: '.' (bg unchanged), '=' (non-bg preserved), digit (bg→this color), '~' followed by digit (color transformed), '-' (cell emptied)."},
  {"role": "user", "content": "INPUT:\n7 7 7 ...\nOUTPUT:\n7 2 7 ..."},
  {"role": "assistant", "content": ". 2 . . 2 . . . . .\n2 = = = = 2 . . = .\n..."}
]}
```

**Phase 1b JSONL example:**
```json
{"messages": [
  {"role": "system", "content": "You apply ARC transformation substrates. Given an input grid and a substrate, produce the output grid. Substrate symbols: '.' (output equals bg), '=' (output equals input), digit (output is this color), '~' followed by digit (output is this color), '-' (output equals bg)."},
  {"role": "user", "content": "INPUT:\n7 7 7 ...\nSUBSTRATE:\n. 2 . . 2 . . . . .\n..."},
  {"role": "assistant", "content": "7 2 7 ..."}
]}
```

**Data sources:**

| Source | Puzzles |
|---|---|
| ARC-AGI-1 training (`fchollet/ARC-AGI`) | 400 |
| ARC-AGI-1 evaluation (public, fair to train on) | 400 |
| ARC-AGI-2 training (`arcprize/ARC-AGI-2`) | 1,000 |
| **Total trainable universe** | **1,800** |
| Excluded: 10 locked eval puzzles + 120 ARC-AGI-2 eval | held out for benchmarking |

**Pairs per puzzle:** ~3 train + 1 test = ~4. Total raw: ~7,200 (input, output) pairs.

**Augmentation (safe for Phase 1 — substrate is rotation-equivariant and color-permutation-equivariant):**
- D4 group (4 rotations × 2 flips): ×8
- Color permutations (random permutations of the 10 colors): ×10
- **Total augmented dataset: ~575,000 examples.**

Each (input, output) pair generates one example for Phase 1a and one for Phase 1b → ~1.15M training examples total.

---

## Mix and training setup

- Joint training, not sequential. Mixed batch: 50% Phase 1a, 50% Phase 1b.
- LoRA fine-tuning on Qwen-2.5-7B-Instruct, r=16, target all projection layers.
- 4-bit quantization for free Colab T4.
- ~1 epoch over 1M examples ≈ 8 hours on T4.

---

## Open questions for review

**1. Lossiness of the substrate vs. usefulness.** The substrate is lossless w.r.t. output reconstruction. But it abstracts away the *rule* (why changes happen). Is this a good intermediate representation, or are we training a step that has no path to the actual goal (rule identification)?

**2. Is Phase 1b worth training?** Phase 1b is `(input, substrate) → output`. Since the substrate is lossless, this is a fully deterministic task. Does it teach the model anything Phase 1a doesn't, or is it just memorizing a substitution rule?

**3. Should we add rule annotations as a third channel?** Natural-language rule sentences ("squares get color-2 corner markers") generated by Claude/GPT in batch (~$5 for 1,800 puzzles). This couples substrate (effect) with rule text (precondition + effect). Without it, Phase 1 only teaches "what changed," not "why."

**4. Substrate symbol choices.** We chose `. = digit ~digit -`. Alternatives considered: collapsing `~digit` into `digit` (lose color-transform distinction), using human-readable words instead of symbols (more tokens, but clearer). Are these the right tradeoffs?

**5. Background detection.** `bg = most_common_color(input)` is deterministic but can be wrong for puzzles where background is conceptually a non-majority color. Worth a more sophisticated heuristic?

**6. Augmentation scale.** ×80 augmentation (D4 × 10 color perms) on ~7,200 raw pairs = 575K examples. Is this too much for a 7B model to absorb without overfitting to surface patterns? Should we keep augmentation lighter (e.g., ×8 D4 only, no color perms)?

**7. Will any of this actually help?** Our empirical baseline is 0/99. The hypothesis is that substrate training will improve rule perception and lift the solve rate when we go to Phase 2 (code generation). But it's a hypothesis — we have no direct evidence that Phase 1 substrate training transfers to better code. We plan to measure by training Phase 1 only, then re-running raw `bulk_collect.py` on the locked 10 eval puzzles to see if solve rate moves from 0. Is this a valid signal, or should we go straight to Phase 1 + Phase 2 to test the full pipeline?

---

## What's NOT up for review (locked decisions)

- Model choice: Qwen-2.5-7B-Instruct (fits on free Colab, OpenRouter-callable, base-instruct is fine).
- Eval set: 10 locked ARC-AGI-2 same-size puzzles, never touched in training.
- Single-task fine-tune scope: no multi-task with general code/chat data.

---

## What we want from review

- Sanity check on the substrate alphabet and lossless property.
- Critique of the curriculum (Phase 1a + 1b mixed batch).
- Direct answer to the seven open questions, especially Q1, Q3, and Q7.
- Pointers to any prior work that has tried similar intermediate representations on ARC (DSL programs, sketches, diff representations) and what worked/failed.
- Any failure mode in the spec we've missed.
