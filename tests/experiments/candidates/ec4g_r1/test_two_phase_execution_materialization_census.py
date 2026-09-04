from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import experiments.candidates.ec4g_r1.two_phase_execution_materialization_census as census_module

from experiments.candidates.ec4g_r1.two_phase_execution_materialization_census import (
    BINDING_PATH,
    C0_COMMIT,
    C1_COMMIT,
    C0_SHA256,
    C1_SHA256,
    CELL_ORDER,
    COMPARED_FIELDS,
    CONTRACT_PATH,
    CensusBranch,
    DEFAULT_COMPONENTS,
    ExecutionComponents,
    EXCLUDED_FIELDS,
    HARD_CAPS,
    MAP_ORDER,
    ROW_SCHEMA,
    _compare_validated_rows,
    authenticate_immutable_inputs,
    canonical_json_bytes,
    census_sealed_phase2,
    freeze_design,
    materialize_and_seal_phase1,
    parse_strict_json,
    run_two_phase_census,
)


ROOT = Path(__file__).resolve().parents[4]
SOURCE_REVISION = "1" * 40


def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "blob", f"{commit}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


@pytest.fixture(scope="module")
def immutable_inputs() -> tuple[bytes, bytes]:
    return _git_blob(C0_COMMIT, CONTRACT_PATH), _git_blob(C1_COMMIT, BINDING_PATH)


def test_complete_census_is_cell_major_exact_and_uses_all_hard_caps(tmp_path: Path, immutable_inputs) -> None:
    observed: list[tuple[str, str]] = []

    def map_e(contract, cell):
        observed.append((cell, "M_E"))
        return DEFAULT_COMPONENTS.map_E(contract, cell)

    def map_d(contract, cell):
        observed.append((cell, "M_D"))
        return DEFAULT_COMPONENTS.map_D(contract, cell)

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / "sealed",
        source_revision=SOURCE_REVISION,
        run_id="complete",
        components=ExecutionComponents(map_e, map_d, DEFAULT_COMPONENTS.compiler),
    )

    assert result.terminal_branch is CensusBranch.COMPLETE_TWO_PHASE_EXECUTION_CENSUS
    assert observed == [(cell, map_name) for cell in CELL_ORDER for map_name in MAP_ORDER]
    assert result.equality_vector == {"join": True, "leave": False, "rejoin": True}
    assert str(result.d_fraction) == "1/4"
    assert str(result.d_decimal) == "0.25"
    assert result.activity_counts == HARD_CAPS
    assert result.seal is not None
    assert len(result.seal.rows) == 6
    assert len(result.seal.sha256_identities) == 10
    assert len(result.pair_witnesses) == 3


def test_maps_ignore_all_prediction_metadata_and_derive_actions_from_decision_literals(immutable_inputs) -> None:
    contract = parse_strict_json(immutable_inputs[0])
    assert isinstance(contract, dict)
    original = [
        DEFAULT_COMPONENTS.map_E(contract, cell) for cell in CELL_ORDER
    ], [DEFAULT_COMPONENTS.map_D(contract, cell) for cell in CELL_ORDER]
    contract["total_EC4G_action_map_M_E"]["predeclared_prediction"] = {cell: "A" for cell in CELL_ORDER}
    contract["total_Direct_tau_action_map_M_D"]["predeclared_prediction"] = {cell: "A" for cell in CELL_ORDER}
    contract["canonicalizer_equality_Gamma"]["predeclared_separation"] = {"predicted_D_RER3": "1.00"}
    contract["prospective_prediction"] = {"predicted_D_RER3": "1.00"}
    mutated = [
        DEFAULT_COMPONENTS.map_E(contract, cell) for cell in CELL_ORDER
    ], [DEFAULT_COMPONENTS.map_D(contract, cell) for cell in CELL_ORDER]
    assert mutated == original == (["P", "A", "N"], ["P", "P", "N"])


def test_forbidden_information_flow_precedes_materialization_and_invalidates_all_evidence(tmp_path: Path, immutable_inputs) -> None:
    calls: list[str] = []

    def forbidden(*_args):
        calls.append("called")
        raise AssertionError("must not run")

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / "never-created",
        source_revision=SOURCE_REVISION,
        run_id="forbidden",
        components=ExecutionComponents(forbidden, forbidden, forbidden),
        information_flow_events=({"code": "PREDICTION_FIELD_USE", "detail": "fixture"},),
    )
    assert result.terminal_branch is CensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE
    assert calls == []
    assert result.partial_rows == ()
    assert result.equality_vector is None and result.d_fraction is None


def test_sixth_compilation_failure_has_no_early_comparison_or_D_and_exact_counts(tmp_path: Path, immutable_inputs) -> None:
    compile_calls = 0

    def compiler(contract, cell, action, map_identity):
        nonlocal compile_calls
        compile_calls += 1
        if compile_calls == 6:
            raise RuntimeError("sixth compilation fixture failure")
        return DEFAULT_COMPONENTS.compiler(contract, cell, action, map_identity)

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / "partial",
        source_revision=SOURCE_REVISION,
        run_id="partial",
        components=ExecutionComponents(DEFAULT_COMPONENTS.map_E, DEFAULT_COMPONENTS.map_D, compiler),
    )
    assert result.terminal_branch is CensusBranch.MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS
    assert result.activity_counts["complete_map_calls"] == 6
    assert result.activity_counts["complete_program_compilations"] == 5
    assert result.activity_counts["complete_execution_objects"] == 5
    assert len(result.partial_rows) == 5
    assert result.activity_counts["complete_program_comparisons"] == 0
    assert result.activity_counts["complete_D_aggregations"] == 0
    assert result.d_fraction is None


@pytest.mark.parametrize("fault", ["missing", "default", "substitute"])
def test_missing_default_or_substituted_rows_fail_before_the_barrier(
    tmp_path: Path, immutable_inputs, fault: str
) -> None:
    def compiler(contract, cell, action, map_identity):
        compiled = dict(DEFAULT_COMPONENTS.compiler(contract, cell, action, map_identity))
        if cell == "k_leave" and map_identity == "M_E":
            if fault == "missing":
                compiled.pop("memory_rule")
            elif fault == "default":
                compiled["post_mask"] = None
            else:
                compiled["cell"] = "k_join"
        return compiled

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / fault,
        source_revision=SOURCE_REVISION,
        run_id=fault,
        components=ExecutionComponents(DEFAULT_COMPONENTS.map_E, DEFAULT_COMPONENTS.map_D, compiler),
    )
    assert result.terminal_branch is CensusBranch.MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS
    assert result.activity_counts["materialization_snapshots"] == 0
    assert result.activity_counts["complete_program_comparisons"] == 0
    assert result.d_fraction is None


@pytest.mark.parametrize("mutation", ["snapshot", "object", "import"])
def test_every_postseal_change_or_import_invalidates_before_comparison(
    tmp_path: Path, immutable_inputs, mutation: str
) -> None:
    def mutate(seal):
        if mutation == "snapshot":
            seal.snapshot_path.write_bytes(seal.snapshot_bytes + b" ")
        elif mutation == "object":
            object_path = next(path for path, _bytes in seal.sealed_files if path.name.endswith(".object.json"))
            object_path.write_bytes(b"{}\n")
        else:
            (seal.artifact_root / "imported-row.json").write_text("{}\n", encoding="utf-8")

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / mutation,
        source_revision=SOURCE_REVISION,
        run_id=mutation,
        after_seal=mutate,
    )
    assert result.terminal_branch is CensusBranch.PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID
    assert result.activity_counts["complete_program_comparisons"] == 0
    assert result.activity_counts["complete_D_aggregations"] == 0
    assert result.equality_vector is None and result.d_fraction is None


def _replace_snapshot(seal, transform):
    snapshot = json.loads(seal.snapshot_bytes)
    transform(snapshot)
    new_bytes = canonical_json_bytes(snapshot) + b"\n"
    seal.snapshot_path.write_bytes(new_bytes)
    sealed_files = tuple(
        (path, new_bytes if path == seal.snapshot_path else content)
        for path, content in seal.sealed_files
    )
    return replace(seal, snapshot_bytes=new_bytes, sealed_files=sealed_files)


def _rewrite_fully_linked_seal_with_object_mutation(seal, transform) -> None:
    """Build a digest-consistent invalid seal so Phase 2 reaches schema admission."""

    snapshot = json.loads(seal.snapshot_path.read_bytes())
    manifest = json.loads(seal.manifest_path.read_bytes())
    row = snapshot["rows"][0]
    transform(row["canonical_object"])
    object_bytes = canonical_json_bytes(row["canonical_object"]) + b"\n"
    object_digest = hashlib.sha256(canonical_json_bytes(row["canonical_object"])).hexdigest()
    row["object_sha256"] = object_digest
    row["construction_receipt"]["object_sha256"] = object_digest
    manifest["row_object_sha256"][0] = object_digest
    object_path = seal.artifact_root / "00_k_join_M_E.object.json"
    receipt_path = seal.artifact_root / "00_k_join_M_E.receipt.json"
    object_path.write_bytes(object_bytes)
    receipt_path.write_bytes(canonical_json_bytes(row["construction_receipt"]) + b"\n")

    snapshot_bytes = canonical_json_bytes(snapshot) + b"\n"
    snapshot_digest = hashlib.sha256(snapshot_bytes).hexdigest()
    new_snapshot_path = seal.artifact_root / f"snapshot-{snapshot_digest}.json"
    seal.snapshot_path.rename(new_snapshot_path)
    new_snapshot_path.write_bytes(snapshot_bytes)
    manifest["snapshot_file"] = new_snapshot_path.name
    manifest["snapshot_sha256"] = snapshot_digest
    manifest_bytes = canonical_json_bytes(manifest) + b"\n"
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    new_manifest_path = seal.artifact_root / f"manifest-{manifest_digest}.json"
    seal.manifest_path.rename(new_manifest_path)
    new_manifest_path.write_bytes(manifest_bytes)


@pytest.mark.parametrize("mutation", ["extra", "missing_excluded", "missing_compared"])
def test_phase2_rejects_any_nonexact_canonical_object_key_set_before_witnesses_or_D(
    tmp_path: Path, immutable_inputs, mutation: str
) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / mutation)

    def mutate(compiled):
        if mutation == "extra":
            compiled["unexpected_extra"] = "forbidden"
        elif mutation == "missing_excluded":
            compiled.pop("symbolic_gate_label")
        else:
            compiled.pop("memory_rule")

    _rewrite_fully_linked_seal_with_object_mutation(seal, mutate)
    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(seal, design)
    assert witnesses == ()
    assert equality is None and d_fraction is None and d_decimal is None
    assert failure["code"] == "SEALED_ARTIFACT_INTEGRITY_INVALID"
    assert "key set" in failure["detail"]


def test_replacing_snapshot_and_in_memory_expected_bytes_cannot_bypass_stale_content_address(
    tmp_path: Path, immutable_inputs
) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "stale-address")

    def alter_snapshot(snapshot):
        snapshot["rows"][0]["canonical_object"]["primitive_actions"] = ["tampered"]

    tampered = _replace_snapshot(seal, alter_snapshot)
    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(tampered, design)
    assert witnesses == ()
    assert equality is None and d_fraction is None and d_decimal is None
    assert failure["code"] == "SEALED_ARTIFACT_INTEGRITY_INVALID"
    assert "content-addressed filename" in failure["detail"]


def test_phase2_ignores_all_in_memory_seal_identity_oracles(tmp_path: Path, immutable_inputs) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "ignore-memory")
    untrusted = replace(
        seal,
        snapshot_path=seal.artifact_root / "invented-snapshot.json",
        manifest_path=seal.artifact_root / "invented-manifest.json",
        snapshot_sha256="0" * 64,
        manifest_sha256="f" * 64,
        snapshot_bytes=b"invented",
        manifest_bytes=b"invented",
        rows=(),
        writers_closed=False,
        sha256_identities=(),
        sealed_files=(),
    )
    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(untrusted, design)
    assert failure is None
    assert len(witnesses) == 3
    assert equality == {"join": True, "leave": False, "rejoin": True}
    assert d_fraction == Fraction(1, 4) and d_decimal == Decimal("0.25")


def test_all_three_pairs_are_attempted_without_early_stop_and_D_is_withheld_on_incomplete(tmp_path: Path, immutable_inputs) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "noncanonical")

    rows = json.loads(canonical_json_bytes(seal.rows))
    rows[0]["canonical_object"].pop("memory_rule")
    witnesses, equality, d_fraction, d_decimal, failure = _compare_validated_rows(rows, design)
    assert [item.pair for item in witnesses] == ["join", "leave", "rejoin"]
    assert [item.status for item in witnesses] == ["NONCANONICAL", "COMPLETE", "COMPLETE"]
    assert equality is None and d_fraction is None and d_decimal is None
    assert failure["code"] == "PAIR_WITNESS_INCOMPLETE_OR_NONCANONICAL"


def test_duplicate_sealed_row_identity_never_defaults_or_aggregates_D(tmp_path: Path, immutable_inputs) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "duplicate")

    def duplicate_first_identity(snapshot):
        snapshot["rows"][2]["cell"] = "k_join"
        snapshot["rows"][2]["canonical_object"]["cell"] = "k_join"

    duplicate = _replace_snapshot(seal, duplicate_first_identity)
    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(duplicate, design)
    assert witnesses == ()
    assert equality is None and d_fraction is None and d_decimal is None
    assert failure["code"] == "SEALED_ARTIFACT_INTEGRITY_INVALID"


def test_phase2_never_reinvokes_or_recompiles(tmp_path: Path, immutable_inputs, monkeypatch) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "phase2-no-calls")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Phase 2 must not invoke construction entry points")

    monkeypatch.setattr(census_module, "map_ec4g", forbidden)
    monkeypatch.setattr(census_module, "map_direct_tau", forbidden)
    monkeypatch.setattr(census_module, "compile_gamma", forbidden)
    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(seal, design)
    assert failure is None
    assert len(witnesses) == 3 and len(equality) == 3
    assert str(d_fraction) == "1/4" and str(d_decimal) == "0.25"


def _stdlib_external_artifact_validator(root: Path, c0_bytes: bytes, c1_bytes: bytes):
    """Independent consumer: stdlib only, with no census construction/equality helpers."""

    def encoded(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    files = tuple(sorted(path for path in root.iterdir() if path.is_file()))
    snapshots = tuple(path for path in files if path.name.startswith("snapshot-"))
    manifests = tuple(path for path in files if path.name.startswith("manifest-"))
    assert len(snapshots) == len(manifests) == 1
    snapshot_path, manifest_path = snapshots[0], manifests[0]
    snapshot_bytes = snapshot_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    snapshot_digest = hashlib.sha256(snapshot_bytes).hexdigest()
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    assert snapshot_path.name == f"snapshot-{snapshot_digest}.json"
    assert manifest_path.name == f"manifest-{manifest_digest}.json"
    snapshot = json.loads(snapshot_bytes)
    manifest = json.loads(manifest_bytes)
    assert snapshot_bytes == encoded(snapshot) + b"\n"
    assert manifest_bytes == encoded(manifest) + b"\n"
    assert snapshot["row_schema"] == list(ROW_SCHEMA)
    assert manifest["snapshot_file"] == snapshot_path.name
    assert manifest["snapshot_sha256"] == snapshot_digest
    expected_order = [[cell, map_name] for cell in CELL_ORDER for map_name in MAP_ORDER]
    assert manifest["row_order"] == expected_order
    assert manifest["row_count"] == len(snapshot["rows"]) == 6

    expected_files = {snapshot_path.name, manifest_path.name}
    identities = [hashlib.sha256(c0_bytes).hexdigest(), hashlib.sha256(c1_bytes).hexdigest()]
    assert identities == [C0_SHA256, C1_SHA256]
    rows = snapshot["rows"]
    for ordinal, (row, expected) in enumerate(zip(rows, expected_order, strict=True)):
        cell, map_identity = expected
        assert set(row) == set(ROW_SCHEMA)
        assert [row["cell"], row["map_identity"]] == expected
        assert row["ordinal"] == ordinal
        object_name = f"{ordinal:02d}_{cell}_{map_identity}.object.json"
        receipt_name = f"{ordinal:02d}_{cell}_{map_identity}.receipt.json"
        expected_files.update((object_name, receipt_name))
        object_bytes = (root / object_name).read_bytes()
        receipt_bytes = (root / receipt_name).read_bytes()
        object_document = json.loads(object_bytes)
        receipt_document = json.loads(receipt_bytes)
        assert object_bytes == encoded(object_document) + b"\n"
        assert receipt_bytes == encoded(receipt_document) + b"\n"
        assert object_document == row["canonical_object"]
        assert receipt_document == row["construction_receipt"]
        assert set(object_document) == set(COMPARED_FIELDS + EXCLUDED_FIELDS)
        object_digest = hashlib.sha256(encoded(object_document)).hexdigest()
        identities.append(object_digest)
        assert row["object_sha256"] == receipt_document["object_sha256"] == object_digest
        assert manifest["row_object_sha256"][ordinal] == object_digest
    assert {path.name for path in files} == expected_files
    identities.extend((snapshot_digest, manifest_digest))
    assert len(identities) == 10 and len(set(identities)) == 10

    witnesses = []
    equality = {}
    for label, cell in zip(("join", "leave", "rejoin"), CELL_ORDER, strict=True):
        left, right = [row for row in rows if row["cell"] == cell]
        assert left["map_identity"] == "M_E" and right["map_identity"] == "M_D"
        assert left["canonical_object"]["map_identity"] != right["canonical_object"]["map_identity"]
        left_projection = {name: left["canonical_object"][name] for name in COMPARED_FIELDS}
        right_projection = {name: right["canonical_object"][name] for name in COMPARED_FIELDS}
        assert not (set(EXCLUDED_FIELDS) & set(left_projection))
        assert not (set(EXCLUDED_FIELDS) & set(right_projection))
        equal = encoded(left_projection) == encoded(right_projection)
        equality[label] = equal
        witnesses.append((label, equal, tuple(COMPARED_FIELDS), tuple(EXCLUDED_FIELDS)))
    masses = (Fraction(1, 2), Fraction(1, 4), Fraction(1, 4))
    d_fraction = sum(
        (mass for mass, label in zip(masses, ("join", "leave", "rejoin"), strict=True) if not equality[label]),
        Fraction(0, 1),
    )
    d_decimal = Decimal(d_fraction.numerator) / Decimal(d_fraction.denominator)
    return identities, witnesses, equality, d_fraction, d_decimal


def test_stdlib_external_artifact_validator_rederives_complete_claim_without_helpers(
    tmp_path: Path, immutable_inputs, monkeypatch
) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "external-validator")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("external validator must not call census helpers")

    monkeypatch.setattr(census_module, "map_ec4g", forbidden)
    monkeypatch.setattr(census_module, "map_direct_tau", forbidden)
    monkeypatch.setattr(census_module, "compile_gamma", forbidden)
    monkeypatch.setattr(census_module, "_compare_validated_rows", forbidden)
    identities, witnesses, equality, d_fraction, d_decimal = _stdlib_external_artifact_validator(
        seal.artifact_root, *immutable_inputs
    )
    assert len(identities) == 10
    assert [item[0] for item in witnesses] == ["join", "leave", "rejoin"]
    assert all(item[2] == tuple(COMPARED_FIELDS) and item[3] == tuple(EXCLUDED_FIELDS) for item in witnesses)
    assert equality == {"join": True, "leave": False, "rejoin": True}
    assert d_fraction == Fraction(1, 4) and d_decimal == Decimal("0.25")


def test_equality_compares_canonical_fields_not_supplied_hashes(tmp_path: Path, immutable_inputs) -> None:
    authenticated = authenticate_immutable_inputs(*immutable_inputs)
    design = freeze_design(SOURCE_REVISION)
    seal = materialize_and_seal_phase1(authenticated, design, tmp_path / "hash-collision")

    rows = json.loads(canonical_json_bytes(seal.rows))
    left, right = rows[0], rows[1]
    right["object_sha256"] = left["object_sha256"]
    right["construction_receipt"]["object_sha256"] = left["object_sha256"]
    right["canonical_object"]["primitive_actions"] = ["different-complete-program"]
    witnesses, equality, d_fraction, d_decimal, failure = _compare_validated_rows(rows, design)
    assert failure is None
    assert witnesses[0].exact_equal is False
    assert equality == {"join": False, "leave": False, "rejoin": True}
    assert str(d_fraction) == "3/4" and str(d_decimal) == "0.75"


def test_existing_artifact_root_refuses_overwrite_before_any_map_call(tmp_path: Path, immutable_inputs) -> None:
    root = tmp_path / "existing"
    root.mkdir()
    marker = root / "keep.txt"
    marker.write_text("unchanged", encoding="utf-8")
    calls: list[str] = []

    def forbidden(*_args):
        calls.append("called")
        raise AssertionError("must not run")

    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=root,
        source_revision=SOURCE_REVISION,
        run_id="overwrite",
        components=ExecutionComponents(forbidden, forbidden, forbidden),
    )
    assert result.terminal_branch is CensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID
    assert calls == []
    assert marker.read_text(encoding="utf-8") == "unchanged"


def test_result_has_no_future_publication_identity_and_is_byte_stable(tmp_path: Path, immutable_inputs) -> None:
    result = run_two_phase_census(
        *immutable_inputs,
        artifact_root=tmp_path / "stable",
        source_revision=SOURCE_REVISION,
        run_id="stable",
    )
    payload = result.payload()
    assert payload["source_identities"]["result_revision"] is None
    assert payload["operator_receipt"]["status"] == "not_invoked_by_source"
    assert payload["phase_1_seal"]["status"] == "independently_recomputed_and_validated"
    assert len(payload["phase_1_seal"]["sha256_identities"]) == 10
    assert result.to_bytes() == canonical_json_bytes(payload)
    assert b"predicted_D_RER3" not in result.to_bytes()
    assert tuple(result.design_freeze.compared_fields) == COMPARED_FIELDS
