"""Single source of truth for the canonical latent-T acceptance gate.

Imported by both:
  - scripts/validate_canonical.py   (real golden_train corpus)
  - micro/build_micro.py            (synthetic micro-primitive corpus)

A solver is ACCEPTED iff it reproduces every (train+test) pair's ground-truth
output EXACTLY when run in a fresh subprocess, AND passes the AST hardcoding
audit. Nothing trains on a solver this gate rejects. Keeping the gate in one
place is deliberate: a second copy is exactly how acceptance criteria drift.
"""
import ast, json, os, re, subprocess, sys, tempfile

# Runner: import the solver in a clean process, run solve() on every pair,
# compare the produced grid to the ground-truth output. Size-agnostic
# (works for same-size and diff-size), so it never trusts the solver's claim.
_VRUN = r'''
import json, sys
exec(open(sys.argv[1]).read(), (ns := {}))
pairs = json.load(open(sys.argv[2])); fn = ns.get("solve")
oks = []
for p in pairs:
    try:
        o = fn(p["input"]); o = o.tolist() if hasattr(o, "tolist") else o
        oks.append(o == p["output"])
    except Exception:
        oks.append(False)
print(json.dumps(oks))
'''

_HARD = ("BIG_LITERAL", "EQ_GRID", "FINGERPRINT", "NO_MASK", "unparseable")


def audit(code: str, big_literal_max: int = 12) -> list:
    """AST hardcoding audit. Returns a list of flags; any flag starting with a
    _HARD prefix is disqualifying. big_literal_max may be tightened for the
    diff-size track (small outputs are easier to transcribe)."""
    flags = []
    try:
        t = ast.parse(code)
    except Exception:
        return ["unparseable"]

    def gl(n):  # size of a list-of-lists literal (rows*cols), else 0
        if not isinstance(n, ast.List):
            return 0
        s = 0
        for e in n.elts:
            if isinstance(e, ast.List):
                s += len(e.elts)
            else:
                return 0
        return s

    big = 0
    eq = False
    for n in ast.walk(t):
        big = max(big, gl(n))
        if isinstance(n, ast.Compare):
            for op, c in zip(n.ops, n.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and gl(c) >= 9:
                    eq = True
    if big >= big_literal_max:
        flags.append(f"BIG_LITERAL({big})")
    if eq:
        flags.append("EQ_GRID")
    if "frozenset(" in code and ("known" in code.lower() or "case" in code.lower()):
        flags.append("FINGERPRINT")
    if not re.search(r"\b(infer_T|apply_T|mask|changes|delta|T\s*=|Tcells)\b", code):
        flags.append("NO_MASK")
    return flags


def run_pairs(solver_path, pairs, timeout: int = 60) -> list:
    """Run the solver against pairs in a fresh subprocess. Returns a list of
    bool (one per pair). Uses unique temp files so it is concurrency-safe."""
    rf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    rf.write(_VRUN); rf.close()
    pf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(pairs, pf); pf.close()
    try:
        r = subprocess.run([sys.executable, rf.name, str(solver_path), pf.name],
                           capture_output=True, text=True, timeout=timeout)
        lines = r.stdout.strip().splitlines()
        return json.loads(lines[-1]) if lines else [False] * len(pairs)
    except Exception:
        return [False] * len(pairs)
    finally:
        os.unlink(rf.name); os.unlink(pf.name)


def accept(solver_path, pairs, timeout: int = 60, big_literal_max: int = 12):
    """Returns (accepted: bool, pass_str: 'X/Y', flags: list)."""
    oks = run_pairs(solver_path, pairs, timeout)
    flags = audit(open(solver_path).read(), big_literal_max)
    hardbad = any(f.startswith(_HARD) for f in flags)
    return (all(oks) and not hardbad), f"{sum(oks)}/{len(oks)}", flags
