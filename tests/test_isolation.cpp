#include "../src/core/session.hpp"
#include "../src/core/ring_buffer.hpp"
#include "../src/core/formatter.hpp"
#include "../src/platform/environment.hpp"

#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <stdexcept>
#include <thread>

void run_isolation_tests() {
    using namespace copyterm;

    const size_t NUM_TERMINALS = 30;
    std::vector<core::Session> sessions;
    sessions.reserve(NUM_TERMINALS);

    // 1. Create 30 independent terminal sessions with distinct PIDs
    for (size_t i = 1; i <= NUM_TERMINALS; ++i) {
        uint32_t simulated_pid = static_cast<uint32_t>(20000 + i);
        auto session = core::SessionManager::create_session("powershell", simulated_pid);
        sessions.push_back(session);

        // Append unique session marker and commands to this terminal's buffer
        core::RingBuffer ring_buf(session.get_buffer_path());
        ring_buf.clear();

        std::string marker = "TERMINAL_SESSION_MARKER_" + std::to_string(i) + "_UNIQUE_DATA";
        ring_buf.append_command_record("echo \"" + marker + "\"", "C:/projects/term_" + std::to_string(i), 1700000000000ULL + i);
        ring_buf.append(marker + "\n");
        ring_buf.append("Command completed successfully for terminal " + std::to_string(i) + "\n");
    }

    // 2. High-Volume Asymmetric Stress Test:
    // Terminal #1 produces 10,000 lines of heavy output
    {
        core::RingBuffer term1_buf(sessions[0].get_buffer_path());
        std::ostringstream heavy_stream;
        for (int line = 1; line <= 10000; ++line) {
            heavy_stream << "[HEAVY_LOG_TERM_1] Line " << line << ": compiler optimization step pass\n";
        }
        term1_buf.append(heavy_stream.str());
    }

    // Terminal #2 produces only 5 lines of lightweight output
    {
        core::RingBuffer term2_buf(sessions[1].get_buffer_path());
        term2_buf.append("[LIGHT_LOG_TERM_2] Status OK\n");
    }

    // 3. Verify absolute isolation across all 30 terminals
    for (size_t i = 1; i <= NUM_TERMINALS; ++i) {
        const auto& session = sessions[i - 1];
        std::string expected_marker = "TERMINAL_SESSION_MARKER_" + std::to_string(i) + "_UNIQUE_DATA";

        // Read session's buffer
        core::RingBuffer ring_buf(session.get_buffer_path());
        std::string content = ring_buf.read_all();

        // Must contain its own marker
        if (content.find(expected_marker) == std::string::npos) {
            throw std::runtime_error("Session " + std::to_string(i) + " missing its own marker: " + expected_marker);
        }

        // Must NOT contain any marker from ANY other terminal (1..30)
        for (size_t other = 1; other <= NUM_TERMINALS; ++other) {
            if (other == i) continue;
            std::string forbidden_marker = "TERMINAL_SESSION_MARKER_" + std::to_string(other) + "_UNIQUE_DATA";
            if (content.find(forbidden_marker) != std::string::npos) {
                throw std::runtime_error("CROSS-CONTAMINATION DETECTED! Session " + std::to_string(i) +
                                         " contains data from Session " + std::to_string(other) +
                                         " (" + forbidden_marker + ")");
            }
        }

        // Terminal #2 to #30 must NEVER contain Terminal #1's heavy logs
        if (i > 1) {
            if (content.find("[HEAVY_LOG_TERM_1]") != std::string::npos) {
                throw std::runtime_error("CROSS-CONTAMINATION DETECTED! Session " + std::to_string(i) +
                                         " contains heavy logs from Terminal #1!");
            }
        }
    }

    // 4. Verify Formatter with specific session resolution
    for (size_t i = 1; i <= NUM_TERMINALS; ++i) {
        const auto& session = sessions[i - 1];
        core::RingBuffer ring_buf(session.get_buffer_path());
        std::string raw = ring_buf.read_all();

        core::FormatterOptions opts;
        opts.mode = core::OutputMode::Clean;
        auto formatted = core::Formatter::format(raw, opts, session.get_metadata());

        std::string expected_marker = "TERMINAL_SESSION_MARKER_" + std::to_string(i) + "_UNIQUE_DATA";
        if (formatted.text.find(expected_marker) == std::string::npos) {
            throw std::runtime_error("Formatted output missing session marker for terminal " + std::to_string(i));
        }
    }

    // 5. Clean up test sessions
    for (const auto& s : sessions) {
        core::SessionManager::delete_session(s.get_id());
    }
}
