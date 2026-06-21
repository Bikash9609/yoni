"""Build execution plans from normalized intent blocks."""

from __future__ import annotations

from typing import Any

from yoni.ast.base import BlockKind
from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedBlock, NormalizedWorkspace
from yoni.planner.errors import PlanError
from yoni.planner.models import (
    ExecutionPlan,
    InputFieldPlan,
    JobType,
    PlanStep,
    PlannedArtifact,
    ProcessOpPlan,
    StepType,
)

_REF_KIND_TO_JOB: dict[str, JobType] = {
    "Entity": JobType.ENTITY_SCHEMA,
    "State": JobType.STATE_MACHINE,
    "Rule": JobType.RULE_IMPL,
    "Constraint": JobType.CONSTRAINT_IMPL,
    "Query": JobType.QUERY_IMPL,
    "Action": JobType.ACTION_IMPL,
    "Error": JobType.ERROR_DEF,
}

_BLOCK_KIND_TO_JOB: dict[BlockKind, JobType] = {
    BlockKind.ENTITY: JobType.ENTITY_SCHEMA,
    BlockKind.STATE: JobType.STATE_MACHINE,
    BlockKind.RULE: JobType.RULE_IMPL,
    BlockKind.CONSTRAINT: JobType.CONSTRAINT_IMPL,
    BlockKind.QUERY: JobType.QUERY_IMPL,
    BlockKind.ACTION: JobType.ACTION_IMPL,
    BlockKind.ERROR: JobType.ERROR_DEF,
    BlockKind.INTENT: JobType.INTENT_HANDLER,
}


def plan_intent(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    block_id: str,
) -> ExecutionPlan:
    """Build a deterministic execution plan for one intent block."""
    normalized_id = block_id.upper()
    block = workspace.blocks.get(normalized_id)
    if block is None:
        raise PlanError(
            "YONI4001",
            f"Block {normalized_id!r} not found",
            block_id=normalized_id,
            suggestion="Use a valid block id from normalized workspace.",
        )
    if block.kind != BlockKind.INTENT:
        raise PlanError(
            "YONI4002",
            f"Block {normalized_id!r} is {block.kind.value}, not intent",
            block_id=normalized_id,
            suggestion="Plan only intent blocks (id prefix INT_).",
        )

    body = block.body
    steps: list[PlanStep] = []
    order = 1
    artifact_blocks: dict[str, JobType] = {}
    domain = block.file.domain

    inputs = body.get("inputs", [])
    if inputs:
        fields = [_input_field(field, workspace, domain=domain) for field in inputs]
        steps.append(
            PlanStep(
                order=order,
                type=StepType.INPUT,
                fields=fields,
            )
        )
        order += 1
        for field in fields:
            if field.ref:
                _register_artifact(artifact_blocks, field.ref, workspace)

    for ref in body.get("validations", []):
        ref_id = _require_block_id(
            workspace, ref, normalized_id, role="validate", domain=domain
        )
        steps.append(
            PlanStep(
                order=order,
                type=StepType.VALIDATE,
                block=ref_id,
                block_kind=str(ref.get("kind", "")).lower(),
            )
        )
        order += 1
        _register_artifact(artifact_blocks, ref_id, workspace)

    process_ops = body.get("process", [])
    if process_ops:
        ops: list[ProcessOpPlan] = []
        for step in process_ops:
            op = step.get("op", "")
            if op in {"new", "set", "save"}:
                op_plan = _process_op(step)
                ops.append(op_plan)
                if op_plan.entity:
                    _register_artifact(artifact_blocks, op_plan.entity, workspace)
                state_id = _state_ref_id(op_plan.value)
                if state_id:
                    _register_artifact(artifact_blocks, state_id, workspace)
                continue
            ref_id = _optional_block_id(step)
            if ref_id:
                kind = str(step.get("kind", ""))
                if kind == "Query":
                    steps.append(
                        PlanStep(
                            order=order,
                            type=StepType.QUERY,
                            query=ref_id,
                            result=step.get("result"),
                        )
                    )
                    order += 1
                    _register_artifact(artifact_blocks, ref_id, workspace)
                elif kind == "Action":
                    steps.append(
                        PlanStep(
                            order=order,
                            type=StepType.ACTION,
                            action=ref_id,
                            result=step.get("result"),
                        )
                    )
                    order += 1
                    _register_artifact(artifact_blocks, ref_id, workspace)
        if ops:
            steps.append(
                PlanStep(
                    order=order,
                    type=StepType.PROCESS,
                    ops=ops,
                )
            )
            order += 1

    for ref in body.get("emit", []):
        ref_id = _require_block_id(
            workspace, ref, normalized_id, role="emit", domain=domain
        )
        steps.append(
            PlanStep(
                order=order,
                type=StepType.EMIT,
                event=ref_id,
                block_kind=str(ref.get("kind", "")).lower(),
            )
        )
        order += 1

    fail_refs = body.get("fail", [])
    if fail_refs:
        refs: list[str] = []
        for ref in fail_refs:
            ref_id = _require_block_id(
                workspace, ref, normalized_id, role="fail", domain=domain
            )
            refs.append(ref_id)
            _register_artifact(artifact_blocks, ref_id, workspace)
        steps.append(
            PlanStep(
                order=order,
                type=StepType.FAIL,
                refs=refs,
            )
        )
        order += 1

    ret = body.get("return")
    if ret:
        ref_id = _require_block_id(
            workspace, ret, normalized_id, role="return", domain=domain
        )
        steps.append(
            PlanStep(
                order=order,
                type=StepType.RETURN,
                block=ref_id,
                block_kind=str(ret.get("kind", "")).lower(),
            )
        )
        _register_artifact(artifact_blocks, ref_id, workspace)

    artifacts = _build_artifacts(normalized_id, artifact_blocks)
    return ExecutionPlan(
        intent=normalized_id,
        name=block.name,
        domain=block.file.domain,
        desc=block.desc,
        metadata=body.get("metadata"),
        steps=steps,
        artifacts=artifacts,
    )


def plan_all_intents(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> dict[str, ExecutionPlan]:
    plans: dict[str, ExecutionPlan] = {}
    for block_id, block in sorted(workspace.blocks.items()):
        if block.kind != BlockKind.INTENT:
            continue
        plans[block_id] = plan_intent(workspace, graph, block_id)
    return plans


def _input_field(
    field: dict[str, Any],
    workspace: NormalizedWorkspace,
    *,
    domain: str | None,
) -> InputFieldPlan:
    ref_data = field.get("ref")
    ref_id = None
    type_name = field.get("type")
    if isinstance(ref_data, dict):
        ref_id = _resolve_ref_block_id(workspace, ref_data, domain=domain)
        type_name = ref_data.get("kind") or type_name
    return InputFieldPlan(
        name=str(field.get("name", "")),
        type_name=type_name,
        type_code=field.get("type_code"),
        ref=ref_id,
    )


def _process_op(step: dict[str, Any]) -> ProcessOpPlan:
    entity_id = None
    type_ref = step.get("type_ref")
    if isinstance(type_ref, dict):
        entity_id = type_ref.get("block_id")

    value = step.get("value")
    normalized_value = value
    if isinstance(value, dict) and value.get("kind") == "ref":
        ref = value.get("ref", {})
        if isinstance(ref, dict):
            ref_id = ref.get("block_id")
            if ref_id:
                normalized_value = ref_id
    elif isinstance(value, dict) and value.get("kind") == "state_ref":
        state_id = value.get("state_id")
        if state_id:
            normalized_value = {
                "state": state_id,
                "name": value.get("state_name"),
            }

    return ProcessOpPlan(
        op=str(step.get("op", "")),
        target=step.get("target"),
        entity=entity_id,
        value=normalized_value,
    )


def _state_ref_id(value: Any) -> str | None:
    if isinstance(value, dict) and "state" in value:
        state_id = value.get("state")
        if state_id:
            return str(state_id)
    return None


def _optional_block_id(value: dict[str, Any]) -> str | None:
    block_id = value.get("block_id")
    if block_id:
        return str(block_id)
    ref = value.get("ref")
    if isinstance(ref, dict):
        ref_id = ref.get("block_id")
        if ref_id:
            return str(ref_id)
    return None


def _resolve_ref_block_id(
    workspace: NormalizedWorkspace,
    ref: dict[str, Any],
    *,
    domain: str | None,
) -> str | None:
    block_id = ref.get("block_id")
    if block_id:
        return str(block_id)
    kind = ref.get("kind", "")
    name = ref.get("name", "")
    if not kind or not name:
        return None
    base = f"{kind}.{name}"
    if domain:
        scoped = workspace.symbols.get(f"{domain}:{base}")
        if scoped:
            return scoped
    target = workspace.symbols.get(base)
    if target:
        return target
    suffix = f":{base}"
    matches = [
        block
        for key, block in workspace.symbols.items()
        if key.endswith(suffix)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _require_block_id(
    workspace: NormalizedWorkspace,
    ref: dict[str, Any],
    intent_id: str,
    *,
    role: str,
    domain: str | None,
) -> str:
    block_id = _resolve_ref_block_id(workspace, ref, domain=domain)
    if block_id:
        return block_id
    raw = ref.get("raw", ref.get("name", "unknown"))
    raise PlanError(
        "YONI4003",
        f"Unresolved {role} reference {raw!r} in intent {intent_id}",
        block_id=intent_id,
        suggestion="Ensure reference resolves in normalized workspace.",
    )


def _register_artifact(
    artifact_blocks: dict[str, JobType],
    block_id: str,
    workspace: NormalizedWorkspace,
) -> None:
    if block_id in artifact_blocks:
        return
    block = workspace.blocks.get(block_id)
    if block is None:
        return
    job = _BLOCK_KIND_TO_JOB.get(block.kind)
    if job is not None and job != JobType.INTENT_HANDLER:
        artifact_blocks[block_id] = job
        return
    kind = block.kind.value
    job = _REF_KIND_TO_JOB.get(kind.title())
    if job is not None:
        artifact_blocks[block_id] = job


def _build_artifacts(
    intent_id: str,
    artifact_blocks: dict[str, JobType],
) -> list[PlannedArtifact]:
    dependency_ids = sorted(
        block_id for block_id in artifact_blocks if block_id != intent_id
    )
    artifacts: list[PlannedArtifact] = []
    for block_id in dependency_ids:
        job = artifact_blocks[block_id]
        artifacts.append(PlannedArtifact(job=job, block=block_id, depends=[]))
    artifacts.append(
        PlannedArtifact(
            job=JobType.INTENT_HANDLER,
            block=intent_id,
            depends=dependency_ids,
        )
    )
    return artifacts
