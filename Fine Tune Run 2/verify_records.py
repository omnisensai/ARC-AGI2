#!/usr/bin/env python3
"""Verify the byte-level invariants of Phase 1 SFT records.

Runs against the committed .jsonl / .jsonl.gz files for all three
stages (same / diff / mixed). Exits non-zero on the first violation.

Invariants enforced:

  S1  system content matches the expected system message FOR THIS
      RECORD'S STAGE (provenance.stage_key in {same, diff, mixed})
  S2  messages array is exactly [system, user, assistant]
  S3  no Qwen2 special tokens in any content
  U1  user content ends with `LABEL:\\n` (a trailing label + newline)
  U2  no trailing space on any line of the user content
  U3  no triple-newline ("\\n\\n\\n") anywhere
  A1  assistant content is non-empty
  A2  no leading/trailing whitespace on the assistant content
  P1  provenance.format is one of the known formats
  P2  provenance has the required keys
  P3  provenance.substrate_type matches the stage filter
       (same -> "same", diff -> "diff", mixed -> "same" or "diff")
"""
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_sft"

FILES = [
    DATA / "phase1_lit_train.jsonl.gz",
    DATA / "phase1_lit_probe.jsonl",
    DATA / "phase1_same_train.jsonl.gz",
    DATA / "phase1_same_probe.jsonl",
    DATA / "phase1_diff_train.jsonl.gz",
    DATA / "phase1_diff_probe.jsonl",
    DATA / "phase1_mixed_train.jsonl.gz",
    DATA / "phase1_mixed_probe.jsonl",
]

KNOWN_FORMATS = {
    "pair_to_substrate",
    "substrate_to_output",
    "multi_pair_to_rule",
    "test_substrate_prediction",
    "direct_output_grid",
}

REQUIRED_PROV_KEYS = {"format", "stage", "stage_key", "bucket", "puzzle_id",
                      "sources", "substrate_type", "d4_op",
                      "color_perm_seed", "pair_subset"}

QWEN_SPECIAL_RE = re.compile(
    r"<\|im_(start|end)\|>|<\|object_ref_(start|end)\|>|"
    r"<\|box_(start|end)\|>|<\|quad_(start|end)\|>|"
    r"<\|endoftext\|>"
)

TRAILING_LABEL_RE = re.compile(r"\n?[A-Z][A-Z0-9 _]*:\n$")


# Mirror of build_phase1_dataset.py SYSTEM_MESSAGE_BY_STAGE. Must stay
# in sync.

EXPECTED_SAME = """Encode the transformation from INPUT to OUTPUT as a T grid. Each cell
is an atomic unit colored 0-9.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T."""

EXPECTED_DIFF = """Encode the transformation from INPUT to OUTPUT as a T grid. Each cell
is an atomic unit colored 0-9.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T.

T grid legend when INPUT and OUTPUT have different dimensions
(e.g. 3x3 -> 2x4):
T is an aggregate text block with these sections in fixed order,
separated by blank lines:
  SIZE     overall dimensions:  H x W -> h x w  with relation tags
  BG       background color:  in_bg -> out_bg  with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)
Whole-grid statistics — diagnostic only, not lossless. No per-cell
decoder.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0"""

EXPECTED_MIXED = """ARC-AGI puzzle contains INPUT/OUTPUT grid pairs where each cell is an
atomic unit colored 0-9. There is exactly one transformation rule that
generalizes across all input/output pairs of a puzzle. The rule is
encoded in T grids — one T per pair, and the underlying rule is the
same across all of them.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T.

T grid legend when INPUT and OUTPUT have different dimensions
(e.g. 3x3 -> 2x4):
T is an aggregate text block with these sections in fixed order,
separated by blank lines:
  SIZE     overall dimensions:  H x W -> h x w  with relation tags
  BG       background color:  in_bg -> out_bg  with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)
Whole-grid statistics — diagnostic only, not lossless. No per-cell
decoder.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0"""

# LIT stage shares the DIFF prompt (both alphabets, no puzzle framing).
EXPECTED_LIT = EXPECTED_DIFF

EXPECTED_BY_STAGE = {
    "lit":   EXPECTED_LIT,
    "same":  EXPECTED_SAME,
    "diff":  EXPECTED_DIFF,
    "mixed": EXPECTED_MIXED,
}


def violation(file, line_no, code, detail, record):
    print(f"\nFAIL {file.name}:{line_no} [{code}] {detail}")
    print(f"  provenance: {record.get('provenance', {})}")
    raise SystemExit(1)


def open_records(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            yield i, json.loads(line)


def check_record(rec, file, line_no):
    msgs = rec.get("messages")
    if not isinstance(msgs, list) or len(msgs) != 3:
        violation(file, line_no, "S2",
                  f"messages length is {len(msgs) if isinstance(msgs, list) else None}",
                  rec)

    sys_msg, user_msg, asst_msg = msgs

    prov = rec.get("provenance")
    if not isinstance(prov, dict):
        violation(file, line_no, "P2", "provenance missing", rec)
    missing = REQUIRED_PROV_KEYS - set(prov.keys())
    if missing:
        violation(file, line_no, "P2", f"provenance missing keys: {missing}", rec)
    if prov["format"] not in KNOWN_FORMATS:
        violation(file, line_no, "P1", f"unknown format {prov['format']!r}", rec)

    stage_key = prov.get("stage_key")
    if stage_key not in EXPECTED_BY_STAGE:
        violation(file, line_no, "P2",
                  f"unknown stage_key {stage_key!r}", rec)

    if sys_msg.get("role") != "system" or sys_msg.get("content") != EXPECTED_BY_STAGE[stage_key]:
        violation(file, line_no, "S1",
                  f"system content does not match expected for stage "
                  f"{stage_key!r} (first 80 chars: "
                  f"{sys_msg.get('content', '')[:80]!r})",
                  rec)
    if user_msg.get("role") != "user":
        violation(file, line_no, "S2", "messages[1].role != user", rec)
    if asst_msg.get("role") != "assistant":
        violation(file, line_no, "S2", "messages[2].role != assistant", rec)

    for label, content in (("system", sys_msg["content"]),
                           ("user",   user_msg["content"]),
                           ("asst",   asst_msg["content"])):
        if QWEN_SPECIAL_RE.search(content):
            violation(file, line_no, "S3",
                      f"qwen2 special token inside {label}", rec)

    user = user_msg["content"]
    if not TRAILING_LABEL_RE.search(user):
        violation(file, line_no, "U1",
                  f"user content lacks trailing 'LABEL:\\n' "
                  f"(tail: {user[-40:]!r})", rec)
    for ln_idx, ln in enumerate(user.split("\n")):
        if ln != ln.rstrip(" "):
            violation(file, line_no, "U2",
                      f"trailing space on user line {ln_idx}: {ln!r}", rec)
    if "\n\n\n" in user:
        violation(file, line_no, "U3", "triple-newline in user content", rec)

    asst = asst_msg["content"]
    if not asst:
        violation(file, line_no, "A1", "assistant content empty", rec)
    if asst.startswith((" ", "\n", "\t")) or asst.endswith((" ", "\n", "\t")):
        violation(file, line_no, "A2",
                  f"assistant has leading/trailing whitespace", rec)

    # P3: substrate_type must match stage filter
    sub_type = prov.get("substrate_type")
    if stage_key == "same" and sub_type != "same":
        violation(file, line_no, "P3",
                  f"same-stage record has substrate_type {sub_type!r}", rec)
    if stage_key == "diff" and sub_type != "diff":
        violation(file, line_no, "P3",
                  f"diff-stage record has substrate_type {sub_type!r}", rec)
    if stage_key in ("lit", "mixed") and sub_type not in ("same", "diff"):
        violation(file, line_no, "P3",
                  f"{stage_key}-stage record has bad substrate_type "
                  f"{sub_type!r}", rec)


def main():
    total = 0
    for file in FILES:
        if not file.exists():
            print(f"SKIP {file.name} (does not exist)")
            continue
        n = 0
        for i, rec in open_records(file):
            check_record(rec, file, i)
            n += 1
        total += n
        print(f"OK   {file.name}: {n} records")
    print(f"\nAll invariants hold across {total} records.")


if __name__ == "__main__":
    main()
