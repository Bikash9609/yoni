# Yoni VS Code Extension

Syntax highlighting + live lint for `.yoni`, `.yni`, and `.yo` files.

## Prerequisites

- Python 3.10+ with repo venv (`uv sync` at repo root)
- Node.js + Yarn
- VS Code or Cursor

## Local setup

From the **repo root** (`ai_lang/`):

```bash
uv sync
cd plugins/vscode-yoni
yarn
yarn compile
```

## Run the extension (F5)

1. Open `plugins/vscode-yoni` as your workspace in VS Code/Cursor.
2. Press **F5** (Run Extension).
3. A new **Extension Development Host** window opens with the repo root loaded.
4. Open any `.yoni` file, e.g. `tests/fixtures/intent_create_invoice.yoni`.

You should see syntax colors and diagnostics in the Problems panel when the file has errors.

## Try linting

Open or create a file with bad intent section order:

```yoni
intent Bad

id: INT_BAD_001
desc:
  Bad order.

process:

input:
```

Expected: **YONI1007** with a suggestion to reorder sections.

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `yoni.pythonPath` | `${workspaceFolder}/.venv/bin/python` | Python used to run the LSP |
| `yoni.trace.server` | `off` | LSP trace: `off`, `messages`, or `verbose` |

If lint doesn't show, check `yoni.pythonPath` points to the repo `.venv` and the workspace root is `ai_lang/` (not just the extension folder).

## Manual LSP test

From repo root:

```bash
PYTHONPATH=. .venv/bin/python -m plugins.yoni_lsp
```

Runs the language server on stdio (normally started by the extension).

## Project layout

```
plugins/
├── vscode-yoni/     # this extension (client + TextMate grammar)
└── yoni_lsp/        # Python LSP server (uses yoni parser)
```

Lint logic lives in the main `yoni/` package — the extension does not duplicate the parser.
