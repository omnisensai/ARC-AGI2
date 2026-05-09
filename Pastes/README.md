# Pastes

Folder for the file-commit paste workflow.

## How to use

1. Click **Add file → Create new file** in the GitHub web UI.
2. Filename: `<puzzle_id>__<model>.txt` — e.g. `13e47133__grok.txt`.
   - Optional: `<puzzle_id>__<model>__iter<N>.txt` to force a specific iter number.
   - Models: `claude`, `gpt`, `gemini`, `grok`, `openrouter`.
3. Body: paste the model's full response (def solve + optional TEST_OUTPUT).
   The web UI preserves newlines (unlike workflow_dispatch text inputs).
4. Commit. The workflow auto-runs paste_helper, generates artifacts under
   `Model Results/<Model>/<puzzle>/iter_N_*`, and moves the paste file to
   `Pastes/processed/`.

## Why not workflow_dispatch?

GitHub's `workflow_dispatch` text inputs strip newlines, mangling Python code.
File-commit input via the web UI preserves newlines exactly.
