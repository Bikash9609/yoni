"""Base AST model shared by all block kinds."""

from __future__ import annotations

from pydantic import BaseModel

from yoni.ast.types import RuntimeMetadata, SourceSpan


class BlockBase(BaseModel):
    """Universal block shape: id, name, version, desc, span, metadata."""

    id: str
    name: str
    version: int = 1
    desc: str = ""
    span: SourceSpan | None = None
    metadata: RuntimeMetadata | None = None
