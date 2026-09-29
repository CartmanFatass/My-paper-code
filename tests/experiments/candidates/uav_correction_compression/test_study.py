import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.uav_correction_compression import study, run_b01
from tests.experiments.candidates.uav_correction_compression.test_model import bound_inputs


class NativeInfoFixture(SyntheticAdapter):
    def step(self, actions):
        raw, reward, terminated, truncated, info = super().step(actions)
        connections = np.zeros((5, 50), dtype=bool)
        connections[0, :7] = True
        sinr = np.full((5, 50), 20., dtype=np.float64)
        physical = .014 * 7 + .3 * ((20 - 3) / 30)
        info["rewards_dict"] = {a: physical / 5 for a in AGENTS}
        for agent in AGENTS:
            info["infos_dict"][agent]["global"].update(connections=connections, sinr_matrix=sinr)
        return raw, reward, terminated, truncated, info


def test_complete_224_row_driver_with_actual_history_innovations_and_timing(bound_inputs, tmp_path):
    _, inputs, _, parent, endpoint_dir = bound_inputs
    constructed = []
    def factory(seed):
        env = NativeInfoFixture(seed, 256)
        constructed.append(env)
        return env
    out = tmp_path / "run"
    out.mkdir()
    (out / "launch-manifest.json").write_text("{}")
    (out / "admission-preflight.json").write_text("{}")
    batch = study.run_batch(out, "synthetic-sha", parent, endpoint_dir, factory=factory)
    assert batch["status"] == "COMPLETE", batch["limits"]
    assert len(constructed) == 7 and len({id(env) for env in constructed}) == 7
    assert batch["actual"]["team_steps"] == 57344
    assert batch["actual"]["motion_samples"] == 286720
    assert batch["actual"]["constructors"] == 7
    assert all(batch["actual"][k] == 0 for k in
               ("fit_started", "optimizer_steps", "evaluation_optimizer_steps", "train_team_steps",
                "diagnostic_forward_calls", "behavior_critic_forward_calls"))
    witnesses = {}
    actions = {}
    for cell in batch["cells"]:
        arm = cell["arm"]
        assert cell["status"] == "COMPLETE" and cell["frozen_equal"]
        assert cell["actor_trainable_parameters"] == cell["parameter_displacement"] == 0
        assert cell["initial_tensor_sha256"] == cell["final_tensor_sha256"]
        assert len(cell["rows"]) == 32 and cell["timing"]["actor_forward"]["calls"] == 8192
        rows = [json.loads(line) for line in (out / arm / "episodes.jsonl").read_text().splitlines()]
        assert rows == cell["rows"]
        assert study.sha256(out / arm / "episodes.jsonl") == cell["episode_stream_sha256"]
        assert cell["raw_bytes"] == sum(row["raw_bytes"] for row in rows)
        for row in rows:
            assert row["arm"] == arm and row["world"] == row["episode"]
            assert row["innovation_vectors"] == 1280
            assert row["timing"]["actor_forward"]["calls"] == 256
            assert row["timing"]["episode_loop"]["wall_ns"] >= row["timing"]["actor_forward"]["wall_ns"] > 0
            assert row["timing"]["episode_loop"]["process_cpu_ns"] >= row["timing"]["actor_forward"]["process_cpu_ns"] > 0
            assert study.sha256(out / row["raw"]) == row["raw_sha256"]
            witness = tuple(row[k] for k in ("innovation_sha256", "motion_rng_start_sha256",
                "motion_rng_end_sha256", "channel_sequence_sha256", "initial_scene_sha256"))
            assert witnesses.setdefault(row["world"], witness) == witness
            if row["world"] == 0:
                with np.load(out / row["raw"]) as data:
                    np.testing.assert_array_equal(data["actor_input"][1:, :, 104:107], data["action"][:-1])
                    assert not np.any(data["packet"][:, 7:])
                    assert not np.any(data["actor_input"][..., 171:])
                    assert not np.any(data["critic_input"][..., 451:])
                    # Independent Gaussian/Jacobian expression checks the unchanged density.
                    mean = torch.tensor(data["composed_mean"], dtype=torch.float64)
                    u = torch.tensor(data["pre_tanh_motion"], dtype=torch.float64)
                    log_std = torch.tensor(data["log_std"], dtype=torch.float64).clamp(-5, 2)
                    density = torch.distributions.Normal(mean, log_std.exp()).log_prob(u)
                    jacobian = 2 * (np.log(2) - u - torch.nn.functional.softplus(-2 * u))
                    np.testing.assert_allclose(data["sample_logp"], (density - jacobian).sum(-1).numpy(),
                                               atol=1e-5, rtol=1e-5)
                    if arm.startswith("C"):
                        np.testing.assert_array_equal(data["correction"], np.broadcast_to(
                            np.array(cell["constant_float32"], dtype=np.float32), (256, 5, 3)))
                    elif arm == "B40":
                        assert not np.any(data["correction"])
                    actions[arm] = data["action"].copy()
    assert not np.array_equal(actions["D19701"], actions["C19701"])
    assert all(entry["arms"] == list(study.rotating_order(w)) for w, entry in enumerate(batch["arm_order"]))
    assert batch["resources"]["process_cpu_seconds_during_batch"] > 0
    assert batch["timing"]["json_output"]["calls"] > 0
    assert json.loads((out / "summary.json").read_text()) == batch
    with pytest.raises(FileExistsError, match="retry"):
        study.run_batch(out, "synthetic-sha", parent, endpoint_dir, factory=factory)
    assert len(constructed) == 7


def test_partial_failure_is_retained_without_retry(bound_inputs, tmp_path):
    _, _, _, parent, endpoints = bound_inputs
    class Broken(NativeInfoFixture):
        def step(self, actions):
            if self.t == 2:
                raise RuntimeError("synthetic failure")
            return super().step(actions)
    out = tmp_path / "failure"
    batch = study.run_batch(out, "sha", parent, endpoints, factory=lambda seed: Broken(seed, 256))
    assert batch["status"] == "INCOMPLETE"
    assert any("synthetic failure" in value for value in batch["limits"])
    assert batch["actual"]["constructors"] == 7
    assert batch["actual"]["native_step_calls"] == 3 and batch["actual"]["team_steps"] == 2
    assert batch["actual"]["fit_started"] == batch["actual"]["optimizer_steps"] == 0
    assert batch["frozen_equal"] and all(not cell["rows"] for cell in batch["cells"])
    assert batch["failed_cell"] == dict(arm="D19701", world=0)
    assert batch["arm_order"] == [dict(world=0, arms=["D19701"])]
    assert (out / "summary.json").exists()


def test_fixed_source_and_cli_are_bound_and_admitted(tmp_path, monkeypatch):
    # Inputs are tested against source bytes independently of synthetic model fixture.
    assert study.load_inputs()["horizon"] == 256
    monkeypatch.setattr(study, "INPUTS_PATH", tmp_path / "bad.json")
    study.INPUTS_PATH.write_text("{}")
    with pytest.raises(ValueError, match="digest"):
        study.load_inputs()
    args = ["--out", str(tmp_path / "output"), "--launch-sha", "a" * 40, "--seed", "19801",
            "--parent-checkpoint", str(tmp_path / "parent.pt"), "--endpoint-dir", str(tmp_path)]
    from scripts import hmasd_admission
    called = []
    def refused(*a, **kw):
        called.append(kw["direction"])
        raise RuntimeError("synthetic admission refusal")
    monkeypatch.setattr(hmasd_admission, "require_admission", refused)
    with pytest.raises(RuntimeError, match="admission refusal"):
        run_b01.main(args)
    assert called == ["uav_correction_compression"] and not (tmp_path / "output").exists()
    args[5] = "19802"
    with pytest.raises(SystemExit):
        run_b01.main(args)
