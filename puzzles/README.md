# puzzles/

Combined ARC-AGI corpus, **deduplicated** to one file per unique
puzzle id, in a compact comma-free text format aligned with
`substrate.format_grid`.

## Counts

| Provenance | Same-size (S) | Different-size (D) | Total |
| --- | ---: | ---: | ---: |
| `A1T`        |   7 |   2 |     9 |
| `A1E`        |  15 |   3 |    18 |
| `A2T`        | 174 |  59 |   233 |
| `A2E`        |  77 |  37 |   114 |
| `A1T+A2T`    | 255 | 136 |   391 |
| `A1E+A2T`    | 251 | 125 |   376 |
| `A1E+A2E`    |   4 |   2 |     6 |
| **Total**    | **783** | **364** | **1,147** |

Source totals before dedup: 1,920 files (ARC1 train 400, ARC1 eval 400,
ARC2 train 1,000, ARC2 eval 120). 773 ids appeared in both ARC1 and
ARC2 — for 766 of them the train pairs are identical (only reordered),
1 has slightly different train pairs, 0 have different test pairs. We
keep one record per id, preferring the ARC2 version when both exist.

## Filename grammar

```
<puzzle_id>_<provenance>_<size>.txt
```

### `puzzle_id`
8-char hex id, as used upstream (e.g. `007bbfb7`).

### `provenance` — which corpora hold this id
- `A1T` — only ARC1 training
- `A1E` — only ARC1 evaluation
- `A2T` — only ARC2 training
- `A2E` — only ARC2 evaluation
- `A1T+A2T` — both ARC1 train and ARC2 train
- `A1E+A2T` — ARC1 evaluation, reassigned to ARC2 training (largest overlap)
- `A1E+A2E` — evaluation in both
- (`A` = ARC, `1`/`2` = corpus version, `T` = **t**raining, `E` = **e**valuation)

### `size` — input/output shape relation
- `S` — **same-size**: every train and test pair has `input.shape == output.shape`. Substrate encoder works 1:1 on every pair.
- `D` — **different-size**: at least one pair changes dimensions. Needs an output-shape-prediction step before per-cell rendering.

Examples:
- `00576224_A1E+A2T_S.txt` — id `00576224`, was ARC1 eval and is now ARC2 train, same-size pairs.
- `2b83f449_A2T_D.txt` — only in ARC2 train, has shape-changing pairs.

## File format

Plain text, one digit per cell, newline between rows. Short marker
lines separate sections. No JSON brackets, no commas, no whitespace
beyond newlines.

```
T1I            ← train pair 1, input grid
86
64
T1O            ← train pair 1, output grid
868686
646464
686868
464646
868686
646464
T2I            ← train pair 2, input
...
T2O            ← train pair 2, output
...
E1I            ← test pair 1, input
...
E1O            ← test pair 1, output (omitted if upstream hides it)
...
```

Marker grammar (regex): `^[TE]\d+[IO]$`. Anything else is a grid row.

The 11 ARC1 evaluation files that carry a redundant upstream `"name"`
field (just a copy of the puzzle id) are not preserved — the id is
already in the filename.

## Why this format

- One char per cell halves token count vs space-separated → ~20-30%
  more sampling budget at test time on a fixed context window.
- No commas → no extra tokens spent on separators the model already
  infers from the digit grid.
- Flat folder + suffix tagging → trivial `glob('puzzles/*_S.txt')` for
  all substrate-compatible puzzles, `glob('puzzles/*_A2*_*.txt')` for
  the full ARC2 corpus, etc.

## Round-tripping back to upstream JSON

```python
import re

def parse_puzzle(text):
    sections = {}
    cur = None; buf = []
    for line in text.rstrip().split('\n'):
        if re.match(r'^[TE]\d+[IO]$', line):
            if cur is not None:
                sections[cur] = [[int(c) for c in row] for row in buf]
            cur = line; buf = []
        else:
            buf.append(line)
    if cur is not None:
        sections[cur] = [[int(c) for c in row] for row in buf]

    train, test = [], []
    for i in range(1, 1000):
        if f'T{i}I' not in sections:
            break
        train.append({'input': sections[f'T{i}I'],
                      'output': sections[f'T{i}O']})
    for i in range(1, 1000):
        if f'E{i}I' not in sections:
            break
        pair = {'input': sections[f'E{i}I']}
        if f'E{i}O' in sections:
            pair['output'] = sections[f'E{i}O']
        test.append(pair)
    return {'train': train, 'test': test}
```

Verified: parsing every file in this folder reconstructs the upstream
`{train, test}` JSON exactly (1,147/1,147).
