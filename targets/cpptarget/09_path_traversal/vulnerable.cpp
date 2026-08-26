#include <fstream>
#include <iostream>
#include <string>

void open_sandbox(const std::string& filename) {
    const std::string base = "sandbox_files/";
    const std::string path = base + filename;

    // VULNERABILITY: user-controlled path can escape the intended directory.
    std::ifstream file(path);
    if (!file) {
        std::cerr << "Could not open file\n";
        return;
    }
    std::cout << file.rdbuf();
}

#ifndef CRS_FUZZING
int main() {
    std::string filename;
    std::getline(std::cin, filename);
    open_sandbox(filename);
    return 0;
}
#endif
