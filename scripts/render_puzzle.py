"""Render a puzzle's pairs as (Input | Output | Substrate) panels with ARC colors.

Usage:
    python3 scripts/render_puzzle.py <puzzle_id> [--out path/to/output.png] [--show]
    python3 scripts/render_puzzle.py f9d67f8b
    python3 scripts/render_puzzle.py f9d67f8b --out research/case_studies/f9d67f8b.png

Resolves the puzzle by searching data/arc1_train, data/arc1_eval, data/arc2_train,
data/arc2_eval. If --out is omitted, writes /tmp/<pid>.png.

The substrate column visualizes substrate.encode():
  '.' (background unchanged) -> rendered as the background color (black for 0-bg)
  '=' (non-bg cell unchanged) -> rendered as grey (color 5)
  '0'-'9' (changed) -> rendered as that ARC color
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from substrate import background_of, encode


ARC_COLORS = [
    "#000000",  # 0 black
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 grey
    "#F012BE",  # 6 magenta
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 sky
    "#870C25",  # 9 maroon
]
PUZZLE_DIRS = [
    "data/arc1_train", "data/arc1_eval",
    "data/arc2_train", "data/arc2_eval",
]


def find_puzzle(pid: str) -> Path:
    for d in PUZZLE_DIRS:
        p = Path(d) / f"{pid}.json"
        if p.exists():
            return p
    raise FileNotFoundError(f"puzzle {pid} not found in {PUZZLE_DIRS}")


def substrate_to_display(sub, bg):
    """Map substrate symbols to ARC color indices for rendering.
    '.' -> bg (so background unchanged cells use the actual bg color)
    '=' -> 5 (grey, signifies stable non-bg)
    digit -> that digit
    """
    out = []
    for row in sub:
        out.append([
            bg if c == '.' else 5 if c == '=' else int(c)
            for c in row
        ])
    return out


def render(pid: str, out_path: Path) -> None:
    puzzle_path = find_puzzle(pid)
    puz = json.loads(puzzle_path.read_text())
    n_train = len(puz["train"])
    cmap = mcolors.ListedColormap(ARC_COLORS)
    norm = mcolors.BoundaryNorm(range(11), 10)

    fig, axes = plt.subplots(n_train, 3, figsize=(14, 4.5 * n_train),
                             facecolor="white", squeeze=False)
    for i, pair in enumerate(puz["train"]):
        inp, out = pair["input"], pair["output"]
        bg = background_of(inp)
        sub = encode(inp, out, bg)
        sub_disp = substrate_to_display(sub, bg)
        for ax, grid, title in [
            (axes[i, 0], inp, f"Pair {i+1} Input"),
            (axes[i, 1], out, f"Pair {i+1} Output"),
            (axes[i, 2], sub_disp, f"Pair {i+1} Substrate"),
        ]:
            ax.imshow(np.array(grid), cmap=cmap, norm=norm)
            ax.set_title(title, fontsize=10)
            ax.set_xticks([]); ax.set_yticks([])

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=80, bbox_inches="tight")
    print(f"saved {out_path} ({out_path.stat().st_size // 1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("puzzle_id", help="8-char puzzle id (no .json)")
    ap.add_argument("--out", default=None,
                    help="output PNG path (default: /tmp/<pid>.png)")
    args = ap.parse_args()
    out = Path(args.out) if args.out else Path(f"/tmp/{args.puzzle_id}.png")
    render(args.puzzle_id, out)


if __name__ == "__main__":
    main()
