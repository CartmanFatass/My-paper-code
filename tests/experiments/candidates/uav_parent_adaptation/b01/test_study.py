from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.learner import (
    collect_episode as collect_original_geometry,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_parent_adaptation.b01 import collection, model, protocol, study
from experiments.candidates.uav_parent_adaptation import read_b01 as reader

SOURCE = "a" * 40


class NativeInfoFixture(SyntheticAdapter):
    """Synthetic dynamics with complete native-shaped telemetry, never a UAV result."""
    def step(self, actions):
        raw, reward, terminated, truncated, info = super().step(actions)
        connections = np.zeros((5, 50), dtype=bool)
        connections[0, :7] = True
        sinr = np.full((5, 50), 20., dtype=np.float64)
        physical = .014 * 7 + .3 * ((20 - 3) / 30)
        info["rewards_dict"] = {agent: physical / 5 for agent in AGENTS}
        for agent in AGENTS:
            info["infos_dict"][agent]["global"].update(connections=connections.copy(), sinr_matrix=sinr.copy())
        return raw, reward, terminated, truncated, info


@pytest.fixture(autouse=True)
def one_thread():
    torch.set_num_threads(1)


def test_address_blocks_are_independent_except_declared_pairing():
    all_used = set()
    for lineage in protocol.LINEAGES:
        for stage in ("C", "B", "K", "evaluation"):
            addr = protocol.addresses(lineage, stage)
            used = set(range(addr["scene_start"], addr["scene_end"] + 1))
            used.update(range(addr["channel_start"], addr["channel_end"] + 1))
            if stage == "evaluation":
                used.update(range(addr["motion_start"], addr["motion_end"] + 1))
                assert len(used) == 96
            else:
                used.update((addr["motion"], addr["construction"]))
                assert len(used) == 1026
            assert not all_used & used
            all_used.update(used)
        assert protocol.addresses(lineage, "K") == protocol.addresses(lineage, "D")


@pytest.mark.parametrize("stage", ["C", "B"])
def test_parent_storage_matches_original_geometry_collector(stage):
    actor, critic = model.build_c(29811)
    rows, counts = [], defaultdict(int)
    metadata = dict(phase="train", arm=stage, lineage=1, master=29811, episode=0, motion_seed=55)
    actual = collection.collect_parent(NativeInfoFixture(0, 32), actor, critic, stage, 32,
                                       1000, 6000, generator(55), metadata, counts, rows.append)
    original = collect_original_geometry(NativeInfoFixture(0, 32), actor, critic, 32,
                                          1000, 6000, generator(55), None, metadata,
                                          defaultdict(int), lambda row: None, lambda: None)
    assert actual.keys() == original.keys()
    for key in actual:
        assert torch.equal(actual[key], original[key]), key
    assert counts["native_step_calls"] == counts["team_steps"] == 32
    assert rows[0]["packet_bytes"] == 28
    reader.verify_innovations(rows[0], generator(55))
    assert torch.equal(actual["obs"][1:, :, 104:107], actual["u"][:-1].tanh())
    assert not actual["obs"][..., [126 + 10 * s for s in range(5)]].any()


def make_lineage(tmp_path):
    cells = {}
    for stage in protocol.STAGES:
        parent = None if stage == "C" else cells["C" if stage == "B" else "B"]["final_checkpoint"]
        cells[stage] = study.run_fit(1, stage, tmp_path / stage, SOURCE, parent,
                                     factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2)
        assert cells[stage]["status"] == "COMPLETE", cells[stage]["limits"]
    return cells


def test_fixed_driver_counts_checkpoint_and_training_reader(tmp_path):
    batch = study.run_batch(tmp_path / "run", SOURCE,
                            factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)
    assert batch["status"] == "COMPLETE", batch["limits"]
    assert batch["actual"]["fit_started"] == 12
    assert batch["actual"]["team_steps"] == 1152
    assert batch["actual"]["actual_adam_calls"] == 72
    assert batch["actual"]["joint_optimizer_steps"] == 24
    assert batch["actual"]["actor_optimizer_steps"] == batch["actual"]["critic_optimizer_steps"] == 24
    previous = {l: {} for l in protocol.LINEAGES}
    train_witness = {}
    for cell in batch["fits"]:
        l, stage = cell["lineage"], cell["stage"]
        previous[l][stage] = reader.read_fit_checkpoints(cell, previous[l])
        assert reader.read_updates(cell)["epoch_records"] == 4
        rows = reader.read_episodes(cell, "train")
        if stage in ("K", "D"):
            witness = [(r["initial_scene_sha256"], r["channel_sequence_sha256"], r["innovation_sha256"])
                       for r in rows]
            if stage == "K":
                train_witness[l] = witness
            else:
                assert witness == train_witness[l]
    for cell in batch["evaluations"]:
        assert len(reader.read_episodes(cell, "final_eval")) == 1
        assert cell["counts"]["actual_adam_calls"] == 0
        assert cell["initial_tensor_sha256"] == cell["after_eval_tensor_sha256"]
    with pytest.raises(FileExistsError):
        study.run_batch(tmp_path / "run", SOURCE)


def test_full_horizon_evaluation_writer_reader_all_programs(tmp_path):
    cells = make_lineage(tmp_path / "fits")
    bindings = {"I": cells["C"]["initial_checkpoint"], "P": cells["B"]["final_checkpoint"],
                "K": cells["K"]["final_checkpoint"], "D": cells["D"]["final_checkpoint"]}
    witness = None
    for program, binding in bindings.items():
        cell = study.run_evaluation(1, program, binding, tmp_path / "eval" / program, SOURCE,
                                    factory=lambda seed: NativeInfoFixture(seed, 256), evaluation=1)
        assert cell["status"] == "COMPLETE", cell["limits"]
        rows = reader.read_episodes(cell, "final_eval")
        stage = "C" if program == "I" else "B" if program == "P" else program
        arrays = reader.read_bound_checkpoint(binding, lineage=1, stage=stage,
                                               endpoint="initial" if program == "I" else "final",
                                               launch_sha=SOURCE)
        log_std = arrays["actor"]["log_std" if program in ("I", "P") else "base.log_std"]
        result = reader.read_trace(rows[0], program, arrays["actor"]["b"].tolist() if program == "K" else None, log_std)
        assert result["levels"]["J_net"] == pytest.approx(.267)
        assert result["levels"]["service_p05"] == 7
        assert result["zero_service_times"] == []
        assert len(result["correction_relative_sigma_rms"]) == 3
        current = tuple(result[k] for k in ("initial_scene_sha256", "channel_sha256", "innovation_sha256"))
        if witness is None:
            witness = current
        else:
            assert current == witness


def test_partial_failure_preserves_started_fit_and_does_not_replace_root(tmp_path):
    class BrokenFixture(NativeInfoFixture):
        def step(self, actions):
            raise RuntimeError("deliberate synthetic native-shaped failure")
    batch = study.run_batch(tmp_path / "failed", SOURCE,
                            factory=lambda seed: BrokenFixture(seed, 32), horizon=32, train=2, evaluation=1)
    assert batch["status"] == "INCOMPLETE"
    assert len(batch["fits"]) == 1 and batch["fits"][0]["stage"] == "C"
    assert batch["actual"]["fit_started"] == 1
    assert batch["actual"]["native_step_calls"] == 1
    assert batch["actual"]["team_steps"] == 0
    assert not batch["evaluations"]
    assert (tmp_path / "failed/1/C/initial.pt").is_file()


def test_nonfinite_learner_preserves_failed_fit_counts_and_original_error(tmp_path, monkeypatch):
    def damaged_update(actor, critic, optimizer, episodes, counts, check, emit):
        counts["optimizer_steps"] += 1
        counts["joint_optimizer_steps"] += 1
        counts["actual_adam_calls"] += 1
        with torch.no_grad():
            actor.mean.bias[0] = float("nan")
        raise FloatingPointError("injected nonfinite Adam parameters")
    monkeypatch.setattr(study, "update_parent", damaged_update)
    out = tmp_path / "damaged"
    batch = study.run_batch(out, SOURCE, factory=lambda seed: NativeInfoFixture(seed, 32),
                            horizon=32, train=2, evaluation=1)
    assert batch["status"] == "INCOMPLETE" and len(batch["fits"]) == 1
    assert batch["actual"]["fit_started"] == 1
    assert batch["actual"]["team_steps"] == 64
    assert batch["actual"]["actual_adam_calls"] == 1
    cell = batch["fits"][0]
    assert cell["limits"] == ["FloatingPointError: injected nonfinite Adam parameters"]
    assert cell["exposure"]["actor"]["displacement"] is None
    assert "actor.displacement" in cell["exposure_unavailable"]["fields"]
    assert json.loads((out / "1/C/summary.json").read_text()) == cell
    assert json.loads((out / "summary.json").read_text())["actual"] == batch["actual"]
    assert not (out / "1/B").exists()


def test_outer_contrast_uses_three_programs_and_metric_direction():
    panels = {l: {p: [dict(J_net=float(e + (l if p == "D" else 0)),
                           zero_service_steps=float(e - (l if p == "D" else 0)),
                           mean_height_m=float(e + (l if p == "D" else 0))) for e in range(32)]
                  for p in protocol.PROGRAMS} for l in protocol.LINEAGES}
    result = reader.contrast(panels, "D", "K", "J_net")
    assert result["per_lineage_mean"] == [1., 2., 3.]
    assert result["outer_program"]["df"] == 2
    assert "deployment_average_over_blocks" not in result
    assert reader.contrast(panels, "D", "K", "zero_service_steps")["adverse_worlds"] == {"1": [], "2": [], "3": []}
    assert reader.contrast(panels, "D", "K", "mean_height_m")["adverse_worlds"] is None


def test_cli_requires_admission_before_scientific_import_or_output(monkeypatch, tmp_path):
    from experiments.candidates.uav_parent_adaptation.b01 import run
    import scripts.hmasd_admission
    def refuse(*args, **kwargs):
        raise RuntimeError("deliberate admission refusal")
    monkeypatch.setattr(scripts.hmasd_admission, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="deliberate admission refusal"):
        run.main(["--out", str(tmp_path / "never"), "--launch-sha", SOURCE, "--seed", "29811"])
    assert not (tmp_path / "never").exists()
