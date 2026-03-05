# Backend (FastAPI)

The backend service orchestrates experiment suites, manages configuration
artifacts, and exposes REST endpoints consumed by the frontend.

## Capabilities
- Persist and serve YAML configurations for environments, controllers, and
  experiment suites via `/api/environment`, `/api/controller`, and
  `/api/experiment` routers.
- Launch and monitor experiment suites through the `/api/experiment/suites`
  endpoints. Execution uses the testbed container's process-launch API.
- Provide weather/building metadata utilities and analytics endpoints backed by
  experiment outputs in `data/`.
- Manage TensorBoard sidecar processes for suite visualization.

## Application entry point
`src/main.py` wires the FastAPI application, attaches CORS middleware for the UI
and registers all routers. Each router delegates to service modules under
`src/services/` and pydantic schemas under `src/models/`.

## Local development
```bash
cd backend
pipenv install --dev
pipenv run uvicorn main:app --app-dir src --reload
```
The server listens on port `8000`. Visit `/docs` for the auto-generated OpenAPI
spec.

### Environment variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `TENSORBOARD_HOST` | Hostname embedded in TensorBoard links. | `localhost` |
| `TESTBED_HOST` | Hostname to reach the testbed when spawned via Docker. | `testbed` inside containers |
| `RUNNING_IN_DOCKER` | Set automatically by the Docker image to adjust path logic. | `false` |
| `CORS_ALLOW_ORIGINS` | Comma-separated extra allowed frontend origins. | empty |
| `CORS_ALLOW_ORIGIN_REGEX` | Regex used to allow dynamic origins (preflight + requests). | `^https?://(localhost\|127\.0\.0\.1\|0\.0\.0\.0\|172\.\d+\.\d+\.\d+)(:\d+)?$` |

When running outside Docker you typically only need to set any environment variables. When running in docker, make sure to provide a `.env` file with the the correct variables set in the project root.

### Database
Experiment suite metadata is persisted in
`data/experiments/experiment_suites.db` (SQLite). The path is created
automatically and is safe to delete between runs when you want a clean state.

## Key modules
- `src/services/experiment_suite.py` – suite repository, state machine, path
  resolution, and HTTP orchestration with the testbed API.
- `src/services/experiment_context.py` – reads HDF5 files and YAML configs to
  build the downloadable suite context bundles.
- `src/services/tensorboard.py` – manages TensorBoard subprocesses and exposes
  status helpers.
- `src/api/analytics.py` – surfaces aggregated metrics derived from experiment
  HDF5 logs for the frontend analytics views.

## Running unit tests
```bash
pipenv run pytest
```
Add new tests under `src/tests/` (create the directory if it does not yet
exist).

## Docker image
`Dockerfile` installs dependencies via Pipenv and runs the service with Uvicorn
on `0.0.0.0:8000`. The compose file mounts `./config` and `./data` into
`/config` and `/data` respectively so the backend and testbed share state.
