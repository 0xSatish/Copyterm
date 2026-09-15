#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <optional>

namespace copyterm::platform {

struct ProcessInfo {
    uint32_t pid{0};
    uint32_t ppid{0};
    std::string name;
    std::string path;
};

class Process {
public:
    // Returns current process ID
    static uint32_t get_current_pid();

    // Returns parent process ID of the given PID (default: current process)
    static uint32_t get_parent_pid(uint32_t pid = 0);

    // Returns process name for a given PID
    static std::string get_process_name(uint32_t pid);

    // Checks if a process is still active/alive
    static bool is_process_alive(uint32_t pid);

    // Returns list of ancestor process IDs starting from parent up to root
    static std::vector<ProcessInfo> get_process_ancestors(uint32_t pid = 0);

    // Detects the active shell name (e.g. "powershell", "pwsh", "bash", "zsh", "cmd")
    static std::string detect_shell_name();

    // Detects the terminal emulator name (e.g. "Windows Terminal", "GNOME Terminal", "Alacritty", "Kitty", "tmux", "VS Code")
    static std::string detect_terminal_emulator();

    // Detects the current TTY / Console device name
    static std::string detect_tty_device();
};

} // namespace copyterm::platform
