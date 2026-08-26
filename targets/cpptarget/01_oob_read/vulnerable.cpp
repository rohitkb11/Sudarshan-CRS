#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

bool parse_packet(const uint8_t* data, size_t size, std::vector<uint8_t>& out) {
    if (size < 2) return false;

    uint16_t length = static_cast<uint16_t>(data[0]) |
                      (static_cast<uint16_t>(data[1]) << 8);

    out.resize(length);

    // VULNERABILITY: attacker-controlled length is not bounded by input size.
    std::memcpy(out.data(), data + 2, length);
    return true;
}

#ifndef CRS_FUZZING
int main() {
    std::vector<uint8_t> input(
        (std::istreambuf_iterator<char>(std::cin)),
        std::istreambuf_iterator<char>());

    std::vector<uint8_t> payload;
    if (!parse_packet(input.data(), input.size(), payload)) {
        std::cerr << "Invalid packet\n";
        return 1;
    }

    std::cout << "Parsed " << payload.size() << " bytes\n";
}
#endif
