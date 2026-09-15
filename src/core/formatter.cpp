#include "formatter.hpp"
#include "sanitizer.hpp"
#include "redaction.hpp"

#include <sstream>
#include <iostream>
#include <algorithm>

namespace copyterm::core {

namespace {
size_t count_lines(const std::string& str) {
    if (str.empty()) return 0;
    size_t lines = 0;
    for (char c : str) {
        if (c == '\n') lines++;
    }
    if (!str.empty() && str.back() != '\n') {
        lines++;
    }
    return lines;
}
} // namespace

std::string Formatter::take_last_lines(const std::string& content, size_t n) {
    if (n == 0 || content.empty()) return content;

    std::vector<std::string> lines;
    std::istringstream iss(content);
    std::string line;
    while (std::getline(iss, line)) {
        lines.push_back(line);
    }

    if (lines.size() <= n) {
        return content;
    }

    std::ostringstream oss;
    for (size_t i = lines.size() - n; i < lines.size(); ++i) {
        oss << lines[i] << "\n";
    }
    return oss.str();
}

std::string Formatter::filter_commands_only(const std::string& content) {
    std::istringstream iss(content);
    std::string line;
    std::ostringstream oss;

    while (std::getline(iss, line)) {
        // Strip trailing \r
        if (!line.empty() && line.back() == '\r') line.pop_back();

        // Check if line looks like a shell command prompt ($ ..., > ..., # ..., PS ...)
        if (line.rfind("$ ", 0) == 0 || line.rfind("> ", 0) == 0 || line.rfind("# ", 0) == 0 || line.rfind("PS ", 0) == 0) {
            oss << line << "\n";
        }
    }
    return oss.str();
}

std::string Formatter::filter_output_only(const std::string& content) {
    std::istringstream iss(content);
    std::string line;
    std::ostringstream oss;

    while (std::getline(iss, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();

        // Filter out obvious command prompts
        if (line.rfind("$ ", 0) != 0 && line.rfind("> ", 0) != 0 && line.rfind("# ", 0) != 0 && line.rfind("PS ", 0) != 0) {
            oss << line << "\n";
        }
    }
    return oss.str();
}

FormattedOutput Formatter::format_ai_markdown(
    const std::string& clean_content,
    const FormatterOptions& options,
    const std::optional<SessionMetadata>& metadata
) {
    FormattedOutput out;
    std::ostringstream oss;

    oss << "### Terminal Session Output\n\n";
    if (metadata) {
        oss << "- **Shell:** `" << metadata->shell_name << "`\n";
        oss << "- **Working Directory:** `" << metadata->cwd << "`\n";
        oss << "- **Terminal:** `" << metadata->terminal_name << "`\n";
        oss << "- **Session ID:** `" << metadata->session_id << "`\n\n";
    }

    oss << "```bash\n";
    oss << clean_content;
    if (!clean_content.empty() && clean_content.back() != '\n') {
        oss << "\n";
    }
    oss << "```\n";

    std::string formatted_text = oss.str();
    if (options.redact_secrets) {
        RedactionStats rstats;
        formatted_text = Redaction::redact(formatted_text, &rstats);
        out.secrets_redacted = rstats.secrets_masked;
    }

    out.text = formatted_text;
    out.line_count = count_lines(out.text);
    out.byte_count = out.text.size();
    return out;
}

FormattedOutput Formatter::format(
    const std::string& raw_content,
    const FormatterOptions& options,
    const std::optional<SessionMetadata>& metadata
) {
    FormattedOutput out;

    if (raw_content.empty()) {
        out.text = "";
        out.line_count = 0;
        out.byte_count = 0;
        return out;
    }

    if (options.mode == OutputMode::Raw) {
        std::string text = raw_content;
        if (options.last_n_lines > 0) {
            text = take_last_lines(text, options.last_n_lines);
        }
        if (options.redact_secrets) {
            RedactionStats rstats;
            text = Redaction::redact(text, &rstats);
            out.secrets_redacted = rstats.secrets_masked;
        }
        out.text = text;
        out.line_count = count_lines(out.text);
        out.byte_count = out.text.size();
        return out;
    }

    // Default clean mode: sanitize ANSI and collapse CR/BS
    std::string cleaned = Sanitizer::sanitize(raw_content);
    cleaned = Sanitizer::strip_shell_integration_marks(cleaned);

    if (options.mode == OutputMode::CommandsOnly) {
        cleaned = filter_commands_only(cleaned);
    } else if (options.mode == OutputMode::OutputOnly) {
        cleaned = filter_output_only(cleaned);
    }

    if (options.last_n_lines > 0) {
        cleaned = take_last_lines(cleaned, options.last_n_lines);
    }

    if (options.mode == OutputMode::AiMarkdown) {
        return format_ai_markdown(cleaned, options, metadata);
    }

    if (options.show_metadata_header && metadata) {
        std::ostringstream hdr;
        hdr << "# copyterm session: " << metadata->session_id << "\n";
        hdr << "# shell: " << metadata->shell_name << " | cwd: " << metadata->cwd << "\n";
        hdr << "# ------------------------------------------------------------\n";
        cleaned = hdr.str() + cleaned;
    }

    if (options.redact_secrets) {
        RedactionStats rstats;
        cleaned = Redaction::redact(cleaned, &rstats);
        out.secrets_redacted = rstats.secrets_masked;
    }

    out.text = cleaned;
    out.line_count = count_lines(out.text);
    out.byte_count = out.text.size();
    return out;
}

} // namespace copyterm::core
