FROM nrel/energyplus:25.1.0

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_VENV_IN_PROJECT=1 \
    ENERGYPLUS_INSTALL=/usr/local/EnergyPlus-25-1-0

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common curl && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3.12 python3.12-venv python3.12-dev build-essential && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN python3.12 -m pip install pipenv && \
    pipenv install --deploy --ignore-pipfile && \
    SITE_PACKAGES=$(pipenv run python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])") && \
    echo "${ENERGYPLUS_INSTALL}" > "${SITE_PACKAGES}/energyplus_path.pth"

COPY . .

EXPOSE 8001

CMD ["pipenv", "run", "uvicorn", "api.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001", "--reload"]
