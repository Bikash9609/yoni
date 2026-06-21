"""ErrorAST — strongly-typed AST for error blocks."""

from __future__ import annotations

from typing import Literal

from yoni.ast.block_base import BlockBase


class ErrorAST(BlockBase):
    type: Literal["Error"] = "Error"
    code: str = ""
    http_status: int | None = None
    message: str = ""
