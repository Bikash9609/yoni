"""IntentAST — strongly-typed AST for intent blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import ProcessOp
from yoni.ast.types import FieldDef, Reference, SourceSpan


class IntentAST(BaseModel):
    """AST node for `intent` blocks."""

    type: Literal["Intent"] = "Intent"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    inputs: list[FieldDef] = Field(default_factory=list)
    validations: list[Reference] = Field(default_factory=list)
    process: list[ProcessOp] = Field(default_factory=list)
    emit: list[Reference] = Field(default_factory=list)
    fail: list[Reference] = Field(default_factory=list)
    return_ref: Reference | None = None
    span: SourceSpan | None = None
