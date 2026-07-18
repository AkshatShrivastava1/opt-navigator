# Containerized OPT Navigator API (FastAPI).
#   Build:  docker build -t opt-navigator-api .
#   Run:    docker run -p 8000:8000 --env-file .env opt-navigator-api
#   Deploy: push the image to GCP Cloud Run / AWS, or point Render at this Dockerfile.
#
# Note: retrieval hits Supabase at runtime, so the corpus is NOT baked into the image.
FROM python:3.12-slim

# Leaner, quieter Python in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code only (no data/, tests/, or frontend/ — see .dockerignore)
COPY app ./app

# Cloud Run / Render inject $PORT; default to 8000 for local `docker run`
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
