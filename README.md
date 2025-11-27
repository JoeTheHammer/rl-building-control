# Installation & Quick Start

## 1. Prerequisites

Before running the platform with Docker, ensure the following are
installed:

-   **Docker 24+**
-   **Docker Compose V2**
-   **20 GB free disk space**

## 2. Clone the repository

``` bash
git clone https://github.com/JoeTheHammer/rl-building-control.git
cd rl-building-control

```

## 3. Start the entire system

``` bash
docker-compose up --build
```

Services: 
- Frontend: http://localhost:5173 
- Backend: http://localhost:8000
- Testbed: http://localhost:8001


Stop:

``` bash
CTRL + C
docker-compose down
docker-compose down -v   # wipe volumes
```

## 4. Remote access

If you want to access the system from remote, make sure to set the host environment variables in the `.env` file in the project root. The hostnames should correstpond to the host system.

This is only needed for remote access, as the default hostname is `localhost`. 

------------------------------------------------------------------------

# System overview

## Purpose

This repository hosts a complete reinforcement-learning platform for
building control.

-   **Testbed runtime** -- executes experiment suites via
    [Sinergym](https://github.com/ugr-sail/sinergym)/EnergyPlus.
-   **Backend API** -- manages configurations, experiments, TensorBoard.
-   **Frontend UI** -- configure experiments, monitor progress, analyze
    results.

## Architecture overview

``` mermaid
graph TD
subgraph UI
    FE[Frontend - React/Vite]
end
subgraph API
    BE[Backend - FastAPI]
end
subgraph Runtime
    TB[Testbed - Typer + FastAPI]
end
subgraph Storage
    CFG[Config volume]
    DAT[Data volume]
end
FE -->|REST| BE
BE -->|Launch/monitor| TB
BE -->|Writes| CFG
BE -->|Reads| DAT
TB -->|Writes| DAT
TB -->|Reads| CFG
```

## Component responsibilities

-   Frontend: React dashboard, configuration creation, analytics views.
-   Backend: REST API, suite orchestration, YAML config handling.
-   Testbed: CLI + FastAPI service for experiment execution.
-   Volumes: `config/` and `data/` shared across backend & testbed.

## Repository structure

    backend/      FastAPI orchestration service
    config/       YAML configs
    data/         Experiment results, Environment data (building model, weather data)
    docs/         Documentation (in progress)
    frontend/     React UI
    testbed/      Sinergym runtime
    docker-compose.yml

## Running locally

### Backend

``` bash
cd backend
pipenv install --dev
pipenv run uvicorn main:app --app-dir src --reload
```

### Testbed

``` bash
cd testbed
pipenv install --dev
pipenv run uvicorn api.api:app --app-dir src --port 8001
pipenv run python src/main.py config/experiments/<suite>.yaml
```

### Frontend

``` bash
cd frontend
npm install
npm run dev
```

## Extending the system

-   Add environments via `testbed/src/environments/`
-   Add controllers via `testbed/src/controllers/`
-   Add backend endpoints under `backend/src/api/`
-   Add frontend routes under `frontend/src/lib/routes.tsx`

When more information about adding additional controllers or enviornments can be found in the README of the testbed (testbed/README). 