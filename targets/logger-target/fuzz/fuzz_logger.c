#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "logger.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 4096) {
        return 0;
    }

    char *input = malloc(size + 1);
    if (input == NULL) {
        return 0;
    }

    memcpy(input, data, size);
    input[size] = '\0';
    (void)log_event(input);
    free(input);
    return 0;
}
