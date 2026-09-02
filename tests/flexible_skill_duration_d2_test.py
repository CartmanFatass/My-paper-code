"""D2 phase 0 — baseline fingerprint for invariant 1.

Specification: `docs/Claude_docs/plans/D2_IMPLEMENTATION_PLAN_20260902.md` section 2 (phase 0),
against `docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md` (revision 3, accepted).

This file is produced strictly before any edit to `config_1.py`, `hmasd/networks.py`,
`hmasd/agent.py`, or `hmasd/utils.py`. The fingerprint it records is the only reference
invariant 1 ("`off` is byte-identical to current HMASD on the same seed") has; it must be
regenerated from a clean baseline if it is ever taken after a D2 edit.

The driver mirrors the batched base-route loop of `train_multiproc_config_1.py:4567-5036`
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
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config_1 import Config  # noqa: E402
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter  # noqa: E402
from envs.pettingzoo.scenario1 import UAVBaseStationEnv  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

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
