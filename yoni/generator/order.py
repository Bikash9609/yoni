"""Topological ordering for generation jobs."""

from __future__ import annotations

import networkx as nx

from yoni.generator.errors import GenerateError
from yoni.generator.models import GenerationJob
from yoni.planner.models import JobType

_JOB_PRIORITY: dict[JobType, int] = {
    JobType.ENTITY_SCHEMA: 10,
    JobType.STATE_MACHINE: 20,
    JobType.ERROR_DEF: 30,
    JobType.RULE_IMPL: 40,
    JobType.CONSTRAINT_IMPL: 50,
    JobType.QUERY_IMPL: 60,
    JobType.ACTION_IMPL: 70,
    JobType.INTENT_HANDLER: 80,
}


def sort_jobs(jobs: list[GenerationJob]) -> list[GenerationJob]:
    """Return jobs in dependency-safe build order."""
    if not jobs:
        return []

    def _key(job: GenerationJob) -> str:
        return f"{job.type.value}:{job.block}"

    by_key = {_key(job): job for job in jobs}
    block_to_job_key: dict[str, str] = {}
    for job in jobs:
        job_key = _key(job)
        existing_key = block_to_job_key.get(job.block)
        if existing_key is None:
            block_to_job_key[job.block] = job_key
            continue
        current = by_key[existing_key]
        if _JOB_PRIORITY[job.type] < _JOB_PRIORITY[current.type]:
            block_to_job_key[job.block] = job_key

    graph = nx.DiGraph()
    for job in jobs:
        graph.add_node(_key(job), priority=_JOB_PRIORITY.get(job.type, 99))

    for job in jobs:
        job_key = _key(job)
        for dep_block in job.depends:
            dep_key = block_to_job_key.get(dep_block)
            if dep_key and dep_key != job_key:
                graph.add_edge(dep_key, job_key)

    if not nx.is_directed_acyclic_graph(graph):
        raise GenerateError(
            "YONI5006",
            "Job dependency cycle detected",
            suggestion="Check execution plan artifact depends lists.",
        )

    ordered_keys = list(
        nx.lexicographical_topological_sort(
            graph,
            key=lambda node_key: (
                _JOB_PRIORITY.get(by_key[node_key].type, 99),
                by_key[node_key].block,
                node_key,
            ),
        )
    )
    return [by_key[node_key] for node_key in ordered_keys]
