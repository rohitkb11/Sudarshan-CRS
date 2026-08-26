/**
 * AI Kavach CRS — Generic libFuzzer Harness Template
 * Reusable harness entrypoint for target functions conforming to LLVMFuzzerTestOneInput.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Forward declaration of target interface
#ifdef __cplusplus
extern "C" {
#endif

// Weak default implementation or target function prototype
int target_entrypoint(const char *buffer, size_t len) __attribute__((weak));

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0 || size > 4096) {
        return 0;
    }

    char *null_terminated = (char *)malloc(size + 1);
    if (null_terminated == NULL) {
        return 0;
    }

    memcpy(null_terminated, data, size);
    null_terminated[size] = '\0';

    if (target_entrypoint) {
        (void)target_entrypoint(null_terminated, size);
    }

    free(null_terminated);
    return 0;
}

#ifdef __cplusplus
}
#endif
