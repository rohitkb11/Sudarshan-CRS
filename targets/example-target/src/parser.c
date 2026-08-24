#include <stdio.h>
#include <string.h>

int parse_message(const char *input) {
    char buffer[16];
    strcpy(buffer, input);
    return buffer[0] == '!' ? 1 : 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <message>\n", argv[0]);
        return 64;
    }
    return parse_message(argv[1]);
}
