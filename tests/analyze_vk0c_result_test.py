"""Calibration tests for the V-K0C order-transport-localization analyzer
(scripts/analyze_vk0c_result.py).

The V-K0C driver (scripts/audit_vk0c_order_transport.py) does not exist yet
-- exactly the situation scripts/analyze_vk0_result.py was developed under.
Every fixture here is synthetic, hand-built against the frozen row schema
(A-VC-10, A-VC-6, A-VC-3) and the frozen Factor A-E predicates (section 8,
docs/external-review/rounds/20260801_vk0b_valid_rerun_result/21_PRO_OPEN_RAW.md).

Reward values and probability masses are chosen so every quantity the
Factor A-E predicates gate on (D_R^(0), D_R^(T), A_R, TV, propagated
competence) is a DEGENERATE (zero-variance) statistic across the whole
synthetic population: every matched anchor carries the identical reward
difference, so the seed-first nested bootstrap's resampled distribution
collapses to a single point exactly equal to the input value regardless of
which clusters a given resample draws. This makes the +-0.5/+-LCB95
boundary tests exact rather than approximate -- a fixture built with
D_R = 0.5 produces lower_95 == upper_95 == 0.5 to full float64 precision,
so the strict-inequality predicates can be tested exactly at their own
frozen boundary.

Each test earns its place by being able to fail: the factor tests plant a
fixture on each side of the ruled +-0.5 / LCB95>0.5 / 0.75 boundary and
check the corresponding factor flips; the invalidity tests plant a
violation of exactly one precedence-1 condition with everything else valid,
so only that condition can be responsible; the paired-negative test
mutates a temporary copy of the analyzer's own equivalence predicate and
shows a boundary fixture's Factor A promotion flips under the mutant while
the untouched production module still reports the original verdict.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_SCRIPT_PATH = _ROOT / "scripts" / "analyze_vk0c_result.py"
_SPEC = importlib.util.spec_from_file_location("analyze_vk0c_result", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)


# =============================================================================
# Fixture builders
# =============================================================================

SKILL_SET = ["A", "B", "C", "D"]
INC0 = "A"
INC1 = "B"


def _order_agents(order_code: str) -> tuple[str, str]:
    return ("agent_0", "agent_1") if order_code == M.ORDER_CANONICAL else ("agent_1", "agent_0")


def make_matched_state_group(
    seed: int,
    episode,
    check_index: int,
    policy_state: str,
    order_code: str,
    occupancy_stratum: str,
    checkpoint_hash: str,
    reward_value: float,
    dtype: str = "float32",
    concentrate_outcome_index: int | None = None,
    task_optimal_index: int | None = None,
    slow_cov_fail_index: int | None = None,
    fast_cov_fail_index: int | None = None,
    replay_ok: bool = True,
) -> list[dict]:
    """Builds the 16 common-coordinate outcome rows for one
    (policy_state, anchor, order). `five_step_reward` is IDENTICAL across
    all 16 rows, so R_order = reward_value exactly regardless of how mass
    is distributed -- this decouples D_R (materiality) from TV (structural
    presence) for precise fixture construction."""
    first_agent, second_agent = _order_agents(order_code)
    incumbent = {"agent_0": INC0, "agent_1": INC1}
    first_tokens = [("KEEP", None)] + [("SET", s) for s in SKILL_SET if s != incumbent[first_agent]]
    second_tokens = [("KEEP", None)] + [("SET", s) for s in SKILL_SET if s != incumbent[second_agent]]

    rows = []
    idx = 0
    for fk, fs in first_tokens:
        for sk, ss in second_tokens:
            final = dict(incumbent)
            final[first_agent] = incumbent[first_agent] if fk == "KEEP" else fs
            final[second_agent] = incumbent[second_agent] if sk == "KEEP" else ss
            if concentrate_outcome_index is not None:
                raw_first = 1.0 if idx == concentrate_outcome_index else 0.0
                raw_second = 1.0 if idx == concentrate_outcome_index else 0.0
            else:
                raw_first = 0.25
                raw_second = 0.25
            raw_joint = raw_first * raw_second
            rows.append(
                {
                    "contract_id": M.VK0_CONTRACT_ID,
                    "vk0c_schema_version": M.VK0C_SCHEMA_VERSION,
                    "training_seed": seed,
                    "episode_id": episode,
                    "check_index": check_index,
                    "occupancy_stratum": occupancy_stratum,
                    "checkpoint_hash": checkpoint_hash,
                    "policy_state": policy_state,
                    "order_code": order_code,
                    "outcome_index": idx,
                    "incumbent_skill": dict(incumbent),
                    "final_skill": final,
                    "first_token": {"kind": fk, "skill": fs},
                    "second_token": {"kind": sk, "skill": ss},
                    "policy_probability_dtype": dtype,
                    "raw_first_mass": raw_first,
                    "raw_second_mass": raw_second,
                    "raw_joint_mass": raw_joint,
                    "canonical_joint_probability": None,
                    "keep_marginal": {"agent_0": 0.5, "agent_1": 0.5},
                    "set_marginal": {
                        "agent_0": {s: 1.0 / 6.0 for s in SKILL_SET if s != INC0},
                        "agent_1": {s: 1.0 / 6.0 for s in SKILL_SET if s != INC1},
                    },
                    "five_step_reward": reward_value,
                    "slow_match_vector": [1, 1, 1, 1, 1],
                    "fast_match_vector": [1, 1, 1, 1, 1],
                    "task_optimal": idx == task_optimal_index,
                    "slow_coverage_failure": idx == slow_cov_fail_index,
                    "fast_coverage_failure": idx == fast_cov_fail_index,
                    "boundary_state_replay_ok": replay_ok,
                }
            )
            idx += 1

    raw_sum = sum(r["raw_joint_mass"] for r in rows)
    for r in rows:
        r["canonical_joint_probability"] = r["raw_joint_mass"] / raw_sum
    return rows


def make_anchor_matched_rows(
    seed: int,
    episode,
    check_index: int,
    occupancy_stratum: str,
    fresh_ckpt: str,
    trained_ckpt: str,
    fresh_d_r: float,
    trained_d_r: float,
    tv_present_fresh: bool = False,
    tv_present_trained: bool = False,
    dtype: str = "float32",
    replay_ok: bool = True,
) -> list[dict]:
    rows: list[dict] = []
    for policy_state, ckpt, d_r, tv_present in (
        (M.POLICY_STATE_FRESH, fresh_ckpt, fresh_d_r, tv_present_fresh),
        (M.POLICY_STATE_TRAINED, trained_ckpt, trained_d_r, tv_present_trained),
    ):
        for order_code, reward, concentrate in (
            (M.ORDER_CANONICAL, d_r, 0 if tv_present else None),
            (M.ORDER_REVERSED, 0.0, 1 if tv_present else None),
        ):
            rows.extend(
                make_matched_state_group(
                    seed, episode, check_index, policy_state, order_code, occupancy_stratum,
                    ckpt, reward, dtype=dtype, concentrate_outcome_index=concentrate, replay_ok=replay_ok,
                )
            )
    return rows


def build_population(
    seeds: list[int],
    episodes: int,
    fresh_d_r: float,
    trained_d_r: float,
    tv_present_fresh: bool = False,
    tv_present_trained: bool = False,
    trained_d_r_by_stratum: dict[str, float] | None = None,
) -> list[dict]:
    """Two noninitial checks per episode, alternating occupancy stratum, so
    both CANONICAL_OCCUPANCY and REVERSED_OCCUPANCY are always populated in
    equal proportion."""
    checks = [1, 2]
    strata = {1: M.STRATUM_CANONICAL_OCCUPANCY, 2: M.STRATUM_REVERSED_OCCUPANCY}
    rows: list[dict] = []
    for seed in seeds:
        fresh_ckpt = f"fresh-ctor-seed{seed}"
        trained_ckpt = f"ckpt-seed{seed}"
        for episode in range(episodes):
            for check_index in checks:
                stratum = strata[check_index]
                t_d_r = trained_d_r if trained_d_r_by_stratum is None else trained_d_r_by_stratum[stratum]
                rows.extend(
                    make_anchor_matched_rows(
                        seed, episode, check_index, stratum, fresh_ckpt, trained_ckpt,
                        fresh_d_r, t_d_r, tv_present_fresh, tv_present_trained,
                    )
                )
    return rows


def make_propagation_row(seed, episode, order_code, policy_state, checkpoint_hash, slow_v, fast_v, replay_ok=True):
    return {
        "contract_id": M.VK0_CONTRACT_ID,
        "vk0c_schema_version": M.VK0C_SCHEMA_VERSION,
        "training_seed": seed,
        "episode_id": episode,
        "order_code": order_code,
        "policy_state": policy_state,
        "checkpoint_hash": checkpoint_hash,
        "occupancy_summary": [{"state_key": "s0", "occupancy_probability": 1.0}],
        "expected_slow_match_vector": [slow_v] * 5,
        "expected_fast_match_vector": [fast_v] * 5,
        "expected_external_reward_vector": [0.0] * 5,
        "expected_episode_return": 0.0,
        "expected_keep_rate": {"agent_0": 0.5, "agent_1": 0.5},
        "expected_set_rate": {"agent_0": 0.5, "agent_1": 0.5},
        "expected_renewal_rate": {"agent_0": 0.1, "agent_1": 0.1},
        "lifetime_mass": {"agent_0": {"5": 1.0}, "agent_1": {"5": 1.0}},
        "replay_conformance": {"factual_row_reproduction": replay_ok},
    }


def build_propagation_population(seeds, episodes, canonical_slow, canonical_fast, reversed_slow, reversed_fast, replay_ok=True):
    rows = []
    for seed in seeds:
        ckpt = f"ckpt-seed{seed}"
        for episode in range(episodes):
            rows.append(make_propagation_row(seed, episode, M.ORDER_CANONICAL, M.POLICY_STATE_TRAINED, ckpt, canonical_slow, canonical_fast, replay_ok))
            rows.append(make_propagation_row(seed, episode, M.ORDER_REVERSED, M.POLICY_STATE_TRAINED, ckpt, reversed_slow, reversed_fast, replay_ok))
    return rows


def make_manifest(bindings_ok: bool = True, checkpoint_hash_fn=None) -> dict:
    all_seeds = list(range(1, 7))
    if checkpoint_hash_fn is None:
        checkpoint_hash_fn = lambda s: f"ckpt-seed{s}"
    seeds = {
        str(s): {
            "checkpoint_hash": checkpoint_hash_fn(s),
            "resolved_config_hash": f"cfg-seed{s}",
            "exposure_authorization": {"artifact_sha256": "b" * 64},
        }
        for s in all_seeds
    }
    manifest = {
        "contract_id": M.VK0_CONTRACT_ID,
        "vk0c_schema_version": M.VK0C_SCHEMA_VERSION,
        "vk0b_trace_schema_version": M.VK0B_TRACE_SCHEMA_VERSION,
        "check_row_count": M.FROZEN_CHECK_ROW_COUNT,
        "deduplicated_anchor_count": M.FROZEN_ANCHOR_COUNT,
        "episodes_per_seed": M.FROZEN_EPISODES_PER_SEED,
        "noninitial_checks": M.FROZEN_NONINITIAL_CHECKS,
        "seeds": seeds,
    }
    if bindings_ok:
        manifest["vk0b_source_bindings"] = {f: "a" * 64 for f in M.VK0B_SOURCE_BINDING_FIELDS}
    return manifest


def make_positive_control_row(seed, episode, check_index, forced_pair, mismatched=False):
    row = {
        "contract_id": M.VK0_CONTRACT_ID,
        "vk0c_schema_version": M.VK0C_SCHEMA_VERSION,
        "control_type": M.CONTROL_TYPE_POSITIVE,
        "training_seed": seed,
        "episode_id": episode,
        "check_index": check_index,
        "forced_assignment": forced_pair,
    }
    for prefix in (M.ORDER_CANONICAL, M.ORDER_REVERSED):
        row[f"{prefix}_realized_skill"] = dict(forced_pair)
        row[f"{prefix}_primitive_actions"] = [0, 1, 2, 3, 4]
        row[f"{prefix}_reward_vector"] = [1.0, 1.0, 1.0, 1.0, 1.0]
        row[f"{prefix}_slow_match_vector"] = [1, 1, 1, 1, 1]
        row[f"{prefix}_fast_match_vector"] = [1, 1, 1, 1, 1]
        row[f"{prefix}_post_window_state_hash"] = "hash-common"
    if mismatched:
        row[f"{M.ORDER_REVERSED}_reward_vector"] = [9.0, 9.0, 9.0, 9.0, 9.0]
    return row


def make_fresh_init_row(seed, hash1="p1", hash2="p1"):
    return {
        "contract_id": M.VK0_CONTRACT_ID,
        "vk0c_schema_version": M.VK0C_SCHEMA_VERSION,
        "control_type": M.CONTROL_TYPE_FRESH_INIT,
        "training_seed": seed,
        "construction_1_param_hash": hash1,
        "construction_2_param_hash": hash2,
    }


def write_files(tmp_path: Path, manifest, matched_rows, propagation_rows, control_rows, prefix="") -> dict[str, Path]:
    manifest_path = tmp_path / f"{prefix}manifest.json"
    matched_path = tmp_path / f"{prefix}matched.jsonl"
    propagation_path = tmp_path / f"{prefix}propagation.jsonl"
    control_path = tmp_path / f"{prefix}control.jsonl"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    for path, rows in ((matched_path, matched_rows), (propagation_path, propagation_rows), (control_path, control_rows)):
        text = "".join(json.dumps(r) + "\n" for r in rows)
        path.write_text(text, encoding="utf-8")
    return {
        "manifest": manifest_path,
        "matched_state": matched_path,
        "propagation": propagation_path,
        "control": control_path,
    }


def run(tmp_path, matched_rows, propagation_rows=(), control_rows=(), manifest=None, prefix=""):
    manifest = manifest if manifest is not None else make_manifest()
    paths = write_files(tmp_path, manifest, matched_rows, list(propagation_rows), list(control_rows), prefix=prefix)
    return M.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])


# =============================================================================
# Bootstrap seed identity with V-K0B
# =============================================================================


def test_bootstrap_seed_matches_vk0_analyzer():
    vk0_spec = importlib.util.spec_from_file_location("analyze_vk0_result", _ROOT / "scripts" / "analyze_vk0_result.py")
    assert vk0_spec is not None and vk0_spec.loader is not None
    vk0 = importlib.util.module_from_spec(vk0_spec)
    vk0_spec.loader.exec_module(vk0)
    assert M.BOOTSTRAP_SEED == vk0.BOOTSTRAP_SEED


# =============================================================================
# Precedence-1: authorization
# =============================================================================


def test_authorization_missing_bindings_produces_invalidity(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0)
    manifest = make_manifest(bindings_ok=False)
    result = run(tmp_path, rows, manifest=manifest)
    assert result["result"]["code"] == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert any("MANIFEST_SOURCE_BINDINGS_MISSING_OR_MISMATCHED" in r for r in result["result"]["reasons"])


def test_authorization_row_checkpoint_hash_mismatch_produces_invalidity(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0)
    # Tamper one trained row's checkpoint_hash so it no longer matches the
    # manifest's recorded hash for that seed.
    for r in rows:
        if r["policy_state"] == M.POLICY_STATE_TRAINED and r["training_seed"] == 1:
            r["checkpoint_hash"] = "tampered-hash"
    result = run(tmp_path, rows)
    assert result["result"]["code"] == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert any("ROW_CHECKPOINT_HASH_MISMATCH_WITH_MANIFEST" in r for r in result["result"]["reasons"])


def test_valid_population_is_not_invalid(tmp_path):
    """Sanity anchor for every other test: the baseline population,
    unperturbed, must NOT trigger precedence-1 invalidity."""
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0)
    result = run(tmp_path, rows)
    assert result["result"]["code"] != "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"


# =============================================================================
# Precedence-1: mass tolerance (A-VC-7)
# =============================================================================


def test_mass_tolerance_violation_produces_invalidity(tmp_path):
    rows = build_population([1], 1, fresh_d_r=0.0, trained_d_r=0.0)
    # Perturb one outcome's raw_first_mass/raw_second_mass/raw_joint_mass so
    # the group's raw_joint_mass sum drifts far outside
    # 32*eps(float32) (~3.8e-6) of 1.0 -- large enough to be a genuine
    # violation rather than float noise.
    target = next(
        r for r in rows
        if r["training_seed"] == 1 and r["policy_state"] == M.POLICY_STATE_TRAINED
        and r["order_code"] == M.ORDER_CANONICAL and r["outcome_index"] == 0
    )
    target["raw_first_mass"] = 0.35
    target["raw_second_mass"] = 0.35
    target["raw_joint_mass"] = 0.1225
    # canonical_joint_probability left as originally normalized -- the
    # invalidity must fire on the RAW mass sum, independent of reporting.
    result = run(tmp_path, rows)
    assert result["result"]["code"] == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert any("RAW_JOINT_MASS_NOT_NORMALIZED" in r for r in result["result"]["reasons"])


# =============================================================================
# Factor A -- structural order sensitivity
# =============================================================================


def test_factor_a_present_and_promoted_at_the_materiality_boundary(tmp_path):
    """Fresh D_R held exactly at 0.5 (the frozen boundary): the strict
    `upper_95 < MATERIALITY` equivalence test fails at exact equality, so
    promotion fires."""
    rows = build_population([1, 2], 2, fresh_d_r=0.5, trained_d_r=0.0, tv_present_fresh=True)
    result = run(tmp_path, rows)
    factor_a = result["factor_a"]
    assert factor_a["fresh_D_R_pooled"]["lower_95"] == pytest.approx(0.5)
    assert factor_a["fresh_D_R_pooled"]["upper_95"] == pytest.approx(0.5)
    assert factor_a["present"] is True
    assert factor_a["fresh_D_R_equivalent_within_materiality"] is False
    assert factor_a["promoted"] is True


def test_factor_a_present_but_not_promoted_when_fresh_d_r_equivalent(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0, tv_present_fresh=True)
    result = run(tmp_path, rows)
    factor_a = result["factor_a"]
    assert factor_a["present"] is True
    assert factor_a["fresh_D_R_equivalent_within_materiality"] is True
    assert factor_a["promoted"] is False


def test_factor_a_absent_when_fresh_distributions_identical(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.5, trained_d_r=0.0, tv_present_fresh=False)
    result = run(tmp_path, rows)
    factor_a = result["factor_a"]
    assert factor_a["present"] is False
    assert factor_a["promoted"] is False


# =============================================================================
# Factor B -- learned order specialization
# =============================================================================


def test_factor_b_identified_when_all_three_conditions_hold(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.6)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=1.0, canonical_fast=1.0, reversed_slow=0.0, reversed_fast=0.0)
    result = run(tmp_path, rows, propagation_rows=propagation)
    factor_b = result["factor_b"]
    assert factor_b["fresh_D_R_equivalent_within_materiality"] is True
    assert factor_b["trained_D_R_lcb95_above_materiality"] is True
    assert factor_b["propagation_split_reproduced"] is True
    assert factor_b["identified"] is True


def test_factor_b_not_identified_when_trained_lcb_sits_at_the_boundary(tmp_path):
    """Trained D_R held exactly at 0.5: LCB95==0.5 fails the strict `>0.5`
    amplification test, so Factor B must not fire even though the other two
    conditions hold."""
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.5)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=1.0, canonical_fast=1.0, reversed_slow=0.0, reversed_fast=0.0)
    result = run(tmp_path, rows, propagation_rows=propagation)
    factor_b = result["factor_b"]
    assert result["matched_state_quantities"]["D_R_trained"]["pooled"]["lower_95"] == pytest.approx(0.5)
    assert factor_b["trained_D_R_lcb95_above_materiality"] is False
    assert factor_b["identified"] is False


def test_factor_b_not_identified_when_propagation_split_missing(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.6)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=0.9, canonical_fast=0.9, reversed_slow=0.9, reversed_fast=0.9)
    result = run(tmp_path, rows, propagation_rows=propagation)
    factor_b = result["factor_b"]
    assert factor_b["fresh_D_R_equivalent_within_materiality"] is True
    assert factor_b["trained_D_R_lcb95_above_materiality"] is True
    assert factor_b["propagation_split_reproduced"] is False
    assert factor_b["identified"] is False


# =============================================================================
# Factor C -- training amplification
# =============================================================================


def test_factor_c_not_amplified_at_the_a_r_boundary(tmp_path):
    """A_R = D_R^(T) - D_R^(0) held exactly at 0.5: LCB95==0.5 fails the
    strict `>0.5` amplification test."""
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.5, tv_present_fresh=True)
    result = run(tmp_path, rows)
    factor_c = result["factor_c"]
    assert result["matched_state_quantities"]["A_R"]["pooled"]["lower_95"] == pytest.approx(0.5)
    assert factor_c["requires_factor_a_present"] is True
    assert factor_c["a_r_pooled_lcb95_above_materiality"] is False
    assert factor_c["identified"] is False


def test_factor_c_amplified_above_the_boundary(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.6, tv_present_fresh=True)
    result = run(tmp_path, rows)
    factor_c = result["factor_c"]
    assert factor_c["a_r_pooled_lcb95_above_materiality"] is True
    assert factor_c["identified"] is True


def test_factor_c_never_fires_without_factor_a_present(tmp_path):
    """Same amplified A_R, but fresh distributions never differ anywhere:
    Factor C is gated on Factor A's base presence and must not fire."""
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.6, tv_present_fresh=False)
    result = run(tmp_path, rows)
    assert result["factor_a"]["present"] is False
    factor_c = result["factor_c"]
    assert factor_c["a_r_pooled_lcb95_above_materiality"] is True
    assert factor_c["identified"] is False


# =============================================================================
# Factor D -- occupancy mediation (A-VC-9 stratum-safety)
# =============================================================================


def test_factor_d_identified_when_pooled_and_both_strata_equivalent_and_split_reproduced(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=1.0, canonical_fast=1.0, reversed_slow=0.0, reversed_fast=0.0)
    result = run(tmp_path, rows, propagation_rows=propagation)
    factor_d = result["factor_d"]
    assert factor_d["pooled_equivalent"] is True
    assert factor_d["canonical_stratum_equivalent"] is True
    assert factor_d["reversed_stratum_equivalent"] is True
    assert factor_d["propagation_split_reproduced"] is True
    assert factor_d["identified"] is True
    assert factor_d["stratum_direct_effects_diverge"] is False
    assert "SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED" in result["result"]["labels"]


def test_factor_d_unresolved_when_pooled_cancellation_hides_opposite_stratum_effects(tmp_path):
    """A-VC-9: trained D_R is +0.6 in CANONICAL_OCCUPANCY and -0.6 in
    REVERSED_OCCUPANCY -- opposite, material, and each individually outside
    the +-0.5 equivalence region -- yet the equal-weighted pooled average
    cancels to ~0.0, which is trivially equivalent. The pure
    occupancy-mediation label must NOT fire on the pooled view alone; the
    divergence must be recorded, and the overall record must fall through
    to the general unresolved residual rather than any identified factor."""
    rows = build_population(
        [1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0,
        trained_d_r_by_stratum={M.STRATUM_CANONICAL_OCCUPANCY: 0.6, M.STRATUM_REVERSED_OCCUPANCY: -0.6},
    )
    propagation = build_propagation_population([1, 2], 2, canonical_slow=1.0, canonical_fast=1.0, reversed_slow=0.0, reversed_fast=0.0)
    result = run(tmp_path, rows, propagation_rows=propagation)
    quantities = result["matched_state_quantities"]["D_R_trained"]
    assert quantities["pooled"]["point"] == pytest.approx(0.0)
    assert quantities[M.STRATUM_CANONICAL_OCCUPANCY]["point"] == pytest.approx(0.6)
    assert quantities[M.STRATUM_REVERSED_OCCUPANCY]["point"] == pytest.approx(-0.6)

    factor_d = result["factor_d"]
    assert factor_d["pooled_equivalent"] is True
    assert factor_d["canonical_stratum_equivalent"] is False
    assert factor_d["reversed_stratum_equivalent"] is False
    assert factor_d["stratum_direct_effects_diverge"] is True
    assert factor_d["identified"] is False
    assert "SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED" not in result["result"]["labels"]
    assert result["residual"]["code"] == "ORDER_TRANSPORT_LOCALIZATION_UNRESOLVED"


# =============================================================================
# Residual: Factor E / unresolved
# =============================================================================


def test_residual_gap_not_explained_when_distributions_agree_but_split_missing(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0, tv_present_fresh=False)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=0.9, canonical_fast=0.9, reversed_slow=0.9, reversed_fast=0.9)
    result = run(tmp_path, rows, propagation_rows=propagation)
    assert result["factor_a"]["present"] is False
    assert result["factor_b"]["identified"] is False
    assert result["factor_c"]["identified"] is False
    assert result["factor_d"]["identified"] is False
    assert result["residual"]["code"] == "V_K0B_ORDER_GAP_NOT_EXPLAINED_BY_HIGH_POLICY_FACTORIZATION"
    assert "V_K0B_ORDER_GAP_NOT_EXPLAINED_BY_HIGH_POLICY_FACTORIZATION" in result["result"]["labels"]


def test_residual_unresolved_when_fresh_structural_sensitivity_blocks_the_gap_branch(tmp_path):
    """Fresh distributions DO differ (Factor A base present, but not
    promoted since D_R^(0) is equivalent), and nothing else identifies --
    the E-branch's 'distributions agree' precondition requires Factor A to
    be entirely absent, so this must fall to the general unresolved code,
    not the gap-not-explained code."""
    rows = build_population([1, 2], 2, fresh_d_r=0.0, trained_d_r=0.0, tv_present_fresh=True)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=0.9, canonical_fast=0.9, reversed_slow=0.9, reversed_fast=0.9)
    result = run(tmp_path, rows, propagation_rows=propagation)
    assert result["factor_a"]["present"] is True
    assert result["factor_a"]["promoted"] is False
    assert result["residual"]["code"] == "ORDER_TRANSPORT_LOCALIZATION_UNRESOLVED"


# =============================================================================
# A-VC-8: pooled + per-stratum tables present for every listed quantity
# =============================================================================


def test_pooled_and_stratified_tables_present_for_every_required_quantity(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.1, trained_d_r=0.2)
    result = run(tmp_path, rows)
    quantities = result["matched_state_quantities"]
    for key in ("TV_fresh", "TV_trained", "D_R_fresh", "D_R_trained", "A_R"):
        assert set(quantities[key].keys()) == set(M.REQUIRED_STRATA), key
        for stratum in M.REQUIRED_STRATA:
            assert set(quantities[key][stratum].keys()) == {"point", "lower_95", "upper_95", "n"}
    for key in ("optimal_assignment_mass", "slow_coverage_failure_mass", "fast_coverage_failure_mass"):
        assert set(quantities[key].keys()) == {M.POLICY_STATE_FRESH, M.POLICY_STATE_TRAINED}, key
        for policy_state in (M.POLICY_STATE_FRESH, M.POLICY_STATE_TRAINED):
            assert set(quantities[key][policy_state].keys()) == set(M.ORDER_CODES_TUPLE)
            for order_code in M.ORDER_CODES_TUPLE:
                assert set(quantities[key][policy_state][order_code].keys()) == set(M.REQUIRED_STRATA)


# =============================================================================
# Controls
# =============================================================================


def test_positive_control_failure_produces_invalidity(tmp_path):
    rows = build_population([1], 1, fresh_d_r=0.0, trained_d_r=0.0)
    control = [make_positive_control_row(1, 0, 1, {"agent_0": "A", "agent_1": "B"}, mismatched=True)]
    result = run(tmp_path, rows, control_rows=control)
    assert result["result"]["code"] == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert any("ORDER_CONJUGACY_POSITIVE_CONTROL_FAILED" in r for r in result["result"]["reasons"])


def test_positive_control_passing_does_not_trigger_invalidity(tmp_path):
    rows = build_population([1], 1, fresh_d_r=0.0, trained_d_r=0.0)
    control = [make_positive_control_row(1, 0, 1, {"agent_0": "A", "agent_1": "B"}, mismatched=False)]
    result = run(tmp_path, rows, control_rows=control)
    assert result["result"]["code"] != "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"


def test_fresh_init_nondeterminism_produces_invalidity(tmp_path):
    rows = build_population([1], 1, fresh_d_r=0.0, trained_d_r=0.0)
    control = [make_fresh_init_row(1, hash1="p1", hash2="p2")]
    result = run(tmp_path, rows, control_rows=control)
    assert result["result"]["code"] == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert any("FRESH_INITIALIZATION_NONDETERMINISTIC" in r for r in result["result"]["reasons"])


# =============================================================================
# Determinism and recomputability
# =============================================================================


def test_bootstrap_determinism_two_runs_identical_summary(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.1, trained_d_r=0.6)
    manifest = make_manifest()
    paths = write_files(tmp_path, manifest, rows, [], [])
    result_a = M.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])
    result_b = M.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])
    assert json.dumps(result_a, sort_keys=True, default=str) == json.dumps(result_b, sort_keys=True, default=str)


def test_summary_recomputable_delete_and_rerun_byte_identical(tmp_path):
    rows = build_population([1, 2], 2, fresh_d_r=0.1, trained_d_r=0.6)
    propagation = build_propagation_population([1, 2], 2, canonical_slow=0.9, canonical_fast=0.9, reversed_slow=0.9, reversed_fast=0.9)
    manifest = make_manifest()
    paths = write_files(tmp_path, manifest, rows, propagation, [])
    out_path = tmp_path / "summary.json"

    def run_cli():
        completed = subprocess.run(
            [
                sys.executable, str(_SCRIPT_PATH),
                "--manifest", str(paths["manifest"]),
                "--matched-state", str(paths["matched_state"]),
                "--propagation", str(paths["propagation"]),
                "--control", str(paths["control"]),
                "--out", str(out_path),
            ],
            capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stderr

    run_cli()
    first_bytes = out_path.read_bytes()
    out_path.unlink()
    assert not out_path.exists()
    run_cli()
    second_bytes = out_path.read_bytes()
    assert first_bytes == second_bytes


def test_cli_refuses_and_writes_nothing_on_schema_violation(tmp_path):
    rows = build_population([1], 1, fresh_d_r=0.0, trained_d_r=0.0)
    del rows[0]["final_skill"]
    manifest = make_manifest()
    paths = write_files(tmp_path, manifest, rows, [], [])
    out_path = tmp_path / "summary.json"
    completed = subprocess.run(
        [
            sys.executable, str(_SCRIPT_PATH),
            "--manifest", str(paths["manifest"]),
            "--matched-state", str(paths["matched_state"]),
            "--propagation", str(paths["propagation"]),
            "--control", str(paths["control"]),
            "--out", str(out_path),
        ],
        capture_output=True, text=True,
    )
    assert completed.returncode != 0
    assert not out_path.exists()


# =============================================================================
# Paired negative: a mutated equivalence predicate must flip a boundary fixture
# =============================================================================


def test_paired_negative_loosening_equivalence_upper_bound_flips_factor_a_promotion(tmp_path):
    """Mutate a TEMPORARY copy of the analyzer, replacing the strict
    `stats["upper_95"] < MATERIALITY` half of `_equivalent_within_materiality`
    with `<=`, and show that on the Factor-A exact-boundary fixture
    (fresh D_R held at exactly +0.5, so upper_95 == 0.5) the mutant now
    calls the fresh distribution 'equivalent' and Factor A promotion no
    longer fires -- diverging from the production module, which still
    promotes. This proves the boundary assertions in this suite are real
    discriminators, not tautologies."""
    rows = build_population([1, 2], 2, fresh_d_r=0.5, trained_d_r=0.0, tv_present_fresh=True)
    manifest = make_manifest()
    paths = write_files(tmp_path, manifest, rows, [], [])

    production_result = M.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])
    assert production_result["factor_a"]["present"] is True
    assert production_result["factor_a"]["fresh_D_R_equivalent_within_materiality"] is False
    assert production_result["factor_a"]["promoted"] is True

    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    target = 'return stats["lower_95"] > -MATERIALITY and stats["upper_95"] < MATERIALITY'
    assert source.count(target) == 1, "expected exactly one equivalence predicate site to mutate"
    mutated_source = source.replace(
        target, 'return stats["lower_95"] > -MATERIALITY and stats["upper_95"] <= MATERIALITY'
    )
    assert mutated_source != source

    mutant_path = tmp_path / "analyze_vk0c_result_mutant.py"
    mutant_path.write_text(mutated_source, encoding="utf-8")
    mutant_spec = importlib.util.spec_from_file_location("analyze_vk0c_result_mutant", mutant_path)
    assert mutant_spec is not None and mutant_spec.loader is not None
    mutant = importlib.util.module_from_spec(mutant_spec)
    mutant_spec.loader.exec_module(mutant)

    mutant_result = mutant.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])
    assert mutant_result["factor_a"]["fresh_D_R_equivalent_within_materiality"] is True
    assert mutant_result["factor_a"]["promoted"] is False, "mutation must flip the boundary fixture (caught red)"

    # Original file on disk is untouched, and the production module
    # (already loaded, unmutated) still reports the original verdict.
    assert _SCRIPT_PATH.read_text(encoding="utf-8") == source
    rerun = M.run_analysis(paths["manifest"], paths["matched_state"], paths["propagation"], paths["control"])
    assert rerun["factor_a"]["promoted"] is True
