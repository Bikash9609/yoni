"""Per-block allowed and mandatory section validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind

ALLOWED_SECTIONS: dict[BlockKind, frozenset[str]] = {
    BlockKind.PROJECT: frozenset({"domains", "capabilities", "env"}),
    BlockKind.DOMAIN: frozenset({"entities", "rules", "events"}),
    BlockKind.ENTITY: frozenset({"fields", "indices"}),
    BlockKind.STATE: frozenset({"states", "transitions"}),
    BlockKind.EVENT: frozenset({"payload"}),
    BlockKind.INTENT: frozenset(
        {"input", "validate", "process", "emit", "fail"}
    ),
    BlockKind.RULE: frozenset({"expression", "when"}),
    BlockKind.QUERY: frozenset({"where", "order_by", "entity"}),
    BlockKind.ACTION: frozenset({"input", "result", "uses"}),
    BlockKind.CONSTRAINT: frozenset({"check", "entity"}),
    BlockKind.WORKFLOW: frozenset({"steps"}),
    BlockKind.ERROR: frozenset({"message"}),
    BlockKind.TEST: frozenset({"given", "when", "expect"}),
    BlockKind.CAPABILITY: frozenset({"actions", "config"}),
    BlockKind.VIEW: frozenset({"fields", "actions", "layout", "query"}),
    BlockKind.DEPLOYMENT: frozenset({"services", "env", "resources"}),
    BlockKind.MIGRATION: frozenset({"changes", "affects"}),
}

MANDATORY_SECTIONS: dict[BlockKind, frozenset[str]] = {
    BlockKind.ENTITY: frozenset({"fields"}),
    BlockKind.RULE: frozenset({"expression"}),
    BlockKind.QUERY: frozenset({"where"}),
    BlockKind.CONSTRAINT: frozenset({"check"}),
    BlockKind.WORKFLOW: frozenset({"steps"}),
    BlockKind.TEST: frozenset({"when", "expect"}),
    BlockKind.MIGRATION: frozenset({"changes"}),
}

SCALAR_KEYS: dict[BlockKind, frozenset[str]] = {
    BlockKind.QUERY: frozenset({"entity", "limit", "return"}),
    BlockKind.INTENT: frozenset({"return", "sla", "criticality", "owner"}),
    BlockKind.ACTION: frozenset({"uses"}),
    BlockKind.CONSTRAINT: frozenset({"entity"}),
    BlockKind.VIEW: frozenset({"query"}),
    BlockKind.ERROR: frozenset({"code", "http_status", "message"}),
    BlockKind.MIGRATION: frozenset(
        {"from_version", "to_version", "breaking"}
    ),
    BlockKind.DEPLOYMENT: frozenset({"region", "replicas"}),
}
