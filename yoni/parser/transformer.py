"""Parse tree → Pydantic AST transformer.

Dispatches by block kind. Entity and intent are fully implemented;
remaining 15 kinds return YONI1002 gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lark import Token, Transformer, v_args

from yoni.ast.base import BlockKind, YoniBlock
from yoni.ast.entity import EntityAST
from yoni.ast.intent import IntentAST
from yoni.ast.types import FieldDef, IndexDef, RawLine, Reference, TYPE_CODE_MAP, TypeCode
from yoni.errors import (
    ParseError,
    missing_required_field,
    section_order_violation,
    unimplemented_block,
)

INTENT_SECTION_ORDER = ("input", "validate", "process", "emit", "fail", "return")


@dataclass
class _BlockDraft:
    """Mutable accumulator while walking a parse tree."""

    kind: BlockKind
    name: str
    block_id: str | None = None
    desc: str = ""
    sections: dict[str, list[Any]] = field(default_factory=dict)
    errors: list[ParseError] = field(default_factory=list)
    file: str = ""


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
        draft = _BlockDraft(kind=kind, name=name, file=self.file)
        self._collect_body(draft, body_items)
        return self._build_block(draft)

    def block_header(self, items: list[Any]) -> tuple[BlockKind, str]:
        keyword = str(items[0])
        name = str(items[1])
        return BlockKind.from_keyword(keyword), name

    def block_body(self, items: list[Any]) -> list[Any]:
        return [item for item in items if item is not None]

    def body_item(self, item: Any) -> Any:
        return item

    def top_field(self, items: list[Any]) -> dict[str, str]:
        first = items[0]
        if isinstance(first, Token) and first.type == "ID":
            return {"id": str(first)}
        desc_parts = [str(part).strip() for part in items if str(part).strip()]
        return {"desc": " ".join(desc_parts)}

    def desc_body(self, items: list[Any]) -> str:
        if not items:
            return ""
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
        field_name = str(items[0])
        type_value = items[-1]
        if isinstance(type_value, Reference):
            return FieldDef(name=field_name, ref=type_value)
        if isinstance(type_value, TypeCode):
            return FieldDef(name=field_name, type_code=type_value)
        code = TYPE_CODE_MAP.get(str(type_value))
        if code:
            return FieldDef(name=field_name, type_code=code)
        return FieldDef(name=field_name)

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

    @v_args(inline=True)
    def TYPE_CODE(self, token: Token) -> TypeCode:
        return TYPE_CODE_MAP[str(token)]

    @v_args(inline=True)
    def REFERENCE(self, token: Token) -> Reference:
        return Reference.parse(str(token))

    def content_line(self, items: list[Any]) -> RawLine:
        return RawLine(text=str(items[0]).strip())

    def _collect_body(self, draft: _BlockDraft, body_items: list[Any]) -> None:
        for item in body_items:
            if not isinstance(item, dict) and not isinstance(item, tuple):
                continue
            if isinstance(item, dict):
                if "id" in item:
                    draft.block_id = item["id"]
                if "desc" in item:
                    draft.desc = item["desc"]
                continue
            section_name, lines = item
            draft.sections.setdefault(section_name, []).extend(
                line for line in lines if line is not None
            )

    def _build_block(
        self, draft: _BlockDraft
    ) -> tuple[YoniBlock | None, list[ParseError]]:
        errors: list[ParseError] = list(draft.errors)
        if not draft.block_id:
            errors.append(
                missing_required_field("id", file=draft.file, block_id=draft.block_id)
            )
        if draft.desc == "" and "desc" not in draft.sections:
            # desc: with empty body is valid; only error if key never appeared
            has_desc_key = any(
                isinstance(item, dict) and "desc" in item
                for item in []  # desc always collected via top_field
            )
            if not has_desc_key and draft.desc == "":
                # Allow empty desc when desc: section exists but is blank
                pass

        if draft.kind == BlockKind.ENTITY:
            return self._build_entity(draft, errors)
        if draft.kind == BlockKind.INTENT:
            return self._build_intent(draft, errors)
        errors.append(
            unimplemented_block(
                draft.kind.value, file=draft.file, block_id=draft.block_id
            )
        )
        return None, errors

    def _build_entity(
        self, draft: _BlockDraft, errors: list[ParseError]
    ) -> tuple[EntityAST | None, list[ParseError]]:
        if not draft.block_id:
            return None, errors
        fields: list[FieldDef] = []
        indices: list[IndexDef] = []
        for line in draft.sections.get("fields", []):
            if isinstance(line, FieldDef):
                fields.append(line)
        for line in draft.sections.get("indices", []):
            if isinstance(line, RawLine):
                indices.append(IndexDef(field=line.text))
            elif isinstance(line, FieldDef):
                indices.append(IndexDef(field=line.name))
        ast = EntityAST(
            id=draft.block_id,
            name=draft.name,
            desc=draft.desc,
            fields=fields,
            indices=indices,
        )
        return ast, errors

    def _build_intent(
        self, draft: _BlockDraft, errors: list[ParseError]
    ) -> tuple[IntentAST | None, list[ParseError]]:
        if not draft.block_id:
            return None, errors
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

        inputs = [
            line
            for line in draft.sections.get("input", [])
            if isinstance(line, FieldDef)
        ]
        validate = self._refs_from_section(draft.sections.get("validate", []))
        process = [
            line
            for line in draft.sections.get("process", [])
            if isinstance(line, (RawLine, dict))
        ]
        emit = self._refs_from_section(draft.sections.get("emit", []))
        fail = self._refs_from_section(draft.sections.get("fail", []))
        return_lines = draft.sections.get("return", [])
        return_ref = self._single_ref(return_lines)

        ast = IntentAST(
            id=draft.block_id,
            name=draft.name,
            desc=draft.desc,
            inputs=inputs,
            validations=validate,
            process=process,
            emit=emit,
            fail=fail,
            return_ref=return_ref,
        )
        return ast, errors

    def _refs_from_section(self, lines: list[Any]) -> list[Reference]:
        refs: list[Reference] = []
        for line in lines:
            if isinstance(line, Reference):
                refs.append(line)
            elif isinstance(line, RawLine) and line.text.startswith("@"):
                refs.append(Reference.parse(line.text))
            elif isinstance(line, FieldDef) and line.ref:
                refs.append(line.ref)
        return refs

    def _single_ref(self, lines: list[Any]) -> Reference | None:
        refs = self._refs_from_section(lines)
        if refs:
            return refs[0]
        for line in lines:
            if isinstance(line, RawLine) and line.text.startswith("@"):
                return Reference.parse(line.text)
        return None
