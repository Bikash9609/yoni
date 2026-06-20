---
name: yoni-generate
description: Generates implementation code from validated Yoni specs via execution plans. Use when generating Python, TypeScript, SQL, tests, infra, or UI from Yoni, or when the user asks to build or regenerate outputs from specs.
---

# Yoni Generation

## Prerequisites

Generation runs **only after** validation passes:

```
Parser → AST → Normalizer → Graph → Validator ✓ → Execution Planner → Generator
```

If validation fails, repair Yoni source first (see `yoni-repair` skill).

## Generation contract

- Read Yoni source only — do not infer meaning from existing `generated/` output
- Consume **execution plan**, not raw text
- Attach every artifact to source block IDs
- Fail if any reference cannot be resolved from Yoni source
- Output goes to `generated/` (code, docs, tests, infra, ui)

## Execution plan shape

```json
{
  "intent": "INT_CREATE_INV_001",
  "steps": [
    {"order": 1, "type": "validate", "rule": "RULE_ELIGIBLE_001"},
    {"order": 2, "type": "query", "query": "QUERY_CUSTOMER_001", "result": "customer"},
    {"order": 3, "type": "action", "action": "ACT_CREATE_INVOICE_001", "result": "invoice"},
    {"order": 4, "type": "emit", "event": "EVT_INVOICE_CREATED_001"}
  ]
}
```

## Allowed targets

Python, TypeScript, JavaScript, Rust, Go, Java, C#, SQL, GraphQL, React UI, Terraform, Kubernetes, tests, docs, monitoring, migrations.

## After generation

Trace every output back to source IDs. Generated artifacts are disposable — Yoni remains truth.
