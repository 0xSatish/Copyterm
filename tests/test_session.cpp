#include "../src/core/session.hpp"
#include "../src/platform/environment.hpp"
#include "../src/platform/process.hpp"

#include <cassert>
#include <iostream>
#include <stdexcept>

void run_session_tests() {
    using namespace copyterm;

    // 1. Test Session ID generation
    uint32_t pid = 12345;
    std::string sess_id1 = core::SessionManager::generate_session_id(pid);
    std::string sess_id2 = core::SessionManager::generate_session_id(pid);

    if (sess_id1.empty() || sess_id1.find("sess_") != 0) {
        throw std::runtime_error("Session ID format invalid: " + sess_id1);
    }
    if (sess_id1 == sess_id2) {
        throw std::runtime_error("Session IDs must be unique even for same PID");
    }

    // 2. Test SessionMetadata serialization & deserialization
    core::SessionMetadata meta;
    meta.session_id = sess_id1;
    meta.shell_name = "powershell";
    meta.pid = 12345;
    meta.ppid = 1000;
    meta.cwd = "C:/test/path";
    meta.tty = "console_0";
    meta.terminal_name = "Windows Terminal";
    meta.start_time_ms = 1700000000000ULL;
    meta.last_active_time_ms = 1700000001000ULL;
    meta.command_count = 5;
    meta.backend = core::CaptureBackendType::ShellIntegration;

    std::string serialized = meta.serialize();
    auto deserialized = core::SessionMetadata::deserialize(serialized);

    if (!deserialized) {
        throw std::runtime_error("Failed to deserialize SessionMetadata");
    }
    if (deserialized->session_id != meta.session_id) {
        throw std::runtime_error("Deserialized session_id mismatch");
    }
    if (deserialized->shell_name != meta.shell_name) {
        throw std::runtime_error("Deserialized shell_name mismatch");
    }
    if (deserialized->pid != meta.pid || deserialized->ppid != meta.ppid) {
        throw std::runtime_error("Deserialized PID/PPID mismatch");
    }
    if (deserialized->backend != meta.backend) {
        throw std::runtime_error("Deserialized backend mismatch");
    }

    // 3. Test Session creation and file persistence
    core::Session session(meta);
    if (!session.save_metadata()) {
        throw std::runtime_error("Failed to save session metadata file");
    }

    auto resolved = core::SessionResolver::resolve_by_id(sess_id1);
    if (!resolved) {
        throw std::runtime_error("Failed to resolve session by ID after save");
    }
    if (resolved->get_metadata().cwd != meta.cwd) {
        throw std::runtime_error("Resolved session metadata field mismatch");
    }

    // Clean up test session
    core::SessionManager::delete_session(sess_id1);
}
