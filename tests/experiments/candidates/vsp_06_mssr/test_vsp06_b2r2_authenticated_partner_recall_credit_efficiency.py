from __future__ import annotations

import inspect
import itertools
import json
from pathlib import Path

import pytest

from experiments.candidates.vsp_06_mssr import (
    vsp06_b2r2_authenticated_partner_recall_credit_efficiency as experiment,
)
from experiments.candidates.vsp_06_mssr import (
    vsp06_b2r2_independent_exact_manifest_verifier as independent,
)
from experiments.candidates.vsp_06_mssr import (
    vsp06_b2r2_source_bound_symmetry_guaranteed_exact_feasibility as generator,
)
from scripts import run_vsp06_b2r2_authenticated_partner_recall_credit_efficiency as runner


ROOT = Path(__file__).resolve().parents[4]


def _envelope(emission: generator.SyntheticEmission) -> dict[str, object]:
    return {
        "tuple": dict(emission.tuple_value),
        "tuple_sha256": emission.tuple_sha256,
        "bucket": emission.bucket,
        "split": emission.split,
        "cell_index": emission.cell_index,
        "block_start": emission.block_start,
        "block_stop": emission.block_stop,
    }


def _emissions() -> list[generator.SyntheticEmission]:
    return [
        generator.emit_synthetic_cell(
            generator.synthetic_tuple_template(f"proof_{split}"),
            generator.emission_request(index, split),
        )
        for index, split in enumerate(("train", "calibration", "evaluation"))
    ]


def test_fresh_identities_and_stage1_boundary_are_exact() -> None:
    contract = experiment.stage1_contract()
    assert contract["candidate"] == "CAND-VSP-06-MSSR@adversarial-revision-v9"
    assert contract["selector"] == "VSP06-B2R2-SB-SG-EF-CP-SAT-V1"
    assert contract["verifier"] == "VSP06-B2R2-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
    assert contract["formal"] is False
    assert contract["K_search"] == 0
    assert contract["hypothetical_transitions"] == 0
    assert contract["canonical_readiness"] is False
    assert contract["scientific_claim"] is None


def test_oa_recipe_columns_and_every_pair_are_exactly_balanced() -> None:
    rows = generator.oa_rows()
    assert rows == tuple(
        (a, b, a ^ b, a ^ (0, 2, 3, 1)[b], a ^ (0, 2, 3, 1)[b] ^ b)
        for a, b in itertools.product(range(4), repeat=2)
    )
    proof = generator.oa_balance_proof()
    assert proof["column_counts"] == ((4, 4, 4, 4),) * 5
    assert len(proof["pair_counts"]) == 10
    assert all(counts == (1,) * 16 for counts in proof["pair_counts"].values())


def test_every_axis_relabeling_preserves_multiplicity() -> None:
    axes = {
        "pool": ("p0", "p1"),
        "seed": ("s0", "s1", "s2", "s3"),
        "panel": ("n0", "n1"),
        "branch": ("KEEP", "RESET", "CURRENT"),
        "Y": ("0", "1", "2", "3"),
    }
    identities = {axis: dict(zip(labels, labels)) for axis, labels in axes.items()}
    for axis, labels in axes.items():
        for permutation in itertools.permutations(labels):
            relabelings = {name: dict(mapping) for name, mapping in identities.items()}
            relabelings[axis] = dict(zip(labels, permutation))
            proof = generator.relabeling_multiplicity_proof(axes, relabelings)
            assert proof["before"] == proof["after"] == 192
            assert proof["multiplicity_histogram"] == {1: 192}


def test_fixed_enumeration_order_makes_oa_row_the_fastest_cell_axis() -> None:
    sizes = {
        "pool": 2, "seed": 4, "panel": 2, "branch": 3,
        "Y": 4, "replicate": 5, "OA row": 16,
    }
    origin = {axis: 0 for axis in generator.ENUMERATION_ORDER}
    assert generator.fixed_cell_index(origin, sizes) == 0
    next_oa = dict(origin)
    next_oa["OA row"] = 1
    assert generator.fixed_cell_index(next_oa, sizes) == 1
    next_replicate = dict(origin)
    next_replicate["replicate"] = 1
    assert generator.fixed_cell_index(next_replicate, sizes) == 16
    wrong_order = {axis: origin[axis] for axis in reversed(generator.ENUMERATION_ORDER)}
    with pytest.raises(generator.Stage1ContractError, match="order"):
        generator.fixed_cell_index(wrong_order, sizes)


def test_exact_catalog_count_is_algebraic_and_noncanonical() -> None:
    proof = generator.catalog_count_proof()
    assert proof == {
        "components": {
            "primary": 67_584,
            "calibration": 2_560,
            "checkpoint": 28_672,
            "final_keep": 1_024,
        },
        "total": 99_840,
        "selected_target": 22_144,
        "enumerated_canonical_rows": 0,
    }
    assert generator.FINAL_KEEP_REPLICATES_PER_OA_ROW * 16 == 64
    assert 4 * generator.FINAL_KEEP_QUARTETS_PER_SEED * 4 == 1_024


def test_fixed_nonce_blocks_are_disjoint_and_emissions_use_first_matching_nonce() -> None:
    emissions = _emissions()
    assert {emission.split for emission in emissions} == {"train", "calibration", "evaluation"}
    assert [(item.block_start, item.block_stop) for item in emissions] == [
        (0, 4096), (4096, 8192), (8192, 12288)
    ]
    for index, emission in enumerate(emissions):
        template = generator.synthetic_tuple_template(f"proof_{emission.split}")
        request = generator.emission_request(index, emission.split)
        generator.verify_synthetic_emission(template, request, emission)
        for nonce in range(emission.block_start, emission.tuple_value["nonce"]):
            row = dict(template)
            row["nonce"] = nonce
            payload = generator.canonical_tuple_bytes(row)
            assert generator.split_for_bucket(generator.bucket_for_tuple(payload)) != emission.split


def test_missing_nonce_is_terminal() -> None:
    template = generator.synthetic_tuple_template("missing")
    with pytest.raises(generator.Stage1ContractError, match="missing fixed-block emission is terminal"):
        generator.verify_synthetic_emission(
            template, generator.emission_request(7, "evaluation"), None
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cell_conditional", True),
        ("bucket_override", 7),
        ("split_salt", "8100798/"),
        ("salt_resample", True),
        ("domain_extension", 1),
        ("nonce_block_size", 8192),
    ],
)
def test_conditional_override_salt_substitution_and_domain_extension_fail_closed(
    field: str, value: object
) -> None:
    request = generator.emission_request(0, "train")
    request[field] = value
    with pytest.raises(generator.Stage1ContractError, match="forbidden"):
        generator.emit_synthetic_cell(generator.synthetic_tuple_template("guard"), request)


def test_serializer_is_compact_utf8_nfc_fixed_order_and_independently_reconstructed() -> None:
    row = generator.synthetic_tuple_template("serialize")
    payload = generator.canonical_tuple_bytes(row)
    assert payload == independent.canonical_tuple_bytes(row)
    assert b" " not in payload
    assert generator.SPLIT_SALT == b"8100799/" and len(generator.SPLIT_SALT) == 8
    assert generator.CP_SAT_RANDOM_SEED == 8100699
    assert generator.DECISION_SEPARATOR == b"\x00"
    assert b"\x00" not in generator.DECISION_DOMAIN
    assert generator.DECISION_PREFIX.count(b"\x00") == 1
    assert payload.decode("utf-8").startswith('["vsp06_b2r2_authenticated_partner_recall_catalog_v1"')
    wrong_order = {key: row[key] for key in reversed(tuple(row))}
    with pytest.raises(generator.Stage1ContractError, match="order"):
        generator.canonical_tuple_bytes(wrong_order)
    non_nfc = dict(row)
    non_nfc["consumer"] = "synthetic_e\u0301"
    with pytest.raises(generator.Stage1ContractError, match="NFC"):
        generator.canonical_tuple_bytes(non_nfc)


def test_duplicate_tuple_rejection_and_unsigned_collision_tie_break() -> None:
    row = generator.synthetic_tuple_template("duplicate")
    with pytest.raises(generator.Stage1ContractError, match="duplicate"):
        generator.decision_order((row, row))
    same_digest = bytes.fromhex("80" + "00" * 31)
    lower_digest = bytes.fromhex("7f" + "ff" * 31)
    ordered = generator.sort_digest_tuple_pairs(
        ((same_digest, b"z"), (same_digest, b"a"), (lower_digest, b"last-by-signed"))
    )
    assert ordered == (
        (lower_digest, b"last-by-signed"), (same_digest, b"a"), (same_digest, b"z")
    )


def test_independent_verifier_reconstructs_recipe_without_generator_import() -> None:
    assert independent.reconstruct_oa_rows() == generator.oa_rows()
    source = inspect.getsource(independent)
    assert "import vsp06_b2r2_source_bound" not in source
    assert "from experiments.candidates" not in source
    report = independent.stage1_verification_report(
        generator.stage1_structural_proof(), [_envelope(item) for item in _emissions()]
    )
    assert report["verdict"] == "SYNTHETIC_STRUCTURAL_VALID_ONLY"
    assert report["canonical_manifest_verified"] is False
    assert report["global_rank_claim"] is False


@pytest.mark.parametrize("field", ("tuple_sha256", "bucket", "split", "block_start", "block_stop"))
def test_independent_verifier_rejects_envelope_mismatch(field: str) -> None:
    envelope = _envelope(_emissions()[0])
    envelope[field] = "mismatch" if field in {"tuple_sha256", "split"} else -1
    with pytest.raises(independent.IndependentVerificationError, match="mismatch"):
        independent.verify_synthetic_envelopes((envelope,))


def test_independent_verifier_rejects_duplicate_tuple() -> None:
    envelope = _envelope(_emissions()[0])
    with pytest.raises(independent.IndependentVerificationError, match="duplicate"):
        independent.verify_synthetic_envelopes((envelope, dict(envelope)))


def test_fresh_identity_and_path_guards_fail_closed() -> None:
    valid = {
        "direction": experiment.DIRECTION_ID,
        "candidate": experiment.CANDIDATE_ID,
        "treatment": experiment.TREATMENT_ID,
        "selector": experiment.SELECTOR_ID,
        "verifier": experiment.VERIFIER_ID,
        "scientific_parent": experiment.SCIENTIFIC_PARENT,
        "immediate_predecessor_implementation": experiment.IMMEDIATE_PREDECESSOR_IMPLEMENTATION,
    }
    experiment.validate_fresh_identities(valid)
    invalid = dict(valid)
    invalid["candidate"] = invalid["candidate"].replace("v9", "v8")
    with pytest.raises(experiment.Stage1ConfigurationError, match="identity"):
        experiment.validate_fresh_identities(invalid)
    for path in experiment.FRESH_SOURCE_PATHS:
        assert experiment.guard_source_path(path) == path
    for bad in ("../escape.py", "/absolute.py", "experiments/unknown.py", "scripts\\wrong.py"):
        with pytest.raises(experiment.Stage1ConfigurationError, match="path"):
            experiment.guard_source_path(bad)


def test_zero_activity_counters_are_exact_and_nonextensible() -> None:
    counts = experiment.zero_activity_counts()
    assert all(value == 0 for value in counts.values())
    experiment.validate_zero_activity(counts)
    changed = dict(counts)
    changed["rng_draws"] = 1
    with pytest.raises(experiment.Stage1ConfigurationError, match="zero"):
        experiment.validate_zero_activity(changed)
    extended = dict(counts)
    extended["unregistered"] = 0
    with pytest.raises(experiment.Stage1ConfigurationError, match="schema"):
        experiment.validate_zero_activity(extended)


def test_frozen_threshold_schema_and_branch_literal_order_only() -> None:
    assert tuple(experiment.THRESHOLDS.items()) == (
        ("candidate_minus_generic_keep_aulc", 0.08),
        ("candidate_final_keep", 0.55),
        ("selected_p_mediation", 0.20),
        ("selected_p_cross_swap_follow", 0.80),
        ("absolute_decoy_accuracy_change", 0.02),
        ("decoy_kernel_tv_change", 0.02),
        ("maximum_per_seed_current_arm_aulc_gap", 0.05),
        ("mean_reset_stale_target_rate", 0.15),
    )
    assert experiment.BRANCH_PRECEDENCE == (
        "B2R2_INVALID_CONTRACT_ACTIVITY_CAP_OR_PROVENANCE",
        "B2R2_NAVIGATION_OR_CANDIDATE_FINAL_KEEP_GATE_FAILS",
        "B2R2_SELECTED_P_MEDIATION_GATE_FAILS",
        "B2R2_SELECTED_P_CROSS_SWAP_GATE_FAILS",
        "B2R2_DECOY_INVARIANCE_GATE_FAILS",
        "B2R2_CURRENT_OR_RESET_CONTROL_GATE_FAILS",
        "B2R2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_NOT_SUPPORTED",
        "B2R2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_SUPPORTED",
    )
    assert not hasattr(experiment, "classify_result")
    assert "classify_result" not in experiment.__all__


def test_protected_predecessor_is_absent_from_stage1_code_read_set() -> None:
    protected_token = "b2" + "r1"
    protected_receipt = "3fb456f1" + "a1d50caf1a53f066733625921de78b80b572e0f8cdadb395fe6ab5bb"
    paths = [
        Path(generator.__file__), Path(independent.__file__), Path(experiment.__file__),
        Path(runner.__file__),
    ]
    for path in paths:
        source = path.read_text(encoding="utf-8").lower()
        assert protected_token not in source
        assert protected_receipt not in source
        assert "glob(" not in source


def test_immediate_predecessor_is_literal_provenance_only() -> None:
    predecessor = "7d37be4ff33b2ba4984074383a719390e2cce6b0"
    assert experiment.IMMEDIATE_PREDECESSOR_IMPLEMENTATION == predecessor
    assert generator.IMMEDIATE_PREDECESSOR_IMPLEMENTATION == predecessor
    assert independent.IMMEDIATE_PREDECESSOR_IMPLEMENTATION == predecessor
    contract = experiment.stage1_contract()
    assert contract["immediate_predecessor_implementation"] == predecessor
    for module in (experiment, generator, independent):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert source.count(predecessor) == 1
        assert "Path(IMMEDIATE_PREDECESSOR_IMPLEMENTATION" not in source


def test_ledger_matches_source_literals() -> None:
    ledger_path = ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2R2_CONSTRAINT_TARGET_LEDGER_V1.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["source_population"]["catalog_cardinality"] == generator.catalog_count_proof()["total"]
    assert ledger["source_population"]["selected_manifest_target"] == generator.SELECTED_TARGET
    assert ledger["thresholds_in_precedence_order"] == experiment.THRESHOLDS
    assert ledger["caps"] == experiment.CAPS
    assert ledger["branch_precedence"] == list(experiment.BRANCH_PRECEDENCE)
    assert ledger["immediate_predecessor_implementation"] == experiment.IMMEDIATE_PREDECESSOR_IMPLEMENTATION
    assert ledger["formal"] is False and ledger["K_search"] == 0


def test_runner_exposes_only_stage1_status_and_reserved_paths_remain_absent() -> None:
    status = runner.stage1_status()
    assert status["status"] == "SYNTHETIC_STRUCTURAL_VALID_ONLY"
    assert status["stage"] == 1
    assert status["canonical_actions_available"] is False
    assert status["result_claim"] is None
    assert status["all_reserved_paths_absent"] is True
    assert all(status["reserved_path_absence"].values())
    assert status["dependency_facts_separate_from_canonical_readiness"]["canonical_readiness_assessed"] is False
    assert all(value == 0 for value in status["contract"]["activity_counts"].values())
    for path in experiment.RESERVED_CANONICAL_PATHS:
        assert experiment.guard_reserved_path(path) == path
        assert not (ROOT / path).exists()


def test_runner_cli_prints_synthetic_status_only(capsys: pytest.CaptureFixture[str]) -> None:
    assert runner.main(("stage1-status",)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "SYNTHETIC_STRUCTURAL_VALID_ONLY"
    with pytest.raises(SystemExit):
        runner.main(("run-full",))
