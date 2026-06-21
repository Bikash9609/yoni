"""QueryAST — strongly-typed AST for query blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import ExprNode, OrderByDef
from yoni.ast.types import Reference, SourceSpan


class QueryReturn(BaseModel):
    type: str = "Entity"
    ref: Reference | None = None
    inner: Reference | None = None


class QueryAST(BaseModel):
    type: Literal["Query"] = "Query"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    entity: Reference | None = None
    where: ExprNode | None = None
    order_by: list[OrderByDef] = Field(default_factory=list)
    limit: int | None = None
    return_spec: QueryReturn | None = None
    span: SourceSpan | None = None
