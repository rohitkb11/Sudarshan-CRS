#include <iostream>
#include <cstring>

// Safely copy input into a fixed-size buffer.
void process_input(const char *input) {
    // Buffer size is 16 bytes; reserve one byte for the terminating NUL.
    char buffer[16];
    // Use strncpy to copy at most sizeof(buffer)-1 characters.
    // This prevents writing past the end of the array.
    std::strncpy(buffer, input, sizeof(buffer) - 1);
    // Ensure the destination string is NUL-terminated.
    buffer[sizeof(buffer) - 1] = '\0';
    // (Optional) Do something with buffer here.
    // For demonstration, we simply print it.
    std::cout << "Processed input: " << buffer << std::endl;
}

#ifndef CRS_FUZZING
int main(int argc, char **argv) {
    if (argc > 1) {
        process_input(argv[1]);
    }
    return 0;
}
#endif
