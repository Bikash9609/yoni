"""IntentAST — strongly-typed AST for intent blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ProcessOp
from yoni.ast.query import IntentReturn
from yoni.ast.types import FieldDef, RefLink


class IntentAST(BlockBase):
    """AST node for `intent` blocks."""

    type: Literal["Intent"] = "Intent"
    inputs: list[FieldDef] = Field(default_factory=list)
    validations: list[RefLink] = Field(default_factory=list)
    process: list[ProcessOp] = Field(default_factory=list)
    emit: list[RefLink] = Field(default_factory=list)
    fail: list[RefLink] = Field(default_factory=list)
    return_spec: IntentReturn | None = None
