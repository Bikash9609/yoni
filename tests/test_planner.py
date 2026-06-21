"""Execution planner tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yoni.graph.builder import build_graph
from yoni.normalizer.run import normalize_workspace
from yoni.pipeline import compile_workspace
from yoni.planner.errors import PlanError
from yoni.planner.intent import plan_all_intents, plan_intent
from yoni.planner.models import JobType, StepType
from yoni.planner.run import plan_and_write, write_plan
from yoni.workspace.loader import load_workspace

ROOT = Path("samples/invoicing")


def _compiled():
    ws = load_workspace(ROOT)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    return norm, graph


def test_plan_register_user_steps_and_artifacts() -> None:
    norm, graph = _compiled()
    plan = plan_intent(norm, graph, "INT_REGISTER_USER_001")

    assert plan.intent == "INT_REGISTER_USER_001"
    assert plan.name == "RegisterUser"
    assert plan.domain == "customer"
    assert [step.type for step in plan.steps] == [
        StepType.INPUT,
        StepType.VALIDATE,
        StepType.VALIDATE,
        StepType.PROCESS,
        StepType.EMIT,
        StepType.FAIL,
        StepType.RETURN,
    ]

    validate_blocks = {
        step.block
        for step in plan.steps
        if step.type == StepType.VALIDATE
    }
    assert validate_blocks == {"RULE_ADULT_001", "CNST_EMAIL_UNIQUE_001"}

    process = next(step for step in plan.steps if step.type == StepType.PROCESS)
    assert [op.op for op in process.ops] == ["new", "set", "set", "set", "set", "save"]
    assert process.ops[0].entity == "ENT_CUSTOMER_001"

    fail = next(step for step in plan.steps if step.type == StepType.FAIL)
    assert fail.refs == ["ERR_EMAIL_EXISTS_001", "ERR_INVALID_EMAIL_001"]

    artifact_blocks = {item.block: item.job for item in plan.artifacts}
    assert artifact_blocks["ENT_CUSTOMER_001"] == JobType.ENTITY_SCHEMA
    assert artifact_blocks["RULE_ADULT_001"] == JobType.RULE_IMPL
    assert artifact_blocks["CNST_EMAIL_UNIQUE_001"] == JobType.CONSTRAINT_IMPL
    assert artifact_blocks["ERR_EMAIL_EXISTS_001"] == JobType.ERROR_DEF
    assert artifact_blocks["INT_REGISTER_USER_001"] == JobType.INTENT_HANDLER

    handler = plan.artifacts[-1]
    assert handler.block == "INT_REGISTER_USER_001"
    assert "ENT_CUSTOMER_001" in handler.depends
    assert "RULE_ADULT_001" in handler.depends


def test_plan_create_invoice_includes_state_ref() -> None:
    norm, graph = _compiled()
    plan = plan_intent(norm, graph, "INT_CREATE_INV_001")

    process = next(step for step in plan.steps if step.type == StepType.PROCESS)
    status_set = next(op for op in process.ops if op.target == "invoice.status")
    assert status_set.value == {"state": "STS_INVOICE_001", "name": "Draft"}

    artifact_blocks = {item.block for item in plan.artifacts}
    assert "STS_INVOICE_001" in artifact_blocks
    assert "RULE_ELIGIBLE_001" in artifact_blocks


def test_plan_all_intents() -> None:
    norm, graph = _compiled()
    plans = plan_all_intents(norm, graph)
    assert "INT_REGISTER_USER_001" in plans
    assert len(plans) >= 20


def test_plan_unknown_block_raises() -> None:
    norm, graph = _compiled()
    with pytest.raises(PlanError) as exc:
        plan_intent(norm, graph, "INT_MISSING_001")
    assert exc.value.code == "YONI4001"


def test_plan_non_intent_raises() -> None:
    norm, graph = _compiled()
    with pytest.raises(PlanError) as exc:
        plan_intent(norm, graph, "ENT_CUSTOMER_001")
    assert exc.value.code == "YONI4002"


def test_write_plan_and_cli(tmp_path: Path) -> None:
    norm, graph = _compiled()
    plan = plan_intent(norm, graph, "INT_REGISTER_USER_001")
    out = write_plan(tmp_path, plan)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["intent"] == "INT_REGISTER_USER_001"
    assert payload["steps"][0]["type"] == "input"


def test_plan_and_write_integration() -> None:
    plan, path = plan_and_write(ROOT, "INT_REGISTER_USER_001")
    assert plan.intent == "INT_REGISTER_USER_001"
    assert path.name == "INT_REGISTER_USER_001.json"
    assert path.exists()
