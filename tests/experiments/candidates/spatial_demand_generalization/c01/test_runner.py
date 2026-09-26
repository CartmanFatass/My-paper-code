"""C01 block identities, isolated A2 reuse, and fixed five-block reading."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.spatial_demand_generalization.a2 import runner as a2
from experiments.candidates.spatial_demand_generalization.c01 import runner as c01
from scripts import run_spatial_demand_generalization_c01 as entry


def _technical_spec(lanes=16):
    return replace(a2.PRODUCTION_SPEC, horizon=10, train_lanes=lanes, eval_lanes=2,
                   rollouts=1, panels=(0, 1), hidden_size=32, n_heads=4,
                   n_layers=1, ppo_epochs=1, sequence_batch_size=4)


def _schedule():
    return {"U": (6,), "M": (6,)}


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_private_binding_and_exact_production_arithmetic():
    original = (a2.SEED, a2.CONFIG_SEED, a2.TRAINING_WORLD_BASE, dict(a2.WORLD_SEED_BASES),
                a2.TAG, a2.OBJECT_ID)
    seen = []
    for block in c01.BLOCKS:
        private = c01.load_block_runner(block)
        seed = c01.model_seed(block)
        seen.append(private)
        assert private.SEED == seed
        assert private.ARMS["U"].seed == private.ARMS["M"].seed == seed
        assert private.CONFIG_SEED == 269900000 + 1000 * block
        assert private.TRAINING_WORLD_BASE == 264000000 + 100000 * block
        assert private.WORLD_SEED_BASES == c01.EVALUATION_BASES
        assert private.TAG == c01.tag_for(block)
        assert private.OBJECT_ID == c01.OBJECT_ID
        assert private.training_families("M", 0, 16).count("cluster") == 8
        source_names = {path.relative_to(c01.ROOT).as_posix() for path in private._source_paths()}
        assert "experiments/candidates/spatial_demand_generalization/a2/adapter.py" in source_names
        assert "experiments/candidates/spatial_demand_generalization/c01/runner.py" in source_names
        assert "scripts/run_spatial_demand_generalization_c01.py" in source_names
        assert "scripts/run_spatial_demand_generalization_a2.py" not in source_names
    assert len({id(module) for module in seen}) == 5
    assert (a2.SEED, a2.CONFIG_SEED, a2.TRAINING_WORLD_BASE, dict(a2.WORLD_SEED_BASES),
            a2.TAG, a2.OBJECT_ID) == original
    counts = a2._expected_arm_counts(a2.SCHEDULES["U"], a2.PRODUCTION_SPEC)
    reused = a2._expected_arm_counts(a2.SCHEDULES["M"], a2.PRODUCTION_SPEC,
                                     common_stage0=True)
    assert 5 * (counts["training_team_steps"] + reused["training_team_steps"]) == 3_600_000
    assert 5 * (counts["evaluation_team_steps"] + reused["evaluation_team_steps"]) == 720_000
    assert 5 * (counts["training_uav_steps"] + reused["training_uav_steps"] +
                counts["evaluation_uav_steps"] + reused["evaluation_uav_steps"]) == 25_920_000


def test_entry_rejects_wrong_seed_and_admission_precedes_runner(tmp_path, monkeypatch):
    out = tmp_path / c01.tag_for(0)
    calls = []

    def admission(*args, **kwargs):
        calls.append("admission")
        raise RuntimeError("technical admission refusal")

    def forbidden_run(*args, **kwargs):
        calls.append("scientific run")
        raise AssertionError("runner reached before admission")

    monkeypatch.setattr(entry, "require_admission", admission)
    args = ["--block", "0", "--seed", "263000101", "--launch-sha", "sha",
            "--out", str(out)]
    with pytest.raises(SystemExit):
        entry.main([*args[:3], "263000102", *args[4:]], run_fn=forbidden_run)
    assert calls == [] and not out.exists()
    with pytest.raises(RuntimeError, match="technical admission refusal"):
        entry.main(args, run_fn=forbidden_run)
    assert calls == ["admission"] and not out.exists()
    monkeypatch.setattr(entry, "require_admission", lambda *a, **kw: {"sha": "other-sha"})
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main(args, run_fn=forbidden_run)
    assert calls == ["admission"] and not out.exists()


def test_two_real_technical_blocks_have_distinct_learning_and_common_physical_panels(tmp_path):
    summaries = []
    for block in (0, 1):
        out = tmp_path / c01.tag_for(block)
        code = c01.run_block(
            out, "technical-sha", {"sha": "technical-sha"}, block,
            spec=_technical_spec(), technical_seed=280000101 + block,
            technical_constructor_base=289900000 + 1000 * block,
            schedules=_schedule(),
        )
        assert code == 0, (out / "error.txt").read_text() if (out / "error.txt").exists() else ""
        batch = _json(out / "summary.json")
        summaries.append((out, batch))
        assert batch["status"] == "complete" and batch["block"] == block
        assert batch["seed"] == batch["model_seed"] == 280000101 + block
        assert batch["planned_model_seed"] == c01.model_seed(block)
        assert batch["counts"]["training_team_steps"] == 320
        assert batch["counts"]["evaluation_team_steps"] == 180
        assert batch["source_hashes_unchanged"] is True
        assert all(value for key, value in batch["initial_identity"].items()
                   if key.endswith("_equal"))
        assert batch["common_training_world_identity"]["all_equal"]
        for arm in ("U", "M"):
            row = _json(out / arm / "summary.json")
            config = _json(out / arm / "config.json")
            assert row["direction"] == config["direction"] == c01.DIRECTION
            assert row["object_id"] == config["object_id"] == c01.OBJECT_ID
            assert row["block"] == config["block"] == block
            assert row["model_seed"] == config["model_seed"] == 280000101 + block
            assert config["config_constructor_seed"] == 289900000 + 1000 * block
            assert row["optimizer_calls"]["discoverer_actor"] > 0
            for checkpoint in row["checkpoints"]:
                path = out / arm / checkpoint["relative_to_arm"]
                payload = torch.load(path, map_location="cpu", weights_only=True)
                assert payload["direction"] == c01.DIRECTION
                assert payload["object_id"] == c01.OBJECT_ID
                assert payload["tag"] == c01.tag_for(block)
                assert payload["block"] == block and payload["arm"] == arm
                assert payload["model_seed"] == 280000101 + block
                assert checkpoint["sha256"] == a2.b15.file_sha256(path)
            with np.load(out / arm / "raw/training_reset_r01_n6.npz", allow_pickle=False) as scene:
                assert scene["lane_world_seeds"][0] == 274000000 + 100000 * block
                assert tuple(scene["families"]) == a2.training_families(arm, 0, 16)
    (out0, b0), (out1, b1) = summaries
    assert b0["source_hashes_before"] == b1["source_hashes_before"]
    assert _json(out0 / "U/summary.json")["initialization"]["parameter_normalizer_digest"] != \
           _json(out1 / "U/summary.json")["initialization"]["parameter_normalizer_digest"]
    initial0 = _json(out0 / "U/raw/initialization.json")
    initial1 = _json(out1 / "U/raw/initialization.json")
    assert initial0["post_initialization_rng_digest"] != initial1["post_initialization_rng_digest"]
    assert initial0["runtime_digest"] != initial1["runtime_digest"]
    assert initial0["initial_buffer"]["sampler_seed"] != initial1["initial_buffer"]["sampler_seed"]
    assert initial0["initial_buffer"]["sampler_state"] != initial1["initial_buffer"]["sampler_state"]
    for family in c01.FAMILIES:
        first = next(row for row in _json(out0 / "U/summary.json")["panels"]
                     if row["policy_stage"] == 0 and row["family"] == family)
        second = next(row for row in _json(out1 / "U/summary.json")["panels"]
                      if row["policy_stage"] == 0 and row["family"] == family)
        assert first["initial_world_identity"] == second["initial_world_identity"]
        assert first["world_seeds"] == second["world_seeds"]


def test_c01_private_small_path_matches_unchanged_a2_numerics(tmp_path):
    spec = _technical_spec(lanes=2)
    seed = 280000200
    a2_out = tmp_path / a2.TAG
    assert a2.run_batch(a2_out, "technical-sha", {"sha": "technical-sha"},
                        spec=spec, technical_seed=seed, schedules=_schedule()) == 0
    private = c01.load_block_runner(0, technical_constructor_base=a2.CONFIG_SEED)
    private.TRAINING_WORLD_BASE = a2.TRAINING_WORLD_BASE
    private.WORLD_SEED_BASES = dict(a2.WORLD_SEED_BASES)
    c01_out = tmp_path / c01.tag_for(0)
    assert private.run_batch(c01_out, "technical-sha", {"sha": "technical-sha"},
                             spec, technical_seed=seed, schedules=_schedule()) == 0
    for arm in ("U", "M"):
        original = _json(a2_out / arm / "summary.json")
        adapted = _json(c01_out / arm / "summary.json")
        assert original["initialization"]["parameter_normalizer_digest"] == \
               adapted["initialization"]["parameter_normalizer_digest"]
        assert original["final_parameter_normalizer_digest"] == \
               adapted["final_parameter_normalizer_digest"]
        assert original["optimizer_calls"] == adapted["optimizer_calls"]
        for old, new in zip(original["panels"], adapted["panels"]):
            assert old["family"] == new["family"]
            np.testing.assert_array_equal(old["J"], new["J"])
            np.testing.assert_array_equal(old["service_arrays"]["S_served_users_per_step"],
                                          new["service_arrays"]["S_served_users_per_step"])


def _fixture_block(root: Path, block: int, delta_j: float, delta_s: float,
                   *, source="same", physical="same") -> Path:
    # Keep the fixture anchored to a published native production schema. Scores below
    # are synthetic and are used only to check the offline arithmetic/refusal rules.
    native = c01.ROOT / "runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101"
    out = root / c01.tag_for(block)
    out.mkdir()
    seed, tag = c01.model_seed(block), c01.tag_for(block)
    native_batch = _json(native / "summary.json")
    sources = dict(native_batch["source_hashes_before"])
    sources.pop("scripts/run_spatial_demand_generalization_a2.py")
    sources.update({
        "experiments/candidates/spatial_demand_generalization/c01/runner.py": source,
        "experiments/candidates/spatial_demand_generalization/c01/__init__.py": source,
        "scripts/run_spatial_demand_generalization_c01.py": source,
    })
    counts_by_arm = {}
    for arm in ("U", "M"):
        arm_dir = out / arm
        arm_dir.mkdir()
        row = _json(native / arm / "summary.json")
        config = _json(native / arm / "config.json")
        panels = row["panels"]
        for panel in panels:
                stage, family = panel["policy_stage"], panel["family"]
                j = 0.2 if stage == 0 else 1.0 + (delta_j if arm == "M" else 0.0)
                service = 10.0 if stage == 0 else 20.0 + (delta_s if arm == "M" else 0.0)
                worlds = list(range(c01.EVALUATION_BASES[family], c01.EVALUATION_BASES[family] + 32))
                panel["world_seeds"] = worlds
                panel["initial_world_identity"] = {key: physical for key in
                                                   panel["initial_world_identity"]}
                panel["J"] = [j] * 32
                panel["component_means"]["coverage_reward"] = [service / 50] * 32
                panel["component_means"]["quality_reward"] = [0.5] * 32
                panel["component_means"]["energy_penalty"] = [0.1] * 32
                panel["service_arrays"]["E_eligible_users_per_step"] = [40] * 32
                panel["service_arrays"]["S_served_users_per_step"] = [service] * 32
                panel["service_arrays"]["U_eligible_unserved_users_per_step"] = [40 - service] * 32
                panel["uav_height_means_per_world"] = [100] * 32
        counts = row["counts"]
        counts_by_arm[arm] = counts
        identity = {"direction": c01.DIRECTION, "object_id": c01.OBJECT_ID,
                    "tag": tag, "block": block, "seed": seed, "model_seed": seed,
                    "planned_model_seed": seed, "arm": arm}
        row.update(identity, launch_sha="fixed-sha", source_hashes_unchanged=True,
                   source_hashes_before=sources, source_hashes_after=sources)
        config.update(identity, launch_sha="fixed-sha", world_seed_bases=c01.EVALUATION_BASES,
                      config_constructor_seed=c01.CONSTRUCTOR_BASE + 1000 * block,
                      training_world_seed_formula=
                      f"{c01.TRAINING_BASE + 100000 * block} + 1000 * (rollout - 1) + lane")
        config["config"]["seed"] = seed
        for checkpoint in row["checkpoints"]:
            checkpoint.update({key: identity[key] for key in
                               ("direction", "object_id", "tag", "block", "model_seed", "arm")})
        (arm_dir / "summary.json").write_text(json.dumps(row))
        (arm_dir / "config.json").write_text(json.dumps(config))
    batch = native_batch
    batch.update(direction=c01.DIRECTION, object_id=c01.OBJECT_ID, tag=tag,
                 block=block, seed=seed, model_seed=seed, planned_model_seed=seed,
                 launch_sha="fixed-sha", source_hashes_unchanged=True,
                 source_hashes_before=sources, source_hashes_after=sources)
    for arm in ("U", "M"):
        batch["arms"][arm]["counts"] = counts_by_arm[arm]
    path = out / "summary.json"
    path.write_text(json.dumps(batch))
    return path


def test_five_block_interval_and_strict_incomplete_mismatch_refusal(tmp_path):
    paths = [_fixture_block(tmp_path, block, float(block + 1), float(block + 2))
             for block in c01.BLOCKS]
    result = c01.aggregate_five_blocks(paths)
    assert result["primary_joint_lower_bounds_positive"] is True
    j = result["primary_hotspot"]["J"]
    s = result["primary_hotspot"]["S"]
    assert j["block_values"] == [1, 2, 3, 4, 5]
    assert j["mean"] == 3 and s["mean"] == 4
    assert j["sample_sd"] == pytest.approx(np.sqrt(2.5))
    assert j["lower_95"] == pytest.approx(3 - c01.T975_DF4 * np.sqrt(2.5) / np.sqrt(5))
    assert len(result["by_family"]["uniform"]["blocks"]) == 5
    assert len(result["by_family"]["hotspot"]["blocks"][0]["per_world_M_minus_U"]["J"]) == 32
    assert all(result["by_family"][family]["blocks"][0]["mean_U_minus_initial"]["J"] > 0
               for family in c01.FAMILIES)
    with pytest.raises(ValueError):
        c01.aggregate_five_blocks(paths[:4])
    with pytest.raises(ValueError):
        c01.aggregate_five_blocks(paths[:4] + paths[:1])
    one = _json(paths[4]); one["status"] = "failed"; paths[4].write_text(json.dumps(one))
    with pytest.raises(ValueError):
        c01.aggregate_five_blocks(paths)
    one["status"] = "complete"
    one["source_hashes_before"] = _json(paths[0])["source_hashes_before"]
    one["source_hashes_after"] = one["source_hashes_before"]
    one["initial_identity"].pop("runtime_digest_equal")
    paths[4].write_text(json.dumps(one))
    with pytest.raises(ValueError, match="initialization"):
        c01.aggregate_five_blocks(paths)
    one["initial_identity"]["runtime_digest_equal"] = True
    paths[4].write_text(json.dumps(one))
    arm_path = paths[4].parent / "M/summary.json"
    arm = _json(arm_path)
    changed_panel = next(row for row in arm["panels"]
                         if row["policy_stage"] == 45 and row["family"] == "hotspot")
    changed_panel["initial_world_identity"]["states"] = "different"
    arm_path.write_text(json.dumps(arm))
    with pytest.raises(ValueError, match="physical"):
        c01.aggregate_five_blocks(paths)
    changed_panel["initial_world_identity"]["states"] = "same"
    arm_path.write_text(json.dumps(arm))
    for arm_name in ("U", "M"):
        panel_path = paths[4].parent / arm_name / "summary.json"
        panel_summary = _json(panel_path)
        for panel in panel_summary["panels"]:
            if panel["family"] == "hotspot":
                panel["initial_world_identity"]["states"] = "different across blocks"
        panel_path.write_text(json.dumps(panel_summary))
    with pytest.raises(ValueError, match="cross-block physical"):
        c01.aggregate_five_blocks(paths)
    for arm_name in ("U", "M"):
        panel_path = paths[4].parent / arm_name / "summary.json"
        panel_summary = _json(panel_path)
        for panel in panel_summary["panels"]:
            if panel["family"] == "hotspot":
                panel["initial_world_identity"]["states"] = "same"
        panel_path.write_text(json.dumps(panel_summary))
    one["status"] = "complete"; one["source_hashes_before"]["scripts/run_spatial_demand_generalization_c01.py"] = "changed"
    one["source_hashes_after"] = one["source_hashes_before"]
    paths[4].write_text(json.dumps(one))
    with pytest.raises(ValueError, match="different source"):
        c01.aggregate_five_blocks(paths)


def test_known_nonpassing_interval_without_equivalence_claim():
    interval = c01._interval([-2, -1, 0, 1, 2])
    assert interval["mean"] == 0
    assert interval["lower_95"] < 0 < interval["upper_95"]
    assert interval["signs"] == {"positive": 2, "zero": 1, "negative": 2}
