#include "process.hpp"
#include "environment.hpp"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <set>

#if defined(_WIN32) || defined(_WIN64)
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <tlhelp32.h>
    #include <psapi.h>
#else
    #include <unistd.h>
    #include <sys/types.h>
    #include <signal.h>
#endif

namespace copyterm::platform {

namespace {
std::string to_lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s;
}
} // namespace

uint32_t Process::get_current_pid() {
#if defined(_WIN32) || defined(_WIN64)
    return static_cast<uint32_t>(GetCurrentProcessId());
#else
    return static_cast<uint32_t>(getpid());
#endif
}

uint32_t Process::get_parent_pid(uint32_t pid) {
    if (pid == 0) {
        pid = get_current_pid();
    }

#if defined(_WIN32) || defined(_WIN64)
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        return 0;
    }

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    uint32_t ppid = 0;
    if (Process32FirstW(snapshot, &pe)) {
        do {
            if (pe.th32ProcessID == pid) {
                ppid = pe.th32ParentProcessID;
                break;
            }
        } while (Process32NextW(snapshot, &pe));
    }

    CloseHandle(snapshot);
    return ppid;
#else
    // Read from /proc/<pid>/stat
    std::string path = "/proc/" + std::to_string(pid) + "/stat";
    std::ifstream file(path);
    if (!file.is_open()) {
        return 0;
    }

    std::string line;
    if (std::getline(file, line)) {
        // Format: pid (comm) state ppid ...
        auto close_paren = line.rfind(')');
        if (close_paren != std::string::npos && close_paren + 2 < line.size()) {
            std::istringstream iss(line.substr(close_paren + 2));
            char state;
            uint32_t ppid = 0;
            if (iss >> state >> ppid) {
                return ppid;
            }
        }
    }
    return 0;
#endif
}

std::string Process::get_process_name(uint32_t pid) {
    if (pid == 0) return "";

#if defined(_WIN32) || defined(_WIN64)
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        return "";
    }

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    std::string name;
    if (Process32FirstW(snapshot, &pe)) {
        do {
            if (pe.th32ProcessID == pid) {
                char buffer[MAX_PATH];
                WideCharToMultiByte(CP_UTF8, 0, pe.szExeFile, -1, buffer, sizeof(buffer), nullptr, nullptr);
                name = buffer;
                break;
            }
        } while (Process32NextW(snapshot, &pe));
    }

    CloseHandle(snapshot);
    return name;
#else
    std::string comm_path = "/proc/" + std::to_string(pid) + "/comm";
    std::ifstream file(comm_path);
    if (file.is_open()) {
        std::string name;
        if (std::getline(file, name)) {
            // Trim whitespace/newline
            while (!name.empty() && (name.back() == '\n' || name.back() == '\r')) {
                name.pop_back();
            }
            return name;
        }
    }
    return "";
#endif
}

bool Process::is_process_alive(uint32_t pid) {
    if (pid == 0) return false;

#if defined(_WIN32) || defined(_WIN64)
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (hProcess == nullptr) {
        return false;
    }
    DWORD exit_code = 0;
    BOOL result = GetExitCodeProcess(hProcess, &exit_code);
    CloseHandle(hProcess);
    return (result && exit_code == STILL_ACTIVE);
#else
    return (kill(static_cast<pid_t>(pid), 0) == 0);
#endif
}

std::vector<ProcessInfo> Process::get_process_ancestors(uint32_t pid) {
    std::vector<ProcessInfo> ancestors;
    if (pid == 0) {
        pid = get_current_pid();
    }

    std::set<uint32_t> visited;
    uint32_t current = pid;

    while (current != 0 && visited.find(current) == visited.end()) {
        visited.insert(current);
        uint32_t parent = get_parent_pid(current);
        if (parent == 0 || parent == current) {
            break;
        }

        ProcessInfo info;
        info.pid = parent;
        info.ppid = get_parent_pid(parent);
        info.name = get_process_name(parent);
        ancestors.push_back(info);

        current = parent;
    }

    return ancestors;
}

std::string Process::detect_shell_name() {
    // 1. Check environment hints
    auto shell_env = Environment::get_env("SHELL");
    auto ps_module_path = Environment::get_env("PSModulePath");

    // 2. Traverse ancestors to find immediate shell
    auto ancestors = get_process_ancestors();
    for (const auto& proc : ancestors) {
        std::string name_lower = to_lower(proc.name);
        if (name_lower.find("pwsh") != std::string::npos) return "pwsh";
        if (name_lower.find("powershell") != std::string::npos) return "powershell";
        if (name_lower.find("bash") != std::string::npos) return "bash";
        if (name_lower.find("zsh") != std::string::npos) return "zsh";
        if (name_lower.find("fish") != std::string::npos) return "fish";
        if (name_lower.find("cmd.exe") != std::string::npos) return "cmd";
        if (name_lower.find("nushell") != std::string::npos || name_lower.find("nu.exe") != std::string::npos) return "nu";
    }

    if (shell_env && !shell_env->empty()) {
        std::string s = to_lower(*shell_env);
        if (s.find("bash") != std::string::npos) return "bash";
        if (s.find("zsh") != std::string::npos) return "zsh";
        if (s.find("fish") != std::string::npos) return "fish";
        return *shell_env;
    }

#if defined(_WIN32) || defined(_WIN64)
    if (ps_module_path) return "powershell";
    return "cmd";
#else
    return "bash";
#endif
}

std::string Process::detect_terminal_emulator() {
    // Check environment variables first
    if (Environment::get_env("WT_SESSION")) {
        return "Windows Terminal";
    }
    if (Environment::get_env("TMUX")) {
        return "tmux";
    }
    if (Environment::get_env("VSCODE_INJECTION") || Environment::get_env("TERM_PROGRAM") == "vscode") {
        return "VS Code Terminal";
    }
    if (Environment::get_env("KITTY_WINDOW_ID")) {
        return "Kitty";
    }
    if (Environment::get_env("WEZTERM_PANE")) {
        return "WezTerm";
    }
    if (Environment::get_env("ALACRITTY_WINDOW_ID")) {
        return "Alacritty";
    }
    if (Environment::get_env("GNOME_TERMINAL_SCREEN") || Environment::get_env("GNOME_TERMINAL_SERVICE")) {
        return "GNOME Terminal";
    }
    if (Environment::get_env("KONSOLE_VERSION")) {
        return "Konsole";
    }
    auto term_prog = Environment::get_env("TERM_PROGRAM");
    if (term_prog) {
        return *term_prog;
    }

    // Inspect ancestors for terminal GUI process
    auto ancestors = get_process_ancestors();
    for (const auto& proc : ancestors) {
        std::string name_lower = to_lower(proc.name);
        if (name_lower.find("windowsterminal") != std::string::npos) return "Windows Terminal";
        if (name_lower.find("code.exe") != std::string::npos || name_lower.find("code") != std::string::npos) return "VS Code";
        if (name_lower.find("alacritty") != std::string::npos) return "Alacritty";
        if (name_lower.find("kitty") != std::string::npos) return "Kitty";
        if (name_lower.find("wezterm") != std::string::npos) return "WezTerm";
        if (name_lower.find("conhost") != std::string::npos) return "Windows Console (ConHost)";
        if (name_lower.find("gnome-terminal") != std::string::npos) return "GNOME Terminal";
        if (name_lower.find("konsole") != std::string::npos) return "Konsole";
        if (name_lower.find("xterm") != std::string::npos) return "xterm";
    }

#if defined(_WIN32) || defined(_WIN64)
    return "Windows Console";
#else
    return "Standard PTY";
#endif
}

std::string Process::detect_tty_device() {
#if defined(_WIN32) || defined(_WIN64)
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hConsole != INVALID_HANDLE_VALUE && hConsole != nullptr) {
        DWORD mode = 0;
        if (GetConsoleMode(hConsole, &mode)) {
            return "Windows Console Handle (" + std::to_string(reinterpret_cast<uintptr_t>(hConsole)) + ")";
        }
    }
    return "Standard Stream";
#else
    char* tty_name = ttyname(STDIN_FILENO);
    if (tty_name != nullptr) {
        return std::string(tty_name);
    }
    tty_name = ttyname(STDOUT_FILENO);
    if (tty_name != nullptr) {
        return std::string(tty_name);
    }
    return "unknown-tty";
#endif
}

} // namespace copyterm::platform
