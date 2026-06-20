---
name: yoni-author
description: Authors Yoni specification blocks following rigid syntax, folder placement, IDs, and typed references. Use when writing or editing .yoni/.yni/.yo files, creating entities, intents, rules, workflows, or any Yoni block.
---

# Yoni Authoring

## Before writing

1. Read `MANDATORY.md` for philosophy
2. Read `docs/03-final-yoni-specs.md` for AST schemas (authoritative)
3. Confirm canonical folder for block type

## Authoring checklist

- [ ] One top-level block per file
- [ ] kebab-case filename matches block semantically
- [ ] `id:` with correct prefix (`ENT_`, `INT_`, etc.)
- [ ] `desc:` present
- [ ] Typed references: `@Entity.X`, `@Intent.X` — never strings
- [ ] Intent sections in order: `input:` → `validate:` → `process:` → `emit:` → `fail:` → `return:`
- [ ] Rules are machine-checkable expressions, not prose
- [ ] Actions declare side effects only; logic stays in rules/intents
- [ ] Breaking entity/state changes include a `migration` block

## Intent template

```yoni
intent CreateInvoice

id: INT_CREATE_INV_001
desc:
  Creates invoice for an approved order.

input:

validate:

process:

emit:

fail:

return:
```

## Entity template

```yoni
entity Customer

id: ENT_CUSTOMER_001
desc:
  Primary customer record.

fields:
  customer_id: s
  email: s
  active: b
```

## After writing

Run linter validation. Fix all diagnostics before requesting code generation.

## Reference

Full block glossary and ID prefixes: [reference.md](reference.md)
