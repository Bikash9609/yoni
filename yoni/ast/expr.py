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


class ExprBinary(BaseModel):
    kind: Literal["binary"] = "binary"
    op: str
    left: ExprNode
    right: ExprNode


ExprNode = Annotated[
    Union[ExprVar, ExprValue, ExprRef, ExprBinary],
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
    right: str | Reference | None = None
    event: Reference | None = None


class OrderByDef(BaseModel):
    field: str
    direction: str = "asc"


class TransitionDef(BaseModel):
    from_state: str
    to_state: str


class StepDef(BaseModel):
    name: str
    intent: Reference


class WhenDef(BaseModel):
    intent: Reference | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


class EnvDef(BaseModel):
    entries: dict[str, str | int | bool | Reference] = Field(default_factory=dict)


class LayoutDef(BaseModel):
    entries: dict[str, str | int | bool] = Field(default_factory=dict)


class ChangeDef(BaseModel):
    change_type: str
    entity: Reference | None = None
    field_name: str | None = None
    type_code: str | None = None
    nullable: bool = False
