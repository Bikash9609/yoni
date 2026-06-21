"""Entry point: python -m plugins.yoni_lsp"""

from plugins.yoni_lsp.server import server


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
