# Phase 1 Substrate Training — Spec (v2)

**Status:** Pipeline shipped. Substrate library, data generator, and locked split manifest are committed to `main`. Fine-tuning step not yet run.

**Scope:** Phase 1 only — teaching the model the substrate representation as a curriculum step. Phase 2 (substrate → code) is a separate spec.

**Hard precondition:** Same-size grids only (`input.shape == output.shape` across every pair). Different-size puzzles need a different representation and are deferred to a later phase.

---

## Empirical baseline (motivating the design)

We ran raw Qwen-2.5-7B-Instruct single-shot on 10 same-size ARC-AGI-2 training puzzles, 10 attempts per puzzle, temperature 0.7, no scaffolding (see `bulk_collect.py`).

**Result: 0/99 correct.** ~89% of runs produced executable but wrong code; ~11% crashed.

**Failure-mode analysis (manual read of 89 wrong-code runs):**
- When Qwen articulated a rule in prose, the Python faithfully implemented the (wrong) rule.
- Failures are *wrong rule identified*, not *correct rule + buggy code*.
- Example: puzzle `f3e62deb`'s rule is "move shape to top of grid." Qwen wrote clean code for "find first non-zero row, dedupe consecutive duplicates." Two completely different operations. Code is fine; perception is wrong.
- Cell-diff magnitudes correlate with rule-distance: when Qwen named a rule in the right "neighborhood" (lines/positions/shapes), diffs were 12–36 cells; when it skipped articulation, diffs were 90–165 cells.

**Diagnosis: bottleneck is rule perception, not code generation.** The classic "wrong code → right code" corrector framing has limited leverage because the wrong code is *structurally correct code for a wrong rule*.

---

## Design: substrate as hierarchy of invariants and variants

The substrate is a per-cell symbolic grid, same dimensions as the input/output. It uses three tiers:

| Tier | Symbol | Meaning |
|---|---|---|
| **Highest invariant** | `.` | background unchanged (bg in input, bg in output) |
| **Next invariant** | `=` | non-bg cell preserved (input[r,c] == output[r,c]) |
| **Variants** | `0`–`9` | output is this color (different from input) |

**Background convention:** `bg = most common color in input grid`. Smallest color value wins ties (deterministic).

**Lossless property:** given `(input, substrate)`, the `output` is uniquely determined. Reconstruction rule per cell:
- `.` → `bg`
- `=` → `input[r,c]`
- digit → that digit

**Operation type is inferred, not stated.** A digit in the substrate alongside `input[r,c] == bg` means "activation." A digit alongside `input[r,c] != bg` means "transform." The model triangulates from `(input, substrate)`; no separate operation alphabet needed.

**Why this beats earlier proposals we considered:**
- Versus pure operation symbols (`+ = - . ~`): the 5-symbol alphabet can't represent multi-color transforms where the same operation produces different colors at different positions (e.g., puzzle 15663ba9 where one transform produces both `4` and `2` based on geometric context). The digit-as-variant approach handles this naturally.
- Versus richer notation with tagged operations (`~a`, `~b`) or embedded colors (`~4`, `~2`): adds notational overhead without gaining anything the (input, substrate) pair doesn't already encode.
- Versus a per-puzzle legend specifying activation/transform colors: collapses to "state the rule in the legend," which defeats the purpose — the model should *learn* the rule from data, not be told it.

---

## Worked examples

### Single-variant transform — puzzle `14b8e18c`

Rule: square shapes (hollow or solid) get color-2 markers at the orthogonally-adjacent cells outside their corners.

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

Three symbols visible: `.`, `=`, `2`. The variant tier has one value (`2`). Sparse signal: ~70% of cells are `.`.

### Multi-variant transform — puzzle `15663ba9`

Rule: closed irregular polygons get their corners recolored — convex corners → 4, concave corners → 2.

**Pair 1 substrate** (input shapes are 3s):
```
. . . . . . . . . . . . .
. . . . 4 = = 4 . . . . .
. . 4 = 2 . . = . . . . .
. . = . . . . = . . . . .
. . = . . 2 = 4 . . . . .
. . 4 = = 4 . . . 4 = 4 .
. . . . . . . . 4 2 . = .
. . . . . . . . = . . = .
. . . . 4 = = = 2 . . = .
. . . . = . . . . . . = .
. . . . = . . . 2 = = 4 .
. . . . 4 = = = 4 . . . .
. . . . . . . . . . . . .
```

Two distinct variants (`4`, `2`) appear at structurally distinct positions. The substrate doesn't pre-classify them as "convex marker" vs "concave marker" — that's what the model learns from data. But the *positions* of each are visible without confusion.

### Color-invariance across pairs

For 15663ba9, training pair 0 uses 8s, pair 1 uses 3s, pair 2 uses 1s. **The substrates are structurally identical** — same alphabet (`.`, `=`, `4`, `2`), same motif (closed loops of `=` with `4` at convex corners and `2` at concave corners). The original shape color is *erased*. The model can learn the rule once and apply it regardless of palette.

This is the key property color-permutation augmentation exploits.

---

## Encode / decode functions

The full library is `substrate.py` (50 lines, stdlib only). Core functions:

```python
def encode(inp, out, bg):
    return [['.' if (i==bg and o==bg) else '=' if i==o else str(o)
             for i, o in zip(ir, oR)]
            for ir, oR in zip(inp, out)]

def decode(inp, substrate, bg):
    return [[bg if s=='.' else i if s=='=' else int(s)
             for i, s in zip(ir, sr)]
            for ir, sr in zip(inp, substrate)]
```

**Roundtrip property:** `decode(input, encode(input, output, bg), bg) == output` for every same-size pair. Verified on a random sample of 5 pairs across diverse puzzles (5/5 match).

---

## Three-task curriculum

**Phase 1a:** `(input, output) → pixel substrate`. The model learns to compute `encode()`. Same-size puzzles only.
**Phase 1b:** `(input, pixel substrate) → output`. The model learns to compute `decode()`. Same-size puzzles only.
**Task A2:** `grid → hierarchy substrate`. The model learns to decompose any single grid by color frequency. All puzzles regardless of size.

All three are *deterministic functions* — there's a single correct answer for every input. Loss converges fast because the model isn't learning a fuzzy hypothesis, it's learning a per-cell rule.

Mixed-batch training. No sequential phases.

### Task A2 — hierarchy substrate (covers different-size puzzles)

The pixel substrate (Phase 1a/1b) requires `input.shape == output.shape` because it's a per-cell comparison. That excludes ~33% of ARC puzzles (588 of 1,781 examples). Task A2 closes that gap.

**Alphabet:**

| Symbol | Meaning |
|---|---|
| `.` | most common color in the grid (background by frequency) |
| `#` | second most common color (structure by frequency) |
| `S` | all other colors (content / signal) |

**Computation:** count color frequencies in a single grid; sort by count descending (ties broken by lower color value); map the top color → `.`, the next → `#`, everything else → `S`. Lossy by design — `S` doesn't say *which* content color, so the substrate can't be decoded back. That's intentional: hierarchy teaches perception (separate signal from filler), not reconstruction. No Task B2.

**Skip rules:** grids with fewer than 2 unique colors (no hierarchy possible) and grids smaller than 3×3 (insufficient structure).

**Augmentation:** D4 only (8 rotations/flips). Color permutation does not apply — the hierarchy is frequency-based and invariant under color relabeling, so permuting colors produces an identical substrate.

**Worked example** (same grid as user's original spec, but following the mechanical rule):

```
GRID (color 1: 24 cells, color 6: 19 cells, color 4: 6 cells):
1 1 1 1 1 1 1
1 6 6 6 6 6 1
1 6 4 6 4 6 1
1 6 4 4 4 6 1
1 6 6 4 6 6 1
1 6 6 6 6 6 1
1 1 1 1 1 1 1

HIERARCHY SUBSTRATE (1 -> ., 6 -> #, 4 -> S):
. . . . . . .
. # # # # # .
. # S # S # .
. # S S S # .
. # # S # # .
. # # # # # .
. . . . . . .
```

**Important note on the rule:** the mechanical "most common color" rule may not match the human-intuitive notion of "background." In the example above, the outer 1-border has more cells than the inner 6-layer, so 1 wins the `.` tier even though a human might call the border "the structure." That's fine — the model learns a *consistent deterministic function*, not a semantic heuristic. Whether this decomposition transfers usefully to Phase 2 is empirical.

---

## Data pipeline (built and shipped)

| Artifact | Purpose |
|---|---|
| `data/arc1_train/` (400), `arc1_eval/` (400), `arc2_train/` (1000) | All 1,800 puzzle JSONs committed to repo |
| `substrate.py` | encode/decode/is_same_size/background_of library |
| `gen_phase1_data.py` | reads universe, applies augmentations, emits JSONL |
| `splits/training_universe.json` | locked manifest: 696 unique puzzle IDs + train/dev split |

### Numbers

- ARC-AGI-1 train (400) ∪ ARC-AGI-1 eval (400) ∪ ARC-AGI-2 train (1,000) = **1,800 puzzle files** but only **1,033 unique IDs** (ARC-AGI-2 includes ~767 revised versions of ARC-AGI-1 puzzles with the same IDs but different content; treated as separate examples).
- Locked baseline (10 puzzle IDs, all in arc2_train; also appearing in arc1_train/eval where applicable) excluded across all sources.
- Universe after locked exclusion: **1,781 puzzle examples / 1,023 unique IDs**.
  - Same-size subset: **1,193 examples** (used for Phase 1a + 1b)
  - Different-size subset: **588 examples** (used only for Task A2 hierarchy)
- Train/dev split (by unique puzzle_id, prevents arc1/arc2 cross-variant leakage): **923 train IDs (1,606 examples) / 100 dev IDs (175 examples)**.

### Default output (D4 augmentation only, no color permutations)

| Task | Records |
|---|---|
| `phase1a` (pixel encode, same-size) | 39,800 |
| `phase1b` (pixel decode, same-size) | 39,800 |
| `phase1a_hierarchy` (any grid) | 119,072 |
| **Train total** | **180,736** |
| Dev total | 17,936 |

Generation time: ~30s on a laptop.

### With color permutations

`python3 gen_phase1_data.py --color-perms 5` produces ~480K records (10× larger). Augmentation is safe: substrate is rotation- and color-permutation-equivariant by construction.

### Record format

```json
{
  "task": "phase1a",
  "puzzle_id": "00d62c1b",
  "aug": "d4_0",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "INPUT:\n0 0 0 0 0 0\n...\n\nOUTPUT:\n0 0 0 0 0 0\n..."},
    {"role": "assistant", "content": ". . . . . .\n. . = . . .\n. = 4 = . .\n. . = 4 = .\n. . . = . .\n. . . . . ."}
  ]
}
```

---

## Training setup (not yet executed)

- Model: Qwen-2.5-7B-Instruct.
- Method: LoRA, r=16, all projection layers, 4-bit quantization.
- Hardware: free Colab T4.
- Estimated training time at default data size (~67K records): ~1 hour single epoch.
- Estimated cost: $0 (free Colab) + $0 (data generation is local Python).

---

## Open questions (reduced from v1)

**Q1. Does Phase 1 alone transfer to better code generation in Phase 2?** This is the central empirical question. Hypothesis: yes — the model that has internalized substrate semantics will write better code than one trained directly on (puzzle → code) pairs. Test: after Phase 1 training, re-run `bulk_collect.py` on the locked baseline_10 puzzles. If solve rate moves from 0%, the substrate is doing useful work. If it stays at 0%, we need Phase 2 to test the full pipeline.

**Q2. Should we add natural-language rule annotations as a third channel?** A sentence per puzzle ("convex polygon corners get color 4, concave get color 2"), generated in batch by Claude/GPT (~$5 for the full universe). This couples substrate (effect) with rule text (precondition + effect). Open: would it help, or is the substrate sufficient?

**Q3. Background detection edge cases.** Current rule: `bg = most_common_color(input)`, smallest value on ties. Works for the vast majority of puzzles where the background is visually obvious. Edge cases (puzzles with two equally-common colors representing "two backgrounds") may need a smarter heuristic. Open: how often does this fail in practice?

**Q4. Augmentation scale.** Default is D4 only (×8). Color permutations multiply by another ~10×. Is the larger dataset (~480K records) better for a 7B LoRA, or does it overfit to surface patterns? Empirical question — start with D4 and add color perms if Phase 1a/1b accuracy plateaus below target.

---

## Resolved decisions (do not revisit)

- **Pixel substrate alphabet:** `.`, `=`, `0`–`9` only. Three tiers (invariant / preserved / variant). No `+`, `-`, `~`. Decided after testing 14b8e18c (single-variant) and 15663ba9 (multi-variant).
- **Pixel substrate is same-size only:** locked precondition for Phase 1a/1b.
- **Hierarchy substrate covers all sizes:** Task A2 uses `.`, `#`, `S` decomposition by color frequency. Applies to every grid regardless of input/output dimensions. Mechanical rule, no semantic heuristic.
- **Train/dev split:** by unique puzzle_id, seed=42, applied to the full universe (all sizes). Cross-variant leakage between arc1/arc2 versions of the same ID is prevented.
- **Locked eval:** `splits/baseline_10.json` (10 puzzle IDs) is never used in training, even via the arc1 variants of the same IDs.
- **Data generation:** pure Python, no API, fully reproducible. Library at `substrate.py`, generator at `gen_phase1_data.py`.
- **Tagged for ablation:** every record has a `task` field (`phase1a` / `phase1b` / `phase1a_hierarchy`) so the trainer can include/exclude task types via filtering. Enables clean ablation between "Phase 1 alone" and "Phase 1 + A2."

---

## What we want from external review

- Sanity check on the substrate alphabet and lossless property (worked examples included above).
- Critique of the curriculum (Phase 1a + 1b mixed batch).
- Direct opinion on Q1 (does Phase 1 alone improve downstream code?) and Q2 (rule annotations as third channel — yes or no).
- Pointers to any prior work that has tried similar intermediate representations on ARC (DSL programs, sketches, diff representations) and what worked/failed.
- Any failure mode in the spec we've missed.
