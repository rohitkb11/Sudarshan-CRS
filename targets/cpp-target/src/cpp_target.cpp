#include <iostream>
#include <cstring>

void process_input(const char *input) {
    char buffer[16];
    // Custom non-standard copy pattern that bypasses simple static rule matching
    // requiring true LLM reasoning (Groq Qwen/Llama) to understand and patch!
    for (size_t i = 0; input[i] != '\0'; i++) {
        buffer[i] = input[i];
    }
    std::cout << "Processed: " << buffer << std::endl;
}

#ifndef CRS_FUZZING
int main(int argc, char **argv) {
    if (argc > 1) {
        process_input(argv[1]);
    }
    return 0;
}
#endif
