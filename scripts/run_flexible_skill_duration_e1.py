"""E1 runner - age input to the discriminators at fixed k (D0 versus D1, scenario 1).

Launch contract: `docs/Claude_docs/experiments/E1_AGE_INPUT_20260902.md`.
Claim ceiling B (EXPLORE).  Nothing this script writes is a performance claim.

Contract section 2 requires the rollout loop to be *the E0 runner's loop*, imported rather
than copied.  This module therefore imports `scripts/run_flexible_skill_duration_e0.py` and
calls its `_execute()` unchanged.  Three seams are used, none of which edits the E0 file:

1. `e0._make_config` is wrapped so the `d1` arm's config carries `age_feature="normalized"`
   (the `d0` arm keeps the E0 D0 config verbatim, `age_feature="off"`).
2. `e0._exposure_line` is wrapped.  `_execute` calls it exactly once per rollout, after
   `agent.update()` and `agent.clear_buffers()` and *outside* both of E0's timers, which is
   where contract section 3 puts the probe measurements ("after every rollout's update").
   The wrapper returns the original exposure dict untouched and, on the way, runs the probe
   measurements of contract section 3 on the learner.
3. `args.arm` is passed as `"d0"` / `"d1"`.  E0's `_make_config` branches only on
   `arm == "off"`, so both E1 arms take the D2/D0 branch; the arm string is what the manifest,
   the summary and the printed line record.

The measurements never touch the learner.  A second `HMASDAgent` (the E0 evaluation
mechanism) is constructed lazily inside `e0._preserve_rng()` and weight-/normaliser-synced
from the learner before every measurement; every forward pass runs under `torch.no_grad()`
in `train(False)` with `update=False` normalisation.

Usage (explicit interpreter, per CLAUDE.md):

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        scripts/run_flexible_skill_duration_e1.py \
        --arm d1 --seed 1 --rollouts 20 --num-envs 32 --threads 4 \
        --launch-commit 6fba1c7ba \
        --output-root C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E1_20260902
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_flexible_skill_duration_e0 as e0  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402


CONTRACT = "docs/Claude_docs/experiments/E1_AGE_INPUT_20260902.md"

DEFAULT_PROBE_SET = (
    "C:/Projects/HMASD/temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz"
)
# Contract section 3: the frozen E0 probe set's container-independent content digest.
PROBE_SET_CONTENT_SHA256 = (
    "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c"
)

# Contract section 3 item 1: the D1 age input is `(env_step mod 10) / 10` for both ages.
AGE_MODULUS = 10
AGE_DENOMINATOR = 10.0

# Contract section 3 item 3: the age buckets of `env_step mod 10`.
AGE_BUCKETS = (
    ("0-2", (0, 1, 2)),
    ("3-6", (3, 4, 5, 6)),
    ("7-9", (7, 8, 9)),
)

PROBE_ARRAY_KEYS = (
    "states", "observations", "team_skills", "agent_skills",
    "env_step", "rollout_index", "lane",
)


# ---------------------------------------------------------------------------
# probe set
# ---------------------------------------------------------------------------


def load_probe_set(path, expected_digest=PROBE_SET_CONTENT_SHA256):
    """Load the frozen probe set and refuse to continue unless its digest matches.

    The digest recipe is E0's `_sha256_arrays`: sha256 over the named arrays sorted by key,
    each contributing `key || str(dtype) || str(shape) || tobytes()`.  It is
    container-independent, because `np.savez` stamps its zip entries with the wall clock.
    """
    path = Path(path)
    if not path.exists():
        raise RuntimeError(f"frozen probe set not found: {path}")
    with np.load(str(path)) as handle:
        arrays = {key: np.asarray(handle[key]) for key in handle.files}
    missing = [key for key in PROBE_ARRAY_KEYS if key not in arrays]
    if missing:
        raise RuntimeError(f"probe set {path} is missing arrays {missing}")
    digest = e0._sha256_arrays(arrays)
    if digest != expected_digest:
        raise RuntimeError(
            "frozen probe set content digest mismatch; the run is refused.\n"
            f"  path     : {path}\n"
            f"  expected : {expected_digest}\n"
            f"  measured : {digest}"
        )
    return arrays, digest


def normalized_ages(env_step, modulus=AGE_MODULUS, denominator=AGE_DENOMINATOR):
    """Contract section 3 item 1: `(env_step mod 10) / 10`, one scalar per probe."""
    raw = np.asarray(env_step, dtype=np.int64) % int(modulus)
    return raw, (raw.astype(np.float32) / float(denominator))


def age_bucket_masks(raw_ages, buckets=AGE_BUCKETS):
    """Boolean mask per contract bucket of `env_step mod 10`."""
    raw_ages = np.asarray(raw_ages, dtype=np.int64)
    masks = {}
    for name, values in buckets:
        masks[name] = np.isin(raw_ages, np.asarray(values, dtype=np.int64))
    return masks


def age_bucket_index(raw_ages, buckets=AGE_BUCKETS):
    """Bucket ordinal per probe (0, 1, 2); -1 if a probe falls in no bucket."""
    raw_ages = np.asarray(raw_ages, dtype=np.int64)
    out = np.full(raw_ages.shape, -1, dtype=np.int64)
    for ordinal, (_name, values) in enumerate(buckets):
        out[np.isin(raw_ages, np.asarray(values, dtype=np.int64))] = ordinal
    return out


# ---------------------------------------------------------------------------
# contract section 3 arithmetic (pure, unit-testable)
# ---------------------------------------------------------------------------


def team_agreement(previous_labels, current_labels):
    """Contract section 3 item 2 (team): fraction of probes whose label is unchanged."""
    previous_labels = np.asarray(previous_labels)
    current_labels = np.asarray(current_labels)
    if previous_labels.shape != current_labels.shape:
        raise ValueError("team label arrays must have the same shape")
    if previous_labels.size == 0:
        return None
    return float(np.mean(previous_labels == current_labels))


def individual_agreement(previous_labels, current_labels):
    """Contract section 3 item 2 (individual): per-agent fraction, then averaged over agents.

    `previous_labels` / `current_labels` have shape `[n_probes, n_agents]`.
    Returns `(per_agent_list, mean_over_agents)`.
    """
    previous_labels = np.asarray(previous_labels)
    current_labels = np.asarray(current_labels)
    if previous_labels.shape != current_labels.shape:
        raise ValueError("individual label arrays must have the same shape")
    if previous_labels.ndim != 2:
        raise ValueError("individual label arrays must be [n_probes, n_agents]")
    if previous_labels.size == 0:
        return [], None
    per_agent = np.mean(previous_labels == current_labels, axis=0)
    return [float(v) for v in per_agent], float(np.mean(per_agent))


def accuracy_overall_and_by_bucket(labels, truth, raw_ages, buckets=AGE_BUCKETS):
    """Contract section 3 item 3.

    `labels` / `truth` are `[n_probes]` (team) or `[n_probes, n_agents]` (individual);
    `raw_ages` is `[n_probes]` of `env_step mod 10` and is broadcast over agents.
    Returns `{"overall": float, "<bucket>": float or None, "<bucket>_n": int}`.
    """
    labels = np.asarray(labels)
    truth = np.asarray(truth)
    if labels.shape != truth.shape:
        raise ValueError("label and truth arrays must have the same shape")
    correct = (labels == truth)
    masks = age_bucket_masks(raw_ages, buckets)
    out = {"overall": float(np.mean(correct)) if correct.size else None,
           "overall_n": int(correct.size)}
    for name, mask in masks.items():
        selected = correct[mask] if correct.ndim == 1 else correct[mask, :]
        out[name] = float(np.mean(selected)) if selected.size else None
        out[f"{name}_n"] = int(selected.size)
    return out


def age_weight_share(weight, age_columns=1):
    """Contract section 3 item 5: ||age columns of W|| / ||W|| for an input projection W.

    The age input is appended last (`torch.cat([x, age], dim=-1)` in
    `hmasd/networks.py`), so the age columns are the final `age_columns` columns of the
    `[out_features, in_features]` weight matrix.
    """
    weight = np.asarray(weight, dtype=np.float64)
    if weight.ndim != 2:
        raise ValueError("weight must be a 2-D [out_features, in_features] matrix")
    if age_columns <= 0:
        return None
    total = float(np.linalg.norm(weight))
    age_norm = float(np.linalg.norm(weight[:, -int(age_columns):]))
    return {
        "age_column_norm": age_norm,
        "input_projection_norm": total,
        "age_share": (age_norm / total) if total > 0 else None,
    }


# ---------------------------------------------------------------------------
# the probe measurer (a second agent instance, synced from the learner)
# ---------------------------------------------------------------------------


class ProbeMeasurer:
    """Contract section 3, measured on a second `HMASDAgent` synced from the learner.

    The learner is never read in a way that mutates it: the probe agent owns its own
    networks and its own deep copies of the running normalisers, is held in `train(False)`,
    and every forward pass is under `torch.no_grad()` with `update=False` normalisation.
    Construction and every measurement run inside `e0._preserve_rng()`, so the learner's
    RNG streams and per-lane state are untouched.
    """

    def __init__(self, arm, seed, num_envs, rollout_length, episode_length,
                 n_uavs, n_users, rollouts, state_dim, obs_dim, log_dir, probes):
        self.arm = arm
        self.probes = probes
        self.n_probes = int(probes["team_skills"].shape[0])
        self.n_agents = int(probes["agent_skills"].shape[1])
        self.raw_ages, self.age_input = normalized_ages(probes["env_step"])
        self.bucket_index = age_bucket_index(self.raw_ages)
        self.states = np.ascontiguousarray(probes["states"], dtype=np.float32)
        self.observations = np.ascontiguousarray(probes["observations"], dtype=np.float32)
        self.team_truth = np.asarray(probes["team_skills"], dtype=np.int64)
        self.agent_truth = np.asarray(probes["agent_skills"], dtype=np.int64)
        self.config = e0._make_config(
            arm, seed, num_envs, rollout_length, episode_length, n_uavs, n_users,
            rollouts, int(state_dim), int(obs_dim),
        )
        self.agent = HMASDAgent(self.config, log_dir=str(log_dir), device=torch.device("cpu"))
        self.agent.train(False)
        self.previous = None
        self.records = []

    # -- syncing -----------------------------------------------------------

    def sync(self, learner):
        """Exactly the E0 evaluator's sync: weights plus deep-copied normalisers."""
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

    # -- the five measurements --------------------------------------------

    def _forward(self):
        agent = self.agent
        uses_age = bool(agent._d2_uses_age_feature())
        normalized_states = np.asarray(
            agent._normalize_states(self.states, update=False), dtype=np.float32)
        normalized_observations = np.asarray(
            agent._normalize_observations(self.observations, update=False), dtype=np.float32)
        state_tensor = torch.as_tensor(normalized_states, dtype=torch.float32)
        obs_tensor_3d = torch.as_tensor(normalized_observations, dtype=torch.float32)
        flat_obs = torch.as_tensor(
            normalized_observations.reshape(self.n_probes * self.n_agents, -1),
            dtype=torch.float32)
        team_skill_flat = torch.as_tensor(
            np.repeat(self.team_truth, self.n_agents), dtype=torch.long)

        team_age = self.age_input if uses_age else None
        agent_age = np.repeat(self.age_input, self.n_agents) if uses_age else None

        with torch.no_grad():
            # (1) discriminator labels
            team_logits = agent._team_discriminator_logits(state_tensor, None, age=team_age)
            team_labels = team_logits.argmax(dim=-1).cpu().numpy().astype(np.int64)
            individual_logits = agent._individual_discriminator_logits(
                flat_obs, team_skill_flat, None, age=agent_age)
            individual_labels = (
                individual_logits.argmax(dim=-1).cpu().numpy()
                .astype(np.int64).reshape(self.n_probes, self.n_agents))

            # (4) coordinator value heads, denormalised
            state_value, agent_values, _cd = agent.skill_coordinator.get_value(
                state_tensor, obs_tensor_3d)
            if not agent_values:
                agent_values = [torch.zeros_like(state_value)
                                for _ in range(self.n_agents)]
            if (getattr(agent.config, "use_valuenorm", False)
                    and agent.value_norm_coordinator is not None):
                state_value = agent._denormalize_values(
                    state_value, agent.value_norm_coordinator)
                agent_values = [agent._denormalize_values(v, agent.value_norm_coordinator)
                                for v in agent_values]
            team_value = state_value.squeeze(-1).cpu().numpy().astype(np.float64)
            agent_value = np.stack(
                [v.squeeze(-1).cpu().numpy().astype(np.float64) for v in agent_values],
                axis=1)

        return {
            "team_labels": team_labels,
            "individual_labels": individual_labels,
            "team_value": team_value,
            "agent_value": agent_value,
            "uses_age": uses_age,
        }

    def _weight_shares(self):
        """(5) age-feature share of each discriminator's first-layer weight norm."""
        agent = self.agent
        out = {"team": None, "individual": None}
        team_d = agent.team_discriminator
        ind_d = agent.individual_discriminator
        if team_d is not None and int(getattr(team_d, "age_input_dim", 0)) > 0:
            out["team"] = age_weight_share(
                team_d.input_projection.weight.detach().cpu().numpy(),
                int(team_d.age_input_dim))
        if ind_d is not None and int(getattr(ind_d, "age_input_dim", 0)) > 0:
            out["individual"] = age_weight_share(
                ind_d.obs_input_projection.weight.detach().cpu().numpy(),
                int(ind_d.age_input_dim))
        return out

    def measure(self, learner, rollout_index):
        started = time.perf_counter()
        with e0._preserve_rng():
            self.sync(learner)
            forward = self._forward()
            shares = self._weight_shares()

        team_labels = forward["team_labels"]
        individual_labels = forward["individual_labels"]
        team_value = forward["team_value"]
        agent_value = forward["agent_value"]

        record = {
            "rollout": int(rollout_index),
            "arm": self.arm,
            "n_probes": self.n_probes,
            "n_agents": self.n_agents,
            "age_feature_active": bool(forward["uses_age"]),
            # (3) probe accuracy, overall and by age bucket
            "team_accuracy": accuracy_overall_and_by_bucket(
                team_labels, self.team_truth, self.raw_ages),
            "individual_accuracy": accuracy_overall_and_by_bucket(
                individual_labels, self.agent_truth, self.raw_ages),
            # (5) age-feature weight share (None on D0)
            "age_weight_share": shares,
            # label distributions, recorded as observations
            "team_label_histogram": np.bincount(
                team_labels, minlength=int(self.config.n_Z)).tolist(),
            "individual_label_histogram": np.bincount(
                individual_labels.reshape(-1), minlength=int(self.config.n_z)).tolist(),
            # (4) value level, for the drift series
            "team_value_mean": float(np.mean(team_value)),
            "team_value_std": float(np.std(team_value)),
            "agent_value_mean": float(np.mean(agent_value)),
            "agent_value_std": float(np.std(agent_value)),
        }

        # (2) label agreement with the previous rollout, and (4) value drift
        if self.previous is None:
            record["team_label_agreement"] = None
            record["individual_label_agreement"] = None
            record["individual_label_agreement_per_agent"] = None
            record["team_value_mean_abs_change"] = None
            record["agent_value_mean_abs_change"] = None
        else:
            record["team_label_agreement"] = team_agreement(
                self.previous["team_labels"], team_labels)
            per_agent, mean_agreement = individual_agreement(
                self.previous["individual_labels"], individual_labels)
            record["individual_label_agreement_per_agent"] = per_agent
            record["individual_label_agreement"] = mean_agreement
            record["team_value_mean_abs_change"] = float(
                np.mean(np.abs(team_value - self.previous["team_value"])))
            record["agent_value_mean_abs_change"] = float(
                np.mean(np.abs(agent_value - self.previous["agent_value"])))

        record["measure_wall_seconds"] = float(time.perf_counter() - started)
        self.previous = {
            "team_labels": team_labels,
            "individual_labels": individual_labels,
            "team_value": team_value,
            "agent_value": agent_value,
        }
        self.records.append({
            "rollout": int(rollout_index),
            "team_labels": team_labels,
            "individual_labels": individual_labels,
            "team_value": team_value,
            "agent_value": agent_value,
        })
        return record

    def save_arrays(self, path):
        if not self.records:
            return None
        arrays = {
            "rollout_index": np.asarray([r["rollout"] for r in self.records], dtype=np.int64),
            "team_labels": np.stack([r["team_labels"] for r in self.records]),
            "individual_labels": np.stack([r["individual_labels"] for r in self.records]),
            "team_values": np.stack([r["team_value"] for r in self.records]),
            "agent_values": np.stack([r["agent_value"] for r in self.records]),
            "probe_env_step": np.asarray(self.probes["env_step"], dtype=np.int64),
            "probe_raw_age": self.raw_ages.astype(np.int64),
            "probe_age_input": self.age_input.astype(np.float32),
            "probe_age_bucket_index": self.bucket_index.astype(np.int64),
            "probe_team_skills": self.team_truth,
            "probe_agent_skills": self.agent_truth,
        }
        np.savez(str(path), **arrays)
        return {k: list(v.shape) for k, v in arrays.items()}


# ---------------------------------------------------------------------------
# per-run derived series (contract section 3 items 2 and 4, second half)
# ---------------------------------------------------------------------------


def summarise_probe_records(records, rollouts):
    """`r >= R/2` windows for agreement and for value drift, plus the accuracy series."""
    half = math.ceil(rollouts / 2)
    window = [r for r in records if int(r["rollout"]) >= half]

    def _mean(values):
        values = [v for v in values if v is not None]
        return float(np.mean(values)) if values else None

    def _var(values):
        values = [v for v in values if v is not None]
        return float(np.var(values)) if values else None

    out = {
        "window_start_rollout": int(half),
        "window_rollouts": [int(r["rollout"]) for r in window],
        "team_label_agreement_mean_window": _mean(
            [r["team_label_agreement"] for r in window]),
        "individual_label_agreement_mean_window": _mean(
            [r["individual_label_agreement"] for r in window]),
        "team_value_mean_abs_change_mean_window": _mean(
            [r["team_value_mean_abs_change"] for r in window]),
        "agent_value_mean_abs_change_mean_window": _mean(
            [r["agent_value_mean_abs_change"] for r in window]),
        "team_value_mean_abs_change_var_window": _var(
            [r["team_value_mean_abs_change"] for r in window]),
        "agent_value_mean_abs_change_var_window": _var(
            [r["agent_value_mean_abs_change"] for r in window]),
        "team_accuracy_final": records[-1]["team_accuracy"] if records else None,
        "individual_accuracy_final": records[-1]["individual_accuracy"] if records else None,
    }
    for key in ("overall",) + tuple(name for name, _v in AGE_BUCKETS):
        out[f"team_accuracy_{key}_mean_window"] = _mean(
            [r["team_accuracy"][key] for r in window])
        out[f"individual_accuracy_{key}_mean_window"] = _mean(
            [r["individual_accuracy"][key] for r in window])
    if records and records[-1].get("age_weight_share", {}).get("team") is not None:
        out["age_weight_share_first"] = records[0]["age_weight_share"]
        out["age_weight_share_final"] = records[-1]["age_weight_share"]
    return out


def probe_value_variance_over_window(npz_path, rollouts):
    """Per-probe variance of the value across rollouts `r >= R/2`, averaged over probes.

    This is the second reading of contract section 3 item 4's "variance across rollouts
    `r >= R/2`"; the first reading (variance of the per-rollout mean absolute change) is
    `*_mean_abs_change_var_window` in `summarise_probe_records`.  Both are reported.
    """
    with np.load(str(npz_path)) as handle:
        rollout_index = np.asarray(handle["rollout_index"], dtype=np.int64)
        team_values = np.asarray(handle["team_values"], dtype=np.float64)
        agent_values = np.asarray(handle["agent_values"], dtype=np.float64)
    half = math.ceil(rollouts / 2)
    mask = rollout_index >= half
    if not mask.any():
        return None
    return {
        "window_start_rollout": int(half),
        "team_value_var_across_rollouts_mean_over_probes": float(
            np.mean(np.var(team_values[mask], axis=0))),
        "agent_value_var_across_rollouts_mean_over_probes": float(
            np.mean(np.var(agent_values[mask], axis=0))),
    }


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------


def _e0_args(args, run_dir):
    """The exact `argparse.Namespace` E0's `_execute` expects."""
    return argparse.Namespace(
        arm=args.arm,
        seed=args.seed,
        rollouts=args.rollouts,
        num_envs=args.num_envs,
        output_root=str(run_dir.parent),
        threads=args.threads,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        episode_length=args.episode_length,
        rollout_length=args.rollout_length,
        eval_interval=args.eval_interval,
        eval_lanes=args.eval_lanes,
        eval_seed_base=args.eval_seed_base,
        probe_seed=20_260_902,
        probes_per_rollout=512,
        probe_out=None,          # E1 never writes a probe set; the E0 set is read-only
        probe_json_out=None,
        probe_json_count=0,
        reference_dir=None,      # the arms are compared by the test, not by E0's checker
        run_name=run_dir.name,
        timing_only=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="E1 age-input runner (D0 versus D1)")
    parser.add_argument("--arm", choices=("d0", "d1"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--rollouts", type=int, default=20)
    parser.add_argument("--num-envs", type=int, default=32)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--n-uavs", type=int, default=6)
    parser.add_argument("--n-users", type=int, default=50)
    parser.add_argument("--episode-length", type=int, default=500)
    parser.add_argument("--rollout-length", type=int, default=500)
    parser.add_argument("--eval-interval", type=int, default=5)
    parser.add_argument("--eval-lanes", type=int, default=8)
    parser.add_argument("--eval-seed-base", type=int, default=10_000)
    parser.add_argument("--probe-set", default=DEFAULT_PROBE_SET)
    parser.add_argument("--probe-set-sha256", default=PROBE_SET_CONTENT_SHA256)
    parser.add_argument("--launch-commit", default=None,
                        help="the launch commit sha recorded in the manifest (contract section 2)")
    parser.add_argument("--smoke", action="store_true",
                        help="2 rollouts, 4 lanes, 100-step episodes; NOT EVIDENCE")
    args = parser.parse_args()

    if args.smoke:
        args.rollouts = 2
        args.num_envs = 4
        args.episode_length = 100
        args.rollout_length = 100

    run_name = args.run_name or f"{args.arm}_seed{args.seed}"
    run_dir = Path(args.output_root).resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        return _execute_e1(args, run_dir)
    except BaseException:  # noqa: BLE001 - every failure quarantines the run
        text = traceback.format_exc()
        (run_dir / "QUARANTINED").write_text(
            "This run is an incomplete attempt (contract section 4 stop rule, spec 6.2).\n"
            "It yields no observation. No resume, no salvage.\n\n"
            f"time: {e0._utc_now()}\n\n{text}",
            encoding="utf-8",
        )
        sys.stderr.write(text)
        return 2


def _execute_e1(args, run_dir: Path) -> int:
    # 1. the frozen probe set, verified before anything else is built
    probes, probe_digest = load_probe_set(args.probe_set, args.probe_set_sha256)

    state = {"measurer": None, "rollout": 0, "records": []}
    probe_metrics_path = run_dir / "probe_metrics.jsonl"
    probe_metrics_path.write_text("", encoding="utf-8")

    original_make_config = e0._make_config
    original_exposure_line = e0._exposure_line

    def make_config(arm, seed, num_envs, rollout_length, episode_length, n_uavs, n_users,
                    rollouts, state_dim, obs_dim):
        config = original_make_config(
            arm, seed, num_envs, rollout_length, episode_length, n_uavs, n_users,
            rollouts, state_dim, obs_dim)
        if arm == "d1":
            config.age_feature = "normalized"
            config._validate_policy_interruption()
        return config

    def exposure_line(agent, theta0):
        """E0 calls this once per rollout, after `update` and `clear_buffers`.

        The exposure dict is returned untouched; the contract section 3 measurements are
        taken here, on a second agent synced from `agent`.
        """
        exposure = original_exposure_line(agent, theta0)
        state["rollout"] += 1
        if state["measurer"] is None:
            with e0._preserve_rng():
                state["measurer"] = ProbeMeasurer(
                    args.arm, args.seed, args.num_envs, args.rollout_length,
                    args.episode_length, args.n_uavs, args.n_users, args.rollouts,
                    int(probes["states"].shape[1]), int(probes["observations"].shape[2]),
                    run_dir / "probe_logs", probes,
                )
        record = state["measurer"].measure(agent, state["rollout"])
        state["records"].append(record)
        with open(probe_metrics_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(e0._jsonable(record), ensure_ascii=False) + "\n")
        return exposure

    e0._make_config = make_config
    e0._exposure_line = exposure_line
    started = time.perf_counter()
    try:
        status = e0._execute(_e0_args(args, run_dir), run_dir)
    finally:
        e0._make_config = original_make_config
        e0._exposure_line = original_exposure_line
    wall = time.perf_counter() - started

    measurer = state["measurer"]
    labels_path = run_dir / "probe_labels.npz"
    label_shapes = measurer.save_arrays(labels_path) if measurer is not None else None
    derived = summarise_probe_records(state["records"], int(args.rollouts))
    if label_shapes is not None:
        variance = probe_value_variance_over_window(labels_path, int(args.rollouts))
        if variance is not None:
            derived["value_variance_across_rollouts"] = variance

    e1_block = {
        "contract": CONTRACT,
        "claim_ceiling": "B (EXPLORE)",
        "runner": "scripts/run_flexible_skill_duration_e1.py",
        "arm": args.arm,
        "age_feature": "normalized" if args.arm == "d1" else "off",
        "seed": int(args.seed),
        "rollouts": int(args.rollouts),
        "num_envs": int(args.num_envs),
        "torch_num_threads": int(args.threads),
        "launch_commit": args.launch_commit,
        "worktree_branch": e0._git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_branch_sha": e0._git("rev-parse", "HEAD"),
        "probe_set": {
            "path": str(Path(args.probe_set).resolve()),
            "content_sha256": probe_digest,
            "expected_content_sha256": args.probe_set_sha256,
            "n_probes": int(probes["team_skills"].shape[0]),
            "shapes": {k: list(np.asarray(probes[k]).shape) for k in PROBE_ARRAY_KEYS},
            "age_input": "(env_step mod 10) / 10, used for both the team and the agent age",
        },
        "probe_labels_npz": str(labels_path) if label_shapes else None,
        "probe_labels_shapes": label_shapes,
        "probe_metrics_jsonl": str(probe_metrics_path),
        "probe_measurement_rollouts": len(state["records"]),
        "probe_measurement_wall_seconds": float(
            sum(r["measure_wall_seconds"] for r in state["records"])),
        "derived": derived,
        "smoke": bool(args.smoke),
        "e1_wall_seconds": wall,
    }

    for name in ("manifest.json", "summary.json"):
        path = run_dir / name
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["e1"] = e0._jsonable(e1_block)
            path.write_text(json.dumps(e0._jsonable(payload), indent=2, ensure_ascii=False),
                            encoding="utf-8")

    (run_dir / "e1_probe_summary.json").write_text(
        json.dumps(e0._jsonable(e1_block), indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(e0._jsonable({
        "e1_arm": args.arm,
        "age_feature": e1_block["age_feature"],
        "seed": int(args.seed),
        "rollouts": int(args.rollouts),
        "num_envs": int(args.num_envs),
        "e0_status": int(status),
        "probe_measurement_rollouts": len(state["records"]),
        "probe_set_content_sha256": probe_digest,
        "team_accuracy_final": derived.get("team_accuracy_final"),
        "individual_accuracy_final": derived.get("individual_accuracy_final"),
        "team_label_agreement_mean_window": derived.get("team_label_agreement_mean_window"),
        "individual_label_agreement_mean_window": derived.get(
            "individual_label_agreement_mean_window"),
        "age_weight_share_final": derived.get("age_weight_share_final"),
        "e1_wall_seconds": wall,
        "run_dir": str(run_dir),
    }), ensure_ascii=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
