#include <cstdint>
#include <cstddef>

void trigger_uaf(int val);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(int)) return 0;
    int val = *reinterpret_cast<const int*>(data);
    trigger_uaf(val);
    return 0;
}
