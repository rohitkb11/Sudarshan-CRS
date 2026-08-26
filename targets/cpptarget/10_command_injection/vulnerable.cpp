#include <cstdlib>
#include <iostream>
#include <string>

void execute_user(const std::string& name) {
    // VULNERABILITY: attacker-controlled input reaches a shell command.
    std::string command = "echo " + name;
    std::system(command.c_str());
}

#ifndef CRS_FUZZING
int main() {
    std::string name;
    std::getline(std::cin, name);
    execute_user(name);
    return 0;
}
#endif
