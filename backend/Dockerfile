# Stage 1: Install dependencies
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Base runner
FROM python:3.12-slim AS base
WORKDIR /app

RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup --create-home appuser

COPY --from=builder /app/.venv /app/.venv
COPY app/ ./app/
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# Stage 3: Development runner (az CLI for DefaultAzureCredential via az login)
FROM base AS development
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg && \
    curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ bookworm main" \
      > /etc/apt/sources.list.d/azure-cli.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends azure-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Production runner (no dev tools, multi-worker)
FROM base AS production
USER appuser
CMD ["./scripts/entrypoint.sh"]
