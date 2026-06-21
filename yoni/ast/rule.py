"""RuleAST — strongly-typed AST for rule blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from yoni.ast.expr import ExprNode
from yoni.ast.types import SourceSpan


class RuleAST(BaseModel):
    type: Literal["Rule"] = "Rule"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    expression: ExprNode | None = None
    span: SourceSpan | None = None
