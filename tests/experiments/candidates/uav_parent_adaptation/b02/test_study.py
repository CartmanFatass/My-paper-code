from collections import defaultdict
import copy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_parent_adaptation.b01 import (
    collection as old_collection, model as old_model, protocol as old_protocol, study as old_study,
)
from experiments.candidates.uav_parent_adaptation.b02 import assets, collection, model, protocol, study
from experiments.candidates.uav_parent_adaptation import read_b02 as reader

SOURCE = "b" * 40


class NativeInfoFixture(SyntheticAdapter):
    """Synthetic dynamics with native-shaped telemetry; never scientific UAV exposure."""
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


@pytest.fixture(scope="module")
def retained(tmp_path_factory):
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("b02-retained") / "old"
    batch = old_study.run_batch(root, protocol.PARENT_SOURCE,
        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)
    assert batch["status"] == "COMPLETE", batch["limits"]
    sha = assets.digest(root / "summary.json")
    loaded = assets.load_assets(root, summary_sha256=sha, train=2, horizon=32)
    return root, sha, loaded


def test_train_reuses_kd_addresses_and_fresh_panels_are_disjoint():
    old_used = set()
    for lineage in protocol.LINEAGES:
        for stage in ("C", "B", "K", "evaluation"):
            addr = old_protocol.addresses(lineage, stage)
            for key in ("scene", "channel"):
                old_used.update(range(addr[key + "_start"], addr[key + "_end"] + 1))
            if stage == "evaluation":
                old_used.update(range(addr["motion_start"], addr["motion_end"] + 1))
            else:
                old_used.update((addr["motion"], addr["construction"]))
        assert protocol.addresses(lineage, "U") == old_protocol.addresses(lineage, "K")
        assert protocol.addresses(lineage, "U") == old_protocol.addresses(lineage, "D")
    for lineage in protocol.LINEAGES:
        addr = protocol.addresses(lineage, "evaluation")
        used = set()
        for key in ("scene", "channel", "motion"):
            used.update(range(addr[key + "_start"], addr[key + "_end"] + 1))
        assert len(used) == 96 and not used & old_used
        old_used.update(used)


def test_u_storage_matches_original_joint_geometry_and_sends_40_bytes(monkeypatch):
    actor, critic = old_model.build_c(29811)
    with torch.no_grad():
        actor.log_std.copy_(torch.tensor([-.1, -1.7, .3]))
    packets = []
    original_channel = collection.ForecastChannel
    class CaptureChannel(original_channel):
        def resolve_payload(self, sender, packet):
            packets.append(packet.copy())
            return super().resolve_payload(sender, packet)
    monkeypatch.setattr(collection, "ForecastChannel", CaptureChannel)
    metadata = dict(phase="train", arm="U", lineage=1, master=29813, episode=0, motion_seed=55)
    rows, original_rows, counts = [], [], defaultdict(int)
    actual = collection.collect_training(NativeInfoFixture(0, 32), actor, critic, 32, 1000, 6000,
        generator(55), metadata, counts, rows.append)
    original = old_collection.collect_parent(NativeInfoFixture(0, 32), actor, critic, "B", 32,
        1000, 6000, generator(55), dict(metadata, arm="B"), defaultdict(int), original_rows.append)
    assert actual.keys() == original.keys()
    for key in actual:
        assert torch.equal(actual[key], original[key]), key
    assert len(packets) == 32 and all(p.shape == (10,) and not p[7:].any() for p in packets)
    assert tuple(rows[0][k] for k in protocol.WITNESS_FIELDS) == tuple(original_rows[0][k] for k in protocol.WITNESS_FIELDS)
    assert torch.equal(actual["obs"][1:, :, 104:107], actual["u"][:-1].tanh())
    assert rows[0]["packet_bytes"] == 40 and rows[0]["log_std"] == actor.log_std.tolist()
    assert counts["team_steps"] == counts["native_step_calls"] == 32


def test_three_fit_driver_interleaving_counts_and_pure_fit_reader(tmp_path, retained):
    parent_root, sha, bound = retained
    out = tmp_path / "new"
    batch = study.run_batch(out, SOURCE, parent_root=parent_root, parent_summary_sha256=sha,
        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=4)
    assert batch["status"] == "COMPLETE", batch["limits"]
    assert batch["actual"]["fit_started"] == 3 and batch["actual"]["constructors"] == 15
    assert batch["actual"]["team_steps"] == 3 * (2 + 4 * 4) * 32
    assert batch["actual"]["actual_adam_calls"] == batch["actual"]["joint_optimizer_steps"] == 12
    assert batch["actual"]["actor_optimizer_steps"] == batch["actual"]["critic_optimizer_steps"] == 0
    for cell in batch["fits"]:
        lineage = cell["lineage"]
        checked = reader.read_fit(cell, bound["checkpoints"][lineage]["P"], bound["witnesses"][lineage])
        assert checked["reading"]["initial_exact_parent"]
        assert checked["reading"]["matched_training_episodes"] == 2
        assert cell["final_sigma"] != cell["initial_sigma"]
    assert batch["evaluation_order"] == [dict(lineage=l, world=e, rank=r, program=p)
        for l in protocol.LINEAGES for e in range(4) for r, p in enumerate(protocol.rotating_order(e))]
    for cell in batch["evaluations"]:
        rows = reader.read_episodes(cell, "final_eval")
        assert len(rows) == 4 and cell["counts"]["actual_adam_calls"] == 0
        assert cell["initial_tensor_sha256"] == cell["after_eval_tensor_sha256"]
        assert cell["timing"]["actor_forward"]["calls"] == 128
    with pytest.raises(FileExistsError):
        study.run_batch(out, SOURCE)


def test_full_horizon_all_programs_and_variable_u_sigma_reader(tmp_path, retained):
    _, _, bound = retained
    checkpoints = dict(bound["checkpoints"][1])
    fit = study.run_fit(1, tmp_path / "fit", SOURCE, checkpoints["P"], bound["witnesses"][1],
        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2)
    assert fit["status"] == "COMPLETE", fit["limits"]
    checkpoints["U"] = fit["final_checkpoint"]
    cells = study.run_evaluation_panel(1, checkpoints, tmp_path / "eval", SOURCE,
        factory=lambda seed: NativeInfoFixture(seed, 256), evaluation=1)
    witness = None
    for cell in cells:
        assert cell["status"] == "COMPLETE", cell["limits"]
        program = cell["program"]
        row = reader.read_episodes(cell, "final_eval")[0]
        if program == "U":
            arrays = reader.read_u_checkpoint(checkpoints[program], lineage=1, endpoint="final", launch_sha=SOURCE)
        else:
            arrays = reader.old.read_bound_checkpoint(checkpoints[program], lineage=1,
                stage="B" if program == "P" else program, endpoint="final", launch_sha=protocol.PARENT_SOURCE)
        log_std = arrays["actor"]["log_std" if program in ("P", "U") else "base.log_std"]
        checked = reader.read_trace(row, program, arrays["actor"]["b"].tolist() if program == "K" else None, log_std)
        assert checked["levels"]["J_net"] == pytest.approx(.267)
        assert checked["levels"]["service_p05"] == 7
        current = tuple(checked[k] for k in ("initial_scene_sha256", "channel_sha256", "innovation_sha256"))
        if witness is None:
            witness = current
        else:
            assert witness == current
        if program == "U":
            assert "not a parent shadow" in checked["mean_field_semantics"]
            assert fit["final_log_std"] != fit["initial_log_std"]
            with pytest.raises(AssertionError):
                reader.read_trace(row, "U", expected_log_std=np.asarray(fit["initial_log_std"]))


def test_conditional_deployment_variance_separates_lineage_spread():
    panels = {l: {"U": [{"J_net": float(l + x)} for x in range(32)],
                  "D": [{"J_net": 0.} for _ in range(32)]} for l in (1, 2, 3)}
    value = reader.contrast(panels, "U", "D", "J_net")
    expected = 3 * np.var(np.arange(32), ddof=1) / (9 * 32)
    assert value["conditional_deployment"]["variance"] == pytest.approx(expected)
    assert value["per_lineage_mean"] == [16.5, 17.5, 18.5]
    assert value["descriptive_lineage_interval"]["sample_sd"] == 1
    assert value["conditional_deployment"]["standard_error"] != pytest.approx(1 / np.sqrt(3))


def test_sigma_reading_respects_fp32_exponential_and_rejects_corruption():
    log_std = torch.tensor([.002362105762, -6., 3.], dtype=torch.float32)
    sigma = log_std.clamp(-5, 2).exp().numpy()
    reader.check_sigma(log_std.numpy(), sigma.tolist())
    bad = sigma.copy()
    bad[0] = np.nextafter(bad[0], np.float32(10))
    with pytest.raises(AssertionError):
        reader.check_sigma(log_std.numpy(), bad)


def test_stream_mismatch_preserves_actual_exposure_and_stops(tmp_path, retained):
    _, _, bound = retained
    bad = copy.deepcopy(bound["witnesses"][1])
    bad[0] = ("0" * 64, *bad[0][1:])
    cell = study.run_fit(1, tmp_path / "bad", SOURCE, bound["checkpoints"][1]["P"], bad,
        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2)
    assert cell["status"] == "INCOMPLETE" and "actual exogenous" in cell["limits"][0]
    assert cell["counts"]["fit_started"] == 1 and cell["counts"]["team_steps"] == 32
    assert cell["counts"]["actual_adam_calls"] == 0 and cell["matched_training_episodes"] == 0
    assert len((tmp_path / "bad/episodes.jsonl").read_text().splitlines()) == 1


def test_nonfinite_update_keeps_original_error_and_actual_count(tmp_path, retained, monkeypatch):
    _, _, bound = retained
    def damage(actor, critic, opt, episodes, counts, check, emit):
        counts["optimizer_steps"] += 1
        counts["actual_adam_calls"] += 1
        counts["joint_optimizer_steps"] += 1
        with torch.no_grad():
            actor.log_std[0] = float("nan")
        raise FloatingPointError("injected Adam damage")
    monkeypatch.setattr(study, "update_parent", damage)
    cell = study.run_fit(1, tmp_path / "damaged", SOURCE, bound["checkpoints"][1]["P"], bound["witnesses"][1],
        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2)
    assert cell["status"] == "INCOMPLETE" and cell["limits"] == ["FloatingPointError: injected Adam damage"]
    assert cell["counts"]["team_steps"] == 64 and cell["counts"]["actual_adam_calls"] == 1
    assert "exposure_unavailable" in cell
    assert json.loads((tmp_path / "damaged/summary.json").read_text())["limits"] == cell["limits"]


def test_bad_bound_summary_starts_no_fit(tmp_path, retained):
    parent_root, _, _ = retained
    batch = study.run_batch(tmp_path / "wrong", SOURCE, parent_root=parent_root,
        parent_summary_sha256="0" * 64, factory=lambda seed: NativeInfoFixture(seed, 32),
        horizon=32, train=2, evaluation=1)
    assert batch["status"] == "INCOMPLETE" and "summary digest mismatch" in batch["limits"][0]
    assert batch["actual"]["fit_started"] == batch["actual"]["native_step_calls"] == 0
    assert not batch["fits"] and not batch["evaluations"]
