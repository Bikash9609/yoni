"""ConstraintAST — strongly-typed AST for constraint blocks."""

from __future__ import annotations

from typing import Literal

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ExprNode
from yoni.ast.types import RefLink


class ConstraintAST(BlockBase):
    type: Literal["Constraint"] = "Constraint"
    entity: RefLink | None = None
    check: ExprNode | None = None
