import { workspace, ExtensionContext, window } from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

function resolvePythonPath(): string {
  const config = workspace.getConfiguration("yoni");
  let pythonPath = config.get<string>("pythonPath") ?? "${workspaceFolder}/.venv/bin/python";

  const folder = workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (folder) {
    pythonPath = pythonPath.replace("${workspaceFolder}", folder);
  }

  return pythonPath;
}

function resolveWorkspaceRoot(): string | undefined {
  return workspace.workspaceFolders?.[0]?.uri.fsPath;
}

export function activate(context: ExtensionContext): void {
  const workspaceRoot = resolveWorkspaceRoot();
  if (!workspaceRoot) {
    void window.showWarningMessage(
      "Yoni: open a workspace folder to enable language server diagnostics."
    );
    return;
  }

  const pythonPath = resolvePythonPath();
  const serverOptions: ServerOptions = {
    command: pythonPath,
    args: ["-m", "plugins.yoni_lsp"],
    options: {
      cwd: workspaceRoot,
      env: {
        ...process.env,
        PYTHONPATH: workspaceRoot,
      },
    },
    transport: TransportKind.stdio,
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: "file", language: "yoni" },
    ],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher("**/*.{yoni,yni,yo}"),
    },
  };

  client = new LanguageClient(
    "yoniLanguageServer",
    "Yoni Language Server",
    serverOptions,
    clientOptions
  );

  context.subscriptions.push(client);
  client.start();
}

export async function deactivate(): Promise<void> {
  if (client) {
    await client.stop();
  }
}
