This is very useful. It turns the Phase 2 plan from vague “write better code” into a concrete curriculum.

What the 240-run says

The biggest bucket is:

semantic_bug_repair: 81 / 240 = 33.8%

That means the model often writes runnable code with the wrong or incomplete logic. That is exactly what Phase 3 repair should target.

The second big bucket is:

shape_contract: 38 / 240 = 15.8%

And by shape:

same: 0
diff: 31
mixed: 7

So shape contract failure is almost entirely diff/mixed. This confirms the diagnosis: Run 1 never learned diff-size output construction.

The third big bucket is:

syntax_major: 30 / 240 = 12.5%

with:

same: 22
diff: 8

That is a pure code-generation hygiene problem, not a transformation problem.

Same-size signal is strong

Look at the same-size rows:

near_miss: 15 same, 0 diff
partial_rule: 28 same, 0 diff
wrong_rule_runnable: 16 same, 0 diff
semantic_bug_repair: 61 same

That means same-size attempts are mostly in the “runnable but logically imperfect” regime.

That supports the substrate thesis:

same-size substrate training transferred rule structure,
but code still needs robustness and exactness.

Diff-size signal is clear

Diff-size is dominated by:

shape_contract: 31
semantic_bug_repair: 19
syntax_major: 8
trivial_fix_repair: 6

So Run 2 must explicitly teach:

diff-size shape planning
output allocation
crop/extract/tile/project construction

Not just “more ARC code.”

Exception types tell us the code curriculum

Top exceptions:

TypeError: 113
IndexError: 70
NameError: 33
ValueError: 20
UnboundLocalError: 16
AttributeError: 10
KeyError: 8
TimeoutError: 6
ZeroDivisionError: 3

This maps directly to training lessons:

TypeError      → data structure discipline; grid/list/tuple handling
IndexError     → bounds checks; shape-aware loops
NameError      → variable consistency; no half-written code
ValueError     → empty lists / min/max on empty / unpacking
UnboundLocal   → initialize variables on all branches
KeyError       → safe dictionary access
Timeout        → avoid unbounded search / recursion
ZeroDivision   → guard denominators

Phase 2 should now be explicit

I would structure it as:

2.A Code Contract
2.B Shape Contract
2.C Substrate-to-Code
2.D Direct Solver
2.E Repair

With mix:

Code Contract / syntax hygiene: 20%
Shape Contract diff-size:      25%
Substrate-to-Code:             25%
Direct Solver:                 15%
Repair from failures:          15%

Or if focusing on the biggest failure buckets:

semantic repair: high
shape contract: high
syntax/contract: medium

Non-negotiables for Code Solver system prompt

Yes, put this into the system prompt:

Return only Python code.
Define exactly one function:
def solve(input_grid):
The function must return a non-empty rectangular list[list[int]].
Every cell must be an int from 0 to 9.
Do not print.
Do not return None.
Do not return a scalar.
Do not return list[int].
Do not use files, network, eval, exec, subprocess, or imports outside math, collections, itertools, functools, copy.
First determine the output shape.
If output shape equals input shape:
  copy input_grid before editing.
If output shape differs from input shape:
  do not start from a copy of input_grid.
  compute output height and width first.
  allocate a new output grid.

But the stronger move is to make the target code consistently follow this style. The prompt alone will not fix TypeError/IndexError habits if the examples are messy.

What this means strategically

You are right: solve =

1. find the rule
2. write robust code

Run 1 suggests same-size rule finding is already partially there. The bottleneck is now:

robust code contract + exact repair

This 240-run gives the curriculum:

diff-size shape planning
safe loops
safe component logic
valid return contract
repair runnable semantic bugs

This is very actionable.
