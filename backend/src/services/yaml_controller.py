from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from models.controller import SaveControllerRequest

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)  # sequence=4 ensures nested indent
yaml.preserve_quotes = True


def save_controller(req: SaveControllerRequest) -> str:
    s = req.settings

    if s.type == "custom":
        # Type 3: custom controller
        doc = {
            "class_name": s.customClassName,
            "module": s.customModule,
            "args": {kv.key: kv.value for kv in s.initArguments},
        }

    elif s.type == "rule based":
        # --- FIX: use CommentedSeq to force proper indentation ---
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
                kv.key: (
                    float(kv.value)
                    if isinstance(kv.value, (int, float)) or str(kv.value).replace(".", "", 1).isdigit()
                    else kv.value
                )
                for kv in s.customVariables
            },
            "rules": rules_seq,
        }

    else:  # reinforcement learning (Type 1)
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
            "hyperparameters": {kv.key: kv.value for kv in s.hyperparameters},
        }

    # Save file
    Path(req.directory).mkdir(parents=True, exist_ok=True)
    path = Path(req.directory) / req.filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)

    return str(path.resolve())
