"""D2 policy-based interruption — the nine tests of the implementation plan.

Specification: `docs/Claude_docs/plans/D2_IMPLEMENTATION_PLAN_20260902.md` sections 2 and 10,
against `docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md` (revision 3, accepted) and the
non-blocking implementer notes in Part III of
`docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`.

Test map (plan section 10):

  1  invariant 1   `off` reproduces the phase 0 fingerprint byte for byte
  1b invariant 1   `off` allocates no D2 state at all
  2  invariant 2   D0 and `off` boundary masks agree across a mid-rollout reset
                   (review III.1.2), and the target scale ratio matches
                   tau (1 - gamma) / (1 - gamma^tau) (review III.1 P4)
  3  invariant 3   infinite costs permit no switch before the relevant cap
  4  invariant 4   at c = 0 every live agent is sampled every step
  5  invariant 5   scripted S_t: segment lengths partition the live steps
  6  invariant 6   non-contiguous S_t replays exactly, forced positions zero
  7  invariant 7   a team decision closes every agent segment
  8  invariant 8   table shapes, the ADR target formula, normalized ages
  9  review III.1.3 the trigger path draws no RNG

Review follow-ups (Part VII findings F1, F3, F4; owner decisions in VII.5):

  10 VII F1       `d2` refuses a rollout_length that is not a multiple of episode_length
  11 VII F4       `d2` refuses age_feature='normalized' with a compact discriminator
  12 VII F3       stored rows replay to the collection log-probabilities

The phase 0 fingerprint in `tests/fixtures/flexible_skill_duration_d2/fingerprint_off.json`
was produced strictly before any edit to `config_1.py`, `hmasd/networks.py`, `hmasd/agent.py`,
or `hmasd/utils.py`. It is the only reference invariant 1 ("`off` is byte-identical to current
HMASD on the same seed") has; it must never be regenerated after a D2 edit.

The drivers mirror the batched base-route loop of `train_multiproc_config_1.py:4567-5036`
(`agent.step` -> env step with terminal-state storage semantics -> `store_transition_batch`
-> per-env reset bookkeeping -> discoverer bootstrap -> `agent.update`), at the small
deterministic configuration fixed by the plan: scenario 1, three UAVs, two environments,
`rollout_length 40`, `episode_length 40`, `k 10`, one seed. Two rollouts run with one
`agent.update` (one `update_coordinator`) in between.

Run the tests with the explicit interpreter and an isolated basetemp:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
        tests/flexible_skill_duration_d2_test.py \
        --basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt

Regenerate the fixture (baseline code only, never after a D2 edit):

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        tests/flexible_skill_duration_d2_test.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
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
from hmasd.networks import SkillCoordinator  # noqa: E402
from hmasd.utils import RolloutBuffer  # noqa: E402

BASE_SEED = 20260902
N_UAVS = 3
N_USERS = 50
NUM_ENVS = 2
ROLLOUT_LENGTH = 40
EPISODE_LENGTH = 40

FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "flexible_skill_duration_d2" / "fingerprint_off.json"
)


class FingerprintConfig(Config):
    """Small deterministic scenario-1 configuration (plan section 2, phase 0)."""

    n_uavs = N_UAVS
    n_users = N_USERS
    num_envs = NUM_ENVS
    rollout_length = ROLLOUT_LENGTH
    episode_length = EPISODE_LENGTH
    k = 10
    seed = BASE_SEED


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _state_dict_sha256(module) -> str:
    digest = hashlib.sha256()
    state = module.state_dict()
    for key in sorted(state.keys()):
        tensor = state[key].detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(np.ascontiguousarray(tensor.numpy()).tobytes())
    return digest.hexdigest()


def _high_level_snapshot(rollout_buffer) -> dict:
    snapshot = {}
    for name in (
        "high_level_valid_mask",
        "high_level_rewards",
        "high_level_state_values",
        "high_level_agent_values",
        "high_level_team_log_probs",
        "high_level_agent_log_probs",
        "high_level_elapsed_steps",
        "high_level_terminal",
        "high_level_close_reason",
    ):
        snapshot[name] = np.asarray(getattr(rollout_buffer, name)[:ROLLOUT_LENGTH]).tolist()
    return snapshot


def _config_snapshot(config: Config) -> dict:
    names = (
        "n_agents", "n_uavs", "n_users", "num_envs", "rollout_length", "episode_length",
        "k", "n_Z", "n_z", "state_dim", "obs_dim", "action_dim", "action_space_type",
        "gamma", "ppo_epochs", "lambda_h", "lambda_e", "hidden_size", "embedding_dim",
        "n_heads", "gru_hidden_size", "use_valuenorm", "use_obsnorm", "use_statenorm",
        "strict_hmasd_alignment", "seed", "high_level_buffer_size", "high_level_batch_size",
        "buffer_size",
    )
    return {name: getattr(config, name, None) for name in names}


def _generate_fingerprint(log_dir: Path) -> dict:
    """Run the base route twice with one update in between and record the fingerprint."""

    torch.set_num_threads(1)
    random.seed(BASE_SEED)
    np.random.seed(BASE_SEED)
    torch.manual_seed(BASE_SEED)

    envs = []
    for env_idx in range(NUM_ENVS):
        raw_env = UAVBaseStationEnv(
            n_uavs=N_UAVS,
            n_users=N_USERS,
            max_steps=EPISODE_LENGTH,
            user_distribution="uniform",
            channel_model="free_space",
            seed=BASE_SEED + env_idx,
        )
        envs.append(ParallelToArrayAdapter(raw_env, seed=BASE_SEED + env_idx))

    observations_list = []
    states_list = []
    for env in envs:
        obs, info = env.reset()
        observations_list.append(np.asarray(obs, dtype=np.float32))
        states_list.append(np.asarray(info["state"], dtype=np.float64))
    observations = np.stack(observations_list)
    states = np.stack(states_list)

    config = FingerprintConfig()
    config.update_env_dims(
        state_dim=int(envs[0].state_dim),
        obs_dim=int(envs[0].obs_dim),
        n_agents=N_UAVS,
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))

    loop = {
        "states": states,
        "observations": observations,
        "env_steps": np.zeros(NUM_ENVS, dtype=int),
        "dones_tracker": np.zeros(NUM_ENVS, dtype=bool),
        "next_states": None,
        "next_observations": None,
    }

    def run_rollout(record: dict) -> None:
        for t in range(ROLLOUT_LENGTH):
            actions, _infos, step_data = agent.step(
                loop["states"],
                loop["observations"],
                loop["env_steps"],
                loop["dones_tracker"],
                deterministic=False,
                return_step_data=True,
                build_infos=False,
            )

            next_observations_list = []
            next_states_list = []
            rewards = np.zeros(NUM_ENVS, dtype=np.float64)
            dones = np.zeros(NUM_ENVS, dtype=bool)
            step_records = []
            for env_idx, env in enumerate(envs):
                next_obs, reward, terminated, truncated, info = env.step(actions[env_idx])
                done = bool(terminated or truncated)
                next_observations_list.append(np.asarray(next_obs, dtype=np.float32))
                next_states_list.append(np.asarray(info["next_state"], dtype=np.float64))
                rewards[env_idx] = float(reward)
                dones[env_idx] = done
                log_probs = step_data["log_probs"][env_idx]
                step_records.append(
                    [
                        t,
                        env_idx,
                        int(loop["env_steps"][env_idx]),
                        int(step_data["team_skills"][env_idx]),
                        [int(v) for v in np.asarray(step_data["agent_skills"][env_idx]).tolist()],
                        float(log_probs["team_log_prob"]),
                        [float(v) for v in log_probs["agent_log_probs"]],
                    ]
                )
            record["steps"].append(step_records)

            next_observations = np.stack(next_observations_list)
            next_states = np.stack(next_states_list)

            # Storage keeps the terminal transition; the policy input after a done uses the
            # reset observation, exactly as the SubprocVecEnv path does (no 'reset_state'
            # from this collector, so the policy state stays the terminal state).
            agent.store_transition_batch(
                states=loop["states"],
                next_states=next_states.copy(),
                observations=loop["observations"],
                next_observations=next_observations.copy(),
                actions=np.asarray(actions),
                rewards=rewards,
                dones=dones,
                infos_batch=None,
                rollout_step_idx=t,
                step_data=step_data,
            )

            policy_next_states = next_states.copy()
            policy_next_observations = next_observations.copy()
            for env_idx, env in enumerate(envs):
                if dones[env_idx]:
                    loop["dones_tracker"][env_idx] = True
                    loop["env_steps"][env_idx] = 0
                    agent.reset_env_state(env_idx)
                    reset_obs, _reset_info = env.reset()
                    policy_next_observations[env_idx] = np.asarray(reset_obs, dtype=np.float32)
                else:
                    loop["env_steps"][env_idx] += 1
            loop["states"] = policy_next_states
            loop["observations"] = policy_next_observations
            loop["dones_tracker"] = dones.copy()
            loop["next_states"] = next_states
            loop["next_observations"] = next_observations

        record["high_level"] = _high_level_snapshot(agent.rollout_buffer)

    fingerprint = {
        "schema_version": 1,
        "driver": "tests/flexible_skill_duration_d2_test.py",
        "config": None,  # filled after update_env_dims
        "versions": {"numpy": np.__version__, "torch": torch.__version__},
        "rollout_1": {"steps": [], "high_level": None},
        "state_dict_sha256_after_update": None,
        "rollout_2": {"steps": [], "high_level": None},
    }

    run_rollout(fingerprint["rollout_1"])
    fingerprint["config"] = _config_snapshot(config)

    # Bootstrap value of s_{T+1} (mirrors train_multiproc_config_1.py:4942-5005).
    last_values_predicted = np.zeros((NUM_ENVS, config.n_agents), dtype=np.float32)
    with torch.no_grad():
        next_team_skills = np.zeros(NUM_ENVS, dtype=np.int64)
        for env_idx in range(NUM_ENVS):
            next_env_step = int(loop["env_steps"][env_idx]) + 1
            if next_env_step % config.k == 0:
                next_team_skill, _next_agent_skills, _ = agent.assign_skills(
                    loop["next_states"][env_idx], loop["next_observations"][env_idx]
                )
            else:
                next_team_skill = agent.env_team_skills.get(env_idx, 0)
                if next_team_skill == -1:
                    next_team_skill = 0
            next_team_skills[env_idx] = int(next_team_skill)

        normalized_next_states = agent._normalize_states(loop["next_states"], update=False)
        global_state_tensor = torch.FloatTensor(normalized_next_states).to(agent.device)
        team_skill_tensor = torch.as_tensor(
            next_team_skills, dtype=torch.long, device=agent.device
        )

        critic_hidden_batch = np.zeros((NUM_ENVS, config.gru_hidden_size), dtype=np.float32)
        for env_idx in range(NUM_ENVS):
            critic_hidden_batch[env_idx] = agent.get_current_critic_hidden_np(
                env_idx, agent_index=0
            )
        critic_hidden_tensor = torch.FloatTensor(critic_hidden_batch).to(agent.device)

        global_value_tensor, _ = agent.skill_discoverer.get_value(
            global_state_tensor, team_skill_tensor, critic_hidden_state=critic_hidden_tensor
        )
        if config.use_valuenorm and agent.value_norm_discoverer is not None:
            global_value_tensor = agent._denormalize_values(
                global_value_tensor, agent.value_norm_discoverer
            )
        bootstrap_values = (
            global_value_tensor.squeeze(-1).detach().cpu().numpy().reshape(NUM_ENVS, 1)
        )
        last_values_predicted[:, :] = bootstrap_values

    agent.update(
        steps_in_buffer=ROLLOUT_LENGTH,
        last_values=last_values_predicted,
        dones=loop["dones_tracker"].copy(),
        last_state=loop["states"].copy(),
        last_observations=loop["observations"].copy(),
    )
    # Mirrors train_multiproc_config_1.py:5132 — buffers are cleared after each update,
    # otherwise the next rollout's stores are rejected as time steps going backwards.
    agent.clear_buffers()

    fingerprint["state_dict_sha256_after_update"] = {
        "skill_coordinator": _state_dict_sha256(agent.skill_coordinator),
        "team_discriminator": (
            _state_dict_sha256(agent.team_discriminator)
            if agent.team_discriminator is not None
            else None
        ),
        "individual_discriminator": (
            _state_dict_sha256(agent.individual_discriminator)
            if agent.individual_discriminator is not None
            else None
        ),
    }

    run_rollout(fingerprint["rollout_2"])
    return fingerprint


# ---------------------------------------------------------------------------
# D2 shared driver (phase 8).  Small deterministic scenario-1 configuration,
# mirroring the phase 0 driver's batched loop.
# ---------------------------------------------------------------------------


def _make_config(mode, episode_length=EPISODE_LENGTH, rollout_length=ROLLOUT_LENGTH,
                 state_dim=None, obs_dim=None, **overrides):
    class _D2Config(Config):
        n_uavs = N_UAVS
        n_users = N_USERS
        num_envs = NUM_ENVS
        seed = BASE_SEED

    config = _D2Config()
    config.rollout_length = rollout_length
    config.episode_length = episode_length
    config.k = 10
    config.policy_interruption_mode = mode
    for name, value in overrides.items():
        setattr(config, name, value)
    if state_dim is not None:
        config.update_env_dims(state_dim=state_dim, obs_dim=obs_dim, n_agents=N_UAVS)
    config.validate_config()
    return config


def _make_envs(episode_length):
    envs = []
    for env_idx in range(NUM_ENVS):
        raw_env = UAVBaseStationEnv(
            n_uavs=N_UAVS,
            n_users=N_USERS,
            max_steps=episode_length,
            user_distribution="uniform",
            channel_model="free_space",
            seed=BASE_SEED + env_idx,
        )
        envs.append(ParallelToArrayAdapter(raw_env, seed=BASE_SEED + env_idx))
    return envs


def _run_rollout(mode, log_dir, steps=ROLLOUT_LENGTH, episode_length=EPISODE_LENGTH,
                 store=True, do_update=False, patch_held=None, **overrides):
    """Run one rollout of the batched base-route loop and return (agent, record)."""
    torch.set_num_threads(1)
    random.seed(BASE_SEED)
    np.random.seed(BASE_SEED)
    torch.manual_seed(BASE_SEED)

    envs = _make_envs(episode_length)
    observations_list, states_list = [], []
    for env in envs:
        obs, info = env.reset()
        observations_list.append(np.asarray(obs, dtype=np.float32))
        states_list.append(np.asarray(info["state"], dtype=np.float64))
    observations = np.stack(observations_list)
    states = np.stack(states_list)

    config = _make_config(
        mode,
        episode_length=episode_length,
        rollout_length=steps,
        state_dim=int(envs[0].state_dim),
        obs_dim=int(envs[0].obs_dim),
        **overrides,
    )
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))
    if patch_held is not None:
        agent.skill_coordinator.evaluate_held_batch = patch_held(agent.skill_coordinator)

    env_steps = np.zeros(NUM_ENVS, dtype=int)
    dones_tracker = np.zeros(NUM_ENVS, dtype=bool)
    keys = ("boundaries", "rewards", "sampled", "sample_Z", "agent_cause",
            "team_cause", "team_skills", "agent_skills", "log_probs", "dones")
    record = {key: [] for key in keys}

    for t in range(steps):
        actions, _infos, step_data = agent.step(
            states, observations, env_steps, dones_tracker,
            deterministic=False, return_step_data=True, build_infos=False,
        )
        record["boundaries"].append(np.asarray(step_data["skill_changed"], dtype=bool).copy())
        record["team_skills"].append(np.asarray(step_data["team_skills"], dtype=np.int64).copy())
        record["agent_skills"].append(np.asarray(step_data["agent_skills"], dtype=np.int64).copy())
        record["log_probs"].append(
            np.asarray(
                [
                    [float(lp.get("team_log_prob", 0.0))] + list(lp.get("agent_log_probs", []))
                    for lp in step_data["log_probs"]
                ],
                dtype=np.float64,
            )
        )
        if mode == "d2":
            record["sampled"].append(step_data["d2_sampled_mask"].copy())
            record["sample_Z"].append(step_data["d2_sample_Z"].copy())
            record["agent_cause"].append(step_data["d2_agent_cause"].copy())
            record["team_cause"].append(step_data["d2_team_cause"].copy())

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
        record["rewards"].append(rewards.copy())
        record["dones"].append(dones.copy())

        if store:
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

    if do_update:
        last_values = np.zeros((NUM_ENVS, config.n_agents), dtype=np.float32)
        agent.update(
            steps_in_buffer=steps,
            last_values=last_values,
            dones=dones_tracker.copy(),
            last_state=states.copy(),
            last_observations=observations.copy(),
        )
    elif mode == "d2" and store:
        agent._d2_flush_open_segments(steps)

    for key in keys:
        if record[key]:
            record[key] = np.array(record[key])
    return agent, record


def _scripted_gap_patch(agent_rule, team_rule=None, gap=10.0):
    """
    Build a replacement for `evaluate_held_batch` with scripted gaps.

    `agent_rule(call_index, batch_index, agent_index) -> bool` selects the agents
    whose held skill is not the argmax (gap = `gap`); every other position has
    gap 0.  `team_rule(call_index, batch_index) -> bool` does the same for Z.
    The call index counts calls, i.e. rollout steps at which a gap pass runs.
    """

    def _factory(coordinator):
        real = coordinator.evaluate_held_batch
        state = {"calls": 0}

        def _patched(state_tensor, observations, held_Z, held_z):
            out = real(state_tensor, observations, held_Z, held_z)
            batch = state_tensor.shape[0]
            n_agents = observations.shape[1]
            Z_logits = torch.zeros_like(out["Z_logits"])
            z_logits = torch.zeros_like(out["z_logits"])
            for b in range(batch):
                if team_rule is not None and team_rule(state["calls"], b):
                    other = (int(held_Z[b]) + 1) % Z_logits.shape[-1]
                    Z_logits[b, other] = gap
                for i in range(n_agents):
                    if agent_rule(state["calls"], b, i):
                        other = (int(held_z[b, i]) + 1) % z_logits.shape[-1]
                        z_logits[b, i, other] = gap
            state["calls"] += 1
            return {
                "Z_logits": Z_logits,
                "z_logits": z_logits,
                "state_values": out["state_values"],
                "agent_values": out["agent_values"],
            }

        return _patched

    return _factory


def _hand_built_d2_buffer(num_steps, num_envs, n_agents):
    """A bare d2 RolloutBuffer with the low-level masks marked written."""
    buffer = RolloutBuffer(
        num_steps=num_steps,
        num_envs=num_envs,
        n_agents=n_agents,
        obs_dim=4,
        action_dim=2,
        gru_hidden_size=8,
        n_Z=6,
        n_z=6,
        state_dim=5,
        d2_enabled=True,
    )
    buffer.masks[:, :] = True
    buffer.env_lengths[:] = num_steps
    buffer.last_t_per_env[:] = num_steps - 1
    return buffer


# ---------------------------------------------------------------------------
# The nine tests (plan section 10; ADR 01 invariants 1-8 and review III.1).
# ---------------------------------------------------------------------------


def test_1_off_mode_matches_phase0_fingerprint(tmp_path):
    """Invariant 1: `off` on the phase 0 seed reproduces the phase 0 fingerprint exactly."""

    generated = _generate_fingerprint(log_dir=tmp_path / "agent_logs")
    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    generated_digest = hashlib.sha256(_canonical_json(generated)).hexdigest()
    expected_digest = hashlib.sha256(_canonical_json(expected)).hexdigest()
    assert generated_digest == expected_digest, (
        "off-mode fingerprint drifted from the phase 0 baseline: "
        f"expected sha256 {expected_digest}, got {generated_digest}"
    )
    assert generated == expected


def test_1b_off_mode_allocates_no_d2_state(tmp_path):
    """Invariant 1: nothing D2 is allocated in `off`."""

    agent, _record = _run_rollout("off", tmp_path / "logs", steps=2, store=False)
    assert agent.d2_enabled is False
    assert agent.rollout_buffer.d2_enabled is False
    assert agent.d2_metrics is None
    assert agent.d2_coordinator_theta0 is None
    for name in ("d2_agent_valid", "d2_team_valid", "d2_sampled_mask", "d2_order",
                 "d2_agent_reward", "d2_team_reward"):
        assert not hasattr(agent.rollout_buffer, name), f"`off` allocated {name}"
    assert agent.rollout_buffer.get_d2_tables() is None
    assert agent.env_team_ages == {}
    assert agent.env_d2_last_decision == {}
    assert agent.team_discriminator.age_input_dim == 0
    assert agent.individual_discriminator.age_input_dim == 0


def test_2_d0_matches_off_boundaries_and_target_scale(tmp_path):
    """
    Invariant 2 (+ review III.1.2, III.1 P4).

    D0 is `d2` with `c = c_Z = inf` and `k_max = k_Z = k`.  The episode is half
    the rollout, so one reset happens mid-rollout and the reset alignment is
    exercised rather than assumed.  The target-scale ratio is checked on a
    hand-built constant-reward episode.
    """

    episode_length = ROLLOUT_LENGTH // 2  # one mid-rollout reset at t = 20
    _off_agent, off_record = _run_rollout(
        "off", tmp_path / "off", episode_length=episode_length, store=False
    )
    d0_agent, d0_record = _run_rollout(
        "d2", tmp_path / "d0", episode_length=episode_length, store=False,
        interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=10, team_cap_k_Z=10,
    )

    assert off_record["dones"].any(axis=0).all(), "the test needs a mid-rollout reset"
    reset_steps = np.flatnonzero(off_record["dones"][:, 0])
    assert reset_steps[0] < ROLLOUT_LENGTH - 1, "the reset must be mid-rollout"

    np.testing.assert_array_equal(
        off_record["boundaries"], d0_record["boundaries"],
        "D0 and `off` disagree on the boundary mask",
    )
    # A team decision is a boundary for every agent, so the agent boundary mask
    # is the team boundary mask broadcast over agents at D0.
    np.testing.assert_array_equal(
        d0_record["sampled"],
        np.repeat(d0_record["boundaries"][:, :, None], N_UAVS, axis=2),
    )
    np.testing.assert_array_equal(d0_record["sample_Z"], d0_record["boundaries"])

    # Target scale on a constant-reward episode: `off` stores the undiscounted
    # segment sum, `d2` the discounted one, so off / d2 = tau (1 - g) / (1 - g^tau).
    gamma, tau, reward = 0.99, 10, 1.0
    n_segments = ROLLOUT_LENGTH // tau
    d2_buffer = _hand_built_d2_buffer(ROLLOUT_LENGTH, 1, 2)
    off_buffer = RolloutBuffer(
        num_steps=ROLLOUT_LENGTH, num_envs=1, n_agents=2, obs_dim=4, action_dim=2,
        gru_hidden_size=8, n_Z=6, n_z=6, state_dim=5,
    )
    off_buffer.masks[:, :] = True
    off_buffer.env_lengths[:] = ROLLOUT_LENGTH
    off_buffer.last_t_per_env[:] = ROLLOUT_LENGTH - 1
    discounted = sum(gamma ** u * reward for u in range(tau))
    for seg in range(n_segments):
        start = seg * tau
        d2_buffer.close_d2_team_segment(0, start, discounted, tau, False)
        for agent_idx in range(2):
            d2_buffer.close_d2_agent_segment(0, agent_idx, start, discounted, tau, False)
        off_buffer.add_high_level_data(
            env_idx=0, time_step=start, state_value=0.0,
            agent_values=np.zeros(2, dtype=np.float32), team_log_prob=0.0,
            agent_log_probs=np.zeros(2, dtype=np.float32),
            accumulated_reward=tau * reward, elapsed_steps=tau, terminal=False,
            close_reason_code=1,
        )
    last = {"state": np.zeros(1), "agents": np.zeros((1, 2))}
    d2_buffer.compute_high_level_advantages(last, gamma=gamma, gae_lambda=0.95, value_normalizer=None)
    off_buffer.compute_high_level_advantages(last, gamma=gamma, gae_lambda=0.95, value_normalizer=None)

    rows = np.arange(0, ROLLOUT_LENGTH, tau)
    # The final row bootstraps with zero, so its return is the segment target
    # alone and isolates the undiscounted-to-discounted factor exactly.
    d2_last = float(d2_buffer.high_level_team_returns[rows[-1], 0])
    off_last = float(off_buffer.high_level_team_returns[rows[-1], 0])
    ratio_off_over_d2 = off_last / d2_last
    theory = tau * (1.0 - gamma) / (1.0 - gamma ** tau)
    assert abs(ratio_off_over_d2 - theory) < 5e-4, (
        f"target-scale ratio off/d2 = {ratio_off_over_d2:.6f}, expected {theory:.6f}"
    )
    assert abs(theory - 1.0458) < 1e-3
    assert abs((d2_last / off_last) - 1.0 / theory) < 5e-4


def test_3_infinite_costs_permit_no_pre_cap_switch(tmp_path):
    """Invariant 3: `c = c_Z = inf`, `k_max = 7`, `k_Z = 40`."""

    agent, record = _run_rollout(
        "d2", tmp_path / "logs", store=False,
        interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=7, team_cap_k_Z=40,
    )
    causes = agent.get_d2_metrics()["cause_counts"]
    assert causes["gap"] == 0, "an infinite c produced a `gap` boundary"
    assert causes["team_gap"] == 0, "an infinite c_Z produced a `team_gap` boundary"

    # Every agent boundary is at age 7 (or the reset at the start of the episode).
    for env_idx in range(NUM_ENVS):
        agent_boundaries = np.flatnonzero(record["sampled"][:, env_idx, 0])
        assert agent_boundaries.tolist() == [0, 7, 14, 21, 28, 35], agent_boundaries.tolist()
        for other in range(1, N_UAVS):
            np.testing.assert_array_equal(
                record["sampled"][:, env_idx, 0], record["sampled"][:, env_idx, other]
            )
        # The team is re-decided only at reset: k_Z = 40 is never reached inside
        # a 40-step episode whose ages restart at 0.
        team_boundaries = np.flatnonzero(record["sample_Z"][:, env_idx])
        assert team_boundaries.tolist() == [0], team_boundaries.tolist()
        assert record["team_cause"][0, env_idx] == HMASDAgent.D2_CAUSE_RESET
        assert set(record["agent_cause"][7, env_idx].tolist()) == {HMASDAgent.D2_CAUSE_CAP}


def test_4_zero_cost_samples_every_live_agent(tmp_path):
    """Invariant 4: at `c = c_Z = 0`, `delta = 1`, every live agent is sampled every step."""

    agent, record = _run_rollout(
        "d2", tmp_path / "logs", store=False,
        interruption_cost_c=0.0, interruption_cost_c_Z=0.0,
        skill_cap_k_max=10, team_cap_k_Z=10,
    )
    assert record["sampled"].all(), "some agent was not sampled at c = 0"
    assert record["sample_Z"].all(), "the team was not re-decided at c_Z = 0"
    metrics = agent.get_d2_metrics()
    assert metrics["mean_S_t"] == float(N_UAVS)
    assert metrics["S_t_fraction"] == 1.0


def test_5_segment_lengths_partition_live_steps(tmp_path):
    """Invariant 5 with a scripted `S_t`: closed or bootstrapped lengths partition live steps."""

    # Agent i is interrupted whenever (call index + i) % 3 == 0; the team never
    # fires by gap (c_Z stays infinite) and never by cap inside the episode.
    patch = _scripted_gap_patch(
        agent_rule=lambda call, env_idx, agent_idx: ((call + agent_idx + env_idx) % 3) == 0
    )
    agent, record = _run_rollout(
        "d2", tmp_path / "logs", store=True, patch_held=patch,
        interruption_cost_c=1.0, interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=40, team_cap_k_Z=40,
    )
    tables = agent.rollout_buffer.get_d2_tables(ROLLOUT_LENGTH)
    # The scripted gaps really did produce a non-trivial, non-uniform S_t.
    sizes = record["sampled"].sum(axis=2)
    assert sizes.min() < N_UAVS and sizes.max() >= 1

    for env_idx in range(NUM_ENVS):
        for agent_idx in range(N_UAVS):
            valid = tables["agent_valid"][:, env_idx, agent_idx]
            total = int(tables["agent_elapsed"][:, env_idx, agent_idx][valid].sum())
            assert total == ROLLOUT_LENGTH, (
                f"env {env_idx} agent {agent_idx}: segment lengths sum to {total}, "
                f"expected {ROLLOUT_LENGTH} live steps"
            )
        team_valid = tables["team_valid"][:, env_idx]
        team_total = int(tables["team_elapsed"][:, env_idx][team_valid].sum())
        assert team_total == ROLLOUT_LENGTH


def test_6_ordered_replay_covers_sampled_positions_only(tmp_path):
    """Invariant 6: a non-contiguous `S_t` replays exactly, with zeros at forced positions."""

    torch.set_num_threads(1)
    torch.manual_seed(BASE_SEED)
    config = _make_config("d2", state_dim=12, obs_dim=7,
                          interruption_cost_c=float("inf"),
                          interruption_cost_c_Z=float("inf"),
                          skill_cap_k_max=10, team_cap_k_Z=10)
    coordinator = SkillCoordinator(config)
    coordinator.eval()

    batch, n_agents = 2, config.n_agents
    state = torch.randn(batch, config.state_dim)
    observations = torch.randn(batch, n_agents, config.obs_dim)
    held_Z = torch.randint(0, config.n_Z, (batch,))
    held_z = torch.randint(0, config.n_z, (batch, n_agents))
    # Non-contiguous S_t: agents 0 and 2 are re-decided, agent 1 is kept.
    sampled_mask = torch.tensor([[True, False, True], [False, True, False]])
    sample_Z_mask = torch.tensor([True, False])

    torch.manual_seed(7)
    with torch.no_grad():
        assignment = coordinator.assign_partial_batch(
            state, observations, held_Z, held_z, sample_Z_mask, sampled_mask
        )
    order = assignment["order"]
    # O_t is kept agents in canonical order, then S_t in canonical order.
    assert order[0].tolist() == [1, 0, 2]
    assert order[1].tolist() == [0, 2, 1]

    # Forced positions keep the held skill and carry a zero log-probability.
    assert int(assignment["agent_skills"][0, 1]) == int(held_z[0, 1])
    assert int(assignment["team_skills"][1]) == int(held_Z[1])
    assert float(assignment["agent_log_probs"][0, 1]) == 0.0
    assert float(assignment["team_log_probs"][1]) == 0.0

    with torch.no_grad():
        replay = coordinator.evaluate_training_batch_ordered(
            state, observations, assignment["team_skills"], assignment["agent_skills"],
            order, sampled_mask, sample_Z_mask,
        )
    torch.testing.assert_close(
        replay["agent_log_probs"], assignment["agent_log_probs"], rtol=0, atol=1e-6
    )
    torch.testing.assert_close(
        replay["team_log_probs"], assignment["team_log_probs"], rtol=0, atol=1e-6
    )
    forced = ~sampled_mask
    assert torch.all(replay["agent_log_probs"][forced] == 0.0)
    assert torch.all(replay["agent_entropies"][forced] == 0.0)
    assert torch.all(replay["agent_entropies"][sampled_mask] > 0.0)
    assert float(replay["team_log_probs"][1]) == 0.0
    assert float(replay["team_entropy"][1]) == 0.0
    assert float(replay["team_entropy"][0]) > 0.0

    # The joint log-probability is the sum over sampled positions only.
    joint = float(replay["team_log_probs"].sum() + replay["agent_log_probs"].sum())
    expected = float(
        replay["team_log_probs"][sample_Z_mask].sum()
        + replay["agent_log_probs"][sampled_mask].sum()
    )
    # The two sums are the same terms in a different float32 reduction order, so
    # the tolerance is float32 round-off, not an algorithmic allowance.
    assert abs(joint - expected) < 1e-6


def test_7_team_decision_closes_every_agent_segment(tmp_path):
    """Invariant 7: a forced team decision at a chosen step closes every agent segment."""

    forced_step = 13
    patch = _scripted_gap_patch(
        agent_rule=lambda call, env_idx, agent_idx: False,
        team_rule=lambda call, env_idx: call == forced_step - 1,
    )
    agent, record = _run_rollout(
        "d2", tmp_path / "logs", store=True, patch_held=patch,
        interruption_cost_c=float("inf"), interruption_cost_c_Z=1.0,
        skill_cap_k_max=40, team_cap_k_Z=40,
    )
    # The gap pass runs on every non-reset step, so call index t - 1 is step t.
    assert record["sample_Z"][forced_step].all(), "the scripted team decision did not fire"
    assert record["team_cause"][forced_step].tolist() == \
        [HMASDAgent.D2_CAUSE_TEAM_GAP] * NUM_ENVS
    assert record["sampled"][forced_step].all(), "a team decision did not force every agent"
    assert not record["sample_Z"][1:forced_step].any()

    tables = agent.rollout_buffer.get_d2_tables(ROLLOUT_LENGTH)
    for env_idx in range(NUM_ENVS):
        for agent_idx in range(N_UAVS):
            # The segment opened at the reset (t = 0) closes at t = 13 with
            # elapsed 13, and a new segment starts at 13.
            assert tables["agent_valid"][0, env_idx, agent_idx]
            assert int(tables["agent_elapsed"][0, env_idx, agent_idx]) == forced_step
            assert tables["sampled_mask"][forced_step, env_idx, agent_idx]
        assert tables["team_valid"][0, env_idx]
        assert int(tables["team_elapsed"][0, env_idx]) == forced_step


def test_8_shapes_targets_and_normalized_ages(tmp_path):
    """Invariant 8: table shapes, the ADR target formula, and the normalized ages."""

    gamma = 0.99
    rewards = [0.5, -0.25, 2.0]
    tau = len(rewards)
    discounted = sum(gamma ** u * r for u, r in enumerate(rewards))
    n_agents, num_envs, num_steps = 3, 2, 8
    buffer = _hand_built_d2_buffer(num_steps, num_envs, n_agents)

    assert buffer.d2_agent_valid.shape == (num_steps, num_envs, n_agents)
    assert buffer.d2_agent_reward.shape == (num_steps, num_envs, n_agents)
    assert buffer.d2_agent_elapsed.shape == (num_steps, num_envs, n_agents)
    assert buffer.d2_agent_terminal.shape == (num_steps, num_envs, n_agents)
    assert buffer.d2_team_valid.shape == (num_steps, num_envs)
    assert buffer.d2_team_reward.shape == (num_steps, num_envs)
    assert buffer.d2_team_elapsed.shape == (num_steps, num_envs)
    assert buffer.d2_team_terminal.shape == (num_steps, num_envs)

    bootstrap_value = 3.0
    segment_value = 1.25
    # env 0: one non-terminal segment (bootstrapped); env 1: one terminal segment.
    for env_idx, terminal in ((0, False), (1, True)):
        buffer.d2_team_value[0, env_idx] = segment_value
        buffer.d2_agent_values[0, env_idx, :] = segment_value
        buffer.close_d2_team_segment(env_idx, 0, discounted, tau, terminal)
        for agent_idx in range(n_agents):
            buffer.close_d2_agent_segment(env_idx, agent_idx, 0, discounted, tau, terminal)

    last = {
        "state": np.full(num_envs, bootstrap_value),
        "agents": np.full((num_envs, n_agents), bootstrap_value),
    }
    buffer.compute_high_level_advantages(last, gamma=gamma, gae_lambda=0.95, value_normalizer=None)

    expected_bootstrapped = discounted + (gamma ** tau) * bootstrap_value
    expected_terminal = discounted
    assert abs(float(buffer.high_level_team_returns[0, 0]) - expected_bootstrapped) < 1e-5
    assert abs(float(buffer.high_level_team_returns[0, 1]) - expected_terminal) < 1e-5
    for agent_idx in range(n_agents):
        assert abs(
            float(buffer.high_level_agent_returns[0, 0, agent_idx]) - expected_bootstrapped
        ) < 1e-5
        assert abs(
            float(buffer.high_level_agent_returns[0, 1, agent_idx]) - expected_terminal
        ) < 1e-5
    # advantage = target - V(segment start)
    assert abs(
        float(buffer.high_level_team_advantages[0, 0]) - (expected_bootstrapped - segment_value)
    ) < 1e-5

    # Normalized ages: a_i / k_max and a_Z / k_Z at the step of collection.
    k_max, k_Z = 10, 40
    agent, _record = _run_rollout(
        "d2", tmp_path / "logs", store=True,
        interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=k_max, team_cap_k_Z=k_Z, age_feature="normalized",
    )
    tables = agent.rollout_buffer.get_d2_tables(ROLLOUT_LENGTH)
    assert tables["agent_age"].shape == (ROLLOUT_LENGTH, NUM_ENVS, N_UAVS)
    assert tables["team_age"].shape == (ROLLOUT_LENGTH, NUM_ENVS)
    np.testing.assert_array_equal(
        tables["agent_age"][:12, 0, 0], np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1])
    )
    np.testing.assert_array_equal(tables["team_age"][:12, 0], np.arange(12))
    np.testing.assert_allclose(
        tables["agent_age"][:12, 0, 0] / k_max,
        np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.0, 0.1]),
        rtol=0, atol=1e-9,
    )
    np.testing.assert_allclose(
        tables["team_age"][:12, 0] / k_Z, np.arange(12) / k_Z, rtol=0, atol=1e-9
    )
    np.testing.assert_allclose(
        agent._d2_normalized_agent_age(tables["agent_age"][5, 0], N_UAVS),
        tables["agent_age"][5, 0] / k_max, rtol=0, atol=1e-9,
    )
    np.testing.assert_allclose(
        agent._d2_normalized_team_age(tables["team_age"][5, 0], 1),
        np.array([tables["team_age"][5, 0] / k_Z]), rtol=0, atol=1e-9,
    )
    assert float(tables["agent_age"][:, 0, 0].max()) / k_max < 1.0
    assert float(tables["team_age"][:, 0].max()) / k_Z < 1.0
    assert agent.team_discriminator.age_input_dim == 1
    assert agent.individual_discriminator.age_input_dim == 1
    assert agent.team_discriminator.input_projection.in_features == agent.config.state_dim + 1
    assert agent.individual_discriminator.obs_input_projection.in_features == \
        agent.config.obs_dim + 1


def test_9_trigger_path_draws_no_rng(tmp_path):
    """Review III.1.3: two `d2` runs at `c = inf` with the same seed are identical."""

    params = dict(
        interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=10, team_cap_k_Z=10,
    )
    _agent_a, record_a = _run_rollout("d2", tmp_path / "run_a", store=False, **params)
    _agent_b, record_b = _run_rollout("d2", tmp_path / "run_b", store=False, **params)

    for key in ("boundaries", "sampled", "sample_Z", "team_skills", "agent_skills",
                "agent_cause", "team_cause"):
        np.testing.assert_array_equal(
            record_a[key], record_b[key], f"the d2 trigger path is not deterministic in {key}"
        )
    np.testing.assert_array_equal(record_a["log_probs"], record_b["log_probs"])
    np.testing.assert_array_equal(record_a["rewards"], record_b["rewards"])


def test_10_d2_requires_rollout_length_multiple_of_episode_length():
    """Review VII F1 (owner decision VII.5): the rollout-boundary guard."""

    with pytest.raises(ValueError) as excinfo:
        _make_config("d2", episode_length=40, rollout_length=45,
                     interruption_cost_c=float("inf"),
                     interruption_cost_c_Z=float("inf"),
                     skill_cap_k_max=10, team_cap_k_Z=10)
    message = str(excinfo.value)
    assert "45" in message and "40" in message, message

    # `off` is unaffected by the guard.
    off_config = _make_config("off", episode_length=40, rollout_length=45)
    assert off_config.rollout_length == 45
    assert off_config.episode_length == 40

    # A multiple is accepted in `d2`.
    ok_config = _make_config("d2", episode_length=20, rollout_length=40,
                             interruption_cost_c=float("inf"),
                             interruption_cost_c_Z=float("inf"),
                             skill_cap_k_max=10, team_cap_k_Z=10)
    assert ok_config.rollout_length == 40


def test_11_d2_refuses_age_feature_with_compact_discriminators():
    """Review VII F4: the compact discriminators do not accept the age feature."""

    for flag in ("use_compact_team_discriminator", "use_compact_individual_discriminator"):
        with pytest.raises(ValueError) as excinfo:
            _make_config("d2", age_feature="normalized",
                         interruption_cost_c=float("inf"),
                         interruption_cost_c_Z=float("inf"),
                         skill_cap_k_max=10, team_cap_k_Z=10,
                         **{flag: True})
        assert flag in str(excinfo.value)

    # age_feature='off' with the same flags, and 'normalized' without them, pass.
    _make_config("d2", age_feature="off", use_compact_team_discriminator=True,
                 interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
                 skill_cap_k_max=10, team_cap_k_Z=10)
    _make_config("d2", age_feature="normalized",
                 interruption_cost_c=float("inf"), interruption_cost_c_Z=float("inf"),
                 skill_cap_k_max=10, team_cap_k_Z=10)
    # `off` ignores the age feature entirely.
    _make_config("off", age_feature="normalized", use_compact_team_discriminator=True)


def test_12_stored_rows_replay_to_the_collection_log_probs(tmp_path):
    """
    Review VII F3: the buffer-level replay consistency.

    A short `d2` rollout is collected with a scripted non-uniform `S_t` (the
    same rule as test 5, so this is not the trivial all-sampled case), and the
    stored rows are replayed through the D2 sampler and
    `evaluate_training_batch_ordered` at the *collecting* parameters — no update
    runs in between.  The replayed log-probabilities must reproduce
    `d2_agent_old_log_probs` at valid agent positions and `d2_team_old_log_prob`
    at valid team rows.
    """

    patch = _scripted_gap_patch(
        agent_rule=lambda call, env_idx, agent_idx: ((call + agent_idx + env_idx) % 3) == 0
    )
    agent, record = _run_rollout(
        "d2", tmp_path / "logs", store=True, patch_held=patch,
        interruption_cost_c=1.0, interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=40, team_cap_k_Z=40,
    )
    # The scripted gaps really did produce a non-trivial S_t.
    sizes = record["sampled"].sum(axis=2)
    assert sizes.min() < N_UAVS

    # The update replays with the running normalisers as they stand at update
    # time, while collection normalised with the statistics of the moment, so an
    # exact comparison is only meaningful with the normalisers off.  The D2
    # configuration inherits `use_obsnorm = use_statenorm = False` from
    # `config_1.Config`, so the stored rows *are* the normalised rows the update
    # would use, and no separate disabling is needed.
    assert bool(getattr(agent.config, "use_obsnorm", False)) is False
    assert bool(getattr(agent.config, "use_statenorm", True)) is False

    tables = agent.rollout_buffer.get_d2_tables(ROLLOUT_LENGTH)
    assert tables["agent_valid"].any() and tables["team_valid"].any()

    sampler = agent.rollout_buffer.get_d2_coordinator_sampler(
        ROLLOUT_LENGTH, 1, 4096, device=agent.device
    )
    assert sampler is not None

    checked_team = 0
    checked_agent = 0
    for batch in sampler:
        with torch.no_grad():
            replay = agent.skill_coordinator.evaluate_training_batch_ordered(
                batch["states"],
                batch["observations"],
                batch["team_skills"],
                batch["agent_skills"],
                batch["order"],
                batch["sampled_mask"],
                batch["sample_Z"],
            )
        team_mask = batch["team_valid"].bool()
        agent_mask = batch["agent_valid"].bool()
        # `valid` implies `sampled`, so no forced position enters the comparison.
        assert torch.all(batch["sampled_mask"][agent_mask])
        assert torch.all(batch["sample_Z"][team_mask])
        torch.testing.assert_close(
            replay["team_log_probs"][team_mask],
            batch["old_team_log_probs"][team_mask],
            rtol=0, atol=1e-5,
        )
        torch.testing.assert_close(
            replay["agent_log_probs"][agent_mask],
            batch["old_agent_log_probs"][agent_mask],
            rtol=0, atol=1e-5,
        )
        checked_team += int(team_mask.sum())
        checked_agent += int(agent_mask.sum())

    assert checked_team == int(tables["team_valid"].sum())
    assert checked_agent == int(tables["agent_valid"].sum())


if __name__ == "__main__":
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE_PATH
    temp_path = REPO_ROOT / "temp" / "pytest_d2_policy_interrupt" / "fingerprint_off.json"
    generated = _generate_fingerprint(
        log_dir=REPO_ROOT / "temp" / "pytest_d2_policy_interrupt" / "fingerprint_gen"
    )
    payload = json.dumps(generated, indent=2, sort_keys=True) + "\n"
    for destination in (out_path, temp_path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload, encoding="utf-8")
    print("fingerprint sha256:", hashlib.sha256(_canonical_json(generated)).hexdigest())
    print("wrote:", out_path)
    print("wrote:", temp_path)
