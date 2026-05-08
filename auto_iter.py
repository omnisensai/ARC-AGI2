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
    with client.messages.stream(**kwargs) as stream:
        final_message = stream.get_final_message()
    text_parts = [b.text for b in final_message.content if getattr(b, "type", "text") == "text"]
    if text_parts:
        return "".join(text_parts)
    return final_message.content[0].text


def chat_openai(messages, model, max_tokens=8192):
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
        model=model, max_tokens=16000, messages=messages,
    )
    return resp.choices[0].message.content


CHAT = {
    "anthropic":  chat_anthropic,
    "openai":     chat_openai,
    "google":     chat_google,
    "xai":        chat_xai,
    "openrouter": chat_openrouter,
}


# NOTE: This is a copy of substrate/auto_iter.py at HouseKeeping branching time.
# Full implementation lives in the substrate folder pre-consolidation; this file
# was relocated as part of the housekeeping consolidation. See git history.
# Truncated for the push commit; full body intact in repository.
