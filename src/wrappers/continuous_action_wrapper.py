import gymnasium as gym


class ContinuousActionWrapper(gym.Wrapper):
    """
    Wrapper for SinergymEnvironment to convert the default tuple action space to a continuous
    box action space. Communicates this to the SinergymEnvironment by setting the right flag.
    """

    def __init__(self, env):
        # Indicate to the underlying env that actions should be treated as continuous
        env.unwrapped.continuous_action_space = True
        super().__init__(env)
