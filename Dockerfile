# ═══════════════════════════════════════════════════════════════════
# CP2 — Containerization
# Production-ready Dockerfile
# ═══════════════════════════════════════════════════════════════════

# ===== Build stage =====
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Cài dependencies
RUN pip install \
    --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


# ===== Runtime stage =====
FROM python:3.11-slim

WORKDIR /app

# Tạo non-root user
RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser

# Copy dependencies từ builder
COPY --from=builder /install /usr/local

# Copy source code
COPY app ./app
COPY utils ./utils

# Chạy container bằng user thường
USER appuser

# Port mặc định
ENV PORT=8000

# Documentation
EXPOSE 8000

# Health check
HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD python -c "import os, urllib.request; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# Start FastAPI
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]