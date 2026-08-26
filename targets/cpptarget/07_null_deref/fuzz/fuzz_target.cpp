#include <cstdint>
#include <cstddef>

int read_value(const char* p);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    const char* p = nullptr;
    if (size > 0 && data[0] == 'V') {
        static const char val = 'B';
        p = &val;
    }
    read_value(p);
    return 0;
}
