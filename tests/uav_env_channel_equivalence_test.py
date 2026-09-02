"""Scenario-1 channel-model equivalence harness (throughput refactor P0).

Specification: `docs/Claude_docs/plans/ENV_THROUGHPUT_REFACTOR_PLAN_20260902.md` section 3,
phase P0, with the owner decisions of section 6.1 (tolerance-level equivalence: `1e-9`
absolute on SINR, rewards, observations and the global state; the connection matrices exactly
equal).

What it does
------------

For every `channel_model` `envs/pettingzoo/uav_env.py` accepts, it builds
`UAVBaseStationEnv(n_uavs=6, n_users=50, max_steps=500)`, drives it through two 500-step
episodes with a fixed seeded action sequence, and records per step

  * `sinr_matrix`      [n_uavs, n_users] float64
  * `connections`      [n_uavs, n_users] bool
  * `rewards`          [n_uavs]          float64  (the per-agent rewards of `step`)
  * `observations`     [n_uavs, obs_dim] float32  (the `obs` field of each agent)
  * `state`            [state_dim]       float64  (`_get_state`)

The tape is written **once**, from the reference (scalar) channel backend, to

  temp/directions/flexible_skill_duration/test/uav_env_reference_tape_<sha12>.npz

which is gitignored. Its content digest — a sha256 over the named arrays (name, dtype, shape,
bytes, sorted by name), independent of the `.npz` container's timestamps — is recorded below as
`EXPECTED_TAPE_CONTENT_SHA256`. If the tape file is missing the harness regenerates it from the
reference backend (the oracle) and refuses to continue unless the regenerated content digest
matches. So a lost tape costs time, not evidence.

The live environment (default backend) is then replayed against the tape.

Regenerate the tape (reference backend; prints the content digest):

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        tests/uav_env_channel_equivalence_test.py --write

Run the harness:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -s \
        tests/uav_env_channel_equivalence_test.py \
        --basetemp C:/Projects/HMASD/temp/pytest_uav_env_refactor -p no:cacheprovider

`-s` shows the per-quantity difference report and the measured per-step wall time, neither of
which is asserted beyond the tolerances above.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
import time
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from envs.pettingzoo.scenario1 import UAVBaseStationEnv  # noqa: E402

# --- frozen harness configuration -------------------------------------------------------

N_UAVS = 6
N_USERS = 50
EPISODE_LENGTH = 500
N_EPISODES = 2
AREA_SIZE = 1000
ENV_SEED = 20260902
ACTION_SEED = 20260902

#: every model `_compute_path_loss_reference` accepts, in a fixed order.
CHANNEL_MODELS = (
    "free_space",
    "urban",
    "suburban",
    "3gpp-36777",
    "probabilistic",
)

#: owner decision (plan section 6.1).
ABSOLUTE_TOLERANCE = 1e-9
#: reported, not asserted: how many positions moved at all.
REPORT_THRESHOLD = 1e-12

TAPE_DIR = REPO_ROOT / "temp" / "directions" / "flexible_skill_duration" / "test"
#: sha256 over the tape's named arrays; frozen from the reference backend on 2026-09-02.
EXPECTED_TAPE_CONTENT_SHA256 = (
    "cf389585ba62371e2c95b63cd645f6de29d87ad0b421de5587e838a17ebf8c02"
)
TAPE_PATH = TAPE_DIR / f"uav_env_reference_tape_{EXPECTED_TAPE_CONTENT_SHA256[:12]}.npz"
SUMMARY_PATH = TAPE_DIR / "uav_env_channel_equivalence_summary.json"

_QUANTITIES = ("sinr", "connections", "rewards", "observations", "state")


# --- environment driving ----------------------------------------------------------------


def _supports_backend() -> bool:
    return "channel_backend" in inspect.signature(UAVBaseStationEnv.__init__).parameters


def _make_env(channel_model: str, backend: str | None = None):
    kwargs = dict(
        n_uavs=N_UAVS,
        n_users=N_USERS,
        area_size=AREA_SIZE,
        max_steps=EPISODE_LENGTH,
        user_distribution="uniform",
        channel_model=channel_model,
        seed=ENV_SEED,
    )
    if backend is not None:
        if not _supports_backend():
            raise RuntimeError(
                "this environment has no channel_backend parameter; "
                "the reference oracle is unavailable"
            )
        kwargs["channel_backend"] = backend
    return UAVBaseStationEnv(**kwargs)


def _action_sequence(n_steps: int) -> np.ndarray:
    """One fixed action tape shared by every channel model and both backends."""
    rng = np.random.RandomState(ACTION_SEED)
    return rng.uniform(-1.0, 1.0, size=(N_EPISODES, n_steps, N_UAVS, 3)).astype(np.float64)


def _drive(env, actions: np.ndarray) -> dict[str, np.ndarray]:
    """Run `N_EPISODES` episodes and return the recorded tape for one channel model."""
    agents = [f"uav_{i}" for i in range(N_UAVS)]
    obs_dim = env.obs_dim
    state_dim = env.state_dim
    total = N_EPISODES * EPISODE_LENGTH

    sinr = np.empty((total, N_UAVS, N_USERS), dtype=np.float64)
    connections = np.empty((total, N_UAVS, N_USERS), dtype=bool)
    rewards = np.empty((total, N_UAVS), dtype=np.float64)
    observations = np.empty((total, N_UAVS, obs_dim), dtype=np.float32)
    state = np.empty((total, state_dim), dtype=np.float64)

    row = 0
    for episode in range(N_EPISODES):
        env.reset(seed=ENV_SEED + episode)
        for step_idx in range(EPISODE_LENGTH):
            action_dict = {
                agent: actions[episode, step_idx, idx].copy()
                for idx, agent in enumerate(agents)
            }
            step_observations, step_rewards, _terminations, _truncations, _infos = env.step(
                action_dict
            )
            sinr[row] = env.sinr_matrix
            connections[row] = env.connections
            rewards[row] = [step_rewards[agent] for agent in agents]
            observations[row] = [step_observations[agent]["obs"] for agent in agents]
            state[row] = env._get_state()
            row += 1

    return {
        "sinr": sinr,
        "connections": connections,
        "rewards": rewards,
        "observations": observations,
        "state": state,
    }


def _tape_key(channel_model: str, quantity: str) -> str:
    return f"{channel_model.replace('-', '_')}__{quantity}"


def build_tape(backend: str | None = "reference") -> dict[str, np.ndarray]:
    """Drive every channel model and return the flat array mapping written to the npz."""
    actions = _action_sequence(EPISODE_LENGTH)
    tape: dict[str, np.ndarray] = {}
    for channel_model in CHANNEL_MODELS:
        env = _make_env(channel_model, backend=backend)
        recorded = _drive(env, actions)
        for quantity, array in recorded.items():
            tape[_tape_key(channel_model, quantity)] = array
    return tape


def content_sha256(tape: dict[str, np.ndarray]) -> str:
    """Container-independent digest: name, dtype, shape and bytes, sorted by name."""
    digest = hashlib.sha256()
    for name in sorted(tape):
        array = np.ascontiguousarray(tape[name])
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(array.dtype.str).encode("ascii"))
        digest.update(b"\0")
        digest.update(json.dumps(list(array.shape)).encode("ascii"))
        digest.update(b"\0")
        digest.update(array.tobytes())
        digest.update(b"\0")
    return digest.hexdigest()


def write_tape(path: Path = TAPE_PATH) -> str:
    tape = build_tape(backend="reference" if _supports_backend() else None)
    digest = content_sha256(tape)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **tape)
    return digest


# --- fixtures ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def reference_tape() -> dict[str, np.ndarray]:
    """The frozen tape, regenerated from the reference backend when the file is gone."""
    if TAPE_PATH.is_file():
        with np.load(TAPE_PATH) as handle:
            tape = {name: handle[name] for name in handle.files}
    else:
        tape = build_tape(backend="reference" if _supports_backend() else None)
        TAPE_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.savez(TAPE_PATH, **tape)
    digest = content_sha256(tape)
    assert digest == EXPECTED_TAPE_CONTENT_SHA256, (
        "reference tape content digest mismatch: expected "
        f"{EXPECTED_TAPE_CONTENT_SHA256}, got {digest}"
    )
    return tape


# --- the harness ------------------------------------------------------------------------


def _difference_report(expected: np.ndarray, measured: np.ndarray) -> dict[str, float]:
    difference = np.abs(
        measured.astype(np.float64, copy=False) - expected.astype(np.float64, copy=False)
    )
    return {
        "max_abs_diff": float(difference.max()) if difference.size else 0.0,
        "above_1e-12": int(np.count_nonzero(difference > REPORT_THRESHOLD)),
        "positions": int(difference.size),
    }


@pytest.mark.parametrize("channel_model", CHANNEL_MODELS)
def test_live_channel_model_matches_reference_tape(channel_model, reference_tape):
    """Live environment against the frozen reference tape, at the plan's tolerances."""
    actions = _action_sequence(EPISODE_LENGTH)
    env = _make_env(channel_model)

    started = time.perf_counter()
    measured = _drive(env, actions)
    elapsed = time.perf_counter() - started
    steps = N_EPISODES * EPISODE_LENGTH

    report: dict[str, object] = {
        "channel_model": channel_model,
        "seconds_per_step": elapsed / steps,
        "steps": steps,
    }
    for quantity in _QUANTITIES:
        expected = reference_tape[_tape_key(channel_model, quantity)]
        report[quantity] = _difference_report(expected, measured[quantity])

    print(f"\n[uav-env-equivalence] {json.dumps(report, sort_keys=True)}")
    _record_summary(channel_model, report)

    expected_connections = reference_tape[_tape_key(channel_model, "connections")]
    mismatches = int(np.count_nonzero(expected_connections != measured["connections"]))
    assert mismatches == 0, (
        f"{channel_model}: {mismatches} connection-matrix positions differ; "
        "the greedy assignment order is not reproduced"
    )

    for quantity in ("sinr", "rewards", "observations", "state"):
        max_abs = report[quantity]["max_abs_diff"]
        assert max_abs <= ABSOLUTE_TOLERANCE, (
            f"{channel_model}: {quantity} max abs diff {max_abs:.3e} exceeds "
            f"{ABSOLUTE_TOLERANCE:.0e}"
        )


def _record_summary(channel_model: str, report: dict[str, object]) -> None:
    """Accumulate the per-model reports into one gitignored JSON summary."""
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        summary = {}
    summary[channel_model] = report
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_reference_backend_reproduces_the_tape(reference_tape):
    """The scalar oracle still reproduces the tape bit for bit (free_space only, for time)."""
    if not _supports_backend():
        pytest.skip("environment has no channel_backend parameter yet (pre-P1)")
    actions = _action_sequence(EPISODE_LENGTH)
    env = _make_env("free_space", backend="reference")
    measured = _drive(env, actions)
    for quantity in _QUANTITIES:
        expected = reference_tape[_tape_key("free_space", quantity)]
        np.testing.assert_array_equal(expected, measured[quantity])


def test_step_wall_time_is_reported(capsys):
    """Not an assertion: record the per-step wall time at the harness configuration."""
    actions = _action_sequence(EPISODE_LENGTH)
    env = _make_env("free_space")
    env.reset(seed=ENV_SEED)
    agents = [f"uav_{i}" for i in range(N_UAVS)]
    warmup = 20
    measured_steps = 200
    for step_idx in range(warmup + measured_steps):
        if step_idx == warmup:
            started = time.perf_counter()
        action_dict = {
            agent: actions[0, step_idx, idx].copy() for idx, agent in enumerate(agents)
        }
        env.step(action_dict)
    elapsed = time.perf_counter() - started
    per_step_ms = 1000.0 * elapsed / measured_steps
    print(
        f"\n[uav-env-equivalence] free_space per-step wall time: {per_step_ms:.3f} ms "
        f"over {measured_steps} steps at n_uavs={N_UAVS}, n_users={N_USERS}"
    )
    _record_summary("__timing__", {"per_step_ms": per_step_ms, "steps": measured_steps})
    assert per_step_ms > 0.0


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(
            "pass --write to regenerate the reference tape from the reference backend"
        )
    written_digest = write_tape()
    print("tape content sha256:", written_digest)
    print("wrote:", TAPE_PATH)
