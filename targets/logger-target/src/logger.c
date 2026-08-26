#include <stdio.h>
#include <string.h>

#include "logger.h"

int log_event(const char *input) {
    char buffer[16];
    sprintf(buffer, "%s", input);
    return buffer[0] == '#' ? 1 : 0;
}

#ifndef CRS_FUZZING
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <event_msg>\n", argv[0]);
        return 64;
    }
    return log_event(argv[1]);
}
#endif
