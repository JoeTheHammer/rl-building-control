"""Utilities for exporting controller manifests."""

from __future__ import annotations

import json
from pathlib import Path

from experiment.manager import ExperimentManager


def export_controller_manifest(experiment_manager: ExperimentManager) -> None:
    """Write a JSON manifest describing all registered controllers."""
    manifest = [
        {"key": key, "name": key.replace("-", " ").title()}
        for key in experiment_manager.controller_factories.keys()
    ]

    manifest_dir = Path(__file__).resolve().parents[2] / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "controllers.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
