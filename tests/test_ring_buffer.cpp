#include "../src/core/ring_buffer.hpp"
#include "../src/platform/environment.hpp"

#include <iostream>
#include <stdexcept>
#include <sstream>

void run_ring_buffer_tests() {
    using namespace copyterm;

    auto temp_dir = platform::Environment::get_sessions_dir();
    auto test_buf_path = temp_dir / "test_buffer_unit.buf";

    // 1. Initialize and clear
    core::RingBuffer buf(test_buf_path, 1024 * 1024); // 1 MB limit
    buf.clear();

    // 2. Append lines
    buf.append("Line 1: echo hello\n");
    buf.append("Line 2: output line 1\n");
    buf.append("Line 3: output line 2\n");
    buf.append("Line 4: error message\n");
    buf.append("Line 5: final line\n");

    // 3. Test read_all()
    std::string all = buf.read_all();
    if (all.find("Line 1: echo hello") == std::string::npos ||
        all.find("Line 5: final line") == std::string::npos) {
        throw std::runtime_error("read_all() failed to return all lines");
    }

    // 4. Test read_last_lines(N)
    std::string last2 = buf.read_last_lines(2);
    if (last2.find("Line 4: error message") == std::string::npos ||
        last2.find("Line 5: final line") == std::string::npos) {
        throw std::runtime_error("read_last_lines(2) did not include last 2 lines");
    }
    if (last2.find("Line 1: echo hello") != std::string::npos) {
        throw std::runtime_error("read_last_lines(2) included older lines");
    }

    std::string last1 = buf.read_last_lines(1);
    if (last1.find("Line 5: final line") == std::string::npos ||
        last1.find("Line 4:") != std::string::npos) {
        throw std::runtime_error("read_last_lines(1) failed");
    }

    // 5. Test stats
    auto stats = buf.get_stats();
    if (stats.line_count != 5) {
        throw std::runtime_error("get_stats() line_count mismatch: expected 5, got " + std::to_string(stats.line_count));
    }

    // 6. Test Ring Buffer Size Truncation
    auto small_buf_path = temp_dir / "test_small_ring.buf";
    core::RingBuffer small_buf(small_buf_path, 1000); // 1000 bytes max
    small_buf.clear();

    for (int i = 0; i < 50; ++i) {
        small_buf.append("Long line of terminal session output for testing ring buffer overflow " + std::to_string(i) + "\n");
    }

    auto small_stats = small_buf.get_stats();
    if (small_stats.byte_count > 1200) {
        throw std::runtime_error("Ring buffer failed to enforce max size limit");
    }

    // Clean up
    buf.clear();
    small_buf.clear();
    std::filesystem::remove(test_buf_path);
    std::filesystem::remove(small_buf_path);
}
