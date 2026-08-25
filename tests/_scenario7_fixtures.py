import numpy as np

from config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv


def capture_structured_evidence(value):
    """Canonicalize the small set of structured values used by this test."""

    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        return ("ndarray", array.dtype.str, array.shape, array.tobytes())
    if isinstance(value, np.generic):
        scalar = np.asarray(value)
        return ("numpy-scalar", scalar.dtype.str, scalar.tobytes())
    if isinstance(value, dict):
        return (
            "dict",
            tuple(
                (capture_structured_evidence(key), capture_structured_evidence(item))
                for key, item in value.items()
            ),
        )
    if isinstance(value, (list, tuple)):
        return (
            type(value).__name__,
            tuple(capture_structured_evidence(item) for item in value),
        )
    return (type(value).__name__, value)


def capture_environment_rng_state(adapter):
    scenario_rng = adapter.env.np_random
    adapter_rng = adapter.np_random
    return (
        capture_structured_evidence(scenario_rng.get_state()),
        capture_structured_evidence(adapter_rng.bit_generator.state),
    )


def rng_states_equal(left, right):
    return left == right


def make_env(preset="S7-S3", seed=123):
    config = Config(preset)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def make_variant_env(variant, seed=123):
    config = Config("S7-S3")
    config.apply_scenario7_reward_variant(variant)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def make_arm_env(arm, seed=123):
    config = Config("S7-S3")
    config.apply_scenario7_experiment_arm(arm)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def zero_actions(env):
    return {agent: np.zeros(4, dtype=np.float32) for agent in env.agents}
