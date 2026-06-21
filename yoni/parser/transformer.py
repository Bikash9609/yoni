"""Parse tree → Pydantic AST transformer."""

from __future__ import annotations

from typing import Any

from lark import Token, Transformer, v_args

from yoni.ast.base import BlockKind, YoniBlock
from yoni.ast.expr import (
    ChangeDef,
    ExpectOp,
    ExprBinary,
    ExprRef,
    ExprValue,
    ExprVar,
    OrderByDef,
    ProcessOp,
    StepDef,
    TransitionDef,
    WhenDef,
)
from yoni.ast.query import QueryReturn
from yoni.ast.types import FieldDef, IndexDef, Reference, TYPE_CODE_MAP, TypeCode
from yoni.errors import ParseError, missing_required_field
from yoni.parser.builders import build_block
from yoni.parser.builders.base import field_from_parts, make_binary, process_value_as_ast
from yoni.parser.draft import BlockDraft


class YoniTransformer(Transformer):
    """Walk Lark parse tree and produce a YoniBlock + diagnostics."""

    def __init__(self, *, file: str = "<stdin>") -> None:
        super().__init__()
        self.file = file

    def start(self, items: list[Any]) -> tuple[YoniBlock | None, list[ParseError]]:
        return items[0]

    def block(self, items: list[Any]) -> tuple[YoniBlock | None, list[ParseError]]:
        header: tuple[BlockKind, str] = items[0]
        body_items: list[Any] = items[1] if len(items) > 1 else []
        kind, name = header
        draft = BlockDraft(kind=kind, name=name, file=self.file)
        self._collect_body(draft, body_items)
        if not draft.block_id:
            draft.errors.append(
                missing_required_field("id", file=draft.file, block_id=draft.block_id)
            )
        return build_block(draft)

    def block_header(self, items: list[Any]) -> tuple[BlockKind, str]:
        keyword = str(items[0])
        name = str(items[1])
        return BlockKind.from_keyword(keyword), name

    def block_body(self, items: list[Any]) -> list[Any]:
        return [item for item in items if item is not None]

    def body_item(self, item: Any) -> Any:
        return item

    def top_id(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "id", "value": str(items[0])}

    def top_desc(self, items: list[Any]) -> dict[str, Any]:
        desc = items[0] if items else ""
        return {"scalar": "desc", "value": desc if isinstance(desc, str) else ""}

    def top_limit(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "limit", "value": items[0]}

    def top_code(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "code", "value": str(items[0])}

    def top_http_status(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "http_status", "value": items[0]}

    def top_from_version(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "from_version", "value": items[0]}

    def top_to_version(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "to_version", "value": items[0]}

    def top_breaking(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "breaking", "value": items[0]}

    def top_region(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "region", "value": str(items[0])}

    def SCALAR_TEXT(self, token: Token) -> str:
        return str(token)

    def top_replicas(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "replicas", "value": items[0]}

    def top_entity(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "entity", "value": items[0]}

    def top_uses(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "uses", "value": items[0]}

    def top_query(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "query", "value": items[0]}

    def top_return(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "return", "value": items[0]}

    def top_message(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "message", "value": str(items[0])}

    def desc_body(self, items: list[Any]) -> str:
        lines: list[str] = []
        for item in items:
            if isinstance(item, str):
                lines.append(item.strip())
            elif isinstance(item, Token):
                lines.append(str(item).strip())
        return " ".join(line for line in lines if line)

    def desc_line(self, items: list[Any]) -> str:
        return str(items[0]).strip()

    def section(self, items: list[Any]) -> tuple[str, list[Any]]:
        section_name = str(items[0]).lower()
        body: list[Any] = []
        for item in reversed(items):
            if isinstance(item, list):
                body = item
                break
        return section_name, body

    def section_body(self, items: list[Any]) -> list[Any]:
        if not items:
            return []
        return [item for item in items if item is not None and item != ""]

    def section_line(self, items: list[Any]) -> Any:
        return items[0] if items else None

    def field_line(self, items: list[Any]) -> FieldDef:
        name = str(items[0])
        type_value = items[1]
        modifiers = items[2:] if len(items) > 2 else []
        return field_from_parts(name, type_value, modifiers)

    def field_modifier(self, items: list[Any]) -> str:
        return str(items[0]).lower()

    def index_line(self, items: list[Any]) -> IndexDef:
        return IndexDef(field=str(items[0]), type=str(items[1]).lower())

    def ref_line(self, items: list[Any]) -> Reference:
        return items[0]

    def process_value(self, items: list[Any]) -> Any:
        return process_value_as_ast(items[0])

    def process_new(self, items: list[Any]) -> ProcessOp:
        type_ref = items[-1]
        if isinstance(type_ref, Token):
            type_ref = Reference.parse(str(type_ref))
        return ProcessOp(op="new", target=str(items[-2]), type_ref=type_ref)

    def process_set(self, items: list[Any]) -> ProcessOp:
        value = items[-1]
        if isinstance(value, Token):
            value = process_value_as_ast(value)
        return ProcessOp(
            op="set",
            target=str(items[-2]),
            value=value,
        )

    def process_save(self, items: list[Any]) -> ProcessOp:
        return ProcessOp(op="save", target=str(items[-1]))

    def state_line(self, items: list[Any]) -> str:
        return str(items[0])

    def transition_line(self, items: list[Any]) -> TransitionDef:
        return TransitionDef(from_state=str(items[0]), to_state=str(items[-1]))

    def step_line(self, items: list[Any]) -> StepDef:
        return StepDef(name=str(items[0]), intent=items[1])

    def kv_line(self, items: list[Any]) -> tuple[str, Any]:
        return str(items[0]), items[1]

    def kv_value(self, items: list[Any]) -> Any:
        value = items[0]
        if isinstance(value, Token):
            text = str(value)
            if text.isdigit():
                return int(text)
            if text in ("true", "false"):
                return text == "true"
            return text
        return value

    def expect_eq(self, items: list[Any]) -> ExpectOp:
        return ExpectOp(
            op="eq",
            left=str(items[-2]),
            right=process_value_as_ast(items[-1]),
        )

    def expect_emitted(self, items: list[Any]) -> ExpectOp:
        event = items[-1]
        if isinstance(event, Token):
            event = Reference.parse(str(event))
        return ExpectOp(op="emitted", event=event)

    def expr_line(self, items: list[Any]) -> Any:
        return items[0]

    def when_intent(self, items: list[Any]) -> WhenDef:
        intent = items[-1]
        if isinstance(intent, Token):
            intent = Reference.parse(str(intent))
        return WhenDef(intent=intent)

    def when_input(self, items: list[Any]) -> tuple[str, Any]:
        return str(items[0]), items[1]

    def change_line(self, items: list[Any]) -> ChangeDef:
        entity = items[0]
        field_name = str(items[1])
        type_code = str(items[2])
        modifiers = {str(m).lower() for m in items[3:]} if len(items) > 3 else set()
        return ChangeDef(
            change_type="AddField",
            entity=entity,
            field_name=field_name,
            type_code=type_code,
            nullable="nullable" in modifiers,
        )

    def layout_line(self, items: list[Any]) -> tuple[str, Any]:
        return str(items[0]), items[1]

    def type_spec(self, items: list[Any]) -> TypeCode | Reference:
        value = items[0]
        if isinstance(value, Reference):
            return value
        if isinstance(value, TypeCode):
            return value
        token = str(value)
        if token.startswith("@"):
            return Reference.parse(token)
        return TYPE_CODE_MAP[token]

    def return_spec(self, items: list[Any]) -> Reference | QueryReturn:
        if len(items) == 1:
            return items[0]
        return QueryReturn(type="list", inner=items[1])

    @v_args(inline=True)
    def TYPE_CODE(self, token: Token) -> TypeCode:
        return TYPE_CODE_MAP[str(token)]

    @v_args(inline=True)
    def REFERENCE(self, token: Token) -> Reference:
        return Reference.parse(str(token))

    def content_line(self, items: list[Any]) -> str:
        text = str(items[0]).strip()
        if text.startswith("@"):
            return Reference.parse(text)
        return text

    def eq_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("==", items[0], items[1])

    def ne_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("!=", items[0], items[1])

    def ge_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary(">=", items[0], items[1])

    def le_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("<=", items[0], items[1])

    def gt_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary(">", items[0], items[1])

    def lt_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("<", items[0], items[1])

    def add_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("+", items[0], items[1])

    def sub_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("-", items[0], items[1])

    def mul_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("*", items[0], items[1])

    def div_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("/", items[0], items[1])

    def number_atom(self, items: list[Any]) -> ExprValue:
        text = str(items[0])
        if "." in text:
            return ExprValue(value=float(text), type="float")
        return ExprValue(value=int(text), type="integer")

    def bool_atom(self, items: list[Any]) -> ExprValue:
        return ExprValue(value=str(items[0]) == "true", type="boolean")

    def string_atom(self, items: list[Any]) -> ExprValue:
        text = str(items[0])
        return ExprValue(value=text[1:-1], type="string")

    def ref_atom(self, items: list[Any]) -> ExprRef:
        return ExprRef(ref=items[0])

    def var_atom(self, items: list[Any]) -> ExprVar:
        return ExprVar(name=str(items[0]))

    def enum_atom(self, items: list[Any]) -> ExprVar:
        return ExprVar(name=str(items[0]))

    def name_atom(self, items: list[Any]) -> ExprVar:
        return ExprVar(name=str(items[0]))

    def _collect_body(self, draft: BlockDraft, body_items: list[Any]) -> None:
        for item in body_items:
            if isinstance(item, dict) and "scalar" in item:
                key = item["scalar"]
                value = item["value"]
                if key == "id":
                    draft.block_id = str(value)
                elif key == "desc":
                    draft.desc = str(value)
                else:
                    draft.scalars[key] = value
                continue
            if isinstance(item, tuple):
                section_name, lines = item
                draft.sections.setdefault(section_name, []).extend(
                    line for line in lines if line is not None
                )
