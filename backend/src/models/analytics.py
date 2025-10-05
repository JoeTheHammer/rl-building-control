from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from models.experiment import ExperimentSuiteStatus


class AnalyticsSuiteSummary(BaseModel):
    id: int
    name: str
    status: ExperimentSuiteStatus
    path: str | None = None
    config_filename: str | None = None
    has_data: bool = False
    file_name: str | None = None


class AnalyticsEpisode(BaseModel):
    id: str
    label: str | None = None
    reward: List[float] = Field(default_factory=list)
    actions: Dict[str, List[float]] = Field(default_factory=dict)
    states: Dict[str, List[float]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsEvaluation(BaseModel):
    action_names: List[str] = Field(default_factory=list)
    state_names: List[str] = Field(default_factory=list)
    episodes: List[AnalyticsEpisode] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsTraining(BaseModel):
    action_names: List[str] = Field(default_factory=list)
    state_names: List[str] = Field(default_factory=list)
    reward: List[float] = Field(default_factory=list)
    actions: Dict[str, List[float]] = Field(default_factory=dict)
    states: Dict[str, List[float]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsExperiment(BaseModel):
    key: str
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluation: AnalyticsEvaluation | None = None
    training: AnalyticsTraining | None = None


class AnalyticsDataResponse(BaseModel):
    suite_id: int
    suite_name: str
    file_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    experiments: List[AnalyticsExperiment] = Field(default_factory=list)
