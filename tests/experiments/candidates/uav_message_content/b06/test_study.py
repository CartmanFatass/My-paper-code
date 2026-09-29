from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_message_content.b05 import model as base_model
from experiments.candidates.uav_message_content.b06 import model, study
from experiments.candidates.uav_message_content.b06.collector import collect_episode
from experiments.candidates.uav_message_content import read_b06 as reader


class NativeInfoFixture(SyntheticAdapter):
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


@pytest.fixture
def checkpoint(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(887)
        actor, critic = BaseActor(), BaseCritic()
    content = io.BytesIO()
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm="B", master=19451,
                    input_size=171, critic_size=451, inherited_sha256=model.SOURCE_INHERITED_SHA256), content)
    value = content.getvalue()
    digest = hashlib.sha256(value).hexdigest()
    monkeypatch.setattr(base_model, "SOURCE_SHA256", digest)
    monkeypatch.setattr(study, "SOURCE_SHA256", digest)
    monkeypatch.setattr(reader, "BOUND_SHA", digest)
    path = tmp_path / "parent.pt"
    path.write_bytes(value)
    return path, digest


@pytest.mark.parametrize("arm", ["K", "D", "B40"])
def test_complete_geometry_composition_innovation_writer_reader(checkpoint, arm, tmp_path):
    path, digest = checkpoint
    if arm == "B40":
        actor, critic = model.load_base(path.read_bytes(), digest)
    else:
        actor, critic = model.build_arm(19701, arm)
        model.load_warm_start(actor, critic, path.read_bytes(), digest)
        with torch.no_grad():
            if arm == "K":
                actor.b.copy_(torch.tensor([.8, -.4, .2]))
            else:
                actor.residual_output.bias.copy_(torch.tensor([.8, -.4, .2]))
    counts, rows = defaultdict(int), []
    collect_episode(NativeInfoFixture(0, 256), actor, critic, arm, 256, 1970002000, 1970007000,
                    generator(1970003000), dict(phase="final_eval", arm=arm,
                    master=19451 if arm == "B40" else 19701, episode=0, motion_seed=1970003000),
                    counts, rows.append, raw_path=tmp_path / f"{arm}.npz")
    result = reader.read_trace(rows[0], arm, actor.b.tolist() if arm == "K" else None)
    assert result["levels"]["J_net"] == pytest.approx(.267)
    assert rows[0]["innovation_vectors"] == 1280
    assert result["density_max_abs_error"] < 1e-5
    assert counts["diagnostic_forward_calls"] == 0
    assert result["levels"]["zero_service_steps"] == result["levels"]["longest_zero_service"] == 0
    if arm == "K":
        assert max(result["correction_std"]) == 0
    with np.load(rows[0]["raw"]) as data:
        np.testing.assert_array_equal(data["actor_input"][1:, :, 104:107], data["action"][:-1])
        assert not np.any(data["packet"][:, 7:])


def test_small_driver_counts_pairing_and_checkpoint_reading(checkpoint, tmp_path):
    path, digest = checkpoint
    batch = study.run_batch(tmp_path / "run", "synthetic-source", path, digest,
                            factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)
    assert batch["status"] == "COMPLETE", batch["limits"]
    assert batch["actual"]["team_steps"] == 608
    assert batch["actual"]["fit_started"] == 6
    assert batch["actual"]["actor_optimizer_steps"] == batch["actual"]["critic_optimizer_steps"] == 24
    _, parent = reader.checkpoint_arrays(path)
    bindings = {}
    for cell in batch["cells"]:
        check = reader.read_checkpoints(cell, parent)
        assert check["group_sizes"]["calibration" if cell["arm"] == "K" else "residual_output"] > 0
        assert reader.read_updates(cell)["ppo_records"] == 4
        records = [json.loads(line) for line in (Path(cell["directory"]) / "episodes.jsonl").read_text().splitlines()]
        rng = generator(100000 * cell["master"] + 21)
        for row in records[:2]:
            reader.verify_innovations(row, rng)
        witness = [(r["initial_scene_sha256"], r["channel_sequence_sha256"], r["innovation_sha256"])
                   for r in records]
        if cell["master"] in bindings:
            assert bindings[cell["master"]] == witness
        else:
            bindings[cell["master"]] = witness
    batch["cells"][1]["initial_tensor_sha256"]["critic_old"] = "mismatch"
    assert not study.validate_cells(batch["cells"], batch["b40"], horizon=32, train=2, evaluation=1)["complete"]


def test_conditional_units_and_resource_stop(checkpoint, tmp_path, monkeypatch):
    first = {m: [dict(J_net=float(e + b)) for e in range(32)] for b, m in enumerate(study.MASTERS)}
    second = {m: [dict(J_net=float(e)) for e in range(32)] for m in study.MASTERS}
    result = reader.contrast(first, second, "J_net")
    assert result["per_continuation_mean"] == [0., 1., 2.]
    assert result["conditional_training"]["df"] == 2
    assert result["deployment_average_over_blocks"]["df"] == 31
    monkeypatch.setattr(study, "CPU_LIMIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match="ceiling"):
        study.run_batch(tmp_path / "stopped", "synthetic-source", *checkpoint,
                        factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)


@pytest.mark.parametrize("metric", ["zero_service_steps", "longest_zero_service"])
def test_fewer_zero_service_ticks_or_shorter_gaps_are_improvements(metric):
    first = {m: [{metric: 0} for _ in range(32)] for m in study.MASTERS}
    second = {m: [{metric: 4} for _ in range(32)] for m in study.MASTERS}
    better = reader.contrast(first, second, metric)
    worse = reader.contrast(second, first, metric)
    assert better["mean"] == -4 and better["utility_direction"] == "lower"
    assert all(worlds == [] for worlds in better["adverse_worlds"].values())
    assert all(worlds == list(range(32)) for worlds in worse["adverse_worlds"].values())


def test_behavior_descriptors_have_no_invented_utility_direction():
    first = {m: [dict(mean_height_m=50) for _ in range(32)] for m in study.MASTERS}
    second = {m: [dict(mean_height_m=60) for _ in range(32)] for m in study.MASTERS}
    result = reader.contrast(first, second, "mean_height_m")
    assert result["utility_direction"] == "descriptive_only" and result["adverse_worlds"] is None
    assert all(worlds == list(range(32)) for worlds in result["negative_worlds"].values())
