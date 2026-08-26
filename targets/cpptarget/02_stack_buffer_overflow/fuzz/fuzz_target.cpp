#include <cstdint>
#include <cstddef>
#include <string>

void copy_name(const std::string& name);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    std::string input(reinterpret_cast<const char*>(data), size);
    copy_name(input);
    return 0;
}
