# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root unprivileged service user
RUN groupadd -g 10001 mcp && \
    useradd -u 10001 -g mcp -s /bin/bash -m mcpuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/splunk-mcp /usr/local/bin/splunk-mcp
COPY --chown=mcpuser:mcp src/ ./src/
COPY --chown=mcpuser:mcp .env.example ./

USER mcpuser

# STDIO or SSE port
EXPOSE 8001

ENTRYPOINT ["splunk-mcp"]
CMD ["--transport", "stdio"]
