const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const os = require('os');

function activate(context) {
    const outputChannel = vscode.window.createOutputChannel("CopyTerm POC");
    
    let disposable = vscode.commands.registerCommand('copyterm.testTerminalBuffer', async () => {
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine("============================================================");
        outputChannel.appendLine("     ANTIGRAVITY TERMINAL BUFFER PROOF-OF-CONCEPT (POC)     ");
        outputChannel.appendLine("============================================================");

        const terminals = vscode.window.terminals;
        const activeTerminal = vscode.window.activeTerminal;

        outputChannel.appendLine(`Terminal Count: ${terminals.length}`);
        outputChannel.appendLine(`Active Terminal Name: ${activeTerminal ? activeTerminal.name : 'None'}`);

        const diagnostics = {
            timestamp: new Date().toISOString(),
            terminalCount: terminals.length,
            activeTerminal: null,
            terminals: [],
            directBufferAccess: false,
            directBufferDetails: null,
            commandBufferAccess: false,
            capturedBufferPreview: "",
            capturedLineCount: 0,
            capturedByteCount: 0,
            historicalMarkersFound: {},
            currentMarkersFound: {},
            wrappedLineAnalysis: null,
            errors: []
        };

        for (let i = 0; i < terminals.length; i++) {
            const t = terminals[i];
            let pid = undefined;
            try {
                pid = await t.processId;
            } catch (err) {
                pid = "Error: " + err.message;
            }

            const termInfo = {
                index: i,
                name: t.name,
                processId: pid,
                isActive: (activeTerminal && t === activeTerminal),
                properties: Object.getOwnPropertyNames(t),
                protoProperties: Object.getOwnPropertyNames(Object.getPrototypeOf(t) || {}),
                symbols: Object.getOwnPropertySymbols(t).map(s => s.toString())
            };

            // Inspect internal fields
            if (t._core) termInfo.hasCore = true;
            if (t._terminal) termInfo.hasInternalTerminal = true;
            if (t._proxy) termInfo.hasProxy = true;
            if (t._id) termInfo.internalId = t._id;

            diagnostics.terminals.push(termInfo);
            outputChannel.appendLine(`[Terminal #${i}] Name: "${t.name}" | PID: ${pid} | IsActive: ${termInfo.isActive}`);
        }

        // STEP 5: Direct buffer access check on active terminal
        if (activeTerminal) {
            outputChannel.appendLine("\n--- Inspecting Direct Buffer Access on Extension Host ---");
            let xtermBuffer = null;
            if (activeTerminal._core && activeTerminal._core.buffer) {
                xtermBuffer = activeTerminal._core.buffer;
                diagnostics.directBufferAccess = true;
                diagnostics.directBufferDetails = "Found via activeTerminal._core.buffer";
            } else if (activeTerminal._terminal && activeTerminal._terminal._buffer) {
                xtermBuffer = activeTerminal._terminal._buffer;
                diagnostics.directBufferAccess = true;
                diagnostics.directBufferDetails = "Found via activeTerminal._terminal._buffer";
            } else {
                diagnostics.directBufferAccess = false;
                diagnostics.directBufferDetails = "No direct xterm.js instance in ExtensionHost (Running in separate Node.js process)";
                outputChannel.appendLine("Direct xterm.js Buffer: NOT directly exposed on extension host (expected: xterm.js is in Renderer process)");
            }
        }

        // STEP 6 & 7: Test Workbench Terminal Buffer Capture
        outputChannel.appendLine("\n--- Testing Workbench Buffer Extraction ---");
        try {
            // Focus and execute selectAll -> copySelection -> clearSelection
            await vscode.commands.executeCommand('workbench.action.terminal.selectAll');
            await new Promise(r => setTimeout(r, 80));
            await vscode.commands.executeCommand('workbench.action.terminal.copySelection');
            await new Promise(r => setTimeout(r, 80));
            await vscode.commands.executeCommand('workbench.action.terminal.clearSelection');

            const copiedText = await vscode.env.clipboard.readText();
            if (copiedText) {
                diagnostics.commandBufferAccess = true;
                diagnostics.capturedByteCount = Buffer.byteLength(copiedText, 'utf8');
                const lines = copiedText.split(/\r?\n/);
                diagnostics.capturedLineCount = lines.length;
                diagnostics.capturedBufferPreview = lines.slice(0, 10).join('\n') + "\n...\n" + lines.slice(-10).join('\n');

                outputChannel.appendLine(`Successfully retrieved buffer via Workbench Terminal Service:`);
                outputChannel.appendLine(`- Total Lines: ${lines.length}`);
                outputChannel.appendLine(`- Total Bytes: ${diagnostics.capturedByteCount} B`);

                // Check Historical Markers
                const historicalMarkers = [
                    "HISTORICAL_MARKER_AAAAAAAAA",
                    "HISTORICAL_MARKER_BBBBBBBBB",
                    "HISTORICAL_MARKER_CCCCCCCCC",
                    "HISTORY_LINE_1",
                    "HISTORY_LINE_200"
                ];

                for (const m of historicalMarkers) {
                    const found = copiedText.includes(m);
                    diagnostics.historicalMarkersFound[m] = found;
                    outputChannel.appendLine(`- Marker [${m}]: ${found ? "FOUND (PASS)" : "NOT FOUND (FAIL)"}`);
                }

                // Check Current Markers
                const currentMarkers = ["CURRENT_MARKER_123456"];
                for (const m of currentMarkers) {
                    const found = copiedText.includes(m);
                    diagnostics.currentMarkersFound[m] = found;
                    outputChannel.appendLine(`- Marker [${m}]: ${found ? "FOUND (PASS)" : "NOT FOUND (FAIL)"}`);
                }

                // Wrapped Line Analysis
                const sampleWrapped = lines.find(l => l.length > 80);
                diagnostics.wrappedLineAnalysis = {
                    hasLongLines: !!sampleWrapped,
                    sampleLength: sampleWrapped ? sampleWrapped.length : 0
                };
            } else {
                outputChannel.appendLine("Clipboard returned empty text after terminal.copySelection.");
            }
        } catch (cmdErr) {
            diagnostics.errors.push(cmdErr.message);
            outputChannel.appendLine(`Error executing terminal commands: ${cmdErr.message}`);
        }

        // Save diagnostic report to ~/.copyterm/poc_report.json
        try {
            const copytermDir = path.join(os.homedir(), '.copyterm');
            if (!fs.existsSync(copytermDir)) {
                fs.mkdirSync(copytermDir, { recursive: true });
            }
            const reportPath = path.join(copytermDir, 'poc_report.json');
            fs.writeFileSync(reportPath, JSON.stringify(diagnostics, null, 2), 'utf8');
            outputChannel.appendLine(`\nDiagnostic report saved to: ${reportPath}`);
        } catch (fsErr) {
            outputChannel.appendLine(`Failed to write diagnostic file: ${fsErr.message}`);
        }

        outputChannel.appendLine("============================================================");
        vscode.window.showInformationMessage(`CopyTerm POC Complete: Captured ${diagnostics.capturedLineCount} lines from active terminal.`);
    });

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
