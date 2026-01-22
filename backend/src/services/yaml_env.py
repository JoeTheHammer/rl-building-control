from pathlib import Path
from typing import Any
from io import StringIO

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString, DoubleQuotedScalarString
from ruamel.yaml.comments import CommentedSeq

from models.environment import EnvironmentConfig

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True

BASE_DIR = Path(__file__).resolve().parents[3]

WEATHER_DIR = BASE_DIR / "data" / "environment" / "weather"
BUILDING_DIR = BASE_DIR / "data" / "environment" / "buildings"


def try_parse_number(value: str):
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return original string if not a number
    return value

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
        "building_model": DoubleQuotedScalarString(str(building_path)),
        "weather_data": DoubleQuotedScalarString(str(epw_file)),
    }

    # --- State space ---
    variables: dict[str, Any] = {}
    meters: dict[str, Any] = {}
    state_space: dict[str, Any] = {}

    for v in cfg.stateSpaceSettings.variables:
        if v.variableType == "meter":
            meter_name = DoubleQuotedScalarString(v.meterName.strip('"'))
            if v.excludeFromState:
                meters[v.name] = {
                    "name": meter_name,
                    "exclude_from_state": True,
                }
            else:
                meters[v.name] = meter_name
        else:
            entry = {
                "type": DoubleQuotedScalarString(v.energyPlusType.strip('"')),
                "zone": DoubleQuotedScalarString(v.zone.strip('"')),
            }
            if v.excludeFromState:
                entry["exclude_from_state"] = True
            variables[v.name] = entry

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

    # --- Action space ---
    actuators: dict[str, Any] = {}
    for a in cfg.actionSpaceSettings.actuators:
        if a.type == "continuous":
            seq = CommentedSeq([a.min, a.max])
            seq.fa.set_flow_style()
            actuators[a.actuatorName] = {
                "type": DoubleQuotedScalarString("continuous"),
                "range": seq,
                "component": DoubleQuotedScalarString(a.component.strip('"')),
                "control_type": DoubleQuotedScalarString(a.controlType.strip('"')),
                "actuator_key": DoubleQuotedScalarString(a.actuatorKey.strip('"')),
            }
        elif a.type == "discrete" and a.mode == "range":
            seq = CommentedSeq([a.min, a.max])
            seq.fa.set_flow_style()
            actuators[a.actuatorName] = {
                "type": DoubleQuotedScalarString("discrete"),
                "range": seq,
                "step_size": a.stepSize,
                "component": DoubleQuotedScalarString(a.component.strip('"')),
                "control_type": DoubleQuotedScalarString(a.controlType.strip('"')),
                "actuator_key": DoubleQuotedScalarString(a.actuatorKey.strip('"')),
            }
        elif a.type == "discrete" and a.mode == "values":
            val_seq = CommentedSeq(a.valueList)
            val_seq.fa.set_flow_style()
            actuators[a.actuatorName] = {
                "type": DoubleQuotedScalarString("discrete"),
                "values": val_seq,
                "component": DoubleQuotedScalarString(a.component.strip('"')),
                "control_type": DoubleQuotedScalarString(a.controlType.strip('"')),
                "actuator_key": DoubleQuotedScalarString(a.actuatorKey.strip('"')),
            }

    doc["action_space"] = {"actuators": actuators}

    # --- Reward function ---
    reward_params: dict[str, Any] = {p.key: p.value for p in cfg.rewardSettings.parameters}

    init_args: dict[str, Any] = {}
    if cfg.rewardSettings.init_args:
        for arg in cfg.rewardSettings.init_args:
            if arg.key and arg.key.strip():
                # UPDATED LINE: Parse string to number if possible
                init_args[arg.key] = try_parse_number(arg.value)

    var_seq = CommentedSeq(
        [DoubleQuotedScalarString(v.strip('"')) for v in cfg.rewardSettings.variables]
    )
    var_seq.fa.set_flow_style()

    # Construct the base dictionary
    reward_dict = {
        "type": DoubleQuotedScalarString(cfg.rewardSettings.type.strip('"')),
        "variables": var_seq,
        "expression": FoldedScalarString(cfg.rewardSettings.expression),
        "params": reward_params,
    }

    if cfg.rewardSettings.module:
        reward_dict["module"] = DoubleQuotedScalarString(cfg.rewardSettings.module.strip('"'))

    if cfg.rewardSettings.class_name:
        reward_dict["class_name"] = DoubleQuotedScalarString(cfg.rewardSettings.class_name.strip('"'))

    if init_args:
        reward_dict["init_args"] = init_args

    doc["reward_function"] = reward_dict

    # --- Episode ---
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

    # --- Weather variability ---
    if cfg.generalSettings.weatherVariabilityEnabled:
        variability_entries = [
            entry
            for entry in cfg.generalSettings.weatherVariabilityVariables
            if entry.key.strip()
        ]
        if variability_entries:
            weather_variability: dict[str, Any] = {}
            for entry in variability_entries:
                seq = CommentedSeq([entry.sigma, entry.mu, entry.tau])
                seq.fa.set_flow_style()
                weather_variability[entry.key] = seq
            doc["weather_variability"] = weather_variability

    # Dump YAML
    stream = StringIO()
    yaml.dump(doc, stream)
    return stream.getvalue()


def save_environment_yaml(cfg: EnvironmentConfig, filepath: Path) -> None:
    yaml_str = build_environment_yaml(cfg)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(yaml_str)
