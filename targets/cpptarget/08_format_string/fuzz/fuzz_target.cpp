#include <cstdint>
#include <cstddef>
#include <string>

void print_msg(const char* msg);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    std::string s(reinterpret_cast<const char*>(data), size);
    print_msg(s.c_str());
    return 0;
}
