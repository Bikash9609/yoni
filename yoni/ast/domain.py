"""DomainAST — strongly-typed AST for domain blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.types import RefLink


class DomainAST(BlockBase):
    type: Literal["Domain"] = "Domain"
    entities: list[RefLink] = Field(default_factory=list)
    rules: list[RefLink] = Field(default_factory=list)
    events: list[RefLink] = Field(default_factory=list)
