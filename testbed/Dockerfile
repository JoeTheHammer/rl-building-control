FROM nrel/energyplus:23.2.0

ENV ENV=production \
    TESTBED_PATH=/app \
    TESTBED_IMAGE=myproject/testbed:latest \
    FRONTEND_PORT=5173 \
    BACKEND_PORT=8000 \
    ENERGYPLUS_VERSION=23.2.0 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./
RUN python3 -m pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy

COPY . .

CMD ["python3", "-m", "src.main"]
