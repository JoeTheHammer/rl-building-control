from pathlib import Path
from typing import Any
from io import StringIO

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString
from ruamel.yaml.comments import CommentedSeq

from models.environment import EnvironmentConfig

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True

BASE_DIR = Path(__file__).resolve().parents[3]

WEATHER_DIR = BASE_DIR / "data" / "environment" / "weather"
BUILDING_DIR = BASE_DIR / "data" / "environment" / "buildings"


def build_environment_yaml(cfg: EnvironmentConfig) -> str:
    # Building model path
    building_path = BUILDING_DIR / cfg.generalSettings.buildingModelFile

    # Weather input can be either a folder name or a full .epw path
    weather_input = WEATHER_DIR / cfg.generalSettings.weatherDataFile
    weather_input = weather_input.resolve()

    if weather_input.is_file() and weather_input.suffix.lower() == ".epw":
        weather_folder = weather_input.parent
        epw_file = weather_input
    elif weather_input.is_dir():
        epw_files = list(weather_input.glob("*.epw"))
        if not epw_files:
            raise FileNotFoundError(f"No .epw file found in {weather_input}")
        epw_file = epw_files[0]
        weather_folder = weather_input
    else:
        raise FileNotFoundError(f"Weather data must be a folder or .epw file, got {weather_input}")

    # Find the .ddy file in that folder
    ddy_files = list(weather_folder.glob("*.ddy"))
    if not ddy_files:
        raise FileNotFoundError(f"No .ddy file found in {weather_folder}")

    # Build YAML doc with epw (for weather_data)
    doc: dict[str, Any] = {
        "building_model": str(building_path),
        "weather_data": str(epw_file),
    }

    variables: dict[str, Any] = {}
    meters: dict[str, Any] = {}
    state_space: dict[str, Any] = {}

    for v in cfg.stateSpaceSettings.variables:
        if v.variableType == "meter":
            meters[v.name] = f'"{v.meterName}"'
        else:
            variables[v.name] = {
                "type": f'"{v.energyPlusType}"',
                "zone": f'"{v.zone}"',
            }

    if variables:
        state_space["variables"] = variables
    if meters:
        state_space["meters"] = meters

    if cfg.stateSpaceSettings.addTimeInfo:
        state_space["time_info"] = {
            "day_of_month": {"cyclic": cfg.stateSpaceSettings.dayOfMonth.cyclic},
            "month": {"cyclic": cfg.stateSpaceSettings.month.cyclic},
            "day_of_week": {"cyclic": cfg.stateSpaceSettings.dayOfWeek.cyclic},
            "hour": {"cyclic": cfg.stateSpaceSettings.hour.cyclic},
        }

    doc["state_space"] = state_space

    actuators: dict[str, Any] = {}
    for a in cfg.actionSpaceSettings.actuators:
        if a.type == "continuous":
            actuators[a.actuatorName] = {
                "type": '"continuous"',
                "range": [a.min, a.max],
                "component": f'"{a.component}"',
                "control_type": f'"{a.controlType}"',
                "actuator_key": f'"{a.actuatorKey}"',
            }
        elif a.type == "discrete" and a.mode == "range":
            actuators[a.actuatorName] = {
                "type": '"discrete"',
                "range": [a.min, a.max],
                "step_size": a.stepSize,
                "component": f'"{a.component}"',
                "control_type": f'"{a.controlType}"',
                "actuator_key": f'"{a.actuatorKey}"',
            }
        elif a.type == "discrete" and a.mode == "values":
            actuators[a.actuatorName] = {
                "type": '"discrete"',
                "values": a.valueList,
                "component": f'"{a.component}"',
                "control_type": f'"{a.controlType}"',
                "actuator_key": f'"{a.actuatorKey}"',
            }

    doc["action_space"] = {"actuators": actuators}

    reward_params: dict[str, Any] = {p.key: p.value for p in cfg.rewardSettings.parameters}

    doc["reward_function"] = {
        "type": f'"{cfg.rewardSettings.type}"',
        "variables": [f'"{v}"' for v in cfg.rewardSettings.variables],
        "expression": FoldedScalarString(cfg.rewardSettings.expression),
        "params": reward_params,
    }

    episode: dict[str, Any] = {"timesteps_per_hour": cfg.generalSettings.timestepsPerHour}

    if cfg.generalSettings.startDate and cfg.generalSettings.endDate:
        s = cfg.generalSettings.startDate.split("-")
        e = cfg.generalSettings.endDate.split("-")
        seq = CommentedSeq(
            [int(s[2]), int(s[1]), int(s[0]), int(e[2]), int(e[1]), int(e[0])]
        )
        seq.fa.set_flow_style()
        episode["period"] = seq

    doc["episode"] = episode

    stream = StringIO()
    yaml.dump(doc, stream)
    return stream.getvalue()


def save_environment_yaml(cfg: EnvironmentConfig, filepath: Path) -> None:
    yaml_str = build_environment_yaml(cfg)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(yaml_str)
