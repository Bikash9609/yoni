"""Artifact manifest persistence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from yoni.generator.models import GenerationManifest, ManifestEntry, utc_now_iso


def manifest_path(root: Path) -> Path:
    return root / ".ai" / "generation" / "manifest.json"


def load_manifest(root: Path | str) -> GenerationManifest:
    path = manifest_path(Path(root))
    if not path.exists():
        return GenerationManifest()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GenerationManifest.model_validate(payload)


def save_manifest(root: Path | str, manifest: GenerationManifest) -> Path:
    path = manifest_path(Path(root))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def record_entry(
    manifest: GenerationManifest,
    *,
    path: str,
    block_ids: list[str],
    job_id: str,
    content: str = "",
) -> ManifestEntry:
    checksum = checksum_text(content)
    entry = ManifestEntry(
        path=path,
        block_ids=sorted(set(block_ids)),
        job_id=job_id,
        checksum=checksum,
        generated_at=utc_now_iso(),
    )
    manifest.entries[path] = entry
    return entry


def checksum_text(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def paths_for_blocks(
    manifest: GenerationManifest,
    block_ids: set[str],
) -> list[str]:
    matched: list[str] = []
    for path, entry in manifest.entries.items():
        if block_ids & set(entry.block_ids):
            matched.append(path)
    return sorted(matched)


def remove_entries(manifest: GenerationManifest, paths: list[str]) -> None:
    for path in paths:
        manifest.entries.pop(path, None)
