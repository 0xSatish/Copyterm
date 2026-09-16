const vscode = require('vscode');
const net = require('net');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

let ipcServer = null;
let discoveryFilePath = null;
let authToken = null;
let outputChannel = null;

function getCopyTermDir() {
    const custom = process.env.COPYTERM_DATA_DIR;
    if (custom) return custom;
    if (process.platform === 'win32') {
        const profile = process.env.USERPROFILE;
        if (profile) return path.join(profile, '.copyterm');
        const appdata = process.env.LOCALAPPDATA;
        if (appdata) return path.join(appdata, 'copyterm');
    }
    return path.join(os.homedir(), '.copyterm');
}

function logDebug(msg) {
    try {
        const logFile = path.join(getCopyTermDir(), 'ide_bridge_debug.log');
        const ts = new Date().toISOString();
        fs.appendFileSync(logFile, `[${ts}] ${msg}\n`, 'utf8');
    } catch {}
    if (outputChannel) {
        try { outputChannel.appendLine(msg); } catch {}
    }
}

function generateEndpoint() {
    if (process.platform === 'win32') {
        const userHash = crypto.createHash('sha256').update(os.userInfo().username || 'user').digest('hex').substring(0, 8);
        return `\\\\.\\pipe\\copyterm-ide-${userHash}`;
    } else {
        return path.join(getCopyTermDir(), 'ide_bridge.sock');
    }
}

async function findTerminalForPids(callerPids) {
    const terminals = vscode.window.terminals;
    if (!terminals || terminals.length === 0) {
        logDebug("findTerminalForPids: 0 terminals open in IDE");
        return { terminal: null, error: "No open terminals found in IDE." };
    }

    logDebug(`findTerminalForPids: Searching for callerPids=[${callerPids.join(', ')}] among ${terminals.length} terminals`);
    
    const terminalList = [];
    for (let i = 0; i < terminals.length; i++) {
        const t = terminals[i];
        let pid = null;
        try {
            pid = await t.processId;
        } catch (err) {
            logDebug(`  Terminal #${i} ("${t.name}") processId error: ${err.message}`);
        }
        terminalList.push({ index: i, name: t.name, pid: pid, terminal: t });
        logDebug(`  Terminal #${i}: name="${t.name}", processId=${pid}`);
    }

    // Match against any caller PID in the ancestor hierarchy
    const matches = [];
    for (const termInfo of terminalList) {
        if (termInfo.pid && callerPids.includes(termInfo.pid)) {
            // Find priority index in callerPids (lower index = closer ancestor)
            const priority = callerPids.indexOf(termInfo.pid);
            matches.push({ ...termInfo, priority });
        }
    }

    logDebug(`findTerminalForPids: Found ${matches.length} matches among ancestors`);

    if (matches.length === 1) {
        logDebug(`findTerminalForPids: Selected terminal #${matches[0].index} ("${matches[0].name}", PID: ${matches[0].pid})`);
        return { terminal: matches[0].terminal, processId: matches[0].pid, name: matches[0].name };
    } else if (matches.length > 1) {
        // Sort by closest ancestor
        matches.sort((a, b) => a.priority - b.priority);
        logDebug(`findTerminalForPids: Multiple matches resolved to closest ancestor: #${matches[0].index} ("${matches[0].name}", PID: ${matches[0].pid})`);
        return { terminal: matches[0].terminal, processId: matches[0].pid, name: matches[0].name };
    }

    // If callerPids has no match, check if active terminal is available
    const active = vscode.window.activeTerminal;
    let activePid = null;
    if (active) {
        try { activePid = await active.processId; } catch {}
    }

    // If only 1 terminal is open in the entire IDE, it is safe to use
    if (terminalList.length === 1 && terminalList[0].terminal) {
        logDebug(`findTerminalForPids: Exact PID match not found, but only 1 terminal open in IDE (#0 "${terminalList[0].name}", PID: ${terminalList[0].pid})`);
        return { terminal: terminalList[0].terminal, processId: terminalList[0].pid, name: terminalList[0].name, isSingleFallback: true };
    }

    const availablePidsStr = terminalList.map(t => `${t.name}:${t.pid}`).join(', ');
    logDebug(`findTerminalForPids: No match for [${callerPids.join(', ')}]. Available: [${availablePidsStr}]`);

    return {
        terminal: null,
        error: `No terminal matching process tree [${callerPids.join(', ')}] found in IDE. (Open terminals: ${availablePidsStr})`,
        availableTerminals: terminalList.map(t => ({ name: t.name, process_id: t.pid }))
    };
}

async function extractTerminalBuffer(targetTerminal) {
    logDebug(`extractTerminalBuffer: Starting extraction for terminal "${targetTerminal.name}"`);
    let originalClipboard = "";
    try {
        originalClipboard = await vscode.env.clipboard.readText();
    } catch (clipErr) {
        logDebug(`extractTerminalBuffer: Failed to read initial clipboard: ${clipErr.message}`);
    }

    try {
        // Explicitly focus target terminal
        targetTerminal.show(false);
        await new Promise(r => setTimeout(r, 120));

        logDebug("extractTerminalBuffer: Executing workbench.action.terminal.selectAll");
        await vscode.commands.executeCommand('workbench.action.terminal.selectAll');
        await new Promise(r => setTimeout(r, 150));

        logDebug("extractTerminalBuffer: Executing workbench.action.terminal.copySelection");
        await vscode.commands.executeCommand('workbench.action.terminal.copySelection');
        await new Promise(r => setTimeout(r, 200));

        const bufferContent = await vscode.env.clipboard.readText();
        const charCount = bufferContent ? bufferContent.length : 0;
        const lineCount = bufferContent ? bufferContent.split(/\r?\n/).length : 0;
        logDebug(`extractTerminalBuffer: Read clipboard content: ${charCount} chars, ${lineCount} lines`);

        logDebug("extractTerminalBuffer: Executing workbench.action.terminal.clearSelection");
        await vscode.commands.executeCommand('workbench.action.terminal.clearSelection');

        // Restore original user clipboard
        try {
            await vscode.env.clipboard.writeText(originalClipboard);
            logDebug("extractTerminalBuffer: Restored original user clipboard");
        } catch (restErr) {
            logDebug(`extractTerminalBuffer: Failed to restore clipboard: ${restErr.message}`);
        }

        return bufferContent || "";
    } catch (err) {
        logDebug(`extractTerminalBuffer: ERROR: ${err.message}\n${err.stack}`);
        try {
            await vscode.commands.executeCommand('workbench.action.terminal.clearSelection');
            await vscode.env.clipboard.writeText(originalClipboard);
        } catch {}
        throw err;
    }
}

function handleClientConnection(socket) {
    let rawBuffer = "";

    socket.on('data', async (chunk) => {
        rawBuffer += chunk.toString('utf8');

        if (rawBuffer.includes('\n') || rawBuffer.endsWith('}')) {
            const msgStr = rawBuffer.trim();
            rawBuffer = "";

            let req;
            try {
                req = JSON.parse(msgStr);
            } catch (parseErr) {
                logDebug(`handleClientConnection: Malformed JSON: ${parseErr.message}`);
                socket.write(JSON.stringify({
                    version: 1,
                    ok: false,
                    error: "Malformed JSON request"
                }) + "\n");
                return;
            }

            logDebug(`handleClientConnection: Request action="${req.action}", caller_pid=${req.caller_pid}, caller_pids=[${(req.caller_pids || []).join(',')}]`);

            // Authentication verification
            if (!req.auth_token || req.auth_token !== authToken) {
                logDebug("handleClientConnection: REJECTED Unauthorized auth_token");
                socket.write(JSON.stringify({
                    version: 1,
                    ok: false,
                    error: "Unauthorized: Invalid or missing authentication token"
                }) + "\n");
                return;
            }

            if (req.action === 'ping') {
                logDebug("handleClientConnection: PING -> PONG");
                socket.write(JSON.stringify({
                    version: 1,
                    ok: true,
                    message: "pong",
                    ide: "Antigravity",
                    protocol_version: 1
                }) + "\n");
                return;
            }

            if (req.action === 'doctor') {
                const terminals = vscode.window.terminals || [];
                const active = vscode.window.activeTerminal;
                let activePid = null;
                if (active) {
                    try { activePid = await active.processId; } catch {}
                }

                const terminalDetails = [];
                for (let i = 0; i < terminals.length; i++) {
                    const t = terminals[i];
                    let p = null;
                    try { p = await t.processId; } catch {}
                    terminalDetails.push({
                        index: i,
                        name: t.name,
                        process_id: p,
                        is_active: (active && t === active)
                    });
                }

                logDebug(`handleClientConnection: DOCTOR requested (${terminals.length} terminals)`);
                socket.write(JSON.stringify({
                    version: 1,
                    ok: true,
                    ide: "Antigravity",
                    terminal_count: terminals.length,
                    active_terminal: active ? { name: active.name, process_id: activePid } : null,
                    terminals: terminalDetails,
                    capabilities: {
                        terminal_buffer: true,
                        historical_scrollback: true,
                        wrapped_line_serialization: true
                    }
                }) + "\n");
                return;
            }

            if (req.action === 'capture_terminal') {
                let callerPids = [];
                if (Array.isArray(req.caller_pids) && req.caller_pids.length > 0) {
                    callerPids = req.caller_pids.map(p => parseInt(p, 10)).filter(p => !isNaN(p) && p > 0);
                } else if (req.caller_pid) {
                    callerPids = [parseInt(req.caller_pid, 10)];
                }

                logDebug(`handleClientConnection: CAPTURE requested for callerPids=[${callerPids.join(', ')}]`);

                const termResult = await findTerminalForPids(callerPids);

                if (!termResult.terminal) {
                    logDebug(`handleClientConnection: Terminal matching failed: ${termResult.error}`);
                    socket.write(JSON.stringify({
                        version: 1,
                        ok: false,
                        error: termResult.error || "Terminal not found",
                        available_terminals: termResult.availableTerminals || []
                    }) + "\n");
                    return;
                }

                try {
                    const content = await extractTerminalBuffer(termResult.terminal);
                    const lineCount = content ? content.split(/\r?\n/).length : 0;
                    const byteCount = content ? Buffer.byteLength(content, 'utf8') : 0;
                    logDebug(`handleClientConnection: Capture SUCCESS for "${termResult.name}" (PID ${termResult.processId}): ${lineCount} lines, ${byteCount} bytes`);

                    socket.write(JSON.stringify({
                        version: 1,
                        ok: true,
                        terminal: {
                            name: termResult.name,
                            process_id: termResult.processId
                        },
                        content: content,
                        metadata: {
                            source: "xterm",
                            historical: true,
                            line_count: lineCount,
                            byte_count: byteCount
                        }
                    }) + "\n");
                } catch (captureErr) {
                    logDebug(`handleClientConnection: Capture EXCEPTION: ${captureErr.message}`);
                    socket.write(JSON.stringify({
                        version: 1,
                        ok: false,
                        error: "Capture failed: " + captureErr.message
                    }) + "\n");
                }
                return;
            }

            logDebug(`handleClientConnection: Unknown action: ${req.action}`);
            socket.write(JSON.stringify({
                version: 1,
                ok: false,
                error: `Unknown action: ${req.action}`
            }) + "\n");
        }
    });

    socket.on('error', (err) => {
        logDebug(`handleClientConnection: Socket error: ${err.message}`);
    });
}

function startIpcServer() {
    const copytermDir = getCopyTermDir();
    if (!fs.existsSync(copytermDir)) {
        fs.mkdirSync(copytermDir, { recursive: true });
    }

    const endpoint = generateEndpoint();
    authToken = crypto.randomBytes(24).toString('hex');

    if (process.platform !== 'win32' && fs.existsSync(endpoint)) {
        try { fs.unlinkSync(endpoint); } catch {}
    }

    ipcServer = net.createServer((socket) => {
        handleClientConnection(socket);
    });

    ipcServer.listen(endpoint, () => {
        discoveryFilePath = path.join(copytermDir, 'ide_bridge.json');
        const discoveryData = {
            pid: process.pid,
            ide: "Antigravity",
            product_name: "Antigravity IDE",
            protocol_version: 1,
            endpoint: endpoint,
            auth_token: authToken,
            capabilities: {
                terminal_buffer: true,
                historical_scrollback: true,
                wrapped_line_serialization: true
            },
            created_at_ms: Date.now()
        };

        fs.writeFileSync(discoveryFilePath, JSON.stringify(discoveryData, null, 2), {
            encoding: 'utf8',
            mode: 0o600
        });

        logDebug(`CopyTerm IDE Bridge active on: ${endpoint} (PID: ${process.pid})`);
    });

    ipcServer.on('error', (err) => {
        logDebug(`CopyTerm IDE Bridge server error: ${err.message}`);
    });
}

function activate(context) {
    outputChannel = vscode.window.createOutputChannel("CopyTerm Bridge");
    logDebug("CopyTerm Terminal Bridge Extension Initializing...");

    try {
        startIpcServer();
    } catch (err) {
        logDebug(`Failed to start IPC server: ${err.message}`);
    }

    let captureCmd = vscode.commands.registerCommand('copyterm.captureTerminal', async () => {
        const active = vscode.window.activeTerminal;
        if (!active) {
            vscode.window.showWarningMessage("CopyTerm: No active terminal to capture.");
            return;
        }
        try {
            const content = await extractTerminalBuffer(active);
            if (content) {
                await vscode.env.clipboard.writeText(content);
                const lineCount = content.split(/\r?\n/).length;
                vscode.window.showInformationMessage(`CopyTerm: Copied ${lineCount} lines from active terminal.`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`CopyTerm Capture Error: ${err.message}`);
        }
    });

    let doctorCmd = vscode.commands.registerCommand('copyterm.doctor', async () => {
        outputChannel.show(true);
        outputChannel.appendLine("=== CopyTerm IDE Bridge Diagnostics ===");
        outputChannel.appendLine(`PID: ${process.pid}`);
        outputChannel.appendLine(`Terminals Open: ${vscode.window.terminals.length}`);
        outputChannel.appendLine(`IPC Discovery: ${discoveryFilePath}`);
        outputChannel.appendLine(`IPC Status: ${ipcServer && ipcServer.listening ? "LISTENING" : "STOPPED"}`);
    });

    context.subscriptions.push(captureCmd);
    context.subscriptions.push(doctorCmd);
}

function deactivate() {
    logDebug("CopyTerm IDE Bridge deactivating...");
    if (discoveryFilePath && fs.existsSync(discoveryFilePath)) {
        try { fs.unlinkSync(discoveryFilePath); } catch {}
    }
    if (ipcServer) {
        try { ipcServer.close(); } catch {}
    }
}

module.exports = {
    activate,
    deactivate
};
