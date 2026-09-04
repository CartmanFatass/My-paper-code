"""Legacy raw-checkpoint validator retained behind the metrics-only gate.

Clarification ``.03`` deliberately leaves AUC, diagnostic aggregation and
scientific interpretation unassigned.  Formal publication uses the lossless
table authority in :mod:`b1_metrics_artifact`; this compatibility surface
cannot authorize publication or emit a scientific branch.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import math
from typing import Any, Mapping, Sequence

from .artifact import canonical_json_bytes
from .b0 import ARMS
from .b1_contract import B1_CHECKPOINT_UPDATES, B1_RUN_NAME, B1_SEEDS
from .b1_metrics_artifact import FORMAL_ANALYSIS_BOUND


RAW_CHECKPOINT_SCHEMA = "cbsc_omrc_b01_b1_raw_checkpoint_evaluation_v1"
B1_RAW_ANALYSIS_SCHEMA = "cbsc_omrc_b01_b1_raw_analysis_v1"
DECISION_PENDING = "DECISION_PENDING"
DECISION_REASONS = (
    "AUC_DEFINITION_PENDING",
    "DIAGNOSTIC_AGGREGATION_PENDING",
    "SCIENTIFIC_BRANCH_CLASSIFIER_PENDING",
)
_PANELS = ("EVAL_STOCHASTIC", "EVAL_MOTIF")
_ACTIONS = {"SERVE", "REFRESH", "SAFE_FALLBACK"}
_ARM_LABELS = {
    "STRUCT-CURRENTNESS-GRU": "STRUCT",
    "RAW-GRU": "RAW",
    "PI-GRU": "PI",
    "DERANGED-CURRENTNESS-GRU": "DERANGED",
}


class B1AnalysisError(ValueError):
    """Raw B1 evaluator evidence is incomplete or noncanonical."""


def _ratio(value: object, *, name: str) -> Fraction:
    if not isinstance(value, Mapping):
        raise B1AnalysisError(f"{name} must be an exact ratio record")
    if set(value) != {"numerator", "denominator", "float"}:
        raise B1AnalysisError(f"{name} must contain only numerator, denominator, and float")
    numerator = value["numerator"]
    denominator = value["denominator"]
    floating = value["float"]
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise B1AnalysisError(f"{name} has an invalid exact ratio")
    if type(floating) is not float or not math.isfinite(floating):
        raise B1AnalysisError(f"{name} float must be finite")
    exact = Fraction(numerator, denominator)
    if exact.numerator != numerator or exact.denominator != denominator:
        raise B1AnalysisError(f"{name} ratio must be reduced with a positive denominator")
    if float(exact) != floating:
        raise B1AnalysisError(f"{name} float does not match its exact ratio")
    return exact


def _ratio_record(value: Fraction) -> dict[str, int | float]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "float": float(value),
    }


def _require_exact_int_counts(name: str, value: object, keys: set[str]) -> None:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise B1AnalysisError(f"{name} keys differ from the raw evaluator contract")
    if any(type(item) is not int or item < 0 for item in value.values()):
        raise B1AnalysisError(f"{name} must contain nonnegative exact integer counts")


def _validate_decision(value: object, *, name: str, opportunity: int) -> None:
    if not isinstance(value, Mapping):
        raise B1AnalysisError(f"{name} is not a raw decision record")
    required = {
        "opportunity_index",
        "action",
        "oracle_action",
        "valid",
        "request_active",
        "decision_reward",
        "settlement_reward",
        "regret",
        "motif_family",
        "motif_side",
        "designated_comparison",
    }
    if set(value) != required:
        raise B1AnalysisError(f"{name} fields differ from the raw diagnostic surface")
    if value["opportunity_index"] != opportunity:
        raise B1AnalysisError(f"{name} opportunity order differs")
    if value["action"] not in _ACTIONS or value["oracle_action"] not in _ACTIONS:
        raise B1AnalysisError(f"{name} contains an illegal decision action")
    for field in ("valid", "request_active", "designated_comparison"):
        if type(value[field]) is not bool:
            raise B1AnalysisError(f"{name}.{field} must be a literal Boolean fact")
    for field in ("decision_reward", "settlement_reward", "regret"):
        _ratio(value[field], name=f"{name}.{field}")
    if value["motif_family"] is not None and type(value["motif_family"]) is not int:
        raise B1AnalysisError(f"{name}.motif_family differs")
    if value["motif_side"] not in {None, "A", "B"}:
        raise B1AnalysisError(f"{name}.motif_side differs")


def _validate_episode(
    value: object, *, arm: str, seed: int, panel: str, episode_id: int
) -> tuple[Fraction, Fraction]:
    if not isinstance(value, Mapping):
        raise B1AnalysisError("raw evaluation episode is not a mapping")
    required = {
        "identity",
        "return",
        "oracle_return",
        "oracle_regret",
        "action_counts",
        "diagnostic_counts",
        "decisions",
    }
    if set(value) != required:
        raise B1AnalysisError("raw evaluation episode fields differ")
    identity = value["identity"]
    expected_identity = {
        "run_name": B1_RUN_NAME,
        "seed": seed,
        "split": panel,
        "episode_id": episode_id,
    }
    if identity != expected_identity:
        raise B1AnalysisError(f"{arm} raw episode is not the exact B1 run identity")
    episode_return = _ratio(value["return"], name="return")
    oracle_return = _ratio(value["oracle_return"], name="oracle_return")
    regret = _ratio(value["oracle_regret"], name="oracle_regret")
    if oracle_return - episode_return != regret:
        raise B1AnalysisError("episode return and oracle regret arithmetic differs")
    _require_exact_int_counts("action_counts", value["action_counts"], _ACTIONS)
    _require_exact_int_counts(
        "diagnostic_counts",
        value["diagnostic_counts"],
        {
            "oracle_action_correct",
            "invalid_serve",
            "missed_serve",
            "unnecessary_refresh",
            "missed_refresh",
            "inactive_fallback",
        },
    )
    decisions = value["decisions"]
    if not isinstance(decisions, list) or len(decisions) != 24:
        raise B1AnalysisError("raw episode must preserve exactly 24 decision records")
    for opportunity, decision in enumerate(decisions):
        _validate_decision(
            decision,
            name=f"{arm}/{seed}/{panel}/{episode_id}/{opportunity}",
            opportunity=opportunity,
        )
    if sum(value["action_counts"].values()) != 24:
        raise B1AnalysisError("raw action counts do not cover exactly 24 decisions")
    return episode_return, regret


def compute_b1_analysis(
    raw_checkpoint_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate complete B1 raw evidence and return a fail-closed analysis packet.

    No AUC, diagnostic aggregate, competence classification, or scientific
    branch is inferred while their literal law remains pending.
    """

    if not isinstance(raw_checkpoint_records, Sequence) or isinstance(
        raw_checkpoint_records, (str, bytes, bytearray)
    ):
        raise B1AnalysisError("raw checkpoint records must be a sequence")
    if len(raw_checkpoint_records) != len(ARMS) * len(B1_SEEDS) * len(B1_CHECKPOINT_UPDATES):
        raise B1AnalysisError("B1 analysis requires the complete 48 checkpoint records")

    expected_keys = {
        (arm, seed, update)
        for arm in ARMS
        for seed in B1_SEEDS
        for update in B1_CHECKPOINT_UPDATES
    }
    observed: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    summaries: dict[tuple[str, int, int], dict[str, Any]] = {}
    episode_values: dict[tuple[str, int, int, str, int], Fraction] = {}
    for raw in raw_checkpoint_records:
        if not isinstance(raw, Mapping):
            raise B1AnalysisError("raw checkpoint record is not a mapping")
        required = {
            "schema",
            "run_name",
            "arm",
            "seed",
            "checkpoint_update",
            "checkpoint_identity",
            "numerical_finite",
            "invalid_masking_count",
            "episodes",
        }
        if set(raw) != required:
            raise B1AnalysisError("raw checkpoint record fields differ")
        if raw["schema"] != RAW_CHECKPOINT_SCHEMA or raw["run_name"] != B1_RUN_NAME:
            raise B1AnalysisError("raw checkpoint record is not the exact B1 run identity")
        key = (raw["arm"], raw["seed"], raw["checkpoint_update"])
        if key not in expected_keys:
            raise B1AnalysisError("raw checkpoint record lies outside frozen B1 coverage")
        if key in observed:
            raise B1AnalysisError("duplicate raw B1 checkpoint record")
        if type(raw["checkpoint_identity"]) is not str or not raw["checkpoint_identity"]:
            raise B1AnalysisError("checkpoint identity must be a nonempty string")
        if raw["numerical_finite"] is not True:
            raise B1AnalysisError("raw checkpoint numerical finite audit failed")
        if type(raw["invalid_masking_count"]) is not int or raw["invalid_masking_count"] < 0:
            raise B1AnalysisError("invalid masking count differs")
        episodes = raw["episodes"]
        if not isinstance(episodes, list) or len(episodes) != 64:
            raise B1AnalysisError("each checkpoint must preserve exactly 64 held-out episodes")
        panel_ids: dict[str, set[int]] = {panel: set() for panel in _PANELS}
        returns: list[Fraction] = []
        regrets: list[Fraction] = []
        for episode in episodes:
            if not isinstance(episode, Mapping) or not isinstance(episode.get("identity"), Mapping):
                raise B1AnalysisError("raw episode identity is absent")
            panel = episode["identity"].get("split")
            episode_id = episode["identity"].get("episode_id")
            if panel not in _PANELS or type(episode_id) is not int or not 0 <= episode_id < 32:
                raise B1AnalysisError("raw episode panel identity differs")
            if episode_id in panel_ids[panel]:
                raise B1AnalysisError("duplicate raw held-out episode identity")
            panel_ids[panel].add(episode_id)
            episode_return, regret = _validate_episode(
                episode,
                arm=raw["arm"],
                seed=raw["seed"],
                panel=panel,
                episode_id=episode_id,
            )
            returns.append(episode_return)
            regrets.append(regret)
            episode_values[(raw["arm"], raw["seed"], raw["checkpoint_update"], panel, episode_id)] = episode_return
        if any(ids != set(range(32)) for ids in panel_ids.values()):
            raise B1AnalysisError("raw held-out panel coverage differs")
        observed[key] = raw
        summaries[key] = {
            "update": raw["checkpoint_update"],
            "checkpoint_identity": raw["checkpoint_identity"],
            "mean_return": _ratio_record(sum(returns, Fraction(0)) / 64),
            "mean_oracle_regret": _ratio_record(sum(regrets, Fraction(0)) / 64),
            "episode_count": 64,
            "decision_count": 1536,
        }
    if set(observed) != expected_keys:
        raise B1AnalysisError("raw B1 checkpoint coverage is incomplete")

    curves: list[dict[str, Any]] = []
    for arm in ARMS:
        for seed in B1_SEEDS:
            points = [summaries[(arm, seed, update)] for update in B1_CHECKPOINT_UPDATES]
            curves.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "points": points,
                    "terminal_return": points[-1]["mean_return"],
                    "terminal_oracle_regret": points[-1]["mean_oracle_regret"],
                    "normalized_return_auc": None,
                    "auc_status": "AUC_DEFINITION_PENDING",
                }
            )

    paired: list[dict[str, Any]] = []
    structured_arm = ARMS[0]
    for comparator in ARMS:
        if comparator == structured_arm:
            continue
        for seed in B1_SEEDS:
            for update in B1_CHECKPOINT_UPDATES:
                for panel in _PANELS:
                    for episode_id in range(32):
                        structured = episode_values[(structured_arm, seed, update, panel, episode_id)]
                        control = episode_values[(comparator, seed, update, panel, episode_id)]
                        paired.append(
                            {
                                "seed": seed,
                                "update": update,
                                "panel": panel,
                                "episode_id": episode_id,
                                "contrast": f"STRUCT_MINUS_{_ARM_LABELS[comparator]}",
                                "structured_return": _ratio_record(structured),
                                "comparator_return": _ratio_record(control),
                                "paired_difference": _ratio_record(structured - control),
                            }
                        )

    raw_competence = [
        {
            "arm": ARMS[1],
            "seed": seed,
            "terminal_checkpoint_identity": observed[(ARMS[1], seed, 48)]["checkpoint_identity"],
            "stochastic_episode_records": [
                episode
                for episode in observed[(ARMS[1], seed, 48)]["episodes"]
                if episode["identity"]["split"] == "EVAL_STOCHASTIC"
            ],
            "competence_predicate": None,
            "status": "DIAGNOSTIC_AGGREGATION_PENDING",
        }
        for seed in B1_SEEDS
    ]
    packet = {
        "schema": B1_RAW_ANALYSIS_SCHEMA,
        "run_name": B1_RUN_NAME,
        "arms": list(ARMS),
        "seeds": list(B1_SEEDS),
        "checkpoint_updates": list(B1_CHECKPOINT_UPDATES),
        "per_seed_curves": curves,
        "terminal_records": [
            {
                "arm": curve["arm"],
                "seed": curve["seed"],
                "return": curve["terminal_return"],
                "oracle_regret": curve["terminal_oracle_regret"],
            }
            for curve in curves
        ],
        "paired_heldout_differences": paired,
        "raw_competence_observables": raw_competence,
        "raw_checkpoint_records": deepcopy(list(raw_checkpoint_records)),
        "normalized_return_auc": None,
        "diagnostic_aggregates": None,
        "scientific_branch": None,
        "decision": DECISION_PENDING,
        "decision_reasons": list(DECISION_REASONS),
    }
    try:
        canonical_json_bytes(packet)
    except Exception as exc:
        raise B1AnalysisError("raw B1 analysis is not finite canonical JSON") from exc
    return packet


__all__ = [
    "B1AnalysisError",
    "B1_RAW_ANALYSIS_SCHEMA",
    "DECISION_PENDING",
    "DECISION_REASONS",
    "FORMAL_ANALYSIS_BOUND",
    "RAW_CHECKPOINT_SCHEMA",
    "compute_b1_analysis",
]
