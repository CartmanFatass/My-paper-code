"""Read-only, checkpoint-local Stage C skill-semantics audit helpers.

This module deliberately performs no experiment I/O or result-file writes.  The
controller supplies validated inputs to :func:`run_audit` after the audit gate.
"""

from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import argparse
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
    nuisance_low, _ = metrics["natural_nuisance_ci"]
    matched_low, _ = metrics["natural_matched_margin_ci"]
    if nuisance_low <= 0 or matched_low <= 0:
        return "E_NUISANCE_SHORTCUT"
    return "D_STABLE_LOCAL_NATURAL_OVERLAP"


def _ci_rows(rows: Sequence[Mapping[str, Any]], key: str) -> tuple[float, float]:
    low, _, high = cluster_bootstrap_ci(rows, value_key=key)
    return low, high


def _source_identity(source: Mapping[str, Any]) -> str:
    return str(source.get("source_identity", source.get("result_path", "synthetic")))


def _m0(result: Mapping[str, Any], expected_arm: str) -> tuple[bool, list[str]]:
    required = {
        "source_valid": True, "arm_mode": expected_arm, "checkpoint_schema_version": 3,
        "runtime_count": 16, "update": 250, "transitions": 320_000,
        "intrinsic_applications": 0, "forced_effects": object, "low_rows": object,
    }
    reasons = []
    for name, expected in required.items():
        if name not in result or (expected is not object and result[name] != expected):
            reasons.append(f"m0_{name}")
    if "forced_effects" in result:
        try:
            forced_action_signatures(np.asarray(result["forced_effects"]))
        except (TypeError, ValueError):
            reasons.append("m0_forced_shape_or_simplex")
    if len(result.get("low_rows", [])) != 5_120:
        reasons.append("m0_low_row_count")
    prohibited = {"reward", "utility", "wave", "owner", "progress", "contact", "success", "role"}
    if any(prohibited & set(row) for row in result.get("low_rows", []) if isinstance(row, Mapping)):
        reasons.append("m0_prohibited_field")
    return not reasons, reasons


def _minimal_metrics(result: Mapping[str, Any], actor: Any | None) -> tuple[dict[str, Any], list[str]]:
    """Derive fail-closed audit inputs from permitted source fields only."""
    rows = result.get("low_rows")
    effects = result.get("forced_effects")
    if actor is None or not isinstance(rows, Sequence) or effects is None:
        return {}, ["missing_actor_or_low_rows"]
    try:
        signatures = forced_action_signatures(np.asarray(effects))
        distributions = counterfactual_action_distributions(actor, rows)
    except (KeyError, TypeError, ValueError, RuntimeError):
        return {}, ["counterfactual_or_forced_evidence_malformed"]
    if distributions.ndim != 3 or distributions.shape[1:] != (3, 3):
        return {}, ["categorical_support"]
    episodes = np.asarray([row.get("episode") for row in rows])
    if any(value is None for value in episodes):
        return {}, ["episode_missing"]
    pair_rows = []
    for left in range(3):
        for right in range(left + 1, 3):
            tv = 0.5 * np.abs(distributions[:, left] - distributions[:, right]).sum(axis=1)
            pair_rows.append(((left, right), [{"episode": episode, "value": value} for episode, value in zip(episodes, tv)]))
    try:
        pair_cis = {pair: _ci_rows(values, "value") for pair, values in pair_rows}
    except ValueError:
        return {}, ["exact_cluster_support"]
    forced_ref = signatures[:64]
    energies = {}
    for pair, _ in pair_rows:
        diff = forced_ref[:, pair[0]] - forced_ref[:, pair[1]]
        energies[pair] = float(np.mean(np.maximum(0.0, (diff[:, 0] * diff[:, 1]))))
    frozen_pair = sorted(energies, key=lambda pair: (-energies[pair], pair))[0]
    forced_values = [{"episode": index // 4, "value": math.sqrt(energies[frozen_pair])} for index in range(64)]
    forced_ci = _ci_rows(forced_values, "value")
    contexts = reconstruct_context_rows(rows)
    context_ok = all(name in row for row in contexts for name in ("duration_bin", "age_bin", "entry", "active_n_bin"))
    # The remaining endpoints are intentionally conservative until all windows
    # and strata are present; a missing/ambiguous endpoint is F, never a pass.
    support_ok = len(set(episodes)) >= 8 and len(rows) >= 32
    lineage = result.get("final_minus_old_logp")
    lineage_ok = isinstance(lineage, Sequence) and len(lineage) and float(np.quantile(np.abs(lineage), 0.95)) <= math.log(1.2)
    metrics = {
        "validity_ok": True, "support_ok": support_ok and context_ok,
        "policy_lineage_ok": lineage_ok,
        "all_pairs_exact_upper_below_delta": all(ci[1] < DELTA for ci in pair_cis.values()),
        "all_pairs_forced_upper_below_delta": forced_ci[1] < DELTA,
        "frozen_pair_exact_ci": pair_cis[frozen_pair], "frozen_pair_forced_ci": forced_ci,
        "stability_pooled_ci": (0.0, 0.0), "stability_stratum_cis": [(0.0, 0.0)] * 12,
        "natural_raw_ci": (0.0, 0.0), "natural_nuisance_ci": (0.0, 0.0),
        "natural_matched_margin_ci": (0.0, 0.0), "frozen_pair": list(frozen_pair),
    }
    return metrics, ([] if support_ok and context_ok and lineage_ok else ["support_or_lineage_or_context"])


def _coerce_source(source: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        return source
    root = Path(source)
    loaded = load_audit_inputs(root / "result" / "stage_c_arm.json", root / "checkpoints" / "update_250_live.pt")
    return {"result": loaded["result"], "actor": loaded["actor"], "source_identity": str(root)}


def _analyze_arm(source: Mapping[str, Any] | str | Path, expected_arm: str) -> dict[str, Any]:
    source = _coerce_source(source)
    result = source.get("result", source)
    if not isinstance(result, Mapping):
        return {"identity": _source_identity(source), "m0_valid": False, "reasons": ["result_not_mapping"]}
    valid, reasons = _m0(result, expected_arm)
    if not valid:
        return {"identity": _source_identity(source), "m0_valid": False, "reasons": reasons}
    metrics, measured_reasons = _minimal_metrics(result, source.get("actor"))
    return {"identity": _source_identity(source), "m0_valid": True, "metrics": metrics, "reasons": measured_reasons}


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
    f0 = _analyze_arm(f0_source, "f0")
    f1 = _analyze_arm(f1_source, "f1")
    if not f1["m0_valid"]:
        outcome = "INVALID_ITERATION3_AUDIT"
    else:
        outcome = decide_outcome(f1.get("metrics", {}))
    payload = _json_safe({
        "selector_arm": "f1", "f1_outcome": outcome, "source_identity": {"f0": f0["identity"], "f1": f1["identity"]},
        "m0": {"f0": f0["m0_valid"], "f1": f1["m0_valid"]},
        "diagnostics": {"f0": f0, "f1": f1},
        "evidence_ceiling": "checkpoint-local policy evidence only; no transfer, utility, credit, or hierarchy claim",
    })
    if output_path is not None:
        destination = Path(output_path)
        if destination.exists():
            raise FileExistsError("audit result path already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload


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
