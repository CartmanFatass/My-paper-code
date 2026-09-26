"""Arithmetic fixtures only: no policy, environment or confirmation exposure."""
from copy import deepcopy
import hashlib
import json
import math

import pytest

from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import analysis as a


SHA = "a" * 40


def panel(block, arm, stage, n, service):
    coverage = service / 50
    j = .7*coverage + .3*.2 - .01
    digest = f"{block}_{arm}_{stage}"
    return {
        "status": "complete", "arm": arm, "cell_key": f"b{block}_{arm.lower()}",
        "policy_stage": stage, "after_rollout": stage, "prior_training_team_steps": stage*8000,
        "test_n": n, "world_seeds": list(range(a.WORLD_BASES[n], a.WORLD_BASES[n]+32)),
        "runtime_seed": a.WORLD_BASES[n]+51, "execution_law": "clip",
        "steps": 16000, "episodes": 32, "resets": 32, "policy_step_calls": 500,
        "J": [j]*32, "scalar_returns": [j*500/n]*32,
        "component_means": {"coverage_reward": [coverage]*32, "quality_reward": [.2]*32,
                            "energy_penalty": [.01]*32, "total_reward": [j]*32},
        "service_arrays": {"S_served_users_per_step": [service]*32,
                           "E_eligible_users_per_step": [service+1]*32,
                           "U_eligible_unserved_users_per_step": [1]*32},
        "training_storage_calls": 0, "optimizer_calls": {"actor": 0},
        "frozen_weights_and_normalizers": True, "runtime_evolved": True,
        "post_transition_semantics": True, "parameter_normalizer_digest_before": digest,
        "parameter_normalizer_digest_after": digest, "n_users": 50, "max_connections_per_uav": 10,
        "trace": {"path": f"trace_stage{stage:02d}_n{n}.npz"},
    }


def batch(differences=(4, 5, 6)):
    runs = []
    for (block, seed, base), difference in zip(a.BLOCKS, differences):
        for arm in ("H6", "SET"):
            key = f"b{block}_{arm.lower()}"
            tag = f"{a.OBJECT_ID}_{key}_s{seed}"
            runs.append({
                "object_id": a.OBJECT_ID, "direction": "agent_count_generalization",
                "cell": {"key": key, "arm": arm, "tag": tag, "seed": seed,
                         "train_n": 6, "law": "clip", "lambda_l": .05},
                "arm": arm, "seed": seed, "tag": tag, "launch_sha": SHA,
                "status": "complete", "fit_started": True, "failure": None,
                "config": {"seed": seed, "count_arm": arm, "n_agents": 6, "n_uavs": 6,
                           "k": 10, "lambda_l": .05, "lambda_l_initial": .05,
                           "lambda_l_final": .05, "use_entropy_annealing": False,
                           "use_entropy_targets": False,
                           "use_central_snapshot_in_flat_actor": arm == "SET"},
                "spec": deepcopy(a.SPEC), "counts": deepcopy(a.COUNTS),
                "expected_counts": deepcopy(a.COUNTS),
                "training_world_seeds": list(range(base, base+16)),
                "initial_evaluation_enabled": True,
                "evaluation_order": [{"stage": stage, "test_n": n} for stage in (0, 45) for n in (8, 6)],
                "source_hashes_unchanged": True, "source_hashes_before": {"fixture": "f"*64},
                "source_hashes_after": {"fixture": "f"*64},
                "rollouts": [{"rollout": i, "team_steps": 8000*i} for i in range(1, 46)],
                "optimizer_calls": {"discoverer_actor": 101250, "discoverer_critic": 101250,
                                    "coordinator": 675 if arm == "H6" else 0,
                                    "team_discriminator": 675 if arm == "H6" else 0,
                                    "individual_discriminator": 2700 if arm == "H6" else 0},
                "runtime": {"device": "cpu", "dtype": "float32", "torch_threads": 4},
                "checkpoints": [{"path": "checkpoint_00.pt"}, {"path": "checkpoint_45.pt"}],
                "training_reset_trace": {"path": "training_reset_scenes.npz",
                                         "reset_calls_per_lane": 46, "sha256": str(block)*64},
                "stage_isolation": {str(stage): {"before": {"fixture_state": stage},
                                                "after": {"fixture_state": stage},
                                                **{name+"_preserved": True for name in a.ISOLATION}}
                                    for stage in (0, 45)},
                "observed_initial_parameter_normalizer_digest": f"{block}_{arm}_0",
                "final_parameter_normalizer_digest": f"{block}_{arm}_45",
                "panels": [panel(block, arm, stage, n,
                                 (9 if arm == "H6" else 10) if stage == 0 else
                                 20+(difference if arm == "H6" else 0))
                           for stage, n in ((0, 8), (0, 6), (45, 8), (45, 6))],
            })
    return runs


def test_df2_interval_uses_three_block_means_and_strict_threshold():
    expected_t = math.sqrt(2*.95**2/(1-.95**2))
    assert a.T975_DF2 == pytest.approx(expected_t, abs=1e-14)
    result = a.interval([2, 5, 8], 1)
    assert result["mean"] == 5 and result["sample_sd"] == 3
    assert result["lower"] == pytest.approx(-2.45241313525099)
    assert result["upper"] == pytest.approx(12.45241313525099)
    assert result["reading"] == "inconclusive"
    assert not a.interval([1, 1, 1], 1)["strict_lower_exceeds_threshold"]
    assert not a.interval([0, 0, 0], 0)["strict_lower_exceeds_threshold"]
    assert a.interval([.5, .5, .5], 1)["reading"] == "against_component"


def test_fixed_joint_rule_and_no_world_pseudoreplication():
    result = a.analyze_batch(batch(), SHA)
    assert result["joint_claim_supported_under_stated_model"]
    assert result["primary"]["S"]["block_differences"] == [4, 5, 6]
    assert result["primary"]["S"]["lower"] == pytest.approx(5-a.T975_DF2/math.sqrt(3))
    assert result["primary"]["J"]["mean"] == pytest.approx(.07)
    assert result["counts"]["fits"] == 6
    assert not a.analyze_batch(batch((2, 5, 8)), SHA)["joint_claim_supported_under_stated_model"]
    # J can pass while the prewritten service threshold fails.
    small = a.analyze_batch(batch((.5, .5, .5)), SHA)
    assert small["primary"]["J"]["strict_lower_exceeds_threshold"]
    assert not small["joint_claim_supported_under_stated_model"]


def test_secondary_losses_and_own_regression_do_not_rewrite_primary_rule():
    runs = batch()
    # One N6 final world is adverse for both J and S; preserve it explicitly.
    bad = panel(1, "H6", 45, 6, 8)
    p = runs[0]["panels"][3]
    for key in ("J", "scalar_returns"):
        p[key][0] = bad[key][0]
    for key in ("component_means", "service_arrays"):
        for name in p[key]:
            p[key][name][0] = bad[key][name][0]
    result = a.analyze_batch(runs, SHA)
    assert result["joint_claim_supported_under_stated_model"]
    n6 = result["blocks"][0]["by_test_n"]["6"]
    assert n6["all_final_J_or_service_loss_worlds"][0]["world_seed"] == 1945600
    assert n6["contrasts"]["S"]["I_H"]["values"][0] == -1
    assert n6["absolute"]["S"]["H45"]["minimum"]["value"] == 8
    assert n6["contrasts"]["S"]["D45"]["negative"] == 1


@pytest.mark.parametrize("mutation", [
    lambda r: r.pop(), lambda r: r.__setitem__(1, deepcopy(r[0])),
    lambda r: r[0].__setitem__("status", "failed"),
    lambda r: r[0].__setitem__("launch_sha", "wrong"),
    lambda r: r[0]["counts"].__setitem__("training_team_steps", 359999),
    lambda r: r[0]["config"].__setitem__("seed", 974201),
    lambda r: r[0]["panels"][0]["world_seeds"].reverse(),
    lambda r: r[0]["stage_isolation"]["0"].__setitem__("sampler_rng_digest_preserved", False),
    lambda r: r[0]["training_reset_trace"].__setitem__("sha256", "different"),
    lambda r: r[2].__setitem__("observed_initial_parameter_normalizer_digest", r[0]["observed_initial_parameter_normalizer_digest"]),
    lambda r: r[0]["panels"][2]["J"].__setitem__(0, float("nan")),
    lambda r: r[0]["panels"][2]["service_arrays"]["S_served_users_per_step"].__setitem__(0, 49),
    lambda r: r[0].pop("optimizer_calls"),
])
def test_invalid_or_incomplete_batch_has_no_claim(mutation):
    runs = batch()
    mutation(runs)
    with pytest.raises(a.InvalidBatch):
        a.analyze_batch(runs, SHA)


def test_file_reader_checks_actual_saved_bytes_and_panel_consistency(tmp_path):
    runs = batch()
    for run in runs:
        directory = tmp_path / run["tag"]
        directory.mkdir()
        records = [*run["checkpoints"], run["training_reset_trace"],
                   *(p["trace"] for p in run["panels"])]
        for record in records:
            payload = (str(run["seed"])+record["path"]).encode()
            (directory / record["path"]).write_bytes(payload)
            record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        for p in run["panels"]:
            (directory / f"panel_stage{p['policy_stage']:02d}_n{p['test_n']}.json").write_text(json.dumps(p))
        (directory / "summary.json").write_text(json.dumps(run))
    assert a.read_batch(tmp_path, SHA)["joint_claim_supported_under_stated_model"]
    (tmp_path / runs[0]["tag"] / "checkpoint_45.pt").write_bytes(b"changed")
    with pytest.raises(a.InvalidBatch, match="artifact integrity"):
        a.read_batch(tmp_path, SHA)
