#include "ring_buffer.hpp"
#include "../platform/environment.hpp"

#include <fstream>
#include <iostream>
#include <algorithm>
#include <cstring>

#if defined(_WIN32) || defined(_WIN64)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace copyterm::core {

RingBuffer::RingBuffer(std::filesystem::path file_path, size_t max_size_bytes)
    : file_path_(std::move(file_path)), max_size_bytes_(max_size_bytes) {
    if (file_path_.has_parent_path()) {
        platform::Environment::ensure_directory(file_path_.parent_path());
    }
}

bool RingBuffer::append(const std::string& data) {
    if (data.empty()) return true;

    std::ofstream out(file_path_, std::ios::out | std::ios::app | std::ios::binary);
    if (!out.is_open()) {
        return false;
    }

    out.write(data.data(), static_cast<std::streamsize>(data.size()));
    out.flush();

    enforce_size_limit();
    return true;
}

bool RingBuffer::append_command_record(const std::string& command, const std::string& cwd, uint64_t timestamp_ms) {
    std::string record = "\n\x1b]133;C;cmd=" + command + ";cwd=" + cwd + ";ts=" + std::to_string(timestamp_ms) + "\x07\n"
                         + "$ " + command + "\n";
    return append(record);
}

bool RingBuffer::append_exit_record(int exit_code, uint64_t timestamp_ms) {
    std::string record = "\x1b]133;D;exit=" + std::to_string(exit_code) + ";ts=" + std::to_string(timestamp_ms) + "\x07\n";
    return append(record);
}

std::string RingBuffer::read_all() const {
    if (!std::filesystem::exists(file_path_)) {
        return "";
    }

#if defined(_WIN32) || defined(_WIN64)
    HANDLE hFile = CreateFileW(
        file_path_.c_str(),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );
    if (hFile == INVALID_HANDLE_VALUE) {
        return "";
    }
    LARGE_INTEGER size;
    if (!GetFileSizeEx(hFile, &size) || size.QuadPart == 0) {
        CloseHandle(hFile);
        return "";
    }
    std::string result(static_cast<size_t>(size.QuadPart), '\0');
    DWORD bytesRead = 0;
    ReadFile(hFile, &result[0], static_cast<DWORD>(size.QuadPart), &bytesRead, NULL);
    CloseHandle(hFile);
    result.resize(bytesRead);
    return result;
#else
    std::ifstream in(file_path_, std::ios::in | std::ios::binary);
    if (!in.is_open()) {
        return "";
    }
    return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
#endif
}

std::string RingBuffer::read_last_lines(size_t n) const {
    if (n == 0 || !std::filesystem::exists(file_path_)) {
        return "";
    }

    std::ifstream in(file_path_, std::ios::in | std::ios::binary | std::ios::ate);
    if (!in.is_open()) {
        return "";
    }

    std::streampos file_size = in.tellg();
    if (file_size <= 0) {
        return "";
    }

    // Read backwards in chunks of 8KB
    const size_t chunk_size = 8192;
    std::vector<char> buffer(chunk_size);
    size_t lines_found = 0;
    std::streampos current_pos = file_size;
    std::streampos start_pos = 0;

    // Check if file ends with newline
    bool last_char_checked = false;

    while (current_pos > 0 && lines_found <= n) {
        size_t bytes_to_read = std::min(static_cast<size_t>(current_pos), chunk_size);
        current_pos -= bytes_to_read;
        in.seekg(current_pos);
        in.read(buffer.data(), static_cast<std::streamsize>(bytes_to_read));

        // Scan chunk in reverse
        for (ssize_t i = static_cast<ssize_t>(bytes_to_read) - 1; i >= 0; --i) {
            char c = buffer[static_cast<size_t>(i)];

            // If the very last character of the file is a newline, don't count it as a line boundary
            if (!last_char_checked && (current_pos + static_cast<std::streampos>(i) == file_size - static_cast<std::streampos>(1))) {
                last_char_checked = true;
                if (c == '\n') continue;
            }
            last_char_checked = true;

            if (c == '\n') {
                lines_found++;
                if (lines_found >= n) {
                    start_pos = current_pos + static_cast<std::streampos>(i + 1);
                    break;
                }
            }
        }

        if (lines_found >= n) {
            break;
        }
    }

    in.seekg(start_pos);
    size_t length_to_read = static_cast<size_t>(file_size - start_pos);
    std::string result(length_to_read, '\0');
    in.read(&result[0], static_cast<std::streamsize>(length_to_read));

    return result;
}

RingBufferStats RingBuffer::get_stats() const {
    RingBufferStats stats;
    if (!std::filesystem::exists(file_path_)) {
        return stats;
    }

    try {
        stats.byte_count = std::filesystem::file_size(file_path_);
    } catch (...) {
        return stats;
    }

    std::ifstream in(file_path_, std::ios::in | std::ios::binary);
    if (!in.is_open()) {
        return stats;
    }

    char ch;
    while (in.get(ch)) {
        if (ch == '\n') {
            stats.line_count++;
        }
    }

    return stats;
}

bool RingBuffer::clear() {
    try {
        if (std::filesystem::exists(file_path_)) {
            std::ofstream out(file_path_, std::ios::out | std::ios::trunc);
            return out.is_open();
        }
        return true;
    } catch (...) {
        return false;
    }
}

void RingBuffer::enforce_size_limit() {
    try {
        if (!std::filesystem::exists(file_path_)) return;
        auto size = std::filesystem::file_size(file_path_);
        if (size <= max_size_bytes_) return;

        // Truncate oldest half: keep the most recent max_size_bytes_ / 2 bytes
        size_t keep_bytes = max_size_bytes_ / 2;
        std::ifstream in(file_path_, std::ios::in | std::ios::binary);
        if (!in.is_open()) return;

        in.seekg(static_cast<std::streamoff>(size - keep_bytes));
        
        // Find next newline to keep line integrity
        std::string line;
        std::getline(in, line); // discard partial line

        std::string remaining_content((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        in.close();

        std::ofstream out(file_path_, std::ios::out | std::ios::trunc | std::ios::binary);
        if (out.is_open()) {
            std::string notice = "[copyterm: older session history truncated to conserve memory]\n";
            out.write(notice.data(), static_cast<std::streamsize>(notice.size()));
            out.write(remaining_content.data(), static_cast<std::streamsize>(remaining_content.size()));
        }
    } catch (...) {}
}

} // namespace copyterm::core
