#include "../src/core/sanitizer.hpp"

#include <iostream>
#include <stdexcept>

void run_sanitizer_tests() {
    using namespace copyterm;

    // 1. Test ANSI color sequence stripping
    std::string colored = "\x1b[31mError: \x1b[1;32mBuild succeeded\x1b[0m with \x1b[38;2;255;100;0m2 warnings\x1b[m\n";
    std::string stripped = core::Sanitizer::strip_ansi(colored);
    if (stripped != "Error: Build succeeded with 2 warnings\n") {
        throw std::runtime_error("strip_ansi failed, got: " + stripped);
    }

    // 2. Test OSC title sequence stripping
    std::string osc_str = "\x1b]0;Current Directory: /home/user\x07Hello Terminal\n";
    std::string osc_cleaned = core::Sanitizer::strip_ansi(osc_str);
    if (osc_cleaned != "Hello Terminal\n") {
        throw std::runtime_error("strip_ansi failed for OSC sequence, got: " + osc_cleaned);
    }

    // 3. Test Carriage Return Overwrite (\r) Simulation (Progress Bars)
    std::string progress_bar = "[=>       ] 10%\r[=====>   ] 50%\r[=========] 100%\n";
    std::string collapsed = core::Sanitizer::collapse_carriage_returns(progress_bar);
    if (collapsed != "[=========] 100%\n") {
        throw std::runtime_error("collapse_carriage_returns failed on progress bar, got: " + collapsed);
    }

    // 4. Test Backspace (\b) handling
    std::string backspace_str = "abc\b\bXY\n";
    std::string bs_collapsed = core::Sanitizer::collapse_carriage_returns(backspace_str);
    if (bs_collapsed != "aXY\n") {
        throw std::runtime_error("collapse_carriage_returns failed on backspace, got: " + bs_collapsed);
    }

    // 5. Test Shell integration marker stripping
    std::string shell_marks = "\x1b]133;C;cmd=ls -la\x07$ ls -la\nfile1.txt\nfile2.txt\n";
    std::string marks_stripped = core::Sanitizer::strip_shell_integration_marks(shell_marks);
    if (marks_stripped != "$ ls -la\nfile1.txt\nfile2.txt\n") {
        throw std::runtime_error("strip_shell_integration_marks failed, got: " + marks_stripped);
    }

    // 6. Test full sanitize pipeline
    std::string complex_input = "\x1b[1;34m[=>  ] 20%\x1b[0m\r\x1b[1;32m[====] 100%\x1b[0m\r\n";
    std::string sanitized = core::Sanitizer::sanitize(complex_input);
    if (sanitized != "[====] 100%\n") {
        throw std::runtime_error("Full sanitize pipeline failed, got: " + sanitized);
    }
}
