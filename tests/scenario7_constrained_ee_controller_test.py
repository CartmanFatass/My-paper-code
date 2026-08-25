import numpy as np

from config_1 import Config
from train_multiproc_config_1 import (
    Scenario7SafetyDualController,
    broadcast_scenario7_safety_dual,
)


def test_safety_controller_updates_return_dual_from_constraint_cost():
    config = Config("S7-S3")
    config.outer_update_min_episodes = 2
    controller = Scenario7SafetyDualController(config)

    controller.record_episode(
        constraint_cost_sum=1.0,
        steps=10,
    )
    assert controller.update() is None

    controller.record_episode(
        constraint_cost_sum=0.0,
        steps=10,
    )
    update = controller.update()

    assert np.isclose(update["window_mean_return_constraint_cost"], 0.05)
    assert np.isclose(update["safety_dual"], 0.0005)


def test_outer_controller_state_round_trip_preserves_window():
    config = Config("S7-S3")
    config.outer_update_min_episodes = 2
    controller = Scenario7SafetyDualController(config)
    controller.record_episode(0.2, 5)
    state = controller.state_dict()

    restored = Scenario7SafetyDualController(config, state=state)

    assert restored.parameters() == controller.parameters()
    assert list(restored.episodes) == list(controller.episodes)
    assert restored.pending_episodes == 1


def test_safety_dual_is_broadcast_as_one_frozen_snapshot():
    config = Config("S7-S3")
    controller = Scenario7SafetyDualController(config)
    controller.safety_dual = 2.5

    class FakeVecEnv:
        def __init__(self):
            self.calls = []

        def env_method(self, method_name, *args, **kwargs):
            self.calls.append((method_name, args, kwargs))
            return [None]

    vec_env = FakeVecEnv()
    params = broadcast_scenario7_safety_dual(vec_env, controller)

    assert params == {"safety_dual": 2.5}
    assert vec_env.calls == [
        (
            "set_scenario7_safety_dual",
            (2.5,),
            {},
        )
    ]
