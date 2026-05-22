# puzzles/ — canonical ARC corpus, compact JSON

Fresh mirror of the public ARC-AGI-1 and ARC-AGI-2 puzzle JSONs, re-saved
in a compact form so the file *is* the data: no wrapper indentation, no
spaces, no commas inside grids.

## Sources

| Label | Source | Repo |
|---|---|---|
| `A1T` | ARC-AGI-1 training (400 puzzles) | `fchollet/ARC-AGI`, `data/training/` |
| `A1E` | ARC-AGI-1 evaluation (400 puzzles) | `fchollet/ARC-AGI`, `data/evaluation/` |
| `A2T` | ARC-AGI-2 training (1000 puzzles) | `arcprize/ARC-AGI-2`, `data/training/` |
| `A2E` | ARC-AGI-2 evaluation (~120 puzzles) | `arcprize/ARC-AGI-2`, `data/evaluation/` |

## Filenames

`<puzzle_id>_<src>.json` — one file per puzzle per source. The same
8-char id can appear in multiple sources (ARC-AGI-2 includes revised
versions of many ARC-AGI-1 puzzles); we keep both as separate examples.

No dedupe. No S/D size suffix. No combined markers (`A1E+A2T_D` etc.).

## File format

Standard ARC schema, minified, with grids stored as newline-separated
digit strings instead of nested integer arrays:

```json
{"train":[{"input":"707\n707\n770","output":"707000707\n707000707\n770000770\n707000707\n707000707\n770000770\n707707000\n707707000\n770770000"}],"test":[{"input":"...","output":"..."}]}
```

Trade-offs vs the canonical array form:

- No spaces, no commas inside grids → ~30–50% smaller files
- Grids are visually grids when you open the file
- Needs a one-line helper to parse a grid string back into a list of
  lists of ints (`[[int(c) for c in row] for row in s.split("\n")]`)
- Still parses as standard JSON; wrapper commas (between train/test
  entries, between input/output keys) are required and preserved

## Per-pair size dispatch (no S/D at the puzzle level)

Some puzzles have mixed-shape pairs (pair 0 is same-size, pair 1 is
diff-size). Tagging a whole puzzle as S or D is not well-defined.

Instead, the substrate library dispatches at the **pair** level via
`substrate.encode_auto(inp, out)`:

- `inp.shape == out.shape` → per-cell substrate grid (`.` and digits)
- `inp.shape != out.shape` → diff-size text block (DIMS / ARITH /
  PALETTE)

The substrate type is a function of each pair, not the puzzle.

## What's next

The next step (the "sort the data" step the user mentioned) will read
these files and emit the SFT training records. This folder is the input,
not the training data.
