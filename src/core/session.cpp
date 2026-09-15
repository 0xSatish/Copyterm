#include "session.hpp"
#include "../platform/environment.hpp"
#include "../platform/process.hpp"

#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>

namespace copyterm::core {

std::string backend_type_to_string(CaptureBackendType type) {
    switch (type) {
        case CaptureBackendType::ShellIntegration: return "shell_integration";
        case CaptureBackendType::Tmux: return "tmux";
        case CaptureBackendType::PtyWrapper: return "pty_wrapper";
        case CaptureBackendType::WindowsConsoleApi: return "windows_console_api";
        case CaptureBackendType::Unknown:
        default: return "unknown";
    }
}

CaptureBackendType string_to_backend_type(const std::string& s) {
    if (s == "shell_integration") return CaptureBackendType::ShellIntegration;
    if (s == "tmux") return CaptureBackendType::Tmux;
    if (s == "pty_wrapper") return CaptureBackendType::PtyWrapper;
    if (s == "windows_console_api") return CaptureBackendType::WindowsConsoleApi;
    return CaptureBackendType::Unknown;
}

std::string SessionMetadata::serialize() const {
    std::ostringstream oss;
    oss << "session_id=" << session_id << "\n";
    oss << "shell_name=" << shell_name << "\n";
    oss << "pid=" << pid << "\n";
    oss << "ppid=" << ppid << "\n";
    oss << "cwd=" << cwd << "\n";
    oss << "tty=" << tty << "\n";
    oss << "terminal_name=" << terminal_name << "\n";
    oss << "start_time_ms=" << start_time_ms << "\n";
    oss << "last_active_time_ms=" << last_active_time_ms << "\n";
    oss << "command_count=" << command_count << "\n";
    oss << "backend=" << backend_type_to_string(backend) << "\n";
    if (!tmux_pane.empty()) {
        oss << "tmux_pane=" << tmux_pane << "\n";
    }
    return oss.str();
}

std::optional<SessionMetadata> SessionMetadata::deserialize(const std::string& data) {
    SessionMetadata meta;
    std::istringstream iss(data);
    std::string line;
    bool has_id = false;

    while (std::getline(iss, line)) {
        // Strip carriage return if present
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        auto eq = line.find('=');
        if (eq == std::string::npos) continue;

        std::string key = line.substr(0, eq);
        std::string val = line.substr(eq + 1);

        if (key == "session_id") {
            meta.session_id = val;
            has_id = true;
        } else if (key == "shell_name") {
            meta.shell_name = val;
        } else if (key == "pid") {
            try { meta.pid = static_cast<uint32_t>(std::stoul(val)); } catch (...) {}
        } else if (key == "ppid") {
            try { meta.ppid = static_cast<uint32_t>(std::stoul(val)); } catch (...) {}
        } else if (key == "cwd") {
            meta.cwd = val;
        } else if (key == "tty") {
            meta.tty = val;
        } else if (key == "terminal_name") {
            meta.terminal_name = val;
        } else if (key == "start_time_ms") {
            try { meta.start_time_ms = std::stoull(val); } catch (...) {}
        } else if (key == "last_active_time_ms") {
            try { meta.last_active_time_ms = std::stoull(val); } catch (...) {}
        } else if (key == "command_count") {
            try { meta.command_count = static_cast<uint32_t>(std::stoul(val)); } catch (...) {}
        } else if (key == "backend") {
            meta.backend = string_to_backend_type(val);
        } else if (key == "tmux_pane") {
            meta.tmux_pane = val;
        }
    }

    if (has_id && !meta.session_id.empty()) {
        return meta;
    }
    return std::nullopt;
}

Session::Session(SessionMetadata meta) : metadata_(std::move(meta)) {}

std::filesystem::path Session::get_buffer_path() const {
    return platform::Environment::get_sessions_dir() / (metadata_.session_id + ".buf");
}

std::filesystem::path Session::get_metadata_path() const {
    return platform::Environment::get_sessions_dir() / (metadata_.session_id + ".meta");
}

bool Session::save_metadata() const {
    platform::Environment::ensure_directory(platform::Environment::get_sessions_dir());
    std::filesystem::path meta_path = get_metadata_path();
    std::ofstream out(meta_path, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        return false;
    }
    out << metadata_.serialize();
    return true;
}

void Session::touch() {
    metadata_.last_active_time_ms = platform::Environment::get_current_time_ms();
    save_metadata();
}

void Session::increment_command_count() {
    metadata_.command_count++;
    metadata_.last_active_time_ms = platform::Environment::get_current_time_ms();
    save_metadata();
}

bool Session::is_process_alive() const {
    if (metadata_.pid == 0) return false;
    return platform::Process::is_process_alive(metadata_.pid);
}

std::string SessionManager::generate_session_id(uint32_t pid) {
    uint64_t ts = platform::Environment::get_current_time_ms();
    std::string rand_token = platform::Environment::generate_random_hex(6);
    return "sess_" + std::to_string(ts) + "_" + std::to_string(pid) + "_" + rand_token;
}

Session SessionManager::create_session(const std::string& shell_name, uint32_t pid, CaptureBackendType backend) {
    if (pid == 0) {
        pid = platform::Process::get_parent_pid();
        if (pid == 0) {
            pid = platform::Process::get_current_pid();
        }
    }

    SessionMetadata meta;
    meta.session_id = generate_session_id(pid);
    meta.shell_name = shell_name.empty() ? platform::Process::detect_shell_name() : shell_name;
    meta.pid = pid;
    meta.ppid = platform::Process::get_parent_pid(pid);
    meta.cwd = platform::Environment::get_current_working_dir().string();
    meta.tty = platform::Process::detect_tty_device();
    meta.terminal_name = platform::Process::detect_terminal_emulator();
    meta.start_time_ms = platform::Environment::get_current_time_ms();
    meta.last_active_time_ms = meta.start_time_ms;
    meta.command_count = 0;
    meta.backend = backend;

    auto tmux_pane = platform::Environment::get_env("TMUX_PANE");
    if (tmux_pane) {
        meta.tmux_pane = *tmux_pane;
        meta.backend = CaptureBackendType::Tmux;
    }

    Session session(meta);
    session.save_metadata();
    return session;
}

std::optional<Session> SessionResolver::resolve_by_id(const std::string& session_id) {
    if (session_id.empty()) {
        return std::nullopt;
    }

    std::filesystem::path meta_path = platform::Environment::get_sessions_dir() / (session_id + ".meta");
    if (std::filesystem::exists(meta_path)) {
        std::ifstream in(meta_path);
        if (in.is_open()) {
            std::string content((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
            auto meta = SessionMetadata::deserialize(content);
            if (meta) {
                return Session(*meta);
            }
        }
    }

    // If meta is absent, construct a session instance with this ID
    SessionMetadata meta;
    meta.session_id = session_id;
    meta.shell_name = platform::Process::detect_shell_name();
    meta.cwd = platform::Environment::get_current_working_dir().string();
    meta.start_time_ms = platform::Environment::get_current_time_ms();
    meta.last_active_time_ms = meta.start_time_ms;
    return Session(meta);
}

std::optional<Session> SessionResolver::resolve_current_session() {
    // 1. Check environment variable COPYTERM_SESSION_ID
    auto env_id = platform::Environment::get_env("COPYTERM_SESSION_ID");
    if (env_id && !env_id->empty()) {
        auto sess = resolve_by_id(*env_id);
        if (sess) {
            return sess;
        }
        // If meta file was missing, recreate session with this ID
        SessionMetadata meta;
        meta.session_id = *env_id;
        meta.shell_name = platform::Process::detect_shell_name();
        meta.pid = platform::Process::get_parent_pid();
        meta.ppid = platform::Process::get_parent_pid(meta.pid);
        meta.cwd = platform::Environment::get_current_working_dir().string();
        meta.tty = platform::Process::detect_tty_device();
        meta.terminal_name = platform::Process::detect_terminal_emulator();
        meta.start_time_ms = platform::Environment::get_current_time_ms();
        meta.last_active_time_ms = meta.start_time_ms;
        Session session(meta);
        session.save_metadata();
        return session;
    }

    // 2. Check if running inside tmux
    auto tmux_pane = platform::Environment::get_env("TMUX_PANE");
    auto tmux_env = platform::Environment::get_env("TMUX");
    if (tmux_pane && !tmux_pane->empty() && tmux_env) {
        std::string tmux_session_id = "tmux_pane_" + *tmux_pane;
        // Clean up invalid chars in filename
        std::replace(tmux_session_id.begin(), tmux_session_id.end(), '%', '_');
        auto sess = resolve_by_id(tmux_session_id);
        if (sess) return sess;

        SessionMetadata meta;
        meta.session_id = tmux_session_id;
        meta.shell_name = platform::Process::detect_shell_name();
        meta.pid = platform::Process::get_parent_pid();
        meta.ppid = platform::Process::get_parent_pid(meta.pid);
        meta.cwd = platform::Environment::get_current_working_dir().string();
        meta.tty = platform::Process::detect_tty_device();
        meta.terminal_name = "tmux";
        meta.start_time_ms = platform::Environment::get_current_time_ms();
        meta.last_active_time_ms = meta.start_time_ms;
        meta.backend = CaptureBackendType::Tmux;
        meta.tmux_pane = *tmux_pane;
        Session session(meta);
        session.save_metadata();
        return session;
    }

    // 3. Process tree matching: Check if any ancestor process PID has an active session
    auto ancestors = platform::Process::get_process_ancestors();
    auto all_sessions = SessionManager::list_all_sessions();

    for (const auto& ancestor : ancestors) {
        for (const auto& sess : all_sessions) {
            if (sess.get_metadata().pid == ancestor.pid) {
                return sess;
            }
        }
    }

    return std::nullopt;
}

std::vector<Session> SessionManager::list_all_sessions() {
    std::vector<Session> sessions;
    auto sessions_dir = platform::Environment::get_sessions_dir();
    if (!std::filesystem::exists(sessions_dir)) {
        return sessions;
    }

    try {
        for (const auto& entry : std::filesystem::directory_iterator(sessions_dir)) {
            if (entry.is_regular_file() && entry.path().extension() == ".meta") {
                std::ifstream in(entry.path());
                if (in.is_open()) {
                    std::string content((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
                    auto meta = SessionMetadata::deserialize(content);
                    if (meta) {
                        sessions.emplace_back(*meta);
                    }
                }
            }
        }
    } catch (...) {}

    // Sort by start_time_ms descending
    std::sort(sessions.begin(), sessions.end(), [](const Session& a, const Session& b) {
        return a.get_metadata().start_time_ms > b.get_metadata().start_time_ms;
    });

    return sessions;
}

size_t SessionManager::clean_stale_sessions(uint64_t max_age_ms) {
    size_t cleaned_count = 0;
    auto all_sessions = list_all_sessions();
    uint64_t now = platform::Environment::get_current_time_ms();

    for (const auto& sess : all_sessions) {
        bool is_stale = false;
        
        // If process PID is no longer alive, it's stale
        if (!sess.is_process_alive()) {
            is_stale = true;
        }

        // If older than max_age_ms, it's stale
        if (now > sess.get_metadata().last_active_time_ms &&
            (now - sess.get_metadata().last_active_time_ms) > max_age_ms) {
            is_stale = true;
        }

        if (is_stale) {
            if (delete_session(sess.get_id())) {
                cleaned_count++;
            }
        }
    }

    return cleaned_count;
}

bool SessionManager::delete_session(const std::string& session_id) {
    bool ok = true;
    auto meta_path = platform::Environment::get_sessions_dir() / (session_id + ".meta");
    auto buf_path = platform::Environment::get_sessions_dir() / (session_id + ".buf");

    try {
        if (std::filesystem::exists(meta_path)) {
            std::filesystem::remove(meta_path);
        }
    } catch (...) { ok = false; }

    try {
        if (std::filesystem::exists(buf_path)) {
            std::filesystem::remove(buf_path);
        }
    } catch (...) { ok = false; }

    return ok;
}

} // namespace copyterm::core
