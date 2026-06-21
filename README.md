# Yoni

**From one spec, everything emerges.**

Yoni is a software specification language — not a programming language. You describe **what** the system should do; AI (or the compiler toolchain) decides **how** to implement it.

Humans write `.yoni` specs. Generated code, schemas, APIs, and tests are disposable outputs. **The spec is always the source of truth.**

> See [MANDATORY.md](./MANDATORY.md) for the full philosophy and mental model.

---

## What Yoni is (and isn't)

| Yoni is | Yoni is not |
|---------|-------------|
| A spec language for business intent | Python, TypeScript, or any impl language |
| Machine-checkable and AI-repairable | Free-form prose or markdown docs |
| The canonical source of truth | Generated artifacts in `generated/` |

**Mental model:**

```
Project → Domain → Entity → Intent → Implementation (generated)
```

**Building blocks** (the only top-level concepts):

`project`, `domain`, `entity`, `state`, `event`, `intent`, `rule`, `query`, `action`, `constraint`, `workflow`, `error`, `test`, `capability`, `view`, `deployment`, `migration`

Everything else — functions, classes, APIs, DB schemas, UI — is **derived**.

---

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **Node.js + Yarn** (only for the VS Code / Cursor extension)

---

## Installation

```bash
git clone <repo-url>
cd ai_lang
uv sync
```

This creates a `.venv` and installs the `yoni` package plus dev tools (pytest, ruff, LSP deps).

---

## Quick start

Compile the sample invoicing project:

```bash
uv run python -m yoni samples/invoicing
```

Expected output:

```text
compiled 111/111 -> samples/invoicing/.ai/cache (ast, normalized, graph)
```

Cache artifacts land in `.ai/cache/`:

| Path | Contents |
|------|----------|
| `.ai/cache/ast/` | Per-file parse results + AST JSON |
| `.ai/cache/normalized/normalized.json` | Normalized workspace |
| `.ai/cache/graph/graph.json` | Knowledge graph (nodes + edges) |
| `.ai/generation/plans/` | Execution plans (one JSON per intent) |

Run impact analysis before changing an entity or rule:

```bash
uv run python -m yoni impact ENT_CUSTOMER_001 --root samples/invoicing
```

Build an execution plan for one intent (or all intents with `--all`):

```bash
uv run python -m yoni plan INT_REGISTER_USER_001 --root samples/invoicing
uv run python -m yoni plan --all --root samples/invoicing
```

---

## Compiler pipeline

The deterministic pipeline (no LLM) runs in this order:

```
.yoni files → Parser → AST → Normalizer → Knowledge Graph → Validator → Impact Analyzer
                                                                              ↓
                                                         Repair Engine → Execution Planner → Generator (LLM)
```

| Stage | What it does | Status |
|-------|--------------|--------|
| **Parser** | Lark grammar → typed AST | ✅ |
| **Normalizer** | Resolves refs, canonical block shape | ✅ |
| **Knowledge Graph** | Dependency graph (10 edge types) | ✅ |
| **Validator** | Structure, naming, refs, cycles, repo layout | ✅ |
| **Impact Analyzer** | Downstream blast radius for a block ID | ✅ |
| **Repair Engine** | Deterministic spec patches from diagnostics | 🔜 |
| **Execution Planner** | Ordered steps + artifacts per intent | ✅ |
| **Generator** | Python, TS, SQL, infra, UI from valid specs | 🔜 |

LLM is used **only** for generation, repair suggestions, documentation, and migration strategy — never for parse/validate/graph steps.

---

## Step-by-step: author a Yoni project

### 1. Create project layout

A Yoni project is a folder tree of `.yoni` files. Use the canonical layout:

```
my-project/
├── project/
│   └── my-app.yoni              # project block
├── domains/
│   └── customer/
│       ├── domain.yoni
│       ├── entities/
│       ├── intents/
│       ├── rules/
│       ├── queries/
│       ├── actions/
│       ├── events/
│       ├── states/
│       ├── constraints/
│       ├── errors/
│       ├── workflows/
│       └── tests/
├── capabilities/
│   └── email/
│       └── capability.yoni
├── views/
├── deployments/
└── migrations/
```

One top-level block per file. Kebab-case filenames. No `misc/`, `common/`, or duplicate block homes.

### 2. Define the project

```yoni
project MyApp

id: PROJ_MYAPP_001
desc:
  My application.

domains:
  @Domain.Customer
```

### 3. Add a domain

```yoni
domain Customer

id: DOM_CUSTOMER_001
desc:
  Customer management.
```

### 4. Add entities (canonical schema)

```yoni
entity Customer

id: ENT_CUSTOMER_001
desc:
  Primary customer record.

fields:
  email: s
  age: i
  active: b
```

### 5. Add rules and constraints

```yoni
rule Adult

id: RULE_ADULT_001
desc:
  Customer must be 18 or older.

age >= 18
```

References use typed syntax — `@Entity.Customer`, `@Rule.Adult` — never raw strings.

### 6. Add an intent (core unit of behavior)

Sections are **mandatory and ordered**:

```yoni
intent RegisterUser

id: INT_REGISTER_USER_001
desc:
  Registers a new customer account.

input:
  email: s
  age: i

validate:
  @Rule.Adult
  @Constraint.EmailUnique

process:
  new customer @Entity.Customer
  set customer.email email
  set customer.age age
  save customer

emit:
  @Event.CustomerRegistered

fail:
  @Error.EmailAlreadyExists

return: @Entity.Customer
```

Order: `input:` → `validate:` → `process:` → `emit:` → `fail:` → `return:`

### 7. Compile and fix diagnostics

```bash
uv run python -m yoni path/to/my-project
```

Every diagnostic includes a stable `blockId` — always repair by ID, not line number.

Example:

```text
code: YONI1007
severity: error
message: Intent sections are out of order.
blockId: INT_CREATE_INV_001
suggestion: Move validate: below input:
```

### 8. Check impact before breaking changes

Before renaming/removing entity fields or changing rules:

```bash
uv run python -m yoni impact ENT_CUSTOMER_001 --root path/to/my-project
```

Lists all downstream intents, queries, views, tests, and deployments affected.

### 9. Add a migration (breaking changes)

Entity or state breaking changes require a `migration` block in `migrations/`.

### 10. Plan execution steps

After validation passes, build a deterministic execution plan per intent:

```bash
uv run python -m yoni plan INT_REGISTER_USER_001 --root path/to/my-project
```

Plans are written to `.ai/generation/plans/<INTENT_ID>.json` (steps + artifact list).

### 11. Generate implementation (when generator lands)

Generation runs **only after validation passes** and consumes execution plans. Output goes to `generated/` and can be deleted and regenerated at any time.

---

## Step-by-step: validate specs

### CLI

```bash
uv run python -m yoni <project-root>
```

Exit code `0` = parse + validation OK. Exit code `1` = parse or validation errors.

### Python API

```python
from pathlib import Path
from yoni import compile_workspace

result = compile_workspace(Path("samples/invoicing"))

if result.ok:
    print(f"Graph: {len(result.graph.nodes)} nodes")
else:
    for err in result.validation_errors:
        print(err.code, err.block_id, err.message)
```

### Validation categories

| Class | Examples |
|-------|----------|
| Parse | Unknown block, malformed header |
| Structure | Missing sections, wrong intent order |
| Naming | Non-kebab-case filename, wrong ID prefix |
| Repository | Wrong folder, forbidden folders |
| Reference | Unresolved `@Type.Name` |
| Evolution | Breaking change without migration |
| Cycles | Circular dependencies |

Diagnostics use codes like `YONI1007` (structure) and `YONI2001` (references).

---

## Step-by-step: repair workflow

1. Read the diagnostic (`code`, `blockId`, `suggestion`)
2. Locate the block by `id:` in the `.yoni` source
3. Apply a deterministic patch to the **spec** (never patch `generated/` code)
4. Re-run validation on the whole workspace
5. Regenerate outputs only after validation passes

**Repair primitives:** `ReplaceReference`, `CreateStub`, `DeleteReference`, `AddField`, `RemoveField`, `RenameField`, `CreateTransition`, `RemoveTransition`

Always run impact analysis before breaking entity/state changes.

---

## Step-by-step: IDE setup (VS Code / Cursor)

Syntax highlighting + live lint for `.yoni`, `.yni`, and `.yo` files.

```bash
uv sync
cd plugins/vscode-yoni
yarn
yarn compile
```

Then open `plugins/vscode-yoni` in VS Code/Cursor and press **F5** to launch the Extension Development Host.

Full details: [plugins/vscode-yoni/README.md](./plugins/vscode-yoni/README.md)

Manual LSP test from repo root:

```bash
PYTHONPATH=. .venv/bin/python -m plugins.yoni_lsp
```

---

## Step-by-step: run tests

```bash
uv run pytest
```

Lint / format:

```bash
uv run ruff check .
uv run ruff format .
```

Pre-commit (optional):

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

---

## Knowledge graph

The graph connects blocks with exactly these edge types:

`USES`, `INPUT`, `OUTPUT`, `EMITS`, `VALIDATES`, `DEPENDS_ON`, `REFERENCES`, `OWNS`, `TRIGGERS`, `CONSUMES`

Impact analysis traverses this graph to find everything downstream of a changed block.

---

## Repository layout (this repo)

```
ai_lang/
├── yoni/                  # Compiler: parser, AST, normalizer, graph, validator, impact
├── plugins/
│   ├── vscode-yoni/       # VS Code / Cursor extension
│   └── yoni_lsp/          # Python language server
├── samples/
│   └── invoicing/         # Full sample project (111 specs)
├── tests/                 # Parser, pipeline, graph, validator tests
├── MANDATORY.md           # Philosophy and authoring rules
└── pyproject.toml
```

### Durable vs disposable

| Durable (source of truth) | Disposable |
|---------------------------|------------|
| `.yoni` spec files | `generated/` |
| `yoni.config.yoni`, `.yoni/` | `.ai/cache/` |

---

## Sample project

[`samples/invoicing/`](./samples/invoicing/) is a full billing/invoicing spec with:

- 5 domains (Customer, Invoicing, Payments, Catalog, Notification)
- Entities, intents, rules, queries, workflows, tests
- Capabilities (Email, PaymentGateway, PDF)
- Views and deployments

Use it as a reference when authoring your own project.

---

## Contributing

We welcome contributions. This project is preparing for open source release.

### Getting started

1. Fork and clone the repo
2. `uv sync`
3. Create a branch: `git checkout -b feat/my-change`
4. Make changes; add tests when fixing bugs or adding compiler behavior
5. `uv run pytest && uv run ruff check .`
6. Open a PR with a clear description of what and why

### Contribution areas

- **Compiler** — parser, normalizer, graph, validator rules (`yoni/`)
- **LSP / IDE** — diagnostics, completions (`plugins/`)
- **Specs & samples** — new block types, sample projects (`samples/`)
- **Docs** — clarity beats completeness; keep examples runnable

### Principles

- Spec authority: when spec and generated code disagree, **Yoni wins**
- Debug by stable block `id:`, never by name or line number
- Deterministic pipeline before any LLM step
- Minimal, focused PRs over large rewrites

### Reporting issues

Include:

- Yoni source snippet (or block ID)
- Full diagnostic output
- Expected vs actual behavior
- `uv run python -m yoni <root>` output

---

## Roadmap

- [x] Parser + AST (Lark)
- [x] Normalizer + typed references
- [x] Knowledge graph builder
- [x] Validator (structure, naming, refs, cycles, repo layout)
- [x] Impact analyzer + CLI
- [x] LSP + VS Code extension
- [ ] Repair engine (deterministic patches)
- [x] Execution planner + `yoni plan` CLI
- [ ] Code generator (LLM-backed, spec-driven)
- [ ] Semantic diff

---

## License

License TBD — will be added before public release. Contributions accepted under the terms that will be published with the license file.

---

## Links

- [MANDATORY.md](./MANDATORY.md) — philosophy, blocks, intent structure
- [VS Code extension](./plugins/vscode-yoni/README.md) — IDE setup
- [Sample project](./samples/invoicing/) — full invoicing spec
