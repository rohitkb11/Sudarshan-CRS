#include <cstdint>
#include <cstddef>

void trigger_double_free(int x);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    trigger_double_free(static_cast<int>(data[0]));
    return 0;
}
