# -----------------------------------------------------------------------------
# Makefile for IMAGEWTY-Tool
# -----------------------------------------------------------------------------
# This Makefile compiles the IMAGEWTY-Tool project (a tool to analyze, unpack
# and repack Allwinner firmware images).
#
# Targets:
#   all       - Build the executable
#   clean     - Remove all build artifacts
#   install   - Install the binary to /usr/local/bin
#   uninstall - Remove the binary from /usr/local/bin
#   cleanobj  - Remove only object files
#   format    - Format all source/header files using clang-format
#   debug     - Build with sanitizers and debug info
# -----------------------------------------------------------------------------

# Compiler and flags
CC      = gcc
PYTHON  ?= python3
CPPFLAGS = -D_FILE_OFFSET_BITS=64 -D_POSIX_C_SOURCE=200809L -Iinclude
CFLAGS  = -Wall -Wextra -Wpedantic -std=c11 -O2
DEBUG_CFLAGS = -Wall -Wextra -Wpedantic -std=c11 -g -O0 -fsanitize=address,undefined -fno-omit-frame-pointer
LDFLAGS = 
.DEFAULT_GOAL := all

# Source files and objects
SRC = \
    src/main.c \
    src/img_header.c \
    src/img_extract.c \
    src/img_repack.c \
    src/checksum.c \
    src/config_file.c \
    src/print_info.c

OBJ = $(patsubst src/%.c,build/release/%.o,$(SRC))
DEBUG_OBJ = $(patsubst src/%.c,build/debug/%.o,$(SRC))
DEP = $(OBJ:.o=.d) $(DEBUG_OBJ:.o=.d)

# Binary name
BIN = imagewty-tool
DEBUG_BIN = build/debug/imagewty-tool

# Default target: build the binary
all: $(BIN)

test: $(BIN)
	sh tests/run_tests.sh "$(CURDIR)/$(BIN)"
	$(PYTHON) tests/test_demo.py "$(CURDIR)/$(BIN)"
	+sh tests/test_build.sh "$(CURDIR)"

test-debug: $(DEBUG_BIN)
	sh tests/run_tests.sh "$(CURDIR)/$(DEBUG_BIN)"
	$(PYTHON) tests/test_demo.py "$(CURDIR)/$(DEBUG_BIN)"

fixtures:
	$(PYTHON) scripts/generate_demo.py

check-fixtures:
	$(PYTHON) scripts/generate_demo.py --check

test-h713: $(BIN)
	sh tests/test_h713.sh "$(CURDIR)/$(BIN)"

# Link the binary from object files
$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDFLAGS)

$(DEBUG_BIN): $(DEBUG_OBJ)
	$(CC) $(DEBUG_CFLAGS) -o $@ $(DEBUG_OBJ) $(LDFLAGS)

build/release/%.o: src/%.c Makefile
	mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

build/debug/%.o: src/%.c Makefile
	mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(DEBUG_CFLAGS) -MMD -MP -c $< -o $@

-include $(DEP)

# Remove all object files and the binary
clean: cleanobj
	rm -f $(BIN) $(DEBUG_BIN)
	-rmdir build/release build/debug build

# Install the binary to /usr/local/bin (requires sudo)
install: $(BIN)
	install -m 755 $(BIN) /usr/local/bin/$(BIN)

# Remove the binary from /usr/local/bin (requires sudo)
uninstall:
	rm -f /usr/local/bin/$(BIN)

# Remove only object files
cleanobj:
	rm -f $(OBJ) $(DEBUG_OBJ) $(DEP) $(SRC:.c=.o)

# Automatically format all source and header files using clang-format
format:
	clang-format -i -style=file $(SRC) include/*.h

# Build with sanitizers and debug info (for development)
debug: $(DEBUG_BIN)

.PHONY: all test test-debug test-h713 fixtures check-fixtures clean install uninstall cleanobj format debug
