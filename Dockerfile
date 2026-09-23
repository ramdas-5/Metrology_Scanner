# Backend image for the merged Metrology Scanner project.
#
# This Dockerfile lives at the project root because the repository contains
# BOTH apps: the FastAPI backend in app/ and the React frontend in src/.
# Only the backend belongs in this image - .dockerignore excludes node_modules,
# src/, index.html, package.json and the env files (the frontend is built by
# Vercel from the same repository).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Tesseract OCR engine is a system dependency, not a pip package
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend sources (app/, scripts/, tests/, seed_admin.py) + the trained
# classifier in app/ml. See .dockerignore for what is excluded.
COPY . .

# Writable storage for uploads / generated reports. On a host with an
# ephemeral filesystem mount a persistent disk here (see render.yaml) or the
# images will be lost on every redeploy.
RUN mkdir -p app/uploads app/reports

# Render (and most PaaS hosts) inject the port to listen on.
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
