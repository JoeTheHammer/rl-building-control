from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from models.controller import SaveControllerRequest

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True


def _convert_value(val):
    """Convert string to int/float if possible, else keep string quoted."""
    # If already int or float
    if isinstance(val, (int, float)):
        return val
    # Try to parse int
    if isinstance(val, str):
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            return DoubleQuotedScalarString(val)
    return DoubleQuotedScalarString(str(val))


def save_controller(req: SaveControllerRequest) -> str:
    s = req.settings

    if s.type == "custom":
        doc = {
            "class_name": s.customClassName,
            "module": s.customModule,
            "args": {kv.key: _convert_value(kv.value) for kv in s.initArguments},
        }

    elif s.type == "rule based":
        rules_seq = CommentedSeq()
        for r in s.rules:
            cm = CommentedMap()
            cm["condition"] = DoubleQuotedScalarString(r.condition)
            cm["action"] = DoubleQuotedScalarString(r.action)
            cm.fa.set_block_style()
            rules_seq.append(cm)
        rules_seq.fa.set_block_style()

        doc = {
            "state_space": s.stateSpace,
            "custom_variables": {
                kv.key: _convert_value(kv.value)
                for kv in s.customVariables
            },
            "rules": rules_seq,
        }

    else:
        training = {
            "timesteps": s.trainingTimesteps,
            "report_training": s.reportTraining,
            "report_denormalized_state": s.denormalize,
            "tensorboard_logs": s.tensorboardLogs,
        }

        hp_tuning = {
            "enabled": s.hpTuning,
            "num_trials": s.numTrials,
            "num_episodes": s.numEpisodes,
        }

        doc = {
            "training": training,
            "hyperparameter_tuning": hp_tuning,
            "hyperparameters": {
                kv.key: _convert_value(kv.value) for kv in s.hyperparameters
            },
        }

    Path(req.directory).mkdir(parents=True, exist_ok=True)
    path = Path(req.directory) / req.filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)

    return str(path.resolve())
