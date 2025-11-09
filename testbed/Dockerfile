# ------------------------------------------------------------
# Base image: EnergyPlus 25.1.0
# ------------------------------------------------------------
FROM nrel/energyplus:25.1.0

# ------------------------------------------------------------
# Environment setup
# ------------------------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_VENV_IN_PROJECT=0

WORKDIR /app

# ------------------------------------------------------------
# Install build tools and Python 3.12 from source
# ------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        build-essential \
        wget \
        libssl-dev \
        libffi-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        uuid-dev && \
    wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz && \
    tar -xzf Python-3.12.3.tgz && \
    cd Python-3.12.3 && \
    ./configure --enable-optimizations && \
    make -j"$(nproc)" && \
    make altinstall && \
    ln -sf /usr/local/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python && \
    cd .. && rm -rf Python-3.12.3 Python-3.12.3.tgz && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Install Pipenv and project dependencies
# ------------------------------------------------------------
COPY Pipfile Pipfile.lock ./

RUN python3.12 -m pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy


RUN set -eux; \
    # 1. Detect EnergyPlus install directory dynamically
    EPLUS_DIR="$(find / -maxdepth 1 -type d -name 'EnergyPlus-*' | head -n 1)"; \
    echo "Found EnergyPlus directory: $EPLUS_DIR"; \
    # 2. Add EnergyPlus path to Python import system (.pth)
    SITE_PACKAGES="$(python3.12 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    echo "$EPLUS_DIR" > "$SITE_PACKAGES/energyplus_path.pth"; \
    echo "Added $EPLUS_DIR to Python path ($SITE_PACKAGES/energyplus_path.pth)"; \
    # 3. Persist environment variables for shell sessions
    echo "EPLUS_PATH=$EPLUS_DIR" >> /etc/environment; \
    echo "export EPLUS_PATH=$EPLUS_DIR" >> /etc/profile; \
    # 4. Create symlink for convenience
    ln -sf "$EPLUS_DIR" /usr/local/EnergyPlus

# Let Docker bake it into the image's environment:
ENV EPLUS_PATH=/usr/local/EnergyPlus


# ------------------------------------------------------------
# Copy project source code
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# Expose FastAPI testbed API port
# ------------------------------------------------------------
EXPOSE 8001

# ------------------------------------------------------------
# Start the API server
# ------------------------------------------------------------
CMD ["uvicorn", "api.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001", "--reload"]
