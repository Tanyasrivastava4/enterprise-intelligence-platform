# ==============================================================================
# Stage 1: Build React Frontend
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Production Python Backend & Static SPA Server
# ==============================================================================
FROM python:3.10-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Pre-download and cache lightweight ONNX all-MiniLM-L6-v2 model during build
RUN python -c "from chromadb.utils import embedding_functions; fn = embedding_functions.DefaultEmbeddingFunction(); fn(['warmup'])"

# Copy backend code
COPY backend/ ./backend/
COPY sample_data/ ./sample_data/
COPY .env.example ./.env

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose Render standard port
EXPOSE 10000 8000

# Start Uvicorn application (adapting dynamically to Render's $PORT or default 10000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
