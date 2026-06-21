"""Per-block AST normalization."""

from __future__ import annotations

from typing import Any

from yoni.ast.action import ActionAST
from yoni.ast.base import BlockKind, YoniBlock
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
from yoni.ast.types import FieldDef, RefLink
from yoni.ast.view import ViewAST
from yoni.ast.workflow import WorkflowAST
from yoni.normalizer.expr import normalize_expr, normalize_process_op, ref_from_reference


def _field(f: FieldDef) -> dict[str, Any]:
    return {
        "name": f.name,
        "type": f.type_name,
        "type_code": f.type_code.value if f.type_code else None,
        "ref": ref_from_reference(f.ref).model_dump() if f.ref else None,
        "nullable": f.nullable,
        "unique": f.unique,
        "secret": f.secret,
    }


def _ref_link(link: RefLink | None) -> dict[str, Any] | None:
    if link is None:
        return None
    return ref_from_reference(link.ref).model_dump()


def _ref_links(links: list[RefLink]) -> list[dict[str, Any]]:
    return [ref_from_reference(link.ref).model_dump() for link in links]


def normalize_body(ast: YoniBlock) -> dict[str, Any]:
    if isinstance(ast, EntityAST):
        return {
            "fields": [_field(f) for f in ast.fields],
            "indices": [{"field": i.field, "type": i.type} for i in ast.indices],
        }
    if isinstance(ast, IntentAST):
        return {
            "inputs": [_field(f) for f in ast.inputs],
            "validations": _ref_links(ast.validations),
            "process": [normalize_process_op(op) for op in ast.process],
            "emit": _ref_links(ast.emit),
            "fail": _ref_links(ast.fail),
            "return": (
                ref_from_reference(ast.return_spec.ref).model_dump()
                if ast.return_spec and ast.return_spec.ref
                else None
            ),
            "metadata": ast.metadata.model_dump() if ast.metadata else None,
        }
    if isinstance(ast, RuleAST):
        return {"expression": normalize_expr(ast.expression)}
    if isinstance(ast, QueryAST):
        return {
            "entity": _ref_link(ast.entity),
            "where": normalize_expr(ast.where),
            "order_by": [o.model_dump() for o in ast.order_by],
            "limit": ast.limit,
            "return": ast.return_spec.model_dump() if ast.return_spec else None,
        }
    if isinstance(ast, ActionAST):
        return {
            "uses": _ref_link(ast.uses),
            "inputs": [_field(f) for f in ast.inputs],
            "result": [_field(f) for f in ast.result],
        }
    if isinstance(ast, StateAST):
        return {
            "states": list(ast.states),
            "transitions": [t.model_dump() for t in ast.transitions],
        }
    if isinstance(ast, EventAST):
        return {"payload": [_field(f) for f in ast.payload]}
    if isinstance(ast, WorkflowAST):
        return {"steps": [s.model_dump() for s in ast.steps]}
    if isinstance(ast, ConstraintAST):
        return {
            "entity": _ref_link(ast.entity),
            "check": normalize_expr(ast.check),
        }
    if isinstance(ast, ErrorAST):
        return {
            "code": ast.code,
            "http_status": ast.http_status,
            "message": ast.message,
        }
    if isinstance(ast, TestAST):
        return {
            "given": [normalize_process_op(op) for op in ast.given],
            "when": ast.when.model_dump() if ast.when else None,
            "expect": [e.model_dump() for e in ast.expect],
        }
    if isinstance(ast, CapabilityAST):
        return {
            "actions": _ref_links(ast.actions),
            "config": [_field(f) for f in ast.config],
        }
    if isinstance(ast, ViewAST):
        return {
            "query": _ref_link(ast.query),
            "fields": list(ast.fields),
            "actions": _ref_links(ast.actions),
            "layout": ast.layout.model_dump() if ast.layout else None,
        }
    if isinstance(ast, ProjectAST):
        return {
            "domains": _ref_links(ast.domains),
            "capabilities": _ref_links(ast.capabilities),
            "env": ast.env.model_dump() if ast.env else None,
        }
    if isinstance(ast, DomainAST):
        return {
            "entities": _ref_links(ast.entities),
            "rules": _ref_links(ast.rules),
            "events": _ref_links(ast.events),
        }
    if isinstance(ast, DeploymentAST):
        return {
            "region": ast.region,
            "replicas": ast.replicas,
            "resources": dict(ast.resources),
            "services": _ref_links(ast.services),
            "env": ast.env.model_dump() if ast.env else None,
        }
    if isinstance(ast, MigrationAST):
        return {
            "from_version": ast.from_version,
            "to_version": ast.to_version,
            "breaking": ast.breaking,
            "changes": [c.model_dump() for c in ast.changes],
            "affects": _ref_links(ast.affects),
        }
    kind = getattr(ast, "type", "unknown")
    return {"type": kind}


_KIND_FROM_AST: dict[str, BlockKind] = {
    "Project": BlockKind.PROJECT,
    "Domain": BlockKind.DOMAIN,
    "Entity": BlockKind.ENTITY,
    "State": BlockKind.STATE,
    "Event": BlockKind.EVENT,
    "Intent": BlockKind.INTENT,
    "Rule": BlockKind.RULE,
    "Query": BlockKind.QUERY,
    "Action": BlockKind.ACTION,
    "Constraint": BlockKind.CONSTRAINT,
    "Workflow": BlockKind.WORKFLOW,
    "Error": BlockKind.ERROR,
    "Test": BlockKind.TEST,
    "Capability": BlockKind.CAPABILITY,
    "View": BlockKind.VIEW,
    "Deployment": BlockKind.DEPLOYMENT,
    "Migration": BlockKind.MIGRATION,
}


def block_kind(ast: YoniBlock) -> BlockKind:
    ast_type = getattr(ast, "type", "")
    return _KIND_FROM_AST.get(ast_type, BlockKind.ENTITY)
