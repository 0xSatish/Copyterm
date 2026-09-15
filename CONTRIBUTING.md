# Contributing to COPYTERM

Thank you for your interest in contributing to `copyterm`!

---

## 1. Development Environment Setup

### Prerequisites
- **C++ Compiler:** C++17 compatible compiler (Clang 12+, GCC 9+, or MSVC 2019+).
- **Build System:** CMake 3.15+ or the provided platform build scripts (`scripts/build.ps1`, `scripts/build.sh`).
- **PowerShell / Bash:** For running automated integration tests.

### Building
```bash
# Windows
.\scripts\build.ps1

# Linux / macOS
./scripts/build.sh
```

---

## 2. Running Tests

Always ensure the complete test suite passes before submitting a pull request:

```bash
# Run unit tests
.\copyterm_tests.exe

# Run 30-terminal isolation integration test
powershell -ExecutionPolicy Bypass -File scripts/test_isolation_30_terminals.ps1
```

---

## 3. Pull Request Guidelines

1. Ensure code follows modern C++17 best practices (RAII, `std::optional`, `std::filesystem`, strong typing).
2. Avoid external library dependencies. `copyterm` must remain a lightweight, single-binary distribution.
3. Every new feature must include corresponding automated unit tests.
4. Update documentation in `docs/` and `README.md` if CLI flags or platform behaviors change.
