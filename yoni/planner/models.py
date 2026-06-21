"""Execution plan pydantic models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepType(str, Enum):
    INPUT = "input"
    VALIDATE = "validate"
    PROCESS = "process"
    QUERY = "query"
    ACTION = "action"
    EMIT = "emit"
    FAIL = "fail"
    RETURN = "return"


class JobType(str, Enum):
    ENTITY_SCHEMA = "entity_schema"
    STATE_MACHINE = "state_machine"
    RULE_IMPL = "rule_impl"
    CONSTRAINT_IMPL = "constraint_impl"
    QUERY_IMPL = "query_impl"
    ACTION_IMPL = "action_impl"
    ERROR_DEF = "error_def"
    INTENT_HANDLER = "intent_handler"


class InputFieldPlan(BaseModel):
    name: str
    type_name: str | None = None
    type_code: str | None = None
    ref: str | None = None


class ProcessOpPlan(BaseModel):
    op: str
    target: str | None = None
    entity: str | None = None
    value: Any = None


class PlanStep(BaseModel):
    order: int
    type: StepType
    fields: list[InputFieldPlan] = Field(default_factory=list)
    block: str | None = None
    block_kind: str | None = None
    ops: list[ProcessOpPlan] = Field(default_factory=list)
    query: str | None = None
    action: str | None = None
    result: str | None = None
    event: str | None = None
    error: str | None = None
    refs: list[str] = Field(default_factory=list)


class PlannedArtifact(BaseModel):
    job: JobType
    block: str
    depends: list[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    intent: str
    name: str
    domain: str | None = None
    desc: str = ""
    metadata: dict[str, Any] | None = None
    steps: list[PlanStep] = Field(default_factory=list)
    artifacts: list[PlannedArtifact] = Field(default_factory=list)
    version: int = 1
