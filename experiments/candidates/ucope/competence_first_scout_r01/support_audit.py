"""Read-only odd-support versus even-heldout checkpoint audit.

This module never trains, executes the host, constructs an optimizer, or writes
checkpoint state.  Its sole production input is the accepted B1-04 complete
tree frozen by the prospective contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence
import contextlib
import ctypes
import hashlib
import io
import json
import math
import os
import shutil
import stat
import tempfile
import threading
import time

from .contract import CONTEXTS, OBJECT_ID as B1_OBJECT_ID, RunBinding, ScoutConfig, context_id
from .oracle import (
    direct_probe,
    expected_tail,
    joint_count_probability,
    optimal_tail,
    posterior_short,
)
from .model import root_basis, tail_basis, x_features
from .rng import rng_contract


OBJECT_ID = "UCOPE-A-RECON-B1-ODD-SUPPORT-VS-EVEN-HELDOUT-COMPETENCE-AUDIT-R01"
FORMAT = "UCOPE_B1_ODD_SUPPORT_AUDIT_R01_V1"
ODD_PERIODS = (1, 3, 5, 7, 9)
EVEN_PERIODS = (2, 4, 6, 8)
CHECKPOINT_UPDATES = (40, 80, 160, 320)
ARMS = ("MT-XF-FLEX", "FT-XF-FLEX", "FT-XF-BC")
SEEDS = (
    "ucope-scout-r01-b1-fresh-00",
    "ucope-scout-r01-b1-fresh-01",
    "ucope-scout-r01-b1-fresh-02",
)
MINIMUM_MEMORY_BYTES = 4 * 1024**3
WALL_CAP_SECONDS = 300.0
RSS_CAP_BYTES = 512 * 1024**2
SCRATCH_CAP_BYTES = 64 * 1024**2
DURABLE_CAP_BYTES = 64 * 1024**2
ADMISSION_MAX_AGE_SECONDS = 300.0
RESOURCE_SAMPLE_SECONDS = 0.02
TAIL_WALL_SECONDS = 60.0
TAIL_CPU_SECONDS = 60.0
TAIL_RSS_BYTES = 128 * 1024**2
THREAD_CAP = 256
VISIBLE_LINK_WALL_SECONDS = 1.0
VISIBLE_LINK_CPU_SECONDS = 1.0
VISIBLE_LINK_IO_OTHER_BYTES = 64 * 1024
TAIL_IO_OTHER_BYTES = 8 * 1024**2
CLAIM_CEILING = (
    "A_RECON_RETAINED_POLICY_ODD_VS_EVEN_SUPPORT_MEASUREMENT_ONLY_NO_ALGORITHM_EFFECT_"
    "NO_ACQUISITION_COUNT_RAW_MARL_UAV_TRANSFER_OR_DEPLOYMENT_CLAIM"
)
IMPLEMENTATION_SOURCE_LOCATORS = (
    "experiments/candidates/ucope/competence_first_scout_r01/support_audit.py",
    "scripts/run_ucope_b1_odd_support_audit_r01.py",
    "experiments/candidates/ucope/competence_first_scout_r01/contract.py",
    "experiments/candidates/ucope/competence_first_scout_r01/model.py",
    "experiments/candidates/ucope/competence_first_scout_r01/oracle.py",
    "experiments/candidates/ucope/competence_first_scout_r01/rng.py",
)

EFFECT_COUNTERS = {
    "training_updates": 0,
    "environment_episodes": 0,
    "environment_transitions": 0,
    "optimizer_constructions": 0,
    "optimizer_steps": 0,
    "checkpoint_writes": 0,
    "checkpoint_mutations": 0,
    "model_selection": 0,
    "policy_exclusions": 0,
    "hyperparameter_tuning": 0,
    "sampled_evaluations": 0,
    "acquisition_evaluations": 0,
    "count_raw_evaluations": 0,
    "count_raw_unlocks": 0,
}
CHECKPOINT_ACTIVITY_FIELDS = frozenset({
    "root_inventory", "tail_inventory", "root_optimizer_updates", "tail_optimizer_updates",
    "root_example_exposures", "tail_example_exposures", "target_refresh_events",
    "target_refresh_rows", "target_materialization_events", "target_materialization_rows",
    "root_clipping_events", "tail_clipping_events", "root_gradient_norm_sum",
    "tail_gradient_norm_sum", "root_gradient_norm_max", "tail_gradient_norm_max",
    "nonfinite_events",
})
RETAINED_EVEN_FIELDS = (
    "arm_id", "seed_id", "fold_id", "root_update",
    "all_finite", "all_unique", "root_actions", "root_selected_labels", "tail_periods",
    "root_scores", "tail_scores", "oracle_root_match", "max_regret",
    "minimum_tail_agreement", "competence_pass",
)


@dataclass(frozen=True)
class AuditBinding:
    result_sha256: str
    resource_ledger_sha256: str
    terminal_receipt_sha256: str
    checkpoint_inventory_sha256: str
    source_aggregate: str
    manifest_digest: str
    assessment_digest: str
    checkpoint_count: int = 72
    required_root: str | None = None

    def run_binding(self) -> dict[str, Any]:
        return RunBinding.b1(
            manifest_digest=self.manifest_digest,
            source_aggregate=self.source_aggregate,
            assessment_digest=self.assessment_digest,
        ).to_dict()


ACCEPTED_BINDING = AuditBinding(
    result_sha256="72deee383f2b0ff366e43ddcb43e17fe449c4f9616caf9a9e4f1ed3340bc16b6",
    resource_ledger_sha256="4406f7d8f54bbb47c5ba08b0f65d866a4d1bd673aba8aa6451c17eddeed21acb",
    terminal_receipt_sha256="798079a308d8a5fc83642f1fc34ac682cd54e26722bc78387eb6fb3419bf1d5c",
    checkpoint_inventory_sha256="77fd397ea451a1003191251ea0f0a4f1c380c52e9bd80e4734462721848e1c8f",
    source_aggregate="16ebd3bc30dc667bbc2e47037757290375f9ac7aa08309cef7e22d820644e9e6",
    manifest_digest="47405ebc4def488404b285d9fafb55e8d2b24b4342049ae08f608316684721a9",
    assessment_digest="cbae52fae338e0410935c50b9099ecab1d852b6d3ab647c5977d030b0ac74c31",
    required_root="temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete",
)


def frozen_definitions() -> dict[str, Any]:
    return {
        "odd_periods": list(ODD_PERIODS),
        "even_periods": list(EVEN_PERIODS),
        "contexts": [context_id(context) for context in CONTEXTS],
        "oracle_equations": {
            "q": "q(r,k)=0.95-(k-center(r))^2/100; center(SHORT)=2; center(LONG)=8",
            "return": "R(r,k)=q(r,k)-k/100-k^2/1000",
            "tail": "T_K(b,k)=b*R(SHORT,k)+(1-b)*R(LONG,k)",
            "probe": "probe_K=sum_m w_c,m*T_K(b_c,m,k*_K(b_c,m))+1/25-cost",
        },
        "exact_oracle_tie_rule": "HIGHER_EXACT_VALUE_THEN_LOWER_PERIOD;TIE_IS_NONUNIQUE",
        "fp32_candidate_order": {
            "root": "PROBE_THEN_IMMEDIATE_PERIODS_ASCENDING",
            "tail": "PERIODS_ASCENDING",
            "tie_competence": "TWO_HIGHEST_EQUAL_MEANS_NONUNIQUE",
        },
        "competence": {
            "all_finite": True, "all_unique": True, "root_hamming": 0,
            "max_regret": fraction_record(Fraction(1, 50)),
            "minimum_tail_agreement": fraction_record(Fraction(19, 20)),
        },
        "near": {
            "all_finite": True, "all_unique": True, "root_hamming_max": 1,
            "max_regret": fraction_record(Fraction(1, 25)),
            "minimum_tail_agreement": fraction_record(Fraction(9, 10)),
        },
        "arm_category": "BOTH_FINAL_FOLDS_PER_SEED;AT_LEAST_TWO_OF_THREE_SEEDS",
        "material_dominance": {
            "componentwise": "h_A<=h_B;r_A<=r_B;q_A>=q_B",
            "material_delta": {
                "root_hamming": 1,
                "max_regret": fraction_record(Fraction(1, 50)),
                "minimum_tail_agreement": fraction_record(Fraction(1, 20)),
            },
        },
        "paired_clear": "AT_LEAST_4_OF_6_FORWARD_AND_AT_MOST_1_OF_6_REVERSE",
        "curve_separation": "SAME_CLEAR_DIRECTION_AT_TWO_ADJACENT_ROOTS_IN_40_80_160_320",
        "mt_ft_root_separation": "ALL_6_TAIL_MAPS_EQUAL_AND_AT_LEAST_2_OF_6_ROOT_VECTORS_DIFFER_IN_AT_LEAST_2_OF_8_CONTEXTS",
        "similarity": {
            "median": "ARITHMETIC_MEAN_OF_THIRD_AND_FOURTH_FOR_SIX_VALUES",
            "root_hamming_spread_max": 1,
            "max_regret_spread_max": fraction_record(Fraction(1, 50)),
            "minimum_tail_agreement_spread_max": fraction_record(Fraction(1, 20)),
        },
        "route_order": [
            "ORACLE_NONUNIQUE_TO_MAP",
            "ODD_RECAST_SAME_ARM",
            "UNCONFLICTED_FT_PACKAGE_SEPARATION",
            "UNCONFLICTED_MT_FT_ROOT_SEPARATION",
            "ALL_SIMILAR_ODD_FAILURE_TO_PARK",
            "REMAINDER_TO_MAP",
        ],
        "resource_caps": {
            "wall_seconds": WALL_CAP_SECONDS, "peak_rss_bytes": RSS_CAP_BYTES,
            "scratch_bytes": SCRATCH_CAP_BYTES, "durable_bytes": DURABLE_CAP_BYTES,
            "processes": 1, "threads": THREAD_CAP, "workers": 1, "device": "cpu",
        },
        "publication_tail_envelope": {
            "wall_seconds": TAIL_WALL_SECONDS, "cpu_seconds": TAIL_CPU_SECONDS,
            "additional_rss_bytes": TAIL_RSS_BYTES,
            "hidden_io_other_bytes": TAIL_IO_OTHER_BYTES,
            "visible_link_wall_seconds": VISIBLE_LINK_WALL_SECONDS,
            "visible_link_cpu_seconds": VISIBLE_LINK_CPU_SECONDS,
            "visible_link_io_other_bytes": VISIBLE_LINK_IO_OTHER_BYTES,
        },
        "protected_zero_effects": dict(EFFECT_COUNTERS),
    }


def fraction_record(value: Fraction) -> dict[str, int | float]:
    if not isinstance(value, Fraction):
        raise TypeError("exact values must be fractions")
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def _periods(value: Sequence[int]) -> tuple[int, ...]:
    periods = tuple(value)
    if periods not in {ODD_PERIODS, EVEN_PERIODS}:
        raise ValueError("period support must be the frozen odd or even set")
    return periods


def build_restricted_oracle(periods: Sequence[int]) -> dict[str, dict[str, Any]]:
    periods = _periods(periods)
    rows: dict[str, dict[str, Any]] = {}
    for context in CONTEXTS:
        link, reliability, cost = context
        cell = context_id(context)
        baseline_period, baseline, immediate_unique = optimal_tail(periods, Fraction(1, 2))
        immediate_candidates = {
            str(period): fraction_record(expected_tail(period, Fraction(1, 2)))
            for period in periods
        }
        informed = Fraction(0)
        tail_periods: dict[str, int] = {}
        tail_rows: dict[str, Any] = {}
        tail_unique = True
        for count in range(7):
            belief = posterior_short(link, reliability, count)
            mass = joint_count_probability("SHORT", reliability, count) + joint_count_probability("LONG", reliability, count)
            period, value, unique = optimal_tail(periods, belief)
            informed += mass * value
            tail_unique &= unique
            tail_periods[str(count)] = period
            tail_rows[str(count)] = {
                "belief": fraction_record(belief),
                "mass": fraction_record(mass),
                "period": period,
                "value": fraction_record(value),
                "candidate_values": {
                    str(candidate): fraction_record(expected_tail(candidate, belief))
                    for candidate in periods
                },
                "unique": unique,
            }
        probe = informed + direct_probe(cost)
        root_unique = probe != baseline
        action = "PROBE" if probe > baseline else "IMMEDIATE"
        rows[cell] = {
            "context": {"link": link, "reliability": fraction_record(reliability), "cost": fraction_record(cost)},
            "periods": list(periods),
            "baseline_period": baseline_period,
            "baseline": fraction_record(baseline),
            "immediate_candidate_values": immediate_candidates,
            "probe": fraction_record(probe),
            "direct_probe": fraction_record(direct_probe(cost)),
            "action": action,
            "tail_periods": tail_periods,
            "tail": tail_rows,
            "immediate_unique": immediate_unique,
            "tail_unique": tail_unique,
            "root_unique": root_unique,
            "unique": bool(immediate_unique and tail_unique and root_unique),
        }
    return rows


def score_state(state: Mapping[str, Any], x, z) -> tuple[float, ...]:
    """Apply a retained state dict without constructing or mutating a module."""
    import torch
    import torch.nn.functional as functional

    if not isinstance(state, Mapping) or "beta" not in state:
        raise ValueError("scorer state lacks beta")
    allowed_bc = frozenset({"beta"})
    allowed_flex = frozenset({
        "beta", "residual.0.weight", "residual.0.bias", "residual.2.weight",
        "residual.2.bias", "residual.4.weight", "residual.4.bias",
    })
    state_fields = frozenset(state)
    if state_fields not in {allowed_bc, allowed_flex}:
        raise ValueError("scorer state field inventory mismatch")
    tensors = tuple(state.values())
    if (
        x.dtype != torch.float32 or z.dtype != torch.float32
        or any(not isinstance(item, torch.Tensor) or item.device.type != "cpu" or item.dtype != torch.float32 or not torch.isfinite(item).all().item() for item in tensors)
    ):
        raise ValueError("stateless scorer requires finite CPU FP32 tensors")
    versions = {name: tensor._version for name, tensor in state.items()}
    with torch.inference_mode():
        value = (z * state["beta"]).sum(dim=-1)
        if state_fields == allowed_flex:
            hidden = functional.relu(functional.linear(x, state["residual.0.weight"], state["residual.0.bias"]))
            hidden = functional.relu(functional.linear(hidden, state["residual.2.weight"], state["residual.2.bias"]))
            value = value + functional.linear(hidden, state["residual.4.weight"], state["residual.4.bias"]).squeeze(-1)
    if not torch.isfinite(value).all().item() or versions != {name: tensor._version for name, tensor in state.items()}:
        raise ValueError("stateless scorer was nonfinite or mutated input")
    return tuple(float(item) for item in value.tolist())


def _feature_pair(context, *, stage: str, action_probe: bool, period: int, belief: Fraction):
    import torch

    link, reliability, cost = context
    x = x_features(
        phase_tail=stage == "tail",
        action_probe=action_probe,
        period=period,
        belief=float(belief),
        cost=float(cost),
        linked=link == "LINKED",
        reliability=float(reliability),
    )
    z = (
        tail_basis(belief=float(belief), period=period)
        if stage == "tail"
        else root_basis(
            action_probe=action_probe, period=period, cost=float(cost),
            linked=link == "LINKED", reliability=float(reliability),
        )
    )
    return torch.tensor(x, dtype=torch.float32), torch.tensor(z, dtype=torch.float32)


def _rank(labels: Sequence[Any], values: Sequence[float]) -> tuple[Any, bool, bool]:
    if len(labels) != len(values) or not labels:
        raise ValueError("candidate score inventory mismatch")
    finite = all(math.isfinite(value) for value in values)
    ranked = sorted((value, -index, label) for index, (label, value) in enumerate(zip(labels, values)))
    unique = bool(finite and (len(ranked) == 1 or ranked[-1][0] != ranked[-2][0]))
    return ranked[-1][2], unique, finite


def score_policy_states(
    root_state: Mapping[str, Any],
    tail_state: Mapping[str, Any],
    periods: Sequence[int],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    periods = _periods(periods)
    identity_fields = {"arm_id", "seed_id", "fold_id", "root_update"}
    if not isinstance(identity, Mapping) or set(identity) != identity_fields:
        raise ValueError("policy identity field mismatch")
    oracle = build_restricted_oracle(periods)
    root_scores: dict[str, dict[str, float]] = {}
    root_labels: dict[str, str] = {}
    root_actions: dict[str, str] = {}
    tail_scores: dict[str, dict[str, dict[str, float]]] = {}
    tail_periods: dict[str, dict[str, int]] = {}
    all_unique = True
    all_finite = True
    learned_values: dict[str, Fraction] = {}
    agreements: list[Fraction] = []
    root_hamming = 0
    for context in CONTEXTS:
        link, reliability, cost = context
        cell = context_id(context)
        root_candidate_labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in periods))
        root_pairs = [_feature_pair(context, stage="root", action_probe=True, period=0, belief=Fraction(1, 2))]
        root_pairs.extend(
            _feature_pair(context, stage="root", action_probe=False, period=period, belief=Fraction(1, 2))
            for period in periods
        )
        root_values = score_state(
            root_state,
            __import__("torch").stack([pair[0] for pair in root_pairs]),
            __import__("torch").stack([pair[1] for pair in root_pairs]),
        )
        selected_root, unique, finite = _rank(root_candidate_labels, root_values)
        all_unique &= unique
        all_finite &= finite
        root_scores[cell] = dict(zip(root_candidate_labels, root_values))
        root_labels[cell] = selected_root
        root_action = "PROBE" if selected_root == "PROBE" else "IMMEDIATE"
        root_actions[cell] = root_action
        root_hamming += int(root_action != oracle[cell]["action"])

        tail_scores[cell] = {}
        tail_periods[cell] = {}
        learned_tail = Fraction(0)
        agreement = Fraction(0)
        for count in range(7):
            belief = posterior_short(link, reliability, count)
            mass = joint_count_probability("SHORT", reliability, count) + joint_count_probability("LONG", reliability, count)
            pairs = [
                _feature_pair(context, stage="tail", action_probe=False, period=period, belief=belief)
                for period in periods
            ]
            values = score_state(
                tail_state,
                __import__("torch").stack([pair[0] for pair in pairs]),
                __import__("torch").stack([pair[1] for pair in pairs]),
            )
            selected_period, tail_unique, tail_finite = _rank(periods, values)
            all_unique &= tail_unique
            all_finite &= tail_finite
            tail_scores[cell][str(count)] = {str(period): value for period, value in zip(periods, values)}
            tail_periods[cell][str(count)] = int(selected_period)
            learned_tail += mass * expected_tail(int(selected_period), belief)
            agreement += mass * int(int(selected_period) == oracle[cell]["tail_periods"][str(count)])
        agreements.append(agreement)
        if selected_root == "PROBE":
            learned_values[cell] = learned_tail + direct_probe(cost)
        else:
            learned_values[cell] = expected_tail(int(selected_root.split(":", 1)[1]), Fraction(1, 2))
    regrets = []
    for cell in oracle:
        optimum = max(
            Fraction(oracle[cell]["baseline"]["numerator"], oracle[cell]["baseline"]["denominator"]),
            Fraction(oracle[cell]["probe"]["numerator"], oracle[cell]["probe"]["denominator"]),
        )
        regret = optimum - learned_values[cell]
        if regret < 0:
            raise ValueError("negative exact regret is invalid")
        regrets.append(regret)
    max_regret = max(regrets)
    minimum_agreement = min(agreements)
    root_match = root_hamming == 0
    competent = bool(
        all_finite and all_unique and root_match
        and max_regret <= Fraction(1, 50)
        and minimum_agreement >= Fraction(19, 20)
    )
    near = bool(
        all_finite and all_unique and root_hamming <= 1
        and max_regret <= Fraction(1, 25)
        and minimum_agreement >= Fraction(9, 10)
    )
    return {
        "identity": dict(identity),
        "periods": list(periods),
        "root_scores": root_scores,
        "root_selected_labels": root_labels,
        "root_actions": root_actions,
        "tail_scores": tail_scores,
        "tail_periods": tail_periods,
        "all_finite": bool(all_finite),
        "all_unique": bool(all_unique),
        "root_hamming": root_hamming,
        "oracle_root_match": root_match,
        "max_regret": fraction_record(max_regret),
        "minimum_tail_agreement": fraction_record(minimum_agreement),
        "odd_competent_policy": competent if periods == ODD_PERIODS else None,
        "odd_near_policy": near if periods == ODD_PERIODS else None,
    }


def _exact_fraction_record(value: Mapping[str, Any], name: str) -> Fraction:
    if not isinstance(value, Mapping) or set(value) != {"numerator", "denominator", "decimal"}:
        raise ValueError(f"{name} exact fraction record mismatch")
    if type(value["numerator"]) is not int or type(value["denominator"]) is not int or value["denominator"] <= 0:
        raise ValueError(f"{name} exact fraction integers mismatch")
    exact = Fraction(value["numerator"], value["denominator"])
    if value["decimal"] != float(exact):
        raise ValueError(f"{name} decimal display mismatch")
    return exact


def validate_direct_scored_row(row: Mapping[str, Any], periods: Sequence[int]) -> dict[str, Any]:
    periods = _periods(periods)
    required = {
        "identity", "periods", "root_scores", "root_selected_labels", "root_actions",
        "tail_scores", "tail_periods", "all_finite", "all_unique", "root_hamming",
        "oracle_root_match", "max_regret", "minimum_tail_agreement",
        "odd_competent_policy", "odd_near_policy", "checkpoint",
    }
    if not isinstance(row, Mapping) or set(row) != required or row["periods"] != list(periods):
        raise ValueError("direct scored row field/period inventory mismatch")
    identity = row["identity"]
    if not isinstance(identity, Mapping) or set(identity) != {"arm_id", "seed_id", "fold_id", "root_update"}:
        raise ValueError("direct scored row identity mismatch")
    context_ids = {context_id(context) for context in CONTEXTS}
    for name in (
        "root_scores", "tail_scores", "root_selected_labels", "root_actions", "tail_periods",
    ):
        value = row[name]
        if not isinstance(value, Mapping) or set(value) != context_ids:
            raise ValueError(f"direct {name} context inventory mismatch")
    oracle = build_restricted_oracle(periods)
    selected_roots: dict[str, str] = {}
    root_actions: dict[str, str] = {}
    selected_tails: dict[str, dict[str, int]] = {}
    learned_values: dict[str, Fraction] = {}
    agreements: list[Fraction] = []
    all_unique = True
    all_finite = True
    root_hamming = 0
    for context in CONTEXTS:
        _link, _reliability, cost = context
        cell = context_id(context)
        root_labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in periods))
        scores = row["root_scores"].get(cell) if isinstance(row["root_scores"], Mapping) else None
        if not isinstance(scores, Mapping) or set(scores) != set(root_labels):
            raise ValueError("direct root score candidate inventory mismatch")
        root_values = tuple(scores[label] for label in root_labels)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in root_values):
            raise ValueError("direct root score type mismatch")
        selected, unique, finite = _rank(root_labels, root_values)
        selected_roots[cell] = selected
        root_action = "PROBE" if selected == "PROBE" else "IMMEDIATE"
        root_actions[cell] = root_action
        root_hamming += int(root_action != oracle[cell]["action"])
        all_unique &= unique
        all_finite &= finite
        learned_tail = Fraction(0)
        agreement = Fraction(0)
        selected_tails[cell] = {}
        cell_tail_scores = row["tail_scores"].get(cell) if isinstance(row["tail_scores"], Mapping) else None
        if not isinstance(cell_tail_scores, Mapping) or set(cell_tail_scores) != {str(count) for count in range(7)}:
            raise ValueError("direct tail score count inventory mismatch")
        for count in range(7):
            count_scores = cell_tail_scores[str(count)]
            labels = tuple(str(period) for period in periods)
            if not isinstance(count_scores, Mapping) or set(count_scores) != set(labels):
                raise ValueError("direct tail score candidate inventory mismatch")
            values = tuple(count_scores[label] for label in labels)
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
                raise ValueError("direct tail score type mismatch")
            selected_label, unique, finite = _rank(labels, values)
            selected_period = int(selected_label)
            selected_tails[cell][str(count)] = selected_period
            tail_oracle = oracle[cell]["tail"][str(count)]
            belief = _exact_fraction_record(tail_oracle["belief"], "oracle belief")
            mass = _exact_fraction_record(tail_oracle["mass"], "oracle mass")
            learned_tail += mass * expected_tail(selected_period, belief)
            agreement += mass * int(selected_period == tail_oracle["period"])
            all_unique &= unique
            all_finite &= finite
        agreements.append(agreement)
        learned_values[cell] = (
            learned_tail + direct_probe(cost)
            if selected == "PROBE"
            else expected_tail(int(selected.split(":", 1)[1]), Fraction(1, 2))
        )
    regrets = []
    for cell, oracle_row in oracle.items():
        optimum = max(
            _exact_fraction_record(oracle_row["baseline"], "oracle baseline"),
            _exact_fraction_record(oracle_row["probe"], "oracle probe"),
        )
        regret = optimum - learned_values[cell]
        if regret < 0:
            raise ValueError("direct row implies negative exact regret")
        regrets.append(regret)
    derived = {
        "root_selected_labels": selected_roots,
        "root_actions": root_actions,
        "tail_periods": selected_tails,
        "all_finite": bool(all_finite),
        "all_unique": bool(all_unique),
        "root_hamming": root_hamming,
        "oracle_root_match": root_hamming == 0,
        "max_regret": fraction_record(max(regrets)),
        "minimum_tail_agreement": fraction_record(min(agreements)),
    }
    if any(row[name] != value for name, value in derived.items()):
        raise ValueError("direct score maps and derived competence fields mismatch")
    competent = policy_competence({**row, **derived})
    near = policy_near_competence({**row, **derived})
    expected_competent = competent if periods == ODD_PERIODS else None
    expected_near = near if periods == ODD_PERIODS else None
    if row["odd_competent_policy"] is not expected_competent or row["odd_near_policy"] is not expected_near:
        raise ValueError("direct scored row competence category mismatch")
    return {**derived, "odd_competent_policy": expected_competent, "odd_near_policy": expected_near}


def validate_even_match(recomputed: Mapping[str, Any], retained: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(retained, Mapping) or set(retained) != set(RETAINED_EVEN_FIELDS):
        raise ValueError("retained even field inventory mismatch")
    identity = recomputed["identity"]
    fields = (
        "all_finite", "all_unique", "root_actions", "root_selected_labels", "tail_periods",
        "root_scores", "tail_scores", "oracle_root_match",
    )
    mismatch = []
    for name, item in identity.items():
        if retained.get(name) != item:
            mismatch.append(name)
    for name in fields:
        if retained.get(name) != recomputed.get(name):
            mismatch.append(name)
    if retained.get("max_regret") != recomputed["max_regret"]["decimal"]:
        mismatch.append("max_regret")
    if retained.get("minimum_tail_agreement") != recomputed["minimum_tail_agreement"]["decimal"]:
        mismatch.append("minimum_tail_agreement")
    competence_pass = policy_competence(recomputed)
    if retained.get("competence_pass") is not competence_pass:
        mismatch.append("competence_pass")
    if mismatch:
        raise ValueError(f"even rescore mismatch: {sorted(set(mismatch))}")
    return {
        "identity": dict(identity), "match": True, "recomputed_competence_pass": competence_pass,
        "checked_fields": [*fields, "max_regret", "minimum_tail_agreement", "competence_pass"],
    }


def _sanitize_retained_even(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not set(RETAINED_EVEN_FIELDS).issubset(value):
        raise ValueError("retained even source field inventory mismatch")
    return {name: value[name] for name in RETAINED_EVEN_FIELDS}


def policy_competence(row: Mapping[str, Any]) -> bool:
    regret = row.get("max_regret")
    agreement = row.get("minimum_tail_agreement")
    if not isinstance(regret, Mapping) or not isinstance(agreement, Mapping):
        raise ValueError("policy competence requires exact regret/agreement records")
    exact_regret = Fraction(int(regret["numerator"]), int(regret["denominator"]))
    exact_agreement = Fraction(int(agreement["numerator"]), int(agreement["denominator"]))
    return bool(
        row.get("all_finite") is True
        and row.get("all_unique") is True
        and row.get("oracle_root_match") is True
        and exact_regret <= Fraction(1, 50)
        and exact_agreement >= Fraction(19, 20)
    )


def policy_near_competence(row: Mapping[str, Any]) -> bool:
    regret = row.get("max_regret")
    agreement = row.get("minimum_tail_agreement")
    if not isinstance(regret, Mapping) or not isinstance(agreement, Mapping):
        raise ValueError("policy near-competence requires exact regret/agreement records")
    return bool(
        row.get("all_finite") is True
        and row.get("all_unique") is True
        and int(row.get("root_hamming", 9)) <= 1
        and Fraction(int(regret["numerator"]), int(regret["denominator"])) <= Fraction(1, 25)
        and Fraction(int(agreement["numerator"]), int(agreement["denominator"])) >= Fraction(9, 10)
    )


def materially_dominates(
    first: tuple[int, Fraction, Fraction], second: tuple[int, Fraction, Fraction],
) -> bool:
    h_first, regret_first, agreement_first = first
    h_second, regret_second, agreement_second = second
    ordered = h_first <= h_second and regret_first <= regret_second and agreement_first >= agreement_second
    material = (
        h_second - h_first >= 1
        or regret_second - regret_first >= Fraction(1, 50)
        or agreement_first - agreement_second >= Fraction(1, 20)
    )
    return bool(ordered and material)


def median_fraction(values: Sequence[Fraction]) -> Fraction:
    ordered = sorted(Fraction(value) for value in values)
    if not ordered:
        raise ValueError("median requires values")
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def choose_route(predicates: Mapping[str, bool]) -> dict[str, Any]:
    required = {
        "oracle_unique", "odd_recast", "ft_flex_over_bc", "ft_bc_over_flex",
        "mt_ft_root_separation", "all_similar_odd_failure",
    }
    if not isinstance(predicates, Mapping) or set(predicates) != required or any(type(value) is not bool for value in predicates.values()):
        raise ValueError("routing predicate inventory mismatch")
    conflict = bool(
        predicates["ft_flex_over_bc"] and predicates["ft_bc_over_flex"]
        or predicates["mt_ft_root_separation"] and (predicates["ft_flex_over_bc"] or predicates["ft_bc_over_flex"])
    )
    if not predicates["oracle_unique"]:
        route = "MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED"
    elif predicates["odd_recast"]:
        route = "RECAST_ODD_TO_EVEN_GENERALIZATION"
    elif conflict:
        route = "MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED"
    elif (predicates["ft_flex_over_bc"] ^ predicates["ft_bc_over_flex"]) and not predicates["mt_ft_root_separation"]:
        route = "PERMIT_PAIRED_B_OPTIMIZATION_CONDITIONING_DISCRIMINATOR"
    elif predicates["mt_ft_root_separation"] and not (predicates["ft_flex_over_bc"] or predicates["ft_bc_over_flex"]):
        route = "LATER_TARGET_SCHEDULE_B_COMPARISON_JUSTIFIED"
    elif predicates["all_similar_odd_failure"]:
        route = "PARK_DIRECTION_PER_EXISTING_PRO_MAP"
    else:
        route = "MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED"
    return {"predicates": dict(predicates), "conflict": conflict, "route": route}


def same_arm_odd_recast(
    arm_categories: Sequence[Mapping[str, Any]],
    even_arm_competence: Mapping[str, bool],
) -> bool:
    categories = {row.get("arm_id"): row for row in arm_categories if isinstance(row, Mapping)}
    if set(categories) != set(ARMS) or set(even_arm_competence) != set(ARMS):
        raise ValueError("odd/even arm category inventory mismatch")
    if any(type(even_arm_competence[arm]) is not bool for arm in ARMS):
        raise ValueError("retained even arm competence must be boolean")
    return any(
        (categories[arm].get("competent") is True or categories[arm].get("near") is True)
        and not even_arm_competence[arm]
        for arm in ARMS
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


ADMISSION_RECEIPT_FIELDS = {
    "schema_version", "captured_at", "assessed_at", "measurement_source",
    "minimum_available_bytes", "available_physical_bytes", "cgroup_memory_max_bytes",
    "cgroup_memory_current_bytes", "cgroup_headroom_bytes", "effective_available_bytes",
    "physical_floor_pass", "effective_floor_pass", "passed", "failure_reasons",
}


def _admission_interval(value: Mapping[str, Any]) -> tuple[datetime, datetime]:
    try:
        captured = datetime.fromisoformat(str(value["captured_at"]).replace("Z", "+00:00"))
        assessed = datetime.fromisoformat(str(value["assessed_at"]).replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ValueError("admission captured/assessed timestamps are not ISO-8601") from error
    if captured.tzinfo is None or assessed.tzinfo is None:
        raise ValueError("admission captured/assessed timestamps must be timezone-aware")
    gap = (assessed - captured).total_seconds()
    if gap < 0 or gap > 10.0:
        raise ValueError("central admission capture/assessment interval is invalid")
    return captured, assessed


def _validate_central_admission_payload(value: Mapping[str, Any], encoded: bytes) -> None:
    if not isinstance(value, Mapping) or set(value) != ADMISSION_RECEIPT_FIELDS:
        raise ValueError("central admit-memory receipt schema mismatch")
    expected_bytes = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if encoded != expected_bytes:
        raise ValueError("admission receipt is not the canonical central preflight serialization")
    _admission_interval(value)
    exact_ints = ("minimum_available_bytes", "available_physical_bytes", "effective_available_bytes")
    if (
        value["schema_version"] != 1
        or value["measurement_source"] not in {"GlobalMemoryStatusEx", "/proc/meminfo"}
        or value["failure_reasons"] != []
        or value["passed"] is not True
        or value["physical_floor_pass"] is not True
        or value["effective_floor_pass"] is not True
        or any(type(value[name]) is not int or value[name] < 0 for name in exact_ints)
        or value["minimum_available_bytes"] != MINIMUM_MEMORY_BYTES
        or value["available_physical_bytes"] < MINIMUM_MEMORY_BYTES
        or value["effective_available_bytes"] < MINIMUM_MEMORY_BYTES
        or not value["captured_at"] or not value["assessed_at"]
    ):
        raise ValueError("fresh admission does not establish both 4 GiB floors")
    cgroup_fields = (
        value["cgroup_memory_max_bytes"], value["cgroup_memory_current_bytes"],
        value["cgroup_headroom_bytes"],
    )
    if value["measurement_source"] == "GlobalMemoryStatusEx":
        if cgroup_fields != (None, None, None) or value["effective_available_bytes"] != value["available_physical_bytes"]:
            raise ValueError("Windows central admission cgroup/effective fields are inconsistent")
    elif value["cgroup_memory_max_bytes"] is None:
        if cgroup_fields != (None, None, None) or value["effective_available_bytes"] != value["available_physical_bytes"]:
            raise ValueError("unbounded central admission cgroup/effective fields are inconsistent")
    else:
        if any(type(item) is not int or item < 0 for item in cgroup_fields):
            raise ValueError("bounded central admission cgroup fields are invalid")
        expected_headroom = max(0, value["cgroup_memory_max_bytes"] - value["cgroup_memory_current_bytes"])
        if value["cgroup_headroom_bytes"] != expected_headroom or value["effective_available_bytes"] != min(value["available_physical_bytes"], expected_headroom):
            raise ValueError("bounded central admission headroom is inconsistent")


def _admission_provenance() -> dict[str, Any]:
    project = Path(__file__).resolve().parents[4]
    producer_bytes = _read_plain_file_once(project / "scripts/hmasd_resource_preflight.py", project)
    return {
        "producer": "scripts/hmasd_resource_preflight.py:admit-memory",
        "producer_sha256": hashlib.sha256(producer_bytes).hexdigest(),
        "producer_size_bytes": len(producer_bytes),
        "canonical_central_serialization": True,
    }


def validate_admission(path: str | Path) -> dict[str, Any]:
    receipt_path = Path(path)
    encoded = _read_plain_file_once(receipt_path, receipt_path.parent)
    value = json.loads(encoded.decode("utf-8"))
    _validate_central_admission_payload(value, encoded)
    return {
        **value,
        "receipt_sha256": hashlib.sha256(encoded).hexdigest(),
        "provenance": _admission_provenance(),
    }


def validate_fresh_admission(
    path: str | Path, *, now: datetime | None = None,
) -> dict[str, Any]:
    value = validate_admission(path)
    _captured, timestamp = _admission_interval(value)
    current = now or datetime.now(timezone.utc)
    age = (current.astimezone(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds()
    if age < -5.0 or age > ADMISSION_MAX_AGE_SECONDS:
        raise ValueError("central 4 GiB admission is not fresh for this invocation")
    mtime_age = current.timestamp() - Path(path).stat().st_mtime
    if mtime_age < -5.0 or mtime_age > ADMISSION_MAX_AGE_SECONDS:
        raise ValueError("central admission receipt file is not fresh for this invocation")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _directory_size(root: Path) -> int:
    if not root.exists():
        return 0
    if root.is_symlink() or not root.is_dir():
        raise ValueError("resource root must be a plain directory")
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("resource root contains a symlink")
        if path.is_file():
            total += path.stat().st_size
    return total


def _enumerate_plain_tree(root: Path) -> tuple[set[str], set[str]]:
    root_absolute = root.absolute()
    root_status = os.lstat(root_absolute)
    if _is_reparse_or_symlink(root_absolute, root_status) or not stat.S_ISDIR(root_status.st_mode):
        raise ValueError("tree root is reparse/symlinked or non-directory")
    files: set[str] = set()
    directories: set[str] = set()
    pending = [(root_absolute, (root_status.st_dev, root_status.st_ino))]
    while pending:
        directory, expected_identity = pending.pop()
        current = os.lstat(directory)
        if _is_reparse_or_symlink(directory, current) or not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != expected_identity:
            raise ValueError("tree directory identity changed during enumeration")
        with os.scandir(directory) as entries:
            for entry in entries:
                status = entry.stat(follow_symlinks=False)
                path = Path(entry.path)
                if _is_reparse_or_symlink(path, status):
                    raise ValueError("complete tree contains a reparse point or symlink")
                relative = path.relative_to(root_absolute).as_posix()
                if stat.S_ISDIR(status.st_mode):
                    directory_status = os.lstat(path)
                    if _is_reparse_or_symlink(path, directory_status) or not stat.S_ISDIR(directory_status.st_mode):
                        raise ValueError("complete tree directory became reparse/symlinked")
                    directories.add(relative)
                    pending.append((path, (directory_status.st_dev, directory_status.st_ino)))
                elif stat.S_ISREG(status.st_mode):
                    files.add(relative)
                else:
                    raise ValueError("complete tree contains a non-file/non-directory entry")
    return files, directories


@dataclass(frozen=True)
class _ProcessSample:
    identity: tuple[int, int]
    rss_bytes: int
    cpu_seconds: float
    io_read_bytes: int
    io_write_bytes: int
    io_other_bytes: int
    threads: int


def _filetime_value(value: Any) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


def _windows_process_tree() -> tuple[_ProcessSample, ...]:
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("page_fault_count", wintypes.DWORD),
            ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_nonpaged_pool_usage", ctypes.c_size_t),
            ("quota_nonpaged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("read_operations", ctypes.c_ulonglong), ("write_operations", ctypes.c_ulonglong),
            ("other_operations", ctypes.c_ulonglong), ("read_bytes", ctypes.c_ulonglong),
            ("write_bytes", ctypes.c_ulonglong), ("other_bytes", ctypes.c_ulonglong),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
    ]
    kernel32.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(IoCounters)]
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
    ]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ValueError("CreateToolhelp32Snapshot failed")
    entries: list[tuple[int, int, int]] = []
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while present:
            entries.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID), int(entry.cntThreads)))
            entry.dwSize = ctypes.sizeof(ProcessEntry)
            present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    root_pid = os.getpid()
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent, _threads in entries:
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    thread_by_pid = {pid: threads for pid, _parent, threads in entries}
    rows: list[_ProcessSample] = []
    for pid in sorted(descendants):
        handle = kernel32.GetCurrentProcess() if pid == root_pid else kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not handle:
            continue
        try:
            memory = ProcessMemoryCounters(); memory.cb = ctypes.sizeof(memory)
            io_counters = IoCounters()
            creation = wintypes.FILETIME(); exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME(); user = wintypes.FILETIME()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise ValueError(f"GetProcessMemoryInfo failed for pid {pid}")
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io_counters)):
                raise ValueError(f"GetProcessIoCounters failed for pid {pid}")
            if not kernel32.GetProcessTimes(
                handle, ctypes.byref(creation), ctypes.byref(exit_time),
                ctypes.byref(kernel), ctypes.byref(user),
            ):
                raise ValueError(f"GetProcessTimes failed for pid {pid}")
            rows.append(_ProcessSample(
                (pid, _filetime_value(creation)), int(memory.working_set_size),
                (_filetime_value(kernel) + _filetime_value(user)) / 10_000_000.0,
                int(io_counters.read_bytes), int(io_counters.write_bytes),
                int(io_counters.other_bytes), int(thread_by_pid.get(pid, 0)),
            ))
        finally:
            if pid != root_pid:
                kernel32.CloseHandle(handle)
    if not any(row.identity[0] == root_pid for row in rows):
        raise ValueError("current process absent from process-tree observation")
    return tuple(rows)


def _portable_process_tree() -> tuple[_ProcessSample, ...]:
    import resource
    import sys

    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss) * (1 if sys.platform == "darwin" else 1024)
    return (_ProcessSample(
        (os.getpid(), 0), rss, float(usage.ru_utime + usage.ru_stime),
        int(usage.ru_inblock) * 512, int(usage.ru_oublock) * 512, 0,
        threading.active_count(),
    ),)


def _process_tree_samples() -> tuple[_ProcessSample, ...]:
    return _windows_process_tree() if os.name == "nt" else _portable_process_tree()


class AuditResourceMonitor:
    """Direct current-process and scratch high-water observation for the one-worker audit."""

    def __init__(
        self,
        scratch_root: Path,
        durable_root: Path | None = None,
        *,
        sample_seconds: float = RESOURCE_SAMPLE_SECONDS,
    ):
        self.scratch_root = scratch_root
        self.durable_root = scratch_root if durable_root is None else durable_root
        self.sample_seconds = sample_seconds
        self.started_wall = time.perf_counter()
        self.peak_rss_bytes = 0
        self.peak_process_count = 0
        self.peak_thread_count = 0
        self.scratch_peak_bytes = 0
        self.durable_peak_bytes = 0
        self.sample_count = 0
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._finished: dict[str, Any] | None = None
        self._first: dict[tuple[int, int], _ProcessSample] = {}
        self._last: dict[tuple[int, int], _ProcessSample] = {}

    def _observe_locked(self) -> None:
        rows = _process_tree_samples()
        self.peak_rss_bytes = max(self.peak_rss_bytes, sum(row.rss_bytes for row in rows))
        self.peak_process_count = max(self.peak_process_count, len(rows))
        self.peak_thread_count = max(self.peak_thread_count, sum(row.threads for row in rows))
        self.scratch_peak_bytes = max(self.scratch_peak_bytes, _directory_size(self.scratch_root))
        self.durable_peak_bytes = max(self.durable_peak_bytes, _directory_size(self.durable_root))
        self.sample_count += 1
        for row in rows:
            self._first.setdefault(row.identity, row)
            self._last[row.identity] = row

    def _counters_locked(self) -> tuple[float, int, int, int]:
        cpu = 0.0
        read_bytes = write_bytes = other_bytes = 0
        for identity, last in self._last.items():
            first = self._first[identity]
            cpu += max(0.0, last.cpu_seconds - first.cpu_seconds)
            read_bytes += max(0, last.io_read_bytes - first.io_read_bytes)
            write_bytes += max(0, last.io_write_bytes - first.io_write_bytes)
            other_bytes += max(0, last.io_other_bytes - first.io_other_bytes)
        return cpu, read_bytes, write_bytes, other_bytes

    def _loop(self) -> None:
        try:
            while not self._stop.wait(self.sample_seconds):
                with self._lock:
                    self._observe_locked()
        except BaseException as error:  # surfaced by finish
            with self._lock:
                self._error = error
            self._stop.set()

    def start(self) -> "AuditResourceMonitor":
        with self._lock:
            if self._thread is not None or self._finished is not None:
                raise ValueError("audit resource monitor may start only once")
            self._observe_locked()
            self._thread = threading.Thread(
                target=self._loop, name="ucope-odd-support-audit-resource-monitor", daemon=True,
            )
            self._thread.start()
        return self

    def observe_transaction_point(self) -> None:
        with self._lock:
            if self._finished is not None or self._error is not None:
                raise ValueError("audit resource monitor is inactive")
            self._observe_locked()

    def _record_locked(self, *, complete: bool) -> dict[str, Any]:
        cpu, read_bytes, write_bytes, other_bytes = self._counters_locked()
        return {
            "measurement_complete": complete,
            "measurement_scope": (
                "FULL_HIDDEN_PUBLICATION_TRANSACTION"
                if complete else "PRE_TAIL_CUMULATIVE_OBSERVATION"
            ),
            "measurement_source": (
                "WINDOWS_PROCESS_TREE_APIS"
                if os.name == "nt" else "GETRUSAGE_CURRENT_PROCESS_FALLBACK"
            ),
            "sample_interval_seconds": self.sample_seconds,
            "sample_count": self.sample_count,
            "wall_seconds": time.perf_counter() - self.started_wall,
            "cpu_seconds": cpu,
            "peak_rss_bytes": self.peak_rss_bytes,
            "peak_process_count": self.peak_process_count,
            "peak_thread_count": self.peak_thread_count,
            "scratch_peak_bytes": self.scratch_peak_bytes,
            "durable_peak_bytes": self.durable_peak_bytes,
            "io_read_bytes": read_bytes,
            "io_write_bytes": write_bytes,
            "io_other_bytes": other_bytes,
            "aggregate_io_bytes": read_bytes + write_bytes + other_bytes,
            "worker_count": 1,
            "device": "cpu",
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            if self._finished is not None or self._error is not None:
                raise ValueError("audit resource monitor is inactive")
            self._observe_locked()
            return self._record_locked(complete=False)

    def finish(self) -> dict[str, Any]:
        with self._lock:
            if self._finished is not None:
                return dict(self._finished)
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                raise ValueError("audit resource monitor did not stop")
        with self._lock:
            self._observe_locked()
            if self._error is not None:
                raise ValueError(f"audit resource observation failed: {self._error}") from self._error
            result = self._record_locked(complete=True)
            self._finished = dict(result)
            return result


def _validate_resource_observation(value: Mapping[str, Any], *, complete: bool) -> None:
    required = {
        "measurement_complete", "measurement_scope", "measurement_source",
        "sample_interval_seconds", "sample_count", "wall_seconds", "cpu_seconds",
        "peak_rss_bytes", "peak_process_count", "peak_thread_count", "scratch_peak_bytes",
        "durable_peak_bytes", "io_read_bytes", "io_write_bytes", "io_other_bytes", "aggregate_io_bytes",
        "worker_count", "device",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("audit resource observation structure mismatch")
    expected_scope = "FULL_HIDDEN_PUBLICATION_TRANSACTION" if complete else "PRE_TAIL_CUMULATIVE_OBSERVATION"
    expected_source = "WINDOWS_PROCESS_TREE_APIS" if os.name == "nt" else "GETRUSAGE_CURRENT_PROCESS_FALLBACK"
    exact_nonnegative = (
        "peak_rss_bytes", "peak_process_count", "peak_thread_count", "scratch_peak_bytes",
        "durable_peak_bytes", "io_read_bytes", "io_write_bytes", "io_other_bytes",
        "aggregate_io_bytes", "worker_count",
    )
    if (
        value["measurement_complete"] is not complete
        or value["measurement_scope"] != expected_scope
        or value["measurement_source"] != expected_source
        or not isinstance(value["sample_interval_seconds"], (int, float))
        or isinstance(value["sample_interval_seconds"], bool)
        or not math.isfinite(float(value["sample_interval_seconds"]))
        or float(value["sample_interval_seconds"]) != RESOURCE_SAMPLE_SECONDS
        or type(value["sample_count"]) is not int or value["sample_count"] <= 0
        or any(
            not isinstance(value[name], (int, float)) or isinstance(value[name], bool)
            or not math.isfinite(float(value[name])) or float(value[name]) < 0
            for name in ("wall_seconds", "cpu_seconds")
        )
        or any(type(value[name]) is not int or value[name] < 0 for name in exact_nonnegative)
        or value["device"] != "cpu"
        or value["peak_process_count"] != 1
        or value["worker_count"] != 1
        or (not complete and value["durable_peak_bytes"] != 0)
        or value["aggregate_io_bytes"] != (
            value["io_read_bytes"] + value["io_write_bytes"] + value["io_other_bytes"]
        )
    ):
        raise ValueError("audit resource topology/measurement mismatch")


def _validate_resources(
    value: Mapping[str, Any],
    *,
    durable_peak_bytes: int,
    final_output_bytes: int | None = None,
    validation_read_bytes: int = 0,
) -> dict[str, Any]:
    _validate_resource_observation(value, complete=False)
    if type(durable_peak_bytes) is not int or durable_peak_bytes <= 0:
        raise ValueError("audit durable resource bound is invalid")
    caps = {
        "wall_seconds": WALL_CAP_SECONDS,
        "peak_rss_bytes": RSS_CAP_BYTES,
        "scratch_peak_bytes": SCRATCH_CAP_BYTES,
        "durable_peak_bytes": DURABLE_CAP_BYTES,
        "peak_process_count": 1,
        "peak_thread_count": THREAD_CAP,
        "worker_count": 1,
        "device": "cpu",
    }
    output_bytes = durable_peak_bytes if final_output_bytes is None else final_output_bytes
    if type(output_bytes) is not int or output_bytes <= 0 or type(validation_read_bytes) is not int or validation_read_bytes < 0:
        raise ValueError("prospective final output byte count is invalid")
    reservation = {
        "basis": "FROZEN_HIDDEN_FINAL_TRANSACTION_ENVELOPE_PLUS_VISIBLE_HARDLINK_RESERVATION",
        "wall_seconds": TAIL_WALL_SECONDS,
        "cpu_seconds": TAIL_CPU_SECONDS,
        "rss_bytes": TAIL_RSS_BYTES,
        "io_read_bytes": output_bytes + validation_read_bytes,
        "io_write_bytes": output_bytes,
        "io_other_bytes": TAIL_IO_OTHER_BYTES + VISIBLE_LINK_IO_OTHER_BYTES,
        "aggregate_io_bytes": 2 * output_bytes + validation_read_bytes + TAIL_IO_OTHER_BYTES + VISIBLE_LINK_IO_OTHER_BYTES,
        "validation_read_bytes": validation_read_bytes,
        "scratch_bytes": 0,
        "durable_bytes": output_bytes,
        "peak_process_count": 1,
        "peak_thread_count": THREAD_CAP,
        "worker_count": 1,
        "visible_link_reservation": {
            "wall_seconds": VISIBLE_LINK_WALL_SECONDS,
            "cpu_seconds": VISIBLE_LINK_CPU_SECONDS,
            "io_other_bytes": VISIBLE_LINK_IO_OTHER_BYTES,
            "same_volume_hardlink": True,
        },
    }
    combined = {
        "wall_seconds": round(float(value["wall_seconds"]) + reservation["wall_seconds"], 9),
        "cpu_seconds": round(float(value["cpu_seconds"]) + reservation["cpu_seconds"], 9),
        "peak_rss_bytes": int(value["peak_rss_bytes"]) + reservation["rss_bytes"],
        "peak_process_count": max(int(value["peak_process_count"]), reservation["peak_process_count"]),
        "peak_thread_count": max(int(value["peak_thread_count"]), reservation["peak_thread_count"]),
        "worker_count": int(value["worker_count"]),
        "scratch_peak_bytes": int(value["scratch_peak_bytes"]),
        "durable_peak_bytes": output_bytes,
        "io_read_bytes": int(value["io_read_bytes"]) + reservation["io_read_bytes"],
        "io_write_bytes": int(value["io_write_bytes"]) + reservation["io_write_bytes"],
        "io_other_bytes": int(value["io_other_bytes"]) + reservation["io_other_bytes"],
        "aggregate_io_bytes": int(value["aggregate_io_bytes"]) + reservation["aggregate_io_bytes"],
    }
    if (
        combined["wall_seconds"] > caps["wall_seconds"]
        or combined["peak_rss_bytes"] > caps["peak_rss_bytes"]
        or int(value["scratch_peak_bytes"]) > caps["scratch_peak_bytes"]
        or output_bytes > caps["durable_peak_bytes"]
        or combined["peak_thread_count"] > caps["peak_thread_count"]
    ):
        raise ValueError("audit resource cap exceeded")
    return {
        "pre_tail_observed": dict(value),
        "prospective_tail_envelope": reservation,
        "prospective_total_bound": combined,
        "durable_peak_bytes": durable_peak_bytes,
        "caps": caps,
        "prospective_cap_pass": True,
        "cap_pass": True,
    }


def _validate_actual_transaction(
    pre_tail: Mapping[str, Any],
    completed: Mapping[str, Any],
    resources: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = resources["prospective_tail_envelope"]
    _validate_resource_observation(pre_tail, complete=False)
    _validate_resource_observation(completed, complete=True)
    actual_tail = {
        "wall_seconds": max(0.0, float(completed["wall_seconds"]) - float(pre_tail["wall_seconds"])) + VISIBLE_LINK_WALL_SECONDS,
        "cpu_seconds": max(0.0, float(completed["cpu_seconds"]) - float(pre_tail["cpu_seconds"])) + VISIBLE_LINK_CPU_SECONDS,
        "rss_bytes": max(0, int(completed["peak_rss_bytes"]) - int(pre_tail["peak_rss_bytes"])),
        "io_read_bytes": max(0, int(completed["io_read_bytes"]) - int(pre_tail["io_read_bytes"])),
        "io_write_bytes": max(0, int(completed["io_write_bytes"]) - int(pre_tail["io_write_bytes"])),
        "io_other_bytes": max(0, int(completed["io_other_bytes"]) - int(pre_tail["io_other_bytes"])) + VISIBLE_LINK_IO_OTHER_BYTES,
        "scratch_bytes": max(0, int(completed["scratch_peak_bytes"]) - int(pre_tail["scratch_peak_bytes"])),
        "durable_bytes": int(completed["durable_peak_bytes"]),
        "peak_process_count": int(completed["peak_process_count"]),
        "peak_thread_count": int(completed["peak_thread_count"]),
        "worker_count": int(completed["worker_count"]),
    }
    actual_tail["aggregate_io_bytes"] = actual_tail["io_read_bytes"] + actual_tail["io_write_bytes"] + actual_tail["io_other_bytes"]
    for name in (
        "wall_seconds", "cpu_seconds", "rss_bytes", "io_read_bytes", "io_write_bytes",
        "io_other_bytes", "aggregate_io_bytes", "scratch_bytes", "durable_bytes",
        "peak_process_count", "peak_thread_count", "worker_count",
    ):
        if actual_tail[name] > envelope[name]:
            raise ValueError(
                f"actual publication tail exceeded frozen envelope: {name} "
                f"{actual_tail[name]}>{envelope[name]}"
            )
    caps = resources["caps"]
    if (
        float(completed["wall_seconds"]) + VISIBLE_LINK_WALL_SECONDS > caps["wall_seconds"]
        or int(completed["peak_rss_bytes"]) > caps["peak_rss_bytes"]
        or int(completed["scratch_peak_bytes"]) > caps["scratch_peak_bytes"]
        or int(completed["durable_peak_bytes"]) > caps["durable_peak_bytes"]
        or int(completed["peak_process_count"]) > 1
        or int(completed["peak_thread_count"]) > caps["peak_thread_count"]
        or int(completed["worker_count"]) > 1
    ):
        raise ValueError("actual full hidden publication transaction exceeded total cap")
    return actual_tail


def _is_reparse_or_symlink(path: Path, status: os.stat_result) -> bool:
    return stat.S_ISLNK(status.st_mode) or bool(getattr(status, "st_file_attributes", 0) & 0x400)


def _read_plain_file_once(path: Path, root: Path) -> bytes:
    root_absolute = root.absolute()
    path_absolute = path.absolute()
    try:
        root_status = os.lstat(root_absolute)
    except FileNotFoundError as error:
        raise ValueError(f"missing input root: {root}") from error
    if _is_reparse_or_symlink(root_absolute, root_status) or not stat.S_ISDIR(root_status.st_mode):
        raise ValueError(f"reparse/symlinked input root: {root}")
    try:
        relative = path_absolute.relative_to(root_absolute)
    except ValueError as error:
        raise ValueError(f"out-of-tree input: {path}") from error
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"out-of-tree input: {path}")
    cursor = root_absolute
    for part in relative.parts[:-1]:
        cursor = cursor / part
        try:
            status = os.lstat(cursor)
        except FileNotFoundError as error:
            raise ValueError(f"missing input directory: {cursor}") from error
        if _is_reparse_or_symlink(cursor, status) or not stat.S_ISDIR(status.st_mode):
            raise ValueError(f"reparse/symlinked input directory: {cursor}")
    try:
        before = os.lstat(path_absolute)
    except FileNotFoundError as error:
        raise ValueError(f"missing input file: {path}") from error
    if _is_reparse_or_symlink(path_absolute, before) or not stat.S_ISREG(before.st_mode):
        raise ValueError(f"reparse/symlinked or non-file input: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path_absolute, flags)
    try:
        opened = os.fstat(descriptor)
        before_identity = (before.st_dev, before.st_ino, before.st_size)
        opened_identity = (opened.st_dev, opened.st_ino, opened.st_size)
        if before_identity != opened_identity or not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"input file identity changed before open: {path}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after_handle = os.fstat(descriptor)
        if (after_handle.st_dev, after_handle.st_ino, after_handle.st_size) != opened_identity:
            raise ValueError(f"input file identity changed during read: {path}")
    finally:
        os.close(descriptor)
    after_path = os.lstat(path_absolute)
    if _is_reparse_or_symlink(path_absolute, after_path) or (
        after_path.st_dev, after_path.st_ino, after_path.st_size
    ) != before_identity:
        raise ValueError(f"input file path changed after read: {path}")
    encoded = b"".join(chunks)
    if len(encoded) != before.st_size:
        raise ValueError(f"input file byte count changed during read: {path}")
    return encoded


def _identity(record: Mapping[str, Any]) -> tuple[str, str, int, int]:
    return (record["arm_id"], record["seed_id"], record["fold_id"], record["root_update"])


def _identity_dict(identity: tuple[str, str, int, int]) -> dict[str, Any]:
    return dict(zip(("arm_id", "seed_id", "fold_id", "root_update"), identity))


def snapshot_implementation_sources() -> dict[str, Any]:
    project = Path(__file__).resolve().parents[4]
    records = []
    for locator in IMPLEMENTATION_SOURCE_LOCATORS:
        path = project / locator
        encoded = _read_plain_file_once(path, project)
        records.append({
            "locator": locator,
            "size_bytes": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        })
    return {
        "files": records,
        "aggregate_sha256": hashlib.sha256(_canonical_bytes(records)).hexdigest(),
    }


def validate_implementation_source_snapshots(
    before: Mapping[str, Any], after: Mapping[str, Any],
) -> dict[str, Any]:
    if before != after:
        raise ValueError("implementation source changed during audit")
    if not isinstance(before, Mapping) or set(before) != {"files", "aggregate_sha256"}:
        raise ValueError("implementation source snapshot structure mismatch")
    files = before["files"]
    if not isinstance(files, list) or len(files) != 6:
        raise ValueError("implementation source inventory mismatch")
    expected_locators = list(IMPLEMENTATION_SOURCE_LOCATORS)
    if [record.get("locator") for record in files if isinstance(record, Mapping)] != expected_locators:
        raise ValueError("implementation source locator inventory mismatch")
    if any(
        not isinstance(record, Mapping) or set(record) != {"locator", "size_bytes", "sha256"}
        or type(record["size_bytes"]) is not int or record["size_bytes"] <= 0
        or type(record["sha256"]) is not str or len(record["sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in record["sha256"])
        for record in files
    ):
        raise ValueError("implementation source size/SHA format mismatch")
    if hashlib.sha256(_canonical_bytes(files)).hexdigest() != before["aggregate_sha256"]:
        raise ValueError("implementation source aggregate mismatch")
    if before != snapshot_implementation_sources():
        raise ValueError("implementation source snapshot does not match current actual bytes")
    return dict(before)


def _expected_identities(config: ScoutConfig) -> set[tuple[str, str, int, int]]:
    return {
        (arm, seed, fold, update)
        for arm in config.arms
        for seed in config.seed_ids
        for fold in (0, 1)
        for update in config.evaluation_root_updates
    }


def snapshot_input_tree(root: str | Path, binding: AuditBinding = ACCEPTED_BINDING) -> dict[str, Any]:
    """Validate and snapshot the immutable B1 complete tree without loading tensors."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("complete root must be a plain directory")
    if binding.required_root is not None:
        expected = (Path(__file__).resolve().parents[4] / binding.required_root).resolve()
        if root.resolve() != expected:
            raise ValueError("complete root is not the frozen accepted B1-04 root")
    top_names = ("result.json", "resource-ledger.json", "terminal-receipt.json")
    expected_top = {
        "result.json": binding.result_sha256,
        "resource-ledger.json": binding.resource_ledger_sha256,
        "terminal-receipt.json": binding.terminal_receipt_sha256,
    }
    documents: dict[str, Any] = {}
    top_hashes: dict[str, str] = {}
    top_files: list[dict[str, Any]] = []
    for name in top_names:
        path = root / name
        encoded = _read_plain_file_once(path, root)
        digest = hashlib.sha256(encoded).hexdigest()
        if digest != expected_top[name]:
            raise ValueError(f"{name} SHA-256 mismatch")
        top_hashes[name] = digest
        top_files.append({"locator": name, "size_bytes": len(encoded), "sha256": digest})
        documents[name] = json.loads(encoded.decode("utf-8"))
    result = documents["result.json"]
    if not isinstance(result, Mapping) or result.get("complete") is not True:
        raise ValueError("complete result is absent")
    config = ScoutConfig.from_dict(result.get("config", {}))
    if config != ScoutConfig.b1() or result.get("object_id") != B1_OBJECT_ID:
        raise ValueError("B1 config/object binding mismatch")
    run_binding = binding.run_binding()
    for name, document in documents.items():
        if not isinstance(document, Mapping) or document.get("config") != config.to_dict() or document.get("run_binding") != run_binding:
            raise ValueError(f"{name} config/run binding mismatch")
    records = result.get("checkpoints")
    if not isinstance(records, list) or len(records) != binding.checkpoint_count:
        raise ValueError("checkpoint inventory must contain exactly 72 records")
    expected = _expected_identities(config)
    seen: set[tuple[str, str, int, int]] = set()
    locators: set[str] = set()
    normalized: list[dict[str, Any]] = []
    record_fields = {"format", "arm_id", "seed_id", "fold_id", "root_update", "locator", "size_bytes", "sha256"}
    for raw in records:
        if not isinstance(raw, Mapping) or set(raw) != record_fields:
            raise ValueError("checkpoint inventory record field mismatch")
        identity = _identity(raw)
        if identity not in expected or identity in seen:
            raise ValueError("checkpoint identity mismatch or duplicate")
        locator = raw["locator"]
        locator_path = Path(locator) if isinstance(locator, str) else Path()
        if (
            raw["format"] != "UCOPE_SCOUT_R01_CHECKPOINT_INVENTORY_V1"
            or not isinstance(locator, str) or "\\" in locator or locator_path.is_absolute()
            or not locator_path.parts or ".." in locator_path.parts or locator in locators
            or type(raw["size_bytes"]) is not int or raw["size_bytes"] <= 0
            or type(raw["sha256"]) is not str or len(raw["sha256"]) != 64
        ):
            raise ValueError("checkpoint inventory locator/size/digest mismatch")
        path = root / locator_path
        encoded = _read_plain_file_once(path, root)
        if len(encoded) != raw["size_bytes"] or hashlib.sha256(encoded).hexdigest() != raw["sha256"]:
            raise ValueError("checkpoint file size/SHA mismatch")
        seen.add(identity)
        locators.add(locator)
        normalized.append(dict(raw))
    if seen != expected:
        raise ValueError("checkpoint inventory is not the exact 72 Cartesian identities")
    actual_files, actual_directories = _enumerate_plain_tree(root)
    if actual_files != set(top_names) | locators:
        raise ValueError("complete tree file inventory has missing or extra files")
    expected_directories = set()
    for locator in locators:
        parent = Path(locator).parent
        while parent.parts:
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    if actual_directories != expected_directories:
        raise ValueError("complete tree directory inventory has missing or extra entries")
    aggregate = hashlib.sha256(_canonical_bytes(records)).hexdigest()
    if aggregate != binding.checkpoint_inventory_sha256 or documents["terminal-receipt.json"].get("checkpoint_inventory_aggregate_sha256") != aggregate:
        raise ValueError("checkpoint inventory aggregate mismatch")
    evaluations = result.get("internal_result", {}).get("evaluations")
    if not isinstance(evaluations, list) or len(evaluations) != binding.checkpoint_count:
        raise ValueError("retained evaluation inventory must contain exactly 72 rows")
    evaluation_identities = [_identity(item) for item in evaluations if isinstance(item, Mapping)]
    if len(evaluation_identities) != binding.checkpoint_count or set(evaluation_identities) != expected or len(set(evaluation_identities)) != binding.checkpoint_count:
        raise ValueError("retained evaluation identity mismatch or duplicate")
    order = {arm: index for index, arm in enumerate(config.arms)}
    normalized.sort(key=lambda row: (order[row["arm_id"]], config.seed_ids.index(row["seed_id"]), row["fold_id"], row["root_update"]))
    return {
        "root": str(root.resolve()),
        "top_hashes": top_hashes,
        "top_files": top_files,
        "run_binding": run_binding,
        "config": config.to_dict(),
        "checkpoint_inventory_aggregate_sha256": aggregate,
        "checkpoint_inventory": normalized,
        "retained_evaluations": evaluations,
    }


def _validate_state(state: Any, *, arm_id: str, stage: str) -> dict[str, Any]:
    import torch

    if not isinstance(state, Mapping):
        raise ValueError(f"checkpoint {stage} state must be a mapping")
    beta_size = 7 if stage == "root" else 5
    shapes = {"beta": (beta_size,)}
    if arm_id.endswith("FLEX"):
        shapes.update({
            "residual.0.weight": (64, 9), "residual.0.bias": (64,),
            "residual.2.weight": (64, 64), "residual.2.bias": (64,),
            "residual.4.weight": (1, 64), "residual.4.bias": (1,),
        })
    if set(state) != set(shapes):
        raise ValueError(f"checkpoint {stage} tensor inventory mismatch")
    for name, tensor in state.items():
        if not isinstance(tensor, torch.Tensor) or tensor.device.type != "cpu" or tensor.dtype != torch.float32 or tuple(tensor.shape) != shapes[name] or not torch.isfinite(tensor).all().item():
            raise ValueError(f"invalid checkpoint tensor {stage}.{name}")
    return dict(state)


def _probe_refresh_rows(config: ScoutConfig, fold_id: int, root_updates: int) -> int:
    episode_indices = [
        index for index in range(config.episodes_per_context)
        if (index // 10) % 2 == fold_id
    ]
    probe_flags = tuple(index % 10 < 5 for index in episode_indices for _context in range(8))
    return sum(
        probe_flags[(update * config.batch_size + offset) % len(probe_flags)]
        for update in range(root_updates)
        for offset in range(config.batch_size)
    )


def _validate_checkpoint_activity(
    activity: Any,
    *,
    config: ScoutConfig,
    arm_id: str,
    fold_id: int,
    root_updates: int,
    tail_updates: int,
) -> None:
    if not isinstance(activity, Mapping) or set(activity) != CHECKPOINT_ACTIVITY_FIELDS:
        raise ValueError("checkpoint activity field inventory mismatch")
    frozen = arm_id.startswith("FT-")
    expected = {
        "root_inventory": config.episodes_per_context * 4,
        "tail_inventory": config.episodes_per_context * 2,
        "root_optimizer_updates": root_updates,
        "tail_optimizer_updates": tail_updates,
        "root_example_exposures": root_updates * config.batch_size,
        "tail_example_exposures": tail_updates * config.batch_size,
        "target_refresh_events": root_updates if arm_id == "MT-XF-FLEX" else 0,
        "target_refresh_rows": (
            _probe_refresh_rows(config, fold_id, root_updates)
            if arm_id == "MT-XF-FLEX" else 0
        ),
        "target_materialization_events": int(frozen),
        "target_materialization_rows": config.episodes_per_context * 4 if frozen else 0,
        "nonfinite_events": 0,
    }
    if any(activity.get(name) != value for name, value in expected.items()):
        raise ValueError("checkpoint activity/progress ledger mismatch")
    for prefix, updates in (("root", root_updates), ("tail", tail_updates)):
        clipping = activity[f"{prefix}_clipping_events"]
        norm_sum = activity[f"{prefix}_gradient_norm_sum"]
        norm_max = activity[f"{prefix}_gradient_norm_max"]
        if type(clipping) is not int or not 0 <= clipping <= updates:
            raise ValueError("checkpoint clipping activity mismatch")
        if (
            not isinstance(norm_sum, (int, float)) or isinstance(norm_sum, bool)
            or not isinstance(norm_max, (int, float)) or isinstance(norm_max, bool)
            or not math.isfinite(float(norm_sum)) or not math.isfinite(float(norm_max))
            or not 0 <= norm_max <= norm_sum
        ):
            raise ValueError("checkpoint gradient activity mismatch")


def _load_policy_checkpoint(
    path: Path,
    record: Mapping[str, Any],
    *,
    complete_root: Path,
    config: ScoutConfig,
    run_binding: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    import torch

    encoded = _read_plain_file_once(path, complete_root)
    if len(encoded) != record["size_bytes"] or hashlib.sha256(encoded).hexdigest() != record["sha256"]:
        raise ValueError("checkpoint changed before scoring")
    try:
        value = torch.load(io.BytesIO(encoded), map_location="cpu", weights_only=False)
    except TypeError:  # pragma: no cover - compatibility with old torch only
        value = torch.load(io.BytesIO(encoded), map_location="cpu")
    required = {
        "format", "schema_version", "object_id", "config", "run_binding", "arm_id", "seed_id", "fold_id",
        "root_updates", "tail_updates", "activity", "rng", "root_state", "tail_state",
        "root_optimizer_state", "tail_optimizer_state", "frozen_root_targets",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("checkpoint payload field inventory mismatch")
    if value["format"] != "UCOPE_SCOUT_R01_POLICY_CHECKPOINT_V1" or value["schema_version"] != 1 or value["object_id"] != B1_OBJECT_ID:
        raise ValueError("checkpoint payload identity mismatch")
    if value["config"] != config.to_dict() or value["run_binding"] != run_binding or (value["arm_id"], value["seed_id"], value["fold_id"], value["root_updates"]) != _identity(record):
        raise ValueError("checkpoint payload config/binding/progress mismatch")
    expected_tail = value["root_updates"] // 2 if value["arm_id"] == "MT-XF-FLEX" else config.tail_updates
    if value["tail_updates"] != expected_tail or value["rng"] != rng_contract():
        raise ValueError("checkpoint progress/activity/RNG mismatch")
    _validate_checkpoint_activity(
        value["activity"], config=config, arm_id=value["arm_id"], fold_id=value["fold_id"],
        root_updates=value["root_updates"], tail_updates=value["tail_updates"],
    )
    if not isinstance(value["root_optimizer_state"], Mapping) or not isinstance(value["tail_optimizer_state"], Mapping):
        raise ValueError("checkpoint retained optimizer payload is malformed")
    targets = value["frozen_root_targets"]
    if value["arm_id"].startswith("FT-"):
        if not isinstance(targets, torch.Tensor) or targets.device.type != "cpu" or targets.dtype != torch.float32 or tuple(targets.shape) != (config.episodes_per_context * 4,) or not torch.isfinite(targets).all().item():
            raise ValueError("checkpoint frozen target payload mismatch")
    elif targets is not None:
        raise ValueError("moving-target checkpoint contains frozen targets")
    return (
        _validate_state(value["root_state"], arm_id=value["arm_id"], stage="root"),
        _validate_state(value["tail_state"], arm_id=value["arm_id"], stage="tail"),
    )


def _metric(row: Mapping[str, Any]) -> tuple[int, Fraction, Fraction]:
    regret = row["max_regret"]
    agreement = row["minimum_tail_agreement"]
    return (
        int(row["root_hamming"]),
        Fraction(int(regret["numerator"]), int(regret["denominator"])),
        Fraction(int(agreement["numerator"]), int(agreement["denominator"])),
    )


def _checkpoint_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_id = {tuple(row["identity"][key] for key in ("arm_id", "seed_id", "fold_id", "root_update")): row for row in rows}
    policy_categories = [
        {"identity": row["identity"], "competent": row["odd_competent_policy"], "near": row["odd_near_policy"]}
        for row in rows
    ]
    seed_categories = []
    for arm in ARMS:
        for seed in SEEDS:
            folds = [by_id[(arm, seed, fold, 320)] for fold in (0, 1)]
            seed_categories.append({
                "arm_id": arm, "seed_id": seed,
                "competent": all(row["odd_competent_policy"] for row in folds),
                "near": all(row["odd_near_policy"] for row in folds),
            })
    arm_categories = []
    for arm in ARMS:
        arm_seeds = [row for row in seed_categories if row["arm_id"] == arm]
        arm_categories.append({
            "arm_id": arm,
            "competent_seed_count": sum(row["competent"] for row in arm_seeds),
            "near_seed_count": sum(row["near"] for row in arm_seeds),
            "competent": sum(row["competent"] for row in arm_seeds) >= 2,
            "near": sum(row["near"] for row in arm_seeds) >= 2,
        })

    def paired(first: str, second: str, update: int) -> dict[str, Any]:
        pairs = []
        for seed in SEEDS:
            for fold in (0, 1):
                a, b = by_id[(first, seed, fold, update)], by_id[(second, seed, fold, update)]
                a_over_b = materially_dominates(_metric(a), _metric(b))
                b_over_a = materially_dominates(_metric(b), _metric(a))
                pairs.append({"seed_id": seed, "fold_id": fold, "first_over_second": a_over_b, "second_over_first": b_over_a})
        first_count = sum(row["first_over_second"] for row in pairs)
        second_count = sum(row["second_over_first"] for row in pairs)
        return {
            "first_arm": first, "second_arm": second, "root_update": update, "pairs": pairs,
            "first_count": first_count, "second_count": second_count,
            "first_clear": first_count >= 4 and second_count <= 1,
            "second_clear": second_count >= 4 and first_count <= 1,
        }

    ft_pairs = [paired("FT-XF-FLEX", "FT-XF-BC", update) for update in CHECKPOINT_UPDATES]
    curve_first = any(ft_pairs[index]["first_clear"] and ft_pairs[index + 1]["first_clear"] for index in range(3))
    curve_second = any(ft_pairs[index]["second_clear"] and ft_pairs[index + 1]["second_clear"] for index in range(3))
    all_pair_curves = []
    for first_index, first in enumerate(ARMS):
        for second in ARMS[first_index + 1:]:
            checkpoints = [paired(first, second, update) for update in CHECKPOINT_UPDATES]
            separated = any(
                (checkpoints[index]["first_clear"] and checkpoints[index + 1]["first_clear"])
                or (checkpoints[index]["second_clear"] and checkpoints[index + 1]["second_clear"])
                for index in range(3)
            )
            all_pair_curves.append({"first_arm": first, "second_arm": second, "checkpoints": checkpoints, "separated": separated})

    mt_ft_pairs = []
    for seed in SEEDS:
        for fold in (0, 1):
            mt, ft = by_id[("MT-XF-FLEX", seed, fold, 320)], by_id[("FT-XF-FLEX", seed, fold, 320)]
            tail_equal = mt["tail_periods"] == ft["tail_periods"]
            root_difference = sum(mt["root_actions"][cell] != ft["root_actions"][cell] for cell in mt["root_actions"])
            mt_ft_pairs.append({"seed_id": seed, "fold_id": fold, "tail_equal": tail_equal, "root_hamming": root_difference})
    mt_ft_root_separation = all(row["tail_equal"] for row in mt_ft_pairs) and sum(row["root_hamming"] >= 2 for row in mt_ft_pairs) >= 2

    similarities = []
    for update in CHECKPOINT_UPDATES:
        medians = {}
        for arm in ARMS:
            values = [_metric(by_id[(arm, seed, fold, update)]) for seed in SEEDS for fold in (0, 1)]
            medians[arm] = {
                "root_hamming": fraction_record(median_fraction([Fraction(row[0]) for row in values])),
                "max_regret": fraction_record(median_fraction([row[1] for row in values])),
                "minimum_tail_agreement": fraction_record(median_fraction([row[2] for row in values])),
            }
        h = [Fraction(item["root_hamming"]["numerator"], item["root_hamming"]["denominator"]) for item in medians.values()]
        r = [Fraction(item["max_regret"]["numerator"], item["max_regret"]["denominator"]) for item in medians.values()]
        q = [Fraction(item["minimum_tail_agreement"]["numerator"], item["minimum_tail_agreement"]["denominator"]) for item in medians.values()]
        spreads = {"root_hamming": max(h) - min(h), "max_regret": max(r) - min(r), "minimum_tail_agreement": max(q) - min(q)}
        similar = spreads["root_hamming"] <= 1 and spreads["max_regret"] <= Fraction(1, 50) and spreads["minimum_tail_agreement"] <= Fraction(1, 20)
        similarities.append({"root_update": update, "arm_medians": medians, "spreads": {key: fraction_record(value) for key, value in spreads.items()}, "similar": similar})
    no_arm_category = not any(row["competent"] or row["near"] for row in arm_categories)
    all_similar_failure = no_arm_category and all(row["similar"] for row in similarities) and not any(row["separated"] for row in all_pair_curves) and not mt_ft_root_separation
    return {
        "policy_categories": policy_categories,
        "seed_categories": seed_categories,
        "arm_categories": arm_categories,
        "ft_flex_vs_ft_bc": {"checkpoints": ft_pairs, "curve_first": curve_first, "curve_second": curve_second},
        "all_pair_curves": all_pair_curves,
        "mt_ft_root_separation": {"pairs": mt_ft_pairs, "present": mt_ft_root_separation},
        "similarity": similarities,
        "all_similar_odd_failure": all_similar_failure,
    }


def audit_complete_tree(root: str | Path, binding: AuditBinding = ACCEPTED_BINDING) -> dict[str, Any]:
    """Perform the two immutable, sequential scoring passes and return an in-memory audit."""
    pre = snapshot_input_tree(root, binding)
    config = ScoutConfig.from_dict(pre["config"])
    retained = {
        _identity(item): _sanitize_retained_even(item)
        for item in pre["retained_evaluations"]
    }
    odd_rows = []
    even_rows = []
    even_matches = []
    for periods, destination in ((ODD_PERIODS, odd_rows), (EVEN_PERIODS, even_rows)):
        for record in pre["checkpoint_inventory"]:
            path = Path(root) / record["locator"]
            root_state, tail_state = _load_policy_checkpoint(
                path, record, complete_root=Path(root), config=config,
                run_binding=pre["run_binding"],
            )
            row = score_policy_states(root_state, tail_state, periods, _identity_dict(_identity(record)))
            row["checkpoint"] = {key: record[key] for key in ("locator", "size_bytes", "sha256")}
            destination.append(row)
            if periods == EVEN_PERIODS:
                matched = validate_even_match(row, retained[_identity(record)])
                even_matches.append(matched)
    post = snapshot_input_tree(root, binding)
    before_public = {key: value for key, value in pre.items() if key != "retained_evaluations"}
    after_public = {key: value for key, value in post.items() if key != "retained_evaluations"}
    if before_public != after_public:
        raise ValueError("input tree changed during audit")
    summaries = _checkpoint_summary(odd_rows)
    recomputed_even = {_identity(row["identity"]): row for row in even_rows}
    even_arm_competence = {
        arm: sum(
            all(policy_competence(recomputed_even[(arm, seed, fold, 320)]) for fold in (0, 1))
            for seed in SEEDS
        ) >= 2
        for arm in ARMS
    }
    predicates = {
        "oracle_unique": all(row["unique"] for row in build_restricted_oracle(ODD_PERIODS).values()),
        "odd_recast": same_arm_odd_recast(summaries["arm_categories"], even_arm_competence),
        "ft_flex_over_bc": summaries["ft_flex_vs_ft_bc"]["checkpoints"][-1]["first_clear"],
        "ft_bc_over_flex": summaries["ft_flex_vs_ft_bc"]["checkpoints"][-1]["second_clear"],
        "mt_ft_root_separation": summaries["mt_ft_root_separation"]["present"],
        "all_similar_odd_failure": summaries["all_similar_odd_failure"],
    }
    return {
        "format": FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "complete": True,
        "definitions": frozen_definitions(),
        "odd_oracle": build_restricted_oracle(ODD_PERIODS),
        "even_oracle": build_restricted_oracle(EVEN_PERIODS),
        "input_inventory_before": before_public,
        "input_inventory_after": after_public,
        "read_counts": {"odd": len(odd_rows), "even": len(even_rows)},
        "odd_rows": odd_rows,
        "even_rows": [
            {"recomputed": row, "retained": retained[_identity(row["identity"])]}
            for row in even_rows
        ],
        "even_match": even_matches,
        "summaries": summaries,
        "retained_even_arm_competence": even_arm_competence,
        "route": choose_route(predicates),
        "effect_counters": dict(EFFECT_COUNTERS),
        "claim_ceiling": CLAIM_CEILING,
    }


def _validate_embedded_input_inventory(
    value: Mapping[str, Any], binding: AuditBinding,
) -> dict[tuple[str, str, int, int], dict[str, Any]]:
    required = {
        "root", "top_hashes", "top_files", "run_binding", "config",
        "checkpoint_inventory_aggregate_sha256", "checkpoint_inventory",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("embedded input inventory schema mismatch")
    expected_top = {
        "result.json": binding.result_sha256,
        "resource-ledger.json": binding.resource_ledger_sha256,
        "terminal-receipt.json": binding.terminal_receipt_sha256,
    }
    if value["top_hashes"] != expected_top:
        raise ValueError("embedded input top digest binding mismatch")
    top_files = value["top_files"]
    if not isinstance(top_files, list) or [row.get("locator") for row in top_files if isinstance(row, Mapping)] != list(expected_top):
        raise ValueError("embedded input top file inventory mismatch")
    for row in top_files:
        if set(row) != {"locator", "size_bytes", "sha256"} or type(row["size_bytes"]) is not int or row["size_bytes"] <= 0 or row["sha256"] != expected_top[row["locator"]]:
            raise ValueError("embedded input top file record mismatch")
    config = ScoutConfig.from_dict(value["config"])
    if config != ScoutConfig.b1() or value["run_binding"] != binding.run_binding():
        raise ValueError("embedded input config/run binding mismatch")
    if binding.required_root is not None:
        expected_root = str((Path(__file__).resolve().parents[4] / binding.required_root).resolve())
        if value["root"] != expected_root:
            raise ValueError("embedded input accepted root mismatch")
    elif type(value["root"]) is not str or not Path(value["root"]).is_absolute():
        raise ValueError("embedded input synthetic root must be absolute")
    records = value["checkpoint_inventory"]
    if not isinstance(records, list) or len(records) != binding.checkpoint_count:
        raise ValueError("embedded input checkpoint inventory count mismatch")
    if hashlib.sha256(_canonical_bytes(records)).hexdigest() != binding.checkpoint_inventory_sha256 or value["checkpoint_inventory_aggregate_sha256"] != binding.checkpoint_inventory_sha256:
        raise ValueError("embedded input checkpoint aggregate binding mismatch")
    expected_identities = _expected_identities(config)
    by_identity: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {
            "format", "arm_id", "seed_id", "fold_id", "root_update", "locator", "size_bytes", "sha256",
        }:
            raise ValueError("embedded input checkpoint record schema mismatch")
        identity = _identity(record)
        if identity not in expected_identities or identity in by_identity:
            raise ValueError("embedded input checkpoint identity mismatch")
        if (
            record["format"] != "UCOPE_SCOUT_R01_CHECKPOINT_INVENTORY_V1"
            or type(record["locator"]) is not str or not record["locator"] or "\\" in record["locator"]
            or Path(record["locator"]).is_absolute() or ".." in Path(record["locator"]).parts
            or type(record["size_bytes"]) is not int or record["size_bytes"] <= 0
            or type(record["sha256"]) is not str or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
        ):
            raise ValueError("embedded input checkpoint locator/size/SHA mismatch")
        by_identity[identity] = dict(record)
    if set(by_identity) != expected_identities:
        raise ValueError("embedded input exact 72 checkpoint identities mismatch")
    return by_identity


def validate_audit_core(
    value: Mapping[str, Any], *, binding: AuditBinding = ACCEPTED_BINDING,
) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "complete", "definitions", "odd_oracle",
        "even_oracle", "input_inventory_before", "input_inventory_after", "read_counts",
        "odd_rows", "even_rows", "even_match", "summaries", "retained_even_arm_competence",
        "route", "effect_counters", "claim_ceiling",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("audit core field inventory mismatch")
    if (
        value["format"] != FORMAT or value["schema_version"] != 1
        or value["object_id"] != OBJECT_ID or value["complete"] is not True
        or value["definitions"] != frozen_definitions()
        or value["odd_oracle"] != build_restricted_oracle(ODD_PERIODS)
        or value["even_oracle"] != build_restricted_oracle(EVEN_PERIODS)
        or value["claim_ceiling"] != CLAIM_CEILING
        or value["effect_counters"] != EFFECT_COUNTERS
        or any(value["effect_counters"].values())
    ):
        raise ValueError("audit core frozen identity/definitions/effects mismatch")
    if value["input_inventory_before"] != value["input_inventory_after"]:
        raise ValueError("audit input pre/post inventories differ")
    checkpoint_by_identity = _validate_embedded_input_inventory(
        value["input_inventory_before"], binding,
    )
    expected = _expected_identities(ScoutConfig.b1())
    odd_rows = value["odd_rows"]
    even_rows = value["even_rows"]
    matches = value["even_match"]
    if (
        not isinstance(odd_rows, list) or not isinstance(even_rows, list)
        or not isinstance(matches, list) or len(odd_rows) != 72 or len(even_rows) != 72
        or len(matches) != 72 or value["read_counts"] != {"odd": 72, "even": 72}
    ):
        raise ValueError("audit core policy/read inventory mismatch")
    odd_identities = {_identity(row["identity"]) for row in odd_rows if isinstance(row, Mapping)}
    even_identities = {
        _identity(row["recomputed"]["identity"])
        for row in even_rows
        if isinstance(row, Mapping) and set(row) == {"recomputed", "retained"}
    }
    match_identities = {
        _identity(row["identity"])
        for row in matches
        if isinstance(row, Mapping) and row.get("match") is True
    }
    if odd_identities != expected or even_identities != expected or match_identities != expected:
        raise ValueError("audit core exact policy identity inventory mismatch")
    expected_order = list(checkpoint_by_identity)
    if (
        [_identity(row["identity"]) for row in odd_rows] != expected_order
        or [_identity(row["recomputed"]["identity"]) for row in even_rows] != expected_order
        or [_identity(row["identity"]) for row in matches] != expected_order
    ):
        raise ValueError("audit core exact policy identity order mismatch")
    for row in [*odd_rows, *(item["recomputed"] for item in even_rows)]:
        identity = _identity(row["identity"])
        record = checkpoint_by_identity[identity]
        expected_checkpoint = {
            key: record[key] for key in ("locator", "size_bytes", "sha256")
        }
        if row.get("checkpoint") != expected_checkpoint:
            raise ValueError("direct row checkpoint join mismatch")
    for row in odd_rows:
        validate_direct_scored_row(row, ODD_PERIODS)
    for row in even_rows:
        validate_direct_scored_row(row["recomputed"], EVEN_PERIODS)
    recomputed_matches = [
        validate_even_match(row["recomputed"], row["retained"])
        for row in even_rows
    ]
    if recomputed_matches != matches:
        raise ValueError("audit direct even match inventory does not recompute")
    rebuilt_summaries = _checkpoint_summary(odd_rows)
    if value["summaries"] != rebuilt_summaries:
        raise ValueError("audit summaries do not independently recompute from direct odd rows")
    if not isinstance(value["summaries"], Mapping) or set(value["summaries"]) != {
        "policy_categories", "seed_categories", "arm_categories", "ft_flex_vs_ft_bc",
        "all_pair_curves", "mt_ft_root_separation", "similarity", "all_similar_odd_failure",
    }:
        raise ValueError("audit summary inventory mismatch")
    even_competence = value["retained_even_arm_competence"]
    if not isinstance(even_competence, Mapping) or set(even_competence) != set(ARMS) or any(type(even_competence[arm]) is not bool for arm in ARMS):
        raise ValueError("audit even competence inventory mismatch")
    even_by_id = {
        _identity(row["recomputed"]["identity"]): row["recomputed"]
        for row in even_rows
    }
    rebuilt_even_competence = {
        arm: sum(
            all(policy_competence(even_by_id[(arm, seed, fold, 320)]) for fold in (0, 1))
            for seed in SEEDS
        ) >= 2
        for arm in ARMS
    }
    if even_competence != rebuilt_even_competence:
        raise ValueError("audit recomputed even arm competence mismatch")
    rebuilt_predicates = {
        "oracle_unique": all(row["unique"] for row in build_restricted_oracle(ODD_PERIODS).values()),
        "odd_recast": same_arm_odd_recast(rebuilt_summaries["arm_categories"], rebuilt_even_competence),
        "ft_flex_over_bc": rebuilt_summaries["ft_flex_vs_ft_bc"]["checkpoints"][-1]["first_clear"],
        "ft_bc_over_flex": rebuilt_summaries["ft_flex_vs_ft_bc"]["checkpoints"][-1]["second_clear"],
        "mt_ft_root_separation": rebuilt_summaries["mt_ft_root_separation"]["present"],
        "all_similar_odd_failure": rebuilt_summaries["all_similar_odd_failure"],
    }
    route = value["route"]
    if not isinstance(route, Mapping) or route != choose_route(rebuilt_predicates):
        raise ValueError("audit route does not recompute")
    return dict(value)


def _validation_read_bytes(value: Mapping[str, Any]) -> int:
    inventory = value.get("input_inventory_before", {})
    sources = value.get("implementation_sources_before", {})
    top_files = inventory.get("top_files") if isinstance(inventory, Mapping) else None
    checkpoints = inventory.get("checkpoint_inventory") if isinstance(inventory, Mapping) else None
    source_files = sources.get("files") if isinstance(sources, Mapping) else None
    if not all(isinstance(rows, list) for rows in (top_files, checkpoints, source_files)):
        raise ValueError("tail validation byte inventories are missing")
    records = [*top_files, *checkpoints, *source_files]
    if any(
        not isinstance(record, Mapping) or type(record.get("size_bytes")) is not int
        or record["size_bytes"] <= 0
        for record in records
    ):
        raise ValueError("tail validation byte inventory is invalid")
    input_bytes = sum(record["size_bytes"] for record in [*top_files, *checkpoints])
    source_bytes = sum(record["size_bytes"] for record in source_files)
    admission = value.get("admission", {})
    receipt = admission.get("receipt", {}) if isinstance(admission, Mapping) else {}
    if not isinstance(receipt, Mapping) or not ADMISSION_RECEIPT_FIELDS.issubset(receipt):
        raise ValueError("tail admission read inventory is missing")
    raw_receipt = {key: receipt[key] for key in ADMISSION_RECEIPT_FIELDS}
    receipt_bytes = len((json.dumps(raw_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    provenance = receipt.get("provenance")
    if not isinstance(provenance, Mapping) or type(provenance.get("producer_size_bytes")) is not int or provenance["producer_size_bytes"] <= 0:
        raise ValueError("tail admission producer byte inventory is missing")
    # Tail performs two strict artifact validations and one final source check;
    # the latter snapshots both its argument and current bytes, for four exact
    # reads of the frozen source inventory in total.
    return input_bytes + 4 * source_bytes + receipt_bytes + 3 * provenance["producer_size_bytes"]


def _validate_embedded_admission(value: Mapping[str, Any]) -> None:
    required = {
        "receipt", "receipt_sha256_before", "receipt_sha256_after",
        "receipt_sha256_prepublication", "unchanged",
    }
    if not isinstance(value, Mapping) or set(value) != required or value["unchanged"] is not True:
        raise ValueError("embedded admission binding schema mismatch")
    receipt = value["receipt"]
    if not isinstance(receipt, Mapping) or set(receipt) != ADMISSION_RECEIPT_FIELDS | {"receipt_sha256", "provenance"}:
        raise ValueError("embedded central admission receipt schema mismatch")
    raw = {key: receipt[key] for key in ADMISSION_RECEIPT_FIELDS}
    encoded = (json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _validate_central_admission_payload(raw, encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    if (
        receipt["receipt_sha256"] != digest
        or receipt["provenance"] != _admission_provenance()
        or value["receipt_sha256_before"] != digest
        or value["receipt_sha256_after"] != digest
        or value["receipt_sha256_prepublication"] != digest
    ):
        raise ValueError("embedded admission canonical digest/provenance mismatch")


def validate_audit_artifact(
    value: Mapping[str, Any],
    *,
    expected_size_bytes: int,
    binding: AuditBinding = ACCEPTED_BINDING,
) -> dict[str, Any]:
    execution_fields = {
        "admission", "implementation_sources_before", "implementation_sources_after",
        "resources", "publication",
    }
    if not isinstance(value, Mapping) or not execution_fields.issubset(value):
        raise ValueError("audit final artifact execution fields are incomplete")
    core = {key: item for key, item in value.items() if key not in execution_fields}
    validate_audit_core(core, binding=binding)
    validate_implementation_source_snapshots(
        value["implementation_sources_before"], value["implementation_sources_after"],
    )
    admission = value["admission"]
    _validate_embedded_admission(admission)
    publication = value["publication"]
    if not isinstance(publication, Mapping) or publication != {
        "locator": publication.get("locator"),
        "create_once": True,
        "canonical_json": True,
        "hidden_same_parent_staging": True,
        "hidden_write_fsync_readback_decode_strict_validate": True,
        "visible_publish": "SAME_VOLUME_CREATE_ONCE_HARDLINK_AFTER_ACTUAL_ENVELOPE_ACCEPTANCE",
        "output_size_bytes": expected_size_bytes,
        "durable_peak_bytes": expected_size_bytes,
    } or type(publication["locator"]) is not str or not publication["locator"]:
        raise ValueError("audit publication binding mismatch")
    resources = value["resources"]
    if not isinstance(resources, Mapping):
        raise ValueError("audit resource evidence is missing")
    recomputed_resources = _validate_resources(
        resources.get("pre_tail_observed", {}),
        durable_peak_bytes=expected_size_bytes,
        final_output_bytes=expected_size_bytes,
        validation_read_bytes=_validation_read_bytes(value),
    )
    if resources != recomputed_resources:
        raise ValueError("audit resource evidence does not recompute")
    return dict(value)


def execute_audit_to_output(
    complete_root: str | Path,
    admission_receipt: str | Path,
    output: str | Path,
    *,
    binding: AuditBinding = ACCEPTED_BINDING,
) -> Path:
    """Execute one admitted, result-bearing, read-only audit and publish one JSON."""
    root = Path(complete_root)
    receipt_path = Path(admission_receipt)
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"audit output is create-once: {destination}")
    parent = destination.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("audit output parent must already be a plain directory")
    resolved_root = root.resolve(strict=True)
    resolved_destination = destination.resolve(strict=False)
    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError:
        pass
    else:
        raise ValueError("audit output must be outside the immutable B1 complete tree")
    if receipt_path.resolve(strict=True) == resolved_destination:
        raise ValueError("admission receipt and output may not alias")

    admission_before = validate_fresh_admission(receipt_path)
    scratch = Path(tempfile.mkdtemp(prefix=".ucope-odd-support-audit-scratch-", dir=parent))
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.hidden-staging-", dir=parent))
    hidden = staging / "artifact.json"
    monitor: AuditResourceMonitor | None = None
    published = False
    try:
        monitor = AuditResourceMonitor(scratch, staging).start()
        source_before = snapshot_implementation_sources()
        audit = audit_complete_tree(root, binding)
        validate_audit_core(audit, binding=binding)
        if audit.get("effect_counters") != EFFECT_COUNTERS or any(audit["effect_counters"].values()):
            raise ValueError("audit protected no-effect counters are not all zero")
        admission_after = validate_admission(receipt_path)
        if admission_after != admission_before:
            raise ValueError("admission receipt changed during audit")
        source_after = snapshot_implementation_sources()
        validate_implementation_source_snapshots(source_before, source_after)
        if validate_admission(receipt_path) != admission_before:
            raise ValueError("admission receipt changed before publication")
        pre_tail = monitor.snapshot()
        document = {
            **audit,
            "admission": {
                "receipt": admission_before,
                "receipt_sha256_before": admission_before["receipt_sha256"],
                "receipt_sha256_after": admission_after["receipt_sha256"],
                "receipt_sha256_prepublication": admission_after["receipt_sha256"],
                "unchanged": True,
            },
            "implementation_sources_before": source_before,
            "implementation_sources_after": source_after,
            "resources": {},
            "publication": {},
        }
        encoded_size = 1
        for _ in range(64):
            document["resources"] = _validate_resources(
                pre_tail,
                durable_peak_bytes=encoded_size,
                final_output_bytes=encoded_size,
                validation_read_bytes=_validation_read_bytes(document),
            )
            document["publication"] = {
                "locator": destination.name,
                "create_once": True,
                "canonical_json": True,
                "hidden_same_parent_staging": True,
                "hidden_write_fsync_readback_decode_strict_validate": True,
                "visible_publish": "SAME_VOLUME_CREATE_ONCE_HARDLINK_AFTER_ACTUAL_ENVELOPE_ACCEPTANCE",
                "output_size_bytes": encoded_size,
                "durable_peak_bytes": encoded_size,
            }
            encoded = _canonical_bytes(document)
            if len(encoded) == encoded_size:
                break
            encoded_size = len(encoded)
        else:
            raise ValueError("audit output byte-size fixed point did not converge")
        validate_audit_artifact(document, expected_size_bytes=encoded_size, binding=binding)
        with hidden.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        monitor.observe_transaction_point()
        readback = _read_plain_file_once(hidden, staging)
        if readback != encoded:
            raise ValueError("hidden audit output readback mismatch")
        try:
            decoded = json.loads(
                readback.decode("utf-8"),
                parse_constant=lambda token: (_ for _ in ()).throw(
                    ValueError(f"nonfinite JSON token: {token}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("hidden audit output is not strict JSON") from error
        if _canonical_bytes(decoded) != readback:
            raise ValueError("hidden audit output is not canonical JSON")
        validate_audit_artifact(decoded, expected_size_bytes=len(readback), binding=binding)
        final_input = snapshot_input_tree(root, binding)
        final_input_public = {key: value for key, value in final_input.items() if key != "retained_evaluations"}
        if final_input_public != audit["input_inventory_before"]:
            raise ValueError("input tree changed after hidden publication validation")
        validate_implementation_source_snapshots(source_before, snapshot_implementation_sources())
        if validate_admission(receipt_path) != admission_before:
            raise ValueError("admission receipt changed after hidden validation")
        completed_resources = monitor.finish()
        monitor = None
        _validate_actual_transaction(pre_tail, completed_resources, document["resources"])
        os.link(hidden, destination)
        published = True
        return destination
    finally:
        if monitor is not None:
            with contextlib.suppress(BaseException):
                monitor.finish()
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(scratch, ignore_errors=True)
