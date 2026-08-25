from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from experiments.candidates.eociv_lite import exact_dyadic_ledger_identifiability as a8


def _line_locator(relative: str, line_number: int, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{relative}|{line_number}|{digest}"


def _reference_manifest(marker_locators: dict[str, str]) -> dict:
    leaves = [
        {
            "reward_slot": f"reward.{dtype}",
            "source_dtype": dtype,
            "capture_site": f"emit_{dtype}",
            "after_final_wrapper": True,
            "before_cast": True,
            "before_reduction": True,
            "exactly_once": True,
            "raw_bits_available": True,
            "native_nonmutation": True,
        }
        for dtype in a8.SUPPORTED_DTYPES
    ]
    return {
        "source_witnesses": {
            "reward_interface": [marker_locators["reward"]],
            "capture_sites": [marker_locators["capture"]],
            "dtype_decoder": [marker_locators["decoder"]],
            "fork_tape": [marker_locators["fork"]],
            "mask_identity": [marker_locators["mask"]],
            "phase_count_oracle": [marker_locators["phase"]],
            "endpoint_firewall": [marker_locators["endpoint"]],
            "freshness": [marker_locators["freshness"]],
        },
        "reward_interface": {
            "primary_key": ["episode_key", "timestep", "reward_slot"],
            "payload_fields": ["source_dtype", "value_encoding"],
            "closed_manifest": True,
            "leaves": leaves,
            "reachable_dtypes": list(a8.SUPPORTED_DTYPES),
            "downstream_reward_shaping": [],
            "primary_key_cardinality": "one_per_emitted_scalar",
            "decoder": "exact_integer_n_times_2^-1074",
            "aggregation": {
                "claim_values": "integer_ledger_only",
                "means": "numerator_count_pairs",
                "comparisons": "cross_multiplication",
                "squared_scale_power": -2148,
                "float_aggregation": False,
                "tolerance": False,
            },
        },
        "fork_tape_mask": {
            "deep_state_fields": list(a8.DEEP_STATE_FIELDS),
            "deep_non_aliased": True,
            "cross_arm_aliases": [],
            "tape": {
                "address_fields": list(a8.TAPE_ADDRESS_FIELDS),
                "random_access": True,
                "cursor_based": False,
                "unlisted_stochastic_sources": [],
                "global_or_unkeyed_draws": False,
            },
            "semantic_pipeline": {
                "correct": "CORRECT(payload)",
                "swapped": "SWAPPED(payload)",
                "reveal": "payload_s",
                "mask": "canonical_mask_token_independent_of_semantic",
                "other_semantic_sinks": [],
            },
            "mask_identity": {
                "trace_channels": list(a8.MASK_TRACE_CHANNELS),
                "raw_bit_equal_correct_swapped": True,
                "signed_zero_bits_diagnostic": True,
                "fork_through_termination": True,
                "semantic_value_downstream_sinks": [],
            },
        },
        "phase_count_oracle": {
            "roster": a8.canonical_roster(),
            "training_units": 72,
            "training_native_natural_episodes": 72,
            "training_complementary_episodes": 72,
            "training_episodes": 144,
            "heldout_units": 48,
            "heldout_episodes": 192,
            "complete_episodes": 336,
            "transition_policy_call_ceiling": 16128,
            "native_learner_calls": 18,
            "native_optimizer_updates": 18,
            "exact_shadow_updates": 72,
            "sign_control_updates": 72,
            "native_anchors": 2,
            "training_semantic": "CORRECT_only",
            "evaluation_arms": [
                "REVEAL_CORRECT",
                "MASK_CORRECT",
                "REVEAL_SWAPPED",
                "MASK_SWAPPED",
            ],
        },
        "endpoint_firewall": {
            "native_endpoint_per_history": True,
            "history_specific_exact_accumulator": True,
            "history_specific_sign_control_accumulator": True,
            "context_fields": list(a8.CONTEXT_FIELDS),
            "context_exclusions": list(a8.CONTEXT_EXCLUSIONS),
            "finite_context_vocabulary_enumerated_before_outcomes": True,
            "native_gate_before_reward_or_future": True,
            "native_natural_only_updates_native": True,
            "complementary_ledger_only": True,
            "no_learning_between_pair_branches": True,
            "freeze_hash_endpoints_and_tables_before_heldout_rewards": True,
            "heldout_updates_endpoints": False,
            "missing_target_maps_all_endpoints_to_mask": True,
            "missing_target_retained_as_same_noop_episode": True,
            "missing_target_excluded": False,
            "endpoint_specific_evaluation_episode": False,
        },
        "freshness": {
            "treatment_id": a8.TREATMENT_ID,
            "imports_predecessor_scientific_objects": [],
            "reconstructs_or_redecodes_predecessor": False,
            "artifact_identity_collision": False,
            "predecessor_anchors": a8.PREDECESSOR_ANCHORS,
        },
    }


def _snapshot(tmp_path: Path, mutate=None) -> a8.SourceSnapshot:
    root = tmp_path / "source"
    host = root / "experiments" / "candidates" / "eociv_lite"
    host.mkdir(parents=True)
    marker_names = ("reward", "capture", "decoder", "fork", "mask", "phase", "endpoint", "freshness")
    lines = [f'{name.upper()}_WITNESS = "A8_{name}"' for name in marker_names]
    runtime_relative = a8.HOST_SOURCE_PATHS[1]
    (root / runtime_relative).write_text("\n".join(lines) + "\n", encoding="utf-8")
    locators = {
        name: _line_locator(runtime_relative, index + 1, lines[index])
        for index, name in enumerate(marker_names)
    }
    manifest = _reference_manifest(locators)
    if mutate is not None:
        mutate(manifest)
    sibling_relative = a8.HOST_SOURCE_PATHS[0]
    (root / sibling_relative).write_text(
        f"{a8.MANIFEST_SYMBOL} = {manifest!r}\n", encoding="utf-8"
    )
    return a8.read_source_snapshot(root, a8.HOST_SOURCE_PATHS)


def _certificate(snapshot: a8.SourceSnapshot, name: str) -> a8.Certificate:
    return {certificate.name: certificate for certificate in a8.evaluate_certificates(snapshot)}[name]


def test_reference_fixture_exposes_frozen_seed_span_contradiction(tmp_path: Path) -> None:
    certificates = a8.evaluate_certificates(_snapshot(tmp_path))
    assert [certificate.name for certificate in certificates] == list(a8.CERTIFICATE_ORDER)
    by_name = {certificate.name: certificate for certificate in certificates}
    assert all(
        certificate.passed
        for name, certificate in by_name.items()
        if name != "phase_count_oracle"
    )
    assert by_name["phase_count_oracle"].failures == (
        "natural_seed_span_mismatch",
        "action_seed_span_mismatch",
    )
    assert "observed_natural_seed_span:4810010..4840223" in by_name["phase_count_oracle"].witnesses
    assert "observed_action_seed_span:6810010..6840223" in by_name["phase_count_oracle"].witnesses
    assert all(certificate.source_digest for certificate in certificates)
    assert a8.select_terminal_branch(
        source_binding_passed=True,
        activity_ledger=a8.ZERO_ACTIVITY_LEDGER,
        certificates=certificates,
    ) == "A8_PHASE_ENDPOINT_OR_FIREWALL_UNIDENTIFIED"


def test_exact_dyadic_decoder_preserves_bits_and_rejects_nonfinite() -> None:
    assert a8.decode_float_bits("binary16", 0x3C00)["integer_n"] == 1 << 1074
    assert a8.decode_float_bits("bfloat16", 0x3F80)["integer_n"] == 1 << 1074
    assert a8.decode_float_bits("binary32", 0x80000000)["signed_zero"] is True
    assert a8.decode_float_bits("binary64", 1)["integer_n"] == 1
    assert a8.decode_integer(-7)["integer_n"] == -7 * (1 << 1074)
    with pytest.raises(a8.ContractError, match="nonfinite"):
        a8.decode_float_bits("binary16", 0x7C00)
    with pytest.raises(a8.ContractError, match="booleans"):
        a8.decode_integer(True)


def test_dtype_or_value_in_primary_key_fails_reward_certificate(tmp_path: Path) -> None:
    snapshot = _snapshot(
        tmp_path,
        lambda manifest: manifest["reward_interface"].update(
            primary_key=["episode_key", "timestep", "reward_slot", "source_dtype"]
        ),
    )
    certificate = _certificate(snapshot, "reward_interface_manifest")
    assert not certificate.passed
    assert "primary_key_is_not_value_free_exact_tuple" in certificate.failures


@pytest.mark.parametrize("field,value", [("float_aggregation", True), ("tolerance", True)])
def test_float_or_tolerance_aggregation_fails_exact_decoder_certificate(
    tmp_path: Path, field: str, value: bool
) -> None:
    def mutate(manifest):
        manifest["reward_interface"]["aggregation"][field] = value

    certificate = _certificate(_snapshot(tmp_path, mutate), "dtype_decoder")
    assert not certificate.passed
    assert f"aggregation_contract_mismatch:{field}" in certificate.failures


def test_cursor_tape_fails_fork_dependency_certificate(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["fork_tape_mask"]["tape"]["cursor_based"] = True

    certificate = _certificate(_snapshot(tmp_path, mutate), "fork_tape_dependency")
    assert not certificate.passed
    assert "cursor_or_consumption_dependent_tape" in certificate.failures


def test_cross_arm_alias_fails_fork_dependency_certificate(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["fork_tape_mask"]["cross_arm_aliases"] = [["actor", "actor"]]

    certificate = _certificate(_snapshot(tmp_path, mutate), "fork_tape_dependency")
    assert not certificate.passed
    assert "deep_fork_nonaliasing_unproved" in certificate.failures


def test_mask_semantic_leak_fails_raw_bit_certificate(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["fork_tape_mask"]["mask_identity"]["semantic_value_downstream_sinks"] = ["debug_log"]

    certificate = _certificate(_snapshot(tmp_path, mutate), "mask_raw_bit_identity")
    assert not certificate.passed
    assert "masked_semantic_value_leaks_downstream" in certificate.failures


def test_missing_target_exclusion_fails_endpoint_certificate(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["endpoint_firewall"]["missing_target_excluded"] = True

    certificate = _certificate(
        _snapshot(tmp_path, mutate), "endpoint_context_no_target_outcome_firewall"
    )
    assert not certificate.passed
    assert "endpoint_firewall_literal_mismatch:missing_target_excluded" in certificate.failures


def test_heldout_endpoint_update_fails_outcome_firewall(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["endpoint_firewall"]["heldout_updates_endpoints"] = True

    certificate = _certificate(
        _snapshot(tmp_path, mutate), "endpoint_context_no_target_outcome_firewall"
    )
    assert not certificate.passed
    assert "endpoint_firewall_literal_mismatch:heldout_updates_endpoints" in certificate.failures


def test_predecessor_import_fails_freshness_certificate(tmp_path: Path) -> None:
    def mutate(manifest):
        manifest["freshness"]["imports_predecessor_scientific_objects"] = ["b7_result"]

    certificate = _certificate(_snapshot(tmp_path, mutate), "b6_b7_freshness")
    assert not certificate.passed
    assert "predecessor_scientific_object_import_declared" in certificate.failures


def test_absent_literal_manifest_fails_closed_at_reward_branch(tmp_path: Path) -> None:
    root = tmp_path / "source"
    for relative in a8.HOST_SOURCE_PATHS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")
    snapshot = a8.read_source_snapshot(root, a8.HOST_SOURCE_PATHS)
    certificates = a8.evaluate_certificates(snapshot)
    assert a8.select_terminal_branch(
        source_binding_passed=True,
        activity_ledger=a8.ZERO_ACTIVITY_LEDGER,
        certificates=certificates,
    ) == "A8_REWARD_INTERFACE_OR_EXACT_DECODER_UNIDENTIFIED"


def test_source_or_activity_failure_has_first_precedence(tmp_path: Path) -> None:
    certificates = a8.evaluate_certificates(_snapshot(tmp_path))
    assert a8.select_terminal_branch(
        source_binding_passed=False,
        activity_ledger=a8.ZERO_ACTIVITY_LEDGER,
        certificates=certificates,
    ) == "A8_INVALID_SOURCE_OR_ACTIVITY_CONTRACT"
    changed = copy.deepcopy(a8.ZERO_ACTIVITY_LEDGER)
    changed["rng_draws"] = 1
    assert a8.select_terminal_branch(
        source_binding_passed=True,
        activity_ledger=changed,
        certificates=certificates,
    ) == "A8_INVALID_SOURCE_OR_ACTIVITY_CONTRACT"


def test_positive_branch_requires_all_eight_certificates() -> None:
    certificates = tuple(
        a8.Certificate(name, True, "d" * 64, ("witness",), ())
        for name in a8.CERTIFICATE_ORDER
    )
    assert a8.select_terminal_branch(
        source_binding_passed=True,
        activity_ledger=a8.ZERO_ACTIVITY_LEDGER,
        certificates=certificates,
    ) == "A8_EXACT_DYADIC_LEDGER_AND_CAUSAL_PANEL_CONSTRUCTIBLE"


def test_public_literal_roster_is_invalid_before_audit_because_seed_span_is_inconsistent() -> None:
    payload = {
        "design_id": a8.DESIGN_ID,
        "treatment_id": a8.TREATMENT_ID,
        "target_version_id": a8.TARGET_VERSION_ID,
        "branch_precedence": [{"branch": branch} for branch in a8.BRANCH_PRECEDENCE],
        "hard_caps": a8.ZERO_ACTIVITY_LEDGER,
        "fixed_roster": a8.canonical_roster(),
        "required_certificates": [f"certificate-{index}" for index in range(8)],
    }
    passed, failures = a8.validate_payload(payload)
    assert passed is False
    assert "payload_internal:natural_seed_span_mismatch" in failures
    assert "payload_internal:action_seed_span_mismatch" in failures


def test_source_witness_hash_mutation_is_detected(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    runtime = snapshot.root / a8.HOST_SOURCE_PATHS[1]
    text = runtime.read_text(encoding="utf-8").replace('A8_reward"', 'A8_reward_changed"')
    runtime.write_text(text, encoding="utf-8")
    changed = a8.read_source_snapshot(snapshot.root, a8.HOST_SOURCE_PATHS)
    certificate = _certificate(changed, "reward_interface_manifest")
    assert not certificate.passed
    assert any(item.startswith("source_witness_hash_mismatch") for item in certificate.failures)


def test_result_validator_rederives_branch_and_rejects_claim_expansion(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    binding = a8.SourceBinding(
        passed=True,
        source_root=str(snapshot.root),
        expected_commit="a" * 40,
        actual_commit="a" * 40,
        cwd=str(snapshot.root),
        runtime_core_file=str(snapshot.root / "core.py"),
        runtime_runner_file=str(snapshot.root / "runner.py"),
        audited_paths=a8.HOST_SOURCE_PATHS,
        file_sha256={},
        failures=(),
    )
    result = a8.build_result(
        binding=binding,
        snapshot=snapshot,
        payload_sha256=a8.EXPECTED_PAYLOAD_SHA256,
        payload_valid=True,
        payload_failures=(),
    )
    a8.validate_result(result)
    result["b8_authorized"] = True
    with pytest.raises(a8.ContractError, match="exceeds_constructibility"):
        a8.validate_result(result)
