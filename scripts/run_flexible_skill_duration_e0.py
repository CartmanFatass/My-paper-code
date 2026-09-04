"""E0 runner - exposure line and frozen probe set on UAV scenario 1 (`off` versus D0).

Launch contract: `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_20260902.md`.
Claim ceiling B (EXPLORE): integrity and exposure only.  Nothing this script writes is a
performance comparison between the arms.

The rollout loop is the batched base-route loop that
`tests/flexible_skill_duration_d2_test.py::_run_rollout` and the Phase 0 fingerprint driver
mirror from `train_multiproc_config_1.py:4567-5036`:

    agent.step(build_infos=False) -> env step with terminal-state storage semantics
    -> store_transition_batch -> per-env reset bookkeeping -> discoverer bootstrap
    -> agent.update -> clear_buffers

Nothing under `hmasd/`, `config_1.py`, `envs/` or `tests/` is modified.  The optimizer step
counters are installed by replacing the bound `step` of the agent's own optimizer *instances*,
which leaves the imported modules untouched.

Usage (explicit interpreter, per CLAUDE.md):

    # use the hmasd-amd-cpu interpreter
    python scripts/run_flexible_skill_duration_e0.py \
        --arm off --seed 1 --rollouts 10 --num-envs 32 \
        --output-root temp/directions/flexible_skill_duration/exp/E0_20260902
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import math
import os
import platform
import random
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
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


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _jsonable(value):
    """Make a value JSON-writable without changing its meaning (inf -> string)."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if math.isnan(value):
            return "NaN"
        return value
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, (str, bool, int)) or value is None:
        return value
    return str(value)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_arrays(arrays: dict) -> str:
    """Container-independent digest over named arrays (zip timestamps excluded)."""
    digest = hashlib.sha256()
    for key in sorted(arrays):
        array = np.ascontiguousarray(arrays[key])
        digest.update(key.encode("utf-8"))
        digest.update(str(array.dtype).encode("utf-8"))
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL
        ).decode("utf-8", "replace").strip()
    except Exception:  # pragma: no cover - diagnostic only
        return ""


@contextlib.contextmanager
def _preserve_rng():
    """Keep the learner's RNG streams independent of evaluation and of agent construction."""
    py_state = random.getstate()
    np_state = np.random.get_state()
    torch_state = torch.get_rng_state()
    try:
        yield
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)
        torch.set_rng_state(torch_state)


class _StepCounter:
    """Counts calls to an optimizer's bound `step`, leaving the optimizer's behaviour intact."""

    def __init__(self, optimizer):
        self.count = 0
        self._inner = optimizer.step
        optimizer.step = self  # instance attribute only; the class is untouched

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self._inner(*args, **kwargs)


# ---------------------------------------------------------------------------
# exposure line
# ---------------------------------------------------------------------------


def _parameter_groups(agent):
    """The five parameter groups the contract's exposure line covers."""
    groups = {
        "coordinator": list(agent.skill_coordinator.parameters()),
        "discoverer_actor": list(agent.skill_discoverer.actor_update_parameters()),
        "discoverer_critic": list(agent.skill_discoverer.critic_update_parameters()),
        "team_discriminator": (
            list(agent.team_discriminator.parameters())
            if agent.team_discriminator is not None else []
        ),
        "individual_discriminator": (
            list(agent.individual_discriminator.parameters())
            if agent.individual_discriminator is not None else []
        ),
    }
    return groups


def _capture_theta0(agent):
    """float64 copies of every covered parameter, taken at construction."""
    theta0 = {}
    for name, params in _parameter_groups(agent).items():
        theta0[name] = {
            "params": [p.detach().double().clone() for p in params],
            "norm": (
                float(torch.sqrt(sum((p.detach().double() ** 2).sum()
                                     for p in params)).item()) if params else 0.0
            ),
        }
    return theta0


def _exposure_line(agent, theta0):
    """||theta - theta_0|| / ||theta_0||, computed in float64, per covered network."""
    out = {}
    with torch.no_grad():
        for name, params in _parameter_groups(agent).items():
            reference = theta0[name]
            if not params or reference["norm"] <= 0.0:
                out[name] = None
                continue
            displacement = torch.sqrt(
                sum(((p.detach().double() - p0) ** 2).sum()
                    for p, p0 in zip(params, reference["params"]))
            ).item()
            out[name] = float(displacement) / reference["norm"]
    return out


# ---------------------------------------------------------------------------
# configuration and environments
# ---------------------------------------------------------------------------


CONFIG_DUMP_FIELDS = (
    "n_agents", "n_uavs", "n_users", "num_envs", "rollout_length", "episode_length",
    "k", "n_Z", "n_z", "state_dim", "obs_dim", "action_dim", "action_space_type",
    "gamma", "gae_lambda", "ppo_epochs", "num_mini_batch", "lambda_e", "lambda_D",
    "lambda_d", "lambda_h", "lambda_l", "lr_coordinator", "lr_discoverer_actor",
    "lr_discoverer_critic", "lr_discriminator", "weight_decay", "clip_param",
    "value_loss_coef", "max_grad_norm", "hidden_size", "embedding_dim", "n_heads",
    "gru_hidden_size", "use_valuenorm", "use_obsnorm", "use_statenorm",
    "coordinator_batch_size", "high_level_batch_size", "high_level_buffer_size",
    "buffer_size", "batch_size", "total_timesteps", "seed",
    "policy_interruption_mode", "interruption_delta", "interruption_cost_c",
    "interruption_cost_c_Z", "skill_cap_k_max", "team_cap_k_Z", "age_feature",
    "use_horizon_window", "use_process_exploration", "strict_hmasd_alignment",
    "use_compact_team_discriminator", "use_compact_individual_discriminator",
)

LOSS_FIELDS = (
    "coordinator_loss", "coordinator_policy_loss", "coordinator_value_loss",
    "discoverer_loss", "discoverer_policy_loss", "discoverer_value_loss",
    "discriminator_loss", "team_skill_entropy", "agent_skill_entropy",
    "action_entropy", "mean_high_level_reward", "avg_intrinsic_reward",
    "discriminator_team_accuracy", "discriminator_individual_accuracy",
)


class E0Config(Config):
    """Module-level subclass so `agent.save_model` can pickle the config into the checkpoint."""


def _make_config(arm, seed, num_envs, rollout_length, episode_length, n_uavs, n_users,
                 rollouts, state_dim, obs_dim):
    config = E0Config()
    config.n_uavs = n_uavs
    config.n_users = n_users
    config.num_envs = num_envs
    config.rollout_length = rollout_length
    config.episode_length = episode_length
    config.k = 10
    config.seed = seed
    # `total_timesteps` is replaced by the rollout count R (contract section 2).
    config.total_timesteps = num_envs * rollout_length * rollouts
    if arm == "off":
        config.policy_interruption_mode = "off"
    else:  # D0 = `d2` with infinite costs and both caps tied to k
        config.policy_interruption_mode = "d2"
        config.interruption_delta = 1
        config.interruption_cost_c = float("inf")
        config.interruption_cost_c_Z = float("inf")
        config.skill_cap_k_max = 10
        config.team_cap_k_Z = 10
        config.age_feature = "off"
    config.update_env_dims(state_dim=state_dim, obs_dim=obs_dim, n_agents=n_uavs)
    return config


def _make_envs(count, base_seed, n_uavs, n_users, episode_length):
    envs = []
    for rank in range(count):
        raw_env = UAVBaseStationEnv(
            n_uavs=n_uavs,
            n_users=n_users,
            max_steps=episode_length,
            user_distribution="uniform",
            channel_model="free_space",
            seed=base_seed + rank,
        )
        envs.append(ParallelToArrayAdapter(raw_env, seed=base_seed + rank))
    return envs


def _reset_all(envs):
    observations, states = [], []
    for env in envs:
        obs, info = env.reset()
        observations.append(np.asarray(obs, dtype=np.float32))
        states.append(np.asarray(info["state"], dtype=np.float64))
    return np.stack(states), np.stack(observations)


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------


class Evaluator:
    """Deterministic evaluation on its own lanes and its own agent instance.

    A separate `HMASDAgent` is used because `agent.step` keeps per-environment state keyed by
    lane index: evaluating on the learner would overwrite the training lanes' skills, timers and
    hidden states.  Weights and the running observation/state normalisers are copied from the
    learner before each evaluation, and the evaluation agent is held in eval mode so it never
    updates those normalisers.  Construction and every evaluation run inside `_preserve_rng`, so
    the learner's trajectory does not depend on the evaluation schedule.
    """

    def __init__(self, arm, seed, lanes, n_uavs, n_users, episode_length, rollouts,
                 log_dir, eval_seed_base):
        self.lanes = lanes
        self.episode_length = episode_length
        self.eval_seed_base = eval_seed_base
        self.envs = _make_envs(lanes, eval_seed_base, n_uavs, n_users, episode_length)
        self.config = _make_config(
            arm, seed, lanes, episode_length, episode_length, n_uavs, n_users, rollouts,
            int(self.envs[0].state_dim), int(self.envs[0].obs_dim),
        )
        self.agent = HMASDAgent(self.config, log_dir=str(log_dir), device=torch.device("cpu"))
        self.agent.train(False)
        self.count = 0

    def _sync(self, learner):
        self.agent.skill_coordinator.load_state_dict(learner.skill_coordinator.state_dict())
        self.agent.skill_discoverer.load_state_dict(learner.skill_discoverer.state_dict())
        if learner.team_discriminator is not None and self.agent.team_discriminator is not None:
            self.agent.team_discriminator.load_state_dict(
                learner.team_discriminator.state_dict())
        if (learner.individual_discriminator is not None
                and self.agent.individual_discriminator is not None):
            self.agent.individual_discriminator.load_state_dict(
                learner.individual_discriminator.state_dict())
        self.agent.obs_norm = copy.deepcopy(learner.obs_norm)
        self.agent.state_norm = copy.deepcopy(learner.state_norm)
        self.agent.value_norm_coordinator = copy.deepcopy(learner.value_norm_coordinator)
        self.agent.value_norm_discoverer = copy.deepcopy(learner.value_norm_discoverer)
        self.agent.train(False)
        for lane in range(self.lanes):
            self.agent.reset_env_state(lane)

    def run(self, learner):
        self._sync(learner)
        states, observations = _reset_all(self.envs)
        env_steps = np.zeros(self.lanes, dtype=int)
        dones_tracker = np.zeros(self.lanes, dtype=bool)
        returns = np.zeros(self.lanes, dtype=np.float64)
        finished = np.zeros(self.lanes, dtype=bool)
        started = time.perf_counter()
        for _t in range(self.episode_length):
            actions, _infos, _step_data = self.agent.step(
                states, observations, env_steps, dones_tracker,
                deterministic=True, return_step_data=True, build_infos=False,
            )
            next_states_list, next_observations_list = [], []
            dones = np.zeros(self.lanes, dtype=bool)
            for lane, env in enumerate(self.envs):
                next_obs, reward, terminated, truncated, info = env.step(actions[lane])
                next_observations_list.append(np.asarray(next_obs, dtype=np.float32))
                next_states_list.append(np.asarray(info["next_state"], dtype=np.float64))
                if not finished[lane]:
                    returns[lane] += float(reward)
                dones[lane] = bool(terminated or truncated)
            states = np.stack(next_states_list)
            observations = np.stack(next_observations_list)
            for lane, env in enumerate(self.envs):
                if dones[lane]:
                    finished[lane] = True
                    dones_tracker[lane] = True
                    env_steps[lane] = 0
                    self.agent.reset_env_state(lane)
                    reset_obs, _reset_info = env.reset()
                    observations[lane] = np.asarray(reset_obs, dtype=np.float32)
                else:
                    env_steps[lane] += 1
            dones_tracker = dones.copy()
            if finished.all():
                break
        if not finished.all():
            raise RuntimeError(
                f"evaluation lane(s) {np.flatnonzero(~finished).tolist()} did not finish an "
                f"episode within {self.episode_length} steps"
            )
        self.count += 1
        return {
            "evaluation_index": self.count,
            "episodes": int(self.lanes),
            "return_mean": float(np.mean(returns)),
            "return_std": float(np.std(returns)),
            "returns": [float(v) for v in returns],
            "lane_seeds": [self.eval_seed_base + rank for rank in range(self.lanes)],
            "wall_seconds": float(time.perf_counter() - started),
        }


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------


def run_preflight(run_dir: Path) -> dict:
    """Mandatory resource preflight, before any RNG master, model, optimizer or result."""
    receipt = run_dir / "preflight.json"
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "hmasd_resource_preflight.py"),
        "admit-memory",
        "--out", str(receipt),
    ]
    completed = subprocess.run(command, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if not receipt.exists():
        raise RuntimeError(
            "resource preflight wrote no receipt; the arm is refused.\n"
            f"command: {command}\nstdout: {completed.stdout}\nstderr: {completed.stderr}"
        )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    admitted = bool(payload.get("passed", payload.get("admitted", False)))
    if completed.returncode != 0 or not admitted:
        raise RuntimeError(
            f"resource preflight refused the arm (returncode={completed.returncode}, "
            f"receipt={payload})"
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="E0 exposure-line and probe-set runner")
    parser.add_argument("--arm", choices=("off", "d0"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--rollouts", type=int, required=True)
    parser.add_argument("--num-envs", type=int, default=32)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--threads", type=int, default=1,
                        help="torch.set_num_threads (contract section 4 step 1)")
    parser.add_argument("--n-uavs", type=int, default=6)
    parser.add_argument("--n-users", type=int, default=50)
    parser.add_argument("--episode-length", type=int, default=500)
    parser.add_argument("--rollout-length", type=int, default=500)
    parser.add_argument("--eval-interval", type=int, default=5)
    parser.add_argument("--eval-lanes", type=int, default=8)
    parser.add_argument("--eval-seed-base", type=int, default=10_000)
    parser.add_argument("--probe-seed", type=int, default=20_260_902)
    parser.add_argument("--probes-per-rollout", type=int, default=512)
    parser.add_argument("--probe-out", default=None,
                        help="npz path for the `off` arm probe set (default: not written)")
    parser.add_argument("--probe-json-out", default=None,
                        help="path of the 32-probe JSON sample for the `off` arm")
    parser.add_argument("--probe-json-count", type=int, default=32)
    parser.add_argument("--reference-dir", default=None,
                        help="`off` run directory whose rollout-1 artifacts this arm compares "
                             "against (contract section 3)")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--timing-only", action="store_true",
                        help="timing run (contract section 4 step 1): no evaluation, no probe "
                             "set, no checkpoint; NOT EVIDENCE")
    args = parser.parse_args()

    run_name = args.run_name or f"{args.arm}_seed{args.seed}"
    run_dir = Path(args.output_root).resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        return _execute(args, run_dir)
    except BaseException:  # noqa: BLE001 - every failure quarantines the arm
        text = traceback.format_exc()
        (run_dir / "QUARANTINED").write_text(
            "This arm is an incomplete attempt (contract section 4 stop rule).\n"
            "It yields no observation. No resume, no salvage.\n\n"
            f"time: {_utc_now()}\n\n{text}",
            encoding="utf-8",
        )
        sys.stderr.write(text)
        return 2


def _execute(args, run_dir: Path) -> int:
    # 1. resource preflight, before any RNG master, model, optimizer or result exists
    preflight = run_preflight(run_dir)

    torch.set_num_threads(int(args.threads))
    started_wall = time.perf_counter()
    started_at = _utc_now()

    # 2. RNG masters
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    probe_rng = np.random.default_rng(args.probe_seed)

    num_envs = int(args.num_envs)
    rollout_length = int(args.rollout_length)
    episode_length = int(args.episode_length)
    rollouts = int(args.rollouts)

    # 3. environments: `num_envs` lanes with seeds `seed + rank`
    envs = _make_envs(num_envs, args.seed, args.n_uavs, args.n_users, episode_length)
    states, observations = _reset_all(envs)

    config = _make_config(
        args.arm, args.seed, num_envs, rollout_length, episode_length,
        args.n_uavs, args.n_users, rollouts,
        int(envs[0].state_dim), int(envs[0].obs_dim),
    )

    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))
    theta0 = _capture_theta0(agent)

    counters = {
        "coordinator": _StepCounter(agent.coordinator_optimizer),
        "discoverer_actor": _StepCounter(agent.discoverer_actor_optimizer),
        "discoverer_critic": _StepCounter(agent.discoverer_critic_optimizer),
    }
    if agent.team_discriminator_optimizer is not None:
        counters["team_discriminator"] = _StepCounter(agent.team_discriminator_optimizer)
    if agent.individual_discriminator_optimizer is not None:
        counters["individual_discriminator"] = _StepCounter(
            agent.individual_discriminator_optimizer)

    evaluator = None
    if not args.timing_only:
        with _preserve_rng():
            evaluator = Evaluator(
                args.arm, args.seed, int(args.eval_lanes), args.n_uavs, args.n_users,
                episode_length, rollouts, run_dir / "eval_logs", int(args.eval_seed_base),
            )

    # 4. manifest
    manifest = {
        "schema_version": 1,
        "contract": "docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_20260902.md",
        "claim_ceiling": "B (EXPLORE) - integrity and exposure only",
        "runner": "scripts/run_flexible_skill_duration_e0.py",
        "arm": args.arm,
        "seed": args.seed,
        "rollouts": rollouts,
        "timing_only": bool(args.timing_only),
        "code_sha": _git("rev-parse", "HEAD"),
        "code_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "code_dirty": bool(_git("status", "--porcelain")),
        "command": list(sys.argv),
        "config": {name: _jsonable(getattr(config, name, None))
                   for name in CONFIG_DUMP_FIELDS},
        "env": {
            "scenario": 1,
            "class": "envs.pettingzoo.scenario1.UAVBaseStationEnv",
            "adapter": "envs.pettingzoo.env_adapter.ParallelToArrayAdapter",
            "n_uavs": args.n_uavs,
            "n_users": args.n_users,
            "episode_length": episode_length,
            "num_envs": num_envs,
            "lane_seeds": [args.seed + rank for rank in range(num_envs)],
            "state_dim": int(envs[0].state_dim),
            "obs_dim": int(envs[0].obs_dim),
        },
        "evaluation": None if args.timing_only else {
            "lanes": int(args.eval_lanes),
            "lane_seeds": [int(args.eval_seed_base) + r for r in range(int(args.eval_lanes))],
            "deterministic": True,
            "interval_rollouts": int(args.eval_interval),
        },
        "machine": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "versions": {"torch": torch.__version__, "numpy": np.__version__},
        "torch_num_threads": int(torch.get_num_threads()),
        "device": "cpu",
        "preflight": preflight,
        "started_at": started_at,
        "ended_at": None,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(_jsonable(manifest), indent=2, ensure_ascii=False), encoding="utf-8")

    metrics_path = run_dir / "metrics.jsonl"
    metrics_path.write_text("", encoding="utf-8")

    probe_rollouts = []
    if args.probe_out and not args.timing_only:
        probe_rollouts = sorted({1, int(math.ceil(rollouts / 2)), rollouts})
    probe_records = {key: [] for key in
                     ("states", "observations", "team_skills", "agent_skills",
                      "env_steps", "rollout_indices", "lanes")}

    env_steps = np.zeros(num_envs, dtype=int)
    dones_tracker = np.zeros(num_envs, dtype=bool)
    episode_accumulator = np.zeros(num_envs, dtype=np.float64)
    cumulative_transitions = 0
    cumulative_episodes = 0
    evaluations = []
    rollout_rows = []
    rollout1 = None
    instability = None
    previous_d2 = None

    for rollout_index in range(1, rollouts + 1):
        rollout_started = time.perf_counter()
        completed_returns = []
        last_next_states = None
        last_next_observations = None

        probe_targets = {}
        if rollout_index in probe_rollouts:
            flat = probe_rng.choice(rollout_length * num_envs,
                                    size=int(args.probes_per_rollout), replace=False)
            for position in np.sort(flat):
                t_idx, lane = divmod(int(position), num_envs)
                probe_targets.setdefault(t_idx, []).append(lane)

        record_rollout1 = rollout_index == 1
        r1_boundaries, r1_team, r1_agent = [], [], []

        for t in range(rollout_length):
            actions, _infos, step_data = agent.step(
                states, observations, env_steps, dones_tracker,
                deterministic=False, return_step_data=True, build_infos=False,
            )

            if record_rollout1:
                r1_boundaries.append(
                    np.asarray(step_data["skill_changed"], dtype=bool).copy())
                r1_team.append(np.asarray(step_data["team_skills"], dtype=np.int64).copy())
                r1_agent.append(np.asarray(step_data["agent_skills"], dtype=np.int64).copy())

            for lane in probe_targets.get(t, ()):
                probe_records["states"].append(np.asarray(states[lane], dtype=np.float64))
                probe_records["observations"].append(
                    np.asarray(observations[lane], dtype=np.float32))
                probe_records["team_skills"].append(int(step_data["team_skills"][lane]))
                probe_records["agent_skills"].append(
                    np.asarray(step_data["agent_skills"][lane], dtype=np.int64))
                probe_records["env_steps"].append(int(env_steps[lane]))
                probe_records["rollout_indices"].append(int(rollout_index))
                probe_records["lanes"].append(int(lane))

            next_observations_list, next_states_list = [], []
            rewards = np.zeros(num_envs, dtype=np.float64)
            dones = np.zeros(num_envs, dtype=bool)
            for lane, env in enumerate(envs):
                next_obs, reward, terminated, truncated, info = env.step(actions[lane])
                next_observations_list.append(np.asarray(next_obs, dtype=np.float32))
                next_states_list.append(np.asarray(info["next_state"], dtype=np.float64))
                rewards[lane] = float(reward)
                dones[lane] = bool(terminated or truncated)
            next_observations = np.stack(next_observations_list)
            next_states = np.stack(next_states_list)

            if not np.all(np.isfinite(rewards)):
                instability = {
                    "kind": "non-finite reward",
                    "rollout": rollout_index,
                    "step": t,
                    "lanes": np.flatnonzero(~np.isfinite(rewards)).tolist(),
                }
                break

            # Storage keeps the terminal transition; the policy input after a done uses the
            # reset observation while the state stays the terminal state (the SubprocVecEnv
            # semantics the fingerprint driver mirrors).
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

            episode_accumulator += rewards
            policy_next_states = next_states.copy()
            policy_next_observations = next_observations.copy()
            for lane, env in enumerate(envs):
                if dones[lane]:
                    completed_returns.append(float(episode_accumulator[lane]))
                    episode_accumulator[lane] = 0.0
                    dones_tracker[lane] = True
                    env_steps[lane] = 0
                    agent.reset_env_state(lane)
                    reset_obs, _reset_info = env.reset()
                    policy_next_observations[lane] = np.asarray(reset_obs, dtype=np.float32)
                else:
                    env_steps[lane] += 1
            states = policy_next_states
            observations = policy_next_observations
            dones_tracker = dones.copy()
            last_next_states = next_states
            last_next_observations = next_observations
            cumulative_transitions += num_envs

        if instability is not None:
            break

        rollout_seconds = time.perf_counter() - rollout_started
        cumulative_episodes += len(completed_returns)

        # discoverer bootstrap, mirroring train_multiproc_config_1.py:4942-5005
        last_values_predicted = np.zeros((num_envs, config.n_agents), dtype=np.float32)
        with torch.no_grad():
            next_team_skills = np.zeros(num_envs, dtype=np.int64)
            for lane in range(num_envs):
                next_env_step = int(env_steps[lane]) + 1
                if next_env_step % config.k == 0:
                    next_team_skill, _skills, _lp = agent.assign_skills(
                        last_next_states[lane], last_next_observations[lane])
                else:
                    next_team_skill = agent.env_team_skills.get(lane, 0)
                    if next_team_skill == -1:
                        next_team_skill = 0
                next_team_skills[lane] = int(next_team_skill)
            normalized_next_states = agent._normalize_states(last_next_states, update=False)
            global_state_tensor = torch.FloatTensor(normalized_next_states).to(agent.device)
            team_skill_tensor = torch.as_tensor(
                next_team_skills, dtype=torch.long, device=agent.device)
            critic_hidden_batch = np.zeros((num_envs, config.gru_hidden_size), dtype=np.float32)
            for lane in range(num_envs):
                critic_hidden_batch[lane] = agent.get_current_critic_hidden_np(
                    lane, agent_index=0)
            critic_hidden_tensor = torch.FloatTensor(critic_hidden_batch).to(agent.device)
            global_value_tensor, _ = agent.skill_discoverer.get_value(
                global_state_tensor, team_skill_tensor,
                critic_hidden_state=critic_hidden_tensor)
            if config.use_valuenorm and agent.value_norm_discoverer is not None:
                global_value_tensor = agent._denormalize_values(
                    global_value_tensor, agent.value_norm_discoverer)
            bootstrap_values = (
                global_value_tensor.squeeze(-1).detach().cpu().numpy().reshape(num_envs, 1))
            last_values_predicted[:, :] = bootstrap_values

        before_counts = {name: counter.count for name, counter in counters.items()}
        update_started = time.perf_counter()
        update_info = agent.update(
            steps_in_buffer=rollout_length,
            last_values=last_values_predicted,
            dones=dones_tracker.copy(),
            last_state=states.copy(),
            last_observations=observations.copy(),
        )
        update_seconds = time.perf_counter() - update_started

        # high-level rows and target scale, read before `clear_buffers`
        buffer = agent.rollout_buffer
        if args.arm == "off":
            valid = np.asarray(buffer.high_level_valid_mask[:rollout_length], dtype=bool)
            rows_M = int(valid.sum())
            team_returns = np.asarray(buffer.high_level_team_returns[:rollout_length])[valid]
            agent_returns = np.asarray(buffer.high_level_agent_returns[:rollout_length])[valid]
            segment_reward = np.asarray(buffer.high_level_rewards[:rollout_length])[valid]
            d2_metrics = None
            d2_delta = None
        else:
            tables = buffer.get_d2_tables(rollout_length)
            team_valid = np.asarray(tables["team_valid"], dtype=bool)
            agent_valid = np.asarray(tables["agent_valid"], dtype=bool)
            team_returns = np.asarray(tables["team_returns"])[team_valid]
            agent_returns = np.asarray(tables["agent_returns"])[agent_valid]
            segment_reward = np.asarray(tables["team_reward"])[team_valid]
            d2_metrics = agent.get_d2_metrics()
            rows_M = int(d2_metrics["rows_M"])
            # `d2_metrics` accumulates across rollouts; record the per-rollout delta too.
            d2_delta = {"cause_counts": {}, "steps": None, "decision_steps": None,
                        "team_decisions": None, "sampled_total": None, "forced_total": None}
            for key in ("steps", "decision_steps", "team_decisions", "sampled_total",
                        "forced_total"):
                prior = int(previous_d2[key]) if previous_d2 else 0
                d2_delta[key] = int(d2_metrics[key]) - prior
            for cause, count in d2_metrics["cause_counts"].items():
                prior = int(previous_d2["cause_counts"].get(cause, 0)) if previous_d2 else 0
                d2_delta["cause_counts"][cause] = int(count) - prior
            previous_d2 = copy.deepcopy(d2_metrics)

        target_scale_team = float(np.mean(np.abs(team_returns))) if team_returns.size else 0.0
        target_scale_agent = float(np.mean(np.abs(agent_returns))) if agent_returns.size else 0.0
        target_var_team = float(np.var(team_returns)) if team_returns.size else 0.0
        target_var_agent = float(np.var(agent_returns)) if agent_returns.size else 0.0
        mean_segment_reward = float(np.mean(segment_reward)) if segment_reward.size else 0.0

        if record_rollout1:
            rollout1 = {
                "boundaries": np.asarray(r1_boundaries, dtype=bool),
                "team_skills": np.asarray(r1_team, dtype=np.int64),
                "agent_skills": np.asarray(r1_agent, dtype=np.int64),
                "rows_M": rows_M,
                "target_scale_team": target_scale_team,
                "target_scale_agent": target_scale_agent,
            }

        agent.clear_buffers()

        exposure = _exposure_line(agent, theta0)
        losses = {}
        if isinstance(update_info, dict):
            for key in LOSS_FIELDS:
                if key in update_info:
                    losses[key] = _jsonable(update_info[key])

        non_finite = [name for name, value in losses.items()
                      if isinstance(value, str) and value in ("NaN", "Infinity", "-Infinity")]
        mean_return = float(np.mean(completed_returns)) if completed_returns else None
        if mean_return is not None and not math.isfinite(mean_return):
            non_finite.append("episode_return")

        row = {
            "rollout": rollout_index,
            "arm": args.arm,
            "seed": args.seed,
            "transitions_this_rollout": rollout_length * num_envs,
            "transitions_cumulative": cumulative_transitions,
            "episodes_this_rollout": len(completed_returns),
            "episodes_cumulative": cumulative_episodes,
            "optimizer_steps_cumulative": {n: c.count for n, c in counters.items()},
            "optimizer_steps_this_rollout": {
                n: c.count - before_counts[n] for n, c in counters.items()},
            "rows_M": rows_M,
            "mean_episode_return": mean_return,
            "mean_high_level_segment_reward": mean_segment_reward,
            "target_scale_team": target_scale_team,
            "target_scale_agent": target_scale_agent,
            "target_var_team": target_var_team,
            "target_var_agent": target_var_agent,
            "exposure_line": exposure,
            "losses": losses,
            "rollout_wall_seconds": rollout_seconds,
            "update_wall_seconds": update_seconds,
            "d2_metrics": _jsonable(d2_metrics) if d2_metrics is not None else None,
            "d2_metrics_delta": _jsonable(d2_delta) if d2_metrics is not None else None,
            "evaluation": None,
        }

        if non_finite:
            instability = {"kind": "non-finite loss or return",
                           "rollout": rollout_index, "fields": non_finite}

        do_eval = evaluator is not None and (
            rollout_index % int(args.eval_interval) == 0
            or rollout_index == rollouts
            or instability is not None)
        if do_eval:
            with _preserve_rng():
                row["evaluation"] = evaluator.run(agent)
            evaluations.append(dict(row["evaluation"], rollout=rollout_index))

        rollout_rows.append(row)
        with open(metrics_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(row), ensure_ascii=False) + "\n")

        if instability is not None:
            break

    # rollout-1 integrity artifacts
    integrity = {}
    if rollout1 is not None:
        np.save(run_dir / "rollout1_boundaries.npy", rollout1["boundaries"])
        np.save(run_dir / "rollout1_team_skills.npy", rollout1["team_skills"])
        np.save(run_dir / "rollout1_agent_skills.npy", rollout1["agent_skills"])
        (run_dir / "rollout1_summary.json").write_text(
            json.dumps(_jsonable({
                "arm": args.arm,
                "seed": args.seed,
                "rows_M": rollout1["rows_M"],
                "target_scale_team": rollout1["target_scale_team"],
                "target_scale_agent": rollout1["target_scale_agent"],
                "boundaries_sha256": _sha256_arrays({"b": rollout1["boundaries"]}),
                "team_skills_sha256": _sha256_arrays({"t": rollout1["team_skills"]}),
                "agent_skills_sha256": _sha256_arrays({"a": rollout1["agent_skills"]}),
                "boundary_count": int(rollout1["boundaries"].sum()),
                "shape_boundaries": list(rollout1["boundaries"].shape),
                "shape_agent_skills": list(rollout1["agent_skills"].shape),
            }), indent=2), encoding="utf-8")

        if args.reference_dir:
            reference = Path(args.reference_dir).resolve()
            ref_b = np.load(reference / "rollout1_boundaries.npy")
            ref_t = np.load(reference / "rollout1_team_skills.npy")
            ref_a = np.load(reference / "rollout1_agent_skills.npy")
            ref_summary = json.loads(
                (reference / "rollout1_summary.json").read_text(encoding="utf-8"))
            expected_M = num_envs * rollout_length // config.k
            ratio_team = (ref_summary["target_scale_team"] / rollout1["target_scale_team"]
                          if rollout1["target_scale_team"] else None)
            ratio_agent = (ref_summary["target_scale_agent"] / rollout1["target_scale_agent"]
                           if rollout1["target_scale_agent"] else None)
            integrity = {
                "reference_dir": str(reference),
                "reference_arm": ref_summary["arm"],
                "this_arm": args.arm,
                "boundary_mask_identical": bool(np.array_equal(ref_b, rollout1["boundaries"])),
                "boundary_mask_mismatches": int(np.sum(ref_b != rollout1["boundaries"])),
                "boundary_mask_shape": list(rollout1["boundaries"].shape),
                "team_skills_identical": bool(np.array_equal(ref_t, rollout1["team_skills"])),
                "team_skill_mismatches": int(np.sum(ref_t != rollout1["team_skills"])),
                "agent_skills_identical": bool(np.array_equal(ref_a, rollout1["agent_skills"])),
                "agent_skill_mismatches": int(np.sum(ref_a != rollout1["agent_skills"])),
                "rows_M_reference": ref_summary["rows_M"],
                "rows_M_this_arm": rollout1["rows_M"],
                "rows_M_expected": expected_M,
                "rows_M_ok": bool(rollout1["rows_M"] == ref_summary["rows_M"] == expected_M),
                "target_scale_team_reference": ref_summary["target_scale_team"],
                "target_scale_team_this_arm": rollout1["target_scale_team"],
                "target_scale_agent_reference": ref_summary["target_scale_agent"],
                "target_scale_agent_this_arm": rollout1["target_scale_agent"],
                "target_scale_ratio_team_off_over_d2": ratio_team,
                "target_scale_ratio_agent_off_over_d2": ratio_agent,
                "target_scale_ratio_band": [1.03, 1.06],
                "target_scale_ratio_team_in_band": bool(
                    ratio_team is not None and 1.03 <= ratio_team <= 1.06),
                "target_scale_ratio_agent_in_band": bool(
                    ratio_agent is not None and 1.03 <= ratio_agent <= 1.06),
                "tau_formula_value": float(
                    config.k * (1 - config.gamma) / (1 - config.gamma ** config.k)),
            }
            (run_dir / "integrity_checks.json").write_text(
                json.dumps(_jsonable(integrity), indent=2), encoding="utf-8")

    # probe set
    probe_record = None
    if probe_records["states"] and args.probe_out:
        arrays = {
            "states": np.stack(probe_records["states"]).astype(np.float64),
            "observations": np.stack(probe_records["observations"]).astype(np.float32),
            "team_skills": np.asarray(probe_records["team_skills"], dtype=np.int64),
            "agent_skills": np.stack(probe_records["agent_skills"]).astype(np.int64),
            "env_step": np.asarray(probe_records["env_steps"], dtype=np.int64),
            "rollout_index": np.asarray(probe_records["rollout_indices"], dtype=np.int64),
            "lane": np.asarray(probe_records["lanes"], dtype=np.int64),
        }
        probe_path = Path(args.probe_out).resolve()
        probe_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(probe_path, **arrays)
        recipe = (
            "rng = numpy.random.default_rng(probe_seed); for each rollout in "
            "[1, ceil(R/2), R] in ascending order: idx = rng.choice("
            "rollout_length * num_envs, size=probes_per_rollout, replace=False), then sorted "
            "ascending; a position p maps to (t, lane) = divmod(p, num_envs); the probe stores "
            "the policy input state and observations at step t of that rollout together with "
            "the team and agent skills `agent.step` assigned at that step, the lane's env_step, "
            "the rollout index and the lane index."
        )
        probe_record = {
            "path": str(probe_path),
            "probe_seed": int(args.probe_seed),
            "probes_per_rollout": int(args.probes_per_rollout),
            "rollouts_sampled": probe_rollouts,
            "n_probes": int(arrays["team_skills"].shape[0]),
            "shapes": {k: list(v.shape) for k, v in arrays.items()},
            "dtypes": {k: str(v.dtype) for k, v in arrays.items()},
            "content_sha256": _sha256_arrays(arrays),
            "file_sha256": _sha256_file(probe_path),
            "recipe": recipe,
        }
        if args.probe_json_out:
            count = min(int(args.probe_json_count), int(arrays["team_skills"].shape[0]))
            sample = {
                "schema_version": 1,
                "recipe": recipe,
                "note": (f"First {count} probes of the frozen probe set, in the npz file's "
                         "canonical order. The full 1,536-probe set is local only (*.npz is "
                         "gitignored)."),
                "arm": args.arm,
                "seed": args.seed,
                "probe_seed": int(args.probe_seed),
                "full_set": {k: probe_record[k] for k in
                             ("path", "n_probes", "shapes", "dtypes", "content_sha256",
                              "file_sha256", "rollouts_sampled", "probes_per_rollout")},
                "probes": [
                    {
                        "index": int(i),
                        "rollout_index": int(arrays["rollout_index"][i]),
                        "lane": int(arrays["lane"][i]),
                        "env_step": int(arrays["env_step"][i]),
                        "team_skill": int(arrays["team_skills"][i]),
                        "agent_skills": [int(v) for v in arrays["agent_skills"][i]],
                        "state": [float(v) for v in arrays["states"][i]],
                        "observations": [[float(v) for v in obs_row]
                                         for obs_row in arrays["observations"][i]],
                    }
                    for i in range(count)
                ],
            }
            json_path = Path(args.probe_json_out).resolve()
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")
            probe_record["json_sample"] = str(json_path)
            probe_record["json_sample_count"] = count

    # checkpoint
    checkpoint_path = None
    if not args.timing_only:
        checkpoint_path = run_dir / "checkpoint_final.pt"
        agent.save_model(str(checkpoint_path))

    ended_at = _utc_now()
    total_seconds = time.perf_counter() - started_wall
    manifest["ended_at"] = ended_at
    manifest["wall_seconds"] = total_seconds
    (run_dir / "manifest.json").write_text(
        json.dumps(_jsonable(manifest), indent=2, ensure_ascii=False), encoding="utf-8")

    completed = instability is None and len(rollout_rows) == rollouts
    final_eval = evaluations[-1] if evaluations else None
    mid_index = int(math.ceil(rollouts / 2))
    summary = {
        "schema_version": 1,
        "arm": args.arm,
        "seed": args.seed,
        "rollouts_requested": rollouts,
        "rollouts_completed": len(rollout_rows),
        "completed": completed,
        "timing_only": bool(args.timing_only),
        "instability": instability,
        "transitions_total": cumulative_transitions,
        "episodes_total": cumulative_episodes,
        "optimizer_steps_total": {n: c.count for n, c in counters.items()},
        "evaluation_count": len(evaluations),
        "final_evaluation_return_mean": (final_eval["return_mean"] if final_eval else None),
        "final_evaluation_return_std": (final_eval["return_std"] if final_eval else None),
        "evaluations": evaluations,
        "exposure_line_rollout_1": rollout_rows[0]["exposure_line"] if rollout_rows else None,
        "exposure_line_rollout_mid": (
            rollout_rows[mid_index - 1]["exposure_line"]
            if len(rollout_rows) >= mid_index else None),
        "exposure_line_rollout_last": (
            rollout_rows[-1]["exposure_line"] if rollout_rows else None),
        "exposure_line_mid_rollout_index": mid_index,
        "rows_M_per_rollout": [r["rows_M"] for r in rollout_rows],
        "mean_episode_return_per_rollout": [r["mean_episode_return"] for r in rollout_rows],
        "rollout_wall_seconds": [r["rollout_wall_seconds"] for r in rollout_rows],
        "update_wall_seconds": [r["update_wall_seconds"] for r in rollout_rows],
        "wall_seconds_total": total_seconds,
        "seconds_per_rollout_mean": (
            float(np.mean([r["rollout_wall_seconds"] + r["update_wall_seconds"]
                           for r in rollout_rows])) if rollout_rows else None),
        "torch_num_threads": int(torch.get_num_threads()),
        "integrity_checks": integrity or None,
        "probe_set": probe_record,
        "checkpoint": str(checkpoint_path) if checkpoint_path else None,
        "started_at": started_at,
        "ended_at": ended_at,
        "code_sha": manifest["code_sha"],
    }
    (run_dir / "summary.json").write_text(
        json.dumps(_jsonable(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    if not completed:
        (run_dir / "QUARANTINED").write_text(
            "This arm is an incomplete attempt (contract section 4 stop rule).\n"
            "It yields no observation. No resume, no salvage.\n\n"
            f"time: {ended_at}\ninstability: {json.dumps(_jsonable(instability))}\n"
            f"rollouts completed: {len(rollout_rows)} of {rollouts}\n",
            encoding="utf-8")

    print(json.dumps(_jsonable({
        "arm": args.arm,
        "seed": args.seed,
        "completed": completed,
        "rollouts_completed": len(rollout_rows),
        "transitions_total": cumulative_transitions,
        "episodes_total": cumulative_episodes,
        "optimizer_steps_total": summary["optimizer_steps_total"],
        "evaluation_count": len(evaluations),
        "final_evaluation_return_mean": summary["final_evaluation_return_mean"],
        "exposure_line_rollout_last": summary["exposure_line_rollout_last"],
        "wall_seconds_total": total_seconds,
        "seconds_per_rollout_mean": summary["seconds_per_rollout_mean"],
        "run_dir": str(run_dir),
    }), ensure_ascii=False))
    return 0 if completed else 3


if __name__ == "__main__":
    raise SystemExit(main())
