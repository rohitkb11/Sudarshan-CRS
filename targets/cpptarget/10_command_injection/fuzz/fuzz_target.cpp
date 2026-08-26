#include <cstdint>
#include <cstddef>
#include <string>

void execute_user(const std::string& name);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    std::string s(reinterpret_cast<const char*>(data), size);
    execute_user(s);
    return 0;
}
