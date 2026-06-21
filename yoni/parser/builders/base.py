"""Shared builder helpers for all block kinds."""

from __future__ import annotations

from typing import Any

from lark import Token

from yoni.ast.expr import (
    ChangeDef,
    EnvDef,
    ExpectOp,
    ExprBinary,
    ExprNode,
    ExprRef,
    ExprValue,
    ExprVar,
    LayoutDef,
    OrderByDef,
    ProcessOp,
    StepDef,
    TransitionDef,
)
from yoni.ast.query import QueryReturn
from yoni.ast.types import FieldDef, IndexDef, Reference, TYPE_CODE_MAP, TypeCode
from yoni.errors import ParseError, section_order_violation
from yoni.parser.draft import BlockDraft

INTENT_SECTION_ORDER = ("input", "validate", "process", "emit", "fail", "return")


def require_id(draft: BlockDraft, errors: list[ParseError]) -> bool:
    if draft.block_id:
        return True
    return False


def check_intent_section_order(draft: BlockDraft, errors: list[ParseError]) -> None:
    seen: list[str] = []
    for name in draft.sections:
        if name in INTENT_SECTION_ORDER:
            seen.append(name)
    for index, name in enumerate(seen):
        expected = INTENT_SECTION_ORDER[index]
        if name != expected:
            errors.append(
                section_order_violation(
                    expected,
                    name,
                    file=draft.file,
                    block_id=draft.block_id,
                )
            )
            break


def fields_from_section(lines: list[Any]) -> list[FieldDef]:
    result: list[FieldDef] = []
    for line in lines:
        if isinstance(line, FieldDef):
            result.append(line)
        elif isinstance(line, tuple) and len(line) == 2:
            field = field_from_parts(str(line[0]), line[1])
            if field.type_code or field.ref:
                result.append(field)
    return result


def refs_from_section(lines: list[Any]) -> list[Reference]:
    refs: list[Reference] = []
    for line in lines:
        if isinstance(line, Reference):
            refs.append(line)
        elif isinstance(line, FieldDef) and line.ref:
            refs.append(line.ref)
    return refs


def single_ref(lines: list[Any]) -> Reference | None:
    refs = refs_from_section(lines)
    return refs[0] if refs else None


def process_ops_from_section(lines: list[Any]) -> list[ProcessOp]:
    return [line for line in lines if isinstance(line, ProcessOp)]


def expr_from_section(lines: list[Any]) -> ExprNode | None:
    for line in lines:
        if isinstance(line, (ExprBinary, ExprVar, ExprValue, ExprRef)):
            return line
    return None


def indices_from_section(lines: list[Any]) -> list[IndexDef]:
    result: list[IndexDef] = []
    for line in lines:
        if isinstance(line, IndexDef):
            result.append(line)
    return result


def transitions_from_section(lines: list[Any]) -> list[TransitionDef]:
    return [line for line in lines if isinstance(line, TransitionDef)]


def steps_from_section(lines: list[Any]) -> list[StepDef]:
    return [line for line in lines if isinstance(line, StepDef)]


def expects_from_section(lines: list[Any]) -> list[ExpectOp]:
    return [line for line in lines if isinstance(line, ExpectOp)]


def order_by_from_section(lines: list[Any]) -> list[OrderByDef]:
    return [line for line in lines if isinstance(line, OrderByDef)]


def changes_from_section(lines: list[Any]) -> list[ChangeDef]:
    return [line for line in lines if isinstance(line, ChangeDef)]


def env_from_section(lines: list[Any]) -> EnvDef | None:
    entries: dict[str, str | int | bool | Reference] = {}
    for line in lines:
        if isinstance(line, tuple) and len(line) == 2:
            key, value = line
            entries[str(key)] = value
    return EnvDef(entries=entries) if entries else None


def layout_from_section(lines: list[Any]) -> LayoutDef | None:
    entries: dict[str, str | int | bool] = {}
    for line in lines:
        if isinstance(line, tuple) and len(line) == 2:
            key, value = line
            if isinstance(value, (str, int, bool)):
                entries[str(key)] = value
    return LayoutDef(entries=entries) if entries else None


def string_list_from_section(lines: list[Any]) -> list[str]:
    result: list[str] = []
    for line in lines:
        if isinstance(line, str):
            result.append(line)
    return result


def scalar_str(draft: BlockDraft, key: str, default: str = "") -> str:
    value = draft.scalars.get(key, default)
    if value is None:
        return default
    return str(value)


def scalar_int(draft: BlockDraft, key: str) -> int | None:
    value = draft.scalars.get(key)
    if value is None:
        return None
    if isinstance(value, Token):
        return int(str(value))
    return int(value)


def scalar_bool(draft: BlockDraft, key: str) -> bool:
    value = draft.scalars.get(key)
    if value is None:
        return False
    if isinstance(value, Token):
        return str(value).lower() == "true"
    return bool(value)


def scalar_ref(draft: BlockDraft, key: str) -> Reference | None:
    value = draft.scalars.get(key)
    return value if isinstance(value, Reference) else None


def return_spec_from_scalar(value: Any) -> QueryReturn | None:
    if isinstance(value, QueryReturn):
        return value
    if isinstance(value, Reference):
        return QueryReturn(type="Entity", ref=value)
    return None


def token_str(value: Any) -> str:
    if isinstance(value, Token):
        return str(value)
    return str(value)


def parse_type_code(value: Any) -> TypeCode | None:
    text = token_str(value)
    return TYPE_CODE_MAP.get(text)


def field_from_parts(
    name: str, type_value: Any, modifiers: list[Any] | None = None
) -> FieldDef:
    mods = {token_str(m).lower() for m in (modifiers or [])}
    field = FieldDef(
        name=name,
        nullable="nullable" in mods,
        unique="unique" in mods,
        secret="secret" in mods,
    )
    if isinstance(type_value, Reference):
        field.ref = type_value
    elif isinstance(type_value, TypeCode):
        field.type_code = type_value
    else:
        code = TYPE_CODE_MAP.get(token_str(type_value))
        if code:
            field.type_code = code
    return field


def make_binary(op: str, left: Any, right: Any) -> ExprBinary:
    return ExprBinary(op=op, left=_as_expr(left), right=_as_expr(right))


def _as_expr(node: Any) -> ExprNode:
    if isinstance(node, (ExprBinary, ExprVar, ExprValue, ExprRef)):
        return node
    if isinstance(node, Reference):
        return ExprRef(ref=node)
    if isinstance(node, Token):
        text = str(node)
        if text in ("true", "false"):
            return ExprValue(value=text == "true", type="boolean")
        if text.replace(".", "", 1).replace("-", "", 1).isdigit():
            if "." in text:
                return ExprValue(value=float(text), type="float")
            return ExprValue(value=int(text), type="integer")
        if text.startswith('"') and text.endswith('"'):
            return ExprValue(value=text[1:-1], type="string")
        if text.startswith("@"):
            return ExprRef(ref=Reference.parse(text))
        if "." in text:
            return ExprVar(name=text)
        return ExprVar(name=text)
    if isinstance(node, str):
        if node.startswith("@"):
            return ExprRef(ref=Reference.parse(node))
        if node in ("true", "false"):
            return ExprValue(value=node == "true", type="boolean")
        return ExprVar(name=node)
    return ExprVar(name=str(node))


def process_value_as_ast(value: Any) -> str | Reference | ExprNode:
    if isinstance(value, Reference):
        return value
    if isinstance(value, (ExprBinary, ExprVar, ExprValue, ExprRef)):
        return value
    text = token_str(value)
    if text.startswith("@"):
        return Reference.parse(text)
    if "." in text and text[0].islower():
        return ExprVar(name=text)
    return text
