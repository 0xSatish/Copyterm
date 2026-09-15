#include "clipboard.hpp"
#include "environment.hpp"

#include <iostream>
#include <sstream>
#include <vector>
#include <cstdio>
#include <cstring>

#if defined(_WIN32) || defined(_WIN64)
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#else
    #include <unistd.h>
#endif

namespace copyterm::platform {

namespace {
// Simple Base64 encoder for OSC 52
std::string base64_encode(const std::string& in) {
    static const char* b64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    int val = 0, valb = -6;
    for (unsigned char c : in) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            out.push_back(b64_chars[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    if (valb > -6) out.push_back(b64_chars[((val << 8) >> (valb + 8)) & 0x3F]);
    while (out.size() % 4) out.push_back('=');
    return out;
}

#if !defined(_WIN32) && !defined(_WIN64)
bool run_pipe_command(const std::string& cmd, const std::string& input) {
    FILE* pipe = popen(cmd.c_str(), "w");
    if (!pipe) return false;
    size_t written = fwrite(input.data(), 1, input.size(), pipe);
    int status = pclose(pipe);
    return (status == 0 && written == input.size());
}

bool command_exists(const std::string& cmd) {
    std::string check = "which " + cmd + " >/dev/null 2>&1";
    return system(check.c_str()) == 0;
}
#endif
} // namespace

ClipboardBackend Clipboard::detect_backend() {
#if defined(_WIN32) || defined(_WIN64)
    return ClipboardBackend::Win32;
#else
    if (Environment::get_env("WAYLAND_DISPLAY") && command_exists("wl-copy")) {
        return ClipboardBackend::Wayland;
    }
    if (Environment::get_env("DISPLAY")) {
        if (command_exists("xclip") || command_exists("xsel")) {
            return ClipboardBackend::X11;
        }
    }
    if (Environment::get_env("SSH_CONNECTION") || Environment::get_env("SSH_CLIENT")) {
        return ClipboardBackend::Osc52;
    }
    return ClipboardBackend::None;
#endif
}

std::string Clipboard::get_backend_name() {
    switch (detect_backend()) {
        case ClipboardBackend::Win32: return "Windows Clipboard (Win32 API)";
        case ClipboardBackend::Wayland: return "Linux Wayland (wl-copy)";
        case ClipboardBackend::X11: return "Linux X11 (xclip/xsel)";
        case ClipboardBackend::Osc52: return "OSC 52 (Terminal Escape Sequence)";
        case ClipboardBackend::None: return "None (Unavailable)";
    }
    return "Unknown";
}

bool Clipboard::is_available() {
    return detect_backend() != ClipboardBackend::None;
}

bool Clipboard::copy_osc52(const std::string& text) {
    std::string encoded = base64_encode(text);
    std::string osc52_seq = "\x1b]52;c;" + encoded + "\x07";
    std::cout << osc52_seq << std::flush;
    return true;
}

bool Clipboard::copy(const std::string& text, std::string* error_msg) {
#if defined(_WIN32) || defined(_WIN64)
    if (!OpenClipboard(nullptr)) {
        if (error_msg) *error_msg = "Failed to open Win32 clipboard (error code: " + std::to_string(GetLastError()) + ")";
        return false;
    }

    if (!EmptyClipboard()) {
        CloseClipboard();
        if (error_msg) *error_msg = "Failed to empty clipboard";
        return false;
    }

    // Convert UTF-8 to UTF-16
    int wide_len = MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, nullptr, 0);
    if (wide_len <= 0) {
        CloseClipboard();
        if (error_msg) *error_msg = "Failed to convert text to wide characters";
        return false;
    }

    HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, static_cast<size_t>(wide_len) * sizeof(wchar_t));
    if (!hMem) {
        CloseClipboard();
        if (error_msg) *error_msg = "Failed to allocate global memory for clipboard";
        return false;
    }

    wchar_t* pWide = static_cast<wchar_t*>(GlobalLock(hMem));
    if (!pWide) {
        GlobalFree(hMem);
        CloseClipboard();
        if (error_msg) *error_msg = "Failed to lock global memory";
        return false;
    }

    MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, pWide, wide_len);
    GlobalUnlock(hMem);

    if (SetClipboardData(CF_UNICODETEXT, hMem) == nullptr) {
        GlobalFree(hMem);
        CloseClipboard();
        if (error_msg) *error_msg = "Failed to set clipboard data (error code: " + std::to_string(GetLastError()) + ")";
        return false;
    }

    CloseClipboard();
    return true;

#else
    ClipboardBackend backend = detect_backend();
    if (backend == ClipboardBackend::Wayland) {
        if (run_pipe_command("wl-copy", text)) {
            return true;
        }
    } else if (backend == ClipboardBackend::X11) {
        if (command_exists("xclip")) {
            if (run_pipe_command("xclip -selection clipboard", text)) return true;
        }
        if (command_exists("xsel")) {
            if (run_pipe_command("xsel --clipboard --input", text)) return true;
        }
    }

    // If running in SSH or terminal supports OSC 52, attempt OSC 52
    if (Environment::is_stdout_tty()) {
        copy_osc52(text);
        return true;
    }

    if (error_msg) {
        *error_msg = "No supported clipboard tool found (install wl-clipboard, xclip, or xsel, or use --save <file>)";
    }
    return false;
#endif
}

} // namespace copyterm::platform
