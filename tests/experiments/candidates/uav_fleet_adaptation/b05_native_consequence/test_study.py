"""Synthetic complete B05 contract checks, with no production asset or native rollout."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import checkpoint, make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.policies import indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b04_native_development.policies import LocalPolicy as OriginalPolicy
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence import read, run
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.assets import load_initial_assets
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.contract import FROZEN, HEADS, evaluation_arms, new_counts
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.policies import LocalPolicy, frozen_forward
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.reading import validate_counts
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.study import ROOT, run_batch


SMALL = replace(FROZEN, acquisition_worlds=(tuple(range(101, 113)), tuple(range(121, 133))),
                evaluation_worlds=((201, 202), (221, 222)), horizon=8, updates=2,
                actor_constructor_seeds=(301, 302), acquisition_roots=(311, 312), evaluation_roots=(321, 322),
                intervention_a_roots=(331, 332), intervention_b_roots=(341, 342),
                address_roots=(351, 352), minibatch_roots=(361, 362))


class Synthetic:
    """Deterministic array fixture, not the production UAV simulator."""
    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 60.], [900., 900., 140.], (5, 3))
        self.users = rng.uniform(0., 1000., (50, 2))
        self.tick = 0
        self.transmitter_mask[:] = True
        return self.obs(), self.info()

    def obs(self):
        result = np.zeros((5, 104), dtype=np.float32)
        for i in range(5):
            own = self.positions[i]
            result[i, :3] = own / [1000., 1000., 100.] - [0., 0., .5]
            result[i, 3:5] = (self.users[i] - own[:2]) / 1000.
            result[i, 5] = .4
            for j, peer in enumerate(np.delete(self.positions, i, axis=0)):
                result[i, 63 + j * 4:66 + j * 4] = (peer - own) / [1000., 1000., 100.]
                result[i, 66 + j * 4] = 1.
            result[i, -1] = self.tick / 8.
        return result

    def info(self):
        sinr = np.full((5, 50), -5., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for i in range(5):
            sinr[i, i] = 4. + self.positions[i, 0] / 1000.
            connections[i, i] = True
        quality = float(np.clip((sinr[connections] - 3.) / 30., 0., 1.).mean())
        reward = .7 * 5 / 50. + .3 * quality
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=5)}},
                    rewards_dict={f"uav_{i}": reward / 5. for i in range(5)})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30.,
                                 [0., 0., 50.], [1000., 1000., 150.])
        self.tick += 1
        return self.obs(), 0., False, self.tick == 8, self.info()


def bindings(root):
    root = Path(root)
    root.mkdir()
    result = []
    for lineage in range(2):
        model = make_student(1701 + lineage).eval()
        saved = checkpoint(model)
        saved.update(endpoint="S", launch_sha="synthetic", optimizer_steps=8000)
        path = root / f"S{lineage}.pt"
        torch.save(saved, path)
        result.append(dict(file_identity(path), state_sha256=state_digest(model.state_dict()), launch_sha="synthetic"))
    return result


@pytest.fixture(scope="module")
def package(tmp_path_factory):
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("fleet_b05")
    inherited = bindings(root / "inputs")
    out = root / "result"
    batch = run_batch(out, "synthetic", protocol=SMALL, factory=Synthetic, bindings=inherited)
    reading = read.read_result(out, ROOT, allow_fixture=True)
    yield out, batch, reading, inherited
    torch.set_num_threads(previous)


def test_fixed_prospective_counts_and_no_production_bypass(tmp_path):
    expected = FROZEN.expected()
    assert expected["head_fits"] == 4
    assert expected["acquisition_episodes"] == 4096 and expected["evaluation_episodes"] == 352
    assert expected["complete_episodes"] == 4448 and expected["native_steps"] == 1138688
    assert expected["head_optimizer_steps"] == 8192 and expected["head_training_rows"] == 1048576
    assert expected["student_requests"] == 1382400 and expected["ordinary_requests"] == 40960
    assert expected["reader_pair_backbone_rows"] == 2048 and expected["reader_final_backbone_rows"] == 71680
    assert expected["reader_backbone_rows"] == 73728 and expected["reader_head_rows"] == 40960
    assert expected["shadow_motion_ticks"] == 163840 and expected["intervention_draws"] == 4096
    assert expected["new_calibrations"] == expected["critic_rows"] == expected["expert_labels"] == 0
    with pytest.raises(ValueError, match="admitted"):
        run_batch(tmp_path / "production", "wrong")
    with pytest.raises(ValueError, match="nonproduction"):
        run_batch(tmp_path / "fixture", "wrong", factory=Synthetic, bindings=[])
    assert not (tmp_path / "production").exists() and not (tmp_path / "fixture").exists()
    with pytest.raises(ValueError, match="substitution"):
        load_initial_assets(SMALL)


def test_addresses_cover_uniform_target_with_original_seed_law():
    for lineage in range(2):
        addresses, weights = FROZEN.addresses(lineage)
        order = np.random.default_rng(FROZEN.address_roots[lineage]).permutation(320)
        assert np.array_equal(addresses, np.r_[np.tile(order, 3), order[:64]])
        assert set(np.bincount(addresses)) == {3, 4}
        np.testing.assert_allclose(np.bincount(addresses, weights=weights), np.full(320, 1024 / 320), atol=1e-15)
    with pytest.raises(ValueError, match="coverage"):
        replace(SMALL, acquisition_worlds=((1, 2), (3, 4))).validate()
    with pytest.raises(ValueError, match="overlap"):
        replace(SMALL, evaluation_worlds=((101,), (222,))).validate()


def test_frozen_forward_and_zero_head_preserve_original_one_row_policy():
    actor = make_student(44).eval()
    feature = np.linspace(-1., 1., 114, dtype=np.float32)
    hidden, logits = frozen_forward(actor, feature)
    with torch.inference_mode():
        original = actor(torch.from_numpy(feature).reshape(1, 114))[0].numpy()
    assert np.array_equal(logits, original) and hidden.shape == (128,)
    env = Synthetic(51)
    row = env.obs()[0]
    old = OriginalPolicy("S_T1", actor, world=51, agent=0, sampling_root=44)
    cal = LocalPolicy("CAL", actor, lineage=0, head=Head("CAL"), world=51, agent=0, sampling_root=44)
    plain = LocalPolicy("S", actor, lineage=0, world=51, agent=0, sampling_root=44)
    for tick in (0, 4, 8):
        a, b, c = (policy.query(row, tick, 0) for policy in (old, cal, plain))
        for key in ("features", "next_nav", "logits", "probabilities", "innovation", "action_index", "command"):
            np.testing.assert_array_equal(a[key], b[key])
            np.testing.assert_array_equal(a[key], c[key])
    assert cal.counters["neural_rows"] == cal.counters["head_rows"] == 1
    assert cal.counters["sampled_draws"] == 3
    assert plain.counters["head_rows"] == 0


def test_complete_synthetic_worker_and_reader(package):
    out, batch, reading, inherited = package
    assert batch["state"] == "COMPLETE" and batch["scientific_execution"] is False
    assert reading["status"] == "VERIFIED"
    validate_counts(batch, SMALL)
    expected = SMALL.expected()
    assert len(batch["rows"]) == expected["complete_episodes"] == 70
    assert batch["actual"]["native_steps"] == 560
    assert batch["actual"]["head_fits_completed"] == 4
    assert batch["actual"]["head_optimizer_steps"] == 8
    assert batch["actual"]["head_training_rows"] == 1024
    assert reading["reader_calls"]["backbone_rows"] == 164
    assert reading["reader_calls"]["head_rows"] == 80
    assert reading["reader_calls"]["shadow_motion_ticks"] == 320
    assert reading["reader_calls"]["optimizer"] == reading["reader_calls"]["native"] == 0
    assert {p.name for p in (out / "assets").iterdir()} == {"CAL0.pt", "CONT0.pt", "CAL1.pt", "CONT1.pt"}
    assert "Bstar" in evaluation_arms(0) and "Bstar" not in evaluation_arms(1)
    assert batch["comparisons"]["lineages"][1]["paired"]["Bstar-S"]["J"]["zero"] == 2
    assert all(file_identity(Path(r["path"]))["sha256"] == r["sha256"] for r in inherited)
    first_final = next(i for i, row in enumerate(batch["rows"]) if row["kind"] == "evaluation")
    assert first_final == 48
    for row in batch["rows"]:
        if row["kind"] == "acquisition":
            assert row["arm"] == "S" and row["policy_counts"]["head_rows"] == 0
        assert ("shadow" in row) == (row["arm"] in HEADS)
    with pytest.raises(FileExistsError, match="existing scientific"):
        run_batch(out, "synthetic", protocol=SMALL, factory=Synthetic, bindings=inherited)
    assert not (out / "reading.json").exists()


def test_pair_overrides_are_separate_from_original_innovations(package):
    out, batch, _, _ = package
    changed = 0
    for row in batch["rows"]:
        if row["kind"] != "acquisition":
            continue
        with np.load(out / row["raw"]["path"], allow_pickle=False) as raw:
            intervention = row["intervention"]
            di, i = intervention["tick"] // 4, intervention["agent"]
            expected = raw["nominal_action_index"].copy()
            expected[di, i] = raw["intervention_action"]
            np.testing.assert_array_equal(raw["action_index"], expected)
            assert raw["innovation"][di, i] == indexed_uniform(row["sampling_root"], row["world"], intervention["tick"], i)
            assert raw["intervention_uniform"] == indexed_uniform(intervention["root"], row["world"], intervention["tick"], i)
            changed += int(raw["intervention_action"] != raw["intervention_nominal_action"])
    assert changed > 0


def _copy_result(package, tmp_path):
    source = package[0]
    out = tmp_path / "result"
    shutil.copytree(source, out)
    return out, json.loads((out / "summary.json").read_text())


def test_reader_detects_native_motion_even_with_updated_raw_hash(package, tmp_path):
    out, batch = _copy_result(package, tmp_path)
    row = batch["rows"][0]
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as saved:
        raw = {key: saved[key] for key in saved.files}
    raw["commands"][1, 0, 0] += .5
    np.savez_compressed(path, **raw)
    row["raw"].update({k: file_identity(path)[k] for k in ("bytes", "sha256")})
    (out / "summary.json").write_text(json.dumps(batch))
    with pytest.raises(AssertionError, match="four-tick holds"):
        read.read_result(out, ROOT, allow_fixture=True)


def test_reader_detects_optimizer_counter_corruption_without_fit_replay(package, tmp_path):
    out, batch = _copy_result(package, tmp_path)
    record = batch["heads"][0]
    path = out / record["path"]
    saved = torch.load(path, map_location="cpu", weights_only=True)
    next(iter(saved["optimizer"]["state"].values()))["step"].add_(1)
    torch.save(saved, path)
    record.update({k: file_identity(path)[k] for k in ("bytes", "sha256")})
    (out / "summary.json").write_text(json.dumps(batch))
    with pytest.raises(AssertionError, match="Adam step count"):
        read.read_result(out, ROOT, allow_fixture=True)


def test_existing_reader_record_refuses_before_any_query(tmp_path, monkeypatch):
    (tmp_path / "reading.json").write_text("{}")
    def forbidden(*args, **kwargs):
        raise AssertionError("a second reader must not enter the body")
    monkeypatch.setattr(read, "_read_result", forbidden)
    with pytest.raises(FileExistsError):
        read.read_result(tmp_path, ROOT)


def test_asset_guard_precedes_constructor_and_failure_costs_are_zero(tmp_path):
    inherited = bindings(tmp_path / "inputs")
    inherited[1]["sha256"] = "wrong"
    calls = []
    def forbidden(seed):
        calls.append(seed)
        raise AssertionError("asset guard failed")
    out = tmp_path / "output"
    with pytest.raises(ValueError, match="asset file identity"):
        run_batch(out, "synthetic", protocol=SMALL, factory=forbidden, bindings=inherited)
    assert not calls
    batch = json.loads((out / "summary.json").read_text())
    assert not any(batch["actual"].values()) and batch["state"] == "INCOMPLETE"


def test_native_failure_retains_actual_partial_and_no_automatic_retry(tmp_path):
    inherited = bindings(tmp_path / "inputs")
    class Failure(Synthetic):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("synthetic interrupted native call")
            return super().step(commands)
    out = tmp_path / "output"
    with pytest.raises(RuntimeError, match="interrupted native"):
        run_batch(out, "synthetic", protocol=SMALL, factory=Failure, bindings=inherited)
    batch = json.loads((out / "summary.json").read_text())
    assert batch["actual"]["native_steps"] == 2 and batch["actual"]["native_step_calls"] == 3
    assert batch["actual"]["complete_episodes"] == 0
    assert (out / batch["partial_episode"]["partial_raw"]["path"]).is_file()
    assert batch["costs"]["incomplete"] and batch["costs"]["interrupted_call_work_may_be_unmeasured"]
    with pytest.raises(FileExistsError):
        run_batch(out, "synthetic", protocol=SMALL, factory=Failure, bindings=inherited)


def test_wrong_cli_seed_refuses_before_admission(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    monkeypatch.setattr(admission, "require_admission", lambda *a, **k: pytest.fail("wrong seed reached admission"))
    with pytest.raises(SystemExit):
        run.main(["--out", str(tmp_path), "--launch-sha", "not-a-run", "--seed", "1"])
