cmake_minimum_required(VERSION 3.15)
project(copyterm VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Common sources
set(COPYTERM_LIB_SOURCES
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

# CLI Binary Target
add_executable(copyterm
    src/cli/main.cpp
    ${COPYTERM_LIB_SOURCES}
)

target_include_directories(copyterm PRIVATE src)

if(WIN32)
    target_link_libraries(copyterm PRIVATE user32 kernel32 advapi32)
endif()

# Tests Target
add_executable(copyterm_tests
    tests/test_main.cpp
    tests/test_session.cpp
    tests/test_ring_buffer.cpp
    tests/test_sanitizer.cpp
    tests/test_redaction.cpp
    tests/test_formatter.cpp
    tests/test_isolation.cpp
    ${COPYTERM_LIB_SOURCES}
)

target_include_directories(copyterm_tests PRIVATE src)

if(WIN32)
    target_link_libraries(copyterm_tests PRIVATE user32 kernel32 advapi32)
endif()

# Enable CTest
enable_testing()
add_test(NAME ComprehensiveTests COMMAND copyterm_tests)
