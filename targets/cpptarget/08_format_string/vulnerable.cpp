#include <cstdio>
#include <iostream>
#include <string>

void print_msg(const char* msg) {
    // VULNERABILITY: attacker-controlled input becomes a format string.
    std::printf(msg);
    std::printf("\n");
}

#ifndef CRS_FUZZING
int main() {
    std::string message;
    std::getline(std::cin, message);
    print_msg(message.c_str());
    return 0;
}
#endif
