"""Load execution plans for generation."""

from __future__ import annotations

import json
from pathlib import Path

from yoni.planner.models import ExecutionPlan
from yoni.planner.run import plan_and_write, plans_dir


def load_plan(
    root: Path | str,
    intent_id: str,
    *,
    require_valid: bool = True,
) -> ExecutionPlan:
    project_root = Path(root)
    normalized_id = intent_id.upper()
    path = plans_dir(project_root) / f"{normalized_id}.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ExecutionPlan.model_validate(payload)
    plan, _ = plan_and_write(
        project_root,
        normalized_id,
        require_valid=require_valid,
    )
    return plan


def load_plans(
    root: Path | str,
    intent_ids: list[str],
    *,
    require_valid: bool = True,
) -> list[ExecutionPlan]:
    return [
        load_plan(root, intent_id, require_valid=require_valid)
        for intent_id in intent_ids
    ]
