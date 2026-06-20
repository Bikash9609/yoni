"""Base AST types and parse result envelope.

Every Yoni block conforms to a fixed schema (docs/03-final-yoni-specs.md §1).
ParseResult wraps the AST together with parse-time diagnostics.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from yoni.ast.entity import EntityAST
from yoni.ast.intent import IntentAST
from yoni.errors import ParseError

T = TypeVar("T")


class BlockKind(str, Enum):
    """All 17 top-level Yoni block kinds."""

    PROJECT = "project"
    DOMAIN = "domain"
    ENTITY = "entity"
    STATE = "state"
    EVENT = "event"
    INTENT = "intent"
    RULE = "rule"
    QUERY = "query"
    ACTION = "action"
    CONSTRAINT = "constraint"
    WORKFLOW = "workflow"
    ERROR = "error"
    TEST = "test"
    CAPABILITY = "capability"
    VIEW = "view"
    DEPLOYMENT = "deployment"
    MIGRATION = "migration"

    @classmethod
    def from_keyword(cls, keyword: str) -> BlockKind:
        normalized = keyword.lower()
        for member in cls:
            if member.value == normalized:
                return member
        msg = f"Unknown block keyword: {keyword!r}"
        raise ValueError(msg)


# Discriminated union — expand as more block transformers are implemented.
YoniBlock = EntityAST | IntentAST


class ParseResult(BaseModel, Generic[T]):
    """Output of parse_file / parse_source."""

    ast: T | None = None
    errors: list[ParseError] = Field(default_factory=list)
    source: str = ""
    file: str = ""

    @property
    def ok(self) -> bool:
        return self.ast is not None and not any(
            error.severity == "error" for error in self.errors
        )
