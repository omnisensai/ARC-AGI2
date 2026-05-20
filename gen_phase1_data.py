"""Generate Phase 1 substrate training data.

Reads same-size puzzles from data/arc1_train, data/arc1_eval, data/arc2_train.
Excludes the 10 locked baseline_10 puzzles. Filters to puzzles where every
(input, output) pair preserves grid dimensions.

For each (input, output) pair, applies augmentations and emits two training
records:
  Phase 1a:  (input, output) -> substrate
  Phase 1b:  (input, substrate) -> output

Augmentations:
  - D4 (8 variants: rotate 0/90/180/270, optionally flipped)
  - Color permutations (random permutations of {0..9} applied to all cells)

Output:
  phase1_train.jsonl      ~99% of puzzles after held-out split
  phase1_dev.jsonl        100 puzzles, never seen in training, used to monitor
                          encode/decode accuracy during fine-tuning

Usage:
  python3 gen_phase1_data.py                       # defaults: D4 only, no color perms
  python3 gen_phase1_data.py --color-perms 5       # 5 random color perms per (pair, rotation)
  python3 gen_phase1_data.py --no-augment          # raw only (no D4, no color perms)
  python3 gen_phase1_data.py --dev-size 100        # change dev puzzle count
"""
import argparse
import json
import random
from itertools import product
from pathlib import Path

from substrate import (background_of, encode, decode, is_same_size,
                       hierarchy_substrate, format_grid, strip_python_comments)


# Single-letter task selectors (the entire system prompt). The verbose
# task descriptions live in research/Phase1_Substrate_Spec.md. During
# training the model learns: see "A" -> emit pixel substrate, see "B" ->
# emit output from substrate, see "H" -> emit hierarchy. At inference the
# caller picks a task by setting system="A" (or "B"/"H").
#
# Reserved tags for future phases:
#   C = substrate -> code           (Phase 2)
#   D = pairs -> code               (Phase 2)
#   E = wrong code + feedback -> right code  (Phase 3 corrector)
PHASE1A_SYSTEM = "A"
PHASE1B_SYSTEM = "B"
HIERARCHY_SYSTEM = "H"
MULTI_PAIR_SYSTEM = "M"     # Task M: all pairs -> all substrates (cross-pair rule)
SUBSTRATE_TO_CODE_SYSTEM = "C"  # Task C: substrates -> code


def rotate90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def flip_h(grid):
    return [row[::-1] for row in grid]


def d4_variants(grid):
    """Return all 8 D4 transforms of a grid, in a fixed order."""
    out = []
    g = grid
    for _ in range(4):
        out.append(g)
        g = rotate90(g)
    g = flip_h(grid)
    for _ in range(4):
        out.append(g)
        g = rotate90(g)
    return out


def apply_color_perm(grid, perm):
    """perm: list of 10 ints mapping old color -> new color."""
    return [[perm[c] if isinstance(c, int) else c for c in row] for row in grid]


def make_record_1a(inp, out, bg, puzzle_id, aug_tag):
    """Phase 1a: (input, output) -> substrate."""
    sub = encode(inp, out, bg)
    return {
        "task": "phase1a",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "messages": [
            {"role": "system", "content": PHASE1A_SYSTEM},
            {"role": "user", "content": f"INPUT:\n{format_grid(inp)}\n\nOUTPUT:\n{format_grid(out)}"},
            {"role": "assistant", "content": format_grid(sub)},
        ],
    }


def make_record_1b(inp, out, bg, puzzle_id, aug_tag):
    """Phase 1b: (input, substrate) -> output."""
    sub = encode(inp, out, bg)
    return {
        "task": "phase1b",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "messages": [
            {"role": "system", "content": PHASE1B_SYSTEM},
            {"role": "user", "content": f"INPUT:\n{format_grid(inp)}\n\nSUBSTRATE:\n{format_grid(sub)}"},
            {"role": "assistant", "content": format_grid(out)},
        ],
    }


def make_record_hierarchy(grid, puzzle_id, aug_tag, side):
    """Task A2: grid -> hierarchy substrate. Works on any single grid.

    `side` is 'input' or 'output' to disambiguate within a pair.
    Returns None if the grid has fewer than 2 unique colors or is too small.
    """
    if len(grid) < 3 or len(grid[0]) < 3:
        return None
    sub = hierarchy_substrate(grid)
    if sub is None:
        return None
    return {
        "task": "phase1a_hierarchy",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "side": side,
        "messages": [
            {"role": "system", "content": HIERARCHY_SYSTEM},
            {"role": "user", "content": f"GRID:\n{format_grid(grid)}"},
            {"role": "assistant", "content": format_grid(sub)},
        ],
    }


def make_record_multi_pair(train_pairs, puzzle_id, aug_tag):
    """Task M: ALL training pairs together -> ALL their substrates together.
    Teaches cross-pair rule consistency (the substrate pattern should be the
    same across pairs because the rule is the same)."""
    user_parts = []
    asst_parts = []
    for i, (inp, out) in enumerate(train_pairs, start=1):
        bg = background_of(inp)
        sub = encode(inp, out, bg)
        user_parts.append(f"P{i} INPUT:\n{format_grid(inp)}\n\nP{i} OUTPUT:\n{format_grid(out)}")
        asst_parts.append(f"P{i} SUBSTRATE:\n{format_grid(sub)}")
    return {
        "task": "phase1_multi_pair",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "messages": [
            {"role": "system", "content": MULTI_PAIR_SYSTEM},
            {"role": "user", "content": "\n\n".join(user_parts)},
            {"role": "assistant", "content": "\n\n".join(asst_parts)},
        ],
    }


def make_record_substrate_to_code(train_pairs, test_input, right_code, puzzle_id):
    """Task C: pairs + their substrates -> Python solve(). Bridges substrate
    perception to code generation. No D4 augmentation (code is orientation-
    specific). One record per (puzzle, right_code)."""
    user_parts = []
    for i, (inp, out) in enumerate(train_pairs, start=1):
        bg = background_of(inp)
        sub = encode(inp, out, bg)
        user_parts.append(
            f"P{i} INPUT:\n{format_grid(inp)}\n\n"
            f"P{i} OUTPUT:\n{format_grid(out)}\n\n"
            f"P{i} SUBSTRATE:\n{format_grid(sub)}"
        )
    user_parts.append(f"TEST INPUT:\n{format_grid(test_input)}")
    return {
        "task": "phase1_substrate_to_code",
        "puzzle_id": puzzle_id,
        "messages": [
            {"role": "system", "content": SUBSTRATE_TO_CODE_SYSTEM},
            {"role": "user", "content": "\n\n".join(user_parts)},
            {"role": "assistant", "content": strip_python_comments(right_code)},
        ],
    }


def gen_puzzle_records(puzzle, puzzle_id, same_size, no_augment, right_codes):
    """Yield Task M and Task C records for one puzzle (whole-puzzle level)."""
    if not same_size:
        return
    train_pairs_raw = [(p["input"], p["output"]) for p in puzzle["train"]]
    test_input_raw = puzzle["test"][0]["input"]
    if no_augment:
        d4_pair_sets = [(train_pairs_raw, test_input_raw, "d4_0")]
    else:
        # Apply same D4 transform to all pairs in a puzzle (rule is rotation-equivariant)
        d4_pair_sets = []
        for i in range(8):
            if i < 4:
                rotated_pairs = [(rotate90_n(inp, i), rotate90_n(out, i)) for inp, out in train_pairs_raw]
                rotated_test = rotate90_n(test_input_raw, i)
            else:
                # flipped then rotated
                rotated_pairs = [(rotate90_n(flip_h(inp), i-4), rotate90_n(flip_h(out), i-4)) for inp, out in train_pairs_raw]
                rotated_test = rotate90_n(flip_h(test_input_raw), i-4)
            d4_pair_sets.append((rotated_pairs, rotated_test, f"d4_{i}"))

    for train_pairs, test_input, aug_tag in d4_pair_sets:
        yield make_record_multi_pair(train_pairs, puzzle_id, aug_tag)

    # Task C: no augmentation (code is orientation-specific), one record per right_code
    for code in right_codes:
        yield make_record_substrate_to_code(train_pairs_raw, test_input_raw, code, puzzle_id)


def rotate90_n(grid, n):
    g = grid
    for _ in range(n):
        g = rotate90(g)
    return g


def gen_pair_records(inp, out, puzzle_id, n_color_perms, no_augment, rng, same_size):
    """Yield records for one (input, output) pair, across augmentations.

    Phase 1a + Phase 1b records emitted only when same_size is True (per-cell
    substrate requires matching dimensions).
    Task A2 (hierarchy) records emitted regardless — one per grid (input + output).
    """
    if no_augment:
        d4_inputs = [inp]
        d4_outputs = [out]
        d4_tags = ["d4_0"]
    else:
        d4_inputs = d4_variants(inp)
        d4_outputs = d4_variants(out)
        d4_tags = [f"d4_{i}" for i in range(8)]

    for i_d4, o_d4, tag in zip(d4_inputs, d4_outputs, d4_tags):
        # Phase 1a + 1b: same-size only
        if same_size:
            bg = background_of(i_d4)
            yield make_record_1a(i_d4, o_d4, bg, puzzle_id, tag)
            yield make_record_1b(i_d4, o_d4, bg, puzzle_id, tag)
            for k in range(n_color_perms):
                perm = list(range(10))
                rng.shuffle(perm)
                i_perm = apply_color_perm(i_d4, perm)
                o_perm = apply_color_perm(o_d4, perm)
                bg_perm = background_of(i_perm)
                aug_tag = f"{tag}_cp{k}"
                yield make_record_1a(i_perm, o_perm, bg_perm, puzzle_id, aug_tag)
                yield make_record_1b(i_perm, o_perm, bg_perm, puzzle_id, aug_tag)

        # Task A2 (hierarchy): one record per grid, regardless of same-size.
        # Color permutations don't apply: hierarchy is frequency-based and
        # invariant under color relabeling.
        rec_in = make_record_hierarchy(i_d4, puzzle_id, tag, "input")
        if rec_in is not None:
            yield rec_in
        rec_out = make_record_hierarchy(o_d4, puzzle_id, tag, "output")
        if rec_out is not None:
            yield rec_out


def collect_universe(repo_root: Path, locked_eval: set):
    """Return [(puzzle_id, source, path, same_size), ...] for ALL non-locked puzzles.

    Phase 1a/1b records are emitted only for same_size puzzles (per-cell substrate
    requires matching dims). Task A2 hierarchy records are emitted for all puzzles
    regardless of size.

    Shared puzzle IDs across arc1/arc2 have DIFFERENT content (ARC-AGI-2 revised
    many ARC-AGI-1 puzzles). We include both as separate examples — same task ID,
    distinct content. Train/dev split groups by puzzle_id so variants stay together.
    """
    sources = [
        ("arc1_train", repo_root / "data" / "arc1_train"),
        ("arc1_eval",  repo_root / "data" / "arc1_eval"),
        ("arc2_train", repo_root / "data" / "arc2_train"),
    ]
    universe = []
    for src_name, src_dir in sources:
        for path in sorted(src_dir.glob("*.json")):
            pid = path.stem
            if pid in locked_eval:
                continue
            puzzle = json.loads(path.read_text())
            universe.append((pid, src_name, path, is_same_size(puzzle)))
    return universe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--color-perms", type=int, default=0,
                    help="random color permutations per (pair, D4 rotation). 0 = D4 only.")
    ap.add_argument("--no-augment", action="store_true",
                    help="raw only, no D4 and no color perms.")
    ap.add_argument("--dev-size", type=int, default=100,
                    help="puzzles held out for phase1_dev.jsonl.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    repo_root = Path(__file__).parent
    splits_dir = repo_root / "splits"
    splits_dir.mkdir(exist_ok=True)

    # Locked eval puzzles (final benchmark, never train on these)
    # = arc2_eval (official ARC-AGI-2 held-out benchmark)
    locked_eval = set()
    arc2_eval_dir = repo_root / "data" / "arc2_eval"
    if arc2_eval_dir.exists():
        locked_eval = {p.stem for p in arc2_eval_dir.glob("*.json")}

    universe = collect_universe(repo_root, locked_eval)
    unique_ids = sorted({pid for pid, _, _, _ in universe})
    same_size_examples = sum(1 for _, _, _, ss in universe if ss)
    diff_size_examples = sum(1 for _, _, _, ss in universe if not ss)
    print(f"Universe: {len(universe)} puzzle examples "
          f"({len(unique_ids)} unique IDs)")
    print(f"  same-size: {same_size_examples} examples (Phase 1a + 1b)")
    print(f"  diff-size: {diff_size_examples} examples (Task A2 hierarchy only)")

    # Deterministic train/dev split BY puzzle_id (all source variants of an ID
    # go to the same side, preventing arc1/arc2 cross-variant leakage)
    rng = random.Random(args.seed)
    shuffled = list(unique_ids)
    rng.shuffle(shuffled)
    dev_ids = set(shuffled[:args.dev_size])
    train_ids = set(shuffled[args.dev_size:])
    train_examples = sum(1 for pid, _, _, _ in universe if pid in train_ids)
    dev_examples = sum(1 for pid, _, _, _ in universe if pid in dev_ids)
    print(f"  train: {len(train_ids)} unique IDs ({train_examples} examples)")
    print(f"  dev:   {len(dev_ids)} unique IDs ({dev_examples} examples)")

    # Save the universe + split manifest (so it's reproducible)
    (splits_dir / "training_universe.json").write_text(json.dumps({
        "description": "Phase 1 training universe: ALL puzzles from ARC-AGI-1 "
                       "train + eval + ARC-AGI-2 train, minus the 10 locked "
                       "baseline_10 puzzles. Phase 1a/1b uses the same-size "
                       "subset only; Task A2 (hierarchy) uses all puzzles. "
                       "Train/dev split by unique puzzle_id (variants across "
                       "sources stay together), seed=42.",
        "seed": args.seed,
        "unique_ids_total": len(unique_ids),
        "examples_total": len(universe),
        "same_size_examples": same_size_examples,
        "diff_size_examples": diff_size_examples,
        "train_unique_ids": len(train_ids),
        "dev_unique_ids": len(dev_ids),
        "train_examples": train_examples,
        "dev_examples": dev_examples,
        "train_ids": sorted(train_ids),
        "dev_ids": sorted(dev_ids),
    }, indent=2))

    train_path = Path(args.out_dir) / "phase1_train.jsonl"
    dev_path = Path(args.out_dir) / "phase1_dev.jsonl"

    rec_rng = random.Random(args.seed + 1)

    # Load corpus right_codes for Task C
    corpus_dir = repo_root / "research" / "agent_corpus" / "by_puzzle"
    right_codes_by_pid = {}
    for cf in corpus_dir.glob("*.json"):
        rec = json.loads(cf.read_text())
        codes = [r["code"] for r in rec.get("right_codes", []) if r.get("code")]
        if codes:
            right_codes_by_pid[cf.stem] = codes
    print(f"Corpus right_codes: {sum(len(v) for v in right_codes_by_pid.values())} codes across {len(right_codes_by_pid)} puzzles")

    counts = {"phase1a": 0, "phase1b": 0, "phase1a_hierarchy": 0,
              "phase1_multi_pair": 0, "phase1_substrate_to_code": 0}
    n_train = 0
    n_dev = 0
    with open(train_path, "w") as ft, open(dev_path, "w") as fd:
        for pid, src, path, same_size in universe:
            puzzle = json.loads(path.read_text())
            sink = ft if pid in train_ids else fd
            # Per-pair records (A, B, H)
            for pair in puzzle["train"] + puzzle["test"]:
                inp, out = pair["input"], pair["output"]
                for rec in gen_pair_records(inp, out, pid,
                                            args.color_perms, args.no_augment,
                                            rec_rng, same_size):
                    sink.write(json.dumps(rec) + "\n")
                    counts[rec["task"]] += 1
                    if pid in train_ids:
                        n_train += 1
                    else:
                        n_dev += 1
            # Whole-puzzle records (M, C)
            right_codes = right_codes_by_pid.get(pid, [])
            for rec in gen_puzzle_records(puzzle, pid, same_size,
                                          args.no_augment, right_codes):
                sink.write(json.dumps(rec) + "\n")
                counts[rec["task"]] += 1
                if pid in train_ids:
                    n_train += 1
                else:
                    n_dev += 1

    print(f"\nWrote:")
    print(f"  {train_path}  {n_train:>7,} records")
    print(f"  {dev_path}    {n_dev:>7,} records")
    print(f"  by task type:")
    for task, c in counts.items():
        print(f"    {task:<22} {c:>7,}")
    print(f"  {splits_dir / 'training_universe.json'}")


if __name__ == "__main__":
    main()
