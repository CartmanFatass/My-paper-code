"""Update-phase equivalence harness (throughput refactor P4).

Specification: `docs/Claude_docs/plans/ENV_THROUGHPUT_REFACTOR_PLAN_20260902.md` section 3 phase
P4, and the owner decision recorded in `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`
section XI.4 (2026-09-03: "P4 first, then E2", under the refactor plan's equivalence policy).

What it does
------------

For each E-series arm (`off` and `d0`) it drives the batched base-route loop at a small but
structurally complete configuration - scenario 1, `n_uavs = 6`, `n_users = 50`, 4 lanes,
`rollout_length = episode_length = 40`, `k = 10`, one fixed seed - for **two** rollouts with a
full `agent.update` after each, and records

  * every parameter tensor of `skill_coordinator`, `skill_discoverer`, `team_discriminator`
    and `individual_discriminator` after the second update, and
  * the numeric fields of both `agent.update` return dictionaries.

Two updates rather than one: the second runs on parameters the first already moved, so any
divergence introduced in the update path compounds instead of cancelling.

The tape is written once from the code as it stood before any P4 edit, to

  temp/directions/flexible_skill_duration/test/update_reference_tape_<sha12>.npz

(gitignored). Its container-independent content digest - sha256 over `(name, dtype, shape,
bytes)` for every array, sorted by name - is pinned below as `EXPECTED_TAPE_CONTENT_SHA256`.
A missing tape is regenerated and must reproduce that digest.

Equivalence policy (in order of preference, from the P4 hand-off):

1. bit-identical parameters and losses - `MAX_ABSOLUTE_DIFFERENCE = 0.0`;
2. otherwise tolerance equivalence at `1e-9` absolute, which spends the single fingerprint
   re-freeze the owner authorised in plan section 6.1 and must be recorded in an addendum to
   the D2 implementation report. Relaxing `MAX_ABSOLUTE_DIFFERENCE` is therefore a documented
   decision, not a convenience.

The harness pins `torch.set_num_threads(1)` so the tape is reproducible independently of the
machine's load; thread count itself changes float reduction order and is not a code change this
phase makes. The scale cross-check the harness cannot give (32 lanes, 4 threads) is the E0
timing run's evaluation return mean, which P3 showed reproduces bit-for-bit.

Regenerate the tape (before any P4 edit only):

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe tests/update_phase_equivalence_test.py --write

Run:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -s \
        tests/update_phase_equivalence_test.py \
        --basetemp C:/Projects/HMASD/temp/pytest_uav_env_refactor -p no:cacheprovider
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config_1 import Config  # noqa: E402
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter  # noqa: E402
from envs.pettingzoo.scenario1 import UAVBaseStationEnv  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

# --- frozen harness configuration -------------------------------------------------------

BASE_SEED = 20260903
N_UAVS = 6
N_USERS = 50
NUM_ENVS = 4
ROLLOUT_LENGTH = 40
EPISODE_LENGTH = 40
SKILL_INTERVAL = 10
N_ROLLOUTS = 2
ARMS = ("off", "d0")

#: preference 1 of the P4 equivalence policy.
MAX_ABSOLUTE_DIFFERENCE = 0.0
#: preference 2, used only with a recorded re-freeze.
TOLERANCE_ABSOLUTE = 1e-9

TAPE_DIR = REPO_ROOT / "temp" / "directions" / "flexible_skill_duration" / "test"
EXPECTED_TAPE_CONTENT_SHA256 = (
    "d870652006702f0c31413b6011054c19c8229da3332cf3a8dad6bccf03e26c06"
)
TAPE_PATH = TAPE_DIR / f"update_reference_tape_{EXPECTED_TAPE_CONTENT_SHA256[:12]}.npz"
SUMMARY_PATH = TAPE_DIR / "update_phase_equivalence_summary.json"


class UpdateEquivalenceConfig(Config):
    """Module-level subclass so the configuration is picklable and stable."""


def _make_config(arm, state_dim, obs_dim):
    """The E0 arm definitions (`scripts/run_flexible_skill_duration_e0.py::_make_config`)."""
    config = UpdateEquivalenceConfig()
    config.n_uavs = N_UAVS
    config.n_users = N_USERS
    config.num_envs = NUM_ENVS
    config.rollout_length = ROLLOUT_LENGTH
    config.episode_length = EPISODE_LENGTH
    config.k = SKILL_INTERVAL
    config.seed = BASE_SEED
    config.total_timesteps = NUM_ENVS * ROLLOUT_LENGTH * N_ROLLOUTS
    if arm == "off":
        config.policy_interruption_mode = "off"
    else:  # D0 = `d2` with infinite costs and both caps tied to k
        config.policy_interruption_mode = "d2"
        config.interruption_delta = 1
        config.interruption_cost_c = float("inf")
        config.interruption_cost_c_Z = float("inf")
        config.skill_cap_k_max = SKILL_INTERVAL
        config.team_cap_k_Z = SKILL_INTERVAL
        config.age_feature = "off"
    config.update_env_dims(state_dim=state_dim, obs_dim=obs_dim, n_agents=N_UAVS)
    return config


def _make_envs():
    envs = []
    for rank in range(NUM_ENVS):
        raw_env = UAVBaseStationEnv(
            n_uavs=N_UAVS,
            n_users=N_USERS,
            max_steps=EPISODE_LENGTH,
            user_distribution="uniform",
            channel_model="free_space",
            seed=BASE_SEED + rank,
        )
        envs.append(ParallelToArrayAdapter(raw_env, seed=BASE_SEED + rank))
    return envs


def _numeric_losses(update_result):
    """(names, values) of every scalar numeric field of an `agent.update` result."""
    names, values = [], []
    for key in sorted(update_result):
        value = update_result[key]
        if isinstance(value, (bool, np.bool_)):
            continue
        if isinstance(value, (int, float, np.integer, np.floating)):
            names.append(key)
            values.append(float(value))
    return names, np.asarray(values, dtype=np.float64)


def _parameter_arrays(agent):
    """Every parameter tensor of the four covered modules."""
    modules = {
        "skill_coordinator": agent.skill_coordinator,
        "skill_discoverer": agent.skill_discoverer,
        "team_discriminator": agent.team_discriminator,
        "individual_discriminator": agent.individual_discriminator,
    }
    arrays = {}
    for module_name, module in modules.items():
        if module is None:
            continue
        state = module.state_dict()
        for key in sorted(state):
            tensor = state[key].detach().cpu().contiguous()
            arrays[f"{module_name}__{key}"] = np.ascontiguousarray(tensor.numpy())
    return arrays


def run_arm(arm, log_dir):
    """Drive two rollouts with an update after each and return the recorded arrays."""
    torch.set_num_threads(1)
    random.seed(BASE_SEED)
    np.random.seed(BASE_SEED)
    torch.manual_seed(BASE_SEED)

    envs = _make_envs()
    observations_list, states_list = [], []
    for env in envs:
        obs, info = env.reset()
        observations_list.append(np.asarray(obs, dtype=np.float32))
        states_list.append(np.asarray(info["state"], dtype=np.float64))
    observations = np.stack(observations_list)
    states = np.stack(states_list)

    config = _make_config(
        arm, state_dim=int(envs[0].state_dim), obs_dim=int(envs[0].obs_dim)
    )
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))

    env_steps = np.zeros(NUM_ENVS, dtype=int)
    dones_tracker = np.zeros(NUM_ENVS, dtype=bool)
    loss_names = None
    loss_rows = []

    for _rollout in range(N_ROLLOUTS):
        for t in range(ROLLOUT_LENGTH):
            actions, _infos, step_data = agent.step(
                states, observations, env_steps, dones_tracker,
                deterministic=False, return_step_data=True, build_infos=False,
            )
            next_observations_list, next_states_list = [], []
            rewards = np.zeros(NUM_ENVS, dtype=np.float64)
            dones = np.zeros(NUM_ENVS, dtype=bool)
            for env_idx, env in enumerate(envs):
                next_obs, reward, terminated, truncated, info = env.step(actions[env_idx])
                next_observations_list.append(np.asarray(next_obs, dtype=np.float32))
                next_states_list.append(np.asarray(info["next_state"], dtype=np.float64))
                rewards[env_idx] = float(reward)
                dones[env_idx] = bool(terminated or truncated)
            next_observations = np.stack(next_observations_list)
            next_states = np.stack(next_states_list)

            agent.store_transition_batch(
                states=states,
                next_states=next_states.copy(),
                observations=observations,
                next_observations=next_observations.copy(),
                actions=np.asarray(actions),
                rewards=rewards,
                dones=dones,
                infos_batch=None,
                rollout_step_idx=t,
                step_data=step_data,
            )

            policy_next_observations = next_observations.copy()
            for env_idx, env in enumerate(envs):
                if dones[env_idx]:
                    dones_tracker[env_idx] = True
                    env_steps[env_idx] = 0
                    agent.reset_env_state(env_idx)
                    reset_obs, _reset_info = env.reset()
                    policy_next_observations[env_idx] = np.asarray(reset_obs, dtype=np.float32)
                else:
                    env_steps[env_idx] += 1
            states = next_states
            observations = policy_next_observations
            dones_tracker = dones.copy()

        last_values = np.zeros((NUM_ENVS, config.n_agents), dtype=np.float32)
        update_result = agent.update(
            steps_in_buffer=ROLLOUT_LENGTH,
            last_values=last_values,
            dones=dones_tracker.copy(),
            last_state=states.copy(),
            last_observations=observations.copy(),
        )
        names, values = _numeric_losses(update_result)
        if loss_names is None:
            loss_names = names
        elif names != loss_names:
            raise RuntimeError("agent.update returned a different field set between rollouts")
        loss_rows.append(values)
        agent.clear_buffers()

    arrays = _parameter_arrays(agent)
    arrays["__losses__"] = np.asarray(loss_rows, dtype=np.float64)
    arrays["__loss_names__"] = np.asarray(loss_names)
    return arrays


def build_tape(log_root):
    tape = {}
    for arm in ARMS:
        for name, array in run_arm(arm, Path(log_root) / arm).items():
            tape[f"{arm}__{name}"] = array
    return tape


def content_sha256(tape):
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


@pytest.fixture(scope="session")
def reference_tape(tmp_path_factory):
    if TAPE_PATH.is_file():
        with np.load(TAPE_PATH, allow_pickle=False) as handle:
            tape = {name: handle[name] for name in handle.files}
    else:
        tape = build_tape(tmp_path_factory.mktemp("update_tape_logs"))
        TAPE_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.savez(TAPE_PATH, **tape)
    digest = content_sha256(tape)
    assert digest == EXPECTED_TAPE_CONTENT_SHA256, (
        "update reference tape content digest mismatch: expected "
        f"{EXPECTED_TAPE_CONTENT_SHA256}, got {digest}"
    )
    return tape


def _record_summary(arm, report):
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        summary = {}
    summary[arm] = report
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


@pytest.mark.parametrize("arm", ARMS)
def test_update_phase_matches_reference_tape(arm, reference_tape, tmp_path):
    """Post-update parameters and losses against the frozen pre-P4 tape."""
    started = time.perf_counter()
    measured = run_arm(arm, tmp_path / "agent_logs")
    elapsed = time.perf_counter() - started

    expected_names = sorted(
        name[len(arm) + 2:] for name in reference_tape if name.startswith(f"{arm}__")
    )
    assert sorted(measured) == expected_names, "the recorded parameter set changed"

    assert list(measured["__loss_names__"]) == list(
        reference_tape[f"{arm}____loss_names__"]
    ), "agent.update's numeric field set changed"

    worst_name = None
    worst_diff = 0.0
    above_tolerance = 0
    non_identical = 0
    positions = 0
    for name in expected_names:
        if name == "__loss_names__":
            continue
        expected = reference_tape[f"{arm}__{name}"]
        actual = measured[name]
        assert expected.shape == actual.shape, f"{name}: shape changed"
        difference = np.abs(
            actual.astype(np.float64, copy=False) - expected.astype(np.float64, copy=False)
        )
        positions += int(difference.size)
        largest = float(difference.max()) if difference.size else 0.0
        if largest > 0.0:
            non_identical += 1
        if largest > TOLERANCE_ABSOLUTE:
            above_tolerance += 1
        if largest > worst_diff:
            worst_diff = largest
            worst_name = name

    report = {
        "arm": arm,
        "seconds": elapsed,
        "tensors": len(expected_names) - 1,
        "positions": positions,
        "max_abs_diff": worst_diff,
        "max_abs_diff_tensor": worst_name,
        "tensors_not_bit_identical": non_identical,
        "tensors_above_1e-9": above_tolerance,
    }
    print(f"\n[update-equivalence] {json.dumps(report, sort_keys=True)}")
    _record_summary(arm, report)

    assert worst_diff <= TOLERANCE_ABSOLUTE, (
        f"{arm}: {worst_name} differs by {worst_diff:.3e}, above the {TOLERANCE_ABSOLUTE:.0e} "
        "tolerance the P4 policy allows"
    )
    assert worst_diff <= MAX_ABSOLUTE_DIFFERENCE, (
        f"{arm}: {worst_name} differs by {worst_diff:.3e}; the update path is no longer "
        "bit-identical. Spending the authorised fingerprint re-freeze is a recorded decision "
        "(plan section 6.1) - do not relax this constant without it."
    )


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit("pass --write to regenerate the update reference tape")
    log_root = (
        REPO_ROOT / "temp" / "directions" / "flexible_skill_duration" / "test" / "update_tape_logs"
    )
    written = build_tape(log_root)
    digest = content_sha256(written)
    TAPE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TAPE_DIR / f"update_reference_tape_{digest[:12]}.npz"
    np.savez(out_path, **written)
    print("tape content sha256:", digest)
    print("wrote:", out_path)
