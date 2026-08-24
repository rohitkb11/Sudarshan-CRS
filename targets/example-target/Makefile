CC ?= clang
MODE ?= sanitized
CFLAGS = -Wall -Wextra -Werror -g -O1
ifeq ($(MODE),sanitized)
CFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
endif

build: build/parser

build/parser: src/parser.c
	@mkdir -p build
	$(CC) $(CFLAGS) -o $@ $<

clean:
	@rm -rf build
