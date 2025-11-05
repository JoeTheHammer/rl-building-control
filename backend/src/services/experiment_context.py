from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import h5py

from fastapi import HTTPException

from models.experiment import SuiteContextExperiment, SuiteContextFile, SuiteContextResponse
from services.experiment_suite import manager as suite_manager
from services.hdf5_utils import find_latest_h5_file


@dataclass(frozen=True)
class StoredFile:
    name: str
    relative_path: str
    original_path: Optional[str]
    is_text: bool
    content: bytes
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ExperimentContextRecord:
    key: str
    experiment_id: int
    name: str
    files: List[StoredFile]

    def get_text_file(self, relative_path: str) -> Optional[StoredFile]:
        for file in self.files:
            if file.relative_path == relative_path and file.is_text:
                return file
        return None

    def iter_resources(self) -> Iterable[StoredFile]:
        for file in self.files:
            if not file.is_text:
                yield file


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, (str, int, float)):
        return str(value)
    return str(value)


def _read_dataset(name: str, dataset: h5py.Dataset) -> StoredFile:
    relative_path = _as_str(dataset.attrs.get("relative_path")) or name
    original_path = _as_str(dataset.attrs.get("original_path"))
    is_text = bool(dataset.attrs.get("is_text", False))

    if is_text:
        content = dataset.asstr()[()].encode("utf-8")
    else:
        data = dataset[()]
        if isinstance(data, bytes):
            content = data
        elif hasattr(data, "tobytes"):
            content = data.tobytes()
        elif hasattr(data, "tolist"):
            content = bytes(data.tolist())
        else:
            content = bytes(data)

    metadata: Dict[str, Any] = {}
    for key, value in dataset.attrs.items():
        key_str = str(key)
        if key_str in {"relative_path", "original_path", "is_text"}:
            continue
        metadata[key_str] = value

    return StoredFile(
        name=name,
        relative_path=relative_path,
        original_path=original_path,
        is_text=is_text,
        content=content,
        metadata=metadata,
    )


def _read_context_group(key: str, group: h5py.Group) -> Optional[ExperimentContextRecord]:
    context_group = group.get("context")
    if not isinstance(context_group, h5py.Group):
        return None

    files: List[StoredFile] = []

    def visitor(name: str, obj: h5py.Dataset | h5py.Group) -> None:
        if isinstance(obj, h5py.Dataset):
            files.append(_read_dataset(name, obj))

    context_group.visititems(visitor)

    if not files:
        return None

    attrs = {str(key): value for key, value in group.attrs.items()}
    experiment_id = int(attrs.get("experiment_id", 0))
    name_value = attrs.get("name") or attrs.get("experiment") or key
    name = _as_str(name_value) or key

    return ExperimentContextRecord(key=key, experiment_id=experiment_id, name=name, files=files)


def _load_context_records(file_path: Path) -> List[ExperimentContextRecord]:
    records: List[ExperimentContextRecord] = []
    with h5py.File(file_path, "r") as handle:
        for key, item in handle.items():
            if not isinstance(item, h5py.Group) or not key.startswith("experiment"):
                continue
            record = _read_context_group(key, item)
            if record:
                records.append(record)
    return records


def _to_suite_context_file(file: StoredFile) -> SuiteContextFile:
    content = file.content.decode("utf-8") if file.is_text else ""
    return SuiteContextFile(
        filename=Path(file.relative_path).name,
        content=content,
        original_path=file.original_path,
        relative_path=file.relative_path,
    )


def load_suite_context(suite_id: int) -> SuiteContextResponse:
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="Experiment suite path not available")

    directory = Path(suite.path).expanduser()
    file_path = find_latest_h5_file(directory)

    records = _load_context_records(file_path)
    experiments: List[SuiteContextExperiment] = []

    for record in records:
        experiment_file = record.get_text_file("configs/experiment.yaml")
        environment_file = record.get_text_file("configs/environment.yaml")
        controller_file = record.get_text_file("configs/controller.yaml")

        if not experiment_file:
            continue

        experiments.append(
            SuiteContextExperiment(
                key=record.key,
                id=record.experiment_id,
                name=record.name,
                experiment=_to_suite_context_file(experiment_file),
                environment=_to_suite_context_file(environment_file)
                if environment_file
                else None,
                controller=_to_suite_context_file(controller_file)
                if controller_file
                else None,
            )
        )

    experiments.sort(key=lambda item: item.id)

    return SuiteContextResponse(
        suite_id=suite_id,
        hdf5_file=file_path.name,
        experiments=experiments,
    )


def get_experiment_record(suite_id: int, experiment_key: str) -> ExperimentContextRecord:
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="Experiment suite path not available")

    directory = Path(suite.path).expanduser()
    file_path = find_latest_h5_file(directory)

    records = _load_context_records(file_path)
    for record in records:
        if record.key == experiment_key:
            return record

    raise HTTPException(status_code=404, detail="Experiment context not found")
