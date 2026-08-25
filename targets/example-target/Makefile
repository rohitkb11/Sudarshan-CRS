CC ?= clang
MODE ?= sanitized
BUILD_DIR = build/$(MODE)
CFLAGS = -Wall -Wextra -Werror -g -O1 -Isrc

ifeq ($(MODE),sanitized)
CFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
endif

ifeq ($(MODE),fuzzer)
CFLAGS += -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer -DCRS_FUZZING
endif

build: $(BUILD_DIR)/parser

fuzz: $(BUILD_DIR)/parser_fuzzer

$(BUILD_DIR)/parser: src/parser.c src/parser.h
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)/parser_fuzzer: src/parser.c src/parser.h fuzz/fuzz_parser.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ src/parser.c fuzz/fuzz_parser.c

clean:
	@rm -rf build
