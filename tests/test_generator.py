"""Generator scope, queue, session, manifest, templates, and execution tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yoni.generator.errors import GenerateError
from yoni.generator.execute import execute_job, run_all_pending, run_next_job
from yoni.generator.manifest import (
    checksum_text,
    load_manifest,
    record_entry,
    save_manifest,
)
from yoni.generator.models import GenerationLayer, GenerationManifest, ScopeRequest
from yoni.generator.plans import load_plan
from yoni.generator.queue import build_queue
from yoni.generator.run import prepare_generation, prepare_impact_regen, scope_from_intent
from yoni.generator.scope import resolve_scope
from yoni.generator.session import (
    load_session,
    mark_job_done,
    next_pending,
    save_session,
)
from yoni.generator.templates import render_entity, render_rule
from yoni.generator.verify import extract_block_markers, verify_content
from yoni.graph.builder import build_graph
from yoni.normalizer.run import normalize_workspace
from yoni.pipeline import compile_workspace
from yoni.planner.models import JobType
from yoni.workspace.loader import load_workspace

ROOT = Path("samples/invoicing")


def _compiled():
    ws = load_workspace(ROOT)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    return norm, graph


def test_resolve_scope_intent_closure() -> None:
    norm, graph = _compiled()
    scope = scope_from_intent("INT_REGISTER_USER_001")
    resolved = resolve_scope(norm, graph, scope)

    assert resolved.intent_ids == ["INT_REGISTER_USER_001"]
    assert "ENT_CUSTOMER_001" in resolved.block_closure
    assert "RULE_ADULT_001" in resolved.block_closure
    assert "INT_REGISTER_USER_001" in resolved.block_closure


def test_resolve_scope_domain() -> None:
    norm, graph = _compiled()
    scope = ScopeRequest(targets=["customer"], layers=[GenerationLayer.BACKEND])
    resolved = resolve_scope(norm, graph, scope)

    assert "INT_REGISTER_USER_001" in resolved.intent_ids
    assert len(resolved.intent_ids) >= 5


def test_resolve_scope_unknown_target_raises() -> None:
    norm, graph = _compiled()
    scope = ScopeRequest(targets=["nope-domain"])
    with pytest.raises(GenerateError) as exc:
        resolve_scope(norm, graph, scope)
    assert exc.value.code == "YONI5005"


def test_build_queue_register_user_order() -> None:
    norm, graph = _compiled()
    scope = scope_from_intent("INT_REGISTER_USER_001")
    resolved = resolve_scope(norm, graph, scope)
    plan = load_plan(ROOT, "INT_REGISTER_USER_001")

    queue = build_queue([plan], resolved, norm)
    assert len(queue) == 6
    assert queue[0].id == "job_001"
    assert queue[-1].type == JobType.INTENT_HANDLER
    assert queue[-1].block == "INT_REGISTER_USER_001"
    assert queue[-1].artifact == "generated/intents/register-user.py"

    types = [job.type for job in queue]
    assert types.index(JobType.ENTITY_SCHEMA) < types.index(JobType.RULE_IMPL)
    assert types.index(JobType.RULE_IMPL) < types.index(JobType.INTENT_HANDLER)


def test_build_queue_dedupes_shared_entity() -> None:
    norm, graph = _compiled()
    scope = ScopeRequest(
        targets=["INT_REGISTER_USER_001", "INT_CREATE_INV_001"],
        layers=[GenerationLayer.BACKEND],
    )
    resolved = resolve_scope(norm, graph, scope)
    plans = [
        load_plan(ROOT, "INT_REGISTER_USER_001"),
        load_plan(ROOT, "INT_CREATE_INV_001"),
    ]

    queue = build_queue(plans, resolved, norm)
    customer_jobs = [job for job in queue if job.block == "ENT_CUSTOMER_001"]
    assert len(customer_jobs) == 1


def test_prepare_generation_writes_session_and_manifest(tmp_path: Path) -> None:
    result = compile_workspace(ROOT)
    assert result.ok

    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    stale = dest / ".ai" / "generation" / "session.json"
    if stale.exists():
        stale.unlink()

    session, session_path, manifest_path = prepare_generation(
        dest,
        scope_from_intent("INT_REGISTER_USER_001"),
    )

    assert session.session_id.startswith("gen_")
    assert session_path.exists()
    assert manifest_path.exists()
    assert len(session.queue) == 6

    payload = json.loads(session_path.read_text(encoding="utf-8"))
    assert payload["intent_ids"] == ["INT_REGISTER_USER_001"]
    assert payload["queue"][0]["status"] == "pending"


def test_continue_next_pending(tmp_path: Path) -> None:
    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))

    pending = next_pending(session)
    assert pending is not None
    assert pending.id == "job_001"

    mark_job_done(session, pending.id)
    save_session(dest, session)

    reloaded = load_session(dest)
    assert reloaded is not None
    assert reloaded.queue[0].status.value == "done"
    assert next_pending(reloaded).id == "job_002"


def test_manifest_record_and_checksum() -> None:
    manifest = GenerationManifest()
    entry = record_entry(
        manifest,
        path="generated/entities/customer.py",
        block_ids=["ENT_CUSTOMER_001"],
        job_id="job_001",
        content="class Customer: ...",
    )
    assert entry.checksum == checksum_text("class Customer: ...")
    assert entry.generated_at


def test_impact_regen_requeues_and_clears_manifest(tmp_path: Path) -> None:
    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))

    manifest = GenerationManifest()
    record_entry(
        manifest,
        path="generated/entities/customer.py",
        block_ids=["ENT_CUSTOMER_001"],
        job_id="job_001",
        content="entity",
    )
    save_manifest(dest, manifest)

    for job in session.queue:
        if job.block == "ENT_CUSTOMER_001":
            mark_job_done(session, job.id)
    save_session(dest, session)

    session, manifest, impact, requeued, stale_paths = prepare_impact_regen(
        dest,
        "ENT_CUSTOMER_001",
    )

    assert impact.block_id == "ENT_CUSTOMER_001"
    assert stale_paths == ["generated/entities/customer.py"]
    assert "generated/entities/customer.py" not in manifest.entries
    customer_job = next(job for job in session.queue if job.block == "ENT_CUSTOMER_001")
    assert customer_job.status.value == "pending"
    assert requeued


def test_generate_cli_integration(tmp_path: Path, capsys) -> None:
    import shutil

    from yoni.generator.cli import main as generate_main

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)

    code = generate_main(
        ["--root", str(dest), "--intent", "INT_REGISTER_USER_001"],
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "session gen_" in out
    assert "job_001" in out
    assert (dest / ".ai" / "generation" / "session.json").exists()


def test_render_entity_customer() -> None:
    norm, _ = _compiled()
    block = norm.blocks["ENT_CUSTOMER_001"]
    content = render_entity(block)
    assert "# yoni:ENT_CUSTOMER_001" in content
    assert "class Customer(BaseModel):" in content
    assert "email: str" in content
    assert "age: int" in content
    assert verify_content(content, ["ENT_CUSTOMER_001"]) == []


def test_render_rule_adult() -> None:
    norm, _ = _compiled()
    block = norm.blocks["RULE_ADULT_001"]
    content = render_rule(block)
    assert "# yoni:RULE_ADULT_001" in content
    assert "def adult(age: int) -> bool:" in content
    assert "return (age >= 18)" in content


def test_execute_job_writes_file_and_manifest(tmp_path: Path) -> None:
    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))
    norm, _ = _compiled()
    manifest = GenerationManifest()
    job = session.queue[0]

    result = execute_job(dest, session, job, norm, manifest)
    assert result.status.value == "done"
    assert (dest / result.artifact).exists()
    assert "# yoni:ENT_CUSTOMER_001" in (dest / result.artifact).read_text(encoding="utf-8")
    assert result.artifact in manifest.entries
    reloaded = load_session(dest)
    assert reloaded is not None
    assert reloaded.queue[0].status.value == "done"


def test_run_next_job(tmp_path: Path) -> None:
    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))

    result = run_next_job(dest, session.session_id)
    assert result is not None
    assert result.status.value == "done"
    assert (dest / result.artifact).exists()


def test_run_all_pending_completes_queue(tmp_path: Path) -> None:
    import shutil

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))

    results = run_all_pending(dest, session.session_id)
    assert len(results) == 6
    assert all(result.status.value == "done" for result in results)

    reloaded = load_session(dest)
    assert reloaded is not None
    assert next_pending(reloaded) is None

    manifest = load_manifest(dest)
    assert "generated/entities/customer.py" in manifest.entries
    assert "generated/intents/register-user.py" in manifest.entries
    intent_content = (dest / "generated/intents/register-user.py").read_text(encoding="utf-8")
    assert "# yoni:INT_REGISTER_USER_001" in intent_content
    assert "def register_user(" in intent_content


def test_continue_cli_runs_one_job(tmp_path: Path, capsys) -> None:
    import shutil

    from yoni.generator.cli import main as generate_main

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    session, _, _ = prepare_generation(dest, scope_from_intent("INT_REGISTER_USER_001"))

    code = generate_main(["--root", str(dest), "--continue", session.session_id])
    assert code == 0
    out = capsys.readouterr().out
    assert "ran job_001" in out
    assert (dest / "generated/entities/customer.py").exists()


def test_generate_run_flag_completes_queue(tmp_path: Path, capsys) -> None:
    import shutil

    from yoni.generator.cli import main as generate_main

    dest = tmp_path / "invoicing"
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)

    code = generate_main(
        ["--root", str(dest), "--intent", "INT_REGISTER_USER_001", "--run"],
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "queue complete" in out
    assert (dest / "generated/intents/register-user.py").exists()


def test_extract_block_markers() -> None:
    content = "# yoni:ENT_CUSTOMER_001\nclass Customer:\n    pass\n"
    assert extract_block_markers(content) == {"ENT_CUSTOMER_001"}
