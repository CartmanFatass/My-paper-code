"""Run the frozen R27-G1 low-actor capacity autopsy."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.low_actor_capacity_audit import (  # noqa: E402
    CapacitySnapshotBatch,
    SyntheticFitConfig,
    build_orthogonal_codebook,
    classify_capacity_autopsy,
    evaluate_static_checkpoint,
    evaluate_synthetic_seed,
    gate_static_family,
    gate_synthetic_family,
    grouped_reset_split,
    read_capacity_snapshot_shards,
    write_capacity_snapshot_shard,
)


@dataclass(frozen=True)
class SnapshotCollectorStats:
    resets: int
    renewal_events: int
    snapshot_rows: int


_RUNTIME_ATTRIBUTES = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "team_intent_remaining",
    "team_intent_age",
    "low_actor_hxs",
    "low_critic_hxs",
    "_last_low_context",
    "segments",
    "situation_debouncer",
    "per_agent_situation_debouncer",
    "situation_hazard_guard",
    "_last_situation_state",
    "_last_agent_situation_state",
    "_team_transition_open",
    "_team_transition_closed",
    "_team_transition_env_steps",
    "_team_intent_boundary_count",
    "_team_intent_boundary_trunc_fracs",
    "_team_intent_boundary_trunc_by_duration",
    "_team_intent_dwell_checks",
    "_team_intent_age_check_samples",
    "_situation_diag_events",
    "_agent_situation_diag_events",
    "_situation_hazard_forced_renewals",
    "_situation_hazard_events",
)


@contextmanager
def preserve_agent_runtime(agent: Any) -> Iterator[None]:
    """Restore mutable rollout state after a frozen reset collection."""

    missing = object()
    originals: dict[str, Any] = {}
    for name in _RUNTIME_ATTRIBUTES:
        value = getattr(agent, name, missing)
        if value is not missing:
            originals[name] = value
    for name, value in copy.deepcopy(originals).items():
        setattr(agent, name, value)
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(agent, name, value)


def require_cuda_device(device: str) -> torch.device:
    requested = str(device).strip().lower()
    if requested != "cuda" and not requested.startswith("cuda:"):
        raise ValueError("R27-G1 scientific audit requires --device cuda")
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested for R27-G1 but is unavailable; CPU fallback is forbidden"
        )
    return torch.device(requested)


def _state_from_info(info: Any, previous: Any = None) -> np.ndarray | None:
    mapping = info if isinstance(info, dict) else {}
    state = mapping.get("next_state", mapping.get("state", previous))
    if state is None:
        return None
    return np.asarray(state, dtype=np.float32).reshape(-1)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def policy_parameter_sha256(agent: Any) -> str:
    digest = hashlib.sha256()
    seen_modules: set[int] = set()
    for attribute, value in sorted(vars(agent).items()):
        if not isinstance(value, torch.nn.Module) or id(value) in seen_modules:
            continue
        seen_modules.add(id(value))
        for name, parameter in sorted(value.named_parameters()):
            tensor = parameter.detach().cpu().contiguous()
            digest.update(f"{attribute}.{name}".encode("utf-8"))
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(np.asarray(tensor.shape, dtype=np.int64).tobytes())
            digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _set_eval_mode(agent: Any) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if isinstance(value, torch.nn.Module) and id(value) not in seen:
            seen.add(id(value))
            value.eval()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    Path(path).write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rows_to_batch(
    rows: list[dict[str, Any]],
    *,
    observation_dim: int,
    hidden_dim: int,
) -> CapacitySnapshotBatch:
    if not rows:
        return CapacitySnapshotBatch(
            observation=np.zeros((0, int(observation_dim)), dtype=np.float32),
            actor_hidden=np.zeros((0, int(hidden_dim)), dtype=np.float32),
            natural_skill=np.zeros(0, dtype=np.int64),
            previous_skill=np.zeros(0, dtype=np.int64),
            duration_idx=np.zeros(0, dtype=np.int64),
            skill_age=np.zeros(0, dtype=np.int64),
            episode_done_mask=np.zeros(0, dtype=np.bool_),
            reset_id=np.zeros(0, dtype=np.int64),
            reset_seed=np.zeros(0, dtype=np.int64),
            episode_id=np.zeros(0, dtype=np.int64),
            env_id=np.zeros(0, dtype=np.int64),
            agent_id=np.zeros(0, dtype=np.int64),
            checkpoint_id=np.zeros(0, dtype=np.str_),
            checkpoint_update=np.zeros(0, dtype=np.int64),
        )
    return CapacitySnapshotBatch(
        observation=np.stack([row["observation"] for row in rows]).astype(
            np.float32
        ),
        actor_hidden=np.stack([row["actor_hidden"] for row in rows]).astype(
            np.float32
        ),
        natural_skill=np.asarray(
            [row["natural_skill"] for row in rows], dtype=np.int64
        ),
        previous_skill=np.asarray(
            [row["previous_skill"] for row in rows], dtype=np.int64
        ),
        duration_idx=np.asarray(
            [row["duration_idx"] for row in rows], dtype=np.int64
        ),
        skill_age=np.asarray([row["skill_age"] for row in rows], dtype=np.int64),
        episode_done_mask=np.asarray(
            [row["episode_done_mask"] for row in rows], dtype=np.bool_
        ),
        reset_id=np.asarray([row["reset_id"] for row in rows], dtype=np.int64),
        reset_seed=np.asarray(
            [row["reset_seed"] for row in rows], dtype=np.int64
        ),
        episode_id=np.asarray(
            [row["episode_id"] for row in rows], dtype=np.int64
        ),
        env_id=np.asarray([row["env_id"] for row in rows], dtype=np.int64),
        agent_id=np.asarray([row["agent_id"] for row in rows], dtype=np.int64),
        checkpoint_id=np.asarray(
            [row["checkpoint_id"] for row in rows], dtype=np.str_
        ),
        checkpoint_update=np.asarray(
            [row["checkpoint_update"] for row in rows], dtype=np.int64
        ),
    )


def collect_capacity_reset(
    env: Any,
    agent: Any,
    *,
    reset_id: int,
    reset_seed: int,
    episode_id: int,
    skill_interval: int,
    episode_max_steps: int,
    checkpoint_id: str,
    checkpoint_update: int,
) -> tuple[CapacitySnapshotBatch, SnapshotCollectorStats]:
    """Collect natural renewal snapshots without retaining runtime mutation."""

    if int(skill_interval) <= 0 or int(episode_max_steps) <= 0:
        raise ValueError("skill_interval and episode_max_steps must be positive")
    rows: list[dict[str, Any]] = []
    renewals = 0
    with preserve_agent_runtime(agent):
        obs, info = env.reset(seed=int(reset_seed))
        obs = np.asarray(obs, dtype=np.float32)
        if obs.ndim != 2 or int(obs.shape[0]) != int(agent.n_agents):
            raise ValueError("environment observation must have one row per agent")
        state = _state_from_info(info)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(int(agent.n_agents))]

        observation_dim = int(obs.shape[1])
        hidden_dim = int(np.asarray(agent.low_actor_hxs[0, 0]).size)
        for step in range(int(episode_max_steps)):
            previous_segments = list(agent.segments.active[0])
            pre_assignment_hidden = np.asarray(
                agent.low_actor_hxs[0], dtype=np.float32
            ).copy()
            with torch.no_grad():
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=int(step),
                    k=int(skill_interval),
                    env_id=0,
                    deterministic=False,
                )
            current_segments = list(agent.segments.active[0])
            changed = [
                agent_id
                for agent_id, (before, after) in enumerate(
                    zip(previous_segments, current_segments)
                )
                if after is not None and after is not before
            ]
            for agent_id in changed:
                renewals += 1
                segment = current_segments[agent_id]
                rows.append(
                    {
                        "observation": np.asarray(
                            obs[agent_id], dtype=np.float32
                        ).copy(),
                        "actor_hidden": pre_assignment_hidden[agent_id].copy(),
                        "natural_skill": int(segment.skill),
                        "previous_skill": int(getattr(segment, "prev_skill", 0)),
                        "duration_idx": int(segment.duration_idx),
                        "skill_age": int(getattr(segment, "skill_age_prev", 0)),
                        "episode_done_mask": False,
                        "reset_id": int(reset_id),
                        "reset_seed": int(reset_seed),
                        "episode_id": int(episode_id),
                        "env_id": 0,
                        "agent_id": int(agent_id),
                        "checkpoint_id": str(checkpoint_id),
                        "checkpoint_update": int(checkpoint_update),
                    }
                )
            with torch.no_grad():
                actions, _, _ = agent.act_low(
                    obs,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
            next_obs, _reward, terminated, truncated, next_info = env.step(
                actions
            )
            obs = np.asarray(next_obs, dtype=np.float32)
            state = _state_from_info(next_info, previous=state)
            if bool(terminated or truncated):
                break

    batch = _rows_to_batch(
        rows, observation_dim=observation_dim, hidden_dim=hidden_dim
    )
    return batch, SnapshotCollectorStats(
        resets=1, renewal_events=renewals, snapshot_rows=len(rows)
    )


def _configure_agent(args: argparse.Namespace):
    from ha_ctse_process import train as train_mod

    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, args, metadata)
    if int(args.n_agents) > 0 and metadata.get("n_agents") is None:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    env = train_mod.create_env(
        config, config.scenario, int(args.seed), rank=0, scale_mode="eval"
    )
    _obs, info = env.reset(seed=int(args.seed))
    state = _state_from_info(info)
    agent = train_mod.create_agent(
        config,
        args,
        env,
        num_envs=1,
        state_dim=None if state is None else int(state.size),
    )
    _total_steps, loaded_update = train_mod.load_checkpoint(
        args.checkpoint, agent, load_optimizers=False
    )
    _set_eval_mode(agent)
    return config, metadata, env, agent, int(loaded_update)


def _static_markdown(report: dict[str, object]) -> str:
    zero = report.get("zero_h", {})
    rollout = report.get("rollout_h", {})
    inactive = report.get("inactive_control", {})
    parity = report.get("parity", {})
    return "\n".join(
        [
            f"# R27 Static Capacity: {report.get('checkpoint_id', '')}",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Snapshot rows: {report.get('rows', 0)}",
            f"- Zero-h symmetric KL: {zero.get('mean_skl', 'n/a')}",
            f"- Zero-h standardized mean distance: {zero.get('mean_stdmean_distance', 'n/a')}",
            f"- Rollout-h symmetric KL: {rollout.get('mean_skl', 'n/a')}",
            f"- Rollout-h standardized mean distance: {rollout.get('mean_stdmean_distance', 'n/a')}",
            f"- Hidden retention ratio: {report.get('hidden_retention_ratio', 'n/a')}",
            f"- Inactive maximum symmetric KL: {inactive.get('max_abs_symmetric_kl', 'n/a')}",
            f"- Live parity: {parity.get('pass', False)}",
            "",
            "## Fixed Gates",
            "",
            "- symmetric KL >= 0.02 nats",
            "- standardized action-mean distance >= 0.20",
            "- reset-cluster bootstrap lower bound > 0",
            "- inactive identity separation <= 1e-8",
            "",
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward is authorized by this checkpoint read.",
            "",
        ]
    )


def run_collect_static(args: argparse.Namespace) -> dict[str, object]:
    require_cuda_device(args.device)
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir = output_dir / "capacity_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    torch.cuda.manual_seed_all(int(args.seed))
    config, metadata, env, agent, loaded_update = _configure_agent(args)
    checkpoint_id = str(args.checkpoint_id or checkpoint.stem)
    checkpoint_update = (
        int(args.checkpoint_update)
        if args.checkpoint_update is not None
        else int(metadata.get("update_idx") or loaded_update)
    )
    file_hash_before = _file_sha256(checkpoint)
    parameter_hash_before = policy_parameter_sha256(agent)
    reset_seeds: list[int] = []
    totals = SnapshotCollectorStats(0, 0, 0)
    try:
        for reset_id in range(int(args.n_resets)):
            reset_seed = int(args.seed) + reset_id
            reset_seeds.append(reset_seed)
            batch, stats = collect_capacity_reset(
                env,
                agent,
                reset_id=reset_id,
                reset_seed=reset_seed,
                episode_id=reset_id,
                skill_interval=int(args.skill_interval),
                episode_max_steps=int(args.episode_max_steps),
                checkpoint_id=checkpoint_id,
                checkpoint_update=checkpoint_update,
            )
            write_capacity_snapshot_shard(
                snapshot_dir / f"reset_{reset_id:04d}.npz", batch
            )
            totals = SnapshotCollectorStats(
                resets=totals.resets + stats.resets,
                renewal_events=totals.renewal_events + stats.renewal_events,
                snapshot_rows=totals.snapshot_rows + stats.snapshot_rows,
            )
        snapshots = read_capacity_snapshot_shards(snapshot_dir)
        static_report = evaluate_static_checkpoint(
            agent.low,
            snapshots,
            checkpoint_id=checkpoint_id,
            bootstrap_reps=int(args.bootstrap_reps),
            bootstrap_seed=int(args.bootstrap_seed),
        )
    finally:
        env.close()

    file_hash_after = _file_sha256(checkpoint)
    parameter_hash_after = policy_parameter_sha256(agent)
    immutable = bool(
        file_hash_before == file_hash_after
        and parameter_hash_before == parameter_hash_after
    )
    if not immutable:
        static_report = dict(static_report)
        static_report["status"] = "INVALID"
        static_report["immutability_failure"] = True
    manifest: dict[str, object] = {
        "status": static_report.get("status"),
        "checkpoint": str(checkpoint),
        "checkpoint_id": checkpoint_id,
        "checkpoint_update": checkpoint_update,
        "checkpoint_sha256_before": file_hash_before,
        "checkpoint_sha256_after": file_hash_after,
        "checkpoint_sha256_equal": file_hash_before == file_hash_after,
        "policy_parameter_sha256_before": parameter_hash_before,
        "policy_parameter_sha256_after": parameter_hash_after,
        "policy_parameter_sha256_equal": parameter_hash_before
        == parameter_hash_after,
        "checkpoint_metadata": _jsonable(metadata),
        "parameter_counts": _jsonable(agent.parameter_counts()),
        "device": str(args.device),
        "n_resets": int(args.n_resets),
        "reset_seeds": reset_seeds,
        "stats": asdict(totals),
        "field_names": list(CapacitySnapshotBatch.__dataclass_fields__),
        "observation_dim": int(snapshots.observation.shape[1]),
        "hidden_dim": int(snapshots.actor_hidden.shape[1]),
        "config_scenario": str(config.scenario),
    }
    _write_json(output_dir / "collector_manifest.json", manifest)
    _write_json(output_dir / "static_capacity.json", static_report)
    (output_dir / "static_capacity.md").write_text(
        _static_markdown(static_report), encoding="utf-8"
    )
    if not immutable:
        raise RuntimeError("source checkpoint or policy parameters changed")
    return {"manifest": manifest, "static": static_report}


def _synthetic_markdown(report: dict[str, object]) -> str:
    lines = [
        "# R27 Synthetic Capacity Control",
        "",
        f"- Family status: `{report.get('status')}`",
        f"- Passing seeds: {report.get('passing_seeds', 0)}",
        f"- Failed seeds: {report.get('failed_seeds', 0)}",
        "",
        "## Fixed Gates",
        "",
        "- active accuracy and macro-F1 >= 0.90",
        "- active minus sham accuracy >= 0.50",
        "- sham accuracy <= 0.35",
        "- train minus test accuracy <= 0.20",
        "",
    ]
    for seed_report in report.get("seed_reports", []):
        lines.extend(
            [
                f"### Seed {seed_report['seed']}",
                "",
                f"- status: `{seed_report['status']}`",
                f"- active accuracy: {seed_report['synthetic_code_accuracy']}",
                f"- sham accuracy: {seed_report['sham_accuracy']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward is authorized before final classification review.",
            "",
        ]
    )
    return "\n".join(lines)


def run_synthetic(args: argparse.Namespace) -> dict[str, object]:
    device = require_cuda_device(args.device)
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    snapshot_dir = Path(args.snapshot_dir)
    snapshots = read_capacity_snapshot_shards(snapshot_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config, metadata, env, agent, loaded_update = _configure_agent(args)
    del config, metadata, loaded_update
    file_hash_before = _file_sha256(checkpoint)
    parameter_hash_before = policy_parameter_sha256(agent)
    try:
        split = grouped_reset_split(snapshots.reset_id, seed=int(args.split_seed))
        codebook = build_orthogonal_codebook(
            int(agent.low.n_skills),
            int(agent.low.action_dim),
            seed=int(args.codebook_seed),
            norm=0.5,
        )
        fit_config = SyntheticFitConfig(
            learning_rate=float(args.learning_rate),
            batch_size=int(args.batch_size),
            max_steps=int(args.max_steps),
            validation_interval=int(args.validation_interval),
            patience=int(args.patience),
            min_delta=float(args.min_delta),
        )
        seed_reports = [
            evaluate_synthetic_seed(
                agent.low,
                snapshots,
                split,
                codebook,
                seed=int(seed),
                config=fit_config,
                device=device,
                bootstrap_reps=int(args.bootstrap_reps),
            )
            for seed in args.synthetic_seeds
        ]
        family = gate_synthetic_family(seed_reports)
    finally:
        env.close()

    file_hash_after = _file_sha256(checkpoint)
    parameter_hash_after = policy_parameter_sha256(agent)
    immutable = bool(
        file_hash_before == file_hash_after
        and parameter_hash_before == parameter_hash_after
    )
    if not immutable:
        family = dict(family)
        family["status"] = "INVALID"
        family["pass"] = False
    report: dict[str, object] = {
        **family,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256_before": file_hash_before,
        "checkpoint_sha256_after": file_hash_after,
        "checkpoint_sha256_equal": file_hash_before == file_hash_after,
        "policy_parameter_sha256_before": parameter_hash_before,
        "policy_parameter_sha256_after": parameter_hash_after,
        "policy_parameter_sha256_equal": parameter_hash_before
        == parameter_hash_after,
        "device": str(args.device),
        "split": {
            "train_reset_ids": list(split.train_reset_ids),
            "validation_reset_ids": list(split.validation_reset_ids),
            "test_reset_ids": list(split.test_reset_ids),
        },
        "codebook": codebook.tolist(),
        "codebook_norm": 0.5,
        "fit_config": asdict(fit_config),
        "seed_reports": seed_reports,
        "parameter_counts": _jsonable(agent.parameter_counts()),
    }
    _write_json(output_dir / "synthetic_control.json", report)
    (output_dir / "synthetic_control.md").write_text(
        _synthetic_markdown(report), encoding="utf-8"
    )
    if not immutable:
        raise RuntimeError("source checkpoint or policy parameters changed")
    return report


def _aggregate_markdown(report: dict[str, object]) -> str:
    return "\n".join(
        [
            "# R27-G1 Low-Actor Capacity Autopsy",
            "",
            f"- Classification: `{report['classification']}`",
            f"- Reasons: {'; '.join(report['reasons'])}",
            f"- Static family: `{report['static_family']['status']}`",
            f"- Synthetic family: `{report['synthetic_family']['status']}`",
            "",
            "## Decision Boundary",
            "",
            "This reward-off audit classifies the existing low-actor path; it does not change the algorithm.",
            "",
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward may be enabled before controller review of this classification.",
            "No actor redesign, hidden reset, or long training run is authorized by this file alone.",
            "",
        ]
    )


def run_aggregate(args: argparse.Namespace) -> dict[str, object]:
    run_root = Path(args.run_root)
    checkpoint_ids = [str(value) for value in args.checkpoint_ids]
    if checkpoint_ids != ["arm0_update25", "arm0_update30", "arm0_final"]:
        raise ValueError("aggregate requires exact arm0 update25/update30/final order")
    static_reports = [
        json.loads(
            (run_root / checkpoint_id / "static_capacity.json").read_text(
                encoding="utf-8"
            )
        )
        for checkpoint_id in checkpoint_ids
    ]
    synthetic_report = json.loads(
        (run_root / "synthetic_control.json").read_text(encoding="utf-8")
    )
    static_family = gate_static_family(static_reports)
    synthetic_family = {
        key: synthetic_report[key]
        for key in (
            "status",
            "pass",
            "passing_seeds",
            "failed_seeds",
        )
        if key in synthetic_report
    }
    classification = classify_capacity_autopsy(
        static_family, synthetic_family
    )
    result: dict[str, object] = {
        **classification,
        "checkpoint_ids": checkpoint_ids,
        "static_family": static_family,
        "synthetic_family": synthetic_family,
        "static_reports": static_reports,
        "synthetic_report": synthetic_report,
        "prohibited_next_actions": [
            "q_A/q_d/q_D or intrinsic reward",
            "actor redesign or hidden reset",
            "long training before classification review",
        ],
    }
    _write_json(run_root / "r27_capacity_autopsy.json", result)
    (run_root / "r27_capacity_autopsy.md").write_text(
        _aggregate_markdown(result), encoding="utf-8"
    )
    return result


def _add_checkpoint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n-agents", dest="n_agents", type=int, default=6)
    parser.add_argument("--device", default="cuda")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Frozen R27-G1 low-actor capacity autopsy"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect-static")
    _add_checkpoint_args(collect)
    collect.add_argument("--output-dir", required=True)
    collect.add_argument("--checkpoint-id", default="")
    collect.add_argument("--checkpoint-update", type=int, default=None)
    collect.add_argument("--skill-interval", type=int, default=10)
    collect.add_argument("--n-resets", type=int, default=64)
    collect.add_argument("--episode-max-steps", type=int, default=500)
    collect.add_argument("--bootstrap-reps", type=int, default=1000)
    collect.add_argument("--bootstrap-seed", type=int, default=27021)

    synthetic = subparsers.add_parser("synthetic")
    _add_checkpoint_args(synthetic)
    synthetic.add_argument("--snapshot-dir", required=True)
    synthetic.add_argument("--output-dir", required=True)
    synthetic.add_argument("--split-seed", type=int, default=27011)
    synthetic.add_argument("--codebook-seed", type=int, default=27030)
    synthetic.add_argument(
        "--synthetic-seeds", type=int, nargs="+", default=[17, 23, 41]
    )
    synthetic.add_argument("--learning-rate", type=float, default=3e-4)
    synthetic.add_argument("--batch-size", type=int, default=256)
    synthetic.add_argument("--max-steps", type=int, default=1000)
    synthetic.add_argument("--validation-interval", type=int, default=25)
    synthetic.add_argument("--patience", type=int, default=20)
    synthetic.add_argument("--min-delta", type=float, default=1e-4)
    synthetic.add_argument("--bootstrap-reps", type=int, default=1000)

    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--run-root", required=True)
    aggregate.add_argument("--checkpoint-ids", nargs="+", required=True)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    if args.command == "collect-static":
        result = run_collect_static(args)
    elif args.command == "synthetic":
        result = run_synthetic(args)
    else:
        result = run_aggregate(args)
    print(json.dumps(_jsonable(result), sort_keys=True))


if __name__ == "__main__":
    main()
