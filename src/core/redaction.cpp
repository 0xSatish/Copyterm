#include "redaction.hpp"

#include <regex>
#include <iostream>

namespace copyterm::core {

namespace {
struct RedactPattern {
    std::string name;
    std::regex regex;
    std::string replacement;
};

const std::vector<RedactPattern>& get_patterns() {
    static const std::vector<RedactPattern> patterns = {
        // AWS Access Key ID
        {
            "AWS Access Key",
            std::regex(R"(\b(AKIA[0-9A-Z]{16})\b)"),
            "AKIA[REDACTED_AWS_KEY]"
        },
        // GitHub Personal Access Token (classic and fine-grained)
        {
            "GitHub Token",
            std::regex(R"(\b(gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59})\b)"),
            "[REDACTED_GITHUB_TOKEN]"
        },
        // Private Key Block
        {
            "Private Key",
            std::regex(R"(-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)"),
            "[REDACTED_PRIVATE_KEY]"
        },
        // Bearer / JWT Token
        {
            "Bearer / JWT Token",
            std::regex(R"((Bearer\s+)(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*))"),
            "$1[REDACTED_JWT_TOKEN]"
        },
        // Generic Password / API Key in assignment (e.g. password="...", api_key='...')
        {
            "Password Assignment",
            std::regex(R"((\b(password|passwd|api_key|apikey|secret_key|secret|auth_token)\s*[:=]\s*["']?)([^"'\s\r\n]{6,})(["']?))", std::regex_constants::icase),
            "$1[REDACTED_SECRET]$4"
        },
        // Slack Webhook / Token
        {
            "Slack Token",
            std::regex(R"(xox[baprs]-[0-9a-zA-Z]{10,48})"),
            "[REDACTED_SLACK_TOKEN]"
        }
    };
    return patterns;
}
} // namespace

std::string Redaction::redact(const std::string& input, RedactionStats* stats) {
    std::string result = input;
    const auto& patterns = get_patterns();

    for (const auto& pat : patterns) {
        try {
            if (stats) {
                auto words_begin = std::sregex_iterator(result.begin(), result.end(), pat.regex);
                auto words_end = std::sregex_iterator();
                stats->secrets_masked += static_cast<size_t>(std::distance(words_begin, words_end));
            }
            result = std::regex_replace(result, pat.regex, pat.replacement);
        } catch (...) {
            // In case of any regex error, continue gracefully
        }
    }

    return result;
}

bool Redaction::contains_secrets(const std::string& input) {
    const auto& patterns = get_patterns();
    for (const auto& pat : patterns) {
        try {
            if (std::regex_search(input, pat.regex)) {
                return true;
            }
        } catch (...) {}
    }
    return false;
}

} // namespace copyterm::core
