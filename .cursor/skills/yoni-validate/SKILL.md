---
name: yoni-validate
description: Validates Yoni specs through the deterministic compiler pipeline — parse, AST, graph, and machine-checkable rules. Use when checking Yoni correctness, building the linter, running diagnostics, or analyzing spec impact before changes.
---

# Yoni Validation

## Pipeline (100% deterministic)

```
.yoni files → Parser → AST → Normalizer → Knowledge Graph → Validator → Impact Analyzer
```

## Knowledge graph edge types (exactly 10)

`USES`, `INPUT`, `OUTPUT`, `EMITS`, `VALIDATES`, `DEPENDS_ON`, `REFERENCES`, `OWNS`, `TRIGGERS`, `CONSUMES`

## Diagnostic format

```text
code: YONI1007
severity: error
message: Intent sections are out of order.
file: domains/invoicing/intents/create-invoice.yoni
blockId: INT_CREATE_INV_001
suggestion: Move validate: below input:
```

Target `blockId`, never line numbers.

## Validation classes

- **Parse**: unknown block, malformed header, duplicate top-level block
- **Structure**: missing sections, wrong order, missing `id:`/`desc:`
- **Naming**: non-kebab-case filename, wrong ID prefix
- **Repository**: wrong folder, forbidden folders, duplicate definitions
- **Reference**: unresolved `@Type.Name`, string refs forbidden
- **Evolution**: breaking change without migration block

## Impact analysis

```python
impact = compute_impact("ENT_CUSTOMER_001")
# Returns all intents, queries, views, tests affected by entity change
```

Use before any entity field rename/remove or rule change.

## Semantic diff

Report changes by meaning + impact set, not raw text diff:

```json
{
  "type": "FieldRename",
  "node": "ENT_CUSTOMER_001",
  "impact": {"intents": ["INT_CREATE_INV_001"], "queries": ["QUERY_ACTIVE_001"]}
}
```
