#!/usr/bin/env python3
"""auto_iter.py - semi-auto iter loop for substrate validation."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def load_keys_env():
    keys_file = Path(__file__).parent / "keys.env"
    if not keys_file.exists():
        return
    for line in keys_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")


load_keys_env()


MODELS = {
    "claude-sonnet":    ("anthropic", "claude-sonnet-4-5"),
    "claude-opus":      ("anthropic", "claude-opus-4-5"),
    "claude-haiku":     ("anthropic", "claude-haiku-4-5"),
    "gpt-5":            ("openai",    "gpt-5"),
    "gpt-5-mini":       ("openai",    "gpt-5-mini"),
    "gpt-4o":           ("openai",    "gpt-4o"),
    "gemini-2.5-pro":   ("google",    "gemini-2.5-pro"),
    "gemini-2.5-flash": ("google",    "gemini-2.5-flash"),
    "grok-4":           ("xai",       "grok-4"),
    "grok-4-fast":      ("xai",       "grok-4-1-fast-reasoning"),
    "qwen-coder":       ("openrouter", "qwen/qwen-2.5-coder-32b-instruct"),
    "qwen-coder-14b":   ("openrouter", "qwen/qwen-2.5-coder-14b-instruct"),
    "qwen-coder-7b":    ("openrouter", "qwen/qwen-2.5-coder-7b-instruct"),
    "qwen-max":         ("openrouter", "qwen/qwen-max"),
    "deepseek-r1-32b":  ("openrouter", "deepseek/deepseek-r1-distill-qwen-32b"),
    "deepseek-r1":      ("openrouter", "deepseek/deepseek-r1"),
    "deepseek-chat":    ("openrouter", "deepseek/deepseek-chat"),
    "llama-3.3-70b":    ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
    "mistral-large":    ("openrouter", "mistralai/mistral-large"),
}

PROVIDER_DIR = {
    "anthropic":  "Claude",
    "openai":     "GPT",
    "google":     "Gemini",
    "xai":        "Grok",
    "openrouter": "OpenRouter",
}


def chat_anthropic(messages, model, max_tokens=8192):
    """Anthropic with extended thinking maxed out for sonnet/opus."""
    from anthropic import Anthropic
    client = Anthropic()
    sys_msg = ""
    msgs = []
    for m in messages:
        if m["role"] == "system":
            sys_msg = m["content"]
        else:
            msgs.append(m)

    use_thinking = "haiku" not in model.lower()

    if use_thinking:
        thinking_budget = 32000
        kwargs = {
            "model": model,
            "max_tokens": 40000,
            "messages": msgs,
            "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
            "temperature": 1.0,
        }
    else:
        kwargs = {"model": model, "max_tokens": 16384, "messages": msgs}

    if sys_msg:
        kwargs["system"] = sys_msg

    resp = client.messages.create(**kwargs)
    text_parts = [b.text for b in resp.content if getattr(b, "type", "text") == "text"]
    if text_parts:
        return "".join(text_parts)
    return resp.content[0].text


def chat_openai(messages, model, max_tokens=8192):
    """OpenAI with reasoning_effort=high and large completion budget."""
    from openai import OpenAI
    client = OpenAI()
    is_reasoning = model.startswith("gpt-5") or model.startswith("o")
    if is_reasoning:
        kwargs = {
            "model": model,
            "max_completion_tokens": 64000,
            "messages": messages,
            "reasoning_effort": "high",
        }
    else:
        kwargs = {
            "model": model,
            "max_completion_tokens": 16384,
            "messages": messages,
        }
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def chat_google(messages, model, max_tokens=8192):
    from google import genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config={"max_output_tokens": 32000},
    )
    return resp.text


def chat_xai(messages, model, max_tokens=8192):
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ["XAI_API_KEY"],
        base_url="https://api.x.ai/v1",
    )
    resp = client.chat.completions.create(
        model=model, max_tokens=16384, messages=messages,
    )
    return resp.choices[0].message.content


def chat_openrouter(messages, model, max_tokens=8192):
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    resp = client.chat.completions.create(
        model=model, max_tokens=32000, messages=messages,
    )
    return resp.choices[0].message.content


CHAT = {
    "anthropic":  chat_anthropic,
    "openai":     chat_openai,
    "google":     chat_google,
    "xai":        chat_xai,
    "openrouter": chat_openrouter,
}


def extract_solve(text):
    fenced_matches = re.findall(
        r"```(?:python)?\s*\n(def solve\b.*?)\n```",
        text, re.DOTALL,
    )
    if fenced_matches:
        return fenced_matches[-1].rstrip()
    raw_matches = re.findall(
        r"^(def solve\b[\s\S]*?)(?=\n```|\n# end|\Z)",
        text, re.MULTILINE,
    )
    if raw_matches:
        return raw_matches[-1].rstrip()
    return None


def extract_hand_grid(text):
    match = re.search(
        r"TEST_OUTPUT\s*=\s*(\[\s*\[.*?\]\s*\])",
        text, re.DOTALL,
    )
    if not match:
        return None
    try:
        import ast
        grid = ast.literal_eval(match.group(1))
        if (isinstance(grid, list)
                and all(isinstance(row, list) for row in grid)
                and all(isinstance(v, int) for row in grid for v in row)):
            return grid
    except (ValueError, SyntaxError):
        pass
    return None


def validate_hand_grid(hand_grid, puzzle_file):
    if hand_grid is None:
        return None
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    if not puzzle.get("test") or "output" not in puzzle["test"][0]:
        return None
    truth = puzzle["test"][0]["output"]
    if len(hand_grid) != len(truth) or any(
        len(hand_grid[r]) != len(truth[r]) for r in range(len(truth))
    ):
        return ("dimension_mismatch", None, None)
    diffs = sum(
        1 for r in range(len(truth)) for c in range(len(truth[0]))
        if hand_grid[r][c] != truth[r][c]
    )
    total = len(truth) * len(truth[0])
    return (diffs == 0, diffs, total)


def derive_puzzle_id(puzzle_file):
    stem = Path(puzzle_file).stem
    m = re.match(r"^puzzle_(.+)$", stem)
    return m.group(1) if m else stem


def run_feedback(puzzle_file):
    """Run validator subprocess and return the FULL diagnostic feedback file.

    run_feedback.py writes the substrate's full diagnostic output (diff maps,
    transformation grids, mechanistic analysis, regression alerts) to
    feedback_<puzzle_id>.txt. Stdout only has the verdict summary (~500 chars).

    The full file is what the model needs to see to iterate effectively.
    Returning stdout instead would starve the model of the substrate's
    diagnostic content.
    """
    result = subprocess.run(
        [sys.executable, "run_feedback.py", puzzle_file, "solution"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"VALIDATOR ERROR (exit {result.returncode}):\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    puzzle_id = derive_puzzle_id(puzzle_file)
    feedback_file = Path(f"feedback_{puzzle_id}.txt")
    if not feedback_file.exists():
        return result.stdout
    return feedback_file.read_text()


def generate_initial_prompt(puzzle_file):
    sys.path.insert(0, str(Path(__file__).parent))
    from arc_prompt_generator import generate_prompt
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    return generate_prompt(puzzle, include_test=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle_file")
    parser.add_argument("--model", required=True, choices=list(MODELS.keys()))
    parser.add_argument("--max-iters", type=int, default=10)
    parser.add_argument("--auto", action="store_true",
                        help="Skip pause between iters (run unattended)")
    args = parser.parse_args()

    provider, full_model = MODELS[args.model]
    chat = CHAT[provider]
    puzzle_id = derive_puzzle_id(args.puzzle_file)
    model_dir = Path("Model Results") / PROVIDER_DIR[provider] / puzzle_id
    model_dir.mkdir(parents=True, exist_ok=True)

    history_file = f"{puzzle_id}_history.json"
    if os.path.exists(history_file):
        os.remove(history_file)

    initial_prompt = generate_initial_prompt(args.puzzle_file)
    messages = [{"role": "user", "content": initial_prompt}]

    print(f"Puzzle: {puzzle_id}")
    print(f"Model:  {args.model} ({provider}/{full_model})")
    print(f"Output: {model_dir}/")
    print(f"Mode:   {'auto' if args.auto else 'pause-between-iters'}")
    print()

    timing = {
        "puzzle_id": puzzle_id,
        "model": args.model,
        "provider": provider,
        "full_model": full_model,
        "iters": [],
    }
    puzzle_start = time.time()

    for n in range(1, args.max_iters + 1):
        print("=" * 60)
        print(f"ITER {n} - sending {len(messages)} message(s), "
              f"{sum(len(m['content']) for m in messages)} chars")
        print("=" * 60)

        iter_start = time.time()
        api_start = time.time()
        try:
            response = chat(messages, full_model)
        except Exception as e:
            print(f"API error: {type(e).__name__}: {e}")
            return
        api_elapsed = time.time() - api_start

        (model_dir / f"iter_{n}_response.txt").write_text(response)
        print(f"Response: {len(response)} chars in {api_elapsed:.1f}s -> iter_{n}_response.txt")

        code = extract_solve(response)
        if code is None:
            print("No def solve found in response. Stopping.")
            (model_dir / f"iter_{n}_response.py").write_text(
                "# NO def solve FOUND IN RESPONSE\n"
            )
            return
        (model_dir / f"iter_{n}_response.py").write_text(code)
        Path("solution.py").write_text(code)

        hand_grid = extract_hand_grid(response)
        hand_validation = None
        if hand_grid is not None:
            (model_dir / f"iter_{n}_hand_grid.json").write_text(
                json.dumps(hand_grid)
            )
            hand_validation = validate_hand_grid(hand_grid, args.puzzle_file)
            print(f"Hand grid: {len(hand_grid)}x{len(hand_grid[0])} extracted "
                  f"-> iter_{n}_hand_grid.json")
            if hand_validation is not None:
                ok, diffs, total = hand_validation
                if ok == "dimension_mismatch":
                    print(f"Hand grid dimensions don't match test ground truth")
                else:
                    print(f"Hand grid vs test ground truth (analysis only, "
                          f"not in feedback): {diffs}/{total} cells wrong "
                          f"({'MATCH' if ok else 'no match'})")
        else:
            print("No TEST_OUTPUT block found in response (hand grid skipped)")

        validation_start = time.time()
        feedback = run_feedback(args.puzzle_file)
        validation_elapsed = time.time() - validation_start
        (model_dir / f"iter_{n}_feedback.txt").write_text(feedback)

        iter_total = time.time() - iter_start
        print(f"Validation: {validation_elapsed:.1f}s | iter total: {iter_total:.1f}s "
              f"(API {api_elapsed:.1f}s + validation {validation_elapsed:.1f}s + parse/io {iter_total - api_elapsed - validation_elapsed:.1f}s)")

        verdict = "SUBMIT" if "VERDICT: SUBMIT" in feedback else "DO NOT SUBMIT"
        timing["iters"].append({
            "iter": n,
            "api_seconds": round(api_elapsed, 2),
            "validation_seconds": round(validation_elapsed, 2),
            "iter_total_seconds": round(iter_total, 2),
            "response_chars": len(response),
            "input_chars_sent": sum(len(m["content"]) for m in messages),
            "verdict": verdict,
            "hand_grid_match": (
                None if hand_validation is None
                else (hand_validation[0] is True)
            ),
        })

        print()
        print("--- feedback (last 1500 chars) ---")
        print(feedback[-1500:] if len(feedback) > 1500 else feedback)
        print("--- end feedback ---")
        print()

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": feedback})
        (model_dir / "conversation.json").write_text(
            json.dumps(messages, indent=2)
        )
        timing["total_wall_seconds"] = round(time.time() - puzzle_start, 2)
        timing["iters_used"] = n
        timing["final_verdict"] = verdict
        (model_dir / "timing.json").write_text(json.dumps(timing, indent=2))

        if "VERDICT: SUBMIT" in feedback:
            total = time.time() - puzzle_start
            print(f"SUBMIT verdict at iter {n}. Total wall time: {total:.1f}s "
                  f"({total/60:.1f} min). Stopping.")
            return

        if not args.auto and n < args.max_iters:
            try:
                input("Press Enter for next iter (Ctrl+C to stop and inspect): ")
            except KeyboardInterrupt:
                print("\nStopped at user request.")
                return

    total = time.time() - puzzle_start
    print(f"\nMax iters ({args.max_iters}) reached without SUBMIT verdict. "
          f"Total wall time: {total:.1f}s ({total/60:.1f} min).")


if __name__ == "__main__":
    main()
