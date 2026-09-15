#include <iostream>
#include <vector>
#include <string>
#include <functional>
#include <cassert>

// Test functions forward declarations
void run_session_tests();
void run_ring_buffer_tests();
void run_sanitizer_tests();
void run_redaction_tests();
void run_formatter_tests();
void run_isolation_tests();

struct TestCase {
    std::string name;
    std::function<void()> func;
};

int main(int argc, char* argv[]) {
    std::cout << "============================================================\n";
    std::cout << "               COPYTERM COMPREHENSIVE TEST SUITE            \n";
    std::cout << "============================================================\n\n";

    std::vector<TestCase> suites = {
        { "Session Identity & Metadata Tests", run_session_tests },
        { "Bounded Ring Buffer Tests", run_ring_buffer_tests },
        { "ANSI & VT Sanitizer Tests", run_sanitizer_tests },
        { "Secret Redaction Tests", run_redaction_tests },
        { "Output Formatter Tests", run_formatter_tests },
        { "30-Terminal Session Isolation Tests", run_isolation_tests }
    };

    size_t passed = 0;
    size_t failed = 0;

    for (const auto& suite : suites) {
        std::cout << "[RUNNING] " << suite.name << "...\n";
        try {
            suite.func();
            std::cout << "  --> [PASS] " << suite.name << "\n\n";
            passed++;
        } catch (const std::exception& e) {
            std::cerr << "  --> [FAIL] " << suite.name << ": " << e.what() << "\n\n";
            failed++;
        } catch (...) {
            std::cerr << "  --> [FAIL] " << suite.name << ": Unknown exception\n\n";
            failed++;
        }
    }

    std::cout << "============================================================\n";
    std::cout << "TEST RESULTS: " << passed << " passed, " << failed << " failed (Total: " << suites.size() << ")\n";
    std::cout << "============================================================\n";

    return (failed == 0) ? 0 : 1;
}
