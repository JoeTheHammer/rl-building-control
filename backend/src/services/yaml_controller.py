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
    """Convert string to int/float/bool if possible, else keep string quoted."""
    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, str):
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            return DoubleQuotedScalarString(val)
    return DoubleQuotedScalarString(str(val))


def _build_nested_dict(items: list) -> dict:
    """
    Converts a list of key-value pairs with dot-separated keys into a nested dict.
    Raises ValueError if a key conflicts with an existing nested structure.
    """
    result = {}
    for item in items:
        keys = item.key.split('.')
        d = result
        for i, key in enumerate(keys[:-1]):
            path = '.'.join(keys[:i+1])
            if key not in d:
                d[key] = {}
            d = d[key]
            if not isinstance(d, dict):
                raise ValueError(f"Key conflict: '{path}' is a leaf node and cannot have sub-keys.")

        leaf_key = keys[-1]
        if leaf_key in d and isinstance(d[leaf_key], dict):
            raise ValueError(f"Key conflict: '{item.key}' is a parent node and cannot be assigned a value.")

        d[leaf_key] = _convert_value(item.value)
    return result


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
            "hyperparameters": _build_nested_dict(s.hyperparameters),
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
            }
            if s.numTrials is not None:
                hp_tuning["num_trials"] = s.numTrials
            if s.numEpisodes is not None:
                hp_tuning["num_episodes"] = s.numEpisodes
            if s.hpSampler:
                hp_tuning["sampler"] = s.hpSampler
            if s.hpTrainingTimesteps is not None:
                hp_tuning["training_timesteps"] = s.hpTrainingTimesteps
            doc["hyperparameter_tuning"] = hp_tuning

    Path(req.directory).mkdir(parents=True, exist_ok=True)
    path = Path(req.directory) / req.filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)

    return str(path.resolve())
