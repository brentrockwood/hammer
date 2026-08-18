HAMMER_COMMIT := $(shell git rev-parse HEAD)

.PHONY: build test

build:
	HAMMER_COMMIT=$(HAMMER_COMMIT) docker compose build

test:
	python3 -m unittest discover -s tests -v
