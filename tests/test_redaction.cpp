#include "../src/core/redaction.hpp"

#include <iostream>
#include <stdexcept>

void run_redaction_tests() {
    using namespace copyterm;

    // 1. Test AWS Access Key Redaction
    std::string text_aws = "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n";
    core::RedactionStats stats1;
    std::string redacted_aws = core::Redaction::redact(text_aws, &stats1);

    if (redacted_aws.find("AKIAIOSFODNN7EXAMPLE") != std::string::npos) {
        throw std::runtime_error("AWS key was not redacted");
    }
    if (redacted_aws.find("AKIA[REDACTED_AWS_KEY]") == std::string::npos) {
        throw std::runtime_error("AWS key replacement marker missing");
    }
    if (stats1.secrets_masked == 0) {
        throw std::runtime_error("Redaction stats failed to count masked secret");
    }

    // 2. Test GitHub Token Redaction
    std::string text_gh = "git clone https://ghp_123456789012345678901234567890123456@github.com/repo\n";
    std::string redacted_gh = core::Redaction::redact(text_gh);
    if (redacted_gh.find("ghp_1234567890") != std::string::npos) {
        throw std::runtime_error("GitHub token was not redacted");
    }

    // 3. Test Private Key Redaction
    std::string text_pk = "Certificate:\n-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----\nDone\n";
    std::string redacted_pk = core::Redaction::redact(text_pk);
    if (redacted_pk.find("MIIEowIBAAKCAQEA0") != std::string::npos) {
        throw std::runtime_error("Private key body was not redacted");
    }

    // 4. Test Password Assignment Redaction
    std::string text_pw = "Connecting with password=\"super_secret_pass123\"\n";
    std::string redacted_pw = core::Redaction::redact(text_pw);
    if (redacted_pw.find("super_secret_pass123") != std::string::npos) {
        throw std::runtime_error("Password assignment was not redacted");
    }

    // 5. Test contains_secrets
    if (!core::Redaction::contains_secrets("token = ghp_123456789012345678901234567890123456")) {
        throw std::runtime_error("contains_secrets failed on valid token");
    }
    if (core::Redaction::contains_secrets("echo normal terminal message")) {
        throw std::runtime_error("contains_secrets false positive on benign text");
    }
}
