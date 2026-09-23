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

# Tesseract OCR engine is a system dependency, not a pip package.
#
# tesseract-ocr-eng is listed EXPLICITLY and must stay: on Debian the English
# traineddata lives in its own package that is only a *Recommends* of
# tesseract-ocr. With --no-install-recommends (used here to keep the image
# small) it is silently skipped, leaving a tesseract binary that starts fine
# but fails every image with "Failed loading language 'eng'" - which surfaces
# as a scan that detects no text at all.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Fail the BUILD, not production, when OCR is not actually usable: the binary
# must be on PATH and the English traineddata present. Without this check a
# broken OCR setup only shows up as "no text detected" on a live scan.
RUN tesseract --version && tesseract --list-langs | grep -qx eng

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
