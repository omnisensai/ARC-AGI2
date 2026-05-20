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
import ast
import io
import tokenize


def strip_python_comments(src: str) -> str:
    """Remove # comments and docstrings from Python source.

    Unverified natural language (comments, docstrings) is risky training
    signal: models can hallucinate prose that doesn't match the code. We
    strip everything but executable code. Behavior of the code is preserved.

    Uses AST for docstring detection and tokenize for # comments — both are
    safe against # inside strings. If the source can't be parsed (rare for
    our verified codes), the input is returned unchanged.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src

    # Find docstring line ranges (module + functions + classes + async funcs)
    docstring_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                ds = node.body[0]
                end = ds.end_lineno if ds.end_lineno is not None else ds.lineno
                for ln in range(ds.lineno, end + 1):
                    docstring_lines.add(ln)

    # Find inline-comment column on each line (leftmost)
    try:
        toks = tokenize.generate_tokens(io.StringIO(src).readline)
        comment_col = {}
        for t in toks:
            if t.type == tokenize.COMMENT:
                ln = t.start[0]
                comment_col[ln] = min(comment_col.get(ln, t.start[1]), t.start[1])
    except tokenize.TokenizeError:
        comment_col = {}

    out = []
    for i, line in enumerate(src.split("\n"), start=1):
        if i in docstring_lines:
            continue
        if i in comment_col:
            line = line[:comment_col[i]].rstrip()
        if line.strip() == "" and (i in docstring_lines or i in comment_col):
            continue
        out.append(line)

    # Collapse runs of blank lines (>1 in a row → 1)
    collapsed = []
    blank = 0
    for ln in out:
        if ln.strip() == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        collapsed.append(ln)
    return "\n".join(collapsed).rstrip() + "\n"




Grid = List[List[int]]
Substrate = List[List[str]]


def background_of(grid: Grid) -> int:
    """Most common color in a grid; smallest value wins ties.

    EDGE CASE — densely-colored grids: the algorithm is purely statistical, not
    semantic. For typical ARC puzzles (mostly 0/black with a few colored shapes)
    background detection is unambiguous: 0 wins by a wide margin (60-95% of cells)
    and the substrate is mostly `.`. For dense puzzles where no color dominates,
    the chosen "background" is essentially arbitrary and changes per-pair within
    the same puzzle.

    Worked example — puzzle f9d67f8b (30x30, 4 pairs, all 9 colors used heavily):
      Pair 1: grey 15.6% beats green 13.8%        -> background = 5 (grey)
      Pair 2: magenta 19.6% wins clearly          -> background = 6 (magenta)
      Pair 3: green 18.8% beats red 18.6% (by 2)  -> background = 3 (green)
      Pair 4: grey and magenta tied at 165 cells  -> background = 5 (smallest wins)

    Implication: when no color dominates, the substrate becomes less interpretable
    to humans (a noisy mix of `.`, `=`, and digits) but remains deterministic and
    consistent (encode/decode round-trip still holds). The model still learns from
    it, because what matters is the consistency of the mapping, not human
    legibility. The "noise reduction" property is strongest on sparse puzzles."""
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


def hierarchy_substrate(grid: Grid):
    """Decompose a single grid into 3 frequency tiers (purely mechanical).

    '.' = the most common color (whatever it is)
    '#' = the second most common color
    'S' = all other colors

    No semantic interpretation — '.' is not necessarily "background" and '#'
    is not necessarily "structure". The rule is frequency-only. Sometimes '.'
    is a big shape filling the grid; sometimes it's border cells. The model
    learns consistent frequency-decomposition; consistency is what matters.

    Ties broken by lower color value (deterministic). Returns None if the grid
    has fewer than 2 unique colors (no hierarchy to decompose).

    Lossy by design: 'S' doesn't specify WHICH content color, so this
    substrate cannot be decoded back. Teaches perception (separate the most
    frequent from the rare), not reconstruction.
    """
    counts = Counter(c for row in grid for c in row)
    if len(counts) < 2:
        return None
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    bg = ranked[0][0]
    struct = ranked[1][0]
    return [
        ['.' if v == bg else '#' if v == struct else 'S' for v in row]
        for row in grid
    ]


def format_grid(grid) -> str:
    """Render a grid (of ints or substrate symbols) as compact rows (no spaces).
    Each cell is exactly one character (0-9 or substrate symbol). This halves
    grid token count vs space-separated, giving ~20-30% more sampling budget
    at test time on a fixed context window."""
    return "\n".join("".join(str(c) for c in row) for row in grid)


def parse_grid(text: str) -> List[List[str]]:
    """Parse a compact grid string back into a list of lists of single-char tokens.
    Each row is a string where every char is one cell."""
    return [list(line) for line in text.strip().split("\n") if line.strip()]
