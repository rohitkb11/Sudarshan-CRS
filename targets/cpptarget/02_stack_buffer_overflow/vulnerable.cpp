#include <cstring>
#include <iostream>
#include <string>

void copy_name(const std::string& name) {
    char buffer[16];

    // VULNERABILITY: unbounded copy into a fixed-size stack buffer.
    std::strcpy(buffer, name.c_str());

    std::cout << "Name: " << buffer << "\n";
}

#ifndef CRS_FUZZING
int main() {
    std::string input;
    std::getline(std::cin, input);
    copy_name(input);
}
#endif
