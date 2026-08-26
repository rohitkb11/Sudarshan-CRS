#include <cstdint>
#include <cstddef>
#include <vector>

bool parse_packet(const uint8_t* data, size_t size, std::vector<uint8_t>& out);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    std::vector<uint8_t> payload;
    parse_packet(data, size, payload);
    return 0;
}
