#pragma once

#include <string>
#include <filesystem>
#include <optional>
#include <vector>
#include <cstdint>

namespace copyterm::core {

enum class CaptureBackendType {
    ShellIntegration,
    Tmux,
    PtyWrapper,
    WindowsConsoleApi,
    Unknown
};

std::string backend_type_to_string(CaptureBackendType type);
CaptureBackendType string_to_backend_type(const std::string& s);

struct SessionMetadata {
    std::string session_id;
    std::string shell_name;
    uint32_t pid{0};
    uint32_t ppid{0};
    std::string cwd;
    std::string tty;
    std::string terminal_name;
    uint64_t start_time_ms{0};
    uint64_t last_active_time_ms{0};
    uint32_t command_count{0};
    CaptureBackendType backend{CaptureBackendType::ShellIntegration};
    std::string tmux_pane;

    std::string serialize() const;
    static std::optional<SessionMetadata> deserialize(const std::string& data);
};

class Session {
public:
    Session() = default;
    explicit Session(SessionMetadata meta);

    const SessionMetadata& get_metadata() const { return metadata_; }
    SessionMetadata& get_metadata() { return metadata_; }
    const std::string& get_id() const { return metadata_.session_id; }

    std::filesystem::path get_buffer_path() const;
    std::filesystem::path get_metadata_path() const;

    bool save_metadata() const;
    void touch();
    void increment_command_count();

    bool is_valid() const { return !metadata_.session_id.empty(); }
    bool is_process_alive() const;

private:
    SessionMetadata metadata_;
};

class SessionResolver {
public:
    // Resolves the active session for the calling process using the multi-tier hierarchy
    static std::optional<Session> resolve_current_session();

    // Resolves a session by explicit ID
    static std::optional<Session> resolve_by_id(const std::string& session_id);
};

class SessionManager {
public:
    // Creates and initializes a new session
    static Session create_session(const std::string& shell_name = "", uint32_t pid = 0, CaptureBackendType backend = CaptureBackendType::ShellIntegration);

    // Lists all stored sessions
    static std::vector<Session> list_all_sessions();

    // Cleans up stale sessions whose parent process has died or are older than max_age_ms
    static size_t clean_stale_sessions(uint64_t max_age_ms = 86400000ULL); // 24 hours default

    // Deletes a specific session files
    static bool delete_session(const std::string& session_id);

    // Generates a new unique session ID
    static std::string generate_session_id(uint32_t pid);
};

} // namespace copyterm::core
