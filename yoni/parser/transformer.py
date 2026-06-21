"""Parse tree → Pydantic AST transformer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from lark import Token, Transformer, v_args

from yoni.ast.base import BlockKind, YoniBlock
from yoni.ast.expr import (
    ChangeDef,
    ExpectOp,
    ExprBinary,
    ExprCall,
    ExprRef,
    ExprValue,
    ExprVar,
    MigrationField,
    OrderByDef,
    ProcessOp,
    StepDef,
    TransitionDef,
    WhenDef,
)
from yoni.ast.query import QueryReturn
from yoni.ast.types import FieldDef, IndexDef, Reference, TYPE_CODE_MAP, TypeCode
from yoni.errors import ParseError, unknown_section, duplicate_section
from yoni.parser.builders import build_block
from yoni.parser.builders.base import (
    field_from_parts,
    make_binary,
    process_value_as_ast,
    strip_quotes,
)
from yoni.parser.draft import BlockDraft
from yoni.parser.sections import ALLOWED_SECTIONS
from yoni.ast.types import SourceSpan


class YoniTransformer(Transformer):
    """Walk Lark parse tree and produce a YoniBlock + diagnostics."""

    def __init__(self, *, file: str = "<stdin>") -> None:
        super().__init__()
        self.file = file

    def start(self, items: list[Any]) -> tuple[YoniBlock | None, list[ParseError]]:
        return items[0]

    @v_args(meta=True)
    def block(self, meta: Any, items: list[Any]) -> tuple[YoniBlock | None, list[ParseError]]:
        header: tuple[BlockKind, str] = items[0]
        body_items: list[Any] = items[1] if len(items) > 1 else []
        kind, name = header
        draft = BlockDraft(kind=kind, name=name, file=self.file)
        draft.span = _span(meta, self.file)
        self._collect_body(draft, body_items)
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

    def top_sla(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "sla", "value": str(items[0])}

    def top_criticality(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "criticality", "value": str(items[0])}

    def top_owner(self, items: list[Any]) -> dict[str, Any]:
        return {"scalar": "owner", "value": str(items[0])}

    def return_section(self, items: list[Any]) -> dict[str, Any]:
        spec = items[0] if items else None
        return {"scalar": "return", "value": spec}

    def return_section_body(self, items: list[Any]) -> Any:
        return items[0] if items else None

    def SCALAR_TEXT(self, token: Token) -> str:
        return str(token)

    def DURATION(self, token: Token) -> str:
        return str(token)

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

    @v_args(meta=True)
    def field_line(self, meta: Any, items: list[Any]) -> FieldDef:
        name = str(items[0])
        type_value = items[1]
        modifiers = items[2:] if len(items) > 2 else []
        return _with_span(field_from_parts(name, type_value, modifiers), meta, self.file)

    def field_modifier(self, items: list[Any]) -> str:
        return str(items[0]).lower()

    @v_args(meta=True)
    def index_line(self, meta: Any, items: list[Any]) -> IndexDef:
        return _with_span(IndexDef(field=str(items[0]), type=str(items[1]).lower()), meta, self.file)

    def name_line(self, items: list[Any]) -> str:
        return str(items[0])

    def order_by_line(self, items: list[Any]) -> OrderByDef:
        return OrderByDef(field=str(items[0]), direction=str(items[1]).lower())

    def ref_line(self, items: list[Any]) -> Reference:
        return items[0]

    def process_value(self, items: list[Any]) -> Any:
        value = items[0]
        if isinstance(value, Token) and value.type == "STRING":
            return strip_quotes(str(value))
        return process_value_as_ast(value)

    def process_new(self, items: list[Any]) -> ProcessOp:
        type_ref = items[-1]
        if isinstance(type_ref, Token):
            type_ref = Reference.parse(str(type_ref))
        return ProcessOp(op="new", target=str(items[-2]), type_ref=type_ref)

    def process_set(self, items: list[Any]) -> ProcessOp:
        value = items[-1]
        if isinstance(value, Token):
            value = process_value_as_ast(value)
        return ProcessOp(op="set", target=str(items[-2]), value=value)

    def process_save(self, items: list[Any]) -> ProcessOp:
        return ProcessOp(op="save", target=str(items[-1]))

    def state_line(self, items: list[Any]) -> str:
        return str(items[0])

    def transition_line(self, items: list[Any]) -> TransitionDef:
        return TransitionDef(from_state=str(items[0]), to_state=str(items[-1]))

    def step_line_simple(self, items: list[Any]) -> StepDef:
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
            return strip_quotes(text)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            return strip_quotes(value)
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

    def expect_value(self, items: list[Any]) -> Any:
        return process_value_as_ast(items[0])

    def expr_line(self, items: list[Any]) -> Any:
        return items[0]

    def when_intent(self, items: list[Any]) -> WhenDef:
        intent = items[-1]
        if isinstance(intent, Token):
            intent = Reference.parse(str(intent))
        return WhenDef(intent=intent)

    def when_input(self, items: list[Any]) -> tuple[str, Any]:
        value = items[1]
        if isinstance(value, Token) and value.type == "ID":
            value = str(value)
        elif not isinstance(value, (str, Reference, ExprBinary, ExprVar, ExprValue, ExprRef, ExprCall)):
            value = process_value_as_ast(value)
        return str(items[0]), value

    def when_value(self, items: list[Any]) -> Any:
        value = items[0]
        if isinstance(value, Token) and value.type in ("ID", "STRING"):
            text = str(value)
            return strip_quotes(text) if value.type == "STRING" else text
        return process_value_as_ast(value)

    def change_add_field(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        entity = filtered[0]
        field_name = str(filtered[1])
        type_code_val = filtered[2]
        tc = type_code_val.value if isinstance(type_code_val, TypeCode) else str(type_code_val)
        modifiers = {str(m).lower() for m in filtered[3:]} if len(filtered) > 3 else set()
        return ChangeDef(
            change_type="AddField",
            entity=entity,
            field=MigrationField(
                name=field_name,
                type_code=tc,
                type=TYPE_CODE_MAP[tc].full_name if tc in TYPE_CODE_MAP else None,
                nullable="nullable" in modifiers,
            ),
        )

    def change_remove_field(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        return ChangeDef(
            change_type="RemoveField",
            entity=filtered[0],
            field=MigrationField(name=str(filtered[1])),
        )

    def change_rename_field(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        return ChangeDef(
            change_type="RenameField",
            entity=filtered[0],
            old_name=str(filtered[1]),
            new_name=str(filtered[2]),
        )

    def change_replace_ref(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        return ChangeDef(
            change_type="ReplaceReference",
            old_ref=filtered[0],
            new_ref=filtered[1],
        )

    def change_create_trans(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        return ChangeDef(
            change_type="CreateTransition",
            from_state=str(filtered[0]),
            to_state=str(filtered[1]),
        )

    def change_remove_trans(self, items: list[Any]) -> ChangeDef:
        filtered = _filter_change_items(items)
        return ChangeDef(
            change_type="RemoveTransition",
            from_state=str(filtered[0]),
            to_state=str(filtered[1]),
        )

    def return_spec_line(self, items: list[Any]) -> QueryReturn | Reference:
        return items[0]

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
        inner = next((i for i in items if isinstance(i, Reference)), None)
        return QueryReturn(type="list", inner=inner)

    @v_args(inline=True)
    def TYPE_CODE(self, token: Token) -> TypeCode:
        return TYPE_CODE_MAP[str(token)]

    @v_args(inline=True)
    def REFERENCE(self, token: Token) -> Reference:
        ref = Reference.parse(str(token))
        span = SourceSpan(
            file=self.file,
            start_line=token.line or 0,
            end_line=getattr(token, "end_line", None) or token.line or 0,
            start_column=token.column or 0,
            end_column=getattr(token, "end_column", None) or token.column or 0,
        )
        return ref.model_copy(update={"span": span})

    def eq_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("==", items[0], items[-1])

    def ne_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("!=", items[0], items[-1])

    def ge_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary(">=", items[0], items[-1])

    def le_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("<=", items[0], items[-1])

    def gt_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary(">", items[0], items[-1])

    def lt_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("<", items[0], items[-1])

    def add_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("+", items[0], items[-1])

    def sub_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("-", items[0], items[-1])

    def mul_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("*", items[0], items[-1])

    def div_expr(self, items: list[Any]) -> ExprBinary:
        return make_binary("/", items[0], items[-1])

    def factor(self, items: list[Any]) -> Any:
        return items[0]

    def paren_factor(self, items: list[Any]) -> Any:
        return items[0]

    def call_expr(self, items: list[Any]) -> ExprCall:
        op = str(items[0])
        args = list(items[1:])
        return ExprCall(op=op, args=[_as_expr_node(a) for a in args])

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

    def _collect_body(self, draft: BlockDraft, body_items: list[Any]) -> None:
        seen_sections: set[str] = set()
        allowed = ALLOWED_SECTIONS.get(draft.kind, frozenset())
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
                if section_name in seen_sections:
                    draft.errors.append(
                        duplicate_section(
                            section_name,
                            file=draft.file,
                            block_id=draft.block_id,
                        )
                    )
                seen_sections.add(section_name)
                if allowed and section_name not in allowed:
                    draft.errors.append(
                        unknown_section(
                            section_name,
                            draft.kind.value,
                            file=draft.file,
                            block_id=draft.block_id,
                        )
                    )
                draft.sections.setdefault(section_name, []).extend(
                    line for line in lines if line is not None
                )


def _filter_change_items(items: list[Any]) -> list[Any]:
    skip = {
        "ADD_FIELD", "REMOVE_FIELD", "RENAME_FIELD",
        "REPLACE_REF", "CREATE_TRANS", "REMOVE_TRANS",
    }
    return [x for x in items if not (isinstance(x, Token) and x.type in skip)]


def _as_expr_node(node: Any) -> Any:
    from yoni.parser.builders.base import _as_expr

    return _as_expr(node)


def _span(meta: Any, file: str) -> SourceSpan | None:
    if meta is None:
        return None
    line = getattr(meta, "line", None)
    if line is None:
        return None
    return SourceSpan(
        file=file,
        start_line=line,
        end_line=getattr(meta, "end_line", line) or line,
        start_column=getattr(meta, "column", 0) or 0,
        end_column=getattr(meta, "end_column", 0) or 0,
    )


def _with_span(obj: Any, meta: Any, file: str) -> Any:
    span = _span(meta, file)
    if span is None or not isinstance(obj, BaseModel):
        return obj
    if "span" not in type(obj).model_fields:
        return obj
    return obj.model_copy(update={"span": span})


def _wrap_spanned_rule(method_name: str):
    original = getattr(YoniTransformer, method_name)

    @v_args(meta=True)
    def wrapped(self, meta: Any, items: list[Any]) -> Any:
        return _with_span(original(self, items), meta, self.file)

    wrapped.__name__ = method_name
    return wrapped


_EXPR_RULES = (
    "eq_expr", "ne_expr", "ge_expr", "le_expr", "gt_expr", "lt_expr",
    "add_expr", "sub_expr", "mul_expr", "div_expr", "factor", "paren_factor",
    "call_expr", "number_atom", "bool_atom", "string_atom", "ref_atom",
    "var_atom", "enum_atom",
)

for _rule in _EXPR_RULES:
    spanned = _wrap_spanned_rule(_rule)
    setattr(YoniTransformer, _rule, spanned)
    setattr(YoniTransformer, f"expressions__{_rule}", spanned)
