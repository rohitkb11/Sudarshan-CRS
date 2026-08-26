#include <cstdint>
#include <cstddef>
#include <string>

void open_sandbox(const std::string& filename);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    std::string s(reinterpret_cast<const char*>(data), size);
    open_sandbox(s);
    return 0;
}
