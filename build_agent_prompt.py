"""Build agent prompts that show the entire puzzle (train + test pairs with outputs).

Agent's job is to write code that captures the rule, NOT to solve. They have
every input/output pair as a reference. This is faster, cheaper, and more
reliable than asking them to figure out the test output.

Usage:
    from build_agent_prompt import build_full_prompt
    prompt = build_full_prompt(puzzle_dict, puzzle_id)
"""
from substrate import format_grid


def build_full_prompt(puzzle: dict, puzzle_id: str) -> str:
    pairs_text = []
    for i, p in enumerate(puzzle["train"]):
        pairs_text.append(
            f"Training pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
            f"Output:\n{format_grid(p['output'])}"
        )
    for i, p in enumerate(puzzle["test"]):
        pairs_text.append(
            f"Test pair {i+1} (the answer is provided so you can use it as another example):\n"
            f"Input:\n{format_grid(p['input'])}\n\nOutput:\n{format_grid(p['output'])}"
        )
    return (
        f"Write a Python `def solve(input_grid):` function that produces the correct "
        f"output for any of the input grids below. You have the FULL puzzle including "
        f"the test answer — your only job is to find the rule and encode it in Python. "
        f"You are NOT solving anything; you are writing code that reproduces the given "
        f"input-to-output mapping for every example here, and would generalize to a "
        f"new input of the same kind.\n\n"
        f"Puzzle ID: {puzzle_id}\n\n"
        + "\n\n".join(pairs_text)
        + "\n\nRequirements:\n"
        "- ONE `def solve(input_grid):` function. `input_grid` is a list of lists of ints; "
        "return a list of lists of ints.\n"
        "- The code must execute correctly on every input above and produce the matching output.\n"
        "- Verify all pairs (training AND test) before reporting.\n"
        "- No `print` statements, no example calls. Just the function.\n\n"
        "Return ONLY the Python code inside a ```python ... ``` block. No prose."
    )
