"""Substrate encode/decode — lossless transformation grid for same-size ARC pairs.

Substrate alphabet (per cell):
  '.'    = background unchanged (bg in input, bg in output)
  '='    = non-background preserved (input[r,c] == output[r,c], not bg)
  '0'-'9' = output is this color (input[r,c] != output[r,c])

Background convention: bg = most common color in input grid.
For ties, the smallest color value wins (deterministic).

Roundtrip property: encode(input, output, bg) then decode(input, substrate, bg)
returns the original output, for any same-size pair.

This file is the shared library imported by gen_phase1_data.py and any future
eval script. Keep it dependency-free (stdlib only).
"""
from collections import Counter
from typing import List


Grid = List[List[int]]
Substrate = List[List[str]]


def background_of(grid: Grid) -> int:
    """Most common color in a grid; smallest value wins ties."""
    counts = Counter(c for row in grid for c in row)
    most = max(counts.values())
    return min(c for c, n in counts.items() if n == most)


def encode(inp: Grid, out: Grid, bg: int) -> Substrate:
    """(input, output, bg) -> substrate. Requires input.shape == output.shape."""
    if len(inp) != len(out) or any(len(ir) != len(oR) for ir, oR in zip(inp, out)):
        raise ValueError("encode requires input and output of the same shape")
    return [
        [
            '.' if (i == bg and o == bg)
            else '=' if i == o
            else str(o)
            for i, o in zip(ir, oR)
        ]
        for ir, oR in zip(inp, out)
    ]


def decode(inp: Grid, substrate: Substrate, bg: int) -> Grid:
    """(input, substrate, bg) -> output. Inverse of encode."""
    if len(inp) != len(substrate) or any(len(ir) != len(sr) for ir, sr in zip(inp, substrate)):
        raise ValueError("decode requires input and substrate of the same shape")
    return [
        [
            bg if s == '.'
            else i if s == '='
            else int(s)
            for i, s in zip(ir, sr)
        ]
        for ir, sr in zip(inp, substrate)
    ]


def is_same_size(puzzle: dict) -> bool:
    """All train and test pairs preserve grid dimensions."""
    for pair in puzzle["train"] + puzzle["test"]:
        inp, out = pair["input"], pair["output"]
        if len(inp) != len(out):
            return False
        if any(len(ir) != len(oR) for ir, oR in zip(inp, out)):
            return False
    return True


def format_grid(grid) -> str:
    """Render a grid (of ints or substrate symbols) as space-separated rows."""
    return "\n".join(" ".join(str(c) for c in row) for row in grid)


def parse_grid(text: str) -> List[List[str]]:
    """Parse a space-separated grid string back into a list of lists of tokens."""
    return [line.split() for line in text.strip().split("\n") if line.strip()]
