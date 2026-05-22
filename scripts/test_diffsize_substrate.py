"""Verify diffsize_encode against the three examples in the v2 spec.

Run:
    python3 scripts/test_diffsize_substrate.py

Exits non-zero on any assertion failure.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from substrate import diffsize_encode, encode_auto, encode, relate


def grid(s):
    return [[int(c) for c in row] for row in s.strip().splitlines()]


def assert_contains(sub, needles, label):
    missing = [n for n in needles if n not in sub]
    if missing:
        print(f"--- {label} ---")
        print(sub)
        print(f"\nMISSING substrings: {missing!r}")
        raise SystemExit(1)


def check_example_1():
    inp = grid("""
00000
02200
02200
00000
""")
    out = grid("""
22
22
""")
    s = diffsize_encode(inp, out)
    print("=" * 80)
    print("EXAMPLE 1 — crop-like (4x5 -> 2x2)")
    print(s)
    assert_contains(
        s,
        [
            "SIZE 4x5 -> 2x2   h:÷2 w:Δ-3",
            "BG 0 -> 2   new",
            "PALETTE",
            "  0 16 -> 0 dropped",
            "  2 4 -> 4 =",
            "ROWS",
            "  IN_DOM:  0 2 2 0",
            "  OUT_DOM: 2 2",
            "  IN_NZ:   0 2 2 0",
            "  OUT_NZ:  0 0",
            "COLS",
            "  IN_DOM:  0 2 2 0 0",
            "  OUT_DOM: 2 2",
            "  IN_NZ:   0 2 2 0 0",
            "  OUT_NZ:  0 0",
            "BBOX",
            "  0 in:r0-3,c0-4 out:none",
            "  2 in:r1-2,c1-2 out:r0-1,c0-1",
        ],
        "example 1",
    )


def check_example_2():
    inp = grid("""
79
43
""")
    out = grid("""
797979
434343
797979
434343
797979
434343
""")
    s = diffsize_encode(inp, out)
    print("=" * 80)
    print("EXAMPLE 2 — tiling-like (2x2 -> 6x6)")
    print(s)
    assert_contains(
        s,
        [
            "SIZE 2x2 -> 6x6   h:×3 w:×3",
            "PALETTE",
            "  3 1 -> 9 ×9",
            "  4 1 -> 9 ×9",
            "  7 1 -> 9 ×9",
            "  9 1 -> 9 ×9",
        ],
        "example 2",
    )


def check_example_3():
    inp = grid("""
000
050
000
""")
    out = grid("""
5
""")
    s = diffsize_encode(inp, out)
    print("=" * 80)
    print("EXAMPLE 3 — scalar selection (3x3 -> 1x1)")
    print(s)
    assert_contains(
        s,
        [
            "SIZE 3x3 -> 1x1   h:÷3 w:÷3",
            "PALETTE",
            "  0 8 -> 0 dropped",
            "  5 1 -> 1 =",
            "BBOX",
            "  5 in:r1-1,c1-1 out:r0-0,c0-0",
        ],
        "example 3",
    )


def check_dispatch_and_domain_rules():
    same_in = grid("00\n00")
    same_out = grid("00\n01")
    result = encode_auto(same_in, same_out)
    assert isinstance(result, list), f"same-size encode_auto should return Substrate, got {type(result)}"
    assert encode(same_in, same_out) == result

    diff_in = grid("00\n00")
    diff_out = grid("0")
    result = encode_auto(diff_in, diff_out)
    assert isinstance(result, str), f"diff-size encode_auto should return str, got {type(result)}"

    try:
        diffsize_encode(same_in, same_out)
    except ValueError:
        pass
    else:
        raise AssertionError("diffsize_encode must raise on same-shape inputs")

    try:
        encode(diff_in, diff_out)
    except ValueError:
        pass
    else:
        raise AssertionError("encode must raise on differing shapes")

    print("=" * 80)
    print("dispatch + domain-rule checks: OK")


def check_relate_table():
    cases = [
        ((0, 0), "="),
        ((0, 5), "new"),
        ((5, 0), "dropped"),
        ((3, 3), "="),
        ((2, 6), "×3"),
        ((9, 3), "÷3"),
        ((5, 2), "Δ-3"),
        ((4, 9), "Δ+5"),
    ]
    for (a, b), want in cases:
        got = relate(a, b)
        assert got == want, f"relate({a}, {b}) = {got!r}, want {want!r}"
    print("=" * 80)
    print("relate() table checks: OK")


if __name__ == "__main__":
    check_relate_table()
    check_example_1()
    check_example_2()
    check_example_3()
    check_dispatch_and_domain_rules()
    print("\nAll checks passed.")
