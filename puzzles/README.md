# puzzles/

Combined ARC-AGI corpus in a single flat folder, one file per puzzle, in
a compact comma-free text format aligned with `substrate.format_grid`.

## Counts

| Source | Split | Files |
| --- | --- | ---: |
| ARC1   | T (training)   |   400 |
| ARC1   | E (evaluation) |   400 |
| ARC2   | T (training)   | 1,000 |
| ARC2   | E (evaluation) |   120 |
| **Total** | | **1,920** |

Unique puzzle ids: 800 in ARC1, 1,120 in ARC2. 773 ids appear in both
corpora. Of those shared ids:

- 391 stayed in training for both,
- 6 stayed in evaluation for both,
- 376 were in ARC1 **evaluation** but moved to ARC2 **training**
  (likely because the old eval set was public/memorised, so ARC2 needed
  a fresh held-out set),
- 0 moved the other way (training → evaluation).

Total size on disk: 3.3 MB.

## Naming

```
<puzzle_id>_<ARC1|ARC2>_<T|E>.txt
```

- `puzzle_id` — 8-char hex id, as used upstream (e.g. `007bbfb7`).
- `ARC1` — sourced from [fchollet/ARC-AGI](https://github.com/fchollet/ARC-AGI) (master).
- `ARC2` — sourced from [arcprize/ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) (main).
- `T` — puzzle lives in the upstream **t**raining split.
- `E` — puzzle lives in the upstream **e**valuation split.

Examples:
- `00576224_ARC1_E.txt` — id `00576224`, ARC1 evaluation split.
- `00576224_ARC2_T.txt` — same id, but ARC2 reassigned it to training.

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

## Why this format

- One char per cell halves token count vs space-separated → ~20-30%
  more sampling budget at test time on a fixed context window
  (`substrate.format_grid` docstring).
- No commas → no extra tokens spent on separators the model already
  infers from the digit grid.
- Flat folder + suffix tagging → trivial `glob('puzzles/*_ARC2_*.txt')`
  filtering by source/split without nested directory walks.

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
