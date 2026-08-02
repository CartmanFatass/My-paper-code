"""Analyze the V-K0C R30 autoregressive order-transport localization result.

Consumes the four durable V-K0C inputs -- the immutable input-authorization
manifest and the three frozen JSONL row files -- and recomputes the entire
ruled factorized causal record solely from those files, per:

  docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md (VC-D6 and
  amendments A-VC-3, A-VC-7, A-VC-8, A-VC-9, A-VC-10)
  docs/external-review/rounds/20260801_vk0b_valid_rerun_result/21_PRO_OPEN_RAW.md
  (sections 1-9: Factor A-E result semantics, the seed-first nested
  bootstrap, delta=0.5 materiality, the 0.75 competence bridge)
  docs/external-review/rounds/20260801_vk0c_design_conformance/22_PRO_CONVERGENCE_3.md
  (Gate-B realization clarifications; row layout is realization-level)

The V-K0C driver (scripts/audit_vk0c_order_transport.py) does not exist yet.
This module is developed and tested against a self-defined row schema that
implements every field A-VC-10 and A-VC-6 name explicitly, using synthetic
fixture rows built by its test suite -- exactly the house pattern
scripts/analyze_vk0_result.py used before scripts/audit_vk0b_r30_access.py
existed.

The analyzer never guesses: any row or manifest field that fails the frozen
schema raises SchemaValidationError, and no summary is written. Missing or
hash-mismatched authorization is never a schema refusal -- it is precedence-1
invalidity (INVALID_VK0C_ORDER_TRANSPORT_AUDIT), a normal analysis result.
Authorization is established solely from vk0c_input_manifest.json and the
stamped row fields; the analyzer never infers it from directory names,
filesystem state, checkpoint filenames, or unstamped artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

# =============================================================================
# Frozen identity and schema constants
# =============================================================================

# VC-D1 / VC-D6: V-K0C reuses the same VK0 contract -- it is not a new toy.
VK0_CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
VK0C_SCHEMA_VERSION = "vk0c-1"
VK0B_TRACE_SCHEMA_VERSION = "vk0-trace-2"

POLICY_STATE_FRESH = "fresh"
POLICY_STATE_TRAINED = "trained"
POLICY_STATES = {POLICY_STATE_FRESH, POLICY_STATE_TRAINED}

ORDER_CANONICAL = "canonical"
ORDER_REVERSED = "reversed"
ORDER_CODES = {ORDER_CANONICAL, ORDER_REVERSED}
ORDER_CODES_TUPLE = (ORDER_CANONICAL, ORDER_REVERSED)

STRATUM_CANONICAL_OCCUPANCY = "CANONICAL_OCCUPANCY"
STRATUM_REVERSED_OCCUPANCY = "REVERSED_OCCUPANCY"
OCCUPANCY_STRATA = {STRATUM_CANONICAL_OCCUPANCY, STRATUM_REVERSED_OCCUPANCY}

TOKEN_KEEP = "KEEP"
TOKEN_SET = "SET"
TOKEN_KINDS = {TOKEN_KEEP, TOKEN_SET}

AGENT_KEYS = ("agent_0", "agent_1")

N_OUTCOMES = 16

CONTROL_TYPE_POSITIVE = "ORDER_CONJUGACY_POSITIVE_CONTROL"
CONTROL_TYPE_FRESH_INIT = "FRESH_INIT_DETERMINISM_CONTROL"
CONTROL_TYPES = {CONTROL_TYPE_POSITIVE, CONTROL_TYPE_FRESH_INIT}

# A-VC-3: the frozen anchor-population identities the manifest must declare.
FROZEN_CHECK_ROW_COUNT = 5_376
FROZEN_ANCHOR_COUNT = 2_688
FROZEN_EPISODES_PER_SEED = 64
FROZEN_NONINITIAL_CHECKS = 7
FROZEN_SEED_COUNT = 6

# The six SHA-256 bindings A-VC-3 requires the manifest to carry.
VK0B_SOURCE_BINDING_FIELDS = (
    "renewal_check_trace_sha256",
    "renewal_counterfactual_units_sha256",
    "train_and_checkpoint_manifest_sha256",
    "summary_sha256",
    "vk0a_panel_sha256",
    "vk0a_sidecar_sha256",
)

# Section 7 (Inference) / MEASUREMENT: the task-semantic materiality unit,
# reused unchanged from V-K0B -- no new effect-size threshold is introduced.
MATERIALITY = 0.5

# The existing 0.75 slow/fast competence floor -- the bridge to V-K0B.
COMPETENCE_FLOOR_MIN = 0.75

# Inference: seed-first nested bootstrap, 10,000 iterations, one frozen seed.
BOOTSTRAP_ITERATIONS = 10_000
LOWER_QUANTILE = 0.05
UPPER_QUANTILE = 0.95

REQUIRED_STRATA = ("pooled", STRATUM_CANONICAL_OCCUPANCY, STRATUM_REVERSED_OCCUPANCY)

# A numerical epsilon for "differ at >=1 matched state" (Factor A base
# presence): distinguishes a genuine distributional difference from
# floating-point accumulation noise. This is a realization detail (not a
# scientific threshold) -- it gates nothing on its own; only the D_R
# materiality test (+-0.5) decides promotion.
TV_DIFFERENCE_EPSILON = 1e-9

# A tight numerical tolerance for the canonical-probability reconstruction
# check (p_hat_j = raw_joint_mass_j / sum_k raw_joint_mass_k must hold
# exactly in float64 arithmetic once the raw sum has passed its own
# dtype-derived mass_tolerance).
CANONICAL_PROBABILITY_RECONSTRUCTION_TOLERANCE = 1e-9

# VC-D7 / A-VC-10 amendments: the one frozen bootstrap seed, mirrored
# (not imported) from scripts/analyze_vk0_result.py -- same VK0_CONTRACT_ID,
# same "|bootstrap" suffix, same SHA-256-prefix derivation, so the value is
# bit-identical without coupling this analyzer's runtime to the VK0B
# analyzer module. Drift is guarded by
# test_analyze_vk0c_result.py::test_bootstrap_seed_matches_vk0_analyzer.
BOOTSTRAP_SEED_DERIVATION = (
    "int.from_bytes(sha256('VK0_TOY_RENEWAL_URGENCY|bootstrap')[:8], 'big')"
)


def _derive_bootstrap_seed() -> int:
    digest = hashlib.sha256(f"{VK0_CONTRACT_ID}|bootstrap".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


BOOTSTRAP_SEED = _derive_bootstrap_seed()


# =============================================================================
# Refusal on schema violation
# =============================================================================


class SchemaValidationError(ValueError):
    """Raised when any row or manifest field violates the frozen VK0C
    schema. The analyzer refuses to select a result rather than guess -- no
    summary is produced when this is raised."""


# =============================================================================
# Small type predicates
# =============================================================================


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _is_nonneg_number(value: Any) -> bool:
    return _is_number(value) and float(value) >= 0.0


def _is_probability(value: Any) -> bool:
    return _is_number(value) and 0.0 <= float(value) <= 1.0


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_sha256_hex(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_five_vector(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 5 and all(_is_number(x) for x in value)


def _is_five_unit_vector(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 5 and all(_is_probability(x) for x in value)


def _is_binary(x: Any) -> bool:
    if isinstance(x, bool):
        return True
    if isinstance(x, int):
        return x in (0, 1)
    if isinstance(x, float):
        return x in (0.0, 1.0)
    return False


def _is_five_binary_vector(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 5 and all(_is_binary(x) for x in value)


def _is_agent_pair_str(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value.keys()) == set(AGENT_KEYS)
        and all(_is_nonempty_str(value[k]) for k in AGENT_KEYS)
    )


def _is_agent_pair_prob(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value.keys()) == set(AGENT_KEYS)
        and all(_is_probability(value[k]) for k in AGENT_KEYS)
    )


def _is_agent_pair_bool(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value.keys()) == set(AGENT_KEYS)
        and all(isinstance(value[k], bool) for k in AGENT_KEYS)
    )


def _is_token(value: Any) -> bool:
    if not isinstance(value, dict) or set(value.keys()) != {"kind", "skill"}:
        return False
    kind = value.get("kind")
    skill = value.get("skill")
    if kind not in TOKEN_KINDS:
        return False
    if kind == TOKEN_SET:
        return _is_nonempty_str(skill)
    return skill is None


def _is_set_marginal(value: Any) -> bool:
    if not isinstance(value, dict) or set(value.keys()) != set(AGENT_KEYS):
        return False
    for k in AGENT_KEYS:
        d = value[k]
        if not isinstance(d, dict) or not d:
            return False
        if not all(isinstance(skill, str) and skill for skill in d.keys()):
            return False
        if not all(_is_probability(v) for v in d.values()):
            return False
    return True


def _is_lifetime_mass(value: Any) -> bool:
    if not isinstance(value, dict) or set(value.keys()) != set(AGENT_KEYS):
        return False
    for k in AGENT_KEYS:
        d = value[k]
        if not isinstance(d, dict) or not d:
            return False
        if not all(_is_nonneg_number(v) for v in d.values()):
            return False
    return True


def _is_bool_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(isinstance(v, bool) for v in value.values())


def _is_occupancy_summary(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for entry in value:
        if not isinstance(entry, dict) or set(entry.keys()) != {"state_key", "occupancy_probability"}:
            return False
        if not isinstance(entry.get("state_key"), str) or not entry["state_key"]:
            return False
        if not _is_probability(entry.get("occupancy_probability")):
            return False
    return True


# =============================================================================
# Order helpers
# =============================================================================


def _first_agent(order_code: str) -> str:
    return "agent_0" if order_code == ORDER_CANONICAL else "agent_1"


def _second_agent(order_code: str) -> str:
    return "agent_1" if order_code == ORDER_CANONICAL else "agent_0"


def _resulting_skill(token: dict[str, Any], incumbent_skill: str) -> str:
    return incumbent_skill if token["kind"] == TOKEN_KEEP else token["skill"]


# =============================================================================
# Row schema validation -- vk0c_matched_state_rows.jsonl (A-VC-10)
# =============================================================================


def validate_matched_state_row(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"matched_state_row[{index}]: {msg}")

    if row.get("contract_id") != VK0_CONTRACT_ID:
        fail("contract_id must equal the frozen VK0 contract id")
    if row.get("vk0c_schema_version") != VK0C_SCHEMA_VERSION:
        fail("vk0c_schema_version must equal 'vk0c-1'")
    if not _is_int(row.get("training_seed")):
        fail("training_seed must be an int")
    if not isinstance(row.get("episode_id"), (int, str)) or isinstance(row.get("episode_id"), bool):
        fail("episode_id must be an int or str")
    if not _is_int(row.get("check_index")):
        fail("check_index must be an int")
    if row.get("occupancy_stratum") not in OCCUPANCY_STRATA:
        fail("occupancy_stratum must be CANONICAL_OCCUPANCY or REVERSED_OCCUPANCY")
    if not _is_nonempty_str(row.get("checkpoint_hash")):
        fail("checkpoint_hash must be a non-empty str")
    if row.get("policy_state") not in POLICY_STATES:
        fail("policy_state must be fresh or trained")
    if row.get("order_code") not in ORDER_CODES:
        fail("order_code must be canonical or reversed")
    outcome_index = row.get("outcome_index")
    if not _is_int(outcome_index) or not (0 <= outcome_index < N_OUTCOMES):
        fail("outcome_index must be an int in [0, 15]")

    if not _is_agent_pair_str(row.get("incumbent_skill")):
        fail("incumbent_skill must be a {'agent_0','agent_1'} str pair")
    if not _is_agent_pair_str(row.get("final_skill")):
        fail("final_skill must be a {'agent_0','agent_1'} str pair")

    first_token = row.get("first_token")
    second_token = row.get("second_token")
    if not _is_token(first_token):
        fail("first_token must be a {'kind','skill'} token")
    if not _is_token(second_token):
        fail("second_token must be a {'kind','skill'} token")

    # Structural consistency: final_skill must equal the transition each
    # token implies for its physical agent, given this row's order.
    order_code = row.get("order_code")
    incumbent = row.get("incumbent_skill")
    final_skill = row.get("final_skill")
    if order_code in ORDER_CODES and _is_agent_pair_str(incumbent) and _is_agent_pair_str(final_skill):
        if _is_token(first_token):
            first_agent = _first_agent(order_code)
            expected = _resulting_skill(first_token, incumbent[first_agent])
            if expected != final_skill[first_agent]:
                fail(
                    f"final_skill[{first_agent}] ({final_skill[first_agent]!r}) does not match "
                    f"first_token's implied transition ({expected!r})"
                )
            # Same-label SET absent: an agent may never SET to its own
            # current incumbent skill (VC-D6 required validity condition).
            if first_token["kind"] == TOKEN_SET and first_token["skill"] == incumbent[first_agent]:
                fail(f"first_token is a same-label SET onto {first_agent}'s own incumbent skill")
        if _is_token(second_token):
            second_agent = _second_agent(order_code)
            expected = _resulting_skill(second_token, incumbent[second_agent])
            if expected != final_skill[second_agent]:
                fail(
                    f"final_skill[{second_agent}] ({final_skill[second_agent]!r}) does not match "
                    f"second_token's implied transition ({expected!r})"
                )
            if second_token["kind"] == TOKEN_SET and second_token["skill"] == incumbent[second_agent]:
                fail(f"second_token is a same-label SET onto {second_agent}'s own incumbent skill")

    dtype = row.get("policy_probability_dtype")
    if dtype not in ("float32", "float64"):
        fail("policy_probability_dtype must be float32 or float64")

    raw_first = row.get("raw_first_mass")
    raw_second = row.get("raw_second_mass")
    raw_joint = row.get("raw_joint_mass")
    if not _is_nonneg_number(raw_first):
        fail("raw_first_mass must be a finite non-negative number")
    if not _is_nonneg_number(raw_second):
        fail("raw_second_mass must be a finite non-negative number")
    if not _is_nonneg_number(raw_joint):
        fail("raw_joint_mass must be a finite non-negative number")
    elif _is_number(raw_first) and _is_number(raw_second):
        expected_joint = float(raw_first) * float(raw_second)
        if abs(float(raw_joint) - expected_joint) > 1e-6:
            fail("raw_joint_mass must equal raw_first_mass * raw_second_mass")

    if not _is_probability(row.get("canonical_joint_probability")):
        fail("canonical_joint_probability must be a probability in [0,1]")

    if not _is_agent_pair_prob(row.get("keep_marginal")):
        fail("keep_marginal must be a {'agent_0','agent_1'} probability pair")
    if not _is_set_marginal(row.get("set_marginal")):
        fail("set_marginal must be a {'agent_0','agent_1'} dict of skill->probability")

    if not _is_number(row.get("five_step_reward")):
        fail("five_step_reward must be a finite number")
    if not _is_five_binary_vector(row.get("slow_match_vector")):
        fail("slow_match_vector must be a five-element 0/1 vector")
    if not _is_five_binary_vector(row.get("fast_match_vector")):
        fail("fast_match_vector must be a five-element 0/1 vector")

    if not isinstance(row.get("task_optimal"), bool):
        fail("task_optimal must be a bool")
    if not isinstance(row.get("slow_coverage_failure"), bool):
        fail("slow_coverage_failure must be a bool")
    if not isinstance(row.get("fast_coverage_failure"), bool):
        fail("fast_coverage_failure must be a bool")
    if not isinstance(row.get("boundary_state_replay_ok"), bool):
        fail("boundary_state_replay_ok must be a bool")

    return errors


# =============================================================================
# Row schema validation -- vk0c_propagation_rows.jsonl (A-VC-6)
# =============================================================================


def validate_propagation_row(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"propagation_row[{index}]: {msg}")

    if row.get("contract_id") != VK0_CONTRACT_ID:
        fail("contract_id must equal the frozen VK0 contract id")
    if row.get("vk0c_schema_version") != VK0C_SCHEMA_VERSION:
        fail("vk0c_schema_version must equal 'vk0c-1'")
    if not _is_int(row.get("training_seed")):
        fail("training_seed must be an int")
    if not isinstance(row.get("episode_id"), (int, str)) or isinstance(row.get("episode_id"), bool):
        fail("episode_id must be an int or str")
    if row.get("order_code") not in ORDER_CODES:
        fail("order_code must be canonical or reversed")
    if row.get("policy_state") not in POLICY_STATES:
        fail("policy_state must be fresh or trained")
    if not _is_nonempty_str(row.get("checkpoint_hash")):
        fail("checkpoint_hash must be a non-empty str")

    if not _is_occupancy_summary(row.get("occupancy_summary")):
        fail("occupancy_summary must be a non-empty list of {'state_key','occupancy_probability'}")

    if not _is_five_unit_vector(row.get("expected_slow_match_vector")):
        fail("expected_slow_match_vector must be a five-element vector of values in [0,1]")
    if not _is_five_unit_vector(row.get("expected_fast_match_vector")):
        fail("expected_fast_match_vector must be a five-element vector of values in [0,1]")

    reward_vector = row.get("expected_external_reward_vector")
    if not _is_five_vector(reward_vector):
        fail("expected_external_reward_vector must be a five-element numeric vector")
    episode_return = row.get("expected_episode_return")
    if not _is_number(episode_return):
        fail("expected_episode_return must be a finite number")
    elif isinstance(reward_vector, list) and len(reward_vector) == 5 and all(_is_number(x) for x in reward_vector):
        if abs(float(episode_return) - float(sum(reward_vector))) > 1e-6:
            fail("expected_episode_return must equal the sum of expected_external_reward_vector")

    if not _is_agent_pair_prob(row.get("expected_keep_rate")):
        fail("expected_keep_rate must be a {'agent_0','agent_1'} probability pair")
    if not _is_agent_pair_prob(row.get("expected_set_rate")):
        fail("expected_set_rate must be a {'agent_0','agent_1'} probability pair")
    if not _is_agent_pair_prob(row.get("expected_renewal_rate")):
        fail("expected_renewal_rate must be a {'agent_0','agent_1'} probability pair")
    if not _is_lifetime_mass(row.get("lifetime_mass")):
        fail("lifetime_mass must be a {'agent_0','agent_1'} dict of run_length->mass")

    if not _is_bool_dict(row.get("replay_conformance")):
        fail("replay_conformance must be a non-empty dict of booleans")

    return errors


# =============================================================================
# Row schema validation -- vk0c_control_rows.jsonl (positive control + fresh-init)
# =============================================================================


def validate_control_row(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"control_row[{index}]: {msg}")

    if row.get("contract_id") != VK0_CONTRACT_ID:
        fail("contract_id must equal the frozen VK0 contract id")
    if row.get("vk0c_schema_version") != VK0C_SCHEMA_VERSION:
        fail("vk0c_schema_version must equal 'vk0c-1'")
    control_type = row.get("control_type")
    if control_type not in CONTROL_TYPES:
        fail("control_type must be ORDER_CONJUGACY_POSITIVE_CONTROL or FRESH_INIT_DETERMINISM_CONTROL")
        return errors
    if not _is_int(row.get("training_seed")):
        fail("training_seed must be an int")

    if control_type == CONTROL_TYPE_POSITIVE:
        if not isinstance(row.get("episode_id"), (int, str)) or isinstance(row.get("episode_id"), bool):
            fail("episode_id must be an int or str")
        if not _is_int(row.get("check_index")):
            fail("check_index must be an int")
        if not _is_agent_pair_str(row.get("forced_assignment")):
            fail("forced_assignment must be a {'agent_0','agent_1'} str pair")
        for prefix in (ORDER_CANONICAL, ORDER_REVERSED):
            if not _is_agent_pair_str(row.get(f"{prefix}_realized_skill")):
                fail(f"{prefix}_realized_skill must be a {{'agent_0','agent_1'}} str pair")
            actions = row.get(f"{prefix}_primitive_actions")
            if not isinstance(actions, list) or len(actions) != 5:
                fail(f"{prefix}_primitive_actions must be a five-element list")
            if not _is_five_vector(row.get(f"{prefix}_reward_vector")):
                fail(f"{prefix}_reward_vector must be a five-element numeric vector")
            if not _is_five_binary_vector(row.get(f"{prefix}_slow_match_vector")):
                fail(f"{prefix}_slow_match_vector must be a five-element 0/1 vector")
            if not _is_five_binary_vector(row.get(f"{prefix}_fast_match_vector")):
                fail(f"{prefix}_fast_match_vector must be a five-element 0/1 vector")
            if not _is_nonempty_str(row.get(f"{prefix}_post_window_state_hash")):
                fail(f"{prefix}_post_window_state_hash must be a non-empty str")
    else:
        if not _is_nonempty_str(row.get("construction_1_param_hash")):
            fail("construction_1_param_hash must be a non-empty str")
        if not _is_nonempty_str(row.get("construction_2_param_hash")):
            fail("construction_2_param_hash must be a non-empty str")

    return errors


def _positive_control_holds(row: dict[str, Any]) -> bool:
    """Independently re-derives the positive-control pass/fail from the raw
    recorded vectors -- never trusts a pre-computed 'pass' boolean the row
    might additionally carry, mirroring the repository convention of
    recomputing rather than trusting a driver-asserted flag."""
    forced = row["forced_assignment"]
    for prefix in (ORDER_CANONICAL, ORDER_REVERSED):
        if row[f"{prefix}_realized_skill"] != forced:
            return False
    if row[f"{ORDER_CANONICAL}_realized_skill"] != row[f"{ORDER_REVERSED}_realized_skill"]:
        return False
    if row[f"{ORDER_CANONICAL}_primitive_actions"] != row[f"{ORDER_REVERSED}_primitive_actions"]:
        return False
    for field in ("reward_vector", "slow_match_vector", "fast_match_vector"):
        a = row[f"{ORDER_CANONICAL}_{field}"]
        b = row[f"{ORDER_REVERSED}_{field}"]
        if len(a) != len(b) or any(abs(float(x) - float(y)) > 1e-9 for x, y in zip(a, b)):
            return False
    if row[f"{ORDER_CANONICAL}_post_window_state_hash"] != row[f"{ORDER_REVERSED}_post_window_state_hash"]:
        return False
    return True


def _fresh_init_deterministic(row: dict[str, Any]) -> bool:
    return row["construction_1_param_hash"] == row["construction_2_param_hash"]


# =============================================================================
# Manifest schema validation (A-VC-3)
# =============================================================================


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("contract_id") != VK0_CONTRACT_ID:
        errors.append("manifest.contract_id must equal the frozen VK0 contract id")
    if manifest.get("vk0c_schema_version") != VK0C_SCHEMA_VERSION:
        errors.append("manifest.vk0c_schema_version must equal 'vk0c-1'")
    if manifest.get("vk0b_trace_schema_version") != VK0B_TRACE_SCHEMA_VERSION:
        errors.append("manifest.vk0b_trace_schema_version must equal 'vk0-trace-2'")

    for field in ("check_row_count", "deduplicated_anchor_count", "episodes_per_seed", "noninitial_checks"):
        if not _is_int(manifest.get(field)):
            errors.append(f"manifest.{field} must be an int")

    seeds = manifest.get("seeds")
    if not isinstance(seeds, dict) or not seeds:
        errors.append("manifest.seeds must be a non-empty dict keyed by training seed")
    else:
        for seed_key, entry in seeds.items():
            if not isinstance(entry, dict):
                errors.append(f"manifest.seeds[{seed_key}] must be a dict")
                continue
            if not _is_nonempty_str(entry.get("checkpoint_hash")):
                errors.append(f"manifest.seeds[{seed_key}].checkpoint_hash must be a non-empty str")
            if not _is_nonempty_str(entry.get("resolved_config_hash")):
                errors.append(f"manifest.seeds[{seed_key}].resolved_config_hash must be a non-empty str")
            # exposure_authorization is OPTIONAL at schema level: its total
            # absence is itself a meaningful precedence-1 finding (below),
            # never a hard refusal -- mirrors VK0's oracle-authorization
            # pattern. If present, it must be a well-formed non-empty dict.
            auth = entry.get("exposure_authorization")
            if auth is not None and (not isinstance(auth, dict) or not auth):
                errors.append(f"manifest.seeds[{seed_key}].exposure_authorization must be a non-empty dict when present")

    # vk0b_source_bindings is likewise OPTIONAL at schema level; its absence
    # or malformation is a precedence-1 finding, not a refusal.
    bindings = manifest.get("vk0b_source_bindings")
    if bindings is not None:
        if not isinstance(bindings, dict):
            errors.append("manifest.vk0b_source_bindings must be a dict when present")
        else:
            for field in VK0B_SOURCE_BINDING_FIELDS:
                if field in bindings and not _is_sha256_hex(bindings[field]):
                    errors.append(f"manifest.vk0b_source_bindings.{field} must be a 64-hex-char SHA-256 when present")

    return errors


# =============================================================================
# I/O
# =============================================================================


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SchemaValidationError(f"{path}:{line_no}: invalid JSON ({exc})") from exc
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _git_blob_sha1(path: Path) -> str:
    """The exact `git hash-object` algorithm, computed without invoking git
    (subagents never run Git; this replicates the hashing scheme in-process
    against the analyzer's own source bytes)."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


# =============================================================================
# Precedence-1: INVALID_VK0C_ORDER_TRANSPORT_AUDIT
# =============================================================================


def _group_matched_state_rows(
    rows: list[dict[str, Any]]
) -> dict[tuple[int, Any, int, str, str], list[dict[str, Any]]]:
    groups: dict[tuple[int, Any, int, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            int(row["training_seed"]),
            row["episode_id"],
            int(row["check_index"]),
            row["policy_state"],
            row["order_code"],
        )
        groups.setdefault(key, []).append(row)
    return groups


def compute_invalid_reasons(
    matched_rows: list[dict[str, Any]],
    propagation_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []

    # ---- Manifest authorization (A-VC-3 / A-VC-10) ----
    bindings = manifest.get("vk0b_source_bindings")
    if (
        not isinstance(bindings, dict)
        or any(field not in bindings or not _is_sha256_hex(bindings[field]) for field in VK0B_SOURCE_BINDING_FIELDS)
    ):
        reasons.append(
            "MANIFEST_SOURCE_BINDINGS_MISSING_OR_MISMATCHED: vk0b_source_bindings missing or "
            "does not carry all six required SHA-256 bindings"
        )

    seeds_map = manifest.get("seeds")
    if not isinstance(seeds_map, dict) or len(seeds_map) != FROZEN_SEED_COUNT:
        reasons.append(
            f"MANIFEST_SEED_COUNT_MISMATCH: manifest.seeds must carry exactly {FROZEN_SEED_COUNT} entries"
        )
    else:
        missing_auth = sorted(
            seed_key
            for seed_key, entry in seeds_map.items()
            if not isinstance(entry, dict) or not isinstance(entry.get("exposure_authorization"), dict) or not entry.get("exposure_authorization")
        )
        if missing_auth:
            reasons.append(f"SEED_EXPOSURE_AUTHORIZATION_MISSING: seed(s) {missing_auth}")

    for field, frozen in (
        ("check_row_count", FROZEN_CHECK_ROW_COUNT),
        ("deduplicated_anchor_count", FROZEN_ANCHOR_COUNT),
        ("episodes_per_seed", FROZEN_EPISODES_PER_SEED),
        ("noninitial_checks", FROZEN_NONINITIAL_CHECKS),
    ):
        if manifest.get(field) != frozen:
            reasons.append(f"MANIFEST_POPULATION_MISMATCH: manifest.{field} ({manifest.get(field)!r}) != {frozen}")

    # ---- Row-level checkpoint hash cross-check against the manifest (trained rows only) ----
    if isinstance(seeds_map, dict):
        mismatched_matched = sorted(
            {
                str(row["training_seed"])
                for row in matched_rows
                if row["policy_state"] == POLICY_STATE_TRAINED
                and (
                    str(row["training_seed"]) not in seeds_map
                    or row["checkpoint_hash"] != seeds_map[str(row["training_seed"])].get("checkpoint_hash")
                )
            }
        )
        if mismatched_matched:
            reasons.append(
                f"ROW_CHECKPOINT_HASH_MISMATCH_WITH_MANIFEST: matched-state trained row seed(s) {mismatched_matched}"
            )
        mismatched_prop = sorted(
            {
                str(row["training_seed"])
                for row in propagation_rows
                if row["policy_state"] == POLICY_STATE_TRAINED
                and (
                    str(row["training_seed"]) not in seeds_map
                    or row["checkpoint_hash"] != seeds_map[str(row["training_seed"])].get("checkpoint_hash")
                )
            }
        )
        if mismatched_prop:
            reasons.append(
                f"ROW_CHECKPOINT_HASH_MISMATCH_WITH_MANIFEST: propagation trained row seed(s) {mismatched_prop}"
            )

    # ---- Exact enumeration validity (VC-D6 required validity conditions) ----
    groups = _group_matched_state_rows(matched_rows)
    anchor_strata: dict[tuple[int, Any, int], set[str]] = {}
    for key, rows in groups.items():
        seed, episode, check_index, policy_state, order_code = key
        indices = sorted(r["outcome_index"] for r in rows)
        if indices != list(range(N_OUTCOMES)):
            reasons.append(f"ANCHOR_INVENTORY_INCONSISTENT: group {key} outcome_index set is not exactly 0..15")

        dtypes = {r["policy_probability_dtype"] for r in rows}
        if len(dtypes) != 1:
            reasons.append(f"POLICY_PROBABILITY_DTYPE_INCONSISTENT: group {key} carries mixed dtypes {sorted(dtypes)}")
        else:
            dtype = next(iter(dtypes))
            eps = float(np.finfo(np.dtype(dtype)).eps)
            tolerance = 32.0 * eps
            raw_sum = math.fsum(float(r["raw_joint_mass"]) for r in rows)
            if abs(raw_sum - 1.0) > tolerance:
                reasons.append(
                    f"RAW_JOINT_MASS_NOT_NORMALIZED: group {key} raw_joint_mass sum={raw_sum!r} "
                    f"deviates from 1 by more than mass_tolerance={tolerance!r}"
                )
            else:
                for r in rows:
                    expected_canonical = float(r["raw_joint_mass"]) / raw_sum
                    if abs(float(r["canonical_joint_probability"]) - expected_canonical) > CANONICAL_PROBABILITY_RECONSTRUCTION_TOLERANCE:
                        reasons.append(
                            f"CANONICAL_PROBABILITY_NOT_RECONSTRUCTED: group {key} outcome_index="
                            f"{r['outcome_index']} canonical_joint_probability does not equal "
                            f"raw_joint_mass / sum(raw_joint_mass)"
                        )
                        break

        if any(r["boundary_state_replay_ok"] is False for r in rows):
            reasons.append(f"ORDER_TRANSPORT_STATE_REPLAY_FAILED: group {key}")

        anchor_key = (seed, episode, check_index)
        anchor_strata.setdefault(anchor_key, set()).add(rows[0]["occupancy_stratum"])

    for anchor_key, strata in anchor_strata.items():
        if len(strata) != 1:
            reasons.append(f"ANCHOR_INVENTORY_INCONSISTENT: anchor {anchor_key} reports inconsistent occupancy_stratum {sorted(strata)}")

    # Common-coordinate mapping complete: at a given (seed, episode,
    # check_index, policy_state), the canonical-order and reversed-order
    # groups must enumerate the identical set of 16 (agent_0, agent_1)
    # final-skill coordinates -- otherwise TV/D_R cannot be computed on a
    # shared coordinate space.
    by_policy_anchor: dict[tuple[int, Any, int, str], dict[str, list[dict[str, Any]]]] = {}
    for key, rows in groups.items():
        seed, episode, check_index, policy_state, order_code = key
        by_policy_anchor.setdefault((seed, episode, check_index, policy_state), {})[order_code] = rows
    for pa_key, by_order in by_policy_anchor.items():
        if ORDER_CANONICAL in by_order and ORDER_REVERSED in by_order:
            coords_can = {(r["final_skill"]["agent_0"], r["final_skill"]["agent_1"]) for r in by_order[ORDER_CANONICAL]}
            coords_rev = {(r["final_skill"]["agent_0"], r["final_skill"]["agent_1"]) for r in by_order[ORDER_REVERSED]}
            if coords_can != coords_rev or len(coords_can) != N_OUTCOMES or len(coords_rev) != N_OUTCOMES:
                reasons.append(f"COMMON_COORDINATE_MAPPING_INCOMPLETE: policy-anchor {pa_key}")

    # ---- Factual-row reproduction (propagation replay_conformance) ----
    false_replay = [
        (p["training_seed"], p["episode_id"], p["order_code"], p["policy_state"])
        for p in propagation_rows
        if any(v is False for v in p["replay_conformance"].values())
    ]
    if false_replay:
        reasons.append(
            f"FACTUAL_ROW_REPRODUCTION_FAILED: {len(false_replay)} propagation row(s), e.g. {false_replay[0]}"
        )

    # ---- Controls ----
    failed_positive = [
        (c["training_seed"], c["episode_id"], c["check_index"])
        for c in control_rows
        if c["control_type"] == CONTROL_TYPE_POSITIVE and not _positive_control_holds(c)
    ]
    if failed_positive:
        reasons.append(
            f"ORDER_CONJUGACY_POSITIVE_CONTROL_FAILED: {len(failed_positive)} anchor(s), e.g. {failed_positive[0]}"
        )

    nondeterministic = [
        c["training_seed"] for c in control_rows
        if c["control_type"] == CONTROL_TYPE_FRESH_INIT and not _fresh_init_deterministic(c)
    ]
    if nondeterministic:
        reasons.append(f"FRESH_INITIALIZATION_NONDETERMINISTIC: seed(s) {sorted(set(nondeterministic))}")

    return reasons


# =============================================================================
# Matched-state anchor table (TV, R_order, D_R, optimal/coverage masses)
# =============================================================================


def build_anchor_table(matched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per (training_seed, episode_id, check_index, policy_state),
    computed purely from the canonical normalized probability p_hat (never
    raw masses) per A-VC-7, with both orders' quantities carried side by
    side so TV/D_R/optimal-mass/coverage-mass can all be read off directly."""
    groups = _group_matched_state_rows(matched_rows)
    by_policy_anchor: dict[tuple[int, Any, int, str], dict[str, list[dict[str, Any]]]] = {}
    for key, rows in groups.items():
        seed, episode, check_index, policy_state, order_code = key
        by_policy_anchor.setdefault((seed, episode, check_index, policy_state), {})[order_code] = rows

    table: list[dict[str, Any]] = []
    for (seed, episode, check_index, policy_state), by_order in by_policy_anchor.items():
        if ORDER_CANONICAL not in by_order or ORDER_REVERSED not in by_order:
            continue
        entry: dict[str, Any] = {
            "training_seed": seed,
            "episode_id": episode,
            "check_index": check_index,
            "policy_state": policy_state,
            "occupancy_stratum": by_order[ORDER_CANONICAL][0]["occupancy_stratum"],
        }
        p_by_order: dict[str, dict[tuple[str, str], float]] = {}
        for order_code in ORDER_CODES_TUPLE:
            rows = by_order[order_code]
            p_map = {
                (r["final_skill"]["agent_0"], r["final_skill"]["agent_1"]): float(r["canonical_joint_probability"])
                for r in rows
            }
            p_by_order[order_code] = p_map
            entry[f"R_{order_code}"] = sum(float(r["canonical_joint_probability"]) * float(r["five_step_reward"]) for r in rows)
            entry[f"optimal_mass_{order_code}"] = sum(
                float(r["canonical_joint_probability"]) for r in rows if r["task_optimal"]
            )
            entry[f"slow_cov_fail_{order_code}"] = sum(
                float(r["canonical_joint_probability"]) for r in rows if r["slow_coverage_failure"]
            )
            entry[f"fast_cov_fail_{order_code}"] = sum(
                float(r["canonical_joint_probability"]) for r in rows if r["fast_coverage_failure"]
            )

        coords = set(p_by_order[ORDER_CANONICAL]) | set(p_by_order[ORDER_REVERSED])
        tv = 0.5 * sum(
            abs(p_by_order[ORDER_CANONICAL].get(z, 0.0) - p_by_order[ORDER_REVERSED].get(z, 0.0)) for z in coords
        )
        entry["TV"] = tv
        entry["D_R"] = entry[f"R_{ORDER_CANONICAL}"] - entry[f"R_{ORDER_REVERSED}"]
        table.append(entry)
    return table


def build_a_r_table(anchor_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A_R(x) = D_R^(T)(x) - D_R^(0)(x), paired within the same matched
    state (section 6, Fresh-initialization control)."""
    trained_by_key = {
        (a["training_seed"], a["episode_id"], a["check_index"]): a
        for a in anchor_table
        if a["policy_state"] == POLICY_STATE_TRAINED
    }
    a_r_table: list[dict[str, Any]] = []
    for fresh in anchor_table:
        if fresh["policy_state"] != POLICY_STATE_FRESH:
            continue
        key = (fresh["training_seed"], fresh["episode_id"], fresh["check_index"])
        trained = trained_by_key.get(key)
        if trained is None:
            continue
        a_r_table.append(
            {
                "training_seed": fresh["training_seed"],
                "episode_id": fresh["episode_id"],
                "occupancy_stratum": fresh["occupancy_stratum"],
                "A_R": trained["D_R"] - fresh["D_R"],
            }
        )
    return a_r_table


# =============================================================================
# Seed-first nested bootstrap (top=training seed, nested=episode)
# =============================================================================


def _cluster_key(entry: dict[str, Any]) -> tuple[int, str]:
    return (int(entry["training_seed"]), str(entry["episode_id"]))


def build_bootstrap_context(
    cluster_source: list[dict[str, Any]], iterations: int, seed: int
) -> dict[str, Any]:
    clusters = sorted({_cluster_key(e) for e in cluster_source})
    cluster_index = {c: i for i, c in enumerate(clusters)}
    n_clusters = len(clusters)

    seeds = sorted({c[0] for c in clusters})
    clusters_of_seed = {s: [cluster_index[c] for c in clusters if c[0] == s] for s in seeds}
    n_seeds = len(seeds)

    rng = np.random.default_rng(seed)
    weight_matrix = np.zeros((iterations, n_clusters), dtype=np.int32)
    for it in range(iterations):
        chosen_positions = rng.integers(0, n_seeds, size=n_seeds)
        for pos in chosen_positions:
            members = clusters_of_seed[seeds[int(pos)]]
            n_members = len(members)
            if n_members == 0:
                continue
            draw = rng.integers(0, n_members, size=n_members)
            drawn = [members[int(i)] for i in draw]
            np.add.at(weight_matrix[it], drawn, 1)

    return {
        "cluster_index": cluster_index,
        "n_clusters": n_clusters,
        "weight_matrix": weight_matrix,
        "seeds": seeds,
    }


def _group_bound(
    values: np.ndarray,
    eligible: np.ndarray,
    mask: np.ndarray,
    cluster_id: np.ndarray,
    ctx: dict[str, Any],
) -> dict[str, float]:
    n_clusters = ctx["n_clusters"]
    weight_matrix = ctx["weight_matrix"]
    included = eligible & mask
    cluster_sum = np.bincount(cluster_id[included], weights=values[included], minlength=n_clusters)
    cluster_count = np.bincount(cluster_id[included], minlength=n_clusters).astype(np.float64)
    total_count = float(cluster_count.sum())
    point = float(cluster_sum.sum() / total_count) if total_count > 0 else float("nan")
    iter_sum = weight_matrix @ cluster_sum
    iter_count = weight_matrix @ cluster_count
    with np.errstate(invalid="ignore", divide="ignore"):
        iter_mean = np.where(iter_count > 0, iter_sum / np.where(iter_count > 0, iter_count, 1), np.nan)
    finite = iter_mean[np.isfinite(iter_mean)]
    lower = float(np.quantile(finite, LOWER_QUANTILE)) if finite.size else float("nan")
    upper = float(np.quantile(finite, UPPER_QUANTILE)) if finite.size else float("nan")
    return {"point": point, "lower_95": lower, "upper_95": upper, "n": int(total_count)}


def _cluster_id_array(table: list[dict[str, Any]], ctx: dict[str, Any]) -> np.ndarray:
    cluster_index = ctx["cluster_index"]
    return np.array([cluster_index[_cluster_key(e)] for e in table], dtype=np.int64)


def _pooled_and_stratified(
    values: np.ndarray, stratum: np.ndarray, cluster_id: np.ndarray, ctx: dict[str, Any]
) -> dict[str, dict[str, float]]:
    eligible = np.ones(len(values), dtype=bool)
    result: dict[str, dict[str, float]] = {}
    for name in REQUIRED_STRATA:
        mask = np.ones(len(values), dtype=bool) if name == "pooled" else (stratum == name)
        result[name] = _group_bound(values, eligible, mask, cluster_id, ctx)
    return result


def _equivalent_within_materiality(stats: dict[str, float]) -> bool:
    """TOST equivalence per Section 7: the two one-sided-test region
    (-MATERIALITY, +MATERIALITY). Mirrors the exact predicate pattern
    scripts/analyze_vk0_result.py::compute_natural already uses for
    'equivalent to zero within +-MATERIALITY' (strict bounds = pass)."""
    return stats["lower_95"] > -MATERIALITY and stats["upper_95"] < MATERIALITY


# =============================================================================
# A-VC-8: pooled + stratified matched-state quantity tables
# =============================================================================


def compute_matched_state_quantities(anchor_table: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    fresh_rows = [a for a in anchor_table if a["policy_state"] == POLICY_STATE_FRESH]
    trained_rows = [a for a in anchor_table if a["policy_state"] == POLICY_STATE_TRAINED]
    a_r_rows = build_a_r_table(anchor_table)

    def stratified(table: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
        if not table:
            nan_stats = {"point": float("nan"), "lower_95": float("nan"), "upper_95": float("nan"), "n": 0}
            return {name: dict(nan_stats) for name in REQUIRED_STRATA}
        values = np.array([float(e[key]) for e in table], dtype=np.float64)
        stratum = np.array([e["occupancy_stratum"] for e in table], dtype=object)
        cluster_id = _cluster_id_array(table, ctx)
        return _pooled_and_stratified(values, stratum, cluster_id, ctx)

    result: dict[str, Any] = {
        "TV_fresh": stratified(fresh_rows, "TV"),
        "TV_trained": stratified(trained_rows, "TV"),
        "D_R_fresh": stratified(fresh_rows, "D_R"),
        "D_R_trained": stratified(trained_rows, "D_R"),
        "A_R": stratified(a_r_rows, "A_R"),
        "optimal_assignment_mass": {},
        "slow_coverage_failure_mass": {},
        "fast_coverage_failure_mass": {},
    }
    for policy_state, table in ((POLICY_STATE_FRESH, fresh_rows), (POLICY_STATE_TRAINED, trained_rows)):
        result["optimal_assignment_mass"][policy_state] = {
            order_code: stratified(table, f"optimal_mass_{order_code}") for order_code in ORDER_CODES_TUPLE
        }
        result["slow_coverage_failure_mass"][policy_state] = {
            order_code: stratified(table, f"slow_cov_fail_{order_code}") for order_code in ORDER_CODES_TUPLE
        }
        result["fast_coverage_failure_mass"][policy_state] = {
            order_code: stratified(table, f"fast_cov_fail_{order_code}") for order_code in ORDER_CODES_TUPLE
        }
    return result


# =============================================================================
# Exact-propagation competence split (Factor B / D condition 3)
# =============================================================================


def compute_propagation_competence(propagation_rows: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    """Reproduces the V-K0B canonical/reversed competence split from the
    exact finite-state propagation of the trained policy: LCB95 > 0.75 for
    canonical order (both slow and fast), UCB95 < 0.75 for reversed order
    (both slow and fast) -- the same pattern
    scripts/analyze_vk0_result.py::compute_competence_floor uses for the
    original per-order competence pass/fail, applied here to the
    propagation-derived per-step match expectations."""
    trained_rows = [p for p in propagation_rows if p["policy_state"] == POLICY_STATE_TRAINED]
    result: dict[str, Any] = {}
    for order_code in ORDER_CODES_TUPLE:
        order_rows = [p for p in trained_rows if p["order_code"] == order_code]
        per_order: dict[str, dict[str, float]] = {}
        for field, out_key in (
            ("expected_slow_match_vector", "slow_match"),
            ("expected_fast_match_vector", "fast_match"),
        ):
            values: list[float] = []
            cluster_ids: list[int] = []
            for row in order_rows:
                cid = ctx["cluster_index"][_cluster_key(row)]
                for v in row[field]:
                    values.append(float(v))
                    cluster_ids.append(cid)
            values_arr = np.asarray(values, dtype=np.float64)
            cluster_arr = np.asarray(cluster_ids, dtype=np.int64)
            eligible = np.ones(len(values_arr), dtype=bool)
            per_order[out_key] = _group_bound(values_arr, eligible, eligible, cluster_arr, ctx)
        result[order_code] = per_order

    canonical_pass = (
        result[ORDER_CANONICAL]["slow_match"]["lower_95"] > COMPETENCE_FLOOR_MIN
        and result[ORDER_CANONICAL]["fast_match"]["lower_95"] > COMPETENCE_FLOOR_MIN
    )
    reversed_decisively_below = (
        result[ORDER_REVERSED]["slow_match"]["upper_95"] < COMPETENCE_FLOOR_MIN
        and result[ORDER_REVERSED]["fast_match"]["upper_95"] < COMPETENCE_FLOOR_MIN
    )
    result["canonical_competence_above_floor"] = bool(canonical_pass)
    result["reversed_competence_below_floor"] = bool(reversed_decisively_below)
    result["split_reproduced"] = bool(canonical_pass and reversed_decisively_below)
    return result


# =============================================================================
# Factor A-E (21_PRO_OPEN_RAW.md section 8, "Result semantics")
# =============================================================================


def compute_factor_a(anchor_table: list[dict[str, Any]], quantities: dict[str, Any]) -> dict[str, Any]:
    fresh_rows = [a for a in anchor_table if a["policy_state"] == POLICY_STATE_FRESH]
    present = any(abs(a["TV"]) > TV_DIFFERENCE_EPSILON for a in fresh_rows)
    pooled_d_r_fresh = quantities["D_R_fresh"]["pooled"]
    equivalent = _equivalent_within_materiality(pooled_d_r_fresh)
    promoted = bool(present and not equivalent)
    return {
        "present": bool(present),
        "promoted": promoted,
        "fresh_D_R_pooled": pooled_d_r_fresh,
        "fresh_D_R_equivalent_within_materiality": bool(equivalent),
    }


def compute_factor_b(quantities: dict[str, Any], propagation_competence: dict[str, Any]) -> dict[str, Any]:
    fresh_equivalent = _equivalent_within_materiality(quantities["D_R_fresh"]["pooled"])
    trained_lcb_above = quantities["D_R_trained"]["pooled"]["lower_95"] > MATERIALITY
    split_reproduced = propagation_competence["split_reproduced"]
    identified = bool(fresh_equivalent and trained_lcb_above and split_reproduced)
    return {
        "identified": identified,
        "fresh_D_R_equivalent_within_materiality": bool(fresh_equivalent),
        "trained_D_R_lcb95_above_materiality": bool(trained_lcb_above),
        "propagation_split_reproduced": bool(split_reproduced),
    }


def compute_factor_c(factor_a: dict[str, Any], quantities: dict[str, Any]) -> dict[str, Any]:
    a_r_pooled = quantities["A_R"]["pooled"]
    amplified = a_r_pooled["lower_95"] > MATERIALITY
    identified = bool(factor_a["present"] and amplified)
    return {
        "identified": identified,
        "requires_factor_a_present": bool(factor_a["present"]),
        "a_r_pooled_lcb95_above_materiality": bool(amplified),
        "a_r_pooled": a_r_pooled,
    }


def compute_factor_d(quantities: dict[str, Any], propagation_competence: dict[str, Any]) -> dict[str, Any]:
    pooled_eq = _equivalent_within_materiality(quantities["D_R_trained"]["pooled"])
    canon_eq = _equivalent_within_materiality(quantities["D_R_trained"][STRATUM_CANONICAL_OCCUPANCY])
    rev_eq = _equivalent_within_materiality(quantities["D_R_trained"][STRATUM_REVERSED_OCCUPANCY])
    split_reproduced = propagation_competence["split_reproduced"]
    identified = bool(pooled_eq and canon_eq and rev_eq and split_reproduced)
    # A-VC-9 / convergence clarification: pooled equivalence produced by
    # opposite material stratum-level direct effects is NOT mediation --
    # it is recorded (as this flag) and leaves the label unresolved.
    stratum_direct_effects_diverge = bool(pooled_eq and not (canon_eq and rev_eq))
    return {
        "identified": identified,
        "pooled_equivalent": bool(pooled_eq),
        "canonical_stratum_equivalent": bool(canon_eq),
        "reversed_stratum_equivalent": bool(rev_eq),
        "propagation_split_reproduced": bool(split_reproduced),
        "stratum_direct_effects_diverge": stratum_direct_effects_diverge,
    }


def compute_residual(
    factor_a: dict[str, Any],
    factor_b: dict[str, Any],
    factor_c: dict[str, Any],
    factor_d: dict[str, Any],
    quantities: dict[str, Any],
    propagation_competence: dict[str, Any],
) -> dict[str, Any]:
    """Factor E / unresolved (section 8): evaluated only once no causal
    factor (A promotion, B, C, D) was identified decisively. The positive
    control necessarily already passed by this point, since its failure is
    precedence-1 invalidity and short-circuits before factor computation."""
    any_identified = factor_a["promoted"] or factor_b["identified"] or factor_c["identified"] or factor_d["identified"]
    if any_identified:
        return {"code": None, "reasoning": "a causal factor was identified decisively; no residual branch applies"}

    distributions_and_returns_agree = (
        not factor_a["present"]
        and _equivalent_within_materiality(quantities["D_R_trained"]["pooled"])
        and _equivalent_within_materiality(quantities["D_R_trained"][STRATUM_CANONICAL_OCCUPANCY])
        and _equivalent_within_materiality(quantities["D_R_trained"][STRATUM_REVERSED_OCCUPANCY])
    )
    if distributions_and_returns_agree and not propagation_competence["split_reproduced"]:
        return {
            "code": "V_K0B_ORDER_GAP_NOT_EXPLAINED_BY_HIGH_POLICY_FACTORIZATION",
            "reasoning": (
                "positive control passed and the exact joint distributions and propagated returns "
                "agree across orders, but the valid V-K0B canonical/reversed competence split was "
                "not reproduced"
            ),
        }
    return {
        "code": "ORDER_TRANSPORT_LOCALIZATION_UNRESOLVED",
        "reasoning": "none of the causal factors was identified decisively",
    }


# =============================================================================
# Top-level analysis
# =============================================================================


def run_analysis(
    manifest_path: str | Path,
    matched_state_path: str | Path,
    propagation_path: str | Path,
    control_path: str | Path,
) -> dict[str, Any]:
    manifest = _load_json(Path(manifest_path))
    matched_rows = _load_jsonl(Path(matched_state_path))
    propagation_rows = _load_jsonl(Path(propagation_path))
    control_rows = _load_jsonl(Path(control_path))

    errors: list[str] = []
    errors.extend(validate_manifest(manifest))
    for i, row in enumerate(matched_rows):
        errors.extend(validate_matched_state_row(row, i))
    for i, row in enumerate(propagation_rows):
        errors.extend(validate_propagation_row(row, i))
    for i, row in enumerate(control_rows):
        errors.extend(validate_control_row(row, i))
    if errors:
        raise SchemaValidationError("; ".join(errors))

    result: dict[str, Any] = {
        "contract_id": VK0_CONTRACT_ID,
        "vk0c_schema_version": VK0C_SCHEMA_VERSION,
        "analyzer_git_blob_sha1": _git_blob_sha1(Path(__file__)),
        "row_counts": {
            "matched_state_rows": len(matched_rows),
            "propagation_rows": len(propagation_rows),
            "control_rows": len(control_rows),
        },
        "training_seeds": sorted({int(row["training_seed"]) for row in matched_rows}),
    }

    invalid_reasons = compute_invalid_reasons(matched_rows, propagation_rows, control_rows, manifest)
    if invalid_reasons:
        result["result"] = {
            "code": "INVALID_VK0C_ORDER_TRANSPORT_AUDIT",
            "reasons": invalid_reasons,
        }
        return result

    anchor_table = build_anchor_table(matched_rows)
    cluster_source = anchor_table + [
        {"training_seed": p["training_seed"], "episode_id": p["episode_id"]}
        for p in propagation_rows
        if p["policy_state"] == POLICY_STATE_TRAINED
    ]
    ctx = build_bootstrap_context(cluster_source, BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED)
    result["bootstrap"] = {
        "iterations": BOOTSTRAP_ITERATIONS,
        "seed": BOOTSTRAP_SEED,
        "seed_derivation": BOOTSTRAP_SEED_DERIVATION,
    }

    quantities = compute_matched_state_quantities(anchor_table, ctx)
    result["matched_state_quantities"] = quantities

    propagation_competence = compute_propagation_competence(propagation_rows, ctx)
    result["propagation_competence"] = propagation_competence

    factor_a = compute_factor_a(anchor_table, quantities)
    factor_b = compute_factor_b(quantities, propagation_competence)
    factor_c = compute_factor_c(factor_a, quantities)
    factor_d = compute_factor_d(quantities, propagation_competence)
    residual = compute_residual(factor_a, factor_b, factor_c, factor_d, quantities, propagation_competence)

    result["factor_a"] = factor_a
    result["factor_b"] = factor_b
    result["factor_c"] = factor_c
    result["factor_d"] = factor_d
    result["residual"] = residual

    labels: list[str] = []
    if factor_a["present"]:
        labels.append("STRUCTURAL_AR_ORDER_SENSITIVITY_PRESENT")
    if factor_a["promoted"]:
        labels.append("STRUCTURAL_AR_ORDER_NONEQUIVARIANCE_MATERIALLY_TASK_RELEVANT")
    if factor_b["identified"]:
        labels.append("LEARNED_CANONICAL_ORDER_SPECIALIZATION_IDENTIFIED")
    if factor_c["identified"]:
        labels.append("STRUCTURAL_ORDER_SENSITIVITY_TRAINING_AMPLIFIED")
    if factor_d["identified"]:
        labels.append("SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED")
    if residual["code"] is not None:
        labels.append(residual["code"])

    result["result"] = {"code": "VK0C_FACTORIZED_RECORD", "labels": labels}
    return result


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the V-K0C order-transport localization result.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--matched-state", required=True)
    parser.add_argument("--propagation", required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    try:
        summary = run_analysis(args.manifest, args.matched_state, args.propagation, args.control)
    except SchemaValidationError as exc:
        print(f"VK0C analyzer refuses -- frozen schema violation: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    _write_json(Path(args.out), summary)
    print(
        f"VK0C analysis completed result={summary['result']['code']} output={args.out}",
        flush=True,
    )


if __name__ == "__main__":
    main()
