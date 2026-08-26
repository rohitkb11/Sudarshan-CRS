#include <cstdint>
#include <cstdlib>
#include <cstring>

void process_input(const char *input);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 4096) return 0;
    char *input = (char *)malloc(size + 1);
    if (!input) return 0;
    memcpy(input, data, size);
    input[size] = '\0';
    process_input(input);
    free(input);
    return 0;
}
