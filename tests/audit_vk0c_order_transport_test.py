"""Calibration of the V-K0C order-transport driver.

`docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md` (VC-D1..VC-D6,
A-VC-1..A-VC-11, clarifications C-1..C-3).

These are not specifications of behaviour. Each one exists because failing
it would mean the number V-K0C reports is wrong:

* the input manifest binds artifacts that were not tampered with;
* the anchor inventory is fail-closed rather than row-selecting;
* the enumeration is exactly the 16-outcome legal support, the incumbent
  carries exactly zero SET mass, and the dtype-derived mass tolerance
  accepts at the boundary and rejects just past it;
* A-VC-4's pure transition equals what the real agent and env actually do;
* the propagation is a memoized occupancy pushforward over the reachable
  finite state space rather than a `16 ** 8` tree walk;
* two same-seed constructions are bit-identical, so `D_R^(0)` is a property
  of the seed rather than of when the process happened to run.

Every expected value here comes from an independent source: the frozen
ledger's own constants, a literal worked by hand, or the stored V-K0B
artifacts -- never from re-running the code under test in the assertion.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for _p in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import analyze_vk0c_result as analyzer  # noqa: E402
import audit_vk0b_r30_access as vk0b  # noqa: E402
import audit_vk0c_order_transport as vk0c  # noqa: E402
from ha_ctse_process.r30_fixed_clock import INVALID_SKILL, KEEP_TOKEN, SET_TOKEN  # noqa: E402

torch.set_num_threads(1)

VK0B_EVAL_DIR = PROJECT_ROOT / "logs" / "vk0b_r2_eval"
VK0A_PANEL = PROJECT_ROOT / "logs" / "vk0a_formal" / "source_oracle_panel.json"
VK0A_SIDECAR = PROJECT_ROOT / "logs" / "vk0a_formal" / "source_oracle_panel.sha256"
CHECKPOINT_BUNDLE = PROJECT_ROOT / "logs" / "vk0b_r2" / "2026080101"
CONFIG_MODULE = "config_d7_2b_toy_learned_keep"

_HAVE_ARTIFACTS = (
    (VK0B_EVAL_DIR / vk0b.VK0B_TRACE_FILENAME).is_file()
    and VK0A_PANEL.is_file()
    and VK0A_SIDECAR.is_file()
    and (CHECKPOINT_BUNDLE / "vk0b_preflight_manifest.json").is_file()
)
requires_artifacts = pytest.mark.skipif(
    not _HAVE_ARTIFACTS, reason="the V-K0B r2 evaluation artifacts are not present in this tree"
)


# =============================================================================
# Shared fixtures
# =============================================================================


@pytest.fixture(scope="module")
def config():
    import importlib

    return importlib.import_module(CONFIG_MODULE).Config()


@pytest.fixture(scope="module")
def source():
    return vk0c.load_source_inputs(VK0B_EVAL_DIR, VK0A_PANEL, VK0A_SIDECAR)


@pytest.fixture(scope="module")
def anchors(source):
    return vk0c.build_anchor_inventory(source.trace_rows)


@pytest.fixture(scope="module")
def trained_agent(config):
    entry = vk0b.resolve_checkpoint_entry(str(CHECKPOINT_BUNDLE))
    return vk0b.build_agent(config, checkpoint_path=entry["checkpoint_path"])


@pytest.fixture(scope="module")
def kernel(config):
    import importlib

    return vk0c.WindowKernel(importlib.import_module(CONFIG_MODULE).Config())


def _focal_row_pair(trace_rows, seed=2026080101, evaluation_seed=0, check_index=1):
    rows = [
        json.loads(json.dumps(r))
        for r in trace_rows
        if int(r["training_seed"]) == seed
        and int(r["evaluation_seed"]) == evaluation_seed
        and int(r["check_index"]) == check_index
    ]
    assert len(rows) == 2
    return rows


# =============================================================================
# (1) Input manifest binding -- A-VC-3
# =============================================================================


@requires_artifacts
def test_untampered_source_artifacts_bind_and_authorize(source):
    """The positive half of the tamper test. Without it, the tamper test
    below could be passing because of some unrelated refusal."""
    assert set(source.source_bindings) == set(analyzer.VK0B_SOURCE_BINDING_FIELDS)
    for name, digest in source.source_bindings.items():
        assert analyzer._is_sha256_hex(digest), name
    # The panel's recomputed nine-field authorization tuple is the one the
    # V-K0B evaluation recorded when it ran (checked inside
    # load_source_inputs; asserted again here so a silent relaxation shows).
    assert source.vk0b_manifest["authorization"] == source.vk0a_authorization
    assert source.vk0b_manifest["replay_mismatch"] is False


@requires_artifacts
def test_tampered_panel_artifact_fires_invalidity(tmp_path):
    """A-VC-3: the manifest binds by SHA-256, so a single flipped byte in a
    bound artifact must refuse, named -- never be absorbed."""
    panel_copy = tmp_path / VK0A_PANEL.name
    sidecar_copy = tmp_path / VK0A_SIDECAR.name
    shutil.copy2(VK0A_PANEL, panel_copy)
    shutil.copy2(VK0A_SIDECAR, sidecar_copy)

    # Control: the untouched copy still authorizes.
    vk0c.load_source_inputs(VK0B_EVAL_DIR, panel_copy, sidecar_copy)

    raw = bytearray(panel_copy.read_bytes())
    # Flip one byte inside the JSON body (not the first character, which
    # would make the file unparseable and refuse for the wrong reason).
    raw[len(raw) // 2] ^= 0x01
    panel_copy.write_bytes(bytes(raw))

    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.load_source_inputs(VK0B_EVAL_DIR, panel_copy, sidecar_copy)
    assert excinfo.value.reason_code == vk0c.REASON_SOURCE_ARTIFACT_HASH_MISMATCH
    assert vk0c.run_verdict_for([str(excinfo.value)]) == vk0c.INVALID_VERDICT


@requires_artifacts
def test_missing_source_artifact_refuses(tmp_path):
    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.load_source_inputs(tmp_path, VK0A_PANEL, VK0A_SIDECAR)
    assert excinfo.value.reason_code == vk0c.REASON_SOURCE_ARTIFACT_MISSING


# =============================================================================
# (2) Anchor gate -- A-VC-3
# =============================================================================


@requires_artifacts
def test_anchor_field_partition_covers_the_real_row_schema(source):
    vk0c.assert_anchor_field_coverage(source.trace_rows[0])

    # Planted violation: a field the partition does not name must be caught,
    # not silently excluded from the shared-agreement comparison.
    drifted = dict(source.trace_rows[0])
    drifted["a_new_upstream_field"] = 1
    with pytest.raises(vk0c.Vk0cAssertionError):
        vk0c.assert_anchor_field_coverage(drifted)


@requires_artifacts
def test_well_formed_anchor_pair_reconstructs_one_ordered_roster(source):
    rows = _focal_row_pair(source.trace_rows)
    built = vk0c.build_anchor_inventory(rows)
    assert len(built) == 1
    anchor = built[0]
    # The roster is assembled from the two focal rows independently -- focal
    # 0 supplies agent 0's incumbent/age, focal 1 supplies agent 1's.
    by_focal = {int(r["focal_agent"]): r for r in rows}
    assert anchor.incumbent == (int(by_focal[0]["current_skill"]), int(by_focal[1]["current_skill"]))
    assert anchor.skill_age == (int(by_focal[0]["skill_age"]), int(by_focal[1]["skill_age"]))
    assert anchor.occupancy_stratum == vk0c.STRATUM_CANONICAL_OCCUPANCY


@requires_artifacts
def test_missing_focal_row_fires_anchor_inventory_inconsistent(source):
    rows = _focal_row_pair(source.trace_rows)
    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.build_anchor_inventory(rows[:1])
    assert excinfo.value.reason_code == vk0c.REASON_ANCHOR_INVENTORY_INCONSISTENT


@requires_artifacts
def test_third_duplicate_row_fires_anchor_inventory_inconsistent(source):
    rows = _focal_row_pair(source.trace_rows)
    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.build_anchor_inventory(rows + [json.loads(json.dumps(rows[0]))])
    assert excinfo.value.reason_code == vk0c.REASON_ANCHOR_INVENTORY_INCONSISTENT


@requires_artifacts
@pytest.mark.parametrize(
    "field_name,new_value",
    [
        ("pre_check_fingerprint", "0" * 64),
        ("checkpoint_hash", "f" * 64),
        ("primitive_step", 999),
        ("active_mask", [True, False]),
        ("natural_external_reward_vector", [0.0, 0.0, 0.0, 0.0, 0.0]),
        ("slow_match_vector", [0, 0, 0, 0, 0]),
        ("current_targets", {"slow": [0.0, 0.0], "fast": [0.0, 0.0]}),
    ],
)
def test_shared_field_disagreement_fires_anchor_inventory_inconsistent(source, field_name, new_value):
    """One planted disagreement per shared field family. The gate must fire
    on the DISAGREEMENT -- not resolve it by taking one row's value."""
    rows = _focal_row_pair(source.trace_rows)
    assert rows[1][field_name] != new_value, "the planted value must actually differ"
    rows[1][field_name] = new_value
    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.build_anchor_inventory(rows)
    assert excinfo.value.reason_code == vk0c.REASON_ANCHOR_INVENTORY_INCONSISTENT
    assert field_name in str(excinfo.value)


@requires_artifacts
def test_two_rows_for_the_same_focal_agent_fires_anchor_inventory_inconsistent(source):
    """Two rows that agree on every SHARED field but name the same focal
    agent twice do not reconstruct an ordered roster. The count check alone
    would pass this fixture, so this pins the roster check specifically."""
    rows = _focal_row_pair(source.trace_rows)
    rows[1]["focal_agent"] = rows[0]["focal_agent"]
    with pytest.raises(vk0c.Vk0cRefusalError) as excinfo:
        vk0c.build_anchor_inventory(rows)
    assert excinfo.value.reason_code == vk0c.REASON_ANCHOR_INVENTORY_INCONSISTENT
    assert "ordered roster" in str(excinfo.value)


@requires_artifacts
def test_full_anchor_population_matches_the_frozen_a_vc_3_shape(anchors):
    """The frozen A-VC-3 numbers, checked against the real artifacts rather
    than recomputed from them."""
    assert len(anchors) == 2688
    assert sorted({a.training_seed for a in anchors}) == [
        2026080101, 2026080102, 2026080103, 2026080104, 2026080105, 2026080106
    ]
    assert sorted({a.check_index for a in anchors}) == [1, 2, 3, 4, 5, 6, 7]
    for seed in {a.training_seed for a in anchors}:
        assert len({a.evaluation_index for a in anchors if a.training_seed == seed}) == 64


# =============================================================================
# (3) Anchor restoration -- VC-D2 (the watched paired negative)
# =============================================================================


@requires_artifacts
def test_anchor_restoration_byte_verifies_and_a_corrupted_fingerprint_fails_closed(
    trained_agent, config, anchors
):
    """VC-D2: from-reset natural replay must reproduce the stored
    `pre_check_fingerprint` exactly; a single corrupted hex digit must fail
    closed rather than be tolerated or drop the anchor."""
    anchor = next(a for a in anchors if a.training_seed == 2026080101 and a.check_index == 4)

    env, restored = vk0c.restore_anchor(agent=trained_agent, config=config, anchor=anchor)
    env.close()
    assert restored.fingerprint_match is True
    assert restored.incumbent == anchor.incumbent
    assert restored.skill_age == anchor.skill_age
    assert restored.primitive_step == anchor.primitive_step

    original = anchor.pre_check_fingerprint
    flipped = ("1" if original[0] != "1" else "2") + original[1:]
    corrupted = dataclasses.replace(anchor, pre_check_fingerprint=flipped)
    env, restored_bad = vk0c.restore_anchor(agent=trained_agent, config=config, anchor=corrupted)
    env.close()
    assert restored_bad.fingerprint_match is False
    assert vk0c.run_verdict_for(
        [f"{vk0c.REASON_ANCHOR_RESTORATION_FINGERPRINT_MISMATCH}: anchor {corrupted.key}"]
    ) == vk0c.INVALID_VERDICT


# =============================================================================
# (4) Pure enumeration -- VC-D1 / A-VC-1 / A-VC-7
# =============================================================================


@requires_artifacts
def test_enumeration_is_exactly_sixteen_distinct_outcomes_under_both_orders(
    trained_agent, config, anchors
):
    anchor = next(a for a in anchors if a.training_seed == 2026080101 and a.check_index == 3)
    env, restored = vk0c.restore_anchor(agent=trained_agent, config=config, anchor=anchor)
    env.close()
    context = vk0c.policy_context(trained_agent, restored.obs, restored.state)

    coordinate_sets = []
    for order_code in vk0c.ORDER_CODES:
        outcomes = vk0c.enumerate_order(
            trained_agent, context, anchor.incumbent, anchor.skill_age, anchor.active_mask, order_code
        )
        assert len(outcomes) == 16
        coordinates = {o.final_skills for o in outcomes}
        assert len(coordinates) == 16
        coordinate_sets.append(coordinates)
        # A-VC-1: an active agent may KEEP or SET to any NON-incumbent skill,
        # so its own incumbent is never a SET target on either position.
        for outcome in outcomes:
            if outcome.first_kind == SET_TOKEN:
                assert outcome.first_skill != anchor.incumbent[outcome.first_agent]
            if outcome.second_kind == SET_TOKEN:
                assert outcome.second_skill != anchor.incumbent[outcome.second_agent]
    # A shared 16-coordinate space is what makes the two orders comparable.
    assert coordinate_sets[0] == coordinate_sets[1]


@requires_artifacts
def test_enumeration_consumes_no_rng(trained_agent, config, anchors):
    """VC-D1: the pure path samples nothing. If it did, the enumeration
    would silently reorder every subsequent replay's random stream."""
    anchor = next(a for a in anchors if a.training_seed == 2026080101 and a.check_index == 2)
    env, restored = vk0c.restore_anchor(agent=trained_agent, config=config, anchor=anchor)
    env.close()
    context = vk0c.policy_context(trained_agent, restored.obs, restored.state)
    before = torch.get_rng_state()
    vk0c.enumerate_order(
        trained_agent, context, anchor.incumbent, anchor.skill_age, anchor.active_mask, "canonical"
    )
    assert torch.equal(before, torch.get_rng_state())


def test_legal_token_support_matches_a_vc_1():
    """A-VC-1's support, against the literal the ledger states rather than
    against another call of the same function."""
    assert vk0c.legal_tokens(2, True) == [
        (KEEP_TOKEN, INVALID_SKILL), (SET_TOKEN, 0), (SET_TOKEN, 1), (SET_TOKEN, 3)
    ]
    assert vk0c.legal_tokens(INVALID_SKILL, False) == [
        (SET_TOKEN, 0), (SET_TOKEN, 1), (SET_TOKEN, 2), (SET_TOKEN, 3)
    ]


def test_incumbent_set_mass_must_be_exactly_zero():
    """A-VC-7's `same-label SET mass exactly zero` is an assertion, not a
    tolerance. A mass of one ULP on the incumbent is still a same-label
    renewal the policy cannot express, so it must go red."""
    clean = {
        "keep_mass": torch.tensor([0.25]),
        "set_mass": torch.tensor([[0.0, 0.25, 0.25, 0.25]]),
    }
    vk0c._assert_branch_semantics(clean, incumbent=0, active=True)

    leaking = {
        "keep_mass": torch.tensor([0.25]),
        "set_mass": torch.tensor([[float(np.nextafter(np.float32(0.0), np.float32(1.0))), 0.25, 0.25, 0.25]]),
    }
    with pytest.raises(vk0c.Vk0cAssertionError, match="same-label SET mass"):
        vk0c._assert_branch_semantics(leaking, incumbent=0, active=True)


def test_no_incumbent_branch_must_carry_zero_keep_mass():
    ok = {"keep_mass": torch.tensor([0.0]), "set_mass": torch.tensor([[0.25, 0.25, 0.25, 0.25]])}
    vk0c._assert_branch_semantics(ok, incumbent=INVALID_SKILL, active=False)

    bad = {"keep_mass": torch.tensor([1e-9]), "set_mass": torch.tensor([[0.25, 0.25, 0.25, 0.25]])}
    with pytest.raises(vk0c.Vk0cAssertionError, match="keep_mass"):
        vk0c._assert_branch_semantics(bad, incumbent=INVALID_SKILL, active=False)


def _outcomes_summing_to(total: float) -> list[vk0c.Outcome]:
    """Sixteen synthetic outcomes whose raw joint masses sum to exactly
    `total` in float64, with sixteen distinct final-skill coordinates."""
    share = total / 16.0
    outcomes = []
    for index in range(16):
        outcomes.append(
            vk0c.Outcome(
                first_agent=0, second_agent=1,
                first_kind=SET_TOKEN, first_skill=index // 4,
                second_kind=SET_TOKEN, second_skill=index % 4,
                raw_first_mass=1.0, raw_second_mass=share, raw_joint_mass=share,
                final_skills=(index // 4, index % 4),
            )
        )
    return outcomes


def test_mass_tolerance_is_thirty_two_eps_of_the_policy_dtype():
    """A-VC-7's rule, against the literal it states."""
    assert vk0c.mass_tolerance("float32") == 32.0 * float(np.finfo(np.float32).eps)
    assert vk0c.mass_tolerance("float64") == 32.0 * float(np.finfo(np.float64).eps)


def test_mass_tolerance_boundary_accepts_at_the_limit_and_rejects_just_above():
    """The pass/fail boundary A-VC-7 fixes. Both sides are exercised: a
    one-sided test would pass a driver that accepted anything."""
    eps = float(np.finfo(np.float32).eps)
    tolerance = 32.0 * eps

    at_limit = vk0c.canonicalize(_outcomes_summing_to(1.0 + tolerance), "float32")
    assert at_limit.within_tolerance is True
    assert at_limit.raw_joint_mass_sum == pytest.approx(1.0 + tolerance, abs=1e-15)

    just_above = vk0c.canonicalize(_outcomes_summing_to(1.0 + 33.0 * eps), "float32")
    assert just_above.within_tolerance is False

    just_below_negative = vk0c.canonicalize(_outcomes_summing_to(1.0 - 33.0 * eps), "float32")
    assert just_below_negative.within_tolerance is False


def test_canonical_distribution_is_the_single_downstream_authority():
    """C-3 / A-VC-7: p_hat is raw_joint_mass / sum(raw_joint_mass) and the
    raw sum plus the correction are both preserved -- reproducing exactly
    the reconstruction `analyze_vk0c_result.compute_invalid_reasons`
    independently recomputes from the written rows."""
    raw_total = 1.0 + 8.0 * float(np.finfo(np.float32).eps)
    dist = vk0c.canonicalize(_outcomes_summing_to(raw_total), "float32")
    assert dist.within_tolerance is True
    assert sum(dist.probabilities) == pytest.approx(1.0, abs=1e-12)
    assert dist.normalization_correction == pytest.approx(1.0 - dist.raw_joint_mass_sum, abs=0.0)
    for outcome, probability in zip(dist.outcomes, dist.probabilities):
        assert probability == pytest.approx(
            outcome.raw_joint_mass / dist.raw_joint_mass_sum,
            abs=analyzer.CANONICAL_PROBABILITY_RECONSTRUCTION_TOLERANCE,
        )


@requires_artifacts
def test_matched_state_rows_satisfy_the_frozen_analyzer_schema(trained_agent, config, anchors, kernel):
    """The driver/analyzer contract (A-VC-10): the rows this driver writes
    must validate under the analyzer's own frozen validator, including its
    structural cross-checks (final_skill vs each token's implied transition,
    raw_joint == raw_first * raw_second, no same-label SET)."""
    anchor = next(a for a in anchors if a.training_seed == 2026080101 and a.check_index == 5)
    env, restored = vk0c.restore_anchor(agent=trained_agent, config=config, anchor=anchor)
    env.close()
    context = vk0c.policy_context(trained_agent, restored.obs, restored.state)
    dtype_name = vk0c.policy_probability_dtype(trained_agent)

    all_rows = []
    for order_code in vk0c.ORDER_CODES:
        outcomes = vk0c.enumerate_order(
            trained_agent, context, anchor.incumbent, anchor.skill_age, anchor.active_mask, order_code
        )
        dist = vk0c.canonicalize(outcomes, dtype_name)
        assert dist.within_tolerance is True
        rows = vk0c.build_matched_state_rows(
            anchor=anchor, policy_state=vk0c.POLICY_STATE_TRAINED,
            checkpoint_hash=anchor.checkpoint_hash, order_code=order_code, dist=dist,
            kernel=kernel, signs=restored.initial_signs, boundary_state_replay_ok=True,
        )
        assert len(rows) == 16
        all_rows.extend(rows)

    errors: list[str] = []
    for index, row in enumerate(all_rows):
        errors.extend(analyzer.validate_matched_state_row(row, index))
    assert errors == []

    reasons = analyzer.compute_invalid_reasons(all_rows, [], [], _minimal_manifest())
    enumeration_reasons = [
        r for r in reasons
        if r.split(":")[0] in {
            "ANCHOR_INVENTORY_INCONSISTENT",
            "POLICY_PROBABILITY_DTYPE_INCONSISTENT",
            "RAW_JOINT_MASS_NOT_NORMALIZED",
            "CANONICAL_PROBABILITY_NOT_RECONSTRUCTED",
            "ORDER_TRANSPORT_STATE_REPLAY_FAILED",
            "COMMON_COORDINATE_MAPPING_INCOMPLETE",
        }
    ]
    assert enumeration_reasons == []


def _minimal_manifest() -> dict:
    """A manifest that satisfies only the authorization checks, so the
    enumeration-validity reasons above are the only ones under test."""
    return {
        "contract_id": analyzer.VK0_CONTRACT_ID,
        "vk0c_schema_version": analyzer.VK0C_SCHEMA_VERSION,
        "vk0b_trace_schema_version": analyzer.VK0B_TRACE_SCHEMA_VERSION,
        "check_row_count": analyzer.FROZEN_CHECK_ROW_COUNT,
        "deduplicated_anchor_count": analyzer.FROZEN_ANCHOR_COUNT,
        "episodes_per_seed": analyzer.FROZEN_EPISODES_PER_SEED,
        "noninitial_checks": analyzer.FROZEN_NONINITIAL_CHECKS,
        "vk0b_source_bindings": {f: "0" * 64 for f in analyzer.VK0B_SOURCE_BINDING_FIELDS},
        "seeds": {
            str(2026080100 + i): {
                "checkpoint_hash": "x", "resolved_config_hash": "y",
                "exposure_authorization": {"actual_exposure_schema": "vk0b-exposure-1"},
            }
            for i in range(1, 7)
        },
    }


# =============================================================================
# (5) Positive control -- VC-D2
# =============================================================================


def test_forced_token_for_target_never_asks_for_a_same_label_set():
    """A same-label SET is structurally excluded, so landing an agent on its
    own incumbent must be expressed as KEEP; `_force_token` raises on the
    other spelling."""
    assert vk0c.forced_token_for_target(2, True, 2) == (KEEP_TOKEN, INVALID_SKILL)
    assert vk0c.forced_token_for_target(2, True, 3) == (SET_TOKEN, 3)
    assert vk0c.forced_token_for_target(INVALID_SKILL, False, 0) == (SET_TOKEN, 0)


@requires_artifacts
def test_positive_control_is_order_conjugate_at_a_real_anchor(trained_agent, config, anchors):
    """VC-D2: with BOTH agents forced to the same final joint assignment, the
    two orders must produce identical executed windows -- identical realized
    skills by physical agent, primitive actions, five-step reward, match
    vectors and post-window state."""
    anchor = next(a for a in anchors if a.training_seed == 2026080101 and a.check_index == 6)
    for target in ((0, 3), (2, 1), (int(anchor.incumbent[0]), int(anchor.incumbent[1]))):
        forced = {
            0: vk0c.forced_token_for_target(anchor.incumbent[0], anchor.active_mask[0], target[0]),
            1: vk0c.forced_token_for_target(anchor.incumbent[1], anchor.active_mask[1], target[1]),
        }
        outcomes = {
            order_code: vk0c.run_forced_window(
                agent=trained_agent, config=config, anchor=anchor,
                order_code=order_code, forced_tokens=forced,
            )
            for order_code in vk0c.ORDER_CODES
        }
        for order_code, outcome in outcomes.items():
            assert outcome.fingerprint_match is True, order_code
            assert outcome.realized_skills == target, order_code
            assert len(outcome.reward_vector) == 5
        canonical = outcomes[vk0c.ORDER_CANONICAL]
        reversed_ = outcomes[vk0c.ORDER_REVERSED]
        assert canonical.realized_skills == reversed_.realized_skills
        assert canonical.primitive_actions == reversed_.primitive_actions
        assert canonical.reward_vector == reversed_.reward_vector
        assert canonical.slow_match_vector == reversed_.slow_match_vector
        assert canonical.fast_match_vector == reversed_.fast_match_vector
        assert canonical.post_window_state_hash == reversed_.post_window_state_hash


def test_positive_control_predicate_rejects_a_planted_order_disagreement():
    """The predicate must be able to go red. A row whose two orders disagree
    on any recorded vector is not a passing control."""
    row = {
        "forced_assignment": {"agent_0": "1", "agent_1": "2"},
        "canonical_realized_skill": {"agent_0": "1", "agent_1": "2"},
        "reversed_realized_skill": {"agent_0": "1", "agent_1": "2"},
        "canonical_primitive_actions": [[[1.0, 0.0], [0.0, 1.0]]] * 5,
        "reversed_primitive_actions": [[[1.0, 0.0], [0.0, 1.0]]] * 5,
        "canonical_reward_vector": [1.0] * 5,
        "reversed_reward_vector": [1.0] * 5,
        "canonical_slow_match_vector": [1] * 5,
        "reversed_slow_match_vector": [1] * 5,
        "canonical_fast_match_vector": [1] * 5,
        "reversed_fast_match_vector": [1] * 5,
        "canonical_post_window_state_hash": "abc",
        "reversed_post_window_state_hash": "abc",
    }
    assert vk0c._positive_control_holds(row) is True

    broken = dict(row)
    broken["reversed_reward_vector"] = [1.0, 1.0, 1.0, 1.0, 0.0]
    assert vk0c._positive_control_holds(broken) is False

    wrong_skill = dict(row)
    wrong_skill["reversed_realized_skill"] = {"agent_0": "1", "agent_1": "3"}
    assert vk0c._positive_control_holds(wrong_skill) is False


# =============================================================================
# (6) Gate B transition parity -- A-VC-4
# =============================================================================


def test_pure_transition_matches_the_a_vc_4_literal():
    """A-VC-4's rule, written out by hand: KEEP -> same skill, age + 5;
    SET(z) -> skill z, age 0 at the edit and 5 at the next check; active
    True after any legal token."""
    post_skills, next_ages, next_active, post_ages = vk0c.pure_inter_check_transition(
        skills=(1, 2), ages=(10, 5), active=(True, True),
        tokens=((KEEP_TOKEN, INVALID_SKILL), (SET_TOKEN, 0)),
    )
    assert post_skills == (1, 0)
    assert post_ages == (10, 0)
    assert next_ages == (15, 5)
    assert next_active == (True, True)

    post_skills, next_ages, next_active, post_ages = vk0c.pure_inter_check_transition(
        skills=(INVALID_SKILL, INVALID_SKILL), ages=(0, 0), active=(False, False),
        tokens=((SET_TOKEN, 3), (SET_TOKEN, 1)),
    )
    assert post_skills == (3, 1)
    assert post_ages == (0, 0)
    assert next_ages == (5, 5)
    assert next_active == (True, True)


def test_canonical_transition_case_set_is_complete_and_finite():
    """The Gate-B case set: the no-incumbent class plus every reachable
    incumbent roster crossed with every legal joint token. 16 + 16 skill
    pairs x 49 reachable age pairs x 16 tokens = 12,560."""
    cases = list(vk0c.canonical_transition_cases())
    assert len(cases) == 16 + 16 * 49 * 16 == 12560
    assert vk0c.REACHABLE_ACTIVE_AGES == (5, 10, 15, 20, 25, 30, 35)
    assert all(len(c["tokens"]) == 2 for c in cases)
    inactive = [c for c in cases if c["active"] == (False, False)]
    assert len(inactive) == 16
    assert all(t[0] == SET_TOKEN for c in inactive for t in c["tokens"])


@requires_artifacts
def test_gate_b_pure_transition_equals_the_executed_transition(trained_agent, config, kernel):
    """A-VC-4 Gate B on a structurally complete slice: both roster classes,
    every joint token kind, and two distinct age pairs (so the `+5` rule is
    exercised on more than one value)."""
    cases = [
        c for c in vk0c.canonical_transition_cases()
        if c["active"] == (False, False) or (c["ages"] in {(5, 10), (35, 5)} and c["skills"] == (1, 2))
    ]
    assert len(cases) == 16 + 2 * 16
    result = vk0c.gate_b_transition_parity(
        agent=trained_agent, config=config, kernel=kernel, cases=cases
    )
    assert result["cases_checked"] == len(cases)
    assert result["mismatch_count"] == 0, result["mismatches"]


@requires_artifacts
def test_gate_b_detects_a_corrupted_pure_transition(trained_agent, config, kernel, monkeypatch):
    """The paired negative for Gate B. With A-VC-4's `age + 5` replaced by
    `age + 4`, the executed agent/env transition must disagree -- otherwise
    Gate B is comparing nothing."""
    original = vk0c.pure_inter_check_transition

    def wrong(skills, ages, active, tokens):
        post_skills, next_ages, next_active, post_ages = original(skills, ages, active, tokens)
        return post_skills, (next_ages[0] - 1, next_ages[1] - 1), next_active, post_ages

    monkeypatch.setattr(vk0c, "pure_inter_check_transition", wrong)
    cases = [
        c for c in vk0c.canonical_transition_cases()
        if c["skills"] == (1, 2) and c["ages"] == (5, 10)
    ]
    assert len(cases) == 16
    result = vk0c.gate_b_transition_parity(
        agent=trained_agent, config=config, kernel=kernel, cases=cases
    )
    assert result["mismatch_count"] == len(cases)


# =============================================================================
# (6b) Propagation -- VC-D3 / A-VC-6
# =============================================================================


def test_reachable_state_bound_matches_the_hand_count():
    """1 no-incumbent state at check 0, then at most 16 * c^2 at check c."""
    assert vk0c.reachable_state_bound() == 1 + 16 * sum(c * c for c in range(1, 8)) == 2241
    assert vk0c.reachable_state_bound() < 16**8


@requires_artifacts
def test_propagation_memoizes_on_the_canonical_state_tuple(trained_agent, kernel):
    """The memo is what turns `16 ** 8` tree paths into a bounded sweep. If
    the cache key ever picked up an irrelevant field, the evaluation count
    would rise above the visited-state count and this goes red."""
    propagator = vk0c.Propagator(
        agent=trained_agent, kernel=kernel, signs=(1, 1), dtype_name="float32"
    )
    state = (1, 2, 5, 10, True, True)
    propagator.distribution(3, state, vk0c.ORDER_CANONICAL)
    assert propagator.distribution_evaluations == 1
    propagator.distribution(3, state, vk0c.ORDER_CANONICAL)
    assert propagator.distribution_evaluations == 1, "an identical key must be a cache hit"
    propagator.distribution(3, state, vk0c.ORDER_REVERSED)
    assert propagator.distribution_evaluations == 2, "the order is part of the key"
    propagator.distribution(4, state, vk0c.ORDER_CANONICAL)
    assert propagator.distribution_evaluations == 3, "the check index is part of the key"


@requires_artifacts
def test_propagation_visits_at_most_the_reachable_state_bound(trained_agent, kernel):
    """VC-D3: an occupancy pushforward, not a tree replay. The visit counter
    is the discriminator -- a path enumeration over the same clock would
    walk 4.3e9 leaves."""
    propagator = vk0c.Propagator(
        agent=trained_agent, kernel=kernel, signs=(-1, 1), dtype_name="float32"
    )
    result = propagator.run(vk0c.ORDER_CANONICAL)
    assert result.distinct_states_visited <= vk0c.reachable_state_bound()
    assert result.distribution_evaluations == result.distinct_states_visited
    assert result.distinct_states_visited < 16**8

    assert len(result.rows) == 8
    for row in result.rows:
        occupancy = sum(x["occupancy_probability"] for x in row["occupancy_summary"])
        assert occupancy == pytest.approx(1.0, abs=1e-9)
    # A-VC-4: the sweep starts with no incumbents, both agents inactive.
    assert result.rows[0]["occupancy_summary"] == [
        {"state_key": vk0c.state_key(0, vk0c.INITIAL_PROPAGATION_STATE), "occupancy_probability": 1.0}
    ]
    assert result.rows[0]["expected_keep_rate"] == {"agent_0": 0.0, "agent_1": 0.0}
    assert result.rows[0]["expected_renewal_rate"] == {"agent_0": 0.0, "agent_1": 0.0}


@requires_artifacts
def test_propagation_rows_satisfy_the_frozen_analyzer_schema(trained_agent, kernel):
    propagator = vk0c.Propagator(
        agent=trained_agent, kernel=kernel, signs=(1, -1), dtype_name="float32"
    )
    result = propagator.run(vk0c.ORDER_REVERSED)
    rows = vk0c.build_propagation_rows(
        training_seed=2026080101, evaluation_index=0, episode_id=123,
        occupancy_stratum=vk0c.STRATUM_CANONICAL_OCCUPANCY, checkpoint_hash="c" * 64,
        policy_state=vk0c.POLICY_STATE_TRAINED, order_code=vk0c.ORDER_REVERSED,
        result=result, replay_conformance={"factual_reward_vector_reproduced": True},
    )
    errors: list[str] = []
    for index, row in enumerate(rows):
        errors.extend(analyzer.validate_propagation_row(row, index))
    assert errors == []
    assert len({r["check_index"] for r in rows}) == 8
    # A-VC-6's whole-episode expectation is carried alongside the per-check
    # window return the analyzer's own sum identity constrains.
    totals = {r["expected_episode_return_total"] for r in rows}
    assert len(totals) == 1
    assert next(iter(totals)) == pytest.approx(
        sum(r["expected_episode_return"] for r in rows), abs=1e-9
    )


# =============================================================================
# Factual-row reproduction -- VC-D3
# =============================================================================


@requires_artifacts
def test_factual_token_sequence_reproduces_the_stored_vk0b_rows(config, anchors, kernel):
    """VC-D3: replaying an episode's factual tokens through the same
    finite-state machinery and the same reward kernel must reproduce the
    stored V-K0B five-step vectors exactly."""
    by_check = {
        a.check_index: a for a in anchors if a.training_seed == 2026080101 and a.evaluation_index == 0
    }
    signs = vk0c.episode_initial_signs(config, 0)
    outcome = vk0c.reproduce_factual_episode(kernel=kernel, signs=signs, anchors_by_check=by_check)
    assert outcome["conformance"] == {
        "factual_reward_vector_reproduced": True,
        "factual_slow_match_vector_reproduced": True,
        "factual_fast_match_vector_reproduced": True,
        "factual_roster_transition_reproduced": True,
    }
    assert outcome["details"] == []


@requires_artifacts
def test_factual_reproduction_detects_a_planted_reward_vector(config, anchors, kernel):
    """The paired negative: with one stored five-step reward vector altered,
    reproduction must report failure rather than absorb it."""
    by_check = {
        a.check_index: a for a in anchors if a.training_seed == 2026080101 and a.evaluation_index == 0
    }
    corrupted = dict(by_check)
    victim = corrupted[3]
    altered = tuple(float(x) + 0.25 for x in victim.natural_reward_vector)
    assert altered != victim.natural_reward_vector
    corrupted[3] = dataclasses.replace(victim, natural_reward_vector=altered)

    signs = vk0c.episode_initial_signs(config, 0)
    outcome = vk0c.reproduce_factual_episode(kernel=kernel, signs=signs, anchors_by_check=corrupted)
    assert outcome["conformance"]["factual_reward_vector_reproduced"] is False
    assert outcome["details"]


@requires_artifacts
def test_factual_reproduction_detects_a_planted_token(config, anchors, kernel):
    """A wrong token must break the downstream roster chain, not just one
    window: the planted SET makes every later check's stored incumbent
    disagree with the propagated one."""
    by_check = {
        a.check_index: a for a in anchors if a.training_seed == 2026080101 and a.evaluation_index == 0
    }
    corrupted = dict(by_check)
    victim = corrupted[2]
    tokens = json.loads(json.dumps(victim.factual_joint_token))
    incumbent = int(victim.incumbent[0])
    tokens["0"] = {"kind": "SET", "set_skill": str((incumbent + 1) % 4)}
    corrupted[2] = dataclasses.replace(victim, factual_joint_token=tokens)

    signs = vk0c.episode_initial_signs(config, 0)
    outcome = vk0c.reproduce_factual_episode(kernel=kernel, signs=signs, anchors_by_check=corrupted)
    assert outcome["conformance"]["factual_roster_transition_reproduced"] is False


# =============================================================================
# (8) Fresh-initialization control -- VC-D5 / A-VC-11
# =============================================================================


@requires_artifacts
def test_two_same_seed_constructions_hash_equal():
    entry = vk0b.resolve_checkpoint_entry(str(CHECKPOINT_BUNDLE))
    control = vk0c.fresh_init_control(
        config_module_name=CONFIG_MODULE,
        training_seed=int(entry["training_seed"]),
        resolved_config_hash=str(entry["resolved_config_hash"]),
    )
    assert control["construction_1_param_hash"] == control["construction_2_param_hash"]
    assert control["construction_1_all_module_hash"] == control["construction_2_all_module_hash"]
    assert control["deterministic"] is True
    assert analyzer._fresh_init_deterministic(
        {
            "construction_1_param_hash": control["construction_1_param_hash"],
            "construction_2_param_hash": control["construction_2_param_hash"],
        }
    )


def test_different_seed_constructions_hash_unequal():
    """The paired negative for the determinism gate. If the construction
    hash were insensitive to the weights -- covering only shapes, say -- it
    would be equal here and the gate would be unable to detect anything."""
    first = vk0c.build_fresh_agent(CONFIG_MODULE, 20260801)
    second = vk0c.build_fresh_agent(CONFIG_MODULE, 20260802)
    hash_first = vk0c.agent_construction_hash(first, vk0c.DECISION_CONTEXT_MODULES, "cfg")
    hash_second = vk0c.agent_construction_hash(second, vk0c.DECISION_CONTEXT_MODULES, "cfg")
    assert hash_first != hash_second


def test_construction_hash_binds_the_resolved_configuration_identity():
    """A-VC-11: the hash covers the resolved configuration identity, so two
    identical parameter sets under different configs never collide."""
    agent = vk0c.build_fresh_agent(CONFIG_MODULE, 20260801)
    assert vk0c.agent_construction_hash(
        agent, vk0c.DECISION_CONTEXT_MODULES, "config-a"
    ) != vk0c.agent_construction_hash(agent, vk0c.DECISION_CONTEXT_MODULES, "config-b")


def test_control_rows_satisfy_the_frozen_analyzer_schema():
    row = {
        "contract_id": vk0c.CONTRACT_ID,
        "vk0c_schema_version": vk0c.VK0C_SCHEMA_VERSION,
        "control_type": vk0c.CONTROL_TYPE_FRESH_INIT,
        "training_seed": 2026080101,
        "construction_1_param_hash": "a" * 64,
        "construction_2_param_hash": "a" * 64,
    }
    assert analyzer.validate_control_row(row, 0) == []
    assert vk0c.CONTROL_TYPE_FRESH_INIT == analyzer.CONTROL_TYPE_FRESH_INIT
    assert vk0c.CONTROL_TYPE_POSITIVE == analyzer.CONTROL_TYPE_POSITIVE


# =============================================================================
# Cross-module frozen-identity drift guards
# =============================================================================


def test_frozen_identity_constants_match_the_analyzer():
    assert vk0c.CONTRACT_ID == analyzer.VK0_CONTRACT_ID
    assert vk0c.VK0C_SCHEMA_VERSION == analyzer.VK0C_SCHEMA_VERSION == "vk0c-1"
    assert vk0c.VK0B_TRACE_SCHEMA_VERSION == analyzer.VK0B_TRACE_SCHEMA_VERSION == "vk0-trace-2"
    assert vk0c.INVALID_VERDICT == "INVALID_VK0C_ORDER_TRANSPORT_AUDIT"
    assert vk0c.FROZEN_CHECK_ROW_COUNT == analyzer.FROZEN_CHECK_ROW_COUNT == 5376
    assert vk0c.FROZEN_ANCHOR_COUNT == analyzer.FROZEN_ANCHOR_COUNT == 2688
    assert vk0c.FROZEN_EPISODES_PER_SEED == analyzer.FROZEN_EPISODES_PER_SEED == 64
    assert vk0c.FROZEN_NONINITIAL_CHECKS == analyzer.FROZEN_NONINITIAL_CHECKS == 7
    assert vk0c.FROZEN_SEED_COUNT == analyzer.FROZEN_SEED_COUNT == 6
    assert set(vk0c.ORDER_CODES) == analyzer.ORDER_CODES
    assert {vk0c.STRATUM_CANONICAL_OCCUPANCY, vk0c.STRATUM_REVERSED_OCCUPANCY} == analyzer.OCCUPANCY_STRATA
    assert {vk0c.POLICY_STATE_FRESH, vk0c.POLICY_STATE_TRAINED} == analyzer.POLICY_STATES


def test_coverage_flag_definition():
    """The recorded realization binding: a duty is covered only if its match
    is 1 at every one of the window's five steps."""
    assert vk0c.coverage_flags([1, 1, 1, 1, 1], [1, 1, 1, 1, 1]) == (False, False)
    assert vk0c.coverage_flags([1, 1, 0, 1, 1], [1, 1, 1, 1, 1]) == (True, False)
    assert vk0c.coverage_flags([1, 1, 1, 1, 1], [0, 0, 0, 0, 0]) == (False, True)


def test_unit_expectation_guard_rejects_a_leaking_occupancy():
    assert vk0c._unit(1.0 + 1e-15, "test") == 1.0
    assert vk0c._unit(-1e-15, "test") == 0.0
    with pytest.raises(vk0c.Vk0cAssertionError):
        vk0c._unit(1.5, "test")
    with pytest.raises(vk0c.Vk0cAssertionError):
        vk0c._unit(float("nan"), "test")
