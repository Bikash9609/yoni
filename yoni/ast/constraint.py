"""ConstraintAST — strongly-typed AST for constraint blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from yoni.ast.expr import ExprNode
from yoni.ast.types import Reference, SourceSpan


class ConstraintAST(BaseModel):
    type: Literal["Constraint"] = "Constraint"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    entity: Reference | None = None
    check: ExprNode | None = None
    span: SourceSpan | None = None
