"""Descriptive B1 curves, published directly by the runner.

Section-11 recast, owner decision 3 of 2026-09-02
(``docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md``;
reviewer reading in ``docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md``
A.2/A.4).  Before the recast the manifest carried every derived quantity as a
literal null so that a separate Convergence consumer would recompute it.  That
consumer-recompute boundary is demoted by evidence spec §11.6, so this module
computes the descriptive quantities from the runner's own materialized raw
tables and the manifest publishes them.

What is published here is descriptive and non-decisional: per-checkpoint
held-out returns, held-out action counts and serve rate, the mechanical
RAW-competence flags, training-episode action counts, and one exposure line per
arm/seed.  No AUC normalization, arm contrast, threshold, branch, polarity,
promotion flag or B2 trigger is computed; those fields remain literal null in
the manifest exactly as before.
"""

from __future__ import annotations

from fractions import Fraction
import struct
from typing import Any, Mapping, Sequence


B1_DESCRIPTIVE_SCHEMA = "cbsc_omrc_b01_b1_descriptive_curves_v1"
DESCRIPTIVE_STATUS_PUBLISHED = "PUBLISHED_DIRECTLY"
DESCRIPTIVE_STATUS_UNAVAILABLE = "UNAVAILABLE"
DESCRIPTIVE_AUTHORITY = (
    "docs/research/candidates/capability_bound_semantic_currentness/"
    "CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md"
)
DESCRIPTIVE_INTERPRETATION = (
    "Descriptive and non-decisional. These are direct summaries of this "
    "attempt's own raw tables, published under the section-11 recast instead "
    "of left null for a consumer to recompute. They carry no AUC "
    "normalization, arm contrast, threshold, branch, polarity, promotion "
    "eligibility or B2 trigger."
)

CHECKPOINT_UPDATES = (0, 12, 24, 48)
ARM_NAMES = (
    "STRUCT-CURRENTNESS-GRU",
    "RAW-GRU",
    "PI-GRU",
    "DERANGED-CURRENTNESS-GRU",
)
SPLIT_NAMES = {0: "TRAIN", 1: "EVAL_STOCHASTIC", 2: "EVAL_MOTIF"}
SCIENTIFIC_ACTIONS = ("SERVE", "REFRESH", "SAFE_FALLBACK")


class B1DescriptiveError(ValueError):
    """Materialized rows cannot support a direct descriptive summary."""


def _ratio_record(value: Fraction) -> dict[str, int | float]:
    floating = float(value)
    if floating != floating or floating in (float("inf"), float("-inf")):
        raise B1DescriptiveError("descriptive ratio is not finite")
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "float": floating,
    }


def _read_fraction(value: object, *, label: str) -> Fraction:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"numerator", "denominator"}
        or type(value["numerator"]) is not int
        or type(value["denominator"]) is not int
        or value["denominator"] <= 0
    ):
        raise B1DescriptiveError(f"{label} is not an exact fraction record")
    return Fraction(value["numerator"], value["denominator"])


def _fp32_from_bits(value: object, *, label: str) -> float:
    if type(value) is str:
        if len(value) != 8 or any(character not in "0123456789abcdef" for character in value):
            raise B1DescriptiveError(f"{label} is not an FP32 bit pattern")
        value = int(value, 16)
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise B1DescriptiveError(f"{label} is not an FP32 bit pattern")
    number = struct.unpack(">f", struct.pack(">I", value))[0]
    if number != number or number in (float("inf"), float("-inf")):
        raise B1DescriptiveError(f"{label} is not a finite FP32 value")
    return number


def _rows(value: object, *, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise B1DescriptiveError(f"{label} must be a sequence of rows")
    rows = list(value)
    if any(not isinstance(row, Mapping) for row in rows):
        raise B1DescriptiveError(f"{label} contains a non-record row")
    return rows


def _arm_name(arm_order: object) -> str:
    if type(arm_order) is not int or not 0 <= arm_order < len(ARM_NAMES):
        raise B1DescriptiveError("arm order lies outside the canonical arm list")
    return ARM_NAMES[arm_order]


def _split_name(split_order: object) -> str:
    if split_order not in SPLIT_NAMES:
        raise B1DescriptiveError("split order lies outside the canonical split list")
    return SPLIT_NAMES[split_order]


def _heldout_return_curves(
    per_tape_curves: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Mean, minimum and maximum per-tape episode return at each checkpoint."""

    grouped: dict[tuple[int, int, int], list[Mapping[str, Any]]] = {}
    for row in per_tape_curves:
        for field in ("seed", "arm_order", "split_order"):
            if field not in row:
                raise B1DescriptiveError("per-tape curve row lacks a canonical key")
        key = (int(row["seed"]), int(row["arm_order"]), int(row["split_order"]))
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        seed, arm_order, split_order = key
        rows = grouped[key]
        points: list[dict[str, Any]] = []
        for update in CHECKPOINT_UPDATES:
            field = f"episode_return_update_{update}"
            values = [
                _read_fraction(row.get(field), label=field) for row in rows
            ]
            if not values:
                raise B1DescriptiveError("per-tape curve group is empty")
            total = sum(values, Fraction(0))
            points.append({
                "checkpoint_update": update,
                "mean_episode_return": _ratio_record(total / len(values)),
                "min_episode_return": _ratio_record(min(values)),
                "max_episode_return": _ratio_record(max(values)),
            })
        output.append({
            "seed": seed,
            "arm_order": arm_order,
            "arm": _arm_name(arm_order),
            "split_order": split_order,
            "split": _split_name(split_order),
            "tape_count": len(rows),
            "points": points,
        })
    return output


def _heldout_action_counts(
    policy_decisions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Held-out scientific-action counts and serve rate per checkpoint."""

    grouped: dict[tuple[int, int, int, int], list[int]] = {}
    for row in policy_decisions:
        for field in ("seed", "arm_order", "split_order", "checkpoint_update"):
            if field not in row:
                raise B1DescriptiveError("policy-decision row lacks a canonical key")
        action = row.get("selected_action")
        if type(action) is not int or not 0 <= action < len(SCIENTIFIC_ACTIONS):
            raise B1DescriptiveError("policy-decision selected action differs")
        key = (
            int(row["seed"]), int(row["arm_order"]),
            int(row["split_order"]), int(row["checkpoint_update"]),
        )
        grouped.setdefault(key, []).append(action)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        seed, arm_order, split_order, checkpoint_update = key
        actions = grouped[key]
        counts = {
            name: sum(1 for action in actions if action == index)
            for index, name in enumerate(SCIENTIFIC_ACTIONS)
        }
        decision_count = len(actions)
        output.append({
            "seed": seed,
            "arm_order": arm_order,
            "arm": _arm_name(arm_order),
            "split_order": split_order,
            "split": _split_name(split_order),
            "checkpoint_update": checkpoint_update,
            "decision_count": decision_count,
            "action_counts": counts,
            "distinct_action_count": sum(1 for value in counts.values() if value > 0),
            "serve_rate": _ratio_record(
                Fraction(counts["SERVE"], decision_count)
            ) if decision_count else None,
        })
    return output


def _training_episode_action_counts(
    training_episodes: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Training-side action counts, summed over the arm/seed's episodes."""

    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    for row in training_episodes:
        for field in ("seed", "arm_order"):
            if field not in row:
                raise B1DescriptiveError("training-episode row lacks a canonical key")
        grouped.setdefault((int(row["seed"]), int(row["arm_order"])), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        seed, arm_order = key
        rows = grouped[key]
        counts: dict[str, int] = {}
        for name, field in zip(
            SCIENTIFIC_ACTIONS,
            ("action_count_serve", "action_count_refresh", "action_count_safe_fallback"),
            strict=True,
        ):
            total = 0
            for row in rows:
                value = row.get(field)
                if type(value) is not int or value < 0:
                    raise B1DescriptiveError(f"training episode {field} differs")
                total += value
            counts[name] = total
        returns = []
        for row in rows:
            value = row.get("episode_return")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise B1DescriptiveError("training episode return is not numeric")
            floating = float(value)
            if floating != floating or floating in (float("inf"), float("-inf")):
                raise B1DescriptiveError("training episode return is not finite")
            returns.append(floating)
        output.append({
            "seed": seed,
            "arm_order": arm_order,
            "arm": _arm_name(arm_order),
            "episode_count": len(rows),
            "action_counts": counts,
            "first_episode_return": returns[0] if returns else None,
            "final_episode_return": returns[-1] if returns else None,
        })
    return output


def _exposure_line(
    optimizer_steps: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """One machine-generated exposure statement per arm/seed (spec §11.4).

    The learner's ability to move inside its budget is stated by the realized
    Adam step count, whether the parameter digest actually changed across those
    steps, and the post-clip gradient-norm magnitudes that produced the moves.
    """

    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    for row in optimizer_steps:
        for field in ("seed", "arm_order", "optimizer_step_count"):
            if field not in row:
                raise B1DescriptiveError("optimizer-step row lacks a canonical key")
        grouped.setdefault((int(row["seed"]), int(row["arm_order"])), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        seed, arm_order = key
        rows = sorted(grouped[key], key=lambda item: int(item["optimizer_step_count"]))
        digests: list[str] = []
        norms: list[float] = []
        for row in rows:
            digest = row.get("parameter_sha256_after_step")
            if type(digest) is not str or len(digest) != 64:
                raise B1DescriptiveError("optimizer-step parameter digest differs")
            digests.append(digest)
            norms.append(_fp32_from_bits(
                row.get("postclip_gradient_norm_fp32_bits"),
                label="postclip gradient norm",
            ))
        output.append({
            "seed": seed,
            "arm_order": arm_order,
            "arm": _arm_name(arm_order),
            "optimizer_step_count": len(rows),
            "final_optimizer_step_count": int(rows[-1]["optimizer_step_count"]),
            "distinct_parameter_digest_count": len(set(digests)),
            "first_parameter_sha256": digests[0],
            "final_parameter_sha256": digests[-1],
            "parameters_moved": len(set(digests)) > 1,
            "postclip_gradient_norm_first": norms[0],
            "postclip_gradient_norm_final": norms[-1],
            "postclip_gradient_norm_max": max(norms),
            "postclip_gradient_norm_min": min(norms),
            "postclip_gradient_norm_sum": sum(norms),
        })
    return output


def _competence_flags(
    raw_competence: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Republish the mechanical RAW-competence gate's own outputs."""

    output: list[dict[str, Any]] = []
    for row in sorted(raw_competence, key=lambda item: int(item.get("seed", -1))):
        if "seed" not in row or "raw_competence_pass" not in row:
            raise B1DescriptiveError("RAW competence row lacks its canonical fields")
        components = row.get("components")
        inputs = row.get("inputs")
        if not isinstance(components, Mapping) or not isinstance(inputs, Mapping):
            raise B1DescriptiveError("RAW competence row lacks components/inputs")
        output.append({
            "seed": int(row["seed"]),
            "raw_competence_pass": row["raw_competence_pass"],
            "components": dict(components),
            "raw_mean_return": inputs.get("raw_mean_return"),
            "always_refresh_mean_return": inputs.get("always_refresh_mean_return"),
            "always_safe_mean_return": inputs.get("always_safe_mean_return"),
            "easy_open_serve_fraction": inputs.get("easy_open_serve_fraction"),
            "easy_open_eligible_count": inputs.get("easy_open_eligible_count"),
            "easy_open_serve_count": inputs.get("easy_open_serve_count"),
            "raw_action_counts": dict(inputs.get("raw_action_counts") or {}),
            "oracle_action_counts": dict(inputs.get("oracle_action_counts") or {}),
            "mask_violation_count": inputs.get("mask_violation_count"),
            "nonfinite_count": inputs.get("nonfinite_count"),
            "missing_record_count": inputs.get("missing_record_count"),
            "duplicate_record_count": inputs.get("duplicate_record_count"),
        })
    return output


def compute_b1_descriptive_curves(
    *,
    per_tape_curves: Sequence[Mapping[str, Any]],
    policy_decisions: Sequence[Mapping[str, Any]],
    training_episodes: Sequence[Mapping[str, Any]],
    optimizer_steps: Sequence[Mapping[str, Any]],
    raw_competence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarize this attempt's own materialized tables, descriptively."""

    return {
        "schema": B1_DESCRIPTIVE_SCHEMA,
        "status": DESCRIPTIVE_STATUS_PUBLISHED,
        "authority": DESCRIPTIVE_AUTHORITY,
        "interpretation": DESCRIPTIVE_INTERPRETATION,
        "heldout_return_curves": _heldout_return_curves(
            _rows(per_tape_curves, label="per_tape_curves")
        ),
        "heldout_action_counts": _heldout_action_counts(
            _rows(policy_decisions, label="policy_decisions")
        ),
        "training_episode_action_counts": _training_episode_action_counts(
            _rows(training_episodes, label="training_episodes")
        ),
        "exposure_line": _exposure_line(
            _rows(optimizer_steps, label="optimizer_steps")
        ),
        "raw_competence_flags": _competence_flags(
            _rows(raw_competence, label="raw_competence")
        ),
    }


def unavailable_descriptive_curves(reason: str) -> dict[str, Any]:
    """Record that no descriptive summary could be produced, and why.

    Per owner decision 7 (2026-09-02) a missing measurement downgrades and
    records; it never annuls or quarantines.  A publication path that cannot
    summarize still publishes, carrying the reason.
    """

    if not isinstance(reason, str) or not reason.strip():
        raise B1DescriptiveError("descriptive unavailability requires a reason")
    return {
        "schema": B1_DESCRIPTIVE_SCHEMA,
        "status": DESCRIPTIVE_STATUS_UNAVAILABLE,
        "authority": DESCRIPTIVE_AUTHORITY,
        "interpretation": DESCRIPTIVE_INTERPRETATION,
        "reason": reason,
        "heldout_return_curves": [],
        "heldout_action_counts": [],
        "training_episode_action_counts": [],
        "exposure_line": [],
        "raw_competence_flags": [],
    }


def validate_descriptive_curves(value: object) -> dict[str, Any]:
    """Structural validation of a published descriptive packet."""

    if not isinstance(value, Mapping):
        raise B1DescriptiveError("descriptive packet must be a mapping")
    packet = dict(value)
    lists = (
        "heldout_return_curves", "heldout_action_counts",
        "training_episode_action_counts", "exposure_line",
        "raw_competence_flags",
    )
    base = {"schema", "status", "authority", "interpretation", *lists}
    if packet.get("status") == DESCRIPTIVE_STATUS_UNAVAILABLE:
        base = base | {"reason"}
    if set(packet) != base:
        raise B1DescriptiveError("descriptive packet fields differ")
    if packet["schema"] != B1_DESCRIPTIVE_SCHEMA:
        raise B1DescriptiveError("descriptive packet schema differs")
    if packet["status"] not in (
        DESCRIPTIVE_STATUS_PUBLISHED, DESCRIPTIVE_STATUS_UNAVAILABLE
    ):
        raise B1DescriptiveError("descriptive packet status differs")
    if packet["authority"] != DESCRIPTIVE_AUTHORITY:
        raise B1DescriptiveError("descriptive packet authority differs")
    if packet["interpretation"] != DESCRIPTIVE_INTERPRETATION:
        raise B1DescriptiveError("descriptive packet interpretation differs")
    for name in lists:
        if not isinstance(packet[name], list):
            raise B1DescriptiveError(f"descriptive {name} must be a list")
    if packet["status"] == DESCRIPTIVE_STATUS_PUBLISHED and not any(
        packet[name] for name in lists
    ):
        raise B1DescriptiveError("published descriptive packet is empty")
    return packet


__all__ = [
    "B1DescriptiveError",
    "B1_DESCRIPTIVE_SCHEMA",
    "DESCRIPTIVE_AUTHORITY",
    "DESCRIPTIVE_INTERPRETATION",
    "DESCRIPTIVE_STATUS_PUBLISHED",
    "DESCRIPTIVE_STATUS_UNAVAILABLE",
    "compute_b1_descriptive_curves",
    "unavailable_descriptive_curves",
    "validate_descriptive_curves",
]
