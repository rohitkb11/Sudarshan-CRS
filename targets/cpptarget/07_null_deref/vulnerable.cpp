#include <cstdlib>
#include <iostream>

int read_value(const char* p) {
    // VULNERABILITY: p is dereferenced without validation.
    return *p;
}

#ifndef CRS_FUZZING
int main() {
    const char* p = nullptr;

    if (std::getenv("USE_VALUE")) {
        static const char value = 'A';
        p = &value;
    }

    std::cout << read_value(p) << "\n";
}
#endif
