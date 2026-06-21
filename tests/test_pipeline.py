"""End-to-end pipeline tests."""

from pathlib import Path

from yoni.pipeline import compile_workspace


def test_pipeline_writes_cache_artifacts(tmp_path: Path) -> None:
    root = Path("samples/invoicing")
    result = compile_workspace(root, write_cache=True)
    cache = root / ".ai" / "cache"
    assert (cache / "normalized" / "normalized.json").is_file()
    assert (cache / "graph" / "graph.json").is_file()
    assert result.ok
    assert result.normalized is not None
    assert result.graph is not None
    assert len(result.normalized.blocks) == 111
    assert len(result.graph.nodes) == 111
