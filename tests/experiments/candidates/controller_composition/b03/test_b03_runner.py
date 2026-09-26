import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.controller_composition.b01.bindings import CHECKPOINT_ROOT, SOURCE
from experiments.candidates.controller_composition.b01.runner import validate_sources
from experiments.candidates.controller_composition.b02 import runner as b02
from experiments.candidates.controller_composition.b03 import runner
from experiments.candidates.controller_composition.b03.bindings import BLOCKS, EVAL_CELLS
from experiments.candidates.controller_composition.b03.reducer import reduce_panel
from scripts import run_controller_composition_b03 as entry


def _sources():
    override = os.environ.get("HMASD_CONTROLLER_COMPOSITION_CHECKPOINTS")
    if override:
        paths = dict(zip(SOURCE, map(Path, json.loads(override))))
    else:
        paths = {i: Path(CHECKPOINT_ROOT) / row["tag"] / "F/raw/checkpoint_45.pt"
                 for i, row in SOURCE.items()}
    return validate_sources(paths)[0]


def test_tiny_real_both_arms_and_new_seeds(tmp_path):
    torch.set_num_threads(4)
    payloads = _sources()
    spec = replace(b02.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    initial = []
    fixture_world_bases = {"B1": 8100, "B2": 9100}
    for block, identity in BLOCKS.items():
        block_out = tmp_path / block
        (block_out / "raw").mkdir(parents=True)
        rng = np.random.default_rng(identity["assignment_seed"])
        fits = []
        snapshots = {}
        for arm in ("F2", "M"):
            fit, snapshot = b02._fit(arm, payloads, rng, block_out, "fixture-sha",
                              {"completed_rollouts": []}, spec,
                              world_base=fixture_world_bases[block],
                              learner_seed=identity["learner_seed"],
                              object_name="controller_composition_b03")
            fits.append(fit)
            snapshots[arm] = snapshot
            assert fit["config"]["seed"] == identity["learner_seed"]
            assert fit["learner_seed"] == identity["learner_seed"]
            expected_sampler = int(np.random.SeedSequence(
                [identity["learner_seed"], 0x484D4153, 0]
            ).generate_state(1, dtype=np.uint64)[0])
            assert fit["rollout_sampler_seed"] == expected_sampler
            assert fit["optimizer_calls"]["discoverer_actor"] == 15
            assert fit["optimizer_calls"]["discoverer_critic"] == 15
            assert fit["counts"]["team_steps"] == 20
            assert fit["rollouts"][0]["world"]["lane_world_seeds"] == [
                fixture_world_bases[block] + 100, fixture_world_bases[block] + 101]
            saved = torch.load(block_out / fit["initial_checkpoint"]["path"],
                               weights_only=True)
            assert saved["object"] == "controller_composition_b03"
            assert saved["config"]["seed"] == identity["learner_seed"]
        assert fits[0]["initial_digest"] == fits[1]["initial_digest"]
        assert fits[0]["initial_optimizer_state_digest"] == fits[1]["initial_optimizer_state_digest"]
        assert fits[0]["initial_sampler_rng_sha256"] == fits[1]["initial_sampler_rng_sha256"]
        assert fits[0]["rollout_sampler_seed"] == fits[1]["rollout_sampler_seed"]
        assert fits[0]["rollouts"][0]["world"]["states"] == fits[1]["rollouts"][0]["world"]["states"]
        assert fits[0]["rollouts"][0]["world"]["observations"] == fits[1]["rollouts"][0]["world"]["observations"]
        assert sorted(fits[1]["rollouts"][0]["assignment"]) == [1, 2]
        cell = b02._eval_cell("M", 3, snapshots, payloads, block_out, spec,
                              world_base=711, learner_seed=identity["learner_seed"])
        assert cell["counts"]["team_steps"] == 20
        assert cell["counts"]["optimizer_updates"] == 0
        assert cell["world_seeds"] == [711, 712]
        initial.append(fits[0])
    assert initial[0]["initial_digest"] != initial[1]["initial_digest"]
    assert initial[0]["rollout_sampler_seed"] != initial[1]["rollout_sampler_seed"]
    assert initial[0]["initial_sampler_rng_sha256"] != initial[1]["initial_sampler_rng_sha256"]
    assert initial[0]["rollouts"][0]["world"]["states"] != initial[1]["rollouts"][0]["world"]["states"]


def test_reducer_all_nineteen_cells_and_joint_bootstrap():
    worlds, draws = 7, 101
    fixture_rng = np.random.default_rng(614)
    j = fixture_rng.normal(size=(worlds, 19)) * 3 + np.arange(19) / 4
    service = fixture_rng.normal(size=(worlds, 19)) + .37 * j
    values = reduce_panel(j, service, draws=draws, seed=37)
    assert values["cell_order"] == [list(cell) for cell in EVAL_CELLS]
    lookup = {cell: i for i, cell in enumerate(EVAL_CELLS)}
    contrasts = {}
    for cell, index in lookup.items():
        weight = np.zeros(19)
        weight[index] = 1
        contrasts[f"{cell[0]}_{cell[1]}_partner{cell[2]}"] = weight
    for block in BLOCKS:
        for p in (1, 2, 3):
            contrast = np.zeros(19)
            contrast[lookup[block, "M", p]] = 1
            contrast[lookup[block, "F2", p]] = -1
            contrasts[f"{block}_M_minus_F2_partner{p}"] = contrast
            for arm in ("F2", "M"):
                own = np.zeros(19)
                own[lookup[block, arm, p]] = 1
                own[lookup[block, "I", p]] = -1
                contrasts[f"{block}_{arm}_minus_initial_partner{p}"] = own
        for arm in ("F2", "M"):
            reuse = np.zeros(19)
            reuse[lookup[block, arm, 3]] = 1
            reuse[lookup["shared", "OLD3", 3]] = -1
            contrasts[f"{block}_{arm}_minus_old3_reuse_partner3"] = reuse
        contrasts[f"{block}_H_partner3_relative_gain"] = (
            contrasts[f"{block}_M_minus_F2_partner3"] -
            (contrasts[f"{block}_M_minus_F2_partner1"] +
             contrasts[f"{block}_M_minus_F2_partner2"]) / 2)
    indices = np.random.default_rng(37).integers(worlds, size=(draws, worlds))
    # Frequency weights form an independent oracle for whole-world resampling.
    frequencies = np.stack([np.bincount(row, minlength=worlds) for row in indices])
    for metric, matrix in (("J", j), ("S_served_users_per_step", service)):
        observed = values[metric]
        assert set(observed["finite_panel"]) == set(contrasts)
        for key, weight in contrasts.items():
            world_values = matrix @ weight
            expected_bootstrap = frequencies @ world_values / worlds
            np.testing.assert_allclose(observed["per_world"][key], world_values)
            assert observed["finite_panel"][key] == pytest.approx(world_values.mean())
            np.testing.assert_allclose(observed["pointwise_95_percentiles"][key],
                                       np.percentile(expected_bootstrap, [2.5, 97.5]))
    assert np.ptp(j @ contrasts["B1_M_minus_F2_partner1"]) > 1
    assert np.ptp(service @ contrasts["B2_M_minus_F2_partner3"]) > 1


def test_entry_admits_before_science(tmp_path, monkeypatch):
    calls = []
    def admit(*args, **kwargs):
        calls.append("admit")
        return {"sha": "fixture-sha"}
    monkeypatch.setattr(entry, "require_admission", admit)
    def run(*args, **kwargs):
        calls.append("run")
    entry.main(["--seed", "92561001", "--launch-sha", "fixture-sha", "--out", str(tmp_path),
                "--checkpoints", "one", "two", "three"], run_fn=run)
    assert calls == ["admit", "run"]
    calls.clear()
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main(["--launch-sha", "wrong", "--out", str(tmp_path),
                    "--checkpoints", "one", "two", "three"], run_fn=run)
    assert calls == ["admit"]


def test_partial_failure_keeps_prefix(tmp_path, monkeypatch):
    out = tmp_path / "batch"
    out.mkdir()
    monkeypatch.setattr(runner.b01, "validate_sources", lambda paths: ({}, {}))
    calls = []
    def fit(arm, payloads, rng, path, sha, progress, spec, **kwargs):
        calls.append((path.name, arm))
        if len(calls) == 2:
            raise RuntimeError("fixture second fit failure")
        artifact = path / "raw" / "init_F2.pt"
        torch.save({"object": "controller_composition_b03"}, artifact)
        return {"config": {"seed": kwargs["learner_seed"]},
                "learner_seed": kwargs["learner_seed"],
                "rollout_sampler_seed": int(np.random.SeedSequence(
                    [kwargs["learner_seed"], 0x484D4153, 0]).generate_state(1, dtype=np.uint64)[0]),
                "initial_digest": "first",
                "initial_checkpoint": b02._artifact(artifact, path),
                "rollouts": [{"world": {"lane_world_seeds": list(range(kwargs["world_base"] + 100,
                                                                    kwargs["world_base"] + 100 + spec.train_lanes))}}]}, {}
    monkeypatch.setattr(runner.b02, "_fit", fit)
    spec = replace(b02.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    with pytest.raises(RuntimeError, match="fixture second fit failure"):
        runner.run_study(out, "fixture-sha", {"sha": "fixture-sha"},
                         {1: Path("a"), 2: Path("b"), 3: Path("c")},
                         seed=92561001, command_start=runner.time.perf_counter(), spec=spec)
    assert calls == [("B1", "F2"), ("B1", "M")]
    assert (out / "B1/raw/init_F2.pt").is_file()
    assert json.loads((out / "progress.json").read_text())["completed_fits"] == [["B1", "F2"]]
    assert json.loads((out / "progress.json").read_text())["status"] == "failed"


def test_complete_runner_orders_nineteen_namespaced_cells(tmp_path, monkeypatch):
    out = tmp_path / "batch"
    out.mkdir()
    monkeypatch.setattr(runner.b01, "validate_sources", lambda paths: ({}, {"source": "digest"}))
    spec = replace(b02.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    def fit(arm, payloads, rng, path, sha, progress, spec, **kwargs):
        block = path.name
        artifact = path / "raw" / f"init_{arm}.pt"
        torch.save({"object": "controller_composition_b03", "block": block}, artifact)
        log = path / "raw" / "logs" / f"fit_{arm}.log"
        log.parent.mkdir(exist_ok=True)
        log.write_text("fixture log")
        world = {"lane_world_seeds": [kwargs["world_base"] + 100,
                                        kwargs["world_base"] + 101],
                 "states": block, "observations": block,
                 "uav_positions": block, "user_positions": block}
        result = {"config": {"seed": kwargs["learner_seed"]},
                  "learner_seed": kwargs["learner_seed"],
                  "rollout_sampler_seed": int(np.random.SeedSequence(
                      [kwargs["learner_seed"], 0x484D4153, 0]).generate_state(1, dtype=np.uint64)[0]),
                  "initial_sampler_rng_sha256": block,
                  "initial_digest": block, "initial_optimizer_state_digest": block,
                  "initial_normalizers": {}, "initial_checkpoint": b02._artifact(artifact, path),
                  "rollouts": [{"world": world, "assignment": [2, 2] if arm == "F2" else [1, 2]}],
                  "optimizer_calls": {"discoverer_actor": 15, "discoverer_critic": 15},
                  "counts": {"team_steps": 20, "executed_learner_rows": 60,
                             "executed_partner_rows": 60, "learner_inferred_rows": 120,
                             "partner_inferred_rows": 120}}
        return result, {"payload": {}, "digest": block}
    monkeypatch.setattr(runner.b02, "_fit", fit)
    called = []
    def evaluate(learner, partner, snapshots, payloads, path, spec, **kwargs):
        called.append((path.name, learner, partner, kwargs["learner_seed"]))
        return {"cell": [learner, partner], "world_seeds": [711, 712],
                "initial_world_identity": {"scene": "common"},
                "initial_world_identity_per_world": ["same", "same"],
                "per_world": {"J": [float(partner)] * 2, "S": [float(partner) / 10] * 2},
                "counts": {"team_steps": 20, "executed_action_rows": 120,
                           "inferred_action_rows": 240}}
    monkeypatch.setattr(runner.b02, "_eval_cell", evaluate)
    # The fixed production address is checked separately; only fixture outputs are constructed.
    monkeypatch.setattr(runner, "EVAL_WORLD_BASE", 711)
    summary = runner.run_study(out, "fixture-sha", {"sha": "fixture-sha"},
                               {1: Path("a"), 2: Path("b"), 3: Path("c")},
                               seed=92561001, command_start=runner.time.perf_counter(), spec=spec)
    assert summary["status"] == "complete"
    assert [(b, a, p) for b, a, p, _ in called] == list(EVAL_CELLS)
    assert len(called) == 19
    assert called[0][3] == BLOCKS["B1"]["learner_seed"]
    assert called[9][3] == BLOCKS["B2"]["learner_seed"]
    assert summary["counts"]["training_team_steps"] == 80
    assert summary["counts"]["evaluation_team_steps"] == 380
    assert summary["counts"]["actor_optimizer_calls"] == 60
    assert json.loads((out / "config.json").read_text())["runtime_seed"] == b02.RUNTIME_SEED
    assert "B1/raw/logs/fit_F2.log" in {row["path"] for row in summary["artifacts"]}
    assert summary["fits"][0]["initial_checkpoint"]["path"] == "B1/raw/init_F2.pt"
    assert summary["fits"][2]["initial_checkpoint"]["path"] == "B2/raw/init_F2.pt"
    assert all((out / fit["initial_checkpoint"]["path"]).is_file() for fit in summary["fits"])
    assert json.loads((out / "progress.json").read_text())["status"] == "complete"
