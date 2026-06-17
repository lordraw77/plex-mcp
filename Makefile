IMAGE   := lordraw/plex-mcp
VERSION := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "dev")

.PHONY: all build push release test lint clean

all: build

## Build the Docker image
build:
	docker build -t $(IMAGE):$(VERSION) -t $(IMAGE):latest .

## Push to Docker Hub
push:
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

## Build + push in one shot
release: build push

## Run the container (requires PLEX_SERVER_URL and PLEX_TOKEN env vars)
run:
	docker run --rm -i \
		-e PLEX_SERVER_URL=$(PLEX_SERVER_URL) \
		-e PLEX_TOKEN=$(PLEX_TOKEN) \
		$(IMAGE):latest

## Run tests locally with uv
test:
	uv run pytest

## Lint with ruff (install with: uv add --dev ruff)
lint:
	uv run ruff check src/ tests/

## Remove local image
clean:
	docker rmi $(IMAGE):$(VERSION) $(IMAGE):latest || true
