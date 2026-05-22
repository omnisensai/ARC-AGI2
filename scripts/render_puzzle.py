"""Render a puzzle's pairs as (Input | Output | Substrate) panels with ARC colors.

Usage:
    python3 scripts/render_puzzle.py <puzzle_id> [--out path/to/output.png] [--show]
    python3 scripts/render_puzzle.py f9d67f8b
    python3 scripts/render_puzzle.py f9d67f8b --out research/case_studies/f9d67f8b.png

Resolves the puzzle by searching data/arc1_train, data/arc1_eval, data/arc2_train,
data/arc2_eval. If --out is omitted, writes /tmp/<pid>.png.

Substrate visualization uses a non-ARC color so unchanged cells can never be
confused with any output digit:
  '.'     (unchanged) -> white (#FFFFFF)
  '0'-'9' (changed)   -> that ARC color
Any colored cell in the substrate panel is therefore a rule-driven change.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from substrate import encode


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
# Index 10 = sentinel for substrate '.'. Non-ARC color.
SUBSTRATE_COLORS = ARC_COLORS + [
    "#FFFFFF",  # 10 — '.' (unchanged)
]
PUZZLE_DIRS = [
    "data/arc1_train", "data/arc1_eval",
    "data/arc2_train", "data/arc2_eval",
]

GRID_CMAP = mcolors.ListedColormap(ARC_COLORS)
GRID_NORM = mcolors.BoundaryNorm(range(11), 10)

SUB_CMAP = mcolors.ListedColormap(SUBSTRATE_COLORS)
SUB_NORM = mcolors.BoundaryNorm(range(12), 11)


def find_puzzle(pid: str) -> Path:
    for d in PUZZLE_DIRS:
        p = Path(d) / f"{pid}.json"
        if p.exists():
            return p
    raise FileNotFoundError(f"puzzle {pid} not found in {PUZZLE_DIRS}")


def substrate_to_display(sub):
    """Map substrate symbols to indices 0-10 for rendering."""
    out = []
    for row in sub:
        out.append([
            10 if c == '.' else int(c)
            for c in row
        ])
    return out


def render(pid: str, out_path: Path) -> None:
    puzzle_path = find_puzzle(pid)
    puz = json.loads(puzzle_path.read_text())
    n_train = len(puz["train"])

    fig, axes = plt.subplots(n_train, 3, figsize=(14, 4.5 * n_train),
                             facecolor="white", squeeze=False)
    for i, pair in enumerate(puz["train"]):
        inp, out = pair["input"], pair["output"]
        sub = encode(inp, out)
        sub_disp = substrate_to_display(sub)
        axes[i, 0].imshow(np.array(inp), cmap=GRID_CMAP, norm=GRID_NORM)
        axes[i, 0].set_title(f"Pair {i+1} Input", fontsize=10)
        axes[i, 1].imshow(np.array(out), cmap=GRID_CMAP, norm=GRID_NORM)
        axes[i, 1].set_title(f"Pair {i+1} Output", fontsize=10)
        axes[i, 2].imshow(np.array(sub_disp), cmap=SUB_CMAP, norm=SUB_NORM)
        axes[i, 2].set_title(f"Pair {i+1} Substrate", fontsize=10)
        for ax in axes[i]:
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

