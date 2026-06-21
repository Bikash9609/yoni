# Yoni VS Code Extension

## Setup

```bash
uv sync
cd plugins/vscode-yoni && yarn && yarn compile
```

## Run (F5)

1. Open this repo as the workspace root.
2. Open `plugins/vscode-yoni` in VS Code/Cursor.
3. Press **F5** (uses `.vscode/launch.json`).
4. In the Extension Development Host, open a `.yoni` file from `tests/fixtures/` or `samples/invoicing/`.

## Settings

- `yoni.pythonPath` — defaults to `${workspaceFolder}/.venv/bin/python`
- `yoni.trace.server` — LSP trace level (`off` | `messages` | `verbose`)

## Manual LSP test

```bash
PYTHONPATH=. .venv/bin/python -m plugins.yoni_lsp
```
