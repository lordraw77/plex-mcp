IMAGE      := lordraw/plex-mcp
VERSION    := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "dev")
MCP_PORT   ?= 8000

.PHONY: all build push release run run-sse run-http test lint clean

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

## Run the container with stdio transport (requires PLEX_SERVER_URL and PLEX_TOKEN env vars)
run:
	docker run --rm -i \
		-e PLEX_SERVER_URL=$(PLEX_SERVER_URL) \
		-e PLEX_TOKEN=$(PLEX_TOKEN) \
		-e MCP_TRANSPORT=stdio \
		$(IMAGE):latest

## Run the container with SSE transport on port MCP_PORT (default: 8000)
run-sse:
	docker run --rm \
		-e PLEX_SERVER_URL=$(PLEX_SERVER_URL) \
		-e PLEX_TOKEN=$(PLEX_TOKEN) \
		-e MCP_TRANSPORT=sse \
		-e MCP_HOST=0.0.0.0 \
		-e MCP_PORT=$(MCP_PORT) \
		-p $(MCP_PORT):$(MCP_PORT) \
		$(IMAGE):latest

## Run the container with streamable-http transport on port MCP_PORT (default: 8000)
run-http:
	docker run --rm \
		-e PLEX_SERVER_URL=$(PLEX_SERVER_URL) \
		-e PLEX_TOKEN=$(PLEX_TOKEN) \
		-e MCP_TRANSPORT=streamable-http \
		-e MCP_HOST=0.0.0.0 \
		-e MCP_PORT=$(MCP_PORT) \
		-p $(MCP_PORT):$(MCP_PORT) \
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
