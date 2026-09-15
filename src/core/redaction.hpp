#pragma once

#include <string>
#include <vector>

namespace copyterm::core {

struct RedactionStats {
    size_t secrets_masked{0};
};

class Redaction {
public:
    // Redacts known sensitive patterns from input text
    static std::string redact(const std::string& input, RedactionStats* stats = nullptr);

    // Checks if input contains likely secrets
    static bool contains_secrets(const std::string& input);
};

} // namespace copyterm::core
