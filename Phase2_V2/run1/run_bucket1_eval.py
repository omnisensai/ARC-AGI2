"""Run bucket 1 (100 trained-sample) eval against the trained LoRA via vLLM.

Loads base Qwen2.5-7B-Instruct + the LoRA adapter, generates code for each
puzzle using EXACTLY the same prompt format the LoRA was trained on (same
SYSTEM, same INPUT/T USER, same chat template), runs each generated solver
against the puzzle's test pair, and reports solve rate.

Usage (from repo root):

    python3 Phase2_V2/run1/run_bucket1_eval.py \\
        --lora outputs/phase2_v2_run1/checkpoint-2460 \\
        [--limit N]

Writes:
    Phase2_V2/run1/eval/bucket1.jsonl   (every prediction + classification)

Format-matching guarantees:
  - SYSTEM = SYSTEM_SAME from build_micro_sft.py (the compact prompt we sealed)
  - USER   = render_pairs(train) + "\\n\\nWrite def solve(input_grid)."
             where render_pairs builds PAIR N: INPUT/T blocks
  - Chat template = Qwen2.5's tokenizer_default (same one axolotl used with
                    chat_template: tokenizer_default in the yaml)
  - Generation = greedy (temperature 0) so output is deterministic
"""
import argparse, ast, json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # ARC-AGI2/
P2 = REPO / "Phase2_V2"
sys.path.insert(0, str(P2 / "micro"))
sys.path.insert(0, str(P2 / "scripts"))

# === Format-matching: import the EXACT same SYSTEM + renderer used in training ===
from build_micro_sft import SYSTEM, render_pairs    # SAME-size SYSTEM + PAIR renderer
from canonical_gate import audit as _ast_audit


def load_puzzle(pid: str) -> dict:
    """Load puzzle JSON from Puzzle_Database. Tries A1T then A2T."""
    for suffix in ("A1T", "A2T", "A1E", "A2E"):
        p = P2 / "Puzzle_Database" / f"{pid}_{suffix}.json"
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError(f"no puzzle file for {pid}")


def build_prompt(puzzle):
    """Build the EXACT prompt format the LoRA was trained on."""
    train = puzzle["train"]
    user = render_pairs(train) + "\n\nWrite def solve(input_grid)."
    return SYSTEM, user


def extract_code(model_output: str) -> str:
    s = model_output.strip()
    if "```" in s:
        chunks, cur, in_block = [], [], False
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
        return {"ok": False, "output": None,
                "error": lines[1] if len(lines) > 1 else result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": None, "error": "TIMEOUT"}


def classify(code, run_result, expected, expected_shape):
    if not code or "def solve" not in code:
        return "EMPTY_OR_INVALID"
    try:
        ast.parse(code)
    except SyntaxError:
        return "EMPTY_OR_INVALID"
    flags = _ast_audit(code, big_literal_max=12)
    if flags and run_result["ok"] and run_result["output"] == expected:
        return "HARDCODED"
    if not run_result["ok"]:
        return "TIMEOUT" if run_result["error"] == "TIMEOUT" else "RUNTIME_ERROR"
    out = run_result["output"]
    if not isinstance(out, list) or not out or not isinstance(out[0], list):
        return "EMPTY_OR_INVALID"
    out_shape = (len(out), len(out[0]))
    if out_shape != expected_shape:
        return "SHAPE_MISMATCH"
    if out == expected:
        return "PASS"
    return "WRONG_OUTPUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True, help="path to LoRA checkpoint dir")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--limit", type=int, default=0, help="cap puzzles (0 = all 100)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    out_path = Path(a.out or P2 / "run1/eval/bucket1.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load puzzle ids
    ids = (P2 / "run1/splits/bucket1_trained_sample.txt").read_text().split()
    if a.limit:
        ids = ids[:a.limit]
    print(f"loading {len(ids)} puzzles ...")
    puzzles = {pid: load_puzzle(pid) for pid in ids}

    # === vLLM setup ===
    print(f"loading vLLM with base={a.base_model}, lora={a.lora} ...")
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm = LLM(
        model=a.base_model,
        enable_lora=True,
        max_lora_rank=32,
        dtype="bfloat16",
        gpu_memory_utilization=0.85,
    )
    sampling = SamplingParams(temperature=0.0, max_tokens=2048)
    lora_req = LoRARequest("phase2v2run1", 1, a.lora)
    tok = llm.get_tokenizer()

    # === Build prompts ===
    prompts = []
    metadata = []
    for pid in ids:
        puz = puzzles[pid]
        system, user = build_prompt(puz)
        # Apply Qwen's chat template (same as training's tokenizer_default)
        prompt = tok.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True,
        )
        prompts.append(prompt)
        metadata.append({
            "puzzle": pid,
            "system": system,
            "user": user,
            "test_input": puz["test"][0]["input"],
            "expected_output": puz["test"][0]["output"],
        })

    # === Generate ===
    print(f"generating {len(prompts)} solvers (greedy, max_tokens=2048) ...")
    import time
    t0 = time.time()
    outputs = llm.generate(prompts, sampling, lora_request=lora_req)
    print(f"generated in {time.time()-t0:.1f}s")

    # === Verify + classify ===
    counts = {}
    with out_path.open("w") as fh:
        for meta, out_obj in zip(metadata, outputs):
            raw = out_obj.outputs[0].text
            code = extract_code(raw)
            expected = meta["expected_output"]
            expected_shape = (len(expected), len(expected[0]))
            run_result = run_code(code, meta["test_input"])
            mode = classify(code, run_result, expected, expected_shape)
            counts[mode] = counts.get(mode, 0) + 1
            rec = {
                "puzzle": meta["puzzle"],
                "bucket": 1,
                "prompt_system": meta["system"],
                "prompt_user": meta["user"],
                "model_output_raw": raw,
                "extracted_code": code,
                "test_input": meta["test_input"],
                "expected_output": expected,
                "got_output": run_result["output"],
                "failure_mode": mode,
            }
            fh.write(json.dumps(rec) + "\n")

    # === Report ===
    n = len(metadata)
    print(f"\n=== Bucket 1 results ({n} puzzles) ===")
    for mode in ("PASS", "WRONG_OUTPUT", "SHAPE_MISMATCH", "RUNTIME_ERROR",
                 "TIMEOUT", "EMPTY_OR_INVALID", "HARDCODED"):
        c = counts.get(mode, 0)
        bar = "█" * int(50 * c / n) if n else ""
        print(f"  {mode:18s} {c:4d}  ({100*c/n:5.1f}%)  {bar}")
    print()
    print(f"solve rate: {100*counts.get('PASS', 0)/n:.1f}%")
    print(f"results saved to: {out_path}")


if __name__ == "__main__":
    main()
