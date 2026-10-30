# ==============================================================================
# NIRIKSHA (Problem Statement 26262) - Multi-Stage Production Dockerfile
# Stage 1: Build React 19 Frontend SPA
# Stage 2: Minimalist, Hardened Python 3.12-slim Runtime
# ==============================================================================

# ----------------- STAGE 1: FRONTEND BUILDER -----------------
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Copy frontend package manifests and install
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source code and compile optimized production bundle
COPY frontend/ ./
RUN npm run build

# ----------------- STAGE 2: PRODUCTION RUNTIME -----------------
FROM python:3.12-slim AS runtime

# Set non-interactive environment & Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    WEB_CONCURRENCY=4

WORKDIR /app

# Install minimal OS runtime dependencies (libpq for postgres, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create unprivileged production system user for security compliance
RUN groupadd -g 1001 niriksha && \
    useradd -u 1001 -g niriksha -m -s /bin/bash niriksha

# Copy backend application code & configuration
COPY app/ ./app/
COPY synthetic_data/ ./synthetic_data/
COPY gunicorn.conf.py .
COPY run_production.py .

# Copy built frontend bundle from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /build/dist ./frontend/dist

# Ensure permissions for runtime uploads and data directories
RUN mkdir -p uploads synthetic_data && \
    chown -R niriksha:niriksha /app

USER niriksha

# Container liveness healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

EXPOSE 8000

# Start enterprise production server with Gunicorn ASGI workers
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
