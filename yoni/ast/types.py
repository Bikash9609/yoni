"""Shared AST value types for the Yoni compiler.

These types appear across multiple block schemas defined in
docs/03-final-yoni-specs.md §1 (Formal AST Schema).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TypeCode(str, Enum):
    """Single-char type codes used in human-format Yoni specs."""

    STRING = "s"
    INTEGER = "i"
    FLOAT = "f"
    BOOLEAN = "b"
    TIMESTAMP = "t"

    @property
    def full_name(self) -> str:
        return {
            TypeCode.STRING: "string",
            TypeCode.INTEGER: "integer",
            TypeCode.FLOAT: "float",
            TypeCode.BOOLEAN: "boolean",
            TypeCode.TIMESTAMP: "timestamp",
        }[self]


TYPE_CODE_MAP: dict[str, TypeCode] = {member.value: member for member in TypeCode}


class SourceSpan(BaseModel):
    """Source location attached to AST nodes for future diagnostics."""

    file: str = ""
    start_line: int = 0
    end_line: int = 0


class Reference(BaseModel):
    """Typed reference such as @Entity.Customer."""

    kind: str
    name: str
    raw: str = ""

    @classmethod
    def parse(cls, raw: str) -> Reference:
        text = raw.strip()
        if not text.startswith("@"):
            msg = f"Invalid reference (missing @): {raw!r}"
            raise ValueError(msg)
        body = text[1:]
        kind, _, name = body.partition(".")
        return cls(kind=kind, name=name, raw=text)


class FieldDef(BaseModel):
    """Field declaration inside entity fields or intent input sections."""

    name: str
    type_code: TypeCode | None = None
    ref: Reference | None = None
    nullable: bool = False
    unique: bool = False
    secret: bool = False

    @property
    def type_name(self) -> str:
        if self.type_code is not None:
            return self.type_code.full_name
        if self.ref is not None:
            return self.ref.kind
        return "unknown"


class IndexDef(BaseModel):
    """Entity index declaration."""

    field: str
    type: str = "unique"


class RawLine(BaseModel):
    """Unstructured line captured from a section body (process, when, etc.)."""

    text: str = Field(default="", description="Raw source line content")
