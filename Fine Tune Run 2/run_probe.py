#!/usr/bin/env python3
"""Phase 1 probe harness — per-format exact-match accuracy.

Loads a saved LoRA adapter on top of Qwen2.5-7B-Instruct, runs greedy
decode on the probe JSONL, computes exact-match accuracy grouped by
provenance.format, and writes a report + failed examples.

Usage:
    python3 "Fine Tune Run 2/run_probe.py" \\
        --adapter outputs/phase1a_substrate_literacy \\
        --probe   "Fine Tune Run 2/data_sft/phase1a_probe.jsonl"

    python3 "Fine Tune Run 2/run_probe.py" \\
        --adapter outputs/phase1b_rule_application \\
        --probe   "Fine Tune Run 2/data_sft/phase1b_probe.jsonl"

Outputs (next to the probe file):
    <stem>_probe_report.json    structured per-format metrics
    <stem>_probe_failures.jsonl one record per wrong prediction
                                (prompt + expected + got + provenance)

Decoding is greedy (temperature 0.0). Exact-match means the model's
generated tokens, after stripping leading/trailing whitespace, equal
the assistant target verbatim. Anything else is a failure.

Probe thresholds from SFT_Strategy.md §4.4:
    pair_to_substrate         same-size  >= 95%
    pair_to_substrate         diff-size  >= 90%
    substrate_to_output       (S only)   >= 95%
    all_pairs_to_substrates              >= 90%

For Phase 1.B, the same harness also reports the new formats:
    cold_pair_to_substrate
    test_substrate_prediction
    direct_output_grid
without baked-in thresholds (1.B is the rule-application stage, no
locked thresholds yet — read the absolute numbers).
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


# Probe thresholds — used to compute pass/fail per format. Missing
# format -> no pass/fail decision, just reported.
THRESHOLDS = {
    ("pair_to_substrate", "same_size"):       0.95,
    ("pair_to_substrate", "diff_size"):       0.90,
    ("substrate_to_output", "same_size"):     0.95,
    ("all_pairs_to_substrates", "any"):       0.90,
}


def is_same_size_record(record):
    """Detect whether the (puzzle, format) pair in a probe record is
    structurally same-size, by checking the assistant target. Pixel
    substrates are rectangular grids of single chars ('.' or 0-9);
    aggregate substrates start with 'SIZE '. Output grids are digit
    grids."""
    target = record["messages"][-1]["content"].strip()
    if target.startswith("SIZE "):
        return False
    # Otherwise assume same-size (pixel substrate or output grid).
    return True


def load_probe(probe_path: Path):
    records = []
    with probe_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def build_prompt(record, tokenizer):
    """Use the tokenizer's chat template to format the user message
    with the system prompt, leaving an open assistant turn for the
    model to complete."""
    msgs = record["messages"][:-1]  # drop assistant target
    return tokenizer.apply_chat_template(
        msgs,
        tokenize=False,
        add_generation_prompt=True,
    )


def exact_match(generated: str, target: str) -> bool:
    return generated.strip() == target.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True,
                    help="LoRA adapter dir, e.g. outputs/phase1a_substrate_literacy")
    ap.add_argument("--probe", type=Path, required=True,
                    help="Probe JSONL, e.g. data_sft/phase1a_probe.jsonl")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap records evaluated (debugging only).")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    if not args.adapter.exists():
        print(f"adapter dir not found: {args.adapter}", file=sys.stderr)
        sys.exit(1)
    if not args.probe.exists():
        print(f"probe file not found: {args.probe}", file=sys.stderr)
        sys.exit(1)

    # Heavy imports deferred so --help and arg parsing run without a
    # GPU/cuda toolchain installed.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"Loading base model: {args.base_model}…")
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model, trust_remote_code=True
    )
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map=args.device,
        trust_remote_code=True,
    )

    print(f"Attaching LoRA: {args.adapter}…")
    model = PeftModel.from_pretrained(base, args.adapter)
    model.eval()

    records = load_probe(args.probe)
    if args.limit:
        records = records[: args.limit]
    print(f"Evaluating {len(records)} probe records…")

    results_by_format = defaultdict(list)
    failures = []

    t0 = time.time()
    for i, record in enumerate(records):
        prompt = build_prompt(record, tokenizer)
        inputs = tokenizer(prompt, return_tensors="pt").to(args.device)

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=0.0,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Decode only the newly generated tokens.
        new_tokens = out[0, inputs["input_ids"].shape[1]:]
        generated = tokenizer.decode(new_tokens, skip_special_tokens=True)
        target = record["messages"][-1]["content"]

        ok = exact_match(generated, target)
        fmt = record["provenance"]["format"]
        size_kind = "same_size" if is_same_size_record(record) else "diff_size"
        key = (fmt, size_kind)
        results_by_format[key].append(ok)

        if not ok:
            failures.append({
                "provenance": record["provenance"],
                "size_kind":  size_kind,
                "prompt":     prompt,
                "expected":   target,
                "got":        generated,
            })

        if (i + 1) % 10 == 0 or i + 1 == len(records):
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(records)}]  {elapsed:.1f}s "
                  f"({(i+1)/elapsed:.2f} rec/s)")

    # Aggregate.
    report = {"adapter": str(args.adapter), "probe": str(args.probe),
              "n_records": len(records), "by_key": {}, "summary": {}}

    overall_correct = 0
    overall_total = 0
    pass_fail = {}
    for key, oks in sorted(results_by_format.items()):
        fmt, size_kind = key
        n = len(oks)
        c = sum(oks)
        acc = c / n
        overall_correct += c
        overall_total += n
        threshold = THRESHOLDS.get(key) or THRESHOLDS.get((fmt, "any"))
        passed = (threshold is not None) and (acc >= threshold)
        report["by_key"][f"{fmt}|{size_kind}"] = {
            "n": n, "correct": c, "exact_match": acc,
            "threshold": threshold, "passed": passed,
        }
        pass_fail[f"{fmt}|{size_kind}"] = passed if threshold is not None else None

    overall_acc = overall_correct / overall_total if overall_total else 0.0
    report["summary"]["overall_exact_match"] = overall_acc
    report["summary"]["overall_n"] = overall_total
    report["summary"]["overall_correct"] = overall_correct

    # Print human report.
    print("\n=== Phase probe report ===")
    print(f"Adapter:  {args.adapter}")
    print(f"Probe:    {args.probe}")
    print(f"Overall:  {overall_correct}/{overall_total} = {overall_acc*100:.1f}%")
    print()
    print(f"{'format|size':40s} {'n':>5s} {'correct':>8s} {'acc':>7s} "
          f"{'thresh':>7s} {'pass':>5s}")
    for key, oks in sorted(results_by_format.items()):
        fmt, size_kind = key
        n = len(oks)
        c = sum(oks)
        acc = c / n
        threshold = THRESHOLDS.get(key) or THRESHOLDS.get((fmt, "any"))
        thr_str = f"{threshold*100:.0f}%" if threshold else "  —  "
        pass_str = "—"
        if threshold is not None:
            pass_str = "PASS" if acc >= threshold else "FAIL"
        print(f"{fmt+'|'+size_kind:40s} {n:5d} {c:8d} {acc*100:6.1f}% "
              f"{thr_str:>7s} {pass_str:>5s}")
    print()

    all_decisions = [v for v in pass_fail.values() if v is not None]
    if all_decisions:
        if all(all_decisions):
            print("Verdict: ALL THRESHOLDS PASSED — stage can be considered done.")
        else:
            failed = [k for k, v in pass_fail.items() if v is False]
            print(f"Verdict: FAIL on {len(failed)} format(s): {failed}")

    # Persist.
    report_path = args.probe.with_name(args.probe.stem + "_probe_report.json")
    failures_path = args.probe.with_name(args.probe.stem + "_probe_failures.jsonl")
    report_path.write_text(json.dumps(report, indent=2))
    with failures_path.open("w") as f:
        for fail in failures:
            f.write(json.dumps(fail, ensure_ascii=False) + "\n")
    print(f"\nWrote {report_path.name} and {failures_path.name} "
          f"({len(failures)} failures)")


if __name__ == "__main__":
    main()
