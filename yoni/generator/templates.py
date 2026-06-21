"""Deterministic code templates — no LLM."""

from __future__ import annotations

import re
from typing import Any

from yoni.ast.base import BlockKind
from yoni.generator.models import GenerationManifest
from yoni.normalizer.models import NormalizedBlock, NormalizedRef, NormalizedWorkspace
from yoni.planner.models import ExecutionPlan, JobType, StepType

_TYPE_CODE_PYTHON: dict[str, str] = {
    "s": "str",
    "i": "int",
    "f": "float",
    "b": "bool",
    "t": "datetime",
}

_PYTHON_DEFAULTS: dict[str, str] = {
    "str": '""',
    "int": "0",
    "float": "0.0",
    "bool": "False",
    "datetime": "None",
}


def block_marker(block_id: str) -> str:
    return f"# yoni:{block_id}"


def _pascal(name: str) -> str:
    parts = re.split(r"[-_\s]+", name)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _snake(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return re.sub(r"[^a-z0-9_]+", "_", spaced.lower()).strip("_")


def _field_python_type(field: dict[str, Any]) -> str:
    type_code = field.get("type_code")
    if type_code and type_code in _TYPE_CODE_PYTHON:
        py_type = _TYPE_CODE_PYTHON[type_code]
    else:
        type_name = field.get("type") or field.get("type_name") or "str"
        mapping = {
            "string": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "timestamp": "datetime",
        }
        py_type = mapping.get(str(type_name).lower(), "str")
    if field.get("nullable"):
        return f"{py_type} | None"
    return py_type


def _header(block: NormalizedBlock, *, extra_markers: list[str] | None = None) -> list[str]:
    lines = [block_marker(block.block_id)]
    for marker in extra_markers or []:
        lines.append(block_marker(marker))
    if block.desc:
        lines.append(f'"""{block.desc.strip()}"""')
    return lines


def expr_to_python(expr: dict[str, Any] | None) -> str:
    if expr is None:
        return "None"
    kind = expr.get("kind")
    if kind == "var":
        return str(expr.get("name", "var"))
    if kind == "value":
        value = expr.get("value")
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, bool):
            return "True" if value else "False"
        return str(value)
    if kind == "binary":
        left = expr_to_python(expr.get("left"))
        right = expr_to_python(expr.get("right"))
        return f"({left} {expr.get('op', '==')} {right})"
    if kind == "call":
        args = ", ".join(expr_to_python(arg) for arg in expr.get("args", []))
        return f"{expr.get('op', 'call')}({args})"
    if kind == "ref":
        ref = expr.get("ref") or {}
        return _snake(str(ref.get("name", "ref")))
    return "None"


def collect_expr_vars(expr: dict[str, Any] | None, out: set[str] | None = None) -> set[str]:
    found: set[str] = set() if out is None else out
    if expr is None:
        return found
    kind = expr.get("kind")
    if kind == "var":
        found.add(str(expr.get("name", "")))
    elif kind in {"binary", "call"}:
        if kind == "binary":
            collect_expr_vars(expr.get("left"), found)
            collect_expr_vars(expr.get("right"), found)
        else:
            for arg in expr.get("args", []):
                collect_expr_vars(arg, found)
    return {name for name in found if name}


def render_entity(block: NormalizedBlock) -> str:
    class_name = _pascal(block.name)
    lines = [
        '"""Generated entity schema."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import datetime",
        "",
        "from pydantic import BaseModel",
        "",
        *_header(block),
        "",
        f"class {class_name}(BaseModel):",
    ]
    fields = block.body.get("fields", [])
    if not fields:
        lines.append("    pass")
    else:
        for field in fields:
            name = field["name"]
            py_type = _field_python_type(field)
            default = _PYTHON_DEFAULTS.get(py_type.split(" | ")[0], "None")
            field_line = f"    {name}: {py_type}"
            extras: list[str] = []
            if field.get("unique"):
                extras.append("unique")
            if field.get("secret"):
                extras.append("secret")
            if extras:
                field_line += f"  # {', '.join(extras)}"
            if " | None" in py_type:
                field_line += " = None"
            elif default != "None":
                field_line += f" = {default}"
            lines.append(field_line)
    indices = block.body.get("indices", [])
    if indices:
        lines.append("")
        lines.append("    model_config = {")
        lines.append('        "json_schema_extra": {')
        lines.append(f'            "yoni_indices": {indices!r},')
        lines.append("        }")
        lines.append("    }")
    return "\n".join(lines) + "\n"


def render_error(block: NormalizedBlock) -> str:
    class_name = f"{_pascal(block.name)}Error"
    body = block.body
    lines = [
        '"""Generated error definition."""',
        "",
        "from __future__ import annotations",
        "",
        *_header(block),
        "",
        f"class {class_name}(Exception):",
        f'    code: str = {body.get("code", "")!r}',
        f'    http_status: int = {body.get("http_status", 500)!r}',
        f'    message: str = {body.get("message", block.desc or block.name)!r}',
        "",
        "    def __init__(self, message: str | None = None) -> None:",
        "        super().__init__(message or self.message)",
    ]
    return "\n".join(lines) + "\n"


def render_rule(block: NormalizedBlock) -> str:
    fn_name = _snake(block.name)
    expression = block.body.get("expression")
    params = sorted(collect_expr_vars(expression))
    param_sig = ", ".join(f"{name}: int" for name in params) or ""
    lines = [
        '"""Generated rule implementation."""',
        "",
        "from __future__ import annotations",
        "",
        *_header(block),
        "",
        f"def {fn_name}({param_sig}) -> bool:",
        f"    return {expr_to_python(expression)}",
    ]
    return "\n".join(lines) + "\n"


def render_constraint(block: NormalizedBlock, workspace: NormalizedWorkspace) -> str:
    fn_name = _snake(block.name)
    entity_ref = block.body.get("entity") or {}
    entity_id = _resolve_ref_id(workspace, entity_ref, domain=block.file.domain)
    markers = [entity_id] if entity_id else []
    check = block.body.get("check")
    params = sorted(collect_expr_vars(check))
    param_sig = ", ".join(f"{name}: object" for name in params) or ""
    lines = [
        '"""Generated constraint check."""',
        "",
        "from __future__ import annotations",
        "",
        *_header(block, extra_markers=[marker for marker in markers if marker]),
        "",
        f"def {fn_name}({param_sig}) -> bool:",
        f"    return {expr_to_python(check)}",
    ]
    return "\n".join(lines) + "\n"


def render_state(block: NormalizedBlock) -> str:
    enum_name = _pascal(block.name)
    states = block.body.get("states", [])
    transitions = block.body.get("transitions", [])
    lines = [
        '"""Generated state machine."""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import Enum",
        "",
        *_header(block),
        "",
        f"class {enum_name}(str, Enum):",
    ]
    if not states:
        lines.append('    UNKNOWN = "Unknown"')
    else:
        for state in states:
            key = _snake(state).upper()
            lines.append(f'    {key} = {state!r}')
    if transitions:
        lines.extend(["", "_TRANSITIONS = ["])
        for transition in transitions:
            lines.append(f"    {transition!r},")
        lines.append("]")
    return "\n".join(lines) + "\n"


def render_query(block: NormalizedBlock) -> str:
    fn_name = _snake(block.name)
    lines = [
        '"""Generated query stub."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        *_header(block),
        "",
        f"def {fn_name}(*args: Any, **kwargs: Any) -> Any:",
        f'    raise NotImplementedError("Query {block.name} — implementation phase")',
    ]
    return "\n".join(lines) + "\n"


def render_action(block: NormalizedBlock) -> str:
    fn_name = _snake(block.name)
    lines = [
        '"""Generated action stub."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        *_header(block),
        "",
        f"def {fn_name}(*args: Any, **kwargs: Any) -> Any:",
        f'    raise NotImplementedError("Action {block.name} — implementation phase")',
    ]
    return "\n".join(lines) + "\n"


def _step_comment(step: Any) -> str:
    if step.type == StepType.INPUT:
        names = ", ".join(field.name for field in step.fields)
        return f"# step {step.order} input: {names}"
    if step.type == StepType.VALIDATE:
        return f"# step {step.order} validate: {step.block}"
    if step.type == StepType.PROCESS:
        ops = ", ".join(op.op for op in step.ops)
        return f"# step {step.order} process: {ops}"
    if step.type == StepType.EMIT:
        return f"# step {step.order} emit: {step.event}"
    if step.type == StepType.FAIL:
        refs = ", ".join(step.refs)
        return f"# step {step.order} fail: {refs}"
    if step.type == StepType.RETURN:
        return f"# step {step.order} return: {step.block}"
    if step.type == StepType.QUERY:
        return f"# step {step.order} query: {step.query}"
    if step.type == StepType.ACTION:
        return f"# step {step.order} action: {step.action}"
    return f"# step {step.order} {step.type.value}"


def _import_path(artifact_path: str, symbol: str) -> str:
    module = artifact_path.replace("/", ".").removesuffix(".py")
    return f"from {module} import {symbol}"


def render_intent(
    block: NormalizedBlock,
    plan: ExecutionPlan,
    manifest: GenerationManifest,
    workspace: NormalizedWorkspace,
) -> str:
    fn_name = _snake(block.name)
    inputs = block.body.get("inputs", [])
    params = ", ".join(
        f"{field['name']}: {_field_python_type(field)}" for field in inputs
    )
    return_block = block.body.get("return")
    return_type = "None"
    if return_block:
        return_id = _resolve_ref_id(workspace, return_block, domain=block.file.domain)
        if return_id and return_id in workspace.blocks:
            return_type = _pascal(workspace.blocks[return_id].name)

    import_lines: list[str] = []
    for dep_id in sorted({dep for artifact in plan.artifacts for dep in artifact.depends}):
        entry = _manifest_entry_for_block(manifest, dep_id)
        if entry is None:
            continue
        dep_block = workspace.blocks.get(dep_id)
        if dep_block is None:
            continue
        symbol = _symbol_for_block(dep_block)
        import_lines.append(_import_path(entry.path, symbol))

    lines = [
        '"""Generated intent handler stub from execution plan."""',
        "",
        "from __future__ import annotations",
        "",
        *import_lines,
        "",
        *_header(block),
        "",
    ]
    for step in plan.steps:
        if step.type == StepType.INPUT:
            continue
        lines.append(_step_comment(step))
    lines.extend(
        [
            "",
            f"def {fn_name}({params}) -> {return_type}:",
            f'    """{block.desc.strip() if block.desc else block.name}"""',
            "    raise NotImplementedError(",
            f'        "Orchestration stub for {block.block_id} — wire plan steps above"',
            "    )",
        ]
    )
    return "\n".join(lines) + "\n"


def _symbol_for_block(block: NormalizedBlock) -> str:
    if block.kind == BlockKind.ENTITY:
        return _pascal(block.name)
    if block.kind == BlockKind.ERROR:
        return f"{_pascal(block.name)}Error"
    if block.kind in {BlockKind.RULE, BlockKind.CONSTRAINT, BlockKind.QUERY, BlockKind.ACTION}:
        return _snake(block.name)
    if block.kind == BlockKind.STATE:
        return _pascal(block.name)
    return _pascal(block.name)


def _manifest_entry_for_block(
    manifest: GenerationManifest,
    block_id: str,
) -> Any | None:
    for entry in manifest.entries.values():
        if block_id in entry.block_ids:
            return entry
    return None


def _resolve_ref_id(
    workspace: NormalizedWorkspace,
    ref: dict[str, Any] | None,
    *,
    domain: str | None = None,
) -> str | None:
    if not ref:
        return None
    return workspace.resolve(NormalizedRef.model_validate(ref), domain=domain)


def render_for_job(
    job_type: JobType,
    block: NormalizedBlock,
    workspace: NormalizedWorkspace,
    *,
    plan: ExecutionPlan | None = None,
    manifest: GenerationManifest | None = None,
) -> str:
    if job_type == JobType.ENTITY_SCHEMA:
        return render_entity(block)
    if job_type == JobType.ERROR_DEF:
        return render_error(block)
    if job_type == JobType.RULE_IMPL:
        return render_rule(block)
    if job_type == JobType.CONSTRAINT_IMPL:
        return render_constraint(block, workspace)
    if job_type == JobType.STATE_MACHINE:
        return render_state(block)
    if job_type == JobType.QUERY_IMPL:
        return render_query(block)
    if job_type == JobType.ACTION_IMPL:
        return render_action(block)
    if job_type == JobType.INTENT_HANDLER:
        if plan is None or manifest is None:
            msg = "Intent handler rendering requires execution plan and manifest"
            raise ValueError(msg)
        return render_intent(block, plan, manifest, workspace)
    msg = f"Unsupported job type: {job_type.value}"
    raise ValueError(msg)
