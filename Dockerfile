# ==============================================================================
# JudiQ AI — Production Multi-Stage Dockerfile
# ==============================================================================

# ── Stage 1: Build Python dependencies ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System libraries needed to compile psycopg2 and cryptography wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into user-local site-packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ── Stage 2: Production runtime image ─────────────────────────────────────────
FROM python:3.11-slim AS runner

# System libraries needed at runtime:
#   - libpq5          : PostgreSQL client (psycopg2-binary)
#   - tesseract-ocr   : OCR engine for scanned documents
#   - poppler-utils   : pdf2image depends on pdftoppm (Poppler)
#   - libgl1          : PyMuPDF / Pillow headless rendering
#   - curl            : health check probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user for container security compliance
RUN groupadd -g 1001 appgroup && \
    useradd  -u 1001 -g appgroup -s /bin/bash -m appuser

# Copy compiled Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Python runtime tunables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy backend application source
COPY --chown=appuser:appgroup backend /app/backend

# Copy frontend static assets (served by FastAPI StaticFiles mount)
COPY --chown=appuser:appgroup frontend /app/frontend

# Copy root-level entrypoint shim so Gunicorn can find main:app
COPY --chown=appuser:appgroup main.py /app/main.py

RUN chown -R appuser:appgroup /app

USER appuser

# Render injects $PORT at runtime. Default to 8000 for local Docker runs.
ENV PORT=8000
EXPOSE 8000

# Health check — Render and Docker both use this
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ready || exit 1

# ── Gunicorn + Uvicorn worker ──────────────────────────────────────────────────
# -w 1          : single worker keeps in-memory WebSocket state consistent
# --timeout 180 : allow long OCR + LLM extraction requests (up to 3 min)
# --graceful-timeout 30 : clean shutdown window for in-flight requests
# main:app      : uses root /app/main.py shim which imports backend/main.py
CMD gunicorn \
      -w 1 \
      -k uvicorn.workers.UvicornWorker \
      -b 0.0.0.0:${PORT} \
      --timeout 180 \
      --graceful-timeout 30 \
      --keep-alive 5 \
      --log-level info \
      --access-logfile - \
      --error-logfile - \
      main:app
