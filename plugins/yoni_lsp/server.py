"""Yoni LSP server — live diagnostics from parse_source."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from yoni import parse_source
from yoni.errors import ParseError

from plugins.yoni_lsp.ranges import error_to_range

server = LanguageServer("yoni-lsp", "0.1.0")


def _to_diagnostic(error: ParseError, source: str) -> types.Diagnostic:
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


def _validate(ls: LanguageServer, uri: str) -> None:
    document = ls.workspace.get_text_document(uri)
    if document is None:
        return

    source = document.source or ""
    file_path = document.path or uri
    result = parse_source(source, file=file_path)
    diagnostics = [_to_diagnostic(error, source) for error in result.errors]

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
