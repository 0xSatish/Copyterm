#include "sanitizer.hpp"

#include <sstream>
#include <iostream>
#include <vector>

namespace copyterm::core {

std::string Sanitizer::strip_ansi(const std::string& input) {
    std::string output;
    output.reserve(input.size());

    size_t i = 0;
    const size_t len = input.size();

    while (i < len) {
        if (input[i] == '\x1b') {
            i++; // skip ESC
            if (i >= len) break;

            if (input[i] == '[') {
                // CSI sequence: ESC [ [0-9;?]* [a-zA-Z~]
                i++;
                while (i < len && ((input[i] >= 0x20 && input[i] <= 0x3F))) {
                    i++;
                }
                if (i < len && (input[i] >= 0x40 && input[i] <= 0x7E)) {
                    i++; // skip final character
                }
            } else if (input[i] == ']') {
                // OSC sequence: ESC ] ... (BEL \x07 or ST ESC \)
                i++;
                while (i < len) {
                    if (input[i] == '\x07') {
                        i++;
                        break;
                    }
                    if (input[i] == '\x1b' && i + 1 < len && input[i + 1] == '\\') {
                        i += 2;
                        break;
                    }
                    i++;
                }
            } else if (input[i] == '(' || input[i] == ')' || input[i] == '*' || input[i] == '+') {
                // Character set selection
                i += 2;
            } else if (input[i] == 'P' || input[i] == '_' || input[i] == '^') {
                // DCS, APC, PM
                i++;
                while (i < len) {
                    if (input[i] == '\x07') {
                        i++;
                        break;
                    }
                    if (input[i] == '\x1b' && i + 1 < len && input[i + 1] == '\\') {
                        i += 2;
                        break;
                    }
                    i++;
                }
            } else {
                // Other 2-char escape sequence (e.g. ESC M, ESC E, etc.)
                i++;
            }
        } else {
            output += input[i];
            i++;
        }
    }

    return output;
}

std::string Sanitizer::collapse_carriage_returns(const std::string& input) {
    std::string result;
    result.reserve(input.size());

    std::string current_line;
    size_t cursor_col = 0;

    for (size_t i = 0; i < input.size(); ++i) {
        char c = input[i];

        if (c == '\r') {
            // Check if followed by \n (standard CRLF)
            if (i + 1 < input.size() && input[i + 1] == '\n') {
                result += current_line;
                result += '\n';
                current_line.clear();
                cursor_col = 0;
                i++; // skip \n
            } else {
                // Standalone \r: reset cursor column to 0 (line overwrite)
                cursor_col = 0;
            }
        } else if (c == '\n') {
            result += current_line;
            result += '\n';
            current_line.clear();
            cursor_col = 0;
        } else if (c == '\b') {
            // Backspace: move cursor back 1 col
            if (cursor_col > 0) {
                cursor_col--;
            }
        } else {
            // Printable or multibyte char
            if (cursor_col < current_line.size()) {
                current_line[cursor_col] = c;
            } else {
                if (cursor_col > current_line.size()) {
                    current_line.append(cursor_col - current_line.size(), ' ');
                }
                current_line += c;
            }
            cursor_col++;
        }
    }

    if (!current_line.empty()) {
        result += current_line;
    }

    return result;
}

std::string Sanitizer::normalize_newlines(const std::string& input) {
    std::string output;
    output.reserve(input.size());

    for (size_t i = 0; i < input.size(); ++i) {
        if (input[i] == '\r') {
            if (i + 1 < input.size() && input[i + 1] == '\n') {
                output += '\n';
                i++;
            } else {
                output += '\n';
            }
        } else {
            output += input[i];
        }
    }
    return output;
}

std::string Sanitizer::strip_shell_integration_marks(const std::string& input) {
    std::string output;
    output.reserve(input.size());

    size_t i = 0;
    const size_t len = input.size();

    while (i < len) {
        if (input[i] == '\x1b' && i + 1 < len && input[i + 1] == ']') {
            // Check for OSC 133
            size_t mark_start = i;
            i += 2;
            std::string osc_body;
            while (i < len && input[i] != '\x07') {
                if (input[i] == '\x1b' && i + 1 < len && input[i + 1] == '\\') {
                    i += 2;
                    break;
                }
                osc_body += input[i];
                i++;
            }
            if (i < len && input[i] == '\x07') {
                i++;
            }
            // If not shell mark, keep original
            if (osc_body.rfind("133;", 0) != 0) {
                output.append(input, mark_start, i - mark_start);
            }
        } else {
            output += input[i];
            i++;
        }
    }

    return output;
}

std::string Sanitizer::sanitize(const std::string& input, const SanitizerOptions& options) {
    std::string processed = input;

    if (options.strip_ansi) {
        processed = strip_ansi(processed);
    }

    if (options.collapse_carriage_returns) {
        processed = collapse_carriage_returns(processed);
    }

    if (options.normalize_newlines) {
        processed = normalize_newlines(processed);
    }

    if (options.strip_control_chars) {
        std::string cleaned;
        cleaned.reserve(processed.size());
        for (unsigned char c : processed) {
            // Keep newline, tab, and standard printable UTF-8 (>= 0x20, 0x09, 0x0A)
            if (c == '\n' || (c == '\t' && options.preserve_tabs) || c >= 0x20) {
                cleaned += static_cast<char>(c);
            }
        }
        processed = std::move(cleaned);
    }

    return processed;
}

} // namespace copyterm::core
