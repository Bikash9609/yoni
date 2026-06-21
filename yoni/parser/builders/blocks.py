"""Block-specific AST builders for all 17 Yoni block kinds."""

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
from yoni.ast.expr import WhenDef
from yoni.ast.intent import IntentAST
from yoni.ast.migration import MigrationAST
from yoni.ast.project import ProjectAST
from yoni.ast.query import QueryAST
from yoni.ast.rule import RuleAST
from yoni.ast.state import StateAST
from yoni.ast.test import TestAST
from yoni.ast.types import FieldDef
from yoni.ast.view import ViewAST
from yoni.ast.workflow import WorkflowAST
from yoni.errors import ParseError, unknown_block_kind
from yoni.parser.builders.base import (
    changes_from_section,
    check_intent_section_order,
    env_from_section,
    expects_from_section,
    expr_from_section,
    fields_from_section,
    indices_from_section,
    layout_from_section,
    order_by_from_section,
    process_ops_from_section,
    refs_from_section,
    require_id,
    return_spec_from_scalar,
    scalar_bool,
    scalar_int,
    scalar_ref,
    scalar_str,
    single_ref,
    steps_from_section,
    string_list_from_section,
    transitions_from_section,
)
from yoni.parser.draft import BlockDraft


def build_block(draft: BlockDraft) -> tuple[YoniBlock | None, list[ParseError]]:
    errors: list[ParseError] = list(draft.errors)
    if not require_id(draft, errors):
        return None, errors

    builders = {
        BlockKind.PROJECT: _build_project,
        BlockKind.DOMAIN: _build_domain,
        BlockKind.ENTITY: _build_entity,
        BlockKind.STATE: _build_state,
        BlockKind.EVENT: _build_event,
        BlockKind.INTENT: _build_intent,
        BlockKind.RULE: _build_rule,
        BlockKind.QUERY: _build_query,
        BlockKind.ACTION: _build_action,
        BlockKind.CONSTRAINT: _build_constraint,
        BlockKind.WORKFLOW: _build_workflow,
        BlockKind.ERROR: _build_error,
        BlockKind.TEST: _build_test,
        BlockKind.CAPABILITY: _build_capability,
        BlockKind.VIEW: _build_view,
        BlockKind.DEPLOYMENT: _build_deployment,
        BlockKind.MIGRATION: _build_migration,
    }
    builder = builders.get(draft.kind)
    if builder is None:
        errors.append(
            unknown_block_kind(
                draft.kind.value, file=draft.file, block_id=draft.block_id
            )
        )
        return None, errors
    return builder(draft, errors)


def _base_kwargs(draft: BlockDraft) -> dict[str, Any]:
    return {
        "id": draft.block_id or "",
        "name": draft.name,
        "desc": draft.desc,
        "span": draft.span,
    }


def _build_project(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[ProjectAST | None, list[ParseError]]:
    return ProjectAST(
        **_base_kwargs(draft),
        domains=refs_from_section(draft.sections.get("domains", [])),
        capabilities=refs_from_section(draft.sections.get("capabilities", [])),
        env=env_from_section(draft.sections.get("env", [])),
    ), errors


def _build_domain(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[DomainAST | None, list[ParseError]]:
    return DomainAST(
        **_base_kwargs(draft),
        entities=refs_from_section(draft.sections.get("entities", [])),
        rules=refs_from_section(draft.sections.get("rules", [])),
        events=refs_from_section(draft.sections.get("events", [])),
    ), errors


def _build_entity(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[EntityAST | None, list[ParseError]]:
    return EntityAST(
        **_base_kwargs(draft),
        fields=fields_from_section(draft.sections.get("fields", [])),
        indices=indices_from_section(draft.sections.get("indices", [])),
    ), errors


def _build_state(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[StateAST | None, list[ParseError]]:
    return StateAST(
        **_base_kwargs(draft),
        states=string_list_from_section(draft.sections.get("states", [])),
        transitions=transitions_from_section(draft.sections.get("transitions", [])),
    ), errors


def _build_event(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[EventAST | None, list[ParseError]]:
    return EventAST(
        **_base_kwargs(draft),
        payload=fields_from_section(draft.sections.get("payload", [])),
    ), errors


def _build_intent(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[IntentAST | None, list[ParseError]]:
    check_intent_section_order(draft, errors)
    return_ref = scalar_ref(draft, "return") or single_ref(
        draft.sections.get("return", [])
    )
    return IntentAST(
        **_base_kwargs(draft),
        inputs=fields_from_section(draft.sections.get("input", [])),
        validations=refs_from_section(draft.sections.get("validate", [])),
        process=process_ops_from_section(draft.sections.get("process", [])),
        emit=refs_from_section(draft.sections.get("emit", [])),
        fail=refs_from_section(draft.sections.get("fail", [])),
        return_ref=return_ref,
    ), errors


def _build_rule(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[RuleAST | None, list[ParseError]]:
    expression = expr_from_section(draft.sections.get("expression", []))
    if expression is None:
        expression = expr_from_section(draft.sections.get("when", []))
    return RuleAST(**_base_kwargs(draft), expression=expression), errors


def _build_query(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[QueryAST | None, list[ParseError]]:
    entity = scalar_ref(draft, "entity") or single_ref(draft.sections.get("entity", []))
    return_spec = return_spec_from_scalar(draft.scalars.get("return"))
    if return_spec is None:
        ref = single_ref(draft.sections.get("return", []))
        if ref:
            return_spec = return_spec_from_scalar(ref)
    return QueryAST(
        **_base_kwargs(draft),
        entity=entity,
        where=expr_from_section(draft.sections.get("where", [])),
        order_by=order_by_from_section(draft.sections.get("order_by", [])),
        limit=scalar_int(draft, "limit"),
        return_spec=return_spec,
    ), errors


def _build_action(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[ActionAST | None, list[ParseError]]:
    uses = scalar_ref(draft, "uses") or single_ref(draft.sections.get("uses", []))
    return ActionAST(
        **_base_kwargs(draft),
        uses=uses,
        inputs=fields_from_section(draft.sections.get("input", [])),
        result=fields_from_section(draft.sections.get("result", [])),
    ), errors


def _build_constraint(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[ConstraintAST | None, list[ParseError]]:
    entity = scalar_ref(draft, "entity") or single_ref(draft.sections.get("entity", []))
    check = expr_from_section(draft.sections.get("check", []))
    return ConstraintAST(**_base_kwargs(draft), entity=entity, check=check), errors


def _build_workflow(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[WorkflowAST | None, list[ParseError]]:
    return WorkflowAST(
        **_base_kwargs(draft),
        steps=steps_from_section(draft.sections.get("steps", [])),
    ), errors


def _build_error(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[ErrorAST | None, list[ParseError]]:
    message = scalar_str(draft, "message")
    if not message:
        message_lines = draft.sections.get("message", [])
        message = " ".join(
            str(line) for line in message_lines if isinstance(line, str)
        ).strip()
    return ErrorAST(
        **_base_kwargs(draft),
        code=scalar_str(draft, "code"),
        http_status=scalar_int(draft, "http_status"),
        message=message,
    ), errors


def _build_test(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[TestAST | None, list[ParseError]]:
    when_lines = draft.sections.get("when", [])
    when: WhenDef | None = None
    if when_lines:
        when = WhenDef()
        for line in when_lines:
            if isinstance(line, WhenDef) and line.intent:
                when.intent = line.intent
            elif isinstance(line, tuple) and len(line) == 2:
                key, value = line
                when.inputs[str(key)] = value
    return TestAST(
        **_base_kwargs(draft),
        given=process_ops_from_section(draft.sections.get("given", [])),
        when=when,
        expect=expects_from_section(draft.sections.get("expect", [])),
    ), errors


def _build_capability(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[CapabilityAST | None, list[ParseError]]:
    return CapabilityAST(
        **_base_kwargs(draft),
        actions=refs_from_section(draft.sections.get("actions", [])),
        config=fields_from_section(draft.sections.get("config", [])),
    ), errors


def _build_view(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[ViewAST | None, list[ParseError]]:
    query = scalar_ref(draft, "query") or single_ref(draft.sections.get("query", []))
    field_lines = draft.sections.get("fields", [])
    fields: list[str] = []
    for line in field_lines:
        if isinstance(line, str):
            fields.append(line)
        elif isinstance(line, FieldDef):
            fields.append(line.name)
        elif isinstance(line, tuple) and len(line) == 2:
            fields.append(str(line[0]))
    return ViewAST(
        **_base_kwargs(draft),
        query=query,
        fields=fields or string_list_from_section(field_lines),
        actions=refs_from_section(draft.sections.get("actions", [])),
        layout=layout_from_section(draft.sections.get("layout", [])),
    ), errors


def _build_deployment(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[DeploymentAST | None, list[ParseError]]:
    resources: dict[str, str | int | float] = {}
    for line in draft.sections.get("resources", []):
        if isinstance(line, tuple) and len(line) == 2:
            key, value = line
            resources[str(key)] = value
    return DeploymentAST(
        **_base_kwargs(draft),
        region=scalar_str(draft, "region"),
        replicas=scalar_int(draft, "replicas"),
        resources=resources,
        services=refs_from_section(draft.sections.get("services", [])),
        env=env_from_section(draft.sections.get("env", [])),
    ), errors


def _build_migration(
    draft: BlockDraft, errors: list[ParseError]
) -> tuple[MigrationAST | None, list[ParseError]]:
    return MigrationAST(
        **_base_kwargs(draft),
        from_version=scalar_int(draft, "from_version"),
        to_version=scalar_int(draft, "to_version"),
        changes=changes_from_section(draft.sections.get("changes", [])),
        affects=refs_from_section(draft.sections.get("affects", [])),
        breaking=scalar_bool(draft, "breaking"),
    ), errors
