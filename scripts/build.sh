#!/usr/bin/env bash
# ==============================================================================
# Build Script for Linux / macOS (Bash)
# ==============================================================================
set -euo pipefail

CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -O2 -Isrc -Wall -Wextra"

echo "Building copyterm with ${CXX}..."

SRC_FILES=(
    src/platform/environment.cpp
    src/platform/process.cpp
    src/platform/clipboard.cpp
    src/core/session.cpp
    src/core/ring_buffer.cpp
    src/core/sanitizer.cpp
    src/core/redaction.cpp
    src/core/formatter.cpp
    src/installer/installer.cpp
    src/cli/cli_args.cpp
)

# Build copyterm CLI
echo "Compiling copyterm executable..."
${CXX} ${CXXFLAGS} src/cli/main.cpp "${SRC_FILES[@]}" -o copyterm

# Build copyterm_tests
echo "Compiling copyterm_tests..."
TEST_FILES=(
    tests/test_main.cpp
    tests/test_session.cpp
    tests/test_ring_buffer.cpp
    tests/test_sanitizer.cpp
    tests/test_redaction.cpp
    tests/test_formatter.cpp
    tests/test_isolation.cpp
)
${CXX} ${CXXFLAGS} "${TEST_FILES[@]}" "${SRC_FILES[@]}" -o copyterm_tests

echo ""
echo "Build successful!"
echo "  -> Binaries: ./copyterm, ./copyterm_tests"
