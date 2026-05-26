#!/usr/bin/env python3
"""Dump test_substrate_prediction cases to a readable markdown for granular
manual review (prompt the model saw + expected T + got T + per-cell metrics).

The failures file has the full prompt (demos + test input); the records file
has every case + metrics. We join on puzzle_id and emit one section per case.

Run on the pod:
    python3 scripts/dump_induction_cases.py
writes: Fine Tune Run 2/data_sft/same_rule_induction_cases.md
"""
import json, os

BASE = "Fine Tune Run 2/data_sft"
REC = f"{BASE}/phase1_same_rule_probe_probe_records.jsonl"
FAIL = f"{BASE}/phase1_same_rule_probe_probe_failures.jsonl"
OUT = f"{BASE}/same_rule_induction_cases.md"

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]

def main():
    recs = [r for r in load(REC) if r.get("format") == "test_substrate_prediction"]
    fails = {}
    for f in load(FAIL):
        if f.get("provenance", {}).get("format") == "test_substrate_prediction":
            fails.setdefault(f["provenance"].get("puzzle_id"), []).append(f)

    out = ["# same_rule — test_substrate_prediction cases (granular review)\n",
           f"{len(recs)} cases. Each shows the PROMPT the model saw (train pairs + test "
           "input), the EXPECTED held-out T, and the model's GOT T.\n"]
    for i, r in enumerate(recs):
        pid = r.get("puzzle_id")
        out.append(f"\n\n## case {i+1} — puzzle {pid}  ({r.get('bucket')})")
        out.append(f"exact={r.get('exact')}  cell={r.get('cell_accuracy'):.2f}  "
                   f"changed_recall={r.get('changed_cell_recall')}  "
                   f"changed_prec={r.get('changed_cell_precision')}")
        # prompt (from failures file if present)
        fl = fails.get(pid)
        if fl:
            prompt = fl[0].get("prompt", "")
            # strip the chat-template scaffolding for readability — keep the user turn
            u = prompt
            if "<|im_start|>user" in prompt:
                u = prompt.split("<|im_start|>user", 1)[1]
                u = u.split("<|im_end|>", 1)[0]
            out.append("\n**PROMPT (train pairs + test input):**\n```\n" + u.strip() + "\n```")
        out.append("\n**EXPECTED T:**\n```\n" + r.get("expected", "").strip() + "\n```")
        out.append("\n**GOT T:**\n```\n" + r.get("got", "").strip() + "\n```")
    open(OUT, "w").write("\n".join(out))
    print(f"wrote {OUT}  ({len(recs)} cases)")

if __name__ == "__main__":
    main()
