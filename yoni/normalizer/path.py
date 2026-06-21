"""Infer domain and folder role from repository path."""

from __future__ import annotations

from yoni.ast.base import BlockKind

_DOMAIN_ROLES = frozenset(
    {
        "entities",
        "intents",
        "rules",
        "queries",
        "actions",
        "events",
        "states",
        "workflows",
        "constraints",
        "errors",
        "tests",
    }
)

_TOP_FOLDERS: dict[str, BlockKind | None] = {
    "project": BlockKind.PROJECT,
    "views": BlockKind.VIEW,
    "deployments": BlockKind.DEPLOYMENT,
    "migrations": BlockKind.MIGRATION,
}

_DOMAIN_FILES = frozenset({"domain.yoni", "domain.yni", "domain.yo"})


def infer_file_context(rel_path: str) -> tuple[str | None, str | None]:
    parts = rel_path.replace("\\", "/").split("/")
    domain: str | None = None
    folder_role: str | None = None

    if len(parts) >= 2 and parts[0] == "domains":
        domain = parts[1]
        if len(parts) >= 3:
            if parts[2] in _DOMAIN_FILES:
                folder_role = "domain"
            elif parts[2] in _DOMAIN_ROLES:
                folder_role = parts[2]
    elif parts[0] in _TOP_FOLDERS:
        folder_role = parts[0].rstrip("s") if parts[0] != "project" else "project"
        if parts[0] == "capabilities" and len(parts) >= 2:
            folder_role = "capability"
    return domain, folder_role
