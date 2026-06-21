"""Base AST types and parse result envelope."""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from yoni.ast.action import ActionAST
from yoni.ast.capability import CapabilityAST
from yoni.ast.constraint import ConstraintAST
from yoni.ast.deployment import DeploymentAST
from yoni.ast.domain import DomainAST
from yoni.ast.entity import EntityAST
from yoni.ast.error import ErrorAST
from yoni.ast.event import EventAST
from yoni.ast.intent import IntentAST
from yoni.ast.migration import MigrationAST
from yoni.ast.project import ProjectAST
from yoni.ast.query import QueryAST
from yoni.ast.rule import RuleAST
from yoni.ast.state import StateAST
from yoni.ast.test import TestAST
from yoni.ast.view import ViewAST
from yoni.ast.workflow import WorkflowAST
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


YoniBlock = (
    ProjectAST
    | DomainAST
    | EntityAST
    | StateAST
    | EventAST
    | IntentAST
    | RuleAST
    | QueryAST
    | ActionAST
    | ConstraintAST
    | WorkflowAST
    | ErrorAST
    | TestAST
    | CapabilityAST
    | ViewAST
    | DeploymentAST
    | MigrationAST
)


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
