import json
import time

import numpy as np
import pytest

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_short_fixed_renewal_continuous_b01 import study


@pytest.mark.parametrize("raise_step", [False, True])
def test_bounded_t_prefix_and_first_exception_metadata(tmp_path, raise_step):
    factories = []

    class BrokenShape(SyntheticAdapter):
        def step(self, actions):
            bad_shape = np.zeros((2, 1), dtype=np.float32)
            return np.broadcast_to(bad_shape, (2,))

    def factory(seed):
        factories.append(seed)
        return (BrokenShape if raise_step else SyntheticAdapter)(seed, horizon=8)

    config = study.Config.failure_location(fixture=True)
    assert config.seed == 9002 and config.train_episodes == 6
    assert config.checkpoints == (2, 4) and config.arm_cap == config.pair_cap == 900
    real_config = study.Config.failure_location()
    assert real_config.seed == 8702 and real_config.train_episodes == 1740
    assert real_config.checkpoints == (512, 1024)
    result = study.run_pair(config, tmp_path, time.monotonic(), factory=factory,
                            failure_location=True)
    assert factories == [900210000]
    assert set(result["arms"]) == {"T"} and result["independent_training_samples"] == 0
    assert result["card"] == study.FAILURE_CARD and result["card_section"] == 3
    assert result["scientific_uav_calls"] == 0
    assert result["primary"]["reading"] is None and result["status"] == "INCOMPLETE"
    assert result["primary"]["J"]["F"] == result["primary"]["J"]["G"] == []
    assert result["primary"]["J"]["H"] == []
    saved = json.loads((tmp_path / "summary.json").read_text())
    assert saved["diagnostic_prefix_complete"] == result["diagnostic_prefix_complete"]
    assert result["diagnostic_prefix_complete"] is (not raise_step)
    if raise_step:
        context = json.loads((tmp_path / "failure_context.json").read_text())
        assert context == result["failure_context"]
        assert context["type"] == "ValueError"
        assert "input operand has more dimensions" in context["message"]
        frame = next(frame for frame in context["frames"] if "bad_shape" in frame["ndarrays"])
        assert frame["ndarrays"]["bad_shape"] == {"shape": [2, 1], "dtype": "float32"}
        assert result["counts"]["step_calls"] == 1 and result["counts"]["team_steps"] == 0
        assert result["counts"]["optimizer_steps"] == 0
        assert not (tmp_path / "final_T.pt").exists()
    else:
        assert result["counts"]["team_steps"] == 80
        assert result["counts"]["optimizer_steps"] == 12
        assert result["counts"]["rollouts"] == 3
        assert (tmp_path / "final_T.pt").exists()
        assert not (tmp_path / "failure_context.json").exists()
        assert "failure_context" not in result and result["limits"] == []
    assert not (tmp_path / "final_F.pt").exists()
    assert not (tmp_path / "final_G.pt").exists()
