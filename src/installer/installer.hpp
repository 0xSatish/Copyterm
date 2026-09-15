#pragma once

#include <string>
#include <vector>
#include <filesystem>

namespace copyterm::installer {

enum class ShellType {
    PowerShell,
    Bash,
    Zsh,
    Cmd,
    All
};

struct InstallResult {
    bool success{false};
    std::string shell_name;
    std::filesystem::path profile_path;
    std::string message;
    bool already_installed{false};
};

class ShellInstaller {
public:
    // Installs shell integration for a specific shell or all detected shells
    static std::vector<InstallResult> install(ShellType shell);

    // Uninstalls shell integration for a specific shell or all detected shells
    static std::vector<InstallResult> uninstall(ShellType shell);

    // Converts string name (e.g. "powershell", "bash", "zsh", "cmd", "all") to ShellType
    static ShellType parse_shell_type(const std::string& name);

    // Generates the hook script snippet for the given shell
    static std::string get_hook_snippet(ShellType shell);

    // Finds the profile path for the given shell
    static std::vector<std::filesystem::path> get_profile_paths(ShellType shell);
};

} // namespace copyterm::installer
