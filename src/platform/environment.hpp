#pragma once

#include <string>
#include <filesystem>
#include <optional>
#include <vector>

namespace copyterm::platform {

class Environment {
public:
    // Returns the root data directory for copyterm (~/.copyterm or %USERPROFILE%\.copyterm)
    static std::filesystem::path get_data_dir();

    // Returns the sessions directory (~/.copyterm/sessions)
    static std::filesystem::path get_sessions_dir();

    // Returns an environment variable value if set
    static std::optional<std::string> get_env(const std::string& name);

    // Sets an environment variable in the current process
    static bool set_env(const std::string& name, const std::string& value);

    // Ensures a directory exists with secure permissions
    static bool ensure_directory(const std::filesystem::path& path);

    // Returns the current OS name
    static std::string get_os_name();

    // Returns the current username
    static std::string get_username();

    // Returns the current working directory
    static std::filesystem::path get_current_working_dir();

    // Generates a cryptographically secure / high-entropy random hex string
    static std::string generate_random_hex(size_t length = 8);

    // Returns current epoch time in milliseconds
    static uint64_t get_current_time_ms();

    // Checks if stdout is a TTY/Terminal
    static bool is_stdout_tty();
};

} // namespace copyterm::platform
