#include <iostream>

struct Item {
    int value;
};

void trigger_uaf(int val) {
    Item* item = new Item{val};
    delete item;

    // VULNERABILITY: object is accessed after its lifetime ended.
    std::cout << "value=" << item->value << "\n";
}

#ifndef CRS_FUZZING
int main() {
    trigger_uaf(42);
    return 0;
}
#endif
