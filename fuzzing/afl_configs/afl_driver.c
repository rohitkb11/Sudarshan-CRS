/**
 * AI Kavach CRS — AFL++ Persistent Mode Driver
 * Translates AFL++ stdin/file input into LLVMFuzzerTestOneInput invocations.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

extern int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

#define MAX_INPUT_SIZE 65536
static uint8_t buffer[MAX_INPUT_SIZE];

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

#ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT();
#endif

    while (__AFL_LOOP(10000)) {
        ssize_t length = read(0, buffer, sizeof(buffer));
        if (length > 0) {
            LLVMFuzzerTestOneInput(buffer, (size_t)length);
        }
    }

    return 0;
}
