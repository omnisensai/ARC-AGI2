"""Phase2_V2 Run 1 eval harness.

Runs the trained LoRA against three buckets and writes a results JSONL per
bucket with the model's emitted code + the canonical correct code + a
failure-mode classification. Phase 3 (repair) is built from the failure records.

Usage:
  python Phase2_V2/run1/eval_harness.py \\
      --lora Phase2_V2/run1/lora_out/checkpoint-N \\
      --bucket 1 \\
      [--augment]      # apply D4 + color perms to multiply the bucket
      [--limit N]      # cap puzzles for smoke tests

Buckets:
  1  trained sample        (200)   -> bucket1_trained_sample.txt
  2  held-out same-size    (43)    -> bucket2_heldout_samesize.txt
  3  cold diff-size       (364)   -> bucket3_cold_diffsize.txt

Failure modes (auto-classified):
  PASS              -- model code, run on test input, exact match expected output
  RUNTIME_ERROR     -- code raised an exception
  TIMEOUT           -- code didn't finish in 3s
  SHAPE_MISMATCH    -- output shape != expected (esp. revealing for diff-size)
  WRONG_OUTPUT      -- shape ok but cells wrong
  EMPTY_OR_INVALID  -- no `def solve` extracted, syntax error, etc.
  HARDCODED         -- code passes via fingerprint/big-literal hardcoding (AST audit)
"""
import argparse, ast, json, sys, subprocess, tempfile, time
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent  # Phase2_V2/
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import audit as _ast_audit   # returns list of flag strings


SYSTEM_SAME = (
    "T encodes how INPUT becomes OUTPUT.\n\n"
    "For same-size grids, T is a per-cell change map:\n"
    ". = unchanged\n"
    "0-9 = overwrite this cell with that colour\n\n"
    "Each pair shows INPUT and T. The same rule produced every T.\n\n"
    "Write Python code in this exact shape:\n\n"
    "def infer_T(input_grid):\n"
    "    ...\n\n"
    "def apply_T(input_grid, T):\n"
    "    out = [row[:] for row in input_grid]\n"
    "    for (r, c), v in T.items():\n"
    "        out[r][c] = v\n"
    "    return out\n\n"
    "def solve(input_grid):\n"
    "    T = infer_T(input_grid)\n"
    "    return apply_T(input_grid, T)\n\n"
    "infer_T must read structure from input_grid only. Do not hardcode grids, "
    "compare to known inputs, or look up outputs. Return code only."
)

SYSTEM_DIFF = (
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


def grid_to_str(g): return "\n".join("".join(str(c) for c in row) for row in g)


def per_cell_T(inp, out):
    return "\n".join(
        "".join("." if inp[r][c] == out[r][c] else str(out[r][c]) for c in range(len(inp[0])))
        for r in range(len(inp))
    )


def render_user_same(pairs):
    blocks = []
    for i, p in enumerate(pairs, 1):
        blocks.append(f"PAIR {i}:\nINPUT:\n{grid_to_str(p['input'])}\nT:\n{per_cell_T(p['input'], p['output'])}")
    return "\n\n".join(blocks) + "\n\nWrite def solve(input_grid)."


def render_user_diff(pairs):
    blocks = []
    for i, p in enumerate(pairs, 1):
        ih, iw = len(p["input"]), len(p["input"][0])
        oh, ow = len(p["output"]), len(p["output"][0])
        blocks.append(f"PAIR {i}:\nINPUT:\n{grid_to_str(p['input'])}\nOUTPUT:\n{grid_to_str(p['output'])}\n"
                      f"T:\nSIZE {ih}x{iw} -> {oh}x{ow}")
    return "\n\n".join(blocks) + "\n\nWrite def solve(input_grid)."


def build_prompt(puzzle, diff_size: bool):
    train = puzzle["train"]
    test_input = puzzle["test"][0]["input"]
    system = SYSTEM_DIFF if diff_size else SYSTEM_SAME
    user = (render_user_diff if diff_size else render_user_same)(train)
    return system, user, test_input


def extract_code(model_output: str) -> str:
    """Extract Python code from the model's output (handles ``` fences and bare)."""
    s = model_output.strip()
    if "```" in s:
        # take the largest fenced block
        chunks = []
        in_block = False; cur = []
        for line in s.split("\n"):
            if line.startswith("```"):
                if in_block:
                    chunks.append("\n".join(cur)); cur = []
                in_block = not in_block
                continue
            if in_block: cur.append(line)
        if cur: chunks.append("\n".join(cur))
        if chunks: s = max(chunks, key=len)
    return s


def run_code(code: str, test_input: list, timeout: float = 3.0) -> dict:
    """Run code on test_input in a subprocess, return {'ok', 'output', 'error'}."""
    runner = (
        f"import sys, json\n"
        f"code = {code!r}\n"
        f"ns = {{}}\n"
        f"try:\n"
        f"    exec(code, ns)\n"
        f"    solve = ns.get('solve')\n"
        f"    if solve is None: raise RuntimeError('no solve function')\n"
        f"    inp = json.loads(sys.stdin.read())\n"
        f"    out = solve(inp)\n"
        f"    print('OK'); print(json.dumps(out))\n"
        f"except Exception as e:\n"
        f"    print('ERR'); print(type(e).__name__ + ': ' + str(e))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", runner],
            input=json.dumps(test_input),
            capture_output=True, text=True, timeout=timeout,
        )
        lines = result.stdout.split("\n", 1)
        if lines[0].strip() == "OK":
            return {"ok": True, "output": json.loads(lines[1]), "error": None}
        return {"ok": False, "output": None, "error": lines[1] if len(lines) > 1 else result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": None, "error": "TIMEOUT"}


def classify(code: str, run_result: dict, expected_output: list, expected_shape) -> str:
    if not code or "def solve" not in code:
        return "EMPTY_OR_INVALID"
    try:
        ast.parse(code)
    except SyntaxError:
        return "EMPTY_OR_INVALID"
    # Hardcode audit. Only flag as HARDCODED if the code actually passes;
    # otherwise WRONG/RUNTIME is the more specific failure tag.
    flags = _ast_audit(code, big_literal_max=12)
    if flags and run_result["ok"] and run_result["output"] == expected_output:
        return "HARDCODED"
    if not run_result["ok"]:
        if run_result["error"] == "TIMEOUT":
            return "TIMEOUT"
        return "RUNTIME_ERROR"
    out = run_result["output"]
    if not isinstance(out, list) or not out or not isinstance(out[0], list):
        return "EMPTY_OR_INVALID"
    out_shape = (len(out), len(out[0]) if out else 0)
    if out_shape != expected_shape:
        return "SHAPE_MISMATCH"
    if out == expected_output:
        return "PASS"
    return "WRONG_OUTPUT"


# ============================================================================
# Augmentation (mirrors canonical/augment_all.py: D4 x color perms x gate)
# ============================================================================
import random as _random
D4 = [("id", lambda g: g),
      ("r90", lambda g: [list(r) for r in zip(*g[::-1])]),
      ("r180", lambda g: [r[::-1] for r in g[::-1]]),
      ("r270", lambda g: [list(r) for r in zip(*g)][::-1]),
      ("flipH", lambda g: [r[::-1] for r in g]),
      ("flipV", lambda g: g[::-1]),
      ("trans", lambda g: [list(r) for r in zip(*g)]),
      ("antiT", lambda g: [list(r) for r in zip(*[row[::-1] for row in g[::-1]])])]


def color_perm(g, perm): return [[perm.get(c, c) for c in row] for row in g]


def random_perm(rng):
    src = list(range(10)); dst = list(range(10)); rng.shuffle(dst)
    return {a: b for a, b in zip(src, dst)}


def augment_puzzle(puzzle, n_color_perms, seed):
    rng = _random.Random(seed)
    perms = [("c_id", {})] + [(f"c_p{k}", random_perm(rng)) for k in range(n_color_perms)]
    pairs = puzzle["train"] + puzzle["test"]
    nt = len(puzzle["train"])
    aug = []
    for dname, dfn in D4:
        for cname, cperm in perms:
            transformed = [{"input":  color_perm(dfn(p["input"]),  cperm),
                            "output": color_perm(dfn(p["output"]), cperm)}
                           for p in pairs]
            aug.append((f"{dname}+{cname}", transformed[:nt], transformed[nt:]))
    return aug


# ============================================================================
# Main
# ============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True, help="path to LoRA checkpoint dir")
    ap.add_argument("--bucket", type=int, choices=[1, 2, 3], required=True)
    ap.add_argument("--augment", action="store_true",
                    help="apply D4 x color perms to multiply the eval set")
    ap.add_argument("--n-color-perms", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="cap puzzles (0 = all)")
    ap.add_argument("--out", default=None,
                    help="output JSONL path (default: Phase2_V2/run1/eval/bucket{N}{_aug}.jsonl)")
    a = ap.parse_args()

    bucket_to_split = {
        1: P2 / "run1/splits/bucket1_trained_sample.txt",
        2: P2 / "run1/splits/bucket2_heldout_samesize.txt",
        3: P2 / "run1/splits/bucket3_cold_diffsize.txt",
    }
    diff_size = (a.bucket == 3)
    out_path = a.out or str(P2 / f"run1/eval/bucket{a.bucket}{'_aug' if a.augment else ''}.jsonl")

    ids = bucket_to_split[a.bucket].read_text().split()
    if a.limit:
        ids = ids[:a.limit]

    # === LoRA inference setup is left as TODO (deferred to actual training run);
    # the harness above is the format & classification spine. Once the LoRA is
    # trained you load it (e.g. via vLLM or HF .generate) and call
    # `model_emit(system, user) -> str` here.
    print(f"[STUB] would run LoRA at {a.lora} over {len(ids)} puzzles, "
          f"diff_size={diff_size}, augment={a.augment} -> {out_path}")
    print("To enable: implement `model_emit(system, user) -> str` below and "
          "uncomment the run loop.")

    # for pid in ids:
    #     puzzle = load_puzzle(pid)
    #     pairs_sets = augment_puzzle(puzzle, a.n_color_perms, seed=hash(pid) & 0xffff) if a.augment else [("id+c_id", puzzle["train"], puzzle["test"])]
    #     for tag, train_pairs, test_pairs in pairs_sets:
    #         system, user, test_input = build_prompt({"train": train_pairs, "test": test_pairs}, diff_size)
    #         model_out = model_emit(system, user)
    #         code = extract_code(model_out)
    #         expected = test_pairs[0]["output"]
    #         expected_shape = (len(expected), len(expected[0]))
    #         run_result = run_code(code, test_input)
    #         mode = classify(code, run_result, expected, expected_shape)
    #         record = {
    #             "puzzle": pid, "augment": tag, "bucket": a.bucket,
    #             "system": system, "user": user, "test_input": test_input,
    #             "wrong_code": code if mode != "PASS" else None,
    #             "model_output_raw": model_out,
    #             "expected_output": expected, "got_output": run_result["output"],
    #             "failure_mode": mode,
    #             "canonical_code": load_canonical_solver(pid),  # for bucket 1/2; None for cold bucket 3
    #         }
    #         out_fh.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main()
