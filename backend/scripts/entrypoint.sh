#!/usr/bin/env bash
set -euo pipefail

# Run one-time startup tasks before spawning uvicorn workers.
# Ensures the search index exists (with retry for MI sidecar readiness).
python -m app.core.startup

# Hand off to uvicorn — exec replaces this shell so signals propagate.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
