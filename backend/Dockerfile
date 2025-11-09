FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PIPENV_VENV_IN_PROJECT=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

COPY . .

ENV TESTBED_URL="http://testbed:8001" \
    CONFIG_PATH="/config" \
    DATA_PATH="/data"

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
