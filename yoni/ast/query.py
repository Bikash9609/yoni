"""QueryAST — strongly-typed AST for query blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ExprNode, OrderByDef
from yoni.ast.types import RefLink, Reference, SpannedBase


class QueryReturn(SpannedBase):
    type: str = "Entity"
    ref: Reference | None = None
    inner: Reference | None = None


class IntentReturn(SpannedBase):
    type: str = "Entity"
    ref: Reference | None = None


class QueryAST(BlockBase):
    type: Literal["Query"] = "Query"
    entity: RefLink | None = None
    where: ExprNode | None = None
    order_by: list[OrderByDef] = Field(default_factory=list)
    limit: int | None = None
    return_spec: QueryReturn | None = None
