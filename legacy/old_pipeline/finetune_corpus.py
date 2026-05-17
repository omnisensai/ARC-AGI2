"""Fine-tuning corpus: collect (code, label, metadata) records for SFT/DPO.

Three buckets keyed by failure mode:
- wrong_training.jsonl: training pairs failed (>=1 of N training pairs wrong)
- wrong_test.jsonl: training passed but test failed (NEAR_MISS or FCS)
- correct.jsonl: TRUE_SOLVE (training passed AND every test pair exact)

Records are idempotent on (puzzle_id, model, n): re-running paste_helper
on the same iter overwrites that record and migrates it across buckets if its
label changed.

Per-puzzle .py mirrors live under by_puzzle/<puzzle>/<bucket>.py so a human
can scan one file to see every wrong attempt and every correct solver on a
given puzzle side by side.

Comp-clean: records include test_diff_total only when the puzzle file
carries test ground truth (evaluation / practice mode). In real competition
the puzzle file lacks `test[i].output`, classify() returns None (we can't
distinguish wrong_test from correct without ground truth), and the record is
not appended.
"""

import json
from pathlib import Path


CORPUS_ROOT = Path("research/finetune_corpus")
BUCKETS = ("wrong_training", "wrong_test", "correct")


def classify(training_pass, training_total, test_diff_total):
    """Return one of the bucket names, or None if the attempt is unclassifiable.

    None is returned when training was not fully evaluated (training_total=0)
    or when training passed but no test ground truth is available — the latter
    is the real-competition case where we genuinely cannot label.
    """
    if training_total == 0:
        return None
    if training_pass < training_total:
        return "wrong_training"
    if test_diff_total is None:
        return None
    if test_diff_total == 0:
        return "correct"
    return "wrong_test"


def _key(puzzle_id, model, n):
    return f"{puzzle_id}__{model}__R{n}"


def _read_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _write_jsonl(path, records):
    if not records:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def build_record(puzzle_id, model, n, code, stated_rule,
                 training_pass, training_total, training_diff_total,
                 test_diff_total, test_label, source_path):
    """Construct a record dict ready for append_record, or None if unclassifiable."""
    label = classify(training_pass, training_total, test_diff_total)
    if label is None:
        return None
    return {
        "puzzle_id": puzzle_id,
        "model": model,
        "n": n,
        "label": label,
        "training_pass": training_pass,
        "training_total": training_total,
        "training_diff_total": training_diff_total,
        "test_diff_total": test_diff_total,
        "test_label": test_label,
        "stated_rule": stated_rule,
        "code": code,
        "source": source_path,
    }


def append_record(record, corpus_root=None):
    """Insert record into its bucket; remove same-key records from other buckets.

    Idempotent on (puzzle_id, model, iter): a re-run of paste_helper on the
    same iter replaces the prior record rather than duplicating. If the
    label changed (e.g., iter N was wrong_training, the model later passed
    on the same iter — unlikely but possible if a code path is rewritten),
    the record migrates: the new bucket gets the record, all other buckets
    drop any matching key.
    """
    root = Path(corpus_root) if corpus_root else CORPUS_ROOT
    bucket = record["label"]
    if bucket is None:
        return None
    key = _key(record["puzzle_id"], record["model"], record["n"])

    for other in BUCKETS:
        path = root / f"{other}.jsonl"
        recs = _read_jsonl(path)
        filtered = [r for r in recs if _key(r["puzzle_id"], r["model"], r["n"]) != key]
        if other == bucket:
            filtered.append(record)
        if filtered != recs:
            _write_jsonl(path, filtered)

    _rebuild_py_mirror(record["puzzle_id"], root=root)
    return str(root / f"{bucket}.jsonl")


def _rebuild_py_mirror(puzzle_id, root=None):
    """Rebuild every bucket's .py mirror for one puzzle from its JSONL files.

    Cheap: we read each bucket's JSONL, filter to this puzzle, rewrite the
    .py. Keeps the mirrors strictly consistent with the JSONL.
    """
    root = Path(root) if root else CORPUS_ROOT
    py_dir = root / "by_puzzle" / puzzle_id
    py_dir.mkdir(parents=True, exist_ok=True)

    for bucket in BUCKETS:
        jsonl_path = root / f"{bucket}.jsonl"
        records = [r for r in _read_jsonl(jsonl_path) if r["puzzle_id"] == puzzle_id]
        records.sort(key=lambda r: (r["model"], r["n"]))
        py_path = py_dir / f"{bucket}.py"
        if not records:
            if py_path.exists():
                py_path.unlink()
            continue
        parts = [
            f'"""Fine-tuning mirror: {puzzle_id} / {bucket}.\n\n'
            f'Auto-generated from {jsonl_path.name}. Each entry below is one\n'
            f'attempt with metadata in the comment header.\n"""\n'
        ]
        for r in records:
            header = (
                "# " + "=" * 70 + "\n"
                f"# {r['model']} R{r['n']} -- {bucket}\n"
                f"# training_pass={r['training_pass']}/{r['training_total']}  "
                f"training_diff_total={r.get('training_diff_total')}  "
                f"test_diff_total={r.get('test_diff_total')}  "
                f"test_label={r.get('test_label')}\n"
                f"# stated_rule: {r.get('stated_rule') or '(none)'}\n"
                f"# source: {r.get('source')}\n"
                "# " + "=" * 70 + "\n"
            )
            parts.append(header + (r["code"].rstrip() if r.get("code") else "") + "\n")
        py_path.write_text("\n\n".join(parts))


def compute_training_stats(solve_module, train_pairs):
    """Run solve() on every training pair; return (pass_count, diff_total)."""
    pass_count = 0
    diff_total = 0
    for pair in train_pairs:
        try:
            out = solve_module.solve(pair["input"])
        except Exception:
            return pass_count, None
        truth = pair["output"]
        if not isinstance(out, list) or not out or not isinstance(out[0], list):
            return pass_count, None
        if len(out) != len(truth) or any(
            len(out[r]) != len(truth[r]) for r in range(len(truth))
        ):
            diff_total += len(truth) * len(truth[0])
            continue
        d = sum(
            1 for r in range(len(truth)) for c in range(len(truth[0]))
            if out[r][c] != truth[r][c]
        )
        diff_total += d
        if d == 0:
            pass_count += 1
    return pass_count, diff_total
