"""Forbid string literals where typed @Type.Name references are required."""

from __future__ import annotations

import re

from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import string_ref_forbidden
from yoni.validator.models import ValidationError

_TYPED_NAME = re.compile(r"^[A-Z][a-z]+\.[A-Z][A-Za-z0-9_]*$")
_REF_KEYS = frozenset(
    {
        "entity",
        "intent",
        "uses",
        "query",
        "return",
        "validations",
        "emit",
        "fail",
        "domains",
        "capabilities",
        "entities",
        "rules",
        "events",
        "actions",
        "services",
        "affects",
    }
)


def _looks_like_ref(value: str) -> bool:
    return value.startswith("@") or bool(_TYPED_NAME.match(value))


def _walk(
    obj: object,
    *,
    block_id: str,
    file: str,
    errors: list[ValidationError],
    key: str | None = None,
) -> None:
    if isinstance(obj, dict):
        if obj.get("kind") == "value" and obj.get("type") == "string":
            value = str(obj.get("value", ""))
            if _looks_like_ref(value):
                errors.append(
                    string_ref_forbidden(value, file=file, block_id=block_id)
                )
        elif key in _REF_KEYS and isinstance(obj.get("kind"), str) and obj["kind"] == "value":
            value = obj.get("value")
            if isinstance(value, str) and _looks_like_ref(value):
                errors.append(
                    string_ref_forbidden(value, file=file, block_id=block_id)
                )
        for child_key, child in obj.items():
            _walk(child, block_id=block_id, file=file, errors=errors, key=str(child_key))
        return
    if isinstance(obj, list):
        for item in obj:
            _walk(item, block_id=block_id, file=file, errors=errors, key=key)


def check_string_refs(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        _walk(
            block.body,
            block_id=block.block_id,
            file=block.file.rel_path,
            errors=errors,
        )
    return errors
