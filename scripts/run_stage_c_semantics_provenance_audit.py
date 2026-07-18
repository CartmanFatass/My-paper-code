"""One-shot, evaluation-only Stage C provenance and semantics audit.

The runner reloads the two registered model-only update-250 checkpoints,
repeats the frozen stochastic evaluation with Task 3A provenance enabled,
requires exact parity with the registered Stage C results, and then applies the
already-frozen A--F analysis.  It has no training or optimizer path.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import io
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = Path(__file__).resolve().parent
for search_root in (PROJECT_ROOT, SCRIPT_ROOT):
    if str(search_root) not in sys.path:
        sys.path.insert(0, str(search_root))

import numpy as np
import torch

from analyze_stage_c_skill_semantics import (
    DELTA,
    DELTA_STRATUM,
    LINEAGE_THRESHOLD,
    REQUIRED_SOURCE_M0,
    _global_rng_equal,
    _global_rng_snapshot,
    _restore_global_rng,
    _tensor_records,
    _tensors_unchanged,
    cluster_bootstrap_ci,
    counterfactual_action_distributions,
    decide_outcome,
    matched_nulls,
    natural_segments,
    reconstruct_context_rows,
)


BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 307_057
SHUFFLE_SEED = 307_058
REFERENCE_EPISODES = tuple(range(16))
INFERENCE_EPISODES = tuple(range(16, 32))
EXPECTED_FORCED_SOURCES = 128
MIN_POOLED_EPISODES = 8
MIN_POOLED_FORCED_SNAPSHOTS = 24
MIN_STRATUM_EPISODES = 8
MIN_FORCED_SNAPSHOTS_PER_STRATUM = 8
MIN_EXACT_ROWS_PER_STRATUM = 32
MIN_NATURAL_WINDOWS_PER_SKILL = 24

NATURAL_FIELDS = frozenset(
    {
        "arm",
        "task_master_seed",
        "episode_id",
        "physical_time",
        "lifecycle_key",
        "membership_epoch",
        "observation",
        "actor_hidden_before",
        "natural_skill",
        "natural_action",
        "natural_action_log_probability",
        "primitive_legal_support",
        "primitive_probabilities",
        "active_set_size",
    }
)
FORCED_FIELDS = NATURAL_FIELDS | frozenset(
    {
        "focal_index",
        "active_keys",
        "active_membership_epochs",
        "active_skills",
        "frontier",
        "membership_deltas",
        "source_rng_ledger",
        "source_rng_states",
        "forced_effects",
    }
)
PROHIBITED_FIELDS = frozenset(
    {
        "task_outcome",
        "task_phase",
        "reward",
        "utility",
        "progress",
        "role",
        "contact",
        "owner",
        "success",
    }
)

FROZEN_STRATA = {
    "age_bin": ("0..9", "10..19", ">=20"),
    "entry_rejoin": ("entry", "rejoin", "ordinary"),
    "active_n_bin": ("2", "4", "6"),
    "duration_bin": ("1..9", "10..19", ">=20"),
}

CLAIM_CEILING = (
    "checkpoint-local z -> action dependence, 12-active-step persistence, "
    "nuisance-stratified stability, and natural overlap in this testbed only; "
    "no environment-independent semantics, transfer, cooperation, hierarchy "
    "superiority, commitment advantage, credit success, or training-seed "
    "robustness claim"
)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _shared_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row["arm"],
        int(row["task_master_seed"]),
        int(row["episode_id"]),
        int(row["physical_time"]),
        str(row["lifecycle_key"]),
        int(row["membership_epoch"]),
    )


def _recursive_prohibited_fields(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in PROHIBITED_FIELDS:
                found.append(normalized)
            found.extend(_recursive_prohibited_fields(nested))
    elif _is_sequence(value):
        for nested in value:
            found.extend(_recursive_prohibited_fields(nested))
    return found


def _finite_json_values(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_json_values(item) for item in value.values())
    if _is_sequence(value):
        return all(_finite_json_values(item) for item in value)
    if isinstance(value, (float, np.floating)):
        return math.isfinite(float(value))
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all().item())
    if isinstance(value, np.ndarray):
        return bool(np.isfinite(value).all())
    return True


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if _is_sequence(value):
        return [_json_safe(item) for item in value]
    return value


def validate_source_identity(
    source: Mapping[str, Any], expected_arm: str
) -> dict[str, Any]:
    """Validate the registered Stage C result, terminal arm manifest and header."""

    result = source.get("result")
    checkpoint = source.get("checkpoint")
    status = source.get("arm_status")
    result = result if isinstance(result, Mapping) else {}
    checkpoint = checkpoint if isinstance(checkpoint, Mapping) else {}
    status = status if isinstance(status, Mapping) else {}
    bundle = checkpoint.get("event_architecture")
    bundle = bundle if isinstance(bundle, Mapping) else {}
    contract = result.get("contract")
    contract = contract if isinstance(contract, Mapping) else {}
    counts = result.get("counts")
    counts = counts if isinstance(counts, Mapping) else {}
    source_m0 = result.get("m0")
    source_m0 = source_m0 if isinstance(source_m0, Mapping) else {}
    architecture = bundle.get("architecture_state")
    architecture = architecture if isinstance(architecture, Mapping) else {}

    checks = {
        "registered_result_header": result.get("schema_version") == 1
        and result.get("stage") == "stage_c_paired_f0_f1",
        "registered_result_arm": result.get("arm") == expected_arm,
        "registered_result_implementation_valid": result.get("implementation_valid")
        is True,
        "registered_source_m0": REQUIRED_SOURCE_M0.issubset(source_m0)
        and all(value is True for value in source_m0.values()),
        "registered_contract": (
            contract.get("num_envs"),
            contract.get("horizon"),
            contract.get("outer_updates"),
            contract.get("environment_transitions"),
            contract.get("latent_skills"),
            contract.get("evaluation_episodes_per_mode"),
        )
        == (16, 80, 250, 320_000, 3, 256),
        "registered_counts": (
            counts.get("environment_steps"),
            counts.get("high_optimizer_steps"),
            counts.get("low_optimizer_steps"),
            counts.get("training_ledger_ids"),
            counts.get("intrinsic_applied_count"),
        )
        == (320_000, 1_000, 1_000, 4_000, 0),
        "terminal_arm_manifest": (
            status.get("state"),
            status.get("phase"),
            status.get("mode"),
            status.get("update"),
            status.get("updates_total"),
            status.get("steps"),
            status.get("steps_total"),
            status.get("high_optimizer_steps"),
            status.get("low_optimizer_steps"),
            status.get("implementation_valid"),
        )
        == (
            "complete",
            "terminal",
            expected_arm,
            250,
            250,
            320_000,
            320_000,
            1_000,
            1_000,
            True,
        ),
        "model_only_schema3_header": checkpoint.get("checkpoint_schema_version")
        == 3
        and checkpoint.get("high_controller") == "variable_roster_event"
        and bundle.get("event_architecture_schema_version") == 1
        and bundle.get("runtime_state_absent_for_fresh_eval") is True,
        "checkpoint_arm_update_steps": (
            bundle.get("architecture_mode"),
            bundle.get("update_idx"),
            bundle.get("total_steps"),
        )
        == (expected_arm, 250, 320_000),
        "checkpoint_runtime_header": (
            bundle.get("k0"),
            bundle.get("opportunity_schedule_name"),
            bundle.get("snapshot_capability_name"),
            bundle.get("snapshot_capability_version"),
        )
        == (
            10,
            "uniform_active_gap_v1",
            "variable_roster_event_snapshot",
            1,
        ),
        "checkpoint_actor_header": (
            architecture.get("n_skills"),
            architecture.get("action_dim"),
            architecture.get("action_space_type"),
            architecture.get("gamma"),
            architecture.get("gae_lambda"),
        )
        == (3, 3, "discrete", 0.99, 0.95)
        and all(
            isinstance(architecture.get(name), int) and architecture[name] > 0
            for name in (
                "obs_dim",
                "critic_member_dim",
                "critic_global_dim",
                "member_hidden_dim",
                "high_hidden_dim",
                "low_hidden_dim",
                "skill_embedding_dim",
            )
        ),
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "reasons": [name for name, valid in checks.items() if not valid],
    }


def _exact_sequence(left: Any, right: Any) -> bool:
    try:
        lhs = np.asarray(left)
        rhs = np.asarray(right)
    except (TypeError, ValueError):
        return left == right
    return lhs.shape == rhs.shape and bool(np.array_equal(lhs, rhs))


def validate_registered_parity(
    registered_result: Mapping[str, Any], evaluation: Mapping[str, Any]
) -> dict[str, Any]:
    """Require exact equality with the original final stochastic evaluation."""

    try:
        registered_stochastic = registered_result["final"]["stochastic"]
        registered_forced = registered_result["forced_audit"]["effects"]
        new_forced = evaluation["forced_audit"]["effects"]
        settings_exact = (
            registered_stochastic.get("deterministic") is False
            and evaluation.get("deterministic") is False
            and registered_stochastic.get("environment_steps") == 256 * 80
            and evaluation.get("environment_steps") == 256 * 80
        )
        outcomes_exact = all(
            _exact_sequence(registered_stochastic[name], evaluation[name])
            for name in ("episode_ids", "persistent", "short", "utility")
        )
        counts_exact = _exact_sequence(
            registered_stochastic["natural_skill_step_counts"],
            evaluation["natural_skill_step_counts"],
        )
        registered_effects = np.asarray(registered_forced, dtype=np.float64)
        evaluated_effects = np.asarray(new_forced, dtype=np.float64)
        effects_exact = (
            registered_effects.shape == (128, 3, 2, 4)
            and evaluated_effects.shape == (128, 3, 2, 4)
            and np.array_equal(registered_effects, evaluated_effects)
        )
    except (KeyError, TypeError, ValueError):
        settings_exact = outcomes_exact = counts_exact = effects_exact = False
    checks = {
        "registered_stochastic_settings_exact": bool(settings_exact),
        "stochastic_episode_outcomes_exact": bool(outcomes_exact),
        "natural_skill_counts_exact": bool(counts_exact),
        "forced_effects_exact": bool(effects_exact),
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "reasons": [name for name, valid in checks.items() if not valid],
    }


def _row_probability_valid(row: Mapping[str, Any]) -> bool:
    try:
        support = list(row["primitive_legal_support"])
        probabilities = np.asarray(row["primitive_probabilities"], dtype=np.float64)
        action = int(row["natural_action"])
        skill = int(row["natural_skill"])
        stored_logp = float(row["natural_action_log_probability"])
    except (KeyError, TypeError, ValueError):
        return False
    if (
        support != [0, 1, 2]
        or probabilities.shape != (3,)
        or not np.isfinite(probabilities).all()
        or not np.all(probabilities > 0.0)
        or not np.isclose(probabilities.sum(), 1.0, atol=1e-6, rtol=0.0)
        or action not in (0, 1, 2)
        or skill not in (0, 1, 2)
        or not math.isfinite(stored_logp)
    ):
        return False
    return abs(math.log(float(probabilities[action])) - stored_logp) <= 1e-5


def _row_vectors_valid(row: Mapping[str, Any]) -> bool:
    try:
        observation = np.asarray(row["observation"], dtype=np.float32)
        hidden = np.asarray(row["actor_hidden_before"], dtype=np.float32)
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        observation.ndim == 1
        and observation.size > 0
        and hidden.ndim == 1
        and hidden.size > 0
        and np.isfinite(observation).all()
        and np.isfinite(hidden).all()
    )


def _forced_metadata_valid(row: Mapping[str, Any]) -> bool:
    try:
        effects = np.asarray(row["forced_effects"], dtype=np.float64)
        active_keys = list(row["active_keys"])
        active_epochs = list(row["active_membership_epochs"])
        active_skills = list(row["active_skills"])
        focal_index = int(row["focal_index"])
        active_n = int(row["active_set_size"])
        ledger = row["source_rng_ledger"]
        states = row["source_rng_states"]
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        effects.shape == (3, 2, 4)
        and np.isfinite(effects).all()
        and active_n in (2, 4, 6)
        and len(active_keys) == active_n
        and len(active_epochs) == active_n
        and len(active_skills) == active_n
        and 0 <= focal_index < active_n
        and str(active_keys[focal_index]) == str(row["lifecycle_key"])
        and int(active_epochs[focal_index]) == int(row["membership_epoch"])
        and all(int(skill) in (0, 1, 2) for skill in active_skills)
        and isinstance(ledger, Mapping)
        and set(ledger) == {
            "episode_id",
            "opportunity",
            "frontier_order",
            "policy_action",
        }
        and int(ledger["episode_id"]) == int(row["episode_id"])
        and isinstance(states, Mapping)
        and set(states) == {"opportunity", "frontier_order", "policy_action"}
    )


def validate_provenance(
    provenance: Mapping[str, Any], expected_arm: str
) -> dict[str, Any]:
    """Validate the Task 3A leakage-free schema and forced--natural pairing."""

    natural = provenance.get("natural_rows")
    forced = provenance.get("forced_sources")
    natural = list(natural) if _is_sequence(natural) else []
    forced = list(forced) if _is_sequence(forced) else []
    natural_schema = bool(natural) and all(
        isinstance(row, Mapping) and set(row) == NATURAL_FIELDS for row in natural
    )
    forced_schema = len(forced) == EXPECTED_FORCED_SOURCES and all(
        isinstance(row, Mapping) and set(row) == FORCED_FIELDS for row in forced
    )
    try:
        natural_keys = [_shared_key(row) for row in natural]
        forced_keys = [_shared_key(row) for row in forced]
    except (KeyError, TypeError, ValueError):
        natural_keys = []
        forced_keys = []
    natural_by_key: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for key, row in zip(natural_keys, natural):
        natural_by_key[key].append(row)
    one_match = bool(forced_keys) and all(
        len(natural_by_key.get(key, ())) == 1 for key in forced_keys
    )
    source_vectors_exact = one_match
    copied_natural_fields_exact = one_match
    if one_match:
        for key, source in zip(forced_keys, forced):
            matched = natural_by_key[key][0]
            try:
                source_vectors_exact = source_vectors_exact and np.array_equal(
                    np.asarray(source["observation"], dtype=np.float32),
                    np.asarray(matched["observation"], dtype=np.float32),
                ) and np.array_equal(
                    np.asarray(source["actor_hidden_before"], dtype=np.float32),
                    np.asarray(matched["actor_hidden_before"], dtype=np.float32),
                )
                copied_natural_fields_exact = copied_natural_fields_exact and all(
                    source[field] == matched[field]
                    for field in NATURAL_FIELDS
                    if field not in {"observation", "actor_hidden_before"}
                )
            except (KeyError, TypeError, ValueError):
                source_vectors_exact = copied_natural_fields_exact = False
    checks = {
        "provenance_schema": provenance.get("schema") == 1,
        "natural_row_schema": natural_schema,
        "forced_source_schema_and_count": forced_schema,
        "only_reference_and_inference_episodes": bool(natural and forced)
        and {int(row.get("episode_id", -1)) for row in natural} == set(range(32))
        and {int(row.get("episode_id", -1)) for row in forced} == set(range(32))
        and Counter(int(row.get("episode_id", -1)) for row in forced)
        == Counter({episode: 4 for episode in range(32)}),
        "arm_and_task_seed_exact": bool(natural and forced)
        and all(
            row.get("arm") == expected_arm
            and row.get("task_master_seed") == 97_057
            for row in (*natural, *forced)
        ),
        "natural_shared_keys_unique": len(natural_keys) == len(set(natural_keys))
        and len(natural_keys) == len(natural),
        "forced_shared_keys_unique": len(forced_keys) == len(set(forced_keys))
        and len(forced_keys) == EXPECTED_FORCED_SOURCES,
        "one_natural_match_per_forced_key": one_match,
        "source_observation_and_hidden_exact": bool(source_vectors_exact),
        "copied_natural_fields_exact": bool(copied_natural_fields_exact),
        "finite_source_vectors": bool(natural and forced)
        and all(_row_vectors_valid(row) for row in (*natural, *forced)),
        "full_three_action_support_and_replay": bool(natural and forced)
        and all(_row_probability_valid(row) for row in (*natural, *forced)),
        "forced_effects_and_source_metadata": forced_schema
        and all(_forced_metadata_valid(row) for row in forced),
        "prohibited_fields_absent": not _recursive_prohibited_fields(provenance),
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "reasons": [name for name, valid in checks.items() if not valid],
        "support_counts": {
            "natural_rows": len(natural),
            "forced_sources": len(forced),
            "unique_natural_shared_keys": len(set(natural_keys)),
            "unique_forced_shared_keys": len(set(forced_keys)),
        },
    }


def _forced_energy(effects: np.ndarray, left: int, right: int) -> np.ndarray:
    difference = effects[:, left, :, :2] - effects[:, right, :, :2]
    energy = np.sum(difference[:, 0] * difference[:, 1], axis=1)
    return np.maximum(energy, 0.0)


def _effect_signatures(effects: np.ndarray) -> np.ndarray:
    values = np.asarray(effects, dtype=np.float64)[..., :2]
    remainder = 1.0 - values.sum(axis=-1, keepdims=True)
    signatures = np.concatenate((values, remainder), axis=-1)
    if (
        not np.isfinite(signatures).all()
        or np.any(signatures < -1e-9)
        or np.any(signatures > 1.0 + 1e-9)
    ):
        raise ValueError("forced action/process signatures are outside the simplex")
    return np.clip(signatures, 0.0, 1.0)


def select_reference_pair(
    forced_sources: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Select the maximum-energy unordered skill pair on episodes 0--15 only."""

    reference = [
        row for row in forced_sources if int(row["episode_id"]) in REFERENCE_EPISODES
    ]
    if len(reference) != 4 * len(REFERENCE_EPISODES):
        raise ValueError("reference fold must contain four forced sources per episode")
    effects = np.asarray([row["forced_effects"] for row in reference], dtype=np.float64)
    if effects.shape != (64, 3, 2, 4) or not np.isfinite(effects).all():
        raise ValueError("reference forced effects have the wrong shape")
    energies: dict[str, float] = {}
    for left in range(3):
        for right in range(left + 1, 3):
            energies[f"{left}-{right}"] = float(
                np.mean(_forced_energy(effects, left, right))
            )
    selected_name = sorted(energies, key=lambda name: (-energies[name], name))[0]
    pair = [int(value) for value in selected_name.split("-")]
    return {
        "pair": pair,
        "mean_cross_replica_forced_energy": energies,
        "reference_episodes": list(REFERENCE_EPISODES),
        "inference_episodes": list(INFERENCE_EPISODES),
    }


def _context_rows(
    natural_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[Any, ...], dict[str, Any]]:
    mapped = [
        {
            "episode": int(row["episode_id"]),
            "lifecycle_key": str(row["lifecycle_key"]),
            "membership_epoch": int(row["membership_epoch"]),
            "physical_time": int(row["physical_time"]),
            "skill": int(row["natural_skill"]),
            "active_n": int(row["active_set_size"]),
        }
        for row in natural_rows
    ]
    originals = {
        (
            int(row["episode_id"]),
            str(row["lifecycle_key"]),
            int(row["membership_epoch"]),
            int(row["physical_time"]),
        ): row
        for row in natural_rows
    }
    contexts: dict[tuple[Any, ...], dict[str, Any]] = {}
    for context in reconstruct_context_rows(mapped):
        lookup = (
            int(context["episode"]),
            str(context["lifecycle_key"]),
            int(context["membership_epoch"]),
            int(context["physical_time"]),
        )
        original = originals[lookup]
        contexts[_shared_key(original)] = {
            "active_age": int(context["active_age"]),
            "age_bin": str(context["age_bin"]),
            "entry_rejoin": (
                "entry"
                if bool(context["entry"])
                and int(context["membership_epoch"]) == 0
                else "rejoin"
                if bool(context["entry"])
                else "ordinary"
            ),
            "active_n_bin": str(context["active_n_bin"]),
            "active_duration": int(context["active_duration"]),
            "duration_bin": str(context["duration_bin"]),
        }
    return contexts


def _ci(records: Sequence[Mapping[str, Any]]) -> list[float]:
    if not records:
        return [0.0, 0.0]
    low, _mean, high = cluster_bootstrap_ci(
        records,
        value_key="value",
        repetitions=BOOTSTRAP_REPETITIONS,
        seed=BOOTSTRAP_SEED,
    )
    return [float(low), float(high)]


def _balanced_accuracy(
    labels: Sequence[int], predictions: Sequence[int], pair: Sequence[int]
) -> float:
    labels_array = np.asarray(labels, dtype=np.int64)
    predictions_array = np.asarray(predictions, dtype=np.int64)
    recalls = []
    for skill in pair:
        selected = labels_array == int(skill)
        if not np.any(selected):
            return 0.0
        recalls.append(float(np.mean(predictions_array[selected] == int(skill))))
    return float(np.mean(recalls))


def _macro_episode_records(
    records: Sequence[Mapping[str, Any]], pair: Sequence[int]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
    for row in records:
        grouped[(int(row["episode"]), int(row["skill"]))].append(float(row["value"]))
    episode_values: dict[int, list[float]] = defaultdict(list)
    for (episode, skill), values in grouped.items():
        if skill in pair:
            episode_values[episode].append(float(np.mean(values)))
    return [
        {"episode": episode, "value": float(np.mean(values))}
        for episode, values in sorted(episode_values.items())
        if values
    ]


def _context_only_predictions(
    segments: Sequence[Mapping[str, Any]], pair: Sequence[int]
) -> np.ndarray:
    labels = np.asarray([segment["skill"] for segment in segments], dtype=np.int64)
    episodes = np.asarray([segment["episode"] for segment in segments], dtype=np.int64)
    contexts = [
        (
            segment["age_bin"],
            segment["entry_rejoin"],
            segment["active_n_bin"],
            segment["duration_bin"],
        )
        for segment in segments
    ]
    predictions = np.empty(len(segments), dtype=np.int64)
    for index, (episode, context) in enumerate(zip(episodes, contexts)):
        training_indices = [
            position
            for position, (other_episode, other_context) in enumerate(
                zip(episodes, contexts)
            )
            if other_episode != episode and other_context == context
        ]
        if not training_indices:
            training_indices = [
                position
                for position, other_episode in enumerate(episodes)
                if other_episode != episode
            ]
        counts = Counter(int(labels[position]) for position in training_indices)
        predictions[index] = sorted(pair, key=lambda skill: (-counts[skill], skill))[0]
    return predictions


def analyze_semantics(
    provenance: Mapping[str, Any], actor: Any
) -> dict[str, Any]:
    """Compute the frozen same-input, persistence, stability and overlap reads."""

    natural_rows = list(provenance["natural_rows"])
    forced_sources = list(provenance["forced_sources"])
    selection = select_reference_pair(forced_sources)
    pair = selection["pair"]
    reference = [
        row for row in forced_sources if int(row["episode_id"]) in REFERENCE_EPISODES
    ]
    inference = [
        row for row in forced_sources if int(row["episode_id"]) in INFERENCE_EPISODES
    ]
    if len(inference) != 4 * len(INFERENCE_EPISODES):
        raise ValueError("inference fold must contain four forced sources per episode")

    distributions = counterfactual_action_distributions(actor, forced_sources)
    if (
        distributions.shape != (EXPECTED_FORCED_SOURCES, 3, 3)
        or not np.isfinite(distributions).all()
        or np.any(distributions <= 0.0)
        or not np.allclose(distributions.sum(axis=-1), 1.0, atol=1e-6, rtol=0.0)
    ):
        raise ValueError("all-skill categorical distributions lack full support")
    inference_indices = [
        index
        for index, row in enumerate(forced_sources)
        if int(row["episode_id"]) in INFERENCE_EPISODES
    ]
    exact_cis: dict[str, list[float]] = {}
    forced_cis: dict[str, list[float]] = {}
    inference_effects = np.asarray(
        [row["forced_effects"] for row in inference], dtype=np.float64
    )
    for left in range(3):
        for right in range(left + 1, 3):
            name = f"{left}-{right}"
            exact_values = 0.5 * np.abs(
                distributions[inference_indices, left]
                - distributions[inference_indices, right]
            ).sum(axis=1)
            exact_records = [
                {"episode": int(row["episode_id"]), "value": float(value)}
                for row, value in zip(inference, exact_values)
            ]
            forced_values = np.sqrt(
                _forced_energy(inference_effects, left, right)
            )
            forced_records = [
                {"episode": int(row["episode_id"]), "value": float(value)}
                for row, value in zip(inference, forced_values)
            ]
            exact_cis[name] = _ci(exact_records)
            forced_cis[name] = _ci(forced_records)

    reference_effects = np.asarray(
        [row["forced_effects"] for row in reference], dtype=np.float64
    )
    reference_signatures = _effect_signatures(reference_effects)
    forced_centroids = {
        skill: reference_signatures[:, skill].mean(axis=(0, 1))
        for skill in pair
    }
    reference_indices = [
        index
        for index, row in enumerate(forced_sources)
        if int(row["episode_id"]) in REFERENCE_EPISODES
    ]
    exact_centroids = {
        skill: distributions[reference_indices, skill].mean(axis=0) for skill in pair
    }
    contexts = _context_rows(natural_rows)
    exact_stability_rows: list[dict[str, Any]] = []
    forced_stability_rows: list[dict[str, Any]] = []
    inference_signatures = _effect_signatures(inference_effects)
    for source, source_index, signatures in zip(
        inference, inference_indices, inference_signatures
    ):
        context = contexts[_shared_key(source)]
        for skill in pair:
            other = pair[1] if skill == pair[0] else pair[0]
            exact_signature = distributions[source_index, skill]
            exact_margin = float(
                np.linalg.norm(exact_signature - exact_centroids[other])
                - np.linalg.norm(exact_signature - exact_centroids[skill])
            )
            forced_signature = signatures[skill].mean(axis=0)
            forced_margin = float(
                np.linalg.norm(forced_signature - forced_centroids[other])
                - np.linalg.norm(forced_signature - forced_centroids[skill])
            )
            common = {
                "episode": int(source["episode_id"]),
                "source_key": _shared_key(source),
                "skill": skill,
                **context,
            }
            exact_stability_rows.append(
                {
                    **common,
                    "value": exact_margin,
                }
            )
            forced_stability_rows.append(
                {
                    **common,
                    "value": forced_margin,
                }
            )
    pooled_exact_stability_ci = _ci(
        _macro_episode_records(exact_stability_rows, pair)
    )
    pooled_forced_stability_ci = _ci(
        _macro_episode_records(forced_stability_rows, pair)
    )
    pooled_stability_ci = [
        min(pooled_exact_stability_ci[0], pooled_forced_stability_ci[0]),
        min(pooled_exact_stability_ci[1], pooled_forced_stability_ci[1]),
    ]
    pooled_episodes = {int(row["episode"]) for row in forced_stability_rows}
    pooled_snapshots = {
        row["source_key"] for row in forced_stability_rows
    }
    pooled_support_ok = (
        len(pooled_episodes) >= MIN_POOLED_EPISODES
        and len(pooled_snapshots) >= MIN_POOLED_FORCED_SNAPSHOTS
    )
    stratum_cis: list[list[float]] = []
    stratum_support: dict[str, dict[str, Any]] = {}
    stability_support_ok = pooled_support_ok
    for field, levels in FROZEN_STRATA.items():
        for level in levels:
            exact_selected = [
                row for row in exact_stability_rows if row[field] == level
            ]
            forced_selected = [
                row for row in forced_stability_rows if row[field] == level
            ]
            exact_episodes = {int(row["episode"]) for row in exact_selected}
            forced_episodes = {int(row["episode"]) for row in forced_selected}
            exact_labels = {int(row["skill"]) for row in exact_selected}
            forced_labels = {int(row["skill"]) for row in forced_selected}
            forced_snapshots = {row["source_key"] for row in forced_selected}
            exact_supported = (
                len(exact_episodes) >= MIN_STRATUM_EPISODES
                and len(exact_selected) >= MIN_EXACT_ROWS_PER_STRATUM
                and exact_labels == set(pair)
            )
            forced_supported = (
                len(forced_episodes) >= MIN_STRATUM_EPISODES
                and len(forced_snapshots) >= MIN_FORCED_SNAPSHOTS_PER_STRATUM
                and forced_labels == set(pair)
            )
            supported = exact_supported and forced_supported
            stability_support_ok = stability_support_ok and supported
            exact_ci = (
                _ci(_macro_episode_records(exact_selected, pair))
                if exact_selected
                else [0.0, 0.0]
            )
            forced_ci = (
                _ci(_macro_episode_records(forced_selected, pair))
                if forced_selected
                else [0.0, 0.0]
            )
            stratum_cis.extend((exact_ci, forced_ci))
            stratum_support[f"{field}:{level}"] = {
                "exact_rows": len(exact_selected),
                "exact_episodes": len(exact_episodes),
                "forced_snapshots": len(forced_snapshots),
                "forced_episodes": len(forced_episodes),
                "selected_skills": sorted(exact_labels & forced_labels),
                "exact_supported": exact_supported,
                "forced_supported": forced_supported,
                "supported": supported,
                "exact_ci": exact_ci,
                "forced_ci": forced_ci,
            }

    mapped_natural = [
        {
            "episode": int(row["episode_id"]),
            "lifecycle_key": str(row["lifecycle_key"]),
            "membership_epoch": int(row["membership_epoch"]),
            "physical_time": int(row["physical_time"]),
            "skill": int(row["natural_skill"]),
            "active_n": int(row["active_set_size"]),
            "observation": row["observation"],
            "actor_hidden_before": row["actor_hidden_before"],
            "source_key": _shared_key(row),
        }
        for row in natural_rows
        if int(row["episode_id"]) in INFERENCE_EPISODES
    ]
    segments = natural_segments(mapped_natural, actor=actor)
    selected_segments: list[dict[str, Any]] = []
    for segment in segments:
        skill = int(segment["skill"])
        if skill not in pair:
            continue
        source_context = contexts[segment["rows"][0]["source_key"]]
        signature = np.asarray(segment["signature"], dtype=np.float64)
        other = pair[1] if skill == pair[0] else pair[0]
        distances = {
            candidate: float(np.linalg.norm(signature - exact_centroids[candidate]))
            for candidate in pair
        }
        predicted = sorted(pair, key=lambda candidate: (distances[candidate], candidate))[0]
        selected_segments.append(
            {
                "episode": int(segment["episode"]),
                "skill": skill,
                "signature": signature,
                "predicted": predicted,
                "value": distances[other] - distances[skill],
                **source_context,
            }
        )
    segment_counts = Counter(int(segment["skill"]) for segment in selected_segments)
    segment_episodes = {
        skill: {
            int(segment["episode"])
            for segment in selected_segments
            if int(segment["skill"]) == skill
        }
        for skill in pair
    }
    natural_support_ok = all(
        segment_counts[skill] >= MIN_NATURAL_WINDOWS_PER_SKILL
        and len(segment_episodes[skill]) >= MIN_STRATUM_EPISODES
        for skill in pair
    )
    raw_distance_ci = _ci(_macro_episode_records(selected_segments, pair))

    labels = np.asarray(
        [int(segment["skill"]) for segment in selected_segments], dtype=np.int64
    )
    predictions = np.asarray(
        [int(segment["predicted"]) for segment in selected_segments], dtype=np.int64
    )
    observed_balanced_accuracy = (
        _balanced_accuracy(labels, predictions, pair) if len(labels) else 0.0
    )
    accuracy_rows = [
        {
            "episode": int(segment["episode"]),
            "skill": int(segment["skill"]),
            "value": float(predictions[index] == labels[index]),
        }
        for index, segment in enumerate(selected_segments)
    ]
    balanced_accuracy_ci = _ci(_macro_episode_records(accuracy_rows, pair))
    raw_decision_ci = [
        min(
            raw_distance_ci[0],
            balanced_accuracy_ci[0] - 0.5 + DELTA,
        ),
        min(
            raw_distance_ci[1],
            balanced_accuracy_ci[1] - 0.5 + DELTA,
        ),
    ]
    if balanced_accuracy_ci[1] <= 0.5:
        raw_decision_ci[1] = min(
            raw_decision_ci[1], np.nextafter(DELTA, -math.inf)
        )
    context_predictions = (
        _context_only_predictions(selected_segments, pair)
        if selected_segments
        else np.empty(0, dtype=np.int64)
    )
    context_balanced_accuracy = (
        _balanced_accuracy(labels, context_predictions, pair) if len(labels) else 0.0
    )
    prior_skill = pair[0]
    if len(labels):
        label_counts = Counter(int(label) for label in labels)
        prior_skill = sorted(pair, key=lambda skill: (-label_counts[skill], skill))[0]
    prior_predictions = np.full(len(labels), prior_skill, dtype=np.int64)
    prior_balanced_accuracy = (
        _balanced_accuracy(labels, prior_predictions, pair) if len(labels) else 0.0
    )
    nuisance_rows: list[dict[str, Any]] = []
    for index, segment in enumerate(selected_segments):
        nuisance_rows.append(
            {
                "episode": int(segment["episode"]),
                "skill": int(segment["skill"]),
                "value": float(predictions[index] == labels[index])
                - float(context_predictions[index] == labels[index]),
            }
        )
    nuisance_ci = _ci(_macro_episode_records(nuisance_rows, pair))

    null_summaries: dict[str, dict[str, float]] = {}
    null_draws: dict[str, np.ndarray] = {}
    if len(labels) and set(labels) == set(pair):
        statistic = lambda shuffled: _balanced_accuracy(  # noqa: E731
            shuffled, predictions, pair
        )
        null_specs = {"global": None}
        null_specs.update(
            {
                field: [segment[field] for segment in selected_segments]
                for field in FROZEN_STRATA
            }
        )
        for name, strata in null_specs.items():
            draws = matched_nulls(
                labels,
                statistic,
                strata=strata,
                repetitions=BOOTSTRAP_REPETITIONS,
                seed=SHUFFLE_SEED,
            )
            null_draws[name] = draws
            null_summaries[name] = {
                "lower": float(np.quantile(draws, 0.025)),
                "mean": float(np.mean(draws)),
                "upper": float(np.quantile(draws, 0.975)),
            }
    matched_margin_ci = [0.0, 0.0]
    matched_names = tuple(FROZEN_STRATA)
    if all(name in null_draws for name in matched_names):
        strongest_null = np.max(
            np.stack([null_draws[name] for name in matched_names], axis=0), axis=0
        )
        margins = observed_balanced_accuracy - strongest_null
        matched_margin_ci = [
            float(np.quantile(margins, 0.025)),
            float(np.quantile(margins, 0.975)),
        ]

    lineage_deltas = []
    for row in natural_rows:
        probabilities = np.asarray(row["primitive_probabilities"], dtype=np.float64)
        action = int(row["natural_action"])
        lineage_deltas.append(
            abs(
                math.log(float(probabilities[action]))
                - float(row["natural_action_log_probability"])
            )
        )
    lineage_p95 = float(np.quantile(lineage_deltas, 0.95))
    support_ok = bool(stability_support_ok and natural_support_ok)
    selected_name = f"{pair[0]}-{pair[1]}"
    metrics = {
        "validity_ok": True,
        "support_ok": support_ok,
        "policy_lineage_ok": lineage_p95 <= LINEAGE_THRESHOLD,
        "all_pairs_exact_upper_below_delta": all(
            ci[1] < DELTA for ci in exact_cis.values()
        ),
        "all_pairs_forced_upper_below_delta": all(
            ci[1] < DELTA for ci in forced_cis.values()
        ),
        "frozen_pair_exact_ci": exact_cis[selected_name],
        "frozen_pair_forced_ci": forced_cis[selected_name],
        "stability_pooled_ci": pooled_stability_ci,
        "stability_stratum_cis": stratum_cis,
        "natural_raw_ci": raw_decision_ci,
        "natural_nuisance_ci": nuisance_ci,
        "natural_matched_margin_ci": matched_margin_ci,
    }
    return {
        "metrics": metrics,
        "reference_selection": selection,
        "same_input_action_tv_ci": exact_cis,
        "persistent_process_dependence_ci": forced_cis,
        "reference_centroids": {
            "exact": {
                str(skill): exact_centroids[skill].tolist() for skill in pair
            },
            "forced": {
                str(skill): forced_centroids[skill].tolist() for skill in pair
            },
        },
        "stability": {
            "pooled_decision_ci": pooled_stability_ci,
            "pooled_exact_ci": pooled_exact_stability_ci,
            "pooled_forced_ci": pooled_forced_stability_ci,
            "pooled_episodes": len(pooled_episodes),
            "pooled_forced_snapshots": len(pooled_snapshots),
            "pooled_supported": pooled_support_ok,
            "strata": stratum_support,
        },
        "natural_overlap": {
            "selected_segments": len(selected_segments),
            "segments_per_skill": {
                str(skill): int(segment_counts[skill]) for skill in pair
            },
            "episodes_per_skill": {
                str(skill): len(segment_episodes[skill]) for skill in pair
            },
            "raw_distance_margin_ci": raw_distance_ci,
            "raw_decision_ci": raw_decision_ci,
            "balanced_accuracy": observed_balanced_accuracy,
            "balanced_accuracy_ci": balanced_accuracy_ci,
            "context_only_balanced_accuracy": context_balanced_accuracy,
            "skill_prior_balanced_accuracy": prior_balanced_accuracy,
            "nuisance_margin_ci": nuisance_ci,
            "matched_shuffle_margin_ci": matched_margin_ci,
            "shuffle_nulls": null_summaries,
        },
        "policy_lineage": {
            "abs_delta_logp_p95": lineage_p95,
            "threshold": LINEAGE_THRESHOLD,
            "valid": lineage_p95 <= LINEAGE_THRESHOLD,
        },
        "support_ok": support_ok,
    }


def frozen_outcome(metrics: Mapping[str, Any]) -> str:
    """Expose the unchanged iteration-3 A--F priority for this runner."""

    return decide_outcome(metrics)


def _model_modules(model_owner: Any) -> tuple[Any, ...]:
    return (
        model_owner.commitment_model,
        model_owner.event_critic,
        model_owner.low_actor,
        model_owner.low_critic,
    )


def model_state_snapshot(model_owner: Any) -> dict[str, Any]:
    modules = _model_modules(model_owner)
    return {
        "tensors": [
            {name: tensor.detach().clone() for name, tensor in module.state_dict().items()}
            for module in modules
        ],
        "grads": [
            [
                None if parameter.grad is None else parameter.grad.detach().clone()
                for parameter in module.parameters()
            ]
            for module in modules
        ],
        "modes": [bool(module.training) for module in modules],
    }


def _model_state_checks(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, bool]:
    tensors_equal = all(
        lhs.keys() == rhs.keys()
        and all(torch.equal(lhs[name], rhs[name]) for name in lhs)
        for lhs, rhs in zip(left["tensors"], right["tensors"])
    )
    grads_equal = True
    for lhs_module, rhs_module in zip(left["grads"], right["grads"]):
        for lhs, rhs in zip(lhs_module, rhs_module):
            if lhs is None or rhs is None:
                grads_equal = grads_equal and lhs is None and rhs is None
            else:
                grads_equal = grads_equal and torch.equal(lhs, rhs)
    return {
        "model_tensors_unchanged": bool(tensors_equal),
        "model_grads_unchanged": bool(grads_equal),
        "module_modes_unchanged": left["modes"] == right["modes"],
    }


def assert_model_state_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> None:
    checks = _model_state_checks(left, right)
    if not all(checks.values()):
        raise AssertionError(f"model state changed: {checks}")


def _restore_model_state(model_owner: Any, state: Mapping[str, Any]) -> None:
    for module, tensor_state, grad_state, mode in zip(
        _model_modules(model_owner),
        state["tensors"],
        state["grads"],
        state["modes"],
    ):
        module.load_state_dict(tensor_state, strict=True)
        for parameter, grad in zip(module.parameters(), grad_state):
            parameter.grad = None if grad is None else grad.detach().clone()
        module.train(bool(mode))


def evaluate_with_guards(
    model_owner: Any, evaluator: Callable[[], Mapping[str, Any]]
) -> tuple[Mapping[str, Any], dict[str, bool]]:
    """Evaluate once, detect mutation, and restore global RNG on every path."""

    model_before = model_state_snapshot(model_owner)
    rng_before = _global_rng_snapshot()
    try:
        payload = evaluator()
        model_after = model_state_snapshot(model_owner)
        checks = _model_state_checks(model_before, model_after)
        checks["global_python_numpy_torch_cuda_rng_unchanged"] = _global_rng_equal(
            rng_before, _global_rng_snapshot()
        )
        return payload, checks
    finally:
        _restore_global_rng(rng_before)
        current = model_state_snapshot(model_owner)
        if not all(_model_state_checks(model_before, current).values()):
            _restore_model_state(model_owner, model_before)


def _read_runner_manifest(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def load_source_bundle(
    root: str | Path, expected_arm: str, device: str | torch.device
) -> dict[str, Any]:
    """Resolve exactly one registered arm result, manifest and eval checkpoint."""

    arm_root = Path(root).resolve()
    if not arm_root.is_dir():
        raise FileNotFoundError(f"Stage C {expected_arm} root does not exist")
    result_path = arm_root / "result" / "stage_c_arm.json"
    checkpoint_path = arm_root / "checkpoints" / "update_250_eval.pt"
    status_path = arm_root / "arm_status.json"
    if not result_path.is_file() or not checkpoint_path.is_file() or not status_path.is_file():
        raise FileNotFoundError(
            f"Stage C {expected_arm} root lacks its exact result/status/update_250_eval.pt"
        )
    result_candidates = list(result_path.parent.glob("stage_c_arm*.json"))
    checkpoint_candidates = list(checkpoint_path.parent.glob("update_250_eval*.pt"))
    if result_candidates != [result_path] or checkpoint_candidates != [checkpoint_path]:
        raise ValueError(f"Stage C {expected_arm} root is ambiguous")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    parent_manifest = _read_runner_manifest(arm_root.parent / "runner_status.txt")
    return {
        "result": result,
        "checkpoint": checkpoint,
        "arm_status": status,
        "source_identity": {
            "root": str(arm_root),
            "result_path": str(result_path),
            "arm_status_path": str(status_path),
            "checkpoint_path": str(checkpoint_path),
            "source_commit": parent_manifest.get("source_commit"),
        },
    }


def _construct_model_owner(
    checkpoint: Mapping[str, Any], device: torch.device
) -> Any:
    from ha_ctse_process.variable_roster_event import VariableRosterEventCore

    bundle = checkpoint["event_architecture"]
    architecture = bundle["architecture_state"]
    rng_state = _global_rng_snapshot()
    try:
        owner = VariableRosterEventCore(
            architecture_mode=str(bundle["architecture_mode"]),
            obs_dim=int(architecture["obs_dim"]),
            critic_member_dim=int(architecture["critic_member_dim"]),
            critic_global_dim=int(architecture["critic_global_dim"]),
            n_skills=int(architecture["n_skills"]),
            action_dim=int(architecture["action_dim"]),
            member_hidden_dim=int(architecture["member_hidden_dim"]),
            high_hidden_dim=int(architecture["high_hidden_dim"]),
            low_hidden_dim=int(architecture["low_hidden_dim"]),
            skill_embedding_dim=int(architecture["skill_embedding_dim"]),
            gamma=float(architecture["gamma"]),
            gae_lambda=float(architecture["gae_lambda"]),
            environment_index=-1,
            device=device,
        )
    finally:
        _restore_global_rng(rng_state)
    return owner


def collect_arm(source: Mapping[str, Any], expected_arm: str, device: torch.device) -> dict[str, Any]:
    """Strictly restore and repeat one registered final stochastic evaluation."""

    from ha_ctse_process import train as process_train
    from ha_ctse_process.variable_roster_event import restore_event_model_only_checkpoint

    identity = validate_source_identity(source, expected_arm)
    if not identity["valid"]:
        return {
            "valid": False,
            "identity": identity,
            "parity": {"valid": False, "checks": {}, "reasons": ["source_identity"]},
            "provenance": {"valid": False, "checks": {}, "reasons": ["source_identity"]},
            "guard_checks": {},
            "source_tensors_unchanged": False,
        }
    checkpoint = source["checkpoint"]
    source_tensor_records = _tensor_records(checkpoint)
    owner = _construct_model_owner(checkpoint, device)
    normalizers, total_steps, update_idx = restore_event_model_only_checkpoint(
        checkpoint, model_owner=owner
    )
    strict_restore = (
        set(normalizers) == {"high", "low"}
        and all(
            state == {"schema_version": 1, "enabled": False, "kind": "identity"}
            for state in normalizers.values()
        )
        and total_steps == 320_000
        and update_idx == 250
    )
    evaluation, guards = evaluate_with_guards(
        owner,
        lambda: process_train._evaluate_event_model(
            owner,
            deterministic=False,
            capture_prefix=True,
            capture_forced_audit=True,
            capture_semantic_provenance=True,
        ),
    )
    parity = validate_registered_parity(source["result"], evaluation)
    provenance_payload = evaluation.get("semantic_provenance", {})
    provenance = validate_provenance(provenance_payload, expected_arm)
    guards["strict_model_only_restore"] = strict_restore
    source_tensors_unchanged = _tensors_unchanged(checkpoint, source_tensor_records)
    valid = bool(
        identity["valid"]
        and parity["valid"]
        and provenance["valid"]
        and all(guards.values())
        and source_tensors_unchanged
    )
    return {
        "valid": valid,
        "identity": identity,
        "parity": parity,
        "provenance": provenance,
        "guard_checks": guards,
        "source_tensors_unchanged": source_tensors_unchanged,
        "evaluation": evaluation,
        "raw_provenance": provenance_payload,
        "model_owner": owner,
        "source_tensor_records": source_tensor_records,
    }


def _registered_metrics(result: Mapping[str, Any]) -> dict[str, Any]:
    stochastic = result["final"]["stochastic"]
    forced = result["forced_audit"]
    return {
        "stochastic": {
            "persistent_mean": stochastic["persistent_mean"],
            "short_mean": stochastic["short_mean"],
            "utility_mean": stochastic["utility_mean"],
            "natural_skill_step_counts": stochastic["natural_skill_step_counts"],
        },
        "forced": {
            name: forced[name]
            for name in (
                "rho",
                "rho_ci95",
                "persistent_like_skill",
                "reactive_like_skill",
                "executable_naturally_used_skills",
            )
        },
    }


def write_audit_outputs(
    output_root: str | Path,
    raw_by_arm: Mapping[str, Mapping[str, Any]],
    result: Mapping[str, Any],
) -> None:
    """Write the four registered destinations with create-new semantics."""

    destination = Path(output_root)
    if destination.exists():
        raise FileExistsError("output root already exists")
    if set(raw_by_arm) != {"f0", "f1"}:
        raise ValueError("raw provenance requires exactly f0 and f1")
    for arm, raw in raw_by_arm.items():
        prohibited = _recursive_prohibited_fields(raw)
        if prohibited:
            raise ValueError(f"{arm} raw provenance contains prohibited fields: {prohibited}")
    safe_result = _json_safe(result)
    if not _finite_json_values(safe_result):
        raise ValueError("audit result contains non-finite values")
    raw_buffers: dict[str, bytes] = {}
    for arm, raw in raw_by_arm.items():
        buffer = io.BytesIO()
        torch.save(deepcopy(dict(raw)), buffer)
        raw_buffers[arm] = buffer.getvalue()
    result_text = json.dumps(safe_result, sort_keys=True, indent=2) + "\n"
    status_text = "\n".join(
        (
            "state=complete",
            "phase=terminal",
            f"status={safe_result.get('outcome', 'INVALID_ITERATION4_PROVENANCE_AUDIT')}",
            f"result_path={destination.resolve() / 'result' / 'iteration4_provenance_audit.json'}",
            "",
        )
    )
    destination.mkdir(parents=True, exist_ok=False)
    raw_root = destination / "raw"
    result_root = destination / "result"
    raw_root.mkdir(exist_ok=False)
    result_root.mkdir(exist_ok=False)
    for arm in ("f0", "f1"):
        with (raw_root / f"{arm}_provenance.pt").open("xb") as handle:
            handle.write(raw_buffers[arm])
    with (result_root / "iteration4_provenance_audit.json").open(
        "x", encoding="utf-8"
    ) as handle:
        handle.write(result_text)
    with (destination / "runner_status.txt").open("x", encoding="utf-8") as handle:
        handle.write(status_text)


def run_audit(
    f0_root: str | Path,
    f1_root: str | Path,
    *,
    output_root: str | Path,
    device: str = "cuda",
) -> dict[str, Any]:
    """Run the one-shot collection and frozen analysis, then write once."""

    destination = Path(output_root).resolve()
    if destination.exists():
        raise FileExistsError("output root already exists")
    if str(device).lower() != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("the registered provenance audit requires available CUDA")
    source_roots = {Path(f0_root).resolve(), Path(f1_root).resolve()}
    if len(source_roots) != 2:
        raise ValueError("f0 and f1 must be distinct registered arm roots")
    if any(destination == root or root in destination.parents for root in source_roots):
        raise ValueError("output root must be separate from both registered source roots")

    target_device = torch.device("cuda")
    rng_before = _global_rng_snapshot()
    try:
        sources = {
            "f0": load_source_bundle(f0_root, "f0", target_device),
            "f1": load_source_bundle(f1_root, "f1", target_device),
        }
        collections = {
            arm: collect_arm(sources[arm], arm, target_device)
            for arm in ("f0", "f1")
        }
        m0_valid = all(collections[arm]["valid"] for arm in ("f0", "f1"))
        if not m0_valid:
            raise RuntimeError(
                "INVALID_ITERATION4_PROVENANCE_AUDIT: source, parity, provenance, "
                "model-state, or RNG M0 failed"
            )
        analyses = {}
        for arm in ("f0", "f1"):
            owner = collections[arm]["model_owner"]
            model_before_analysis = model_state_snapshot(owner)
            actor_mode = bool(owner.low_actor.training)
            try:
                owner.low_actor.eval()
                analyses[arm] = analyze_semantics(
                    collections[arm]["raw_provenance"], owner.low_actor
                )
            finally:
                owner.low_actor.train(actor_mode)
            analysis_state_checks = _model_state_checks(
                model_before_analysis, model_state_snapshot(owner)
            )
            collections[arm]["guard_checks"].update(
                {
                    f"analysis_{name}": valid
                    for name, valid in analysis_state_checks.items()
                }
            )
            collections[arm]["guard_checks"][
                "source_tensors_after_analysis_unchanged"
            ] = _tensors_unchanged(
                sources[arm]["checkpoint"],
                collections[arm]["source_tensor_records"],
            )
            if not all(collections[arm]["guard_checks"].values()):
                raise RuntimeError(
                    "INVALID_ITERATION4_PROVENANCE_AUDIT: model or source state "
                    f"changed during {arm} analysis"
                )
        global_rng_unchanged = _global_rng_equal(rng_before, _global_rng_snapshot())
        if not global_rng_unchanged:
            raise RuntimeError(
                "INVALID_ITERATION4_PROVENANCE_AUDIT: global RNG changed during analysis"
            )
        outcome = frozen_outcome(analyses["f1"]["metrics"])
        source_identity = {}
        for arm in ("f0", "f1"):
            bundle = sources[arm]["checkpoint"]["event_architecture"]
            source_identity[arm] = {
                **sources[arm]["source_identity"],
                "checkpoint_schema_version": sources[arm]["checkpoint"]
                ["checkpoint_schema_version"],
                "event_architecture_schema_version": bundle[
                    "event_architecture_schema_version"
                ],
                "architecture_mode": bundle["architecture_mode"],
                "update_idx": bundle["update_idx"],
                "total_steps": bundle["total_steps"],
                "snapshot_capability_name": bundle["snapshot_capability_name"],
                "snapshot_capability_version": bundle[
                    "snapshot_capability_version"
                ],
            }
        result = _json_safe(
            {
                "schema_version": 1,
                "stage": "iteration4_stage_c_semantics_provenance_audit",
                "selector_arm": "f1",
                "outcome": outcome,
                "m0": {
                    "valid": True,
                    "global_rng_unchanged": global_rng_unchanged,
                    "arms": {
                        arm: {
                            "source_identity": collections[arm]["identity"],
                            "registered_parity": collections[arm]["parity"],
                            "provenance": collections[arm]["provenance"],
                            "guard_checks": collections[arm]["guard_checks"],
                            "source_tensors_unchanged": collections[arm][
                                "source_tensors_unchanged"
                            ],
                        }
                        for arm in ("f0", "f1")
                    },
                },
                "source_identity": source_identity,
                "registered_metrics": {
                    arm: _registered_metrics(sources[arm]["result"])
                    for arm in ("f0", "f1")
                },
                "support_counts": {
                    arm: collections[arm]["provenance"]["support_counts"]
                    for arm in ("f0", "f1")
                },
                "semantic_metrics": analyses,
                "frozen_contract": {
                    "delta": DELTA,
                    "delta_stratum": DELTA_STRATUM,
                    "lineage_guard": LINEAGE_THRESHOLD,
                    "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
                    "bootstrap_seed": BOOTSTRAP_SEED,
                    "shuffle_seed": SHUFFLE_SEED,
                    "reference_episodes": list(REFERENCE_EPISODES),
                    "inference_episodes": list(INFERENCE_EPISODES),
                    "ordinary_marl_objection": (
                        "Outcome D remains compatible with redundant latent modes "
                        "because Stage C has no utility advantage over Stage B."
                    ),
                },
                "claim_ceiling": CLAIM_CEILING,
            }
        )
        if not _finite_json_values(result):
            raise RuntimeError("INVALID_ITERATION4_PROVENANCE_AUDIT: non-finite result")
        write_audit_outputs(
            destination,
            {
                arm: collections[arm]["raw_provenance"] for arm in ("f0", "f1")
            },
            result,
        )
        return result
    finally:
        _restore_global_rng(rng_before)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One-shot Stage C semantic provenance audit"
    )
    parser.add_argument("--f0", required=True, help="registered Stage C F0 arm root")
    parser.add_argument("--f1", required=True, help="registered Stage C F1 arm root")
    parser.add_argument("--output-root", required=True, help="new audit log root")
    parser.add_argument("--device", default="cuda", choices=("cuda",))
    arguments = parser.parse_args(argv)
    run_audit(
        arguments.f0,
        arguments.f1,
        output_root=arguments.output_root,
        device=arguments.device,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
