"""Shared expression and structured line AST nodes."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from yoni.ast.types import Reference, SpannedBase


class ExprVar(SpannedBase):
    kind: Literal["var"] = "var"
    name: str


class ExprValue(SpannedBase):
    kind: Literal["value"] = "value"
    value: str | int | float | bool
    type: str = "string"


class ExprRef(SpannedBase):
    kind: Literal["ref"] = "ref"
    ref: Reference


class ExprCall(SpannedBase):
    kind: Literal["call"] = "call"
    op: str
    args: list[ExprNode] = Field(default_factory=list)


class ExprBinary(SpannedBase):
    kind: Literal["binary"] = "binary"
    op: str
    left: ExprNode
    right: ExprNode


ExprNode = Annotated[
    Union[ExprVar, ExprValue, ExprRef, ExprCall, ExprBinary],
    Field(discriminator="kind"),
]


class ProcessOp(SpannedBase):
    op: str
    target: str | None = None
    type_ref: Reference | None = None
    value: str | Reference | ExprNode | None = None


class ExpectOp(SpannedBase):
    op: str
    left: str | None = None
    right: str | Reference | ExprNode | None = None
    event: Reference | None = None


class OrderByDef(SpannedBase):
    field: str
    direction: str = "asc"


class TransitionDef(SpannedBase):
    from_state: str
    to_state: str


class StepInputValue(SpannedBase):
    step: str | None = None
    field: str | None = None
    ref: Reference | None = None
    literal: str | int | float | bool | None = None


class StepInput(SpannedBase):
    name: str
    value: StepInputValue | Reference | str | int | float | bool


class StepDef(SpannedBase):
    name: str
    intent: Reference
    inputs: list[StepInput] = Field(default_factory=list)


class WhenInput(SpannedBase):
    name: str
    value: Reference | str | int | float | bool | ExprNode


class WhenDef(SpannedBase):
    intent: Reference | None = None
    inputs: list[WhenInput] = Field(default_factory=list)


class EnvDef(SpannedBase):
    entries: dict[str, str | int | bool | Reference] = Field(default_factory=dict)


class LayoutDef(SpannedBase):
    entries: dict[str, str | int | bool] = Field(default_factory=dict)


class MigrationField(SpannedBase):
    name: str
    type: str | None = None
    type_code: str | None = None
    nullable: bool = False


class ChangeDef(SpannedBase):
    change_type: str
    entity: Reference | None = None
    field: MigrationField | None = None
    old_name: str | None = None
    new_name: str | None = None
    old_ref: Reference | None = None
    new_ref: Reference | None = None
    from_state: str | None = None
    to_state: str | None = None
