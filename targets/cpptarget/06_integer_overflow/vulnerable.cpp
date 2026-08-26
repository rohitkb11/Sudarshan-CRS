#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

struct Packet {
    uint32_t count;
    std::vector<uint8_t> data;
};

bool parse(const uint8_t* input, size_t input_size, Packet& p) {
    if (input_size < 4) {
        return false;
    }

    uint32_t count =
        static_cast<uint32_t>(input[0]) |
        (static_cast<uint32_t>(input[1]) << 8) |
        (static_cast<uint32_t>(input[2]) << 16) |
        (static_cast<uint32_t>(input[3]) << 24);

    // BUG: multiplication can overflow.
    uint32_t allocation_size = count * 4;

    p.count = count;
    p.data.resize(allocation_size);

    // BUG: the program later assumes count*4 bytes are available.
    std::memcpy(p.data.data(), input + 4, count * 4);

    return true;
}

int main() {
    std::vector<uint8_t> input(
        (std::istreambuf_iterator<char>(std::cin)),
        std::istreambuf_iterator<char>());

    Packet p;

    if (!parse(input.data(), input.size(), p)) {
        std::cerr << "Invalid packet\n";
        return 1;
    }

    std::cout << "Parsed " << p.count << " items\n";
}