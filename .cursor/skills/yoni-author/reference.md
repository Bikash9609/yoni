# Yoni Block Reference

Source: `docs/03-final-yoni-specs.md`

## Block glossary

| Block | ID Prefix | Folder |
|-------|-----------|--------|
| project | `PROJ_` | `project/` |
| domain | `DOM_` | `domains/<name>/domain.yoni` |
| entity | `ENT_` | `domains/<name>/entities/` |
| state | `STS_` | `domains/<name>/states/` |
| rule | `RULE_` | `domains/<name>/rules/` |
| query | `QUERY_` | `domains/<name>/queries/` |
| intent | `INT_` | `domains/<name>/intents/` |
| action | `ACT_` | `domains/<name>/actions/` |
| event | `EVT_` | `domains/<name>/events/` |
| workflow | `WF_` | `domains/<name>/workflows/` |
| constraint | `CNST_` | `domains/<name>/constraints/` |
| error | `ERR_` | `domains/<name>/errors/` |
| test | `TST_` | `domains/<name>/tests/` |
| capability | `CAP_` | `capabilities/<name>/` |
| view | `VIEW_` | `views/` |
| deployment | `DEP_` | `deployments/` |
| migration | `MIG_` | `migrations/` |

## Type codes

| Code | Type |
|------|------|
| `s` | string |
| `i` | integer |
| `f` | float |
| `b` | boolean |
| `t` | timestamp |

## Breaking change rules

| Change | Breaking? |
|--------|-----------|
| Add field | No |
| Remove/rename field | Yes |
| Add state/transition | No |
| Remove state/transition | Yes |
| Add/remove intent input | Yes |
