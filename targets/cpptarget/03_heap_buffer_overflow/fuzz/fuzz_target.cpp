#include <cstdint>
#include <cstddef>

void process(const char* data, size_t size);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    process(reinterpret_cast<const char*>(data), size);
    return 0;
}
