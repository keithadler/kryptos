# Build the C searchers into bin/. Python needs only numpy.
CC ?= cc
CFLAGS ?= -O3

BINS = bin/trans bin/dfs bin/quag3 bin/sa

all: $(BINS)

bin/%: c/%.c
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $< -lm

verify: all
	python3 verify.py

clean:
	rm -rf bin __pycache__ checks/__pycache__

.PHONY: all verify clean
