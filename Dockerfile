# =========================
# Stage 1: Build React (Vite) frontend
# =========================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy rest of frontend source and build
COPY frontend/ .
RUN npm run build

# =========================
# Stage 2: Python + Flask backend (serves built frontend)
# =========================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (adjust if you need more)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy entire project (Python code, app.py, src/, requirements.txt, etc.)
COPY . .

# Overwrite / ensure we have the fresh built frontend dist from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install Python dependencies (requirements.txt uses "-e ." -> setup.py)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Flask will listen on port 8080 inside the container
EXPOSE 8080

# IMPORTANT: make sure app.py runs on host="0.0.0.0", port=8080
# e.g. app.run(host="0.0.0.0", port=8080)
CMD ["python", "app.py"]
