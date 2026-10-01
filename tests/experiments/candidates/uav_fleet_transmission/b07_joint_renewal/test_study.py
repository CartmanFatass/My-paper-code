"""Fabricated integrations only; zero native queries, training or retained actors."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal import read, study
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.collect import collect_episode
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.contract import FROZEN, HIGH, LOW, Protocol, write_json
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.reading import METRICS, comparisons

REPO = Path(__file__).resolve().parents[5]
PROTOCOL = Protocol(worlds=(113, 117), sampling_roots=(171, 173), phase_root=181,
                    bootstrap_seed=189, bootstrap_resamples=100, horizon=8)


class FabricatedEnvironment:
    """Synthetic geometry and eligibility slots; it never imports native radio."""
    steps = 0

    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def number(self):
        return (2, 3, 2, 1, 2, 1, 2, 1, 3)[self.tick]

    def observation(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        normalized = self.positions.copy()
        normalized[:, :2] /= 1000.
        normalized[:, 2] = (normalized[:, 2] - 50.) / 100.
        obs[:, :3] = normalized
        for agent in range(5):
            ids = np.arange(agent * 10, agent * 10 + self.number())
            slots = obs[agent, 3:63].reshape(20, 3)
            slots[:len(ids), :2] = (self.users[ids] - self.positions[agent, :2]) / 1000.
            slots[:len(ids), 2] = .44
        obs[:, -1] = self.tick / PROTOCOL.horizon
        return obs

    def info(self):
        sinr = np.full((5, 50), -20., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for agent in range(5):
            ids = np.arange(agent * 10, agent * 10 + self.number())
            sinr[agent, ids], connections[agent, ids] = 12., True
        served = int(connections.sum())
        reward = .7 * served / 50. + (.3 * .3 if served else 0.)
        self.sinr_matrix, self.connections = sinr.copy(), connections.copy()
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=served)}},
                    rewards_dict={f"uav_{agent}": reward / 5 for agent in range(5)})

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 70.], [900., 900., 130.], size=(5, 3))
        self.users = rng.uniform(0., 1000., size=(50, 2))
        self.tick = 0
        info = self.info()
        info["infos_dict"] = {f"uav_{agent}": {} for agent in range(5)}
        info.pop("rewards_dict")
        return self.observation(), info

    def step(self, commands):
        type(self).steps += 1
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30., LOW, HIGH)
        self.tick += 1
        return self.observation(), np.zeros(5), False, self.tick == PROTOCOL.horizon, self.info()


def execute_fixture(out, env_factory=FabricatedEnvironment):
    return study._execute(out, "synthetic", protocol=PROTOCOL, env_factory=env_factory, repo=REPO,
                          admission=None, scientific_invocation=False)


def test_full_worker_reader_and_consequential_tampering(tmp_path):
    out = tmp_path / "output"
    before = FabricatedEnvironment.steps
    summary = execute_fixture(out)
    assert FabricatedEnvironment.steps - before == 384
    before_read = FabricatedEnvironment.steps
    result = read.read_result(out, REPO, fixture=True)
    assert result["status"] == "VERIFIED" and not result["scientific_invocation"]
    assert FabricatedEnvironment.steps == before_read
    PROTOCOL.check_counts(result["counts"])
    assert result["replay_counts"]["ordinary_queries"] == 480
    assert result["replay_counts"]["indexed_draws"] == 320
    assert result["replay_counts"]["new_native_steps"] == 0
    assert result["replay_counts"]["actor_rows"] == result["replay_counts"]["analytic_helper_queries"] == 0
    assert result["matching"]["full_clock_draw_multisets_checked"] == 30
    assert len(result["paired"]["comparisons"]) == 5
    assert all(row["queries"] == 10 and row["renewals_after_initial"] == 5 for row in summary["episodes"])
    assert all(row["physical_hold_changes"] <= row["category_changes"] for row in summary["episodes"])
    assert json.loads((out / "progress.json").read_text())["state"] == "COMPLETE"
    with pytest.raises(FileExistsError):
        execute_fixture(out)
    row = next(row for row in summary["episodes"] if row["arm"] == "Q10" and row["schedule"] == "DISPERSED")
    with np.load(out / row["raw"]["path"], allow_pickle=False) as archive:
        raw = {key: archive[key] for key in archive.files}
    for key in ("innovation", "policy_scores", "commands", "features", "nav_pre", "nav_next", "probabilities",
                "decision_ticks", "decision_agents", "decision_phases", "hold_ticks", "next_deadline", "held_before",
                "phases", "phase_offsets", "connections", "sinr", "served", "reward"):
        changed = {name: value.copy() for name, value in raw.items()}
        if changed[key].dtype == bool:
            changed[key].flat[0] = not changed[key].flat[0]
        else:
            changed[key].flat[0] += 1
        # Changing an unused SINR element can be legitimate telemetry; alter an assigned one instead.
        if key == "sinr":
            changed[key] = raw[key].copy()
            changed[key][raw["connections"]] += 1.
        with pytest.raises(AssertionError, match="."):
            read.check_episode(changed, row, PROTOCOL)
    for key in ("query_mask", "memo_hit", "category_changed", "physical_hold_changed"):
        changed = {name: value.copy() for name, value in raw.items()}
        changed[key].flat[0] = not changed[key].flat[0]
        with pytest.raises(AssertionError):
            read.check_episode(changed, row, PROTOCOL)
    config = json.loads((out / "config.json").read_text())
    bad = deepcopy(config)
    bad["source_identities"][next(iter(bad["source_identities"]))] = "wrong"
    write_json(out / "config.json", bad)
    with pytest.raises(AssertionError, match="source identity"):
        read.read_result(out, REPO, fixture=True)
    write_json(out / "config.json", config)
    first = summary["episodes"][0]
    path = out / first["raw"]["path"]
    with np.load(path, allow_pickle=False) as archive:
        changed = {key: archive[key] for key in archive.files}
    changed["policy_scores"].flat[0] += 1.
    np.savez_compressed(path, **changed)
    identity = file_identity(path)
    first["raw"].update({key: identity[key] for key in ("bytes", "sha256")})
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="full original scores"):
        read.read_result(out, REPO, fixture=True)
    failed = json.loads((out / "reading.json").read_text())
    assert failed["status"] == "FAILED" and failed["actual_work"]["completed_episodes"] == 0
    assert failed["actual_work"]["inflight"]["ordinary_queries"] == 1
    assert failed["new_native_steps"] == 0


def test_q_and_tapes_average_inside_world_and_signed_interaction():
    rows = []
    for world_index, world in enumerate(PROTOCOL.worlds):
        for arm, schedule, q, tape in PROTOCOL.episode_order(world_index):
            # All q/tapes differ. C's phase effect is2, Q10's is1; interaction is−1.
            value = 10 * world_index + q + (0 if arm == "C" else 100 + tape)
            value += (2 if arm == "C" else 1) if schedule == "DISPERSED" else 0
            rows.append(dict(arm=arm, schedule=schedule, world=world, q=q, tape=tape,
                             **{metric: value for metric in METRICS}))
    result = comparisons(rows, PROTOCOL)
    assert result["levels"]["C/SYNC"]["J"]["values"] == [1.5, 11.5]
    assert result["levels"]["Q10/SYNC"]["J"]["values"] == [102., 112.]
    assert result["comparisons"]["C/DISPERSED-C/SYNC"]["J"]["values"] == [2., 2.]
    key = "(Q10/DISPERSED-Q10/SYNC)-(C/DISPERSED-C/SYNC)"
    assert result["comparisons"][key]["J"]["values"] == [-1., -1.]
    assert result["comparisons"][key]["J"]["n"] == 2
    assert result["comparisons"][key]["J"]["descriptive_paired_bootstrap95"] == [-1., -1.]
    for bad in (rows[:-1], rows + [rows[0]]):
        with pytest.raises(ValueError, match="missing, duplicated"):
            comparisons(bad, PROTOCOL)


@pytest.mark.parametrize("empty", [False, True])
def test_clipped_cache_hits_and_zero_user_navigation_at_private_queries(tmp_path, empty):
    class ConstantEnvironment(FabricatedEnvironment):
        def number(self):
            return 0 if empty else 2

        def reset(self, seed):
            self.positions = np.tile([100., 100., 50.] if empty else [0., 0., 50.], (5, 1))
            self.users = np.zeros((50, 2), dtype=np.float64)
            self.tick = 0
            info = self.info()
            info["infos_dict"] = {f"uav_{agent}": {} for agent in range(5)}
            info.pop("rewards_dict")
            return self.observation(), info

    out = tmp_path / "one_episode"
    (out / "raw").mkdir(parents=True)
    env = ConstantEnvironment(113)
    counts, inflight = {key: 0 for key in PROTOCOL.expected()}, {}
    row = collect_episode(env, arm="C", schedule="DISPERSED", world=113, q=3, tape=-1,
                          protocol=PROTOCOL, out=out, counts=counts, inflight=inflight)
    with np.load(out / row["raw"]["path"], allow_pickle=False) as archive:
        raw = {key: archive[key] for key in archive.files}
    check = read.check_episode(raw, row, PROTOCOL)
    assert check["ordinary_queries"] == 10 and check["source_counts"]["decisions"] == 10
    if empty:
        assert row["zero_service_steps"] == row["longest_zero_run"] == 8
        assert raw["fallback"].all()
        assert np.all(raw["nav_pre"][:5] == 0) and np.all(raw["nav_next"][:5] == 1)
        assert np.all(raw["nav_pre"][5:] == 1) and np.all(raw["nav_next"][5:] == 1)
    else:
        assert row["policy_cache_hits"] == 5 and row["policy_counts"]["misses"] == 5
        assert row["zero_displacement_uav_ticks"] == 40
        assert row["physical_hold_changes"] == row["category_changes"] == 0
        assert check["source_counts"]["trajectories"] == 270
        assert row["policy_counts"]["trajectories"] == 135


def test_partial_failure_preserves_actual_work(tmp_path):
    class FailingEnvironment(FabricatedEnvironment):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("fabricated native-call failure")
            return super().step(commands)

    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="fabricated native-call"):
        execute_fixture(out, FailingEnvironment)
    saved = json.loads((out / "summary.json").read_text())
    assert saved["state"] == "FAILED"
    assert saved["counts"]["native_step_calls"] == 3 and saved["counts"]["native_steps"] == 2
    assert saved["counts"]["ordinary_queries"] == 5 and saved["counts"]["complete_episodes"] == 0
    assert len(list((out / "raw").glob("*.partial.npz"))) == 1


def test_admission_precedes_science_and_fixture_cannot_expose_production(tmp_path, monkeypatch):
    from scripts import hmasd_admission
    from experiments.candidates.uav_fleet_transmission.b07_joint_renewal import run

    def refuse(*args, **kwargs):
        raise RuntimeError("fabricated admission refusal")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    out = tmp_path / "not_created"
    with pytest.raises(RuntimeError, match="fabricated admission refusal"):
        run.main(["--out", str(out), "--launch-sha", "synthetic", "--seed", "29750100"])
    assert not out.exists()
    with pytest.raises(ValueError, match="synthetic fixture cannot"):
        study._execute(out, "synthetic", protocol=FROZEN, env_factory=None, repo=REPO,
                       admission=None, scientific_invocation=False)
    assert not out.exists()
