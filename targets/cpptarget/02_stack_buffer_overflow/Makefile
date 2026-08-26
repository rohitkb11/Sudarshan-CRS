CXX ?= clang++
MODE ?= sanitized
BUILD_DIR = build/$(MODE)
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O1 -I.

ifeq ($(MODE),sanitized)
CXXFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
endif

ifeq ($(MODE),fuzzer)
CXXFLAGS += -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer -DCRS_FUZZING
endif

build: $(BUILD_DIR)/parser

fuzz: $(BUILD_DIR)/parser_fuzzer

$(BUILD_DIR)/parser: vulnerable.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BUILD_DIR)/parser_fuzzer: vulnerable.cpp fuzz/fuzz_target.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	@rm -rf build
