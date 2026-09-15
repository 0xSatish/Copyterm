#include "../src/core/formatter.hpp"
#include "../src/core/session.hpp"

#include <iostream>
#include <stdexcept>

void run_formatter_tests() {
    using namespace copyterm;

    std::string raw_session = 
        "$ pwd\n"
        "/home/user/project\n"
        "$ git status\n"
        "On branch main\n"
        "nothing to commit\n"
        "$ make\n"
        "\x1b[32mBuild complete.\x1b[0m\n";

    core::SessionMetadata meta;
    meta.session_id = "sess_test_123";
    meta.shell_name = "bash";
    meta.cwd = "/home/user/project";
    meta.terminal_name = "GNOME Terminal";

    // 1. Test Clean Mode (default)
    core::FormatterOptions opts_clean;
    opts_clean.mode = core::OutputMode::Clean;
    auto res_clean = core::Formatter::format(raw_session, opts_clean, meta);

    if (res_clean.text.find("\x1b[32m") != std::string::npos) {
        throw std::runtime_error("Clean mode failed to strip ANSI escape codes");
    }
    if (res_clean.text.find("Build complete.") == std::string::npos) {
        throw std::runtime_error("Clean mode stripped actual text content");
    }

    // 2. Test Raw Mode
    core::FormatterOptions opts_raw;
    opts_raw.mode = core::OutputMode::Raw;
    auto res_raw = core::Formatter::format(raw_session, opts_raw, meta);

    if (res_raw.text.find("\x1b[32m") == std::string::npos) {
        throw std::runtime_error("Raw mode failed to preserve ANSI sequences");
    }

    // 3. Test AI Markdown Mode
    core::FormatterOptions opts_ai;
    opts_ai.mode = core::OutputMode::AiMarkdown;
    auto res_ai = core::Formatter::format(raw_session, opts_ai, meta);

    if (res_ai.text.find("```bash") == std::string::npos ||
        res_ai.text.find("/home/user/project") == std::string::npos) {
        throw std::runtime_error("AI mode output missing Markdown formatting / metadata");
    }

    // 4. Test Commands-Only Mode
    core::FormatterOptions opts_cmd;
    opts_cmd.mode = core::OutputMode::CommandsOnly;
    auto res_cmd = core::Formatter::format(raw_session, opts_cmd, meta);

    if (res_cmd.text.find("$ pwd") == std::string::npos ||
        res_cmd.text.find("$ make") == std::string::npos) {
        throw std::runtime_error("Commands-only mode missing command lines");
    }
    if (res_cmd.text.find("nothing to commit") != std::string::npos) {
        throw std::runtime_error("Commands-only mode included output text");
    }

    // 5. Test Output-Only Mode
    core::FormatterOptions opts_out;
    opts_out.mode = core::OutputMode::OutputOnly;
    auto res_out = core::Formatter::format(raw_session, opts_out, meta);

    if (res_out.text.find("nothing to commit") == std::string::npos) {
        throw std::runtime_error("Output-only mode missing output text");
    }
    if (res_out.text.find("$ git status") != std::string::npos) {
        throw std::runtime_error("Output-only mode included prompt line");
    }

    // 6. Test Last N Lines Filter
    core::FormatterOptions opts_last;
    opts_last.mode = core::OutputMode::Clean;
    opts_last.last_n_lines = 2;
    auto res_last = core::Formatter::format(raw_session, opts_last, meta);

    if (res_last.line_count != 2) {
        throw std::runtime_error("Last N lines mode returned incorrect line count: " + std::to_string(res_last.line_count));
    }
}
