"""Knowledge graph models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from yoni.ast.base import BlockKind


class EdgeKind(str, Enum):
    USES = "USES"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    EMITS = "EMITS"
    VALIDATES = "VALIDATES"
    DEPENDS_ON = "DEPENDS_ON"
    REFERENCES = "REFERENCES"
    OWNS = "OWNS"
    TRIGGERS = "TRIGGERS"
    CONSUMES = "CONSUMES"
    FAILS = "FAILS"


class Node(BaseModel):
    id: str
    kind: BlockKind
    name: str
    version: int = 1
    file: str
    domain: str | None = None
    ast_ref: str = ""


class Edge(BaseModel):
    kind: EdgeKind
    source: str
    target: str
    ref_raw: str | None = None
    resolved: bool = True


class KnowledgeGraph(BaseModel):
    nodes: dict[str, Node] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)
