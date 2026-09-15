#include "installer.hpp"
#include "../platform/environment.hpp"

#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>

namespace copyterm::installer {

namespace {
const char* MARKER_START = "# >>> copyterm shell integration >>>";
const char* MARKER_END   = "# <<< copyterm shell integration <<<";
const char* CMD_MARKER_START = ":: >>> copyterm shell integration >>>";
const char* CMD_MARKER_END   = ":: <<< copyterm shell integration <<<";

std::string get_powershell_hook() {
    return std::string(MARKER_START) + "\n"
        "# copyterm PowerShell Integration\n"
        "if (-not $env:COPYTERM_SESSION_ID) {\n"
        "    $env:COPYTERM_SESSION_ID = \"sess_\" + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + \"_$PID_\" + ([System.Guid]::NewGuid().ToString(\"N\").Substring(0, 6))\n"
        "}\n"
        "$global:__copyterm_session_file = [System.IO.Path]::Combine($env:USERPROFILE, \".copyterm\", \"sessions\", \"$($env:COPYTERM_SESSION_ID).buf\")\n"
        "$null = [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($global:__copyterm_session_file))\n"
        "\n"
        "function global:__copyterm_record_command($cmd) {\n"
        "    if ([string]::IsNullOrWhiteSpace($cmd)) { return }\n"
        "    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()\n"
        "    $cwd = (Get-Location).Path\n"
        "    $entry = \"`n`e]133;C;cmd=$cmd;cwd=$cwd;ts=$ts`a`n`$ $cmd`n\"\n"
        "    [System.IO.File]::AppendAllText($global:__copyterm_session_file, $entry)\n"
        "}\n"
        "\n"
        "# Hook prompt\n"
        "if (Test-Path Function:\\prompt) {\n"
        "    $global:__copyterm_old_prompt = $Function:prompt\n"
        "} else {\n"
        "    $global:__copyterm_old_prompt = { \"PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) \" }\n"
        "}\n"
        "function global:prompt {\n"
        "    $lastHistory = Get-History -Count 1 -ErrorAction SilentlyContinue\n"
        "    if ($lastHistory -and ($global:__copyterm_last_id -ne $lastHistory.Id)) {\n"
        "        $global:__copyterm_last_id = $lastHistory.Id\n"
        "        global:__copyterm_record_command $lastHistory.CommandLine\n"
        "    }\n"
        "    & $global:__copyterm_old_prompt\n"
        "}\n"
        + MARKER_END + "\n";
}

std::string get_bash_hook() {
    return std::string(MARKER_START) + "\n"
        "# copyterm Bash Integration\n"
        "if [ -z \"$COPYTERM_SESSION_ID\" ]; then\n"
        "    export COPYTERM_SESSION_ID=\"sess_$(date +%s%3N)_${$}_$(head /dev/urandom | tr -dc a-f0-9 | head -c 6)\"\n"
        "fi\n"
        "__copyterm_dir=\"${COPYTERM_DATA_DIR:-$HOME/.copyterm}/sessions\"\n"
        "mkdir -p \"$__copyterm_dir\" 2>/dev/null\n"
        "__copyterm_file=\"$__copyterm_dir/${COPYTERM_SESSION_ID}.buf\"\n"
        "\n"
        "__copyterm_preexec() {\n"
        "    local cmd=\"$1\"\n"
        "    [ -z \"$cmd\" ] && return\n"
        "    local ts=$(date +%s%3N 2>/dev/null || date +%s)\n"
        "    printf \"\\n\\033]133;C;cmd=%%s;cwd=%%s;ts=%%s\\007\\n$ %%s\\n\" \"$cmd\" \"$PWD\" \"$ts\" \"$cmd\" >> \"$__copyterm_file\" 2>/dev/null\n"
        "}\n"
        "\n"
        "__copyterm_prompt_command() {\n"
        "    local last_exit=\"$?\"\n"
        "    local last_cmd=\"$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')\"\n"
        "    if [ \"$last_cmd\" != \"$__copyterm_last_cmd\" ] && [ -n \"$last_cmd\" ]; then\n"
        "        __copyterm_last_cmd=\"$last_cmd\"\n"
        "        __copyterm_preexec \"$last_cmd\"\n"
        "    fi\n"
        "}\n"
        "if [[ ! \"$PROMPT_COMMAND\" =~ __copyterm_prompt_command ]]; then\n"
        "    PROMPT_COMMAND=\"__copyterm_prompt_command;${PROMPT_COMMAND:-}\"\n"
        "fi\n"
        + MARKER_END + "\n";
}

std::string get_zsh_hook() {
    return std::string(MARKER_START) + "\n"
        "# copyterm Zsh Integration\n"
        "if [ -z \"$COPYTERM_SESSION_ID\" ]; then\n"
        "    export COPYTERM_SESSION_ID=\"sess_$(date +%s%3N)_${$}_$(head /dev/urandom | tr -dc a-f0-9 | head -c 6)\"\n"
        "fi\n"
        "__copyterm_dir=\"${COPYTERM_DATA_DIR:-$HOME/.copyterm}/sessions\"\n"
        "mkdir -p \"$__copyterm_dir\" 2>/dev/null\n"
        "__copyterm_file=\"$__copyterm_dir/${COPYTERM_SESSION_ID}.buf\"\n"
        "\n"
        "__copyterm_preexec() {\n"
        "    local cmd=\"$1\"\n"
        "    [ -z \"$cmd\" ] && return\n"
        "    local ts=$(date +%s%3N 2>/dev/null || date +%s)\n"
        "    printf \"\\n\\033]133;C;cmd=%%s;cwd=%%s;ts=%%s\\007\\n$ %%s\\n\" \"$cmd\" \"$PWD\" \"$ts\" \"$cmd\" >> \"$__copyterm_file\" 2>/dev/null\n"
        "}\n"
        "autoload -Uz add-zsh-hook 2>/dev/null\n"
        "if (( $+functions[add-zsh-hook] )); then\n"
        "    add-zsh-hook preexec __copyterm_preexec\n"
        "fi\n"
        + MARKER_END + "\n";
}

std::string get_cmd_hook() {
    return std::string(CMD_MARKER_START) + "\n"
        "@echo off\n"
        ":: copyterm CMD integration\n"
        "if \"%COPYTERM_SESSION_ID%\"==\"\" (\n"
        "    set \"COPYTERM_SESSION_ID=sess_%RANDOM%_%RANDOM%\"\n"
        ")\n"
        + CMD_MARKER_END + "\n";
}

bool backup_file(const std::filesystem::path& path) {
    if (!std::filesystem::exists(path)) return true;
    try {
        uint64_t ts = platform::Environment::get_current_time_ms();
        std::filesystem::path backup_path = path.string() + ".bak." + std::to_string(ts);
        std::filesystem::copy_file(path, backup_path, std::filesystem::copy_options::overwrite_existing);
        return true;
    } catch (...) {
        return false;
    }
}
} // namespace

ShellType ShellInstaller::parse_shell_type(const std::string& name) {
    std::string s = name;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    if (s == "powershell" || s == "pwsh" || s == "ps") return ShellType::PowerShell;
    if (s == "bash") return ShellType::Bash;
    if (s == "zsh") return ShellType::Zsh;
    if (s == "cmd") return ShellType::Cmd;
    return ShellType::All;
}

std::string ShellInstaller::get_hook_snippet(ShellType shell) {
    switch (shell) {
        case ShellType::PowerShell: return get_powershell_hook();
        case ShellType::Bash: return get_bash_hook();
        case ShellType::Zsh: return get_zsh_hook();
        case ShellType::Cmd: return get_cmd_hook();
        case ShellType::All: return "";
    }
    return "";
}

std::vector<std::filesystem::path> ShellInstaller::get_profile_paths(ShellType shell) {
    std::vector<std::filesystem::path> paths;

    if (shell == ShellType::PowerShell || shell == ShellType::All) {
#if defined(_WIN32) || defined(_WIN64)
        auto userprofile = platform::Environment::get_env("USERPROFILE");
        if (userprofile) {
            // Windows PowerShell 5.1
            paths.push_back(std::filesystem::path(*userprofile) / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1");
            // PowerShell 7+
            paths.push_back(std::filesystem::path(*userprofile) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1");
        }
#else
        auto home = platform::Environment::get_env("HOME");
        if (home) {
            paths.push_back(std::filesystem::path(*home) / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1");
        }
#endif
    }

    if (shell == ShellType::Bash || shell == ShellType::All) {
#if defined(_WIN32) || defined(_WIN64)
        auto userprofile = platform::Environment::get_env("USERPROFILE");
        if (userprofile) {
            paths.push_back(std::filesystem::path(*userprofile) / ".bashrc");
        }
#else
        auto home = platform::Environment::get_env("HOME");
        if (home) {
            paths.push_back(std::filesystem::path(*home) / ".bashrc");
        }
#endif
    }

    if (shell == ShellType::Zsh || shell == ShellType::All) {
#if defined(_WIN32) || defined(_WIN64)
        auto userprofile = platform::Environment::get_env("USERPROFILE");
        if (userprofile) {
            paths.push_back(std::filesystem::path(*userprofile) / ".zshrc");
        }
#else
        auto home = platform::Environment::get_env("HOME");
        if (home) {
            paths.push_back(std::filesystem::path(*home) / ".zshrc");
        }
#endif
    }

    return paths;
}

std::vector<InstallResult> ShellInstaller::install(ShellType shell) {
    std::vector<InstallResult> results;
    std::vector<ShellType> shells_to_process;

    if (shell == ShellType::All) {
        shells_to_process = { ShellType::PowerShell, ShellType::Bash, ShellType::Zsh };
    } else {
        shells_to_process = { shell };
    }

    for (auto target_shell : shells_to_process) {
        auto profile_paths = get_profile_paths(target_shell);
        std::string snippet = get_hook_snippet(target_shell);
        std::string shell_name = (target_shell == ShellType::PowerShell ? "PowerShell" :
                                 target_shell == ShellType::Bash ? "Bash" :
                                 target_shell == ShellType::Zsh ? "Zsh" : "CMD");

        for (const auto& path : profile_paths) {
            InstallResult res;
            res.shell_name = shell_name;
            res.profile_path = path;

            // Check if profile exists or directory exists
            if (path.has_parent_path()) {
                platform::Environment::ensure_directory(path.parent_path());
            }

            std::string existing_content;
            if (std::filesystem::exists(path)) {
                std::ifstream in(path);
                if (in.is_open()) {
                    existing_content = std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
                }
            }

            // Check if already installed
            if (existing_content.find(MARKER_START) != std::string::npos || existing_content.find(CMD_MARKER_START) != std::string::npos) {
                res.success = true;
                res.already_installed = true;
                res.message = "copyterm integration is already installed in " + path.string();
                results.push_back(res);
                continue;
            }

            // Backup file before modification
            backup_file(path);

            // Append snippet cleanly
            std::ofstream out(path, std::ios::out | std::ios::app);
            if (!out.is_open()) {
                res.success = false;
                res.message = "Failed to open profile for writing: " + path.string();
                results.push_back(res);
                continue;
            }

            if (!existing_content.empty() && existing_content.back() != '\n') {
                out << "\n";
            }
            out << "\n" << snippet;
            out.close();

            res.success = true;
            res.message = "Successfully installed copyterm integration to " + path.string();
            results.push_back(res);
        }
    }

    return results;
}

std::vector<InstallResult> ShellInstaller::uninstall(ShellType shell) {
    std::vector<InstallResult> results;
    std::vector<ShellType> shells_to_process;

    if (shell == ShellType::All) {
        shells_to_process = { ShellType::PowerShell, ShellType::Bash, ShellType::Zsh };
    } else {
        shells_to_process = { shell };
    }

    for (auto target_shell : shells_to_process) {
        auto profile_paths = get_profile_paths(target_shell);
        std::string shell_name = (target_shell == ShellType::PowerShell ? "PowerShell" :
                                 target_shell == ShellType::Bash ? "Bash" :
                                 target_shell == ShellType::Zsh ? "Zsh" : "CMD");

        for (const auto& path : profile_paths) {
            InstallResult res;
            res.shell_name = shell_name;
            res.profile_path = path;

            if (!std::filesystem::exists(path)) {
                res.success = true;
                res.message = "Profile file does not exist: " + path.string();
                results.push_back(res);
                continue;
            }

            std::ifstream in(path);
            if (!in.is_open()) {
                res.success = false;
                res.message = "Failed to open profile: " + path.string();
                results.push_back(res);
                continue;
            }

            std::string line;
            std::ostringstream new_content;
            bool inside_marker = false;
            bool found_marker = false;

            while (std::getline(in, line)) {
                if (line.find(MARKER_START) != std::string::npos || line.find(CMD_MARKER_START) != std::string::npos) {
                    inside_marker = true;
                    found_marker = true;
                    continue;
                }
                if (line.find(MARKER_END) != std::string::npos || line.find(CMD_MARKER_END) != std::string::npos) {
                    inside_marker = false;
                    continue;
                }
                if (!inside_marker) {
                    new_content << line << "\n";
                }
            }
            in.close();

            if (!found_marker) {
                res.success = true;
                res.message = "No copyterm integration found in " + path.string();
                results.push_back(res);
                continue;
            }

            backup_file(path);

            std::ofstream out(path, std::ios::out | std::ios::trunc);
            if (!out.is_open()) {
                res.success = false;
                res.message = "Failed to write updated profile: " + path.string();
                results.push_back(res);
                continue;
            }

            out << new_content.str();
            out.close();

            res.success = true;
            res.message = "Successfully removed copyterm integration from " + path.string();
            results.push_back(res);
        }
    }

    return results;
}

} // namespace copyterm::installer
