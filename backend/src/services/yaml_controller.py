from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from decimal import Decimal

from models.controller import SaveControllerRequest

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True

# Force float representation in fixed-point decimal notation
def float_representer(dumper, value: float):
    # "0.00001" instead of "1e-05"
    text = format(Decimal(str(value)), 'f')
    return dumper.represent_scalar('tag:yaml.org,2002:float', text)

yaml.representer.add_representer(float, float_representer)


def _convert_value(val):
    """Convert string to int/float if possible, else keep string quoted."""
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return val
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

        doc = {
            "training": training,
            "hyperparameters": {
                kv.key: _convert_value(kv.value) for kv in s.hyperparameters
            },
        }

        doc["environment_wrapper"] = {
            "normalize_state": s.environmentWrapper.normalizeState,
            "normalize_reward": s.environmentWrapper.normalizeReward,
            "normalize_action": s.environmentWrapper.normalizeAction,
            "continuous_action": s.environmentWrapper.continuousAction,
            "discrete_action": s.environmentWrapper.discreteAction,
        }

        # Only add hyperparameter_tuning if enabled == True
        if s.hpTuning:
            hp_tuning = {
                "enabled": True,
                "num_trials": s.numTrials,
                "num_episodes": s.numEpisodes,
            }
            doc["hyperparameter_tuning"] = hp_tuning

    Path(req.directory).mkdir(parents=True, exist_ok=True)
    path = Path(req.directory) / req.filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)

    return str(path.resolve())
