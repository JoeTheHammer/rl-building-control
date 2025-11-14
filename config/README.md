# Configuration assets

This directory contains YAML files that describe environments, controllers, and
experiment suites. The backend writes to these folders through its `/api/*/save`
endpoints, and the testbed runtime reads them when launching experiments.

```
config/
├── controllers/   
├── environments/  
└── experiments/  
```

## Conventions
- File names should be unique and descriptive; they are displayed verbatim in
  the frontend configurators.
- Paths inside experiment YAML files may be absolute or relative. When executed
  inside Docker, the backend remaps host-style paths into `/config` and `/data`
  using the helpers in `backend/src/services/experiment_suite.py`.

## Creating new assets
1. Use the frontend configurators to author YAML interactively, or craft them by
   hand following the examples in this directory.
2. Save the files under the appropriate subfolder.
3. Reference them in experiment suites via relative or aboslute paths, e.g.
   ```yaml
   experiments:
     - name: data-center-sac
       environment_config: environments/sinergym-data-center.yaml
       controller_config: controllers/sac-default.yaml
       controller: sac
       engine: sinergym
       episodes: 10
   ```
4. Commit both environment and controller files alongside the experiment suite
   so runs are reproducible.

## Runtime behavior
During execution the backend copies resolved YAML content into the experiment
context bundles stored with the results. This guarantees that reruns always use
exactly the configuration referenced when the suite was launched.
