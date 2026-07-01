FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies without the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy source
COPY src/ src/

# Install the project
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Transport: stdio (default) | sse | streamable-http
ENV MCP_TRANSPORT=stdio
# SSE / streamable-http bind address and port
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Expose HTTP port (used only when MCP_TRANSPORT=sse or streamable-http)
EXPOSE 8000

ENTRYPOINT ["plex-mcp"]
