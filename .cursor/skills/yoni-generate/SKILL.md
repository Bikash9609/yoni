---
name: yoni-generate
description: Generates implementation code from validated Yoni specs via execution plans. Use when generating Python, TypeScript, SQL, tests, infra, or UI from Yoni, or when the user asks to build or regenerate outputs from specs.
---

# Yoni Generation

## Prerequisites

Generation runs **only after** validation passes:

```
Parser → AST → Normalizer → Graph → Validator ✓ → Execution Planner → Scope + Queue → Generator (LLM)
```

If validation fails, repair Yoni source first (see `yoni-repair` skill).

## Step 1 — Plan

Build execution plans before generating code:

```bash
uv run python -m yoni plan INT_REGISTER_USER_001 --root <project-root>
uv run python -m yoni plan --all --root <project-root>
```

Plans land in `.ai/generation/plans/<INTENT_ID>.json`.

## Step 2 — Prepare queue (implemented)

Build a scoped, topologically ordered job queue:

```bash
uv run python -m yoni generate --intent INT_REGISTER_USER_001 --root <project-root>
uv run python -m yoni generate --domain customer --root <project-root>
uv run python -m yoni generate --continue gen_abc --root <project-root>
uv run python -m yoni generate --impact ENT_CUSTOMER_001 --root <project-root>
```

Writes:

| Path | Contents |
|------|----------|
| `.ai/generation/session.json` | Session id, scope, ordered jobs (`pending`/`done`) |
| `.ai/generation/manifest.json` | Block ID ↔ file registry (filled when jobs complete) |

Job types: `entity_schema`, `state_machine`, `rule_impl`, `constraint_impl`, `query_impl`, `action_impl`, `error_def`, `intent_handler`.

## Step 3 — Execute jobs (upcoming)

LLM and deterministic templates will consume one job at a time from the queue. Do not skip the queue — do not generate the whole project in one call.

## Generation contract

- Read Yoni source only — do not infer meaning from existing `generated/` output
- Consume **execution plan** + **normalized blocks**, not raw text
- Attach every artifact to source block IDs (`# yoni:BLOCK_ID`)
- Fail if any reference cannot be resolved from Yoni source
- Output goes to `generated/` (code, docs, tests, infra, ui)

## Execution plan shape

```json
{
  "intent": "INT_CREATE_INV_001",
  "steps": [
    {"order": 1, "type": "validate", "block": "RULE_ELIGIBLE_001"},
    {"order": 2, "type": "query", "query": "QUERY_CUSTOMER_001", "result": "customer"},
    {"order": 3, "type": "action", "action": "ACT_CREATE_INVOICE_001", "result": "invoice"},
    {"order": 4, "type": "emit", "event": "EVT_INVOICE_CREATED_001"}
  ],
  "artifacts": [
    {"job": "entity_schema", "block": "ENT_CUSTOMER_001", "depends": []},
    {"job": "intent_handler", "block": "INT_CREATE_INV_001", "depends": ["ENT_CUSTOMER_001"]}
  ]
}
```

## Allowed targets

Python, TypeScript, JavaScript, Rust, Go, Java, C#, SQL, GraphQL, React UI, Terraform, Kubernetes, tests, docs, monitoring, migrations.

## After generation

Trace every output back to source IDs. Generated artifacts are disposable — Yoni remains truth.

Full architecture: `docs/05-code-generation-mechanism.md`.
