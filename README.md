# RL Building Control Testbed

## Purpose
This repository hosts a complete reinforcement-learning "testbed" for
experimentation with building control strategies. It combines three services:

- **Testbed runtime** – executes experiment suites against EnergyPlus-powered
  Sinergym environments and writes structured telemetry.
- **Backend API** – a FastAPI service that manages configuration assets,
  launches experiments inside the testbed, and exposes experiment lifecycle and
  analytics endpoints.
- **Frontend UI** – a Vite/React interface that lets users configure
  environments, controllers, and experiment suites, monitor live progress, and
  inspect archived results.

Together the services provide an opinionated environment for developing,
reproducing, and analyzing RL-based HVAC control experiments.

## Architecture overview
```mermaid
graph TD
    subgraph UI
        FE[Frontend (Vite/React)]
    end
    subgraph API
        BE[Backend (FastAPI)]
    end
    subgraph Runtime
        TB[Testbed runtime (Typer + FastAPI)]
    end
    subgraph Storage
        CFG[Config volume]
        DAT[Data volume]
        TBX[(TensorBoard ports)]
    end

    FE -->|REST over HTTP| BE
    BE -->|Launch/monitor| TB
    BE --> CFG
    BE --> DAT
    TB --> CFG
    TB --> DAT
    BE -.-> TBX
```

### Component responsibilities
- **Frontend (`frontend/`)** renders dashboards for active experiment suites,
  configuration editors, and analytics views. It communicates exclusively with
  the backend API.
- **Backend (`backend/`)** exposes REST endpoints under `/api`. It persists
  suite metadata in SQLite, writes YAML configuration files, starts/stops
  experiments in the testbed container, proxies TensorBoard processes, and
  reads experiment output for analytics.
- **Testbed (`testbed/`)** provides two entry points:
  - A CLI (`python src/main.py <config.yaml>`) that reads experiment suites,
    instantiates environments via registered factories, trains/evaluates
    controllers, and records results in HDF5.
  - A lightweight FastAPI service (`/api/testbed`) used by the backend to spawn
    CLI runs and observe their process state.
- **Shared volumes**
  - `config/` contains YAML definitions for environments, controllers, and
    experiment suites.
  - `data/` holds experiment artifacts (logs, HDF5 files, RL checkpoints, and
    derived analytics). Mounted into both the backend and testbed containers.

## Running the full stack with Docker

### Prerequisites
- Docker 24+
- Docker Compose V2 (`docker compose` or `docker-compose`)
- ~20 GB disk space (EnergyPlus base image + RL dependencies)

### Startup
From the repository root run:

```bash
docker-compose up --build
```

Compose builds all images, provisions the EnergyPlus runtime inside the testbed
container, then brings up the services in dependency order:

| Service   | Container | Port | Purpose |
|-----------|-----------|------|---------|
| Testbed   | `testbed` | `8001` | FastAPI process-launch API, also hosts CLI entry point |
| Backend   | `backend` | `8000` | FastAPI REST API consumed by the UI |
| Frontend  | `frontend`| `5173` | Vite dev server for the React application |
| TensorBoard | _dynamic_ (`6006-6100`) | Exposed when the backend starts a TensorBoard session |

Volumes `./config` and `./data` are mounted into the backend and testbed
containers, keeping configuration and experiment outputs on the host. After all
containers are healthy you can access:

- UI dashboard: <http://localhost:5173>
- Backend OpenAPI docs: <http://localhost:8000/docs>
- Testbed API: <http://localhost:8001/api/testbed/status/…>

Stop the stack with `CTRL+C` or `docker-compose down`. Add `-v` to remove
containers and volumes between runs.

### Runtime environment variables
The compose file forwards several knobs you can override via shell environment
variables before `docker-compose up`:

- `BACKEND_HOST` – URL exposed to the frontend (defaults to
  `http://localhost:8000`).
- `TESTBED_HOST` – Hostname the backend should use to contact the testbed when
  running outside Docker (defaults to `127.0.0.1`).
- `TENSORBOARD_HOST` – Hostname that should be embedded in TensorBoard links
  (defaults to `localhost`).

## Repository structure
```
├── backend/                # FastAPI service that orchestrates experiments
├── config/                 # YAML configuration assets (mounted into containers)
│   ├── controllers/
│   ├── environments/
│   └── experiments/
├── data/                   # Experiment outputs, logs, checkpoints, analytics
├── docs/                   # Supplemental documentation and UML diagrams
├── frontend/               # React + TypeScript user interface
├── testbed/                # Experiment runtime (CLI + API) built on Sinergym
├── docker-compose.yml      # Multi-container definition
└── README.md               # This document
```

### Folder highlights
- `data/`
  - Experiment logs captured from the testbed container.
  - RL model checkpoints and evaluation metrics stored in HDF5.
  - TensorBoard metadata generated per suite.
- `config/`
  - Canonical YAML files that describe environments, controllers, and experiment
    suites. The backend writes to this directory through its `/api/*/save`
    endpoints.
- `backend/`
  - `src/main.py` boots the FastAPI app and registers routers for environment,
    controller, building, weather, experiment, and analytics domains.
  - `src/services/experiment_suite.py` manages experiment suite lifecycle using
    SQLite state, Docker-aware path resolution, and HTTP requests to the testbed
    API.
- `frontend/`
  - `src/app.tsx` wires React Router routes to dashboards and configurators.
  - `src/components/` contains feature modules (experiment suites, analytics,
    configurators) that wrap calls to the backend services under
    `src/services/`.
- `testbed/`
  - `src/main.py` registers environment/controller factories and executes suite
    definitions parsed from YAML.
  - `src/api/testbed_api.py` exposes endpoints for starting/stopping CLI runs
    and tracking their processes.
  - `src/reporting/` writes results to HDF5, storing per-episode metadata and
    aggregated metrics.
- `docs/uml/`
  - Generated SVG diagrams describing the internal class structure of the
    testbed runtime.

## Running services locally (without Docker)
### Backend
```bash
cd backend
pipenv install --dev
pipenv run uvicorn main:app --app-dir src --reload
```
Set `TESTBED_URL` (e.g. `http://127.0.0.1:8001`) and `DATA_PATH`/`CONFIG_PATH`
if you are not using the default project-relative directories.

### Testbed runtime
```bash
cd testbed
pipenv install --dev
pipenv run uvicorn api.api:app --app-dir src --port 8001
```
To execute a suite directly from the CLI:
```bash
pipenv run python src/main.py config/experiments/<suite>.yaml
```
Ensure the EnergyPlus path is registered in Python site packages; see
[`testbed/README.md`](testbed/README.md) for detailed setup notes.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_BACKEND_URL` in `.env.local` if the backend is not on
`http://localhost:8000`.

## Extending the system
- Add new environments by implementing `IEnvironmentFactory` subclasses in
  `testbed/src/environments/` and registering them in `src/main.py`.
- Implement custom controllers under `testbed/src/controllers/` using the
  factory pattern established by the existing RL algorithms.
- Expose new backend capabilities by creating routers in
  `backend/src/api/` and corresponding service helpers in `backend/src/services/`.
- Surface new UI features by adding routes in `frontend/src/lib/routes.tsx` and
  composing React components under `frontend/src/components/`.

## Additional resources
- UML class diagrams: [`docs/uml`](docs/uml)
- Automated tests for the testbed runtime: [`testbed/tests`](testbed/tests)
- Experiment analytics utilities: [`backend/src/services/analytics.py`](backend/src/services/analytics.py)

