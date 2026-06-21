"""Plan persistence and orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.pipeline import compile_workspace
from yoni.planner.errors import PlanError
from yoni.planner.intent import plan_all_intents, plan_intent
from yoni.planner.models import ExecutionPlan


def plans_dir(root: Path) -> Path:
    return root / ".ai" / "generation" / "plans"


def write_plan(root: Path | str, plan: ExecutionPlan) -> Path:
    out_dir = plans_dir(Path(root))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{plan.intent}.json"
    out_path.write_text(
        json.dumps(plan.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_all_plans(root: Path | str, plans: dict[str, ExecutionPlan]) -> list[Path]:
    paths: list[Path] = []
    for plan in plans.values():
        paths.append(write_plan(root, plan))
    return paths


def plan_and_write(
    root: Path | str,
    block_id: str,
    *,
    require_valid: bool = True,
) -> tuple[ExecutionPlan, Path]:
    project_root = Path(root).resolve()
    result = compile_workspace(project_root, write_cache=True)
    if result.normalized is None or result.graph is None:
        raise PlanError(
            "YONI4004",
            "Compile failed — workspace could not be normalized",
            block_id=block_id.upper(),
            suggestion="Fix parse errors before planning.",
        )
    if require_valid and not result.ok:
        err_count = len([e for e in result.validation_errors if e.severity == "error"])
        raise PlanError(
            "YONI4005",
            f"Validation failed with {err_count} error(s)",
            block_id=block_id.upper(),
            suggestion="Fix validation errors before planning.",
        )
    plan = plan_intent(result.normalized, result.graph, block_id)
    path = write_plan(project_root, plan)
    return plan, path


def plan_workspace(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    block_id: str | None = None,
) -> ExecutionPlan | dict[str, ExecutionPlan]:
    if block_id is not None:
        return plan_intent(workspace, graph, block_id)
    return plan_all_intents(workspace, graph)
