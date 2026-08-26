#include <iostream>
#include <new>
#include <sstream>
#include <cstring>

void process(const char* data, size_t size) {
    std::string s(data, size);
    std::istringstream iss(s);
    size_t length = 0;
    if (!(iss >> length)) return;

    char* buf = new char[16];
    iss.ignore();
    iss.read(buf, static_cast<std::streamsize>(length));
    delete[] buf;
}

#ifndef CRS_FUZZING
int main() {
    size_t length;
    if (!(std::cin >> length)) return 1;

    char* buf = new char[16];
    std::cin.ignore();
    std::cin.read(buf, static_cast<std::streamsize>(length));

    std::cout << "Read complete\n";
    delete[] buf;
}
#endif
