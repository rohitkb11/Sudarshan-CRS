CXX ?= clang++
MODE ?= sanitized
BUILD_DIR = build/$(MODE)
CXXFLAGS = -Wall -Wextra -Werror -g -O1 -Isrc

ifeq ($(MODE),sanitized)
CXXFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
endif

ifeq ($(MODE),fuzzer)
CXXFLAGS += -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer -DCRS_FUZZING
endif

build: $(BUILD_DIR)/parser

fuzz: $(BUILD_DIR)/parser_fuzzer

$(BUILD_DIR)/parser: src/cpp_target.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BUILD_DIR)/parser_fuzzer: src/cpp_target.cpp fuzz/fuzz_cpp_target.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	@rm -rf build
