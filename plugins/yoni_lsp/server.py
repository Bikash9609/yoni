"""Yoni LSP server — parse + workspace validation diagnostics."""

from __future__ import annotations

from pathlib import Path

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from yoni import parse_source
from yoni.diagnostics import Diagnostic
from yoni.pipeline import compile_workspace
from yoni.validator.models import ValidationError

from plugins.yoni_lsp.ranges import error_to_range

server = LanguageServer("yoni-lsp", "0.1.0")


def _find_project_root(file_path: str) -> Path | None:
    path = Path(file_path).resolve()
    if path.is_file():
        path = path.parent
    for candidate in [path, *path.parents]:
        if (candidate / "project").is_dir() or (candidate / "domains").is_dir():
            return candidate
    return None


def _to_diagnostic(error: Diagnostic, source: str) -> types.Diagnostic:
    severity = (
        types.DiagnosticSeverity.Warning
        if error.severity == "warning"
        else types.DiagnosticSeverity.Error
    )
    message = error.message
    if error.suggestion:
        message = f"{error.message} — {error.suggestion}"

    return types.Diagnostic(
        range=error_to_range(source, error),
        message=message,
        severity=severity,
        code=error.code,
        source="yoni",
    )


def _validation_for_file(
    file_path: str,
    rel_path: str,
) -> list[ValidationError]:
    root = _find_project_root(file_path)
    if root is None:
        return []
    result = compile_workspace(root, write_cache=False)
    if not result.normalized:
        return []
    rel = rel_path.replace("\\", "/")
    block_ids = {
        block.block_id
        for block in result.normalized.blocks.values()
        if block.file.rel_path.replace("\\", "/") == rel
    }
    errors: list[ValidationError] = []
    for error in result.validation_errors:
        if error.file.replace("\\", "/") == rel or error.block_id in block_ids:
            errors.append(error)
    return errors


def _validate(ls: LanguageServer, uri: str) -> None:
    document = ls.workspace.get_text_document(uri)
    if document is None:
        return

    source = document.source or ""
    file_path = document.path or uri
    result = parse_source(source, file=file_path)
    diagnostics: list[types.Diagnostic] = [
        _to_diagnostic(error, source) for error in result.errors
    ]

    rel_path = file_path
    root = _find_project_root(file_path)
    if root is not None:
        try:
            rel_path = str(Path(file_path).resolve().relative_to(root))
        except ValueError:
            rel_path = file_path

    if result.ok:
        for error in _validation_for_file(file_path, rel_path):
            diagnostics.append(_to_diagnostic(error, source))

    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    _validate(ls, params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    _validate(ls, params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: LanguageServer, params: types.DidSaveTextDocumentParams) -> None:
    _validate(ls, params.text_document.uri)
