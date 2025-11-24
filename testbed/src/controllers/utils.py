from typing import Dict


def add_squash_output_to_hp(hp: Dict) -> Dict:
    """
    Modifies a hyperparameter dictionary to enable squashed policy output and
    state-dependent exploration (SDE).

    This function is typically used  with continuous action spaces,
    to prepare hyperparameters for models that benefit from these configurations.
    **It improves training stability by squashing outputs to a bounded range and enables
    more effective exploration through state-dependent noise, leading to faster and more robust learning.**

    Args:
        hp (Dict): The dictionary of hyperparameters to be modified.

    Returns:
        Dict: The modified hyperparameter dictionary with 'squash_output'
              set to True within 'policy_kwargs' and 'use_sde' set to True.
    """

    if "policy_kwargs" not in hp:
        hp["policy_kwargs"] = {}
    hp["policy_kwargs"]["squash_output"] = True
    hp["use_sde"] = True

    return hp


def stabilize_training(hp: Dict) -> Dict:
    """
    Stabilizes training by applying gradient clipping and limiting policy changes.

    Args:
        hp (Dict): A dictionary of hyperparameters.

    Returns:
        Dict: The updated hyperparameters with stabilization settings.
    """
    hp["max_grad_norm"] = 0.5
    hp["target_kl"] = 0.03
    return hp
