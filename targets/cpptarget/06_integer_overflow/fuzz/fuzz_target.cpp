#include <cstdint>
#include <cstddef>

void process_count(uint32_t count, const char* data, size_t data_len);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(uint32_t)) return 0;
    uint32_t count = *reinterpret_cast<const uint32_t*>(data);
    process_count(count, reinterpret_cast<const char*>(data + sizeof(uint32_t)), size - sizeof(uint32_t));
    return 0;
}
