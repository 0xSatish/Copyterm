#include "cli_args.hpp"

#include <iostream>
#include <iomanip>
#include <cstring>

namespace copyterm::cli {

namespace {
const char* COPYTERM_VERSION = "1.1.0";
}

void CliParser::print_version() {
    std::cout << "cpt (CopyTerm) version " << COPYTERM_VERSION << " (cross-platform terminal session capture)\n";
}

void CliParser::print_help(const char* prog_name) {
    std::cout << R"(
COPYTERM (cpt) — End-to-End Cross-Platform Terminal Session Capture Utility

USAGE:
    cpt [OPTIONS]
    cpt <SUBCOMMAND> [OPTIONS]
    copyterm [OPTIONS]

DESCRIPTION:
    Copies the useful terminal session output for the CURRENT terminal
    directly into your system clipboard with strict per-session isolation.

SUBCOMMANDS:
    doctor                     Run environment & terminal diagnostics
    install [shell]            Install shell integration (powershell, bash, zsh, cmd, all)
    uninstall [shell]          Uninstall shell integration cleanly
    list                       List all active terminal sessions
    clean-sessions             Purge stale and terminated session buffers
    session [cmd...]           Launch a new PTY-wrapped capture session

CAPTURE OPTIONS:
    -n, --last <N>             Copy only the last N lines of output
    --clean                    Strip ANSI escapes & normalize carriage returns (default)
    --raw                      Preserve exact raw ANSI/VT escape sequences
    --ai                       Format output as Markdown with terminal execution context
    --redact                   Mask sensitive credentials (AWS keys, GitHub tokens, JWTs)
    --commands-only            Extract only user-entered commands
    --output-only              Extract only command outputs without prompts
    -s, --save <path>          Save captured output directly to a file
    --stdout                   Print captured content directly to stdout (for piping)
    --session-id <id>          Override session ID for manual retrieval

GENERAL OPTIONS:
    -h, --help                 Print this help information
    -v, --version              Print version information

EXAMPLES:
    copyterm                   # Copy current terminal session to clipboard
    copyterm --last 50         # Copy the last 50 lines to clipboard
    copyterm --ai              # Copy formatted markdown for pasting into AI/LLM
    copyterm --redact          # Copy with API keys & credentials masked
    copyterm -s session.txt    # Save session output directly to file
    copyterm --stdout | grep ERROR
    copyterm install powershell
    copyterm doctor
)";
}

CliArgs CliParser::parse(int argc, char* argv[]) {
    CliArgs args;

    if (argc <= 1) {
        return args;
    }

    int i = 1;
    while (i < argc) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help" || arg == "help") {
            args.command = CommandType::Help;
            return args;
        } else if (arg == "-v" || arg == "--version" || arg == "version") {
            args.command = CommandType::Version;
            return args;
        } else if (arg == "doctor" || arg == "--doctor") {
            args.command = CommandType::Doctor;
        } else if (arg == "install") {
            args.command = CommandType::Install;
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                args.target_shell = installer::ShellInstaller::parse_shell_type(argv[++i]);
            }
        } else if (arg == "uninstall") {
            args.command = CommandType::Uninstall;
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                args.target_shell = installer::ShellInstaller::parse_shell_type(argv[++i]);
            }
        } else if (arg == "list" || arg == "ls") {
            args.command = CommandType::ListSessions;
        } else if (arg == "clean-sessions" || arg == "clean") {
            args.command = CommandType::CleanSessions;
        } else if (arg == "session" || arg == "wrap") {
            args.command = CommandType::SessionWrap;
            while (++i < argc) {
                args.wrapped_command.push_back(argv[i]);
            }
            return args;
        } else if (arg == "record-command") {
            args.command = CommandType::RecordCommand;
            while (++i < argc) {
                if (!args.record_cmd_arg.empty()) args.record_cmd_arg += " ";
                args.record_cmd_arg += argv[i];
            }
            return args;
        } else if (arg == "record-output") {
            args.command = CommandType::RecordOutput;
        } else if (arg == "-n" || arg == "--last") {
            if (i + 1 < argc) {
                try {
                    args.format_options.last_n_lines = static_cast<size_t>(std::stoul(argv[++i]));
                } catch (...) {}
            }
        } else if (arg == "--clean") {
            args.format_options.mode = core::OutputMode::Clean;
        } else if (arg == "--raw") {
            args.format_options.mode = core::OutputMode::Raw;
        } else if (arg == "--ai") {
            args.format_options.mode = core::OutputMode::AiMarkdown;
        } else if (arg == "--commands-only") {
            args.format_options.mode = core::OutputMode::CommandsOnly;
        } else if (arg == "--output-only") {
            args.format_options.mode = core::OutputMode::OutputOnly;
        } else if (arg == "--redact") {
            args.format_options.redact_secrets = true;
        } else if (arg == "-s" || arg == "--save") {
            if (i + 1 < argc) {
                args.save_file = argv[++i];
            }
        } else if (arg == "--stdout") {
            args.to_stdout = true;
        } else if (arg == "--session-id") {
            if (i + 1 < argc) {
                args.explicit_session_id = argv[++i];
            }
        }

        i++;
    }

    return args;
}

} // namespace copyterm::cli
