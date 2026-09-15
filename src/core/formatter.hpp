#pragma once

#include <string>
#include <vector>
#include <optional>
#include "session.hpp"

namespace copyterm::core {

enum class OutputMode {
    Clean,         // Default: clean plain text with ANSI stripped and CR collapsed
    Raw,           // Raw binary VT stream preserved exactly
    AiMarkdown,    // Markdown formatted with metadata for AI/Notepad/LLM pasting
    CommandsOnly,  // Only command lines
    OutputOnly     // Only command output
};

struct FormatterOptions {
    OutputMode mode{OutputMode::Clean};
    size_t last_n_lines{0};  // 0 means all lines
    bool redact_secrets{false};
    bool show_metadata_header{false};
};

struct FormattedOutput {
    std::string text;
    size_t line_count{0};
    size_t byte_count{0};
    size_t secrets_redacted{0};
};

class Formatter {
public:
    static FormattedOutput format(
        const std::string& raw_content,
        const FormatterOptions& options,
        const std::optional<SessionMetadata>& metadata = std::nullopt
    );

private:
    static FormattedOutput format_ai_markdown(
        const std::string& clean_content,
        const FormatterOptions& options,
        const std::optional<SessionMetadata>& metadata
    );

    static std::string filter_commands_only(const std::string& content);
    static std::string filter_output_only(const std::string& content);
    static std::string take_last_lines(const std::string& content, size_t n);
};

} // namespace copyterm::core
