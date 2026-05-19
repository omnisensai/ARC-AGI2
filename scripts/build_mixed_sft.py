"""Build a mixed-curriculum SFT dataset from our actual data_sft/ files.

Reads:
  data_sft/phase1_train.jsonl.gz  -> A, B, H, M, C  (filter by 'task' field)
  data_sft/phase2_train.jsonl      -> D
  data_sft/phase3_train.jsonl      -> E

Writes:
  data_sft/mixed_arc_sft_train.jsonl

Mix (revised for rule-selection bottleneck, not code-gen):
  A:10%  B:10%  H:8%  M:22%  C:18%  D:8%  E:24%
"""
import gzip
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data_sft"
OUT = DATA / "mixed_arc_sft_train.jsonl"

# Map our internal task names -> single-letter tag
TASK_TO_TAG = {
    "phase1a": "A",
    "phase1b": "B",
    "phase1a_hierarchy": "H",
    "phase1_multi_pair": "M",
    "phase1_substrate_to_code": "C",
    "phase2": "D",
    "phase3": "E",
}

TARGET_COUNTS = {
    "A": 7000,
    "B": 7000,
    "H": 5600,
    "M": 15400,
    "C": 12600,
    "D": 5600,
    "E": 16800,
}


def open_jsonl(path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def load_by_tag():
    """Read all training records, bucket by single-letter tag."""
    by_tag = defaultdict(list)
    for path in [DATA / "phase1_train.jsonl.gz",
                 DATA / "phase2_train.jsonl",
                 DATA / "phase3_train.jsonl"]:
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}")
        with open_jsonl(path) as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                tag = TASK_TO_TAG.get(d.get("task"))
                if tag is None:
                    continue
                by_tag[tag].append(d)
    return by_tag


def sample_or_repeat(rows, n, rng):
    if len(rows) >= n:
        return rng.sample(rows, n)
    out = []
    while len(out) < n:
        batch = rows[:]
        rng.shuffle(batch)
        out.extend(batch)
    return out[:n]


def validate(row):
    assert "messages" in row, f"missing messages: {row}"
    assert len(row["messages"]) == 3
    assert row["messages"][0]["role"] == "system"
    assert row["messages"][1]["role"] == "user"
    assert row["messages"][2]["role"] == "assistant"
    assert row["messages"][0]["content"] in {"A", "B", "H", "M", "C", "D", "E"}


def main():
    rng = random.Random(42)
    by_tag = load_by_tag()
    print("Source counts by tag:")
    for tag in "ABHMCDE":
        print(f"  {tag}: {len(by_tag[tag]):>7,}")

    mixed = []
    for tag in "ABHMCDE":
        rows = by_tag[tag]
        if not rows:
            print(f"  WARN: no records for tag {tag}, skipping")
            continue
        for r in rows[:5]:
            validate(r)
        chosen = sample_or_repeat(rows, TARGET_COUNTS[tag], rng)
        mixed.extend(chosen)
        print(f"  {tag}: chose {len(chosen):,} from pool of {len(rows):,}")

    rng.shuffle(mixed)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in mixed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    total = len(mixed)
    final = Counter(r["messages"][0]["content"] for r in mixed)
    print(f"\nWrote {total:,} rows to {OUT}")
    print("Final mix:")
    for tag, cnt in sorted(final.items()):
        print(f"  {tag}: {cnt:>7,}  ({100*cnt/total:.1f}%)")


if __name__ == "__main__":
    main()
