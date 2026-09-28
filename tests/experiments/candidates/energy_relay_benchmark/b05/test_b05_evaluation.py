"""B05 canonical evaluator: identity = plain path (a), physical traces, one transform (g), FULL (h)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as b01
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b05 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b05 import frame as fr
from experiments.candidates.energy_relay_benchmark.b05 import readers as rd
from experiments.candidates.energy_relay_benchmark.b05 import run_b05
from experiments.candidates.uav_geometric_generalization.b01.symmetry import (
    D4, transform_observations, transform_state,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

REPO = Path(__file__).resolve().parents[5]
C06 = REPO / "runs/energy_relay_benchmark/b02_s1_set_a01r/checkpoints/c06"
C00 = REPO / "runs/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c00"
HORIZON = 24
needs_c06 = pytest.mark.skipif(not (C06 / "agent.pt").exists(),
                               reason="retained c06 checkpoint is not present on this test host")
ADDED_ROW_KEYS = {"arm", "frame", "spawn_corner", "users_in_access_range_t0", "full_speed"}
TIMING_KEYS = {"wall_seconds", "worker_peak_rss_kib"}


def _world(seed, mode, tmp_path, checkpoint=C06):
    record = json.loads((checkpoint / "record.json").read_text())
    return b01.WorldTask(controller="L", seed=seed, params=PRODUCTION_PARAMS, horizon=HORIZON,
                         policy_seed=int(record["training_seed"]), threads=1,
                         checkpoint=str(checkpoint / record["agent_pt"]),
                         expected_checkpoint_sha256=record["agent_pt_sha256"],
                         expected_policy_fingerprint=record["policy_fingerprint"],
                         log_dir=str(tmp_path), action_mode=mode,
                         draw=0 if mode == "stochastic" else None,
                         checkpoint_record=str(checkpoint / "record.json"))


@needs_c06
@pytest.mark.parametrize("mode", ["deterministic", "stochastic"])
def test_identity_frame_is_bitwise_the_plain_evaluator(mode, tmp_path):
    """(a) On a W,S world the SW wrapper picks IDENTITY and reproduces B01's evaluate_task bitwise
    (row readings, every per-step array: positions, QoS, rewards, modes, batteries...)."""
    torch.set_num_threads(1)
    world = _world(955001, mode, tmp_path)
    plain = b01.evaluate_task(world)
    canonical = ev.evaluate_canonical_task(ev.CanonicalTask(world=world, arm="C_SW"))
    assert canonical["row"]["frame"] == "IDENTITY" and canonical["row"]["spawn_corner"] == "W,S"
    assert set(canonical["row"]) - set(plain["row"]) == ADDED_ROW_KEYS
    for key, value in plain["row"].items():
        if key not in TIMING_KEYS:
            assert canonical["row"][key] == value, key
    assert plain["arrays"].keys() == canonical["arrays"].keys()
    for key, value in plain["arrays"].items():
        assert np.asarray(canonical["arrays"][key]).tobytes() == np.asarray(value).tobytes(), key
    assert plain["identity"] == canonical["identity"]
    trace = ev.canonical_trace_arrays([canonical])
    for key, value in b01.trace_arrays([plain]).items():
        assert trace[key].tobytes() == value.tobytes(), key
    # The observer's proposal is what the shield received; identity + no rescale: raw == proposal.
    observed = canonical["observation"]
    assert observed["proposal"].shape == (HORIZON, 8, 4)
    np.testing.assert_array_equal(observed["proposal"], observed["proposal_raw"])
    assert "world_0_proposal_raw" not in trace and trace["world_0_frame"] == D4.IDENTITY.value


@needs_c06
def test_non_identity_world_keeps_physical_traces(tmp_path):
    """On an E,S world (MIRROR_X) the recorded positions are physical: t = 0 equals the plain
    reset, and the physical proposal mirrors the canonical one."""
    torch.set_num_threads(1)
    world = _world(955003, "deterministic", tmp_path)
    plain = b01.evaluate_task(world)
    canonical = ev.evaluate_canonical_task(ev.CanonicalTask(world=world, arm="C_SW"))
    assert canonical["row"]["frame"] == "MIRROR_X" and canonical["row"]["spawn_corner"] == "E,S"
    assert canonical["arrays"]["own_xyz"][0].tobytes() == plain["arrays"]["own_xyz"][0].tobytes()
    assert canonical["row"]["users_in_access_range_t0"] == \
        ev.evaluate_canonical_task(ev.CanonicalTask(world=world, arm="C_SW"))["row"]["users_in_access_range_t0"]
    assert canonical["row"]["qos_per_step"] != plain["row"]["qos_per_step"] or \
        not np.array_equal(canonical["arrays"]["own_xyz"], plain["arrays"]["own_xyz"])


@needs_c06
def test_full_speed_rescales_before_the_shield(tmp_path):
    """(h) C_SW_FULL: the shield receives the unit-norm horizontal proposal; the raw proposal is
    recorded and at t = 0 equals C_SW's (same world, deterministic); z and dock unchanged."""
    torch.set_num_threads(1)
    world = _world(955003, "deterministic", tmp_path)
    base = ev.evaluate_canonical_task(ev.CanonicalTask(world=world, arm="C_SW"))
    full = ev.evaluate_canonical_task(ev.CanonicalTask(world=world, arm="C_SW_FULL"))
    raw, shielded_in = full["observation"]["proposal_raw"], full["observation"]["proposal"]
    assert raw[0].tobytes() == base["observation"]["proposal"][0].tobytes()
    for t in range(len(raw)):
        np.testing.assert_array_equal(shielded_in[t], fr.full_horizontal(raw[t]))
    np.testing.assert_array_equal(shielded_in[..., 2:], raw[..., 2:])
    norms = np.linalg.norm(shielded_in[..., :2].astype(np.float64), axis=-1)
    np.testing.assert_allclose(norms[np.linalg.norm(raw[..., :2], axis=-1) > 0], 1.0, atol=1e-6)
    assert full["row"]["full_speed"] is True
    assert "world_0_proposal_raw" in ev.canonical_trace_arrays([full])


class SpyEvaluator:
    device = "cpu"

    def __init__(self):
        self.inputs = []

    def reset_env_state(self, lane):
        pass

    def step(self, state, obs, steps, done, **kwargs):
        self.inputs.append((state[0].copy(), obs[0].copy()))
        return np.tile(np.array([.3, -.4, .5, .6], np.float32), (1, 8, 1)), None, None


@pytest.mark.parametrize("seed", [955001, 955002, 955003, 955005])
def test_evaluator_and_training_wrapper_feed_the_same_inputs(seed):
    """(g) For the same physical observation/state the evaluator's controller feeds exactly what the
    training collector feeds (``frame.canonical_inputs`` with ``sw_frame``; the collector side is
    pinned to the adapter in test_b05_training), and returns the inverse-transformed action."""
    env = make_env(b01.make_eval_config(8, 925031), seed)
    try:
        obs, info = env.reset(seed=seed)
        obs, state = np.asarray(obs, np.float32), np.asarray(info["state"], np.float32)
        spy = SpyEvaluator()
        controller = ev.SWController(spy, deterministic=True)
        controller.reset()
        action = controller.propose(obs, state, 0, np.ones(1, bool), np.zeros(8, bool))
        frame = fr.sw_frame(obs)
        expected_obs, expected_state = fr.canonical_inputs(obs, state, frame)
        assert spy.inputs[0][1].tobytes() == expected_obs.tobytes()
        assert spy.inputs[0][0].tobytes() == expected_state.tobytes()
        if frame != D4.IDENTITY:
            assert expected_obs.tobytes() == transform_observations(obs, frame).tobytes()
            assert expected_state.tobytes() == transform_state(state, frame).tobytes()
        np.testing.assert_array_equal(action, fr.physical_actions(
            np.tile(np.array([.3, -.4, .5, .6], np.float32), (8, 1)), frame))
        # Held for the episode even when the team crosses the centre; reset re-chooses.
        moved = obs.copy()
        moved[:, :2] = 1.0 - moved[:, :2]
        controller.propose(moved, state, 5, np.zeros(1, bool), np.zeros(8, bool))
        assert controller.frame is frame
        assert spy.inputs[1][1].tobytes() == fr.canonical_inputs(moved, state, frame)[0].tobytes()
        controller.reset()
        with pytest.raises(RuntimeError, match="episode reset"):
            controller.propose(obs, state, 3, np.zeros(1, bool), np.zeros(8, bool))
    finally:
        env.close()


@needs_c06
def test_panel_guards_create_nothing(tmp_path):
    out = tmp_path / "panel"
    with pytest.raises(ValueError, match="hold-out"):
        ev.run_panel(arm="C_SW", checkpoint_dir=C06, out=out, worlds=[957001], modes=["deterministic"],
                     final=False, launch_sha="x")
    with pytest.raises(ValueError, match="deterministic only"):
        ev.run_panel(arm="C_SW_FULL", checkpoint_dir=C06, out=out, worlds=[955001],
                     modes=["deterministic", "stochastic"], final=False, launch_sha="x")
    with pytest.raises(ValueError, match="deterministic only"):
        ev.run_panel(arm="C_SW_FULL", checkpoint_dir=C06, out=out, worlds=[957001],
                     modes=["deterministic"], final=True, launch_sha="x")
    with pytest.raises(ValueError, match="B05"):
        ev.run_panel(arm="B", checkpoint_dir=C06, out=out, worlds=[955001], modes=["deterministic"],
                     final=False, launch_sha="x")
    if (C00 / "agent.pt").exists():
        with pytest.raises(ValueError, match="frozen B02 c06"):
            ev.run_panel(arm="C_SW", checkpoint_dir=C00, out=out, worlds=[955001],
                         modes=["deterministic"], final=False, launch_sha="x")
    assert not out.exists()


def test_runner_admission_precedes_outputs(monkeypatch, tmp_path):
    import scripts.hmasd_admission

    def refusal(*args, **kwargs):
        raise RuntimeError("test admission refusal")

    monkeypatch.setattr(scripts.hmasd_admission, "require_admission", refusal)
    for argv in (["train", "--seed", "925031", "--launch-sha", "abc", "--out", str(tmp_path / "t")],
                 ["panel", "--arm", "C_SW", "--checkpoint", str(tmp_path / "missing"),
                  "--out", str(tmp_path / "p"), "--launch-sha", "abc"]):
        with pytest.raises(RuntimeError, match="test admission refusal"):
            run_b05.main(argv)
    assert not any(tmp_path.iterdir())
    with pytest.raises(SystemExit):
        run_b05.parse_args(["read", "--out", "x", "--panel", "A=p.json", "--pair", "L=A"])


@needs_c06
def test_panel_end_to_end_and_readers(tmp_path):
    """A two-world C_SW panel (W,S and E,S; H24) and a C_SW_FULL panel: records, traces with the
    b04 keys + the b05 arrays, manifest; then the readers over them (a pair by corner)."""
    torch.set_num_threads(1)
    common = dict(checkpoint_dir=C06, worlds=[955001, 955003], final=False, launch_sha="test",
                  workers=1, threads=1, horizon=HORIZON, argv=["test"])
    summary = ev.run_panel(arm="C_SW", out=tmp_path / "c_sw", modes=["deterministic", "stochastic"],
                           **common)
    full = ev.run_panel(arm="C_SW_FULL", out=tmp_path / "full", modes=["deterministic"], **common)
    assert summary["status"] == full["status"] == "COMPLETE"
    name = ev.panel_name("C_SW", "c06", "deterministic")
    panel = json.loads((tmp_path / "c_sw" / "panels" / f"{name}.json").read_text())
    assert panel["frames"] == {"955001": "IDENTITY", "955003": "MIRROR_X"}
    trace = np.load(tmp_path / "c_sw" / "traces" / f"{name}.npz")
    for key in ("own_xyz", "qos", "mode", "seed", "proposal", "submitted", "frame",
                "users_in_access_range_t0"):
        assert f"world_1_{key}" in trace.files
    manifest = json.loads((tmp_path / "c_sw" / "manifest.json").read_text())
    assert manifest["checkpoint"]["agent_pt_sha256"] == ev.C06_SHA256
    assert f"traces/{name}.npz" in manifest["artifacts"]
    assert not (tmp_path / "c_sw" / "logs").exists()
    with pytest.raises(FileExistsError):
        ev.run_panel(arm="C_SW", out=tmp_path / "c_sw", modes=["deterministic"], **common)
    full_name = ev.panel_name("C_SW_FULL", "c06", "deterministic")
    payload = rd.read(tmp_path / "read",
                      panels={"C_SW": str(tmp_path / "c_sw" / "panels" / f"{name}.json"),
                              "C_SW_FULL": str(tmp_path / "full" / "panels" / f"{full_name}.json")},
                      pairs={"FULL-C_SW": ("C_SW_FULL", "C_SW")})
    reading = payload["panels"]["C_SW"]
    assert reading["corners"] == {"955001": "W,S", "955003": "E,S"}
    assert reading["first_service_access_source"] == "panel rows"
    assert set(reading["inward"]["by_corner"]) == {"W,S", "E,S"}
    pair = payload["pairs"]["FULL-C_SW"]
    assert pair["paired_worlds"] == 2 and set(pair["metrics"]["qos_per_step"]["by_corner"]) == {"W,S", "E,S"}
    assert (tmp_path / "read" / "manifest.json").exists()


@pytest.fixture(scope="module")
def b05_c00(tmp_path_factory):
    """A production-architecture B05 checkpoint record (c00 of the B recipe, CPU init)."""
    import time as _time

    from experiments.candidates.energy_relay_benchmark.b02 import training as b02_tr
    from experiments.candidates.energy_relay_benchmark.b05 import training as tr

    root = tmp_path_factory.mktemp("b05_fit")
    torch.set_num_threads(1)
    spec = tr.production_spec(925031)
    recipe = tr.b05_recipe()
    config = recipe.make_config(spec)
    agent, _ = b02_tr.new_agent(config, device=torch.device("cpu"), log_dir=root / "logs",
                                seed=spec.seed)
    b02_tr.save_checkpoint(agent, config, spec, root, 0, rollout=0, transitions=0,
                           started=_time.perf_counter(), launch_sha="test", recipe=recipe)
    return root / "checkpoints" / "c00"


def test_arm_b_evaluates_a_b05_checkpoint(b05_c00, tmp_path):
    """Arm B takes the B05 record (object, frame rule) through the same evaluator; the c06-only arms
    refuse it; B's and C_SW's stochastic panels share the sample seed of each world."""
    torch.set_num_threads(1)
    summary = ev.run_panel(arm="B", checkpoint_dir=b05_c00, out=tmp_path / "b", worlds=[955002],
                           modes=["deterministic", "stochastic"], final=False, launch_sha="test",
                           workers=1, threads=1, horizon=HORIZON, argv=["test"])
    assert summary["status"] == "COMPLETE" and summary["checkpoint_object_id"] == "ENERGY-RELAY-BENCHMARK-B05"
    panel = json.loads((tmp_path / "b" / "panels" / f"{ev.panel_name('B', 'c00', 'stochastic')}.json").read_text())
    assert panel["frames"] == {"955002": "MIRROR_Y"}
    assert panel["sample_seeds"]["955002"] == b01.sample_seed(925031, 955002, 0)
    with pytest.raises(ValueError, match="frozen B02 c06"):
        ev.run_panel(arm="C_SW", checkpoint_dir=b05_c00, out=tmp_path / "x", worlds=[955001],
                     modes=["deterministic"], final=False, launch_sha="x")
