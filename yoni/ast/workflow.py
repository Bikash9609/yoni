"""WorkflowAST — strongly-typed AST for workflow blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import StepDef


class WorkflowAST(BlockBase):
    type: Literal["Workflow"] = "Workflow"
    steps: list[StepDef] = Field(default_factory=list)
