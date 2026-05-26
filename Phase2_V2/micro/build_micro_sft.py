"""Build SFT records from validated micro tasks, with pair-cycling.

  python Phase2_V2/micro/build_micro_sft.py ray_to_edge

For each validated task, emit several records that vary which/how many train
pairs are shown (variants A/B/C/D) — but the assistant target is ALWAYS the one
canonical solver. That is the invariance lesson: instance varies, code is fixed.

Format matches real puzzles (Phase2_PROMPTS.md §4): same-size code system prompt;
user = pairs as INPUT + per-cell T, then the ask; assistant = solver source.
The prompt carries ONLY ARC-shaped evidence — never family/seed/difficulty/params.
"""
import argparse, json, random, sys
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent  # Phase2_V2/

DIFF_SYSTEM = (
    "Transformation dynamics:\n"
    "T encodes how the INPUT grid becomes the OUTPUT grid.\n"
    "Each T encodes exactly one transformation rule that applies across all pairs.\n\n"
    "When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy — OUTPUT cannot be rebuilt exactly from INPUT via T.\n\n"
    "T encoding (aggregate summary):\n"
    "  SIZE     H x W -> h x w\n\n"
    "Task:\n"
    "The output grid has DIFFERENT dimensions from the input. Each pair below is shown as INPUT, OUTPUT, and its SIZE relation. "
    "Write Python that infers the output geometry and content from the input and constructs the output:\n\n"
    "    def solve(input_grid):\n"
    "        T = infer_T(input_grid)\n"
    "        return apply_T(input_grid, T)\n\n"
    "infer_T reads structure from input_grid alone and returns the output geometry (h, w) plus how to fill it "
    "(gather from the input and/or paint). apply_T builds a fresh h x w grid and fills it from T. "
    "Derive the geometry rule (crop / tile / scale / extract) and the content rule from the pairs. "
    "Do not hardcode an output grid. Return only the code."
)

SYSTEM = (
    "Transformation dynamics:\n"
    "T encodes how the INPUT grid becomes the OUTPUT grid.\n"
    "Each T encodes exactly one transformation rule that applies across all pairs.\n\n"
    "When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.\n\n"
    "T encoding (per cell [r,c]):\n"
    "  .       INPUT -> OUTPUT cell unchanged\n"
    "  0-9     INPUT -> OUTPUT cell changed to this color\n\n"
    "Task:\n"
    "Each pair below is shown as INPUT and its T. The same rule produced every T. "
    "Write Python that regenerates T for any input of this task, then applies it:\n\n"
    "    def solve(input_grid):\n"
    "        T = infer_T(input_grid)\n"
    "        return apply_T(input_grid, T)\n\n"
    "infer_T reads structure from input_grid alone and returns the latent change map. "
    "apply_T copies the input and overwrites only the cells T selects; unselected cells are kept. "
    "Infer the rule from the pairs. Do not hardcode a grid, do not compare against a known input, "
    "do not look up an output. Return only the code."
)


def grid_to_str(g):
    return "\n".join("".join(str(c) for c in row) for row in g)


def per_cell_T(inp, out):
    return "\n".join(
        "".join("." if inp[r][c] == out[r][c] else str(out[r][c]) for c in range(len(inp[0])))
        for r in range(len(inp))
    )


def render_pairs(pairs):
    blocks = []
    for i, p in enumerate(pairs, 1):
        blocks.append(f"PAIR {i}:\nINPUT:\n{grid_to_str(p['input'])}\nT:\n{per_cell_T(p['input'], p['output'])}")
    return "\n\n".join(blocks)


def render_pairs_diff(pairs):
    """Diff-size: T is lossy, so show INPUT, OUTPUT and the SIZE relation."""
    blocks = []
    for i, p in enumerate(pairs, 1):
        ih, iw = len(p["input"]), len(p["input"][0])
        oh, ow = len(p["output"]), len(p["output"][0])
        blocks.append(f"PAIR {i}:\nINPUT:\n{grid_to_str(p['input'])}\nOUTPUT:\n{grid_to_str(p['output'])}\n"
                      f"T:\nSIZE {ih}x{iw} -> {oh}x{ow}")
    return "\n\n".join(blocks)


def variants(train, test, rng):
    """Yield (label, shown_train_pairs, test_input_or_None)."""
    n = len(train)
    out = [("A_all", train, None)]
    if n >= 3:
        out.append(("B_3pair", rng.sample(train, 3), None))
    if n >= 2:
        out.append(("C_2pair", rng.sample(train, 2), None))
    out.append(("D_comp", train, test[0]["input"]))  # competition-shaped
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dir", default="micro", help="corpus dir under Phase2_V2/ (micro | micro_diff)")
    ap.add_argument("--diff", action="store_true", help="diff-size rendering (INPUT/OUTPUT/SIZE, not per-cell T)")
    a = ap.parse_args()

    ROOT = P2 / a.dir
    SOLV = ROOT / "solvers"; TASKS = ROOT / "tasks"; SFT = ROOT / "sft"
    system = DIFF_SYSTEM if a.diff else SYSTEM
    render = render_pairs_diff if a.diff else render_pairs

    solver_src = (SOLV / f"{a.family}.py").read_text()
    task_files = sorted((TASKS / a.family).glob("*.json"))
    rng = random.Random(a.seed)
    SFT.mkdir(parents=True, exist_ok=True)
    out_path = SFT / f"{a.family}.jsonl"

    n_rec = 0
    by_variant = {}
    with out_path.open("w") as fh:
        for tf in task_files:
            task = json.loads(tf.read_text())
            for label, shown, test_input in variants(task["train"], task["test"], rng):
                user = render(shown)
                if test_input is not None:
                    user += f"\n\nTEST INPUT:\n{grid_to_str(test_input)}"
                user += "\n\nWrite def solve(input_grid)."
                rec = {"system": system, "user": user, "assistant": solver_src,
                       "meta": {"family": a.family, "task": tf.stem, "variant": label, "diff": a.diff}}
                fh.write(json.dumps(rec) + "\n")
                n_rec += 1
                by_variant[label] = by_variant.get(label, 0) + 1

    print(f"{a.family}: {n_rec} SFT records from {len(task_files)} tasks -> {out_path}")
    print(f"  by variant: {by_variant}")
    print(f"  (1 solver target across all {n_rec} records — the invariance signal)")


if __name__ == "__main__":
    main()
