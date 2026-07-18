"""Read-only, checkpoint-local Stage C skill-semantics audit helpers.

This module deliberately performs no experiment I/O or result-file writes.  The
controller supplies validated inputs to :func:`run_audit` after the audit gate.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import torch


DELTA = 1.0 / 12.0
DELTA_STRATUM = 1.0 / 24.0


def load_audit_inputs(result_path: str | Path, checkpoint_path: str | Path) -> dict[str, Any]:
    """Load offline sources and reconstruct the final actor without RNG mutation."""
    import json
    from ha_ctse_process.variable_roster_event import EventLowActor

    with Path(result_path).open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    checkpoint = torch.load(Path(checkpoint_path), map_location="cpu", weights_only=False)
    bundle = checkpoint["event_architecture"]
    header = bundle["architecture_state"]
    rng_state = torch.get_rng_state()
    try:
        actor = EventLowActor(
            obs_dim=int(header["obs_dim"]),
            n_skills=int(header["n_skills"]),
            action_dim=int(header["action_dim"]),
            hidden_dim=int(header["low_hidden_dim"]),
            action_space_type=str(header.get("action_space_type", "discrete")),
            device="cpu",
        )
    finally:
        torch.set_rng_state(rng_state)
    actor.load_state_dict(bundle["low_actor_state"], strict=True)
    actor.eval()
    return {"result": result, "checkpoint": checkpoint, "actor": actor}


def counterfactual_action_distributions(actor: Any, rows: Sequence[Mapping[str, Any]]) -> np.ndarray:
    """Evaluate all skills at fixed stored observations and hidden states."""
    outputs: list[np.ndarray] = []
    with torch.no_grad():
        for row in rows:
            observation = torch.as_tensor(row["observation"], dtype=torch.float32).reshape(1, -1)
            hidden = torch.as_tensor(row["actor_hidden_before"], dtype=torch.float32).reshape(1, -1)
            row_outputs = []
            for skill in range(3):
                skills = torch.tensor([skill], dtype=torch.long)
                features = actor._features(observation.to(actor.device), skills.to(actor.device))
                features, _ = actor.actor_rnn(features, hidden.to(actor.device), torch.ones(1, 1, device=actor.device))
                row_outputs.append(actor.actor_act.action_out(features).probs.detach().cpu().numpy()[0].copy())
            outputs.append(np.asarray(row_outputs))
    return np.asarray(outputs)


def reconstruct_context_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Derive lifecycle nuisance context without retaining prohibited task fields."""
    permitted = ("episode", "lifecycle_key", "membership_epoch", "physical_time", "skill", "active_n")
    ordered = sorted(rows, key=lambda row: (row["episode"], row["lifecycle_key"], row["physical_time"]))
    ages: dict[tuple[Any, Any], int] = defaultdict(int)
    previous_skill: dict[tuple[Any, Any], int] = {}
    epoch_steps: dict[tuple[Any, Any, Any], int] = defaultdict(int)
    contexts: list[dict[str, Any]] = []
    for row in ordered:
        key = (row["episode"], row["lifecycle_key"])
        epoch_key = (*key, row["membership_epoch"])
        skill = int(row["skill"])
        if key in previous_skill and previous_skill[key] != skill:
            ages[key] = 0
        age = ages[key]
        context = {name: row[name] for name in permitted}
        context.update(
            active_age=age,
            age_bin="0..9" if age < 10 else "10..19" if age < 20 else ">=20",
            entry=epoch_steps[epoch_key] < 10,
            active_n_bin=str(row["active_n"]),
        )
        contexts.append(context)
        ages[key] += 1
        epoch_steps[epoch_key] += 1
        previous_skill[key] = skill
    return contexts


def forced_action_signatures(effect_rows: np.ndarray) -> np.ndarray:
    """Convert the two registered forced effects to three-action occupancies."""
    values = np.asarray(effect_rows, dtype=np.float64)
    if values.shape[-1] != 2:
        raise ValueError("forced effects must have final dimension 2")
    signatures = np.concatenate((values, 1.0 - values.sum(axis=-1, keepdims=True)), axis=-1)
    if not np.isfinite(signatures).all() or (signatures < 0).any():
        raise ValueError("forced action occupancy simplex is invalid")
    return signatures


def natural_segments(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
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
                    segments.append({"episode": key[0], "skill": key[3], "rows": consecutive[:12], "weight": 1.0})
                consecutive = []
            consecutive.append(row)
            previous_time = int(row["physical_time"])
        if len(consecutive) >= 12:
            segments.append({"episode": key[0], "skill": key[3], "rows": consecutive[:12], "weight": 1.0})
    return segments


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
    labels: Sequence[int], statistic: Callable[[np.ndarray], float], *, repetitions: int = 10_000, seed: int = 307058
) -> np.ndarray:
    """Compute matched-label null statistics from a local PCG64 shuffle stream."""
    generator = np.random.Generator(np.random.PCG64(seed))
    source = np.asarray(labels)
    return np.asarray([statistic(generator.permutation(source)) for _ in range(repetitions)], dtype=np.float64)


def decide_outcome(metrics: Mapping[str, Any]) -> str:
    """Apply the frozen mutually exclusive A--F result order."""
    if not metrics.get("validity_ok", True):
        return "INVALID_ITERATION3_AUDIT"
    if metrics["all_pairs_exact_upper_below_delta"] and metrics["all_pairs_forced_upper_below_delta"]:
        return "A_NO_MATERIAL_Z_DEPENDENCE"
    if not metrics.get("support_ok", True) or not metrics.get("policy_lineage_ok", True):
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    if metrics["frozen_pair_exact_lower"] < DELTA or metrics["frozen_pair_forced_lower"] < DELTA:
        return "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"
    if metrics["stability_has_reversal"] or any(value < DELTA_STRATUM for value in metrics["stability_stratum_lowers"]):
        return "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"
    if metrics["stability_pooled_lower"] < DELTA:
        return "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    if not metrics["natural_raw_pass"]:
        return "C_STABLE_FORCED_NO_NATURAL_OVERLAP"
    if metrics["natural_nuisance_lower"] <= 0 or metrics["natural_matched_margin"] <= 0:
        return "E_NUISANCE_SHORTCUT"
    return "D_STABLE_LOCAL_NATURAL_OVERLAP"


def run_audit(inputs: Mapping[str, Any], metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Return an in-memory audit disposition; persistence is controller-owned."""
    return {"outcome": decide_outcome(metrics), "inputs": dict(inputs), "metrics": dict(metrics)}
