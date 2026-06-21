"""WorkflowAST — strongly-typed AST for workflow blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import StepDef
from yoni.ast.types import SourceSpan


class WorkflowAST(BaseModel):
    type: Literal["Workflow"] = "Workflow"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    steps: list[StepDef] = Field(default_factory=list)
    span: SourceSpan | None = None
