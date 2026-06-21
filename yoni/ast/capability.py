"""CapabilityAST — strongly-typed AST for capability blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.types import FieldDef, RefLink


class CapabilityAST(BlockBase):
    type: Literal["Capability"] = "Capability"
    actions: list[RefLink] = Field(default_factory=list)
    config: list[FieldDef] = Field(default_factory=list)
