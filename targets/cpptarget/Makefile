# Default forwarder to 01_oob_read benchmark
MODE ?= sanitized
CC ?= clang
CXX ?= clang++

build:
	@$(MAKE) -C 01_oob_read build MODE=$(MODE) CC=$(CC) CXX=$(CXX)
	@mkdir -p build/$(MODE)
	@cp 01_oob_read/build/$(MODE)/parser build/$(MODE)/parser

fuzz:
	@$(MAKE) -C 01_oob_read fuzz MODE=fuzzer CC=$(CC) CXX=$(CXX)
	@mkdir -p build/fuzzer
	@cp 01_oob_read/build/fuzzer/parser_fuzzer build/fuzzer/parser_fuzzer

clean:
	@rm -rf build
	@$(MAKE) -C 01_oob_read clean
