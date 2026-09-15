#pragma once

#include <string>
#include <vector>
#include <optional>
#include "../core/formatter.hpp"
#include "../installer/installer.hpp"

namespace copyterm::cli {

enum class CommandType {
    Capture,        // Default: capture & copy
    Doctor,         // Diagnostic doctor check
    Install,        // Install shell integration
    Uninstall,      // Uninstall shell integration
    ListSessions,   // List active sessions
    CleanSessions,  // Clean stale sessions
    SessionWrap,    // Run wrapped command
    RecordCommand,  // Internal helper for hooks
    RecordOutput,   // Internal helper for hooks
    Help,           // Show help
    Version         // Show version
};

struct CliArgs {
    CommandType command{CommandType::Capture};
    core::FormatterOptions format_options;
    std::string save_file;
    bool to_stdout{false};
    std::string explicit_session_id;
    installer::ShellType target_shell{installer::ShellType::All};
    std::vector<std::string> wrapped_command;
    std::string record_cmd_arg;
};

class CliParser {
public:
    static CliArgs parse(int argc, char* argv[]);
    static void print_help(const char* prog_name);
    static void print_version();
};

} // namespace copyterm::cli
