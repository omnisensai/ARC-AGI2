"""Convert Run 1 SFT records to axolotl chat format.

Input: Phase2_V2/canonical/sft/real_samesize_{original,augmented_shard0[0-3]}.jsonl
       Each line: {"system": str, "user": str, "assistant": str, "meta": {...}}

Output: Phase2_V2/run1/data_sft/run1_train.jsonl.gz
       Each line: {"messages": [
           {"role": "system",    "content": ...},
           {"role": "user",      "content": ...},
           {"role": "assistant", "content": ...},
       ]}

Also FILTERS OUT records whose meta.puzzle is in the held-out splits
(defensive — the corpus should already be clean, but this guarantees no leak).

Run from repo root:
    python3 Phase2_V2/run1/prepare_dataset.py
"""
import gzip, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # ARC-AGI2/
P2 = REPO / "Phase2_V2"

SRC_FILES = [
    P2 / "canonical/sft/real_samesize_original.jsonl",
    P2 / "canonical/sft/real_samesize_augmented_shard00.jsonl",
    P2 / "canonical/sft/real_samesize_augmented_shard01.jsonl",
    P2 / "canonical/sft/real_samesize_augmented_shard02.jsonl",
    P2 / "canonical/sft/real_samesize_augmented_shard03.jsonl",
]
HELDOUT_FILES = [
    P2 / "run1/splits/bucket2_heldout_samesize.txt",
    P2 / "run1/splits/bucket3_cold_diffsize.txt",
]
DST = P2 / "run1/data_sft/run1_train.jsonl.gz"


def main():
    held = set()
    for p in HELDOUT_FILES:
        held |= {line.strip() for line in p.read_text().split() if line.strip()}
    print(f"held-out puzzle ids: {len(held)}")

    DST.parent.mkdir(parents=True, exist_ok=True)
    n_in = n_out = n_skipped_heldout = 0
    with gzip.open(DST, "wt") as fh:
        for src in SRC_FILES:
            n_src = 0
            for line in src.read_text().splitlines():
                if not line.strip():
                    continue
                n_in += 1; n_src += 1
                rec = json.loads(line)
                if rec["meta"]["puzzle"] in held:
                    n_skipped_heldout += 1
                    continue
                out = {"messages": [
                    {"role": "system",    "content": rec["system"]},
                    {"role": "user",      "content": rec["user"]},
                    {"role": "assistant", "content": rec["assistant"]},
                ]}
                fh.write(json.dumps(out) + "\n")
                n_out += 1
            print(f"  {src.name}: {n_src} read")

    print()
    print(f"records read:    {n_in}")
    print(f"held-out skips:  {n_skipped_heldout}  (expected 0; corpus is pre-filtered)")
    print(f"records written: {n_out}  ->  {DST}")
    print(f"file size:       {DST.stat().st_size / 1024 / 1024:.1f} MB (gzipped)")


if __name__ == "__main__":
    main()
