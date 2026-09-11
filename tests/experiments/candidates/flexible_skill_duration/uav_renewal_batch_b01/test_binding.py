"""One explicitly synthetic binding/sampler/primary fixture; no learner or host.

Run directly with --scratch pointing to this invocation's directory under temp/.
The caller retains this report, removes its scratch, and measures complete wall.
"""
import argparse
import inspect
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import numpy as np
import run_fsd_uav_renewal_batch_b01 as binding
from hmasd.utils import RolloutBuffer

shared = binding.shared


def synthetic_arm(arm, configs, scores):
    """Supplied metadata only: the counts below never describe executed learning."""
    return {
        "synthetic_fixture": True, "object_id": binding.OBJECT_ID, "card": binding.CARD,
        "arm": arm, "status": "complete", "training_seed": binding.TRAINING_SEED,
        "evaluation_seed": binding.EVALUATION_SEED,
        "training_lane_seeds": list(range(binding.TRAINING_SEED, binding.TRAINING_SEED + 16)),
        "evaluation_lane_seeds": list(range(binding.EVALUATION_SEED, binding.EVALUATION_SEED + 32)),
        "host": {"synthetic_fixture": True}, "device": "cpu", "torch_threads": 4,
        "learner_precision": "float32", "reward_return_precision": "float64",
        "native_score_factor": 6 / 500,
        "learner_config": configs[arm]["learner"], "evaluation_config": configs[arm]["evaluation"],
        "counts": {"training_transitions": 40000, "stored_training_transitions": 40000,
                   "training_episodes": 80, "update_stages": 5, "model_constructions": 2,
                   "training_starts": 1, "checkpoint_loads": 0, "training_agent_step_batches": 2500,
                   "evaluation_steps": 16000, "evaluation_agent_step_batches": 500,
                   "evaluation_episodes": 32},
        "training_rows": [{"updated": True} for _ in range(5)], "evaluation_optimizer_calls": {},
        "evaluation": {"status": "complete", "after_update": 5, "episode_ids": list(range(32)),
                       "lane_seeds": list(range(binding.EVALUATION_SEED, binding.EVALUATION_SEED + 32)),
                       "steps_per_lane": [500] * 32, "completed_episodes": 32,
                       "returns_U": (scores * 500 / 6).tolist(), "native_scores_J": scores.tolist()}}


def run_fixture(scratch):
    # This record supplies dimensions only. It has no environment constructor or methods.
    class Dimensions:
        state_dim, obs_dim = 45, 19

    configs = {"I": {}, "D0": {}}
    for arm in configs:
        for phase, lanes, seed in (("learner", 16, binding.TRAINING_SEED),
                                   ("evaluation", 32, binding.EVALUATION_SEED)):
            config = binding.make_config(arm, [Dimensions] * lanes, seed)
            assert config.coordinator_batch_size == (1280 if arm == "I" else 128)
            assert config.interruption_cost_c == (.25 if arm == "I" else float("inf"))
            assert config.interruption_cost_c_Z == float("inf")
            assert (config.policy_interruption_mode, config.k, config.skill_cap_k_max,
                    config.team_cap_k_Z, config.interruption_delta, config.age_feature) == (
                        "d2", 10, 10, 10, 1, "off")
            configs[arm][phase] = shared.config_snapshot(config)

    # Old B01/B02 leave this argument False; no fifth Config or old learner is built.
    for function in (shared.make_config, shared.build_learner, shared.Evaluator,
                     shared.final_evaluation, shared.assemble_pair, shared.main):
        assert inspect.signature(function).parameters["renewal_batch"].default is False
    assert (shared.TRAIN_SEED, shared.EVAL_SEED) == (770503, 780503)
    assert shared.CAPS == {"D0": 3600., "I": 18000.}
    assert inspect.signature(shared.main).parameters["caps"].default is shared.CAPS
    assert "coordinator_batch_size" not in vars(shared.e0.Config)

    # One buffer, 1281 valid joint rows plus one invalid row, with six head masks.
    buffer = RolloutBuffer(1282, 1, 6, 1, 1, 1, 6, 6, 1, d2_enabled=True, sampler_seed=0)
    buffer.masks[:] = True
    buffer.env_lengths[:] = 1282
    buffer.states[:, 0, 0] = np.arange(1282)
    buffer.obs[:, 0, :, 0] = np.arange(1282)[:, None]
    buffer.d2_agent_valid[:640, 0, 0] = True
    buffer.d2_team_valid[640:1281, 0] = True
    buffer.d2_order[:] = np.arange(6)
    buffer.d2_agent_skills[:] = 1
    buffer.d2_team_skill[:] = 2
    traversals = []
    for batch_size in (1280, 128):
        visited, sizes = [], []
        for batch in buffer.get_d2_coordinator_sampler(1282, 1, batch_size):
            ids = batch["states"][:, 0].numpy().astype(int)
            visited.extend(ids.tolist())
            sizes.append(len(ids))
            assert batch["observations"].shape == (len(ids), 6, 1)
            assert np.array_equal(batch["observations"][:, 0, 0].numpy(), ids)
            assert np.array_equal(batch["agent_valid"][:, 0].numpy(), ids < 640)
            assert np.array_equal(batch["team_valid"].numpy(), ids >= 640)
            assert not batch["agent_valid"][:, 1:].any()
        assert sorted(visited) == list(range(1281))
        assert sizes == ([1280, 1] if batch_size == 1280 else [128] * 10 + [1])
        traversals.append({"batch_size": batch_size, "chunks": sizes,
                           "valid_rows_visited_once": len(visited), "invalid_row_excluded": True})

    control_scores = np.full(32, .2)
    delta = np.array([.04, -.005] * 16)
    treatment = synthetic_arm("I", configs, control_scores + delta)
    control = synthetic_arm("D0", configs, control_scores)
    readouts = []
    for sign, branch in ((1, "above_mei"), (-1, "opposite_sign")):
        scores = control_scores + sign * delta
        treatment["evaluation"].update(native_scores_J=scores.tolist(), returns_U=(scores * 500 / 6).tolist())
        result = binding.assemble_pair(treatment, control)
        primary = result["i_minus_d0"]
        np.testing.assert_allclose(primary["differences"], sign * delta, rtol=1e-7, atol=1e-8)
        expected_sd = math.sqrt(32 * .0225 ** 2 / 31)
        assert math.isclose(primary["mean"], sign * .0175, abs_tol=1e-8)
        assert math.isclose(primary["sample_sd"], expected_sd, abs_tol=1e-8)
        assert math.isclose(primary["conditional_se"], expected_sd / math.sqrt(32), abs_tol=1e-8)
        assert result["independent_training_pairs"] == 1 and result["card_reading"] == branch
        readouts.append({"synthetic_fixture": True, "case": branch, "result": result})

    original_gamma = control["learner_config"]["gamma"]
    control["learner_config"]["gamma"] = .9
    try:
        binding.assemble_pair(treatment, control)
    except ValueError as exc:
        assert str(exc) == "pair mismatch: learner_config"
        readouts.append({"synthetic_fixture": True, "case": "undeclared_gamma", "rejected": str(exc)})
    else:
        raise AssertionError("undeclared configuration difference accepted")
    finally:
        control["learner_config"]["gamma"] = original_gamma

    treatment["evaluation"]["returns_U"] = None  # All 32 J scores remain supplied.
    try:
        binding.assemble_pair(treatment, control)
    except ValueError as exc:
        assert str(exc) == "I missing primary values"
        readouts.append({"synthetic_fixture": True, "case": "missing_U", "rejected": str(exc)})
    else:
        raise AssertionError("missing primary accepted")

    report = {"synthetic_fixture": True, "status": "pass", "configs": configs,
              "old_defaults_static": "preserved", "traversals": traversals, "readouts": readouts,
              "actual_exposure": {"fixture_commands": 1, "configuration_objects": 4, "buffers": 1,
                                  "valid_joint_rows": 1281, "sampler_traversals": 2, "paired_readouts": 4,
                                  "models": 0, "checkpoint_loads": 0, "environments": 0,
                                  "environment_steps": 0, "training_starts": 0, "optimizer_calls": 0,
                                  "real_endpoint_evaluations": 0, "replay": 0, "profiling": 0,
                                  "support_search": 0, "scientific_invocations": 0}}
    path = scratch / "synthetic_primary.json"
    shared.write_json(path, report)
    assert json.loads(path.read_text(encoding="utf-8")) == report
    assert not path.with_suffix(".partial.json").exists()
    print(json.dumps({"synthetic_fixture": True, "status": "pass", "actual_exposure": report["actual_exposure"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", type=Path, required=True)
    run_fixture(parser.parse_args().scratch)
