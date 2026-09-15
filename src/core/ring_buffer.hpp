#pragma once

#include <string>
#include <filesystem>
#include <vector>
#include <cstdint>

namespace copyterm::core {

struct RingBufferStats {
    size_t byte_count{0};
    size_t line_count{0};
    bool is_truncated{false};
};

class RingBuffer {
public:
    static constexpr size_t DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB per session
    static constexpr size_t DEFAULT_MAX_LINES = 50000;

    explicit RingBuffer(std::filesystem::path file_path, size_t max_size_bytes = DEFAULT_MAX_SIZE_BYTES);

    // Appends raw text data to the session buffer
    bool append(const std::string& data);

    // Appends a demarcated command entry
    bool append_command_record(const std::string& command, const std::string& cwd, uint64_t timestamp_ms);

    // Appends a command exit record
    bool append_exit_record(int exit_code, uint64_t timestamp_ms);

    // Reads all available captured content
    std::string read_all() const;

    // Reads the last N lines efficiently using reverse seeking
    std::string read_last_lines(size_t n) const;

    // Returns stats about the buffer
    RingBufferStats get_stats() const;

    // Clears the buffer
    bool clear();

    const std::filesystem::path& get_file_path() const { return file_path_; }

private:
    std::filesystem::path file_path_;
    size_t max_size_bytes_;

    void enforce_size_limit();
};

} // namespace copyterm::core
