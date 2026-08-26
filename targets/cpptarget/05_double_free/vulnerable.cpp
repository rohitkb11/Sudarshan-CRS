#include <iostream>

void trigger_double_free(int x) {
    int* data = new int[8];
    data[0] = x;
    std::cout << data[0] << "\n";

    delete[] data;

    // VULNERABILITY: the same allocation is freed twice.
    delete[] data;
}

#ifndef CRS_FUZZING
int main() {
    trigger_double_free(123);
    return 0;
}
#endif
