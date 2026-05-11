# syntax=docker/dockerfile:1.7
# =============================================================================
# Nexus-Diagnostix — Backend Dockerfile (multi-stage)
# =============================================================================

# -------- Base système -------------------------------------------------------
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système (WeasyPrint + runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        fonts-liberation \
        curl \
    && rm -rf /var/lib/apt/lists/*

# -------- Development --------------------------------------------------------
FROM base AS development

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -------- Builder (venv isolé) -----------------------------------------------
FROM base AS builder

# build-essential uniquement dans le builder, pas dans le runtime final
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Créer le virtualenv et installer les dépendances
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copier pyproject.toml PUIS le source complet pour construire le package
COPY pyproject.toml ./
COPY . .
RUN pip install --upgrade pip && pip install --no-cache-dir .

# -------- Production ---------------------------------------------------------
FROM base AS production

RUN useradd --create-home --shell /bin/bash --uid 1000 nexus

WORKDIR /app

# Copier le virtualenv depuis le builder (pas les outils de build)
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copier le code source
COPY --chown=nexus:nexus . .

USER nexus

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
