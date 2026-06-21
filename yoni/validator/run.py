"""Run all graph validation rules."""

from __future__ import annotations

from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError
from yoni.validator.rules.cycles import check_cycles
from yoni.validator.rules.duplicates import check_duplicates
from yoni.validator.rules.evolution import check_evolution
from yoni.validator.rules.naming import check_naming
from yoni.validator.rules.references import check_references
from yoni.validator.rules.repository import check_repository
from yoni.validator.rules.string_refs import check_string_refs
from yoni.workspace.loader import Workspace


def validate_workspace(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    source: Workspace | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    errors.extend(check_duplicates(workspace, source))
    errors.extend(check_naming(workspace))
    errors.extend(check_repository(workspace))
    errors.extend(check_references(workspace, graph))
    errors.extend(check_string_refs(workspace))
    errors.extend(check_cycles(workspace, graph))
    errors.extend(check_evolution(workspace))
    return errors
