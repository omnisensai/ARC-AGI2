"""Substrate encode/decode — transformation grid for ARC pairs.

Two-family representation, dispatched per pair by `encode_auto`:

(1) SAME-SIZE WRITE FIELD — `encode` / `decode`
    Use when input.shape == output.shape. Per-cell, lossless:
      '.'     = cell preserved (input[r,c] == output[r,c])
      '0'-'9' = output is this color (input[r,c] != output[r,c])
    Roundtrip: decode(input, encode(input, output)) == output.

(2) DIFF-SIZE AGGREGATE FIELD — `diffsize_encode`
    Use when input.shape != output.shape. Coordinates do not align, so
    per-cell encoding is impossible. Emits a fixed-shape text block of
    mechanical spatial facts: SIZE, BG, PALETTE, ROWS, COLS, BBOX. No
    semantic labels (no "tiling", "crop", "object", etc.). Lossy by
    design — there is no `diffsize_decode`. The aggregate field is
    training-signal evidence, not a reconstruction recipe.

`encode_auto(inp, out)` dispatches: returns a Substrate (grid of strings)
for same-size pairs, a str for diff-size pairs.

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
    return len(g), (len(g[0]) if g else 0)


def relate(a: int, b: int) -> str:
    """Mechanical relation between two non-negative ints.

    Treats 0 as a special absent/empty value:
      relate(0, 0)   -> "="
      relate(0, b)   -> "new"      (b > 0)
      relate(a, 0)   -> "dropped"  (a > 0)
    For both > 0:
      a == b              -> "="
      b is a*k (k>=2)     -> "×K"
      a is b*k (k>=2)     -> "÷K"
      otherwise           -> "Δ±N"

    Multiplicative checks precede additive on purpose: when both ratio
    and difference hold, the ratio is the more informative tag.
    """
    if a == 0 and b == 0:
        return "="
    if a == 0:
        return "new"
    if b == 0:
        return "dropped"
    if a == b:
        return "="
    if b % a == 0:
        return f"×{b // a}"
    if a % b == 0:
        return f"÷{a // b}"
    return f"Δ{b - a:+d}"


def _row_dominant(row, bg):
    """Most-frequent color in a row, preferring non-bg colors when any exist.

    Tie-break by smaller numeric color. If only bg appears, returns bg.
    """
    counts = Counter(row)
    non_bg = {c: n for c, n in counts.items() if c != bg}
    pool = non_bg if non_bg else counts
    best = max(pool.values())
    return min(c for c, n in pool.items() if n == best)


def _col_dominant(grid, c, bg):
    return _row_dominant([row[c] for row in grid], bg)


def _row_non_bg_count(row, bg):
    return sum(1 for v in row if v != bg)


def _col_non_bg_count(grid, c, bg):
    return sum(1 for row in grid if row[c] != bg)


def _color_bbox(grid, color):
    """Min/max row and col indices where `color` appears. None if absent."""
    rows = [r for r, row in enumerate(grid) if color in row]
    if not rows:
        return None
    cols = [c for row in grid for c, v in enumerate(row) if v == color]
    return (min(rows), max(rows), min(cols), max(cols))


def _fmt_bbox(bb):
    if bb is None:
        return "none"
    r0, r1, c0, c1 = bb
    return f"r{r0}-{r1},c{c0}-{c1}"


def diffsize_encode(inp: Grid, out: Grid) -> str:
    """Diff-size aggregate substrate. Lossy by design.

    Returns a multi-line string of mechanical spatial facts. Intended
    for puzzles where input.shape != output.shape. Raises ValueError
    if shapes match (use `encode` for that case).

    Format (sections separated by blank lines):

        SIZE H x W -> h x w   h:<rel> w:<rel>
        BG <in_bg> -> <out_bg>   <rel>

        PALETTE
          <color> <in_count> -> <out_count> <rel>
          ...

        ROWS
          IN_DOM:  <per-row dominant colors of input>
          OUT_DOM: <per-row dominant colors of output>
          IN_NZ:   <per-row non-input-bg counts>
          OUT_NZ:  <per-row non-output-bg counts>

        COLS
          IN_DOM:  ...
          OUT_DOM: ...
          IN_NZ:   ...
          OUT_NZ:  ...

        BBOX
          <color> in:<bbox> out:<bbox>
          ...

    No semantic labels (no "tiling", "crop", "extraction", etc.). Facts
    only. The model proposes hypotheses; the validator decides.
    """
    ih, iw = _shape(inp)
    oh, ow = _shape(out)
    if ih == oh and iw == ow:
        raise ValueError("diffsize_encode requires differing shapes; use encode()")

    in_bg = background_of(inp)
    out_bg = background_of(out)

    in_counts = Counter(c for row in inp for c in row)
    out_counts = Counter(c for row in out for c in row)
    all_colors = sorted(set(in_counts) | set(out_counts))

    lines = []
    lines.append(
        f"SIZE {ih}x{iw} -> {oh}x{ow}   h:{relate(ih, oh)} w:{relate(iw, ow)}"
    )
    lines.append(f"BG {in_bg} -> {out_bg}   {relate(in_bg, out_bg)}")

    lines.append("")
    lines.append("PALETTE")
    for c in all_colors:
        a = in_counts.get(c, 0)
        b = out_counts.get(c, 0)
        lines.append(f"  {c} {a} -> {b} {relate(a, b)}")

    in_row_dom = [_row_dominant(row, in_bg) for row in inp]
    out_row_dom = [_row_dominant(row, out_bg) for row in out]
    in_row_nz = [_row_non_bg_count(row, in_bg) for row in inp]
    out_row_nz = [_row_non_bg_count(row, out_bg) for row in out]

    lines.append("")
    lines.append("ROWS")
    lines.append("  IN_DOM:  " + " ".join(str(x) for x in in_row_dom))
    lines.append("  OUT_DOM: " + " ".join(str(x) for x in out_row_dom))
    lines.append("  IN_NZ:   " + " ".join(str(x) for x in in_row_nz))
    lines.append("  OUT_NZ:  " + " ".join(str(x) for x in out_row_nz))

    in_col_dom = [_col_dominant(inp, c, in_bg) for c in range(iw)]
    out_col_dom = [_col_dominant(out, c, out_bg) for c in range(ow)]
    in_col_nz = [_col_non_bg_count(inp, c, in_bg) for c in range(iw)]
    out_col_nz = [_col_non_bg_count(out, c, out_bg) for c in range(ow)]

    lines.append("")
    lines.append("COLS")
    lines.append("  IN_DOM:  " + " ".join(str(x) for x in in_col_dom))
    lines.append("  OUT_DOM: " + " ".join(str(x) for x in out_col_dom))
    lines.append("  IN_NZ:   " + " ".join(str(x) for x in in_col_nz))
    lines.append("  OUT_NZ:  " + " ".join(str(x) for x in out_col_nz))

    lines.append("")
    lines.append("BBOX")
    for c in all_colors:
        in_bb = _color_bbox(inp, c)
        out_bb = _color_bbox(out, c)
        lines.append(f"  {c} in:{_fmt_bbox(in_bb)} out:{_fmt_bbox(out_bb)}")

    return "\n".join(lines)


def encode_auto(inp: Grid, out: Grid):
    """Per-pair dispatch.

    Returns a Substrate (grid of single-char strings) for same-size
    pairs, a str (the diff-size aggregate block) for diff-size pairs.

    Callers can disambiguate by `isinstance(result, str)`.
    """
    ih, iw = _shape(inp)
    oh, ow = _shape(out)
    if ih == oh and iw == ow:
        return encode(inp, out)
    return diffsize_encode(inp, out)


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
