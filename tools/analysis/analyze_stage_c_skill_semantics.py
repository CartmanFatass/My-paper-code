"""Read-only, checkpoint-local Stage C skill-semantics audit helpers.

This module performs only registered offline reads.  Its CLI creates one new
JSON result and refuses to replace an existing destination.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
import math
from pathlib import Path
import argparse
import random
import sys
from typing import Any, Callable, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch


DELTA = 1.0 / 12.0
DELTA_STRATUM = 1.0 / 24.0
LINEAGE_THRESHOLD = math.log(1.2)

REQUIRED_SOURCE_M0 = frozenset(
    {
        "formal_contract_exact",
        "environment_steps_exact",
        "high_optimizer_steps_exact",
        "low_optimizer_steps_exact",
        "training_ledger_ids_exact",
        "zero_evaluation_exact",
        "final_evaluation_exact",
        "forced_audit_exact",
        "intrinsic_reward_and_count_zero",
        "sampling_replay_probability",
        "sampling_replay_value",
        "natural_probability_read_replay",
        "all_updates_finite",
        "final_parameters_finite",
        "parameter_update_nonzero",
        "strict_vector_schema3_resume",
        "f0_common_support_reduction",
    }
)

EVIDENCE_AVAILABILITY = {
    "fixed_input_rows": True,
    "all_skill_categorical_distributions": True,
    "policy_lineage_final_log_probabilities": True,
    "forced_aggregate_action_signatures": True,
    "natural_observation": True,
    "natural_recurrent_state": True,
    "natural_lifecycle_context": True,
    "forced_snapshot_observation": False,
    "forced_snapshot_recurrent_state": False,
    "forced_snapshot_lifecycle_metadata": False,
    "forced_snapshot_legal_support": False,
    "forced_snapshot_source_episode": False,
    "forced_nuisance_strata": False,
    "forced_per_stratum_support": False,
    "natural_source_episode": False,
    "forced_natural_shared_key": False,
    "natural_forced_alignment": False,
    "natural_common_support": False,
    "natural_endpoint_window_support": False,
}


def load_audit_inputs(result_path: str | Path, checkpoint_path: str | Path) -> dict[str, Any]:
    """Load offline sources and reconstruct the final actor without RNG mutation."""
    rng_state = _global_rng_snapshot()
    try:
        with Path(result_path).open("r", encoding="utf-8") as handle:
            result = json.load(handle)
        checkpoint = torch.load(
            Path(checkpoint_path), map_location="cpu", weights_only=False
        )
        actor = _actor_from_checkpoint(checkpoint)
    finally:
        _restore_global_rng(rng_state)
    return {"result": result, "checkpoint": checkpoint, "actor": actor}


def counterfactual_action_distributions(actor: Any, rows: Sequence[Mapping[str, Any]]) -> np.ndarray:
    """Evaluate all skills at fixed stored observations and hidden states."""
    if not rows:
        return np.empty((0, 3, 3), dtype=np.float64)
    observations = torch.as_tensor(
        np.stack([row["observation"] for row in rows]), dtype=torch.float32
    )
    hidden = torch.as_tensor(
        np.stack([row["actor_hidden_before"] for row in rows]), dtype=torch.float32
    )
    row_count = observations.shape[0]
    expanded_observations = observations.repeat_interleave(3, dim=0).to(actor.device)
    expanded_hidden = hidden.repeat_interleave(3, dim=0).to(actor.device)
    skills = torch.arange(3, dtype=torch.long).repeat(row_count).to(actor.device)
    with torch.no_grad():
        features = actor._features(expanded_observations, skills)
        features, _ = actor.actor_rnn(
            features,
            expanded_hidden,
            torch.ones(row_count * 3, 1, device=actor.device),
        )
        probabilities = (
            actor.actor_act.action_out(features)
            .probs.detach()
            .cpu()
            .numpy()
            .astype(np.float64, copy=True)
        )
    return probabilities.reshape(row_count, 3, 3)


def reconstruct_context_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Derive lifecycle nuisance context without retaining prohibited task fields."""
    permitted = ("episode", "lifecycle_key", "membership_epoch", "physical_time", "skill", "active_n")
    ordered = sorted(rows, key=lambda row: (row["episode"], row["lifecycle_key"], row["physical_time"]))
    ages: dict[tuple[Any, Any], int] = defaultdict(int)
    previous_skill: dict[tuple[Any, Any], int] = {}
    skill_duration: dict[tuple[Any, Any], int] = defaultdict(int)
    epoch_steps: dict[tuple[Any, Any, Any], int] = defaultdict(int)
    contexts: list[dict[str, Any]] = []
    for row in ordered:
        key = (row["episode"], row["lifecycle_key"])
        epoch_key = (*key, row["membership_epoch"])
        skill = int(row["skill"])
        if key in previous_skill and previous_skill[key] != skill:
            ages[key] = 0
            skill_duration[key] = 0
        age = ages[key]
        duration = skill_duration[key] + 1
        context = {name: row[name] for name in permitted}
        context.update(
            active_age=age,
            age_bin="0..9" if age < 10 else "10..19" if age < 20 else ">=20",
            entry=epoch_steps[epoch_key] < 10,
            active_n_bin=str(row["active_n"]),
            active_duration=duration,
            duration_bin="1..9" if duration < 10 else "10..19" if duration < 20 else ">=20",
        )
        contexts.append(context)
        ages[key] += 1
        epoch_steps[epoch_key] += 1
        previous_skill[key] = skill
        skill_duration[key] = duration
    return contexts


def forced_action_signatures(effect_rows: np.ndarray) -> np.ndarray:
    """Convert the two registered forced effects to three-action occupancies."""
    values = np.asarray(effect_rows, dtype=np.float64)
    if values.shape != (128, 3, 2, 4):
        raise ValueError("forced effects must have registered shape [128,3,2,4]")
    # The frozen evidence boundary permits precisely these two dimensions.
    values = values[..., :2]
    signatures = np.concatenate((values, 1.0 - values.sum(axis=-1, keepdims=True)), axis=-1)
    if not np.isfinite(signatures).all() or (signatures < 0).any():
        raise ValueError("forced action occupancy simplex is invalid")
    return signatures


def natural_segments(rows: Sequence[Mapping[str, Any]], actor: Any | None = None) -> list[dict[str, Any]]:
    """Return one capped, equally weighted window per constant natural context."""
    keys = ("episode", "lifecycle_key", "membership_epoch", "skill", "active_n")
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: (item["episode"], item["lifecycle_key"], item["physical_time"])):
        groups[tuple(row[name] for name in keys)].append(row)
    segments = []
    for key, group in groups.items():
        consecutive: list[Mapping[str, Any]] = []
        previous_time: int | None = None
        for row in group:
            if previous_time is not None and row["physical_time"] != previous_time + 1:
                if len(consecutive) >= 12:
                    segments.append(_natural_window(key, consecutive[:12], actor))
                consecutive = []
            consecutive.append(row)
            previous_time = int(row["physical_time"])
        if len(consecutive) >= 12:
            segments.append(_natural_window(key, consecutive[:12], actor))
    return segments


def _natural_window(key: tuple[Any, ...], rows: list[Mapping[str, Any]], actor: Any | None) -> dict[str, Any]:
    window = {"episode": key[0], "skill": key[3], "rows": rows, "weight": 1.0}
    if actor is not None:
        probabilities = _recurrent_window_probabilities(actor, rows, int(key[3]))
        window["signature"] = probabilities.mean(axis=0).tolist()
    return window


def _recurrent_window_probabilities(actor: Any, rows: Sequence[Mapping[str, Any]], skill: int) -> np.ndarray:
    hidden = torch.as_tensor(rows[0]["actor_hidden_before"], dtype=torch.float32).reshape(1, -1)
    probabilities = []
    with torch.no_grad():
        for row in rows:
            observation = torch.as_tensor(row["observation"], dtype=torch.float32).reshape(1, -1).to(actor.device)
            skills = torch.tensor([skill], dtype=torch.long, device=actor.device)
            features = actor._features(observation, skills)
            features, hidden = actor.actor_rnn(features, hidden.to(actor.device), torch.ones(1, 1, device=actor.device))
            probabilities.append(actor.actor_act.action_out(features).probs.detach().cpu().numpy()[0].copy())
    return np.asarray(probabilities, dtype=np.float64)


def cluster_bootstrap_ci(
    rows: Sequence[Mapping[str, Any]], *, value_key: str, repetitions: int = 10_000, seed: int = 307057
) -> tuple[float, float, float]:
    """Episode-clustered bootstrap CI using only a local PCG64 generator."""
    by_episode: dict[Any, list[float]] = defaultdict(list)
    for row in rows:
        by_episode[row["episode"]].append(float(row[value_key]))
    episode_means = np.asarray([np.mean(values) for values in by_episode.values()], dtype=np.float64)
    if not len(episode_means):
        raise ValueError("cluster bootstrap requires at least one episode")
    generator = np.random.Generator(np.random.PCG64(seed))
    sampled = generator.choice(episode_means, size=(repetitions, len(episode_means)), replace=True).mean(axis=1)
    return (float(np.quantile(sampled, 0.025)), float(episode_means.mean()), float(np.quantile(sampled, 0.975)))


def matched_nulls(
    labels: Sequence[int], statistic: Callable[[np.ndarray], float], *, strata: Sequence[Any] | None = None,
    repetitions: int = 10_000, seed: int = 307058
) -> np.ndarray:
    """Compute local-RNG label nulls, optionally shuffling only within strata."""
    generator = np.random.Generator(np.random.PCG64(seed))
    source = np.asarray(labels)
    groups: dict[Any, np.ndarray] = {}
    if strata is not None:
        for index, stratum in enumerate(strata):
            groups.setdefault(stratum, []).append(index)
        groups = {key: np.asarray(indices) for key, indices in groups.items()}
    draws = []
    for _ in range(repetitions):
        shuffled = source.copy()
        if groups:
            for indices in groups.values():
                shuffled[indices] = generator.permutation(source[indices])
        else:
            shuffled = generator.permutation(source)
        draws.append(statistic(shuffled))
    return np.asarray(draws, dtype=np.float64)


def decide_outcome(metrics: Mapping[str, Any]) -> str:
    """Apply the frozen mutually exclusive A--F result order."""
    required = {
        "validity_ok", "support_ok", "policy_lineage_ok", "all_pairs_exact_upper_below_delta",
        "all_pairs_forced_upper_below_delta", "frozen_pair_exact_ci", "frozen_pair_forced_ci",
        "stability_pooled_ci", "stability_stratum_cis", "natural_raw_ci",
        "natural_nuisance_ci", "natural_matched_margin_ci",
    }
    if not required.issubset(metrics):
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    if not metrics["validity_ok"]:
        return "INVALID_ITERATION3_AUDIT"
    if metrics["all_pairs_exact_upper_below_delta"] and metrics["all_pairs_forced_upper_below_delta"]:
        return "A_NO_MATERIAL_Z_DEPENDENCE"
    if not metrics["support_ok"] or not metrics["policy_lineage_ok"]:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    exact_low, exact_high = metrics["frozen_pair_exact_ci"]
    forced_low, forced_high = metrics["frozen_pair_forced_ci"]
    if exact_high < DELTA or forced_high < DELTA:
        return "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"
    if exact_low < DELTA or forced_low < DELTA:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    pooled_low, pooled_high = metrics["stability_pooled_ci"]
    if pooled_high < DELTA:
        return "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"
    if pooled_low < DELTA:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    for lower, upper in metrics["stability_stratum_cis"]:
        if upper <= 0 or upper < DELTA_STRATUM:
            return "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"
        if lower < DELTA_STRATUM:
            return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    raw_low, raw_high = metrics["natural_raw_ci"]
    if raw_high < DELTA:
        return "C_STABLE_FORCED_NO_NATURAL_OVERLAP"
    if raw_low < DELTA:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    nuisance_low, nuisance_high = metrics["natural_nuisance_ci"]
    matched_low, matched_high = metrics["natural_matched_margin_ci"]
    if nuisance_high <= 0 or matched_high <= 0:
        return "E_NUISANCE_SHORTCUT"
    if nuisance_low <= 0 or matched_low <= 0:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    return "D_STABLE_LOCAL_NATURAL_OVERLAP"


def _ci_rows(rows: Sequence[Mapping[str, Any]], key: str) -> tuple[float, float]:
    low, _, high = cluster_bootstrap_ci(rows, value_key=key)
    return low, high


def _source_identity(source: Mapping[str, Any]) -> str:
    return str(source.get("source_identity", source.get("result_path", "synthetic")))


def _global_rng_snapshot() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": deepcopy(np.random.get_state()),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else []
        ),
    }


def _numpy_rng_equal(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _global_rng_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        left["python"] == right["python"]
        and _numpy_rng_equal(left["numpy"], right["numpy"])
        and torch.equal(left["torch_cpu"], right["torch_cpu"])
        and len(left["torch_cuda"]) == len(right["torch_cuda"])
        and all(
            torch.equal(left_state, right_state)
            for left_state, right_state in zip(
                left["torch_cuda"], right["torch_cuda"]
            )
        )
    )


def _restore_global_rng(state: Mapping[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    if state["torch_cuda"]:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def _tensor_records(
    value: Any, path: tuple[Any, ...] = ()
) -> list[tuple[tuple[Any, ...], torch.Tensor]]:
    if isinstance(value, torch.Tensor):
        return [(path, value.detach().clone())]
    records: list[tuple[tuple[Any, ...], torch.Tensor]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(item, (torch.Tensor, Mapping, list, tuple)):
                records.extend(_tensor_records(item, (*path, key)))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            if isinstance(item, (torch.Tensor, Mapping, list, tuple)):
                records.extend(_tensor_records(item, (*path, index)))
    return records


def _path_value(value: Any, path: Sequence[Any]) -> Any:
    current = value
    for component in path:
        current = current[component]
    return current


def _tensors_unchanged(
    checkpoint: Mapping[str, Any],
    records: Sequence[tuple[tuple[Any, ...], torch.Tensor]],
) -> bool:
    try:
        current = _tensor_records(checkpoint)
        if [path for path, _ in current] != [path for path, _ in records]:
            return False
        return all(
            isinstance(_path_value(checkpoint, path), torch.Tensor)
            and torch.equal(_path_value(checkpoint, path), saved)
            for path, saved in records
        )
    except (KeyError, IndexError, TypeError):
        return False


def _actor_from_checkpoint(checkpoint: Mapping[str, Any]) -> Any:
    bundle = checkpoint["event_architecture"]
    header = bundle["architecture_state"]
    if not isinstance(header, Mapping):
        raise ValueError("checkpoint architecture header is malformed")
    if (
        int(header.get("n_skills", -1)) != 3
        or int(header.get("action_dim", -1)) != 3
        or str(header.get("action_space_type", "")) != "discrete"
        or int(header.get("obs_dim", 0)) <= 0
        or int(header.get("low_hidden_dim", 0)) <= 0
    ):
        raise ValueError("checkpoint low-actor architecture is incompatible")
    state = bundle.get("low_actor_state")
    if not isinstance(state, Mapping) or not state:
        raise ValueError("checkpoint low-actor state is missing")
    rng_state = _global_rng_snapshot()
    try:
        from ha_ctse_process.variable_roster_event_models import EventLowActor

        actor = EventLowActor(
            obs_dim=int(header["obs_dim"]),
            n_skills=3,
            action_dim=3,
            hidden_dim=int(header["low_hidden_dim"]),
            action_space_type="discrete",
            device="cpu",
        )
    finally:
        _restore_global_rng(rng_state)
    actor.load_state_dict(state, strict=True)
    if not all(torch.isfinite(parameter).all().item() for parameter in actor.parameters()):
        raise ValueError("checkpoint low-actor parameters are non-finite")
    actor.eval()
    return actor


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _extract_runtime_ledger(checkpoint: Mapping[str, Any]) -> list[Any]:
    bundle = checkpoint["event_architecture"]
    runtime_payloads = bundle.get("runtime_payloads")
    if not _is_sequence(runtime_payloads) or len(runtime_payloads) != 16:
        raise ValueError("checkpoint must contain runtime_payloads[16]")
    rows: list[Any] = []
    for environment_index, runtime_payload in enumerate(runtime_payloads):
        if not isinstance(runtime_payload, Mapping):
            raise ValueError("runtime payload is not a mapping")
        if runtime_payload.get("environment_index") != environment_index:
            raise ValueError("runtime environment indices are not canonical")
        ledger = runtime_payload.get("low_ledger")
        if not _is_sequence(ledger):
            raise ValueError("runtime low ledger is malformed")
        rows.extend(ledger)
    if len(rows) != 5_120:
        raise ValueError("checkpoint must contain exactly 5,120 low rows")
    return rows


def _row_value(row: Any, name: str) -> Any:
    if isinstance(row, Mapping):
        return row[name]
    return getattr(row, name)


def _integer_scalar(value: Any, name: str) -> int:
    array = np.asarray(value)
    if array.size != 1 or not np.issubdtype(array.dtype, np.number):
        raise ValueError(f"{name} must be one numeric scalar")
    scalar = float(array.reshape(-1)[0])
    if not np.isfinite(scalar) or scalar != int(scalar):
        raise ValueError(f"{name} must be one finite integer")
    return int(scalar)


def _allowed_rows(ledger: Sequence[Any], actor: Any) -> list[dict[str, Any]]:
    """Extract and validate only the registered non-task row fields."""
    rows = []
    for source_row in ledger:
        lifecycle_key = _row_value(source_row, "lifecycle_key")
        if not isinstance(lifecycle_key, str) or not lifecycle_key:
            raise ValueError("low row lifecycle key is malformed")
        membership_epoch = _integer_scalar(
            _row_value(source_row, "membership_epoch"), "membership_epoch"
        )
        physical_time = _integer_scalar(
            _row_value(source_row, "physical_time"), "physical_time"
        )
        skill = _integer_scalar(_row_value(source_row, "skill"), "skill")
        action_source = np.asarray(_row_value(source_row, "action"))
        if action_source.shape != (1,):
            raise ValueError("low row action must have exact shape [1]")
        action = _integer_scalar(action_source, "action")
        if skill not in (0, 1, 2) or action not in (0, 1, 2):
            raise ValueError("low row skill/action lies outside 0..2")
        observation = np.asarray(
            _row_value(source_row, "observation"), dtype=np.float32
        )
        hidden = np.asarray(
            _row_value(source_row, "actor_hidden_before"), dtype=np.float32
        )
        if observation.shape != (actor.obs_dim,) or not np.isfinite(observation).all():
            raise ValueError("low row observation shape/value is malformed")
        if hidden.shape != (actor.hidden_dim,) or not np.isfinite(hidden).all():
            raise ValueError("low row actor hidden shape/value is malformed")
        old_log_probability = float(
            _row_value(source_row, "old_log_probability")
        )
        if not np.isfinite(old_log_probability):
            raise ValueError("low row stored log probability is non-finite")
        rows.append(
            {
                "lifecycle_key": lifecycle_key,
                "membership_epoch": membership_epoch,
                "physical_time": physical_time,
                "observation": observation.copy(),
                "skill": skill,
                "action": action,
                "old_log_probability": old_log_probability,
                "actor_hidden_before": hidden.copy(),
            }
        )
    return rows


def _all_z_valid(distributions: np.ndarray, row_count: int) -> bool:
    return bool(
        distributions.shape == (row_count, 3, 3)
        and np.isfinite(distributions).all()
        and np.all(distributions > 0.0)
        and np.allclose(distributions.sum(axis=-1), 1.0, atol=1e-6, rtol=0.0)
    )


def _local_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    distributions: np.ndarray,
    signatures: np.ndarray,
) -> dict[str, Any]:
    pairs = {}
    for left in range(3):
        for right in range(left + 1, 3):
            pairs[f"{left}-{right}"] = float(
                np.mean(
                    0.5
                    * np.abs(distributions[:, left] - distributions[:, right]).sum(
                        axis=1
                    )
                )
            )
    indices = np.arange(len(rows), dtype=np.int64)
    skills = np.asarray([row["skill"] for row in rows], dtype=np.int64)
    actions = np.asarray([row["action"] for row in rows], dtype=np.int64)
    final_logp = np.log(distributions[indices, skills, actions])
    old_logp = np.asarray(
        [row["old_log_probability"] for row in rows], dtype=np.float64
    )
    lineage_p95 = float(np.quantile(np.abs(final_logp - old_logp), 0.95))
    return {
        "all_skill_tv_means": pairs,
        "forced_aggregate_signature_mean": signatures.mean(axis=(0, 2)).tolist(),
        "all_skill_distribution_shape": list(distributions.shape),
        "runtime_payload_count": 16,
        "runtime_low_row_count": len(rows),
        "policy_lineage_abs_delta_p95": lineage_p95,
        "policy_lineage_threshold": LINEAGE_THRESHOLD,
        "policy_lineage_ok": lineage_p95 <= LINEAGE_THRESHOLD,
    }


def _timing_grid_valid(result: Mapping[str, Any]) -> bool:
    rows = result.get("timing_rows")
    if not _is_sequence(rows) or len(rows) != 256 * 80:
        return False
    pairs = set()
    try:
        for row in rows:
            if not isinstance(row, Mapping):
                return False
            episode = _integer_scalar(row["episode_id"], "episode_id")
            physical_time = _integer_scalar(row["physical_time"], "physical_time")
            if not 0 <= episode < 256 or not 0 <= physical_time < 80:
                return False
            pairs.add((episode, physical_time))
    except (KeyError, TypeError, ValueError):
        return False
    return len(pairs) == 256 * 80


def _static_m0_checks(
    result: Mapping[str, Any], checkpoint: Mapping[str, Any], expected_arm: str
) -> dict[str, bool]:
    contract = result.get("contract")
    counts = result.get("counts")
    source_m0 = result.get("m0")
    bundle = checkpoint.get("event_architecture")
    counters = bundle.get("counters") if isinstance(bundle, Mapping) else None
    return {
        "result_schema": result.get("schema_version") == 1
        and result.get("stage") == "stage_c_paired_f0_f1",
        "arm_mode_and_implementation_valid": result.get("arm") == expected_arm
        and result.get("implementation_valid") is True,
        "source_m0_complete": isinstance(source_m0, Mapping)
        and REQUIRED_SOURCE_M0.issubset(source_m0)
        and all(value is True for value in source_m0.values()),
        "registered_result_contract": isinstance(contract, Mapping)
        and (
            contract.get("num_envs"),
            contract.get("outer_updates"),
            contract.get("environment_transitions"),
            contract.get("latent_skills"),
        )
        == (16, 250, 320_000, 3),
        "registered_result_counts": isinstance(counts, Mapping)
        and (
            counts.get("environment_steps"),
            counts.get("high_optimizer_steps"),
            counts.get("low_optimizer_steps"),
            counts.get("training_ledger_ids"),
            counts.get("intrinsic_applied_count"),
        )
        == (320_000, 1_000, 1_000, 4_000, 0),
        "checkpoint_schema3_vector": checkpoint.get("checkpoint_schema_version")
        == 3
        and checkpoint.get("high_controller") == "variable_roster_event"
        and isinstance(bundle, Mapping)
        and bundle.get("vector_checkpoint_schema_version") == 1
        and bundle.get("num_envs") == 16
        and bundle.get("runtime_state_absent_for_fresh_eval") is False
        and bundle.get("architecture_mode") == expected_arm
        and bundle.get("event_architecture_schema_version") == 1,
        "checkpoint_registered_counters": isinstance(counters, Mapping)
        and (
            counters.get("total_steps"),
            counters.get("update_idx"),
            counters.get("high_optimizer_steps"),
            counters.get("low_optimizer_steps"),
            counters.get("next_episode_id"),
            counters.get("intrinsic_applied_count"),
        )
        == (320_000, 250, 1_000, 1_000, 4_000, 0),
        "exact_timing_grid": _timing_grid_valid(result),
    }


def _analyze_arm(source: Mapping[str, Any], expected_arm: str) -> dict[str, Any]:
    identity = _source_identity(source)
    result = source.get("result", source)
    checkpoint = source.get("checkpoint")
    if not isinstance(result, Mapping) or not isinstance(checkpoint, Mapping):
        return {
            "identity": identity,
            "m0_valid": False,
            "m0_checks": {
                "result_mapping": isinstance(result, Mapping),
                "checkpoint_mapping": isinstance(checkpoint, Mapping),
            },
            "reasons": [
                name
                for name, ok in {
                    "result_not_mapping": isinstance(result, Mapping),
                    "checkpoint_not_mapping": isinstance(checkpoint, Mapping),
                }.items()
                if not ok
            ],
        }
    checks = _static_m0_checks(result, checkpoint, expected_arm)
    diagnostics: dict[str, Any] = {}
    availability: dict[str, bool] | None = None
    try:
        ledger = _extract_runtime_ledger(checkpoint)
        checks["runtime_payloads_and_low_row_count"] = True
    except (KeyError, TypeError, ValueError):
        ledger = []
        checks["runtime_payloads_and_low_row_count"] = False
    try:
        actor = _actor_from_checkpoint(checkpoint)
        checks["final_actor_strict_load"] = True
    except (KeyError, RuntimeError, TypeError, ValueError):
        actor = None
        checks["final_actor_strict_load"] = False
    if actor is not None and ledger:
        try:
            rows = _allowed_rows(ledger, actor)
            checks["allowed_row_schema_ranges_and_shapes"] = True
        except (AttributeError, KeyError, TypeError, ValueError):
            rows = []
            checks["allowed_row_schema_ranges_and_shapes"] = False
    else:
        rows = []
        checks["allowed_row_schema_ranges_and_shapes"] = False
    try:
        effects = result["forced_audit"]["effects"]
        signatures = forced_action_signatures(np.asarray(effects))
        checks["forced_shape_and_occupancy_simplex"] = True
    except (KeyError, TypeError, ValueError):
        signatures = np.empty((0, 3, 2, 3), dtype=np.float64)
        checks["forced_shape_and_occupancy_simplex"] = False
    if actor is not None and rows:
        try:
            distributions = counterfactual_action_distributions(actor, rows)
            checks["all_z_categorical_shape_support_and_simplex"] = _all_z_valid(
                distributions, len(rows)
            )
        except (RuntimeError, TypeError, ValueError):
            distributions = np.empty((0, 3, 3), dtype=np.float64)
            checks["all_z_categorical_shape_support_and_simplex"] = False
    else:
        distributions = np.empty((0, 3, 3), dtype=np.float64)
        checks["all_z_categorical_shape_support_and_simplex"] = False
    if all(checks.values()):
        diagnostics = _local_diagnostics(rows, distributions, signatures)
        availability = dict(EVIDENCE_AVAILABILITY)
    reasons = [f"m0:{name}" for name, ok in checks.items() if not ok]
    if availability is not None:
        reasons.extend(
            f"missing:{name}" for name, available in availability.items() if not available
        )
        if not diagnostics["policy_lineage_ok"]:
            reasons.append("policy_lineage_drift")
    return {
        "identity": identity,
        "m0_valid": all(checks.values()),
        "m0_checks": checks,
        "diagnostics": diagnostics,
        "evidence_availability": availability,
        "reasons": reasons,
    }


def _coerce_source(source: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        return source
    root = Path(source)
    loaded = load_audit_inputs(
        root / "result" / "stage_c_arm.json",
        root / "checkpoints" / "update_250_live.pt",
    )
    return {
        "result": loaded["result"],
        "checkpoint": loaded["checkpoint"],
        "source_identity": str(root),
    }


def _coerce_or_invalid(
    source: Mapping[str, Any] | str | Path,
) -> Mapping[str, Any]:
    try:
        return _coerce_source(source)
    except (FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError):
        return {
            "source_identity": str(source),
            "result": None,
            "checkpoint": None,
        }


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items() if key not in {"actor", "checkpoint"}}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return value


def run_audit(f0_source: Mapping[str, Any] | str | Path, f1_source: Mapping[str, Any] | str | Path, *, output_path: str | Path | None = None) -> dict[str, Any]:
    """Derive both diagnostics, selecting only F1 for the scientific outcome."""
    destination = Path(output_path) if output_path is not None else None
    if destination is not None and destination.exists():
        raise FileExistsError("audit result path already exists")
    rng_before = _global_rng_snapshot()
    try:
        sources = {
            "f0": _coerce_or_invalid(f0_source),
            "f1": _coerce_or_invalid(f1_source),
        }
        tensor_records = {
            name: (
                _tensor_records(source["checkpoint"])
                if isinstance(source.get("checkpoint"), Mapping)
                else []
            )
            for name, source in sources.items()
        }
        arms = {
            "f0": _analyze_arm(sources["f0"], "f0"),
            "f1": _analyze_arm(sources["f1"], "f1"),
        }
        rng_unchanged = _global_rng_equal(rng_before, _global_rng_snapshot())
        for name, arm in arms.items():
            checkpoint = sources[name].get("checkpoint")
            tensors_unchanged = isinstance(checkpoint, Mapping) and _tensors_unchanged(
                checkpoint, tensor_records[name]
            )
            arm["m0_checks"]["global_python_numpy_cpu_cuda_rng_unchanged"] = (
                rng_unchanged
            )
            arm["m0_checks"]["checkpoint_tensors_unchanged"] = tensors_unchanged
            arm["m0_valid"] = all(arm["m0_checks"].values())
            arm["reasons"] = [
                reason
                for reason in arm["reasons"]
                if not reason.startswith("m0:global_")
                and reason != "m0:checkpoint_tensors_unchanged"
            ]
            arm["reasons"].extend(
                f"m0:{check}"
                for check in (
                    "global_python_numpy_cpu_cuda_rng_unchanged",
                    "checkpoint_tensors_unchanged",
                )
                if not arm["m0_checks"][check]
            )
        outcome = (
            "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
            if arms["f0"]["m0_valid"] and arms["f1"]["m0_valid"]
            else "INVALID_ITERATION3_AUDIT"
        )
        payload = _json_safe(
            {
                "selector_arm": "f1",
                "f1_outcome": outcome,
                "source_identity": {
                    "f0": arms["f0"]["identity"],
                    "f1": arms["f1"]["identity"],
                },
                "m0": {
                    name: {
                        "valid": arm["m0_valid"],
                        "checks": arm["m0_checks"],
                        "reasons": [
                            reason
                            for reason in arm["reasons"]
                            if reason.startswith("m0:")
                        ],
                    }
                    for name, arm in arms.items()
                },
                "diagnostics": arms,
                "uncertainty_and_support": {
                    name: arm["reasons"] for name, arm in arms.items()
                },
                "evidence_ceiling": "checkpoint-local policy evidence only; no transfer, utility, credit, or hierarchy claim",
            }
        )
        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
        return payload
    finally:
        _restore_global_rng(rng_before)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Stage C checkpoint-local skill audit")
    parser.add_argument("--f0", required=True, help="F0 arm directory")
    parser.add_argument("--f1", required=True, help="F1 arm directory")
    parser.add_argument("--output", required=True, help="new JSON result path")
    arguments = parser.parse_args(argv)
    run_audit(arguments.f0, arguments.f1, output_path=arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
