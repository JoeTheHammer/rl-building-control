FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    TESTBED_PATH=/app \
    TESTBED_IMAGE=myproject/testbed:latest \
    DOCKER_HOST=unix:///var/run/docker.sock \
    FRONTEND_PORT=5173 \
    BACKEND_PORT=8000 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY backend/Pipfile backend/Pipfile.lock ./
RUN pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy

COPY backend/ ./
COPY config/ /config/

VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
