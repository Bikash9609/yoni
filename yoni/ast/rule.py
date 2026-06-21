"""RuleAST — strongly-typed AST for rule blocks."""

from __future__ import annotations

from typing import Literal

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ExprNode


class RuleAST(BlockBase):
    type: Literal["Rule"] = "Rule"
    expression: ExprNode | None = None
