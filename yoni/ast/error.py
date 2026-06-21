"""ErrorAST — strongly-typed AST for error blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from yoni.ast.types import SourceSpan


class ErrorAST(BaseModel):
    type: Literal["Error"] = "Error"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    code: str = ""
    http_status: int | None = None
    message: str = ""
    span: SourceSpan | None = None
