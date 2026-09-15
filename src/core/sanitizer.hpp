#pragma once

#include <string>
#include <vector>

namespace copyterm::core {

struct SanitizerOptions {
    bool strip_ansi{true};
    bool collapse_carriage_returns{true};
    bool normalize_newlines{true};
    bool strip_control_chars{true};
    bool preserve_tabs{true};
};

class Sanitizer {
public:
    // Cleans and sanitizes raw terminal output according to options
    static std::string sanitize(const std::string& input, const SanitizerOptions& options = SanitizerOptions{});

    // Fast ANSI escape sequence stripper
    static std::string strip_ansi(const std::string& input);

    // Simulates terminal line buffer for \r carriage returns and \b backspaces
    static std::string collapse_carriage_returns(const std::string& input);

    // Normalizes mixed CRLF / LF newlines to standard system newlines or \n
    static std::string normalize_newlines(const std::string& input);

    // Strips shell integration metadata marks (\x1b]133;...\x07)
    static std::string strip_shell_integration_marks(const std::string& input);
};

} // namespace copyterm::core
