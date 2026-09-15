#include "environment.hpp"

#include <chrono>
#include <random>
#include <sstream>
#include <iomanip>
#include <cstdlib>

#if defined(_WIN32) || defined(_WIN64)
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <io.h>
    #include <direct.h>
#else
    #include <unistd.h>
    #include <sys/types.h>
    #include <sys/stat.h>
    #include <pwd.h>
#endif

namespace copyterm::platform {

std::filesystem::path Environment::get_data_dir() {
    auto custom_dir = get_env("COPYTERM_DATA_DIR");
    if (custom_dir && !custom_dir->empty()) {
        return std::filesystem::path(*custom_dir);
    }

#if defined(_WIN32) || defined(_WIN64)
    auto user_profile = get_env("USERPROFILE");
    if (user_profile && !user_profile->empty()) {
        return std::filesystem::path(*user_profile) / ".copyterm";
    }
    auto appdata = get_env("LOCALAPPDATA");
    if (appdata && !appdata->empty()) {
        return std::filesystem::path(*appdata) / "copyterm";
    }
    return std::filesystem::temp_directory_path() / ".copyterm";
#else
    auto xdg_data = get_env("XDG_DATA_HOME");
    if (xdg_data && !xdg_data->empty()) {
        return std::filesystem::path(*xdg_data) / "copyterm";
    }
    auto home = get_env("HOME");
    if (home && !home->empty()) {
        return std::filesystem::path(*home) / ".copyterm";
    }
    return std::filesystem::temp_directory_path() / ".copyterm";
#endif
}

std::filesystem::path Environment::get_sessions_dir() {
    return get_data_dir() / "sessions";
}

std::optional<std::string> Environment::get_env(const std::string& name) {
#if defined(_WIN32) || defined(_WIN64)
    char buffer[4096];
    size_t required_size = 0;
    getenv_s(&required_size, buffer, sizeof(buffer), name.c_str());
    if (required_size > 0 && buffer[0] != '\0') {
        return std::string(buffer);
    }
    return std::nullopt;
#else
    const char* val = std::getenv(name.c_str());
    if (val != nullptr && val[0] != '\0') {
        return std::string(val);
    }
    return std::nullopt;
#endif
}

bool Environment::set_env(const std::string& name, const std::string& value) {
#if defined(_WIN32) || defined(_WIN64)
    return SetEnvironmentVariableA(name.c_str(), value.c_str()) != 0;
#else
    return setenv(name.c_str(), value.c_str(), 1) == 0;
#endif
}

bool Environment::ensure_directory(const std::filesystem::path& path) {
    try {
        if (!std::filesystem::exists(path)) {
            std::filesystem::create_directories(path);
        }
#if !defined(_WIN32) && !defined(_WIN64)
        // Set secure 0700 permissions on POSIX
        chmod(path.c_str(), S_IRWXU);
#endif
        return true;
    } catch (...) {
        return false;
    }
}

std::string Environment::get_os_name() {
#if defined(_WIN32) || defined(_WIN64)
    return "Windows";
#elif defined(__APPLE__) || defined(__MACH__)
    return "macOS";
#elif defined(__linux__)
    return "Linux";
#elif defined(__FreeBSD__)
    return "FreeBSD";
#else
    return "Unknown OS";
#endif
}

std::string Environment::get_username() {
    auto user = get_env("USERNAME");
    if (user) return *user;
    user = get_env("USER");
    if (user) return *user;
#if !defined(_WIN32) && !defined(_WIN64)
    struct passwd* pw = getpwuid(getuid());
    if (pw && pw->pw_name) {
        return std::string(pw->pw_name);
    }
#endif
    return "user";
}

std::filesystem::path Environment::get_current_working_dir() {
    try {
        return std::filesystem::current_path();
    } catch (...) {
        return std::filesystem::path(".");
    }
}

std::string Environment::generate_random_hex(size_t length) {
    static thread_local std::random_device rd;
    static thread_local std::mt19937_64 gen(rd());
    static thread_local std::uniform_int_distribution<uint32_t> dis(0, 15);

    const char hex_chars[] = "0123456789abcdef";
    std::string result;
    result.reserve(length);
    for (size_t i = 0; i < length; ++i) {
        result += hex_chars[dis(gen)];
    }
    return result;
}

uint64_t Environment::get_current_time_ms() {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()
    );
}

bool Environment::is_stdout_tty() {
#if defined(_WIN32) || defined(_WIN64)
    return _isatty(_fileno(stdout)) != 0;
#else
    return isatty(STDOUT_FILENO) != 0;
#endif
}

} // namespace copyterm::platform
