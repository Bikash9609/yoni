---
name: yoni-repair
description: Repairs Yoni specifications using deterministic patch primitives and validation diagnostics. Use when fixing Yoni linter errors, unresolved references, broken intents, migration issues, or when diagnostics target block IDs.
---

# Yoni Repair

## Rule

Repair **Yoni source first**. Never patch generated code.

## Workflow

1. Read diagnostic: `code`, `blockId`, `file`, `suggestion`
2. Locate block by `id:` (not name, not line number)
3. Choose repair primitive
4. Apply patch to Yoni source
5. Re-validate entire workspace
6. Regenerate outputs only after validation passes

## Repair primitives (exactly 8)

| Primitive | Use when |
|-----------|----------|
| `ReplaceReference` | Typed ref points to wrong/renamed block |
| `CreateStub` | Referenced block missing |
| `DeleteReference` | Remove invalid reference |
| `AddField` | Entity needs new field |
| `RemoveField` | Entity field removed (breaking — add migration) |
| `RenameField` | Entity field renamed (breaking — add migration) |
| `CreateTransition` | State machine needs new transition |
| `RemoveTransition` | State transition removed |

## Patch format

```json
{
  "type": "ReplaceReference",
  "node_id": "INT_CREATE_INV_001",
  "field": "inputs[1].ref",
  "old_value": "ENT_CUSTOMER_001",
  "new_value": "ENT_ACCOUNT_001",
  "reason": "Customer renamed in MIG_CUST_V2_001"
}
```

## Impact before repair

Run impact analysis on the changed node. List affected intents, queries, views, tests before applying breaking changes.

## Never autofix

- Inventing IDs
- Changing semantics
- Patching `generated/` files
