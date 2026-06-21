"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode_1 = require("vscode");
const node_1 = require("vscode-languageclient/node");
let client;
function resolvePythonPath() {
    const config = vscode_1.workspace.getConfiguration("yoni");
    let pythonPath = config.get("pythonPath") ?? "${workspaceFolder}/.venv/bin/python";
    const folder = vscode_1.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (folder) {
        pythonPath = pythonPath.replace("${workspaceFolder}", folder);
    }
    return pythonPath;
}
function resolveWorkspaceRoot() {
    return vscode_1.workspace.workspaceFolders?.[0]?.uri.fsPath;
}
function activate(context) {
    const workspaceRoot = resolveWorkspaceRoot();
    if (!workspaceRoot) {
        void vscode_1.window.showWarningMessage("Yoni: open a workspace folder to enable language server diagnostics.");
        return;
    }
    const pythonPath = resolvePythonPath();
    const serverOptions = {
        command: pythonPath,
        args: ["-m", "plugins.yoni_lsp"],
        options: {
            cwd: workspaceRoot,
            env: {
                ...process.env,
                PYTHONPATH: workspaceRoot,
            },
        },
        transport: node_1.TransportKind.stdio,
    };
    const clientOptions = {
        documentSelector: [
            { scheme: "file", language: "yoni" },
        ],
        synchronize: {
            fileEvents: vscode_1.workspace.createFileSystemWatcher("**/*.{yoni,yni,yo}"),
        },
    };
    client = new node_1.LanguageClient("yoniLanguageServer", "Yoni Language Server", serverOptions, clientOptions);
    context.subscriptions.push(client);
    client.start();
}
async function deactivate() {
    if (client) {
        await client.stop();
    }
}
//# sourceMappingURL=extension.js.map