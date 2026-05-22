"""Substrate encode/decode — transformation grid for ARC pairs.

Two-family representation:

(1) SAME-SIZE WRITE FIELD — `encode` / `decode`
    Use when input.shape == output.shape. Per-cell, lossless:
      '.'     = cell preserved (input[r,c] == output[r,c])
      '0'-'9' = output is this color (input[r,c] != output[r,c])
    Roundtrip: decode(input, encode(input, output)) == output.

(2) VARIABLE-SIZE STRUCTURE FIELD — `encode_structure`
    Use when input.shape != output.shape. Coordinates do not align, so
    per-cell encoding is impossible. Instead, returns deterministic
    metadata (shape, dim relation, color sets, color counts, uniform
    rows/cols, integer dim ratios). Lossy by design — there is no
    `decode_structure`. The structure field is training-signal evidence,
    not a reconstruction recipe.

`encode_any(inp, out)` dispatches to (1) or (2) based on shape match.

Keep this file dependency-free (stdlib only).
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


def encode(inp: Grid, out: Grid) -> Substrate:
    """(input, output) -> substrate. Requires input.shape == output.shape."""
    if len(inp) != len(out) or any(len(ir) != len(oR) for ir, oR in zip(inp, out)):
        raise ValueError("encode requires input and output of the same shape")
    return [
        [
            '.' if i == o else str(o)
            for i, o in zip(ir, oR)
        ]
        for ir, oR in zip(inp, out)
    ]


def decode(inp: Grid, substrate: Substrate) -> Grid:
    """(input, substrate) -> output. Inverse of encode."""
    if len(inp) != len(substrate) or any(len(ir) != len(sr) for ir, sr in zip(inp, substrate)):
        raise ValueError("decode requires input and substrate of the same shape")
    return [
        [
            i if s == '.' else int(s)
            for i, s in zip(ir, sr)
        ]
        for ir, sr in zip(inp, substrate)
    ]


def _shape(g: Grid):
    return len(g), len(g[0]) if g else 0


def _uniform_rows(g: Grid):
    """Indices of rows whose cells are all the same color, with that color."""
    return [(r, row[0]) for r, row in enumerate(g) if len(set(row)) == 1]


def _uniform_cols(g: Grid):
    """Indices of cols whose cells are all the same color, with that color."""
    if not g:
        return []
    out = []
    for c in range(len(g[0])):
        col = [row[c] for row in g]
        if len(set(col)) == 1:
            out.append((c, col[0]))
    return out


def _dim_relation(a: int, b: int) -> str:
    """Compact relation between two positive ints.

    '=' if equal, 'aXb' if b is an integer multiple (b = a*k), 'a/k'
    if a is an integer multiple (a = b*k), 'a>b' otherwise.
    """
    if a == b:
        return '='
    if a and b and b % a == 0:
        return f'*{b // a}'
    if a and b and a % b == 0:
        return f'/{a // b}'
    return f'{a}>{b}'


def encode_structure(inp: Grid, out: Grid) -> str:
    """Variable-size structure field. Lossy by design.

    Returns a multi-line string of deterministic facts about the
    input/output pair. Intended for puzzles where input.shape !=
    output.shape (per-cell coordinates don't align). Safe to call on
    same-size pairs too, but `encode` carries strictly more information
    in that case.
    """
    ih, iw = _shape(inp)
    oh, ow = _shape(out)
    in_colors = sorted({c for row in inp for c in row})
    out_colors = sorted({c for row in out for c in row})
    common = sorted(set(in_colors) & set(out_colors))
    dropped = sorted(set(in_colors) - set(out_colors))
    new = sorted(set(out_colors) - set(in_colors))
    in_counts = Counter(c for row in inp for c in row)
    out_counts = Counter(c for row in out for c in row)

    def _set(xs):
        return ''.join(str(x) for x in xs) if xs else '-'

    def _counts(cs, counts):
        return ' '.join(f'{c}:{counts[c]}' for c in cs) if cs else '-'

    lines = [
        f"SHAPE {ih}x{iw}>{oh}x{ow}",
        f"HEIGHT {_dim_relation(ih, oh)}",
        f"WIDTH {_dim_relation(iw, ow)}",
        f"IN_COLORS {_set(in_colors)}",
        f"OUT_COLORS {_set(out_colors)}",
        f"COMMON {_set(common)}",
        f"DROPPED {_set(dropped)}",
        f"NEW {_set(new)}",
        f"IN_COUNTS {_counts(in_colors, in_counts)}",
        f"OUT_COUNTS {_counts(out_colors, out_counts)}",
    ]

    # Region hints — emitted only when present (no empty-line noise)
    urows_in = _uniform_rows(inp)
    ucols_in = _uniform_cols(inp)
    urows_out = _uniform_rows(out)
    ucols_out = _uniform_cols(out)
    if urows_in:
        lines.append("IN_UROWS " + ' '.join(f'{r}:{c}' for r, c in urows_in))
    if ucols_in:
        lines.append("IN_UCOLS " + ' '.join(f'{c}:{v}' for c, v in ucols_in))
    if urows_out:
        lines.append("OUT_UROWS " + ' '.join(f'{r}:{c}' for r, c in urows_out))
    if ucols_out:
        lines.append("OUT_UCOLS " + ' '.join(f'{c}:{v}' for c, v in ucols_out))

    return "\n".join(lines)


def encode_any(inp: Grid, out: Grid):
    """Dispatch to write-field (same-size) or structure-field (variable-size).

    Returns ('write', Substrate) or ('struct', str).
    """
    ih, iw = _shape(inp)
    oh, ow = _shape(out)
    if ih == oh and iw == ow:
        return ('write', encode(inp, out))
    return ('struct', encode_structure(inp, out))


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
