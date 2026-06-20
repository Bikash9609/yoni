"""IntentAST — strongly-typed AST for intent blocks.

Schema: docs/03-final-yoni-specs.md § IntentAST
Section order: input → validate → process → emit → fail → return
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from yoni.ast.types import FieldDef, RawLine, Reference, SourceSpan


class IntentAST(BaseModel):
    """AST node for `intent` blocks."""

    type: Literal["Intent"] = "Intent"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    inputs: list[FieldDef] = Field(default_factory=list)
    validations: list[Reference] = Field(default_factory=list)
    process: list[RawLine | dict[str, Any]] = Field(default_factory=list)
    emit: list[Reference] = Field(default_factory=list)
    fail: list[Reference] = Field(default_factory=list)
    return_ref: Reference | None = None
    span: SourceSpan | None = None
