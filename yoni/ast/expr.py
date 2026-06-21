"""Shared expression and structured line AST nodes."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

from yoni.ast.types import Reference


class ExprVar(BaseModel):
    kind: Literal["var"] = "var"
    name: str


class ExprValue(BaseModel):
    kind: Literal["value"] = "value"
    value: str | int | float | bool
    type: str = "string"


class ExprRef(BaseModel):
    kind: Literal["ref"] = "ref"
    ref: Reference


class ExprCall(BaseModel):
    kind: Literal["call"] = "call"
    op: str
    args: list[ExprNode] = Field(default_factory=list)


class ExprBinary(BaseModel):
    kind: Literal["binary"] = "binary"
    op: str
    left: ExprNode
    right: ExprNode


ExprNode = Annotated[
    Union[ExprVar, ExprValue, ExprRef, ExprCall, ExprBinary],
    Field(discriminator="kind"),
]


class ProcessOp(BaseModel):
    op: str
    target: str | None = None
    type_ref: Reference | None = None
    value: str | Reference | ExprNode | None = None


class ExpectOp(BaseModel):
    op: str
    left: str | None = None
    right: str | Reference | ExprNode | None = None
    event: Reference | None = None


class OrderByDef(BaseModel):
    field: str
    direction: str = "asc"


class TransitionDef(BaseModel):
    from_state: str
    to_state: str


class StepInputValue(BaseModel):
    step: str | None = None
    field: str | None = None
    ref: Reference | None = None
    literal: str | int | float | bool | None = None


class StepInput(BaseModel):
    name: str
    value: StepInputValue | Reference | str | int | float | bool


class StepDef(BaseModel):
    name: str
    intent: Reference
    inputs: list[StepInput] = Field(default_factory=list)


class WhenInput(BaseModel):
    name: str
    value: Reference | str | int | float | bool | ExprNode


class WhenDef(BaseModel):
    intent: Reference | None = None
    inputs: list[WhenInput] = Field(default_factory=list)


class EnvDef(BaseModel):
    entries: dict[str, str | int | bool | Reference] = Field(default_factory=dict)


class LayoutDef(BaseModel):
    entries: dict[str, str | int | bool] = Field(default_factory=dict)


class MigrationField(BaseModel):
    name: str
    type: str | None = None
    type_code: str | None = None
    nullable: bool = False


class ChangeDef(BaseModel):
    change_type: str
    entity: Reference | None = None
    field: MigrationField | None = None
    old_name: str | None = None
    new_name: str | None = None
    old_ref: Reference | None = None
    new_ref: Reference | None = None
    from_state: str | None = None
    to_state: str | None = None
