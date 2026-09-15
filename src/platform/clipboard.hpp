#pragma once

#include <string>
#include <optional>

namespace copyterm::platform {

enum class ClipboardBackend {
    Win32,
    Wayland,
    X11,
    Osc52,
    None
};

class Clipboard {
public:
    // Copies UTF-8 text directly to the system clipboard
    static bool copy(const std::string& text, std::string* error_msg = nullptr);

    // Emits OSC 52 clipboard escape sequence directly to the active terminal
    static bool copy_osc52(const std::string& text);

    // Detects the active clipboard backend
    static ClipboardBackend detect_backend();

    // Returns a human-readable name of the active clipboard backend
    static std::string get_backend_name();

    // Checks if a clipboard provider is accessible
    static bool is_available();
};

} // namespace copyterm::platform
