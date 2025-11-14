# Testbed Runtime

The testbed package executes experiment suites defined in YAML, manages
reinforcement-learning controllers, and exposes an API for the backend to spawn
runs. It is built on top of [Sinergym](https://github.com/ugr-sail/sinergym)
and EnergyPlus simulations.

## Entry points
- **CLI** – `python src/main.py <path/to/experiment-suite.yaml>`
  - Registers environment and controller factories.
  - Parses experiment definitions via `parser.config_parser`.
  - Streams training/evaluation data into HDF5 through
    `reporting.hdf5_storage`.
- **FastAPI service** – `uvicorn api.api:app --app-dir src --port 8001`
  - `/api/testbed/start` starts a background CLI run and writes logs to a file.
  - `/api/testbed/status/{pid}` returns process status, exit code, and command
    arguments.
  - `/api/testbed/stop` terminates a process by PID.

The backend container interacts solely with these HTTP endpoints.

## Environment prerequisites
- Python 3.12 with C extensions (provided by the Docker image).
- EnergyPlus installation path registered in `site-packages/energyplus_path.pth`.
  The Dockerfile automates this; when running locally use:
  ```bash
  python - <<'PY'
  import site, sys
  from pathlib import Path
  energyplus = Path('/path/to/EnergyPlus-25-1-0')
  site_packages = next(Path(p) for p in site.getsitepackages() if 'site-packages' in p)
  (site_packages / 'energyplus_path.pth').write_text(str(energyplus))
  print('Registered EnergyPlus at', energyplus)
  PY
  ```
- CUDA/cuDNN dependencies are preinstalled in the container. If you do not need
  GPU support locally, install the CPU variants of your preferred RL libraries.

## Output structure
- HDF5 files are created via `reporting/HDF5StorageManager` (see
  `reporting/hdf5_storage.py`). Per-experiment metadata, state/action/reward
  sequences, and evaluation episodes are stored hierarchically.
- Experiment context bundles (YAML config snapshots) are produced in coordination
  with the backend and saved alongside the HDF5 artifacts.
- Log files are written to `data/experiments/logs` (configurable through the
  backend suite manager).

## Extending the runtime
- **Environments** – Implement `IEnvironmentFactory` in `src/environments/` and
  register it in `src/main.py` via `experiment_manager.register_environment_factory`.
- **Controllers** – Implement `IControllerFactory` in `src/controllers/` and
  register it similarly. Existing factories cover SAC, PPO, TD3, A2C, DQN, rule-based,
  and custom controllers.
- **Reporting** – Extend `reporting/` handlers to add new datasets or metadata to
  the HDF5 files. Hooks exist for training/evaluation episodes and context files.

To make new controllers available in the frontend, a new entry in the file `controllers.json` in the frontend (folder `/frontend/public`) nust be created.


## Docker notes
The `Dockerfile` builds on the official EnergyPlus base image, compiles Python
3.12, installs Pipenv dependencies, and exposes port `8001`. Compose mounts
`/config` and `/data` so the runtime has access to the YAML suite definitions and
persists artifacts to the host.
