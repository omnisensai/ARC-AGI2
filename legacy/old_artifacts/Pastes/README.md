# Pastes

Folder for the file-commit paste workflow.

## How to use

1. Click **Add file → Create new file** in the GitHub web UI.
2. Filename: `<puzzle_id>_<model>.txt` — e.g. `13e47133_grok.txt`.
   - For refinement responses (R≥2), use `<puzzle_id>_<model>_R<N>.txt`,
     e.g. `13e47133_grok_R2.txt` for the response to F1.
   - Models: `claude`, `gpt`, `gemini`, `grok`, `openrouter`.
3. Body: paste the model's full response (def solve + optional TEST_OUTPUT).
   The web UI preserves newlines (unlike workflow_dispatch text inputs).
4. Commit. The workflow auto-runs paste_helper, generates artifacts under
   `Model Results/<Model>/<puzzle>/R<N>.*` (and `F<N>.txt` if training
   partially passes), and moves the paste file to `Pastes/processed/`.

## Naming key

| Filename | Meaning |
|---|---|
| `<puzzle>_<model>.txt` | R1 — response to the seed prompt |
| `<puzzle>_<model>_R<N>.txt` | R\<N\> — response to F\<N-1\> |

ARC puzzle IDs are 8-char hex (e.g. `13e47133`), so single-underscore
separators don't collide with anything in the puzzle ID.

## Why not workflow_dispatch?

GitHub's `workflow_dispatch` text inputs strip newlines, mangling Python code.
File-commit input via the web UI preserves newlines exactly.
