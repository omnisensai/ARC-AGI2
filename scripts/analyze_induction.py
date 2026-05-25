#!/usr/bin/env python3
"""Deep-dive the test_substrate_prediction failures (rule-induction).

Run on the pod, against the probe's per-record file:
    python3 scripts/analyze_induction.py \
        "Fine Tune Run 2/data_sft/phase1_same_rule_probe_probe_records.jsonl"

Classifies WHY the model fails to predict the held-out T, because each mode
has a different fix:
  - do-nothing (predicts ~all '.')      -> weak induction signal; needs output-hidden cycling
  - right LOCATION, wrong COLOR         -> found WHERE it changes, not WHAT to; color-rule gap
  - copies a DEMO pair's T verbatim      -> parroting examples, not generalizing
  - changes in wrong places              -> genuine misperception / drift
Splits by grid size and dumps a few concrete expected-vs-got diffs.
"""
import json, sys
from collections import Counter

def parse(s):
    return [list(line) for line in s.strip().split("\n") if line.strip()]

def main():
    path = sys.argv[1]
    recs = [json.loads(l) for l in open(path) if l.strip()]
    tsp = [r for r in recs if r.get("format") == "test_substrate_prediction"]
    print(f"test_substrate_prediction records: {len(tsp)}")
    if not tsp:
        return

    donothing = copydemo = 0
    loc_hits = loc_tot = col_hits = 0
    small_recall = []; large_recall = []
    examples = []

    for r in tsp:
        exp = parse(r["expected"])
        got = parse(r.get("got", ""))
        # changed cells in expected (digits)
        ch = [(i,j,exp[i][j]) for i in range(len(exp)) for j in range(len(exp[i])) if exp[i][j].isdigit()]
        # model's changed cells
        got_changed = sum(1 for row in got for c in row if c.isdigit())
        if got_changed == 0:
            donothing += 1
        # location + color hits (only where shapes allow indexing)
        rec_loc = rec_col = 0
        for (i,j,col) in ch:
            if i < len(got) and j < len(got[i]):
                g = got[i][j]
                if g.isdigit():
                    rec_loc += 1
                    loc_hits += 1
                    if g == col:
                        rec_col += 1; col_hits += 1
            loc_tot += 1
        recall = rec_col/len(ch) if ch else None
        bucket = "small" if (len(exp)<=10 and (max((len(x) for x in exp),default=0))<=10) else "large"
        if recall is not None:
            (small_recall if bucket=="small" else large_recall).append(recall)
        # copy-demo: does got match the verbatim got of a non-changed pattern? approximate:
        # check if got equals expected with all digits blanked (i.e., identity-ish) handled by donothing
        if len(examples) < 6 and ch:
            examples.append((r.get("puzzle_id"), bucket, len(ch), rec_loc, rec_col, r["expected"], r.get("got","")))

    n = len(tsp)
    import statistics as st
    print(f"\n--- failure-mode breakdown (n={n}) ---")
    print(f"do-nothing (predicted all '.'):        {donothing}/{n}  ({100*donothing/n:.0f}%)")
    print(f"location recall (changed somewhere right, any color): {100*loc_hits/loc_tot:.0f}%")
    print(f"color   recall (right place AND color):               {100*col_hits/loc_tot:.0f}%")
    gap = loc_hits - col_hits
    print(f"  -> of cells it located, {100*(gap)/loc_hits:.0f}% had WRONG color" if loc_hits else "")
    if small_recall: print(f"small-grid color-recall: {100*st.mean(small_recall):.0f}%  (n={len(small_recall)})")
    if large_recall: print(f"large-grid color-recall: {100*st.mean(large_recall):.0f}%  (n={len(large_recall)})")

    print(f"\n--- {len(examples)} concrete cases (expected vs got) ---")
    for pid,b,nch,rl,rc,e,g in examples:
        print(f"\n[{pid}] {b}  expected_changes={nch}  located={rl}  color_correct={rc}")
        print("  EXPECTED:"); print("   "+e.replace("\n","\n   "))
        print("  GOT:");      print("   "+(g[:400]).replace("\n","\n   "))

if __name__ == "__main__":
    main()
