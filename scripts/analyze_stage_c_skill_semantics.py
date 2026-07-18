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


def _m0(result: Mapping[str, Any], checkpoint: Mapping[str, Any], expected_arm: str) -> tuple[bool, list[str]]:
    """Validate the actual nested Stage C result/checkpoint contract."""
    reasons = []
    contract = result.get("contract", {})
    counts = result.get("counts", {})
    if result.get("schema_version") != 1 or result.get("stage") != "stage_c_paired_f0_f1":
        reasons.append("m0_result_schema")
    if result.get("arm") != expected_arm or not result.get("implementation_valid"):
        reasons.append("m0_arm_or_validity")
    if checkpoint.get("checkpoint_schema_version") != 3:
        reasons.append("m0_checkpoint_schema")
    if (contract.get("num_envs"), contract.get("outer_updates"), contract.get("environment_transitions"), contract.get("latent_skills")) != (16, 250, 320_000, 3):
        reasons.append("m0_registered_contract")
    if counts.get("intrinsic_applied_count") != 0:
        reasons.append("m0_intrinsic")
    if not all(bool(value) for value in result.get("m0", {}).values()):
        reasons.append("m0_source_checks")
    effects = result.get("forced_audit", {}).get("effects")
    if effects is None:
        reasons.append("m0_forced_missing")
    else:
        try:
            forced_action_signatures(np.asarray(effects))
        except (TypeError, ValueError):
            reasons.append("m0_forced_shape_or_simplex")
    ledger = checkpoint.get("event_architecture", {}).get("low_ledger")
    if not isinstance(ledger, Sequence) or len(ledger) != 5_120:
        reasons.append("m0_low_row_count")
    return not reasons, reasons


def _row_value(row: Any, name: str) -> Any:
    if isinstance(row, Mapping):
        return row[name]
    return getattr(row, name)


def _allowed_rows(ledger: Sequence[Any]) -> list[dict[str, Any]]:
    fields = ("lifecycle_key", "membership_epoch", "physical_time", "observation", "skill", "action", "old_log_probability", "actor_hidden_before")
    return [{field: _row_value(row, field) for field in fields} for row in ledger]


def _final_log_probabilities(actor: Any, rows: Sequence[Mapping[str, Any]]) -> np.ndarray:
    values = []
    with torch.no_grad():
        for row in rows:
            observation = torch.as_tensor(row["observation"], dtype=torch.float32).reshape(1, -1).to(actor.device)
            skills = torch.tensor([int(row["skill"])], dtype=torch.long, device=actor.device)
            hidden = torch.as_tensor(row["actor_hidden_before"], dtype=torch.float32).reshape(1, -1).to(actor.device)
            features = actor._features(observation, skills)
            features, _ = actor.actor_rnn(features, hidden, torch.ones(1, 1, device=actor.device))
            action = torch.as_tensor(row["action"], dtype=torch.long, device=actor.device).reshape(1, 1)
            values.append(float(actor.actor_act.action_out(features).log_probs(action).item()))
    return np.asarray(values, dtype=np.float64)


def _minimal_metrics(result: Mapping[str, Any], checkpoint: Mapping[str, Any], actor: Any | None) -> tuple[dict[str, Any], list[str], dict[str, bool]]:
    """Derive available local diagnostics and name unavailable estimands explicitly."""
    ledger = checkpoint["event_architecture"]["low_ledger"]
    effects = result["forced_audit"]["effects"]
    availability = {
        "fixed_input_rows": False, "policy_lineage": False, "forced_aggregate": False,
        "forced_snapshot_metadata": False, "forced_nuisance_metadata": False,
        "natural_source_episode": False, "natural_forced_alignment": False,
        "natural_common_support": False,
    }
    if actor is None:
        return {}, ["actor_unavailable"], availability
    try:
        signatures = forced_action_signatures(np.asarray(effects))
        rows = _allowed_rows(ledger)
        distributions = counterfactual_action_distributions(actor, rows)
        final_logp = _final_log_probabilities(actor, rows)
    except (KeyError, AttributeError, TypeError, ValueError, RuntimeError):
        return {}, ["ledger_or_actor_evidence_malformed"], availability
    availability.update(fixed_input_rows=True, policy_lineage=True, forced_aggregate=True)
    pairs = {}
    for left in range(3):
        for right in range(left + 1, 3):
            pairs[f"{left}-{right}"] = float(np.mean(0.5 * np.abs(distributions[:, left] - distributions[:, right]).sum(axis=1)))
    lineage = final_logp - np.asarray([row["old_log_probability"] for row in rows], dtype=np.float64)
    diagnostics = {
        "all_skill_tv_means": pairs,
        "forced_aggregate_signature_mean": signatures.mean(axis=(0, 2)).tolist(),
        "policy_lineage_abs_delta_p95": float(np.quantile(np.abs(lineage), 0.95)),
    }
    reasons = [name for name, available in availability.items() if not available]
    return diagnostics, reasons, availability


def _coerce_source(source: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        return source
    root = Path(source)
    loaded = load_audit_inputs(root / "result" / "stage_c_arm.json", root / "checkpoints" / "update_250_live.pt")
    return {"result": loaded["result"], "checkpoint": loaded["checkpoint"], "actor": loaded["actor"], "source_identity": str(root)}


def _analyze_arm(source: Mapping[str, Any] | str | Path, expected_arm: str) -> dict[str, Any]:
    source = _coerce_source(source)
    result = source.get("result", source)
    if not isinstance(result, Mapping):
        return {"identity": _source_identity(source), "m0_valid": False, "reasons": ["result_not_mapping"]}
    checkpoint = source.get("checkpoint")
    if not isinstance(checkpoint, Mapping):
        return {"identity": _source_identity(source), "m0_valid": False, "reasons": ["checkpoint_not_mapping"]}
    valid, reasons = _m0(result, checkpoint, expected_arm)
    if not valid:
        return {"identity": _source_identity(source), "m0_valid": False, "reasons": reasons}
    diagnostics, measured_reasons, availability = _minimal_metrics(result, checkpoint, source.get("actor"))
    return {"identity": _source_identity(source), "m0_valid": True, "diagnostics": diagnostics, "evidence_availability": availability, "reasons": measured_reasons}


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
    if not f0["m0_valid"] or not f1["m0_valid"]:
        outcome = "INVALID_ITERATION3_AUDIT"
    else:
        outcome = "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
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
