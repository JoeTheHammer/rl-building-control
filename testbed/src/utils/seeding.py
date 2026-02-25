from __future__ import annotations

import random
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class _SeedableSpace(Protocol):
    def seed(self, seed: int | None = None) -> None: ...


def apply_global_seed(seed: int | None) -> None:
    if seed is None:
        return

    random.seed(seed)
    np.random.seed(seed)

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def seed_env_spaces(env: object, seed: int | None) -> None:
    if seed is None:
        return

    action_space = getattr(env, "action_space", None)
    if isinstance(action_space, _SeedableSpace):
        action_space.seed(seed)

    observation_space = getattr(env, "observation_space", None)
    if isinstance(observation_space, _SeedableSpace):
        observation_space.seed(seed)
