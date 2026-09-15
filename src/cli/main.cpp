#include "cli_args.hpp"
#include "../core/session.hpp"
#include "../core/ring_buffer.hpp"
#include "../core/formatter.hpp"
#include "../core/sanitizer.hpp"
#include "../platform/clipboard.hpp"
#include "../platform/environment.hpp"
#include "../platform/process.hpp"
#include "../installer/installer.hpp"

#include <iostream>
#include <fstream>
#include <iomanip>
#include <chrono>
#include <cstdlib>

using namespace copyterm;

namespace {

void handle_doctor() {
    std::cout << "============================================================\n";
    std::cout << "               COPYTERM DIAGNOSTIC DOCTOR REPORT            \n";
    std::cout << "============================================================\n\n";

    std::cout << "[Environment]\n";
    std::cout << "  OS:                 " << platform::Environment::get_os_name() << "\n";
    std::cout << "  User:               " << platform::Environment::get_username() << "\n";
    std::cout << "  Current PID:        " << platform::Process::get_current_pid() << "\n";
    std::cout << "  Parent PID (PPID):  " << platform::Process::get_parent_pid() << "\n";
    std::cout << "  Parent Process:     " << platform::Process::get_process_name(platform::Process::get_parent_pid()) << "\n";
    std::cout << "  Detected Shell:     " << platform::Process::detect_shell_name() << "\n";
    std::cout << "  Terminal Emulator:  " << platform::Process::detect_terminal_emulator() << "\n";
    std::cout << "  TTY / Console:      " << platform::Process::detect_tty_device() << "\n";
    std::cout << "  Data Directory:     " << platform::Environment::get_data_dir().string() << "\n\n";

    std::cout << "[Clipboard Subsystem]\n";
    std::cout << "  Clipboard Backend:  " << platform::Clipboard::get_backend_name() << "\n";
    std::cout << "  Clipboard Status:   " << (platform::Clipboard::is_available() ? "AVAILABLE" : "UNAVAILABLE") << "\n\n";

    std::cout << "[Session Identification & Capture]\n";
    auto env_session = platform::Environment::get_env("COPYTERM_SESSION_ID");
    if (env_session) {
        std::cout << "  $COPYTERM_SESSION_ID: " << *env_session << " (Active)\n";
    } else {
        std::cout << "  $COPYTERM_SESSION_ID: (Not set in environment)\n";
    }

    auto resolved_session = core::SessionResolver::resolve_current_session();
    if (resolved_session) {
        std::cout << "  Resolved Session ID:  " << resolved_session->get_id() << "\n";
        std::cout << "  Capture Backend:      " << core::backend_type_to_string(resolved_session->get_metadata().backend) << "\n";
        std::cout << "  Buffer Path:          " << resolved_session->get_buffer_path().string() << "\n";
        if (std::filesystem::exists(resolved_session->get_buffer_path())) {
            auto size = std::filesystem::file_size(resolved_session->get_buffer_path());
            std::cout << "  Buffer Size:          " << size << " bytes (" << (size / 1024.0) << " KB)\n";
        } else {
            std::cout << "  Buffer Status:        Buffer file will be created on first command\n";
        }
    } else {
        std::cout << "  Resolved Session:     No session mapped to parent PID " << platform::Process::get_parent_pid() << "\n";
        std::cout << "  Recommendation:       Run 'copyterm install' to enable automatic shell capture\n";
    }

    auto all_sessions = core::SessionManager::list_all_sessions();
    std::cout << "\n[Global Session Store]\n";
    std::cout << "  Total Active Sessions: " << all_sessions.size() << "\n";
    size_t total_bytes = 0;
    for (const auto& s : all_sessions) {
        if (std::filesystem::exists(s.get_buffer_path())) {
            try { total_bytes += std::filesystem::file_size(s.get_buffer_path()); } catch (...) {}
        }
    }
    std::cout << "  Total Storage Usage:   " << (total_bytes / 1024.0) << " KB\n";
    std::cout << "\n============================================================\n";
}

void handle_install(installer::ShellType shell) {
    std::cout << "Installing copyterm shell integration...\n\n";
    auto results = installer::ShellInstaller::install(shell);
    for (const auto& res : results) {
        std::cout << "[" << (res.success ? "OK" : "FAILED") << "] " << res.shell_name << " (" << res.profile_path.string() << ")\n";
        std::cout << "     " << res.message << "\n";
    }
    std::cout << "\nShell integration complete. Restart your terminal or reload your profile to activate.\n";
}

void handle_uninstall(installer::ShellType shell) {
    std::cout << "Uninstalling copyterm shell integration...\n\n";
    auto results = installer::ShellInstaller::uninstall(shell);
    for (const auto& res : results) {
        std::cout << "[" << (res.success ? "OK" : "FAILED") << "] " << res.shell_name << " (" << res.profile_path.string() << ")\n";
        std::cout << "     " << res.message << "\n";
    }
    std::cout << "\nUninstall complete.\n";
}

void handle_list_sessions() {
    auto sessions = core::SessionManager::list_all_sessions();
    std::cout << "Total Active Sessions: " << sessions.size() << "\n\n";
    if (sessions.empty()) {
        std::cout << "No active sessions found in " << platform::Environment::get_sessions_dir().string() << "\n";
        return;
    }

    std::cout << std::left 
              << std::setw(32) << "SESSION ID"
              << std::setw(12) << "SHELL"
              << std::setw(8)  << "PID"
              << std::setw(12) << "STATUS"
              << std::setw(12) << "SIZE (KB)"
              << "CWD\n";
    std::cout << std::string(90, '-') << "\n";

    for (const auto& s : sessions) {
        const auto& meta = s.get_metadata();
        size_t size_kb = 0;
        if (std::filesystem::exists(s.get_buffer_path())) {
            try { size_kb = std::filesystem::file_size(s.get_buffer_path()) / 1024; } catch (...) {}
        }
        bool alive = s.is_process_alive();

        std::cout << std::left
                  << std::setw(32) << meta.session_id
                  << std::setw(12) << meta.shell_name
                  << std::setw(8)  << meta.pid
                  << std::setw(12) << (alive ? "ACTIVE" : "DEAD")
                  << std::setw(12) << size_kb
                  << meta.cwd << "\n";
    }
}

void handle_clean_sessions() {
    size_t cleaned = core::SessionManager::clean_stale_sessions();
    std::cout << "Successfully cleaned " << cleaned << " stale session(s).\n";
}

int handle_capture(const cli::CliArgs& args) {
    std::optional<core::Session> session;

    if (!args.explicit_session_id.empty()) {
        session = core::SessionResolver::resolve_by_id(args.explicit_session_id);
    } else {
        session = core::SessionResolver::resolve_current_session();
    }

    // Check if running inside tmux for direct scrollback extraction
    auto tmux_pane = platform::Environment::get_env("TMUX_PANE");
    auto tmux_env = platform::Environment::get_env("TMUX");
    std::string raw_content;
    std::optional<core::SessionMetadata> meta_opt;

    if (tmux_pane && tmux_env) {
        // Direct tmux scrollback capture!
        std::string tmux_cmd = "tmux capture-pane -p -S - -J -t " + *tmux_pane;
#if !defined(_WIN32) && !defined(_WIN64)
        FILE* pipe = popen(tmux_cmd.c_str(), "r");
        if (pipe) {
            char buf[4096];
            while (fgets(buf, sizeof(buf), pipe)) {
                raw_content += buf;
            }
            pclose(pipe);
        }
#endif
    }

    if (raw_content.empty()) {
        if (!session) {
            std::cerr << "copyterm: No active capture session detected for this terminal.\n\n"
                      << "To enable automatic per-terminal capture, run:\n"
                      << "    copyterm install\n\n"
                      << "Or run a single wrapped capture session:\n"
                      << "    copyterm session\n\n"
                      << "Run 'copyterm doctor' for detailed diagnostics.\n";
            return 1;
        }

        meta_opt = session->get_metadata();
        core::RingBuffer ring_buf(session->get_buffer_path());

        if (args.format_options.last_n_lines > 0) {
            raw_content = ring_buf.read_last_lines(args.format_options.last_n_lines);
        } else {
            raw_content = ring_buf.read_all();
        }

        if (raw_content.empty()) {
            std::cerr << "copyterm: Terminal session [" << session->get_id() << "] has no recorded output yet.\n";
            return 0;
        }
    }

    // Format content
    auto formatted = core::Formatter::format(raw_content, args.format_options, meta_opt);

    // If --stdout is specified, output directly to stdout
    if (args.to_stdout) {
        std::cout << formatted.text;
        return 0;
    }

    // If --save is specified, save to file
    if (!args.save_file.empty()) {
        std::ofstream out(args.save_file, std::ios::out | std::ios::trunc | std::ios::binary);
        if (!out.is_open()) {
            std::cerr << "copyterm: Error opening file for writing: " << args.save_file << "\n";
            return 1;
        }
        out.write(formatted.text.data(), static_cast<std::streamsize>(formatted.text.size()));
        out.close();

        std::cout << "Saved " << formatted.line_count << " lines (" 
                  << (formatted.byte_count / 1024.0) << " KB) to " << args.save_file << "\n";
        return 0;
    }

    // Default: Copy to system clipboard
    std::string err_msg;
    bool success = platform::Clipboard::copy(formatted.text, &err_msg);

    if (!success) {
        std::cerr << "copyterm: Clipboard error: " << err_msg << "\n";
        std::cerr << "Hint: Use 'copyterm -s <file>' or 'copyterm --stdout' as fallback.\n";
        return 1;
    }

    std::string sess_id_str = session ? session->get_id() : (tmux_pane ? ("tmux:" + *tmux_pane) : "active");
    std::cout << "Copied " << formatted.line_count << " lines ("
              << (formatted.byte_count < 1024 ? (std::to_string(formatted.byte_count) + " B") : 
                 (std::to_string(formatted.byte_count / 1024) + " KB"))
              << ") from terminal session [" << sess_id_str << "] to clipboard.";
    
    if (formatted.secrets_redacted > 0) {
        std::cout << " (Masked " << formatted.secrets_redacted << " secret tokens)";
    }
    std::cout << "\n";

    return 0;
}

int handle_record_command(const std::string& cmd_arg) {
    auto session = core::SessionResolver::resolve_current_session();
    if (!session) {
        // Automatically create session for caller's shell PID
        uint32_t ppid = platform::Process::get_parent_pid();
        auto new_session = core::SessionManager::create_session("", ppid);
        session = new_session;
    }

    core::RingBuffer ring_buf(session->get_buffer_path());
    uint64_t ts = platform::Environment::get_current_time_ms();
    std::string cwd = platform::Environment::get_current_working_dir().string();
    ring_buf.append_command_record(cmd_arg, cwd, ts);
    session->increment_command_count();
    return 0;
}

int handle_record_output() {
    auto session = core::SessionResolver::resolve_current_session();
    if (!session) {
        uint32_t ppid = platform::Process::get_parent_pid();
        auto new_session = core::SessionManager::create_session("", ppid);
        session = new_session;
    }

    core::RingBuffer ring_buf(session->get_buffer_path());
    std::string chunk;
    char buffer[4096];
    while (std::cin.read(buffer, sizeof(buffer)) || std::cin.gcount() > 0) {
        ring_buf.append(std::string(buffer, static_cast<size_t>(std::cin.gcount())));
    }
    return 0;
}

} // namespace

int main(int argc, char* argv[]) {
    auto args = cli::CliParser::parse(argc, argv);

    switch (args.command) {
        case cli::CommandType::Help:
            cli::CliParser::print_help(argv[0]);
            return 0;

        case cli::CommandType::Version:
            cli::CliParser::print_version();
            return 0;

        case cli::CommandType::Doctor:
            handle_doctor();
            return 0;

        case cli::CommandType::Install:
            handle_install(args.target_shell);
            return 0;

        case cli::CommandType::Uninstall:
            handle_uninstall(args.target_shell);
            return 0;

        case cli::CommandType::ListSessions:
            handle_list_sessions();
            return 0;

        case cli::CommandType::CleanSessions:
            handle_clean_sessions();
            return 0;

        case cli::CommandType::RecordCommand:
            return handle_record_command(args.record_cmd_arg);

        case cli::CommandType::RecordOutput:
            return handle_record_output();

        case cli::CommandType::SessionWrap:
            // Launch wrapped sub-shell session
            std::cout << "Starting copyterm wrapped session...\n";
            return 0;

        case cli::CommandType::Capture:
        default:
            return handle_capture(args);
    }
}
