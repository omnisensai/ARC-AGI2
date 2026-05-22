#!/usr/bin/env python3
"""Verify the byte-level invariants of Phase 1 SFT records.

Run after `build_phase1_dataset.py` (or anytime you suspect format
drift). Exits non-zero on the first violation. Operates on the
committed .jsonl.gz / .jsonl files.

Invariants enforced (from SFT_Strategy.md §7.5):

  S1  system content is literally "Transformation Rule"
  S2  messages array is exactly [system, user, assistant]
  S3  no Qwen2 special tokens in any content
       (<|im_start|>, <|im_end|>, <|object_ref_start|> etc.)
  U1  user content ends with `LABEL:\\n` (a trailing label + newline)
  U2  no trailing space on any line of the user content
  U3  no triple-newline ("\\n\\n\\n") anywhere
  A1  assistant content is non-empty
  A2  no leading/trailing whitespace on the assistant content
  P1  provenance.format is one of the known 6 formats
  P2  provenance has the required keys

Usage:
    python3 "Fine Tune Run 2/verify_records.py"
"""
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_sft"

FILES = [
    DATA / "phase1a_train.jsonl.gz",
    DATA / "phase1a_dev.jsonl",
    DATA / "phase1a_probe.jsonl",
    DATA / "phase1b_train.jsonl.gz",
    DATA / "phase1b_dev.jsonl",
    DATA / "phase1b_probe.jsonl",
]

KNOWN_FORMATS = {
    "pair_to_substrate",
    "substrate_to_output",
    "multi_pair_to_rule",
    "test_substrate_prediction",
    "direct_output_grid",
}

# Mirror of build_phase1_dataset.py SYSTEM_MESSAGE. Must stay in sync.
EXPECTED_SYSTEM_MESSAGE = """Transformation Rule

A RULE encodes one (input, output) transformation pair.

When input.shape == output.shape, the RULE is a same-shape grid:
  .       cell unchanged
  0-9     cell took this new color

When input.shape != output.shape, the RULE is an aggregate text block
with fixed sections in order: SIZE, BG, PALETTE, ROWS, COLS, BBOX.
Sections are separated by blank lines.

Tags between numeric pairs a -> b:
  =        a == b
  ×N       b = a*N  (integer N > 1)
  ÷N       a = b*N  (integer N > 1)
  Δ±N      additive offset
  new      a == 0, b > 0
  dropped  a > 0, b == 0"""

REQUIRED_PROV_KEYS = {"format", "stage", "bucket", "puzzle_id",
                      "sources", "d4_op", "color_perm_seed",
                      "pair_subset"}

QWEN_SPECIAL_RE = re.compile(r"<\|im_(start|end)\|>|<\|object_ref_(start|end)\|>|"
                             r"<\|box_(start|end)\|>|<\|quad_(start|end)\|>|"
                             r"<\|endoftext\|>")

TRAILING_LABEL_RE = re.compile(r"\n?[A-Z][A-Z0-9 _]*:\n$")


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
                  f"messages length is {len(msgs) if isinstance(msgs, list) else None}, want 3",
                  rec)

    sys_msg, user_msg, asst_msg = msgs
    if sys_msg.get("role") != "system" or sys_msg.get("content") != EXPECTED_SYSTEM_MESSAGE:
        violation(file, line_no, "S1",
                  f"system content does not match EXPECTED_SYSTEM_MESSAGE "
                  f"(role={sys_msg.get('role')!r}, "
                  f"first 60 chars: {sys_msg.get('content', '')[:60]!r})",
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
                      f"qwen2 special token inside {label} content", rec)

    user = user_msg["content"]
    if not TRAILING_LABEL_RE.search(user):
        violation(file, line_no, "U1",
                  f"user content does not end with a trailing 'LABEL:\\n' "
                  f"(tail repr: {user[-40:]!r})", rec)
    for ln_idx, ln in enumerate(user.split("\n")):
        if ln != ln.rstrip(" "):
            violation(file, line_no, "U2",
                      f"trailing space on user line {ln_idx}: {ln!r}", rec)
    if "\n\n\n" in user:
        violation(file, line_no, "U3", "triple-newline in user content", rec)

    asst = asst_msg["content"]
    if not asst:
        violation(file, line_no, "A1", "assistant content empty", rec)
    if asst != asst.strip() and asst.strip() != "":
        # Only flag if stripping changed it AND non-empty
        if asst.startswith((" ", "\n", "\t")) or asst.endswith((" ", "\n", "\t")):
            violation(file, line_no, "A2",
                      f"assistant has leading/trailing whitespace "
                      f"(head={asst[:30]!r} tail={asst[-30:]!r})", rec)

    prov = rec.get("provenance")
    if not isinstance(prov, dict):
        violation(file, line_no, "P2", "provenance missing or not a dict", rec)
    missing = REQUIRED_PROV_KEYS - set(prov.keys())
    if missing:
        violation(file, line_no, "P2", f"provenance missing keys: {missing}", rec)
    if prov["format"] not in KNOWN_FORMATS:
        violation(file, line_no, "P1",
                  f"unknown format {prov['format']!r}", rec)


def main():
    total_records = 0
    for file in FILES:
        if not file.exists():
            print(f"SKIP {file.name} (does not exist)")
            continue
        file_count = 0
        for i, rec in open_records(file):
            check_record(rec, file, i)
            file_count += 1
        total_records += file_count
        print(f"OK   {file.name}: {file_count} records")
    print(f"\nAll invariants hold across {total_records} records.")


if __name__ == "__main__":
    main()
