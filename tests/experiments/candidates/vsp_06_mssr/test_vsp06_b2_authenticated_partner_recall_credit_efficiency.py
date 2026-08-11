"""Synthetic, noncanonical proof-sized checks for the VSP06-B2 candidate."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from experiments.candidates.vsp_06_mssr import (
    vsp06_b2_authenticated_partner_recall_credit_efficiency as b2,
)
from scripts import run_vsp06_b2_authenticated_partner_recall_credit_efficiency as runner
from experiments.candidates.vsp_06_mssr import (
    vsp06_b2_independent_exact_manifest_verifier as verifier,
)
from experiments.candidates.vsp_06_mssr import (
    vsp06_b2_source_bound_exact_feasibility as selector,
)


REPO = Path(__file__).resolve().parents[4]
TEST_ROOT = REPO / "temp/sessions/code_project_manager/vsp06_b2_source_bound_exact_feasibility_credit_efficiency/implementation-tests"
LEDGER_PATH = REPO / "docs/research/candidates/vsp_06_mssr/VSP06_B2_CONSTRAINT_TARGET_LEDGER_V1.json"
SELECTOR_PATH = REPO / "experiments/candidates/vsp_06_mssr/vsp06_b2_source_bound_exact_feasibility.py"
VERIFIER_PATH = REPO / "experiments/candidates/vsp_06_mssr/vsp06_b2_independent_exact_manifest_verifier.py"
RUNNER_PATH = REPO / "scripts/run_vsp06_b2_authenticated_partner_recall_credit_efficiency.py"


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _long_path(path: Path) -> Path:
    resolved = path.resolve()
    if sys.platform == "win32":
        return Path("\\\\?\\" + str(resolved))
    return resolved


@pytest.fixture
def output_root() -> Path:
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="synthetic_", dir=TEST_ROOT))


def _row(y: int, nonce: int) -> dict:
    return {
        "consumer": "final_keep",
        "seed_row": "primary_1",
        "panel": "4096_keep_extra",
        "branch": "KEEP",
        "retention_length": 6,
        "y": y,
        "reset_y": 0,
        "target_identity": 0,
        "target_version": 1,
        "event_type": "target_absent_payload",
        "decoy_sequence": [[0, 0, 1, False], [1, 1, 2, True], [2, 2, 3, False], [3, 3, 0, True]],
        "current_bytes": "synthetic-identical-current",
        "roster": "P0,P1,P2,P3,focal",
        "legal_mask": "1111",
        "clock": "L=6",
        "rng_binding": "synthetic-identical-rng",
        "quartet_base": "synthetic_q0000",
        "nonce": nonce,
    }


def _with_split(row: dict, split: str) -> dict:
    for nonce in range(10000):
        candidate = {**row, "nonce": nonce}
        payload = selector.canonical_tuple_bytes(candidate)
        if selector.split_for_bucket(selector.bucket_for_tuple(payload)) == split:
            return candidate
    raise AssertionError(f"synthetic nonce domain did not reach {split}")


def _synthetic_catalog_rows() -> list[dict]:
    rows = [_with_split(_row(y, 0), "evaluation") for y in range(4)]
    primary = _row(0, 0)
    primary.update({
        "consumer": "primary_fit", "seed_row": "primary_1", "panel": "fit",
        "branch": "KEEP", "retention_length": 4, "quartet_base": "synthetic_primary",
    })
    calibration_fit = _row(1, 0)
    calibration_fit.update({
        "consumer": "calibration_fit", "seed_row": "calibration", "panel": "fit",
        "branch": "CURRENT", "retention_length": 4, "quartet_base": "synthetic_cal_fit",
    })
    calibration_check = _row(2, 0)
    calibration_check.update({
        "consumer": "calibration_check", "seed_row": "calibration", "panel": "check",
        "branch": "CURRENT", "retention_length": 4, "quartet_base": "synthetic_cal_check",
    })
    checkpoint = _row(2, 0)
    checkpoint.update({
        "consumer": "checkpoint", "seed_row": "primary_1", "panel": "0",
        "branch": "RESET", "retention_length": 6, "reset_y": 3,
        "target_identity": 2, "event_type": "renewal_marker",
        "quartet_base": "synthetic_checkpoint",
    })
    rows.extend([
        _with_split(primary, "train"),
        _with_split(calibration_fit, "calibration"),
        _with_split(calibration_check, "calibration"),
        _with_split(checkpoint, "evaluation"),
    ])
    return rows


FAMILIES = (
    "split_bucket_disjointness",
    "primary_counts",
    "calibration_counts",
    "checkpoint_counts",
    "y_conditional_marginals",
    "keep_quartets",
    "anti_lookup_coverage",
    "structural_eligibility",
    "reset_fresh_y_independence",
)


def _ledger(bad_family: str | None = None) -> dict:
    predicates = {
        "split_bucket_disjointness": ({"eq": {"split": "train"}}, 1),
        "primary_counts": ({"eq": {"consumer": "primary_fit", "branch": "KEEP", "retention_length": 4, "y": 0}}, 1),
        "calibration_counts": ({"eq": {"consumer": "calibration_fit", "y": 1}}, 1),
        "checkpoint_counts": ({"eq": {"consumer": "checkpoint", "branch": "RESET", "y": 2}}, 1),
        "y_conditional_marginals": ({"eq": {"consumer": "final_keep", "y": 3, "target_version": 1}}, 1),
        "keep_quartets": ({"eq": {"consumer": "final_keep"}}, 4),
        "anti_lookup_coverage": ({"eq": {"target_identity": 2, "event_type": "renewal_marker"}}, 1),
        "structural_eligibility": ({"eq": {"consumer": "calibration_check", "panel": "check", "retention_length": 4}}, 1),
        "reset_fresh_y_independence": ({"eq": {"consumer": "checkpoint", "branch": "RESET", "y": 2, "reset_y": 3}}, 1),
    }
    templates = []
    for family, (predicate, rhs) in predicates.items():
        templates.append({
            "name_template": f"synthetic/{family}/actual_predicate",
            "family": family, "axes": {},
            "terms": [{"coefficient": 1, "predicate": predicate}],
            "rhs": rhs + 1 if family == bad_family else rhs,
        })
    body = {
        "ledger_id": selector.LEDGER_ID,
        "equation_semantics": "sum(integer_coefficient * selected_row_indicator) == integer_rhs",
        "equation_templates": templates,
        "family_counts": {family: 1 for family in FAMILIES},
    }
    return {**body, "ledger_digest": _digest(_json_bytes(body))}


def _write_json(path: Path, value) -> None:
    path.write_bytes(_json_bytes(value) + b"\n")


def _package(root: Path, bad_family: str | None = None) -> dict[str, Path]:
    catalog_path = root / "catalog.json"
    ledger_path = root / "ledger.json"
    witness_path = root / "witness.json"
    manifest_path = root / "manifest.json"
    bindings_path = root / "bindings.json"
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": _synthetic_catalog_rows()}
    ledger = _ledger(bad_family)
    _write_json(catalog_path, catalog)
    _write_json(ledger_path, ledger)
    rows = selector.parse_catalog(catalog)
    vector = [1] * len(rows)
    witness = {
        "selector_identity": selector.SELECTOR_ID,
        "membership_vector": vector,
        "membership_vector_sha256": _digest(_json_bytes(vector)),
    }
    expected = {
        "selector_source_sha256": selector.sha256_file(SELECTOR_PATH),
        "verifier_source_sha256": selector.sha256_file(VERIFIER_PATH),
        "catalog_sha256": selector.sha256_file(catalog_path),
        "ledger_sha256": selector.sha256_file(ledger_path),
        "python_implementation": "CPython",
        "python_version": "synthetic-only-not-live",
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_sha256": selector.sha256_file(Path(sys.executable).resolve()),
        "ortools_version": selector.REQUIRED_ORTOOLS,
        "ortools_source_tag": "v9.12",
        "solver_artifacts": [],
        "solver_artifact_set_sha256": "synthetic-only-not-live",
        "sat_parameters_sha256": "synthetic-only-not-live",
        "sat_parameters_hex": "synthetic-only-not-live",
        "sat_parameter_assignments": dict(selector.PARAMETER_ASSIGNMENTS),
        "sat_parameter_assignments_sha256": _digest(_json_bytes(selector.PARAMETER_ASSIGNMENTS)),
        "os": "synthetic",
        "os_release": "synthetic",
        "architecture": "synthetic",
    }
    selected_rows = [
        {"tuple": dict(row.tuple_value), "tuple_sha256": row.tuple_sha256, "bucket": row.bucket, "split": row.split}
        for row in rows
    ]
    manifest = {
        "manifest_id": "vsp06_b2_authenticated_partner_recall_manifest_v1",
        "treatment": selector.TREATMENT_ID,
        "selector_identity": selector.SELECTOR_ID,
        "bindings": expected,
        "selected_count": len(rows),
        "selected_rows": selected_rows,
        "common_two_arm_order_digest": _digest(_json_bytes([row["tuple_sha256"] for row in selected_rows])),
        "rank_claim": False,
    }
    _write_json(witness_path, witness)
    _write_json(manifest_path, manifest)
    _write_json(bindings_path, {
        "selector_path": str(SELECTOR_PATH),
        "verifier_path": str(VERIFIER_PATH),
        "synthetic_only": True,
        "expected": expected,
    })
    return {
        "catalog_path": catalog_path, "ledger_path": ledger_path,
        "witness_path": witness_path, "manifest_path": manifest_path,
        "bindings_path": bindings_path,
    }


def test_import_safe_dependency_gate_has_no_fallback() -> None:
    with pytest.raises(selector.SelectorInvalid, match=r"CPython 3\.11 ABI is required|ortools==9\.12\.4544 is not installed"):
        selector.selector_environment()
    source = SELECTOR_PATH.read_text(encoding="utf-8")
    assert "for replica_index in (1, 2)" in source
    assert "replica_2_role" in source
    assert "fallback" not in source.lower()


def test_canonical_tuple_serializer_bucket_split_and_uniqueness() -> None:
    row = _row(0, 7)
    assert selector.canonical_tuple_bytes(row) == selector.canonical_tuple_bytes(dict(reversed(list(row.items()))))
    bucket = selector.bucket_for_tuple(selector.canonical_tuple_bytes(row))
    assert bucket in range(8)
    assert selector.split_for_bucket(bucket) in {"train", "calibration", "evaluation"}
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": [row, _row(1, 7)]}
    assert len(selector.parse_catalog(catalog)) == 2
    catalog["rows"].append(dict(row))
    with pytest.raises(selector.SelectorInvalid, match="not unique"):
        selector.parse_catalog(catalog)


def test_frozen_integer_ledger_digest_and_expanded_family_counts() -> None:
    raw = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    equations = selector.parse_ledger(raw)
    observed = {}
    for equation in equations:
        assert isinstance(equation["rhs"], int) and not isinstance(equation["rhs"], bool)
        assert all(isinstance(term["coefficient"], int) and not isinstance(term["coefficient"], bool) for term in equation["terms"])
        observed[equation["family"]] = observed.get(equation["family"], 0) + 1
    assert observed == raw["family_counts"]
    assert set(observed) == set(FAMILIES)
    by_name = {equation["name"]: equation for equation in equations}
    assert by_name["primary/primary_1/reset/length/4/y/0"]["rhs"] == 64
    assert by_name["checkpoint/primary_1/0/reset/y/0"]["rhs"] == 8
    assert by_name["calibration/fit/y/0"]["rhs"] == 128
    assert by_name["fresh_reset/primary/primary_1/length/4/y/0/reset_y/0"]["rhs"] == 16
    assert by_name["fresh_reset/checkpoint/primary_1/0/y/0/reset_y/0"]["rhs"] == 2
    assert by_name["fresh_reset/primary/primary_1/length/4/reset_y/0/version/0"]["rhs"] == 16
    assert any(
        name.startswith("fresh_reset/checkpoint/primary_1/0/reset_y/0/decoy/")
        and equation["rhs"] == 2
        for name, equation in by_name.items()
    )
    assert any(
        equation["name"].startswith("marginal/calibration/")
        and "/decoy/" in equation["name"]
        for equation in equations
    )
    assert any(
        equation["name"].startswith("marginal/final/")
        and "/decoy/" in equation["name"]
        for equation in equations
    )


def _noncanonical_final_keep_mirror() -> list[dict]:
    generated = []
    events = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")
    decoys = b2._decoy_patterns()
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for quartet in range(64):
            identity = quartet % 4
            version = (quartet // 4) % 4
            event = (quartet // 16) % 4
            decoy = (identity + version + event) % 4
            for y in range(4):
                row = _row(y, 0)
                row.update({
                    "seed_row": seed, "target_identity": identity,
                    "target_version": version, "event_type": events[event],
                    "decoy_sequence": [list(item) for item in decoys[decoy]],
                    "quartet_base": f"synthetic_mirror_{seed}_{quartet}",
                    "current_bytes": f"synthetic_current_{seed}_{quartet}",
                    "rng_binding": f"synthetic_rng_{seed}_{quartet}",
                })
                generated.append(_with_split(row, "evaluation"))
    return generated


def test_noncanonical_final_keep_mirror_support_rejects_all_identity_zero() -> None:
    generated = _noncanonical_final_keep_mirror()
    parsed = selector.parse_catalog({
        "catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": generated,
    })
    report = selector.validate_final_keep_support(parsed)
    assert report["selected_count_required"] == 1024
    assert report["quartet_count"] == 256
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        rows = [row for row in generated if row["seed_row"] == seed]
        assert {value: sum(row["target_identity"] == value for row in rows) for value in range(4)} == {0: 64, 1: 64, 2: 64, 3: 64}

    wrong = []
    for row in generated:
        mutated = {**row, "target_identity": 0}
        wrong.append(_with_split(mutated, "evaluation"))
    wrong_parsed = selector.parse_catalog({
        "catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": wrong,
    })
    with pytest.raises(selector.SelectorInvalid, match="target_identity support is not exactly balanced"):
        selector.validate_final_keep_support(wrong_parsed)


def test_multi_witness_decision_envelope_and_replica_gate() -> None:
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": [_row(0, 3), _row(1, 4)]}
    rows = selector.parse_catalog(catalog)
    order = selector.canonical_order(rows)
    assert order == selector.canonical_order(rows)
    first = {
        "selector_identity": selector.SELECTOR_ID, "terminal_status": "FEASIBLE",
        "membership_vector": [1, 0], "membership_vector_sha256": "a",
        "selected_tuple_sha256": [rows[0].tuple_sha256], "manifest": {"witness": 1},
        "manifest_sha256": "b",
    }
    assert selector.compare_replicas(first, dict(first))["membership_vector"] == [1, 0]
    alternate = dict(first, membership_vector=[0, 1])
    with pytest.raises(selector.SelectorInvalid, match="replicas disagree"):
        selector.compare_replicas(first, alternate)


def test_independent_verifier_complete_mapping_and_family_report(output_root: Path) -> None:
    paths = _package(output_root)
    report = verifier.verify(**paths)
    assert report["verdict"] == "SYNTHETIC_STRUCTURAL_VALID_ONLY"
    assert report["synthetic_only"] is True
    assert report["selected_count"] == 8
    assert set(report["constraint_families"]) == set(FAMILIES)
    assert report["global_rank_claim"] is False


def test_synthetic_fixture_cannot_become_canonical_verified(output_root: Path) -> None:
    paths = _package(output_root)
    bindings = json.loads(paths["bindings_path"].read_text())
    bindings["synthetic_only"] = False
    _write_json(paths["bindings_path"], bindings)
    with pytest.raises(
        verifier.VerificationError,
        match=r"canonical constraint-family counts mismatch|live CPython 3\.11|live ortools==9\.12\.4544 is absent",
    ):
        verifier.verify(**paths)


def test_synthetic_verified_envelope_cannot_admit_registered_full(output_root: Path) -> None:
    package_root = output_root / "package"
    package_root.mkdir()
    paths = _package(package_root)
    report = verifier.verify(**paths)
    # Keep the exact artifact names while staying below legacy Windows path limits.
    session = _long_path(TEST_ROOT / f"gate_{output_root.name[-8:]}")
    selector_root = session / "selector"
    selector_root.mkdir(parents=True)
    manifest_path = session / "frozen_manifest.json"
    catalog_path = session / "canonical_catalog.json"
    bindings_path = selector_root / "frozen_bindings.json"
    witness_path = selector_root / "membership_witness.json"
    report_path = selector_root / "independent_verifier_report.json"
    receipt_path = selector_root / "selector_success_receipt.json"
    manifest = json.loads(paths["manifest_path"].read_text())
    for destination, source in (
        (manifest_path, paths["manifest_path"]),
        (catalog_path, paths["catalog_path"]),
        (bindings_path, paths["bindings_path"]),
        (witness_path, paths["witness_path"]),
    ):
        destination.write_bytes(source.read_bytes())
    _write_json(report_path, report)
    content_digest = _digest(_json_bytes(manifest))
    receipt = {
        "branch": selector.VALID,
        "replica_count": 2,
        "replica_2_role": "prospective_determinism_gate_not_retry",
        "catalog_path": str(catalog_path.resolve()),
        "catalog_sha256": selector.sha256_file(catalog_path),
        "ledger_path": str(paths["ledger_path"].resolve()),
        "ledger_sha256": selector.sha256_file(paths["ledger_path"]),
        "bindings_path": str(bindings_path.resolve()),
        "bindings_sha256": selector.sha256_file(bindings_path),
        "witness_path": str(witness_path.resolve()),
        "witness_sha256": selector.sha256_file(witness_path),
        "manifest_path": str(manifest_path.resolve()),
        "manifest_file_sha256": selector.sha256_file(manifest_path),
        "manifest_content_sha256": content_digest,
        "verifier_report_path": str(report_path.resolve()),
        "verifier_report_sha256": selector.sha256_file(report_path),
    }
    _write_json(receipt_path, receipt)
    manifest_path.chmod(0o444)
    with pytest.raises(b2.B2ContractError, match="synthetic or incomplete binding"):
        b2.ManifestGate(
            manifest_path, content_digest, session_root=session,
            selector_receipt_path=receipt_path,
            verifier_report_path=report_path,
        )


def test_stdlib_sat_parameter_wire_binding_rejects_arbitrary_self_consistent_bytes() -> None:
    frozen = verifier._expected_sat_parameter_bytes()
    assert frozen
    assert _digest(frozen) != _digest(b"arbitrary-self-consistent-parameters")
    assert bytes.fromhex(frozen.hex()) == frozen
    changed = bytearray(frozen)
    changed[-1] ^= 1
    assert bytes(changed) != verifier._expected_sat_parameter_bytes()


@pytest.mark.parametrize("family", FAMILIES)
def test_independent_verifier_rejects_each_constraint_family_corruption(output_root: Path, family: str) -> None:
    paths = _package(output_root, bad_family=family)
    with pytest.raises(verifier.VerificationError, match="integer equation mismatch"):
        verifier.verify(**paths)


def test_independent_verifier_rejects_partial_witness_and_mutated_manifest(output_root: Path) -> None:
    paths = _package(output_root)
    witness = json.loads(paths["witness_path"].read_text())
    witness["membership_vector"] = witness["membership_vector"][:-1]
    _write_json(paths["witness_path"], witness)
    with pytest.raises(verifier.VerificationError, match="partial/nonbinary"):
        verifier.verify(**paths)

    other = output_root / "mutated"
    other.mkdir()
    paths = _package(other)
    manifest = json.loads(paths["manifest_path"].read_text())
    manifest["selected_rows"][0]["tuple"]["current_bytes"] = "mutated"
    _write_json(paths["manifest_path"], manifest)
    with pytest.raises(verifier.VerificationError, match="mapping mismatch"):
        verifier.verify(**paths)


def test_independent_source_has_no_selector_ortools_or_shared_helper_import() -> None:
    tree = ast.parse(VERIFIER_PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.startswith("ortools") or name.startswith("experiments") for name in imports)


def test_write_once_and_preexisting_manifest_fail_before_dependency(output_root: Path) -> None:
    destination = output_root / "write_once.json"
    selector.write_exclusive(destination, b"first")
    with pytest.raises(selector.SelectorInvalid, match="already exists"):
        selector.write_exclusive(destination, b"second")
    manifest = output_root / "preexisting_manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(selector.SelectorInvalid, match="already exists"):
        selector.run_two_replica_sequence(
            catalog_path=output_root / "absent_catalog.json",
            ledger_path=output_root / "absent_ledger.json",
            manifest_path=manifest,
            verifier_path=VERIFIER_PATH,
            work_root=output_root / "selector_work",
        )


def _spec(branch: str = "KEEP", y: int = 2, reset_y: int = 1) -> b2.EpisodeSpec:
    row = _row(y, 0)
    row.update({"consumer": "synthetic_noncanonical", "seed_row": "synthetic", "panel": "synthetic", "branch": branch, "retention_length": 4, "reset_y": reset_y})
    return b2.EpisodeSpec.from_manifest_row(row)


def test_toy_authenticated_keep_reset_current_semantics_and_terminal_reward() -> None:
    toy = b2.AuthenticatedPartnerRecallRelay()
    keep = toy.build(_spec("KEEP", y=2))
    reset = toy.build(_spec("RESET", y=2, reset_y=1))
    current = toy.build(_spec("CURRENT", y=2))
    assert [step.write for step in keep.steps].count(1) == 1
    assert keep.terminal_target == 2
    assert reset.terminal_target == 1 and reset.steps[-2].reset == 1 and reset.steps[-2].write == 1
    assert current.terminal_target == 2 and current.steps[-2].write == 1
    assert b2.terminal_reward(2, 2) == 1 and b2.terminal_reward(1, 2) == -1
    assert all(len(step.observation) == b2.OBSERVATION_DIM for step in keep.steps)


def test_arm_shapes_counts_initialization_exposure_and_gradient_boundary() -> None:
    torch = pytest.importorskip("torch")
    candidate, generic = b2.paired_models("primary_1")
    assert b2.trainable_contract(candidate) == b2.trainable_contract(generic)
    specs = [_spec("KEEP", y=0), _spec("KEEP", y=1)]
    observations, writes, resets, _targets, _episodes = b2.tensor_batch(specs)
    assert torch.equal(observations, observations.clone())
    for model in (candidate, generic):
        logits, values, _gates = model.episode(observations, writes, resets)
        (logits.sum() + values.sum()).backward()
    assert all(parameter.grad is None for parameter in candidate.routing_gate.parameters())
    assert all(parameter.grad is not None for parameter in generic.routing_gate.parameters())


def test_generic_reset_is_learned_from_visible_input_not_forced_external_oracle() -> None:
    torch = pytest.importorskip("torch")
    candidate, generic = b2.paired_models("primary_1")
    observation = torch.zeros(1, b2.OBSERVATION_DIM)
    state = (torch.zeros(1, b2.CONTEXT_DIM), torch.ones(1, b2.CARRIER_DIM))
    zero = torch.zeros(1, 1)
    one = torch.ones(1, 1)
    _logits, _value, candidate_keep, _route = candidate.step(observation, state, zero, zero)
    _logits, _value, candidate_reset, _route = candidate.step(observation, state, zero, one)
    assert not torch.equal(candidate_keep[1], candidate_reset[1])
    _logits, _value, generic_no_flag, _route = generic.step(observation, state, zero, zero)
    _logits, _value, generic_forced_flags, _route = generic.step(observation, state, one, one)
    assert torch.equal(generic_no_flag[1], generic_forced_flags[1])


def test_noncanonical_control_mirrors_reject_previous_wrong_pairings() -> None:
    keep = []
    for quartet in ("mirror_q0", "mirror_q1"):
        keep.extend(
            replace(_spec("KEEP", y=y), quartet_base=quartet, nonce=y)
            for y in b2.ACTIONS
        )
    indices = b2._cross_swap_indices(keep, expected_quartets=2)
    assert len(indices) == len(keep) and len(set(indices)) == len(keep)
    for destination, source in enumerate(indices):
        assert keep[destination].quartet_base == keep[source].quartet_base
        assert keep[destination].y != keep[source].y
    wrong_global_roll = tuple(range(1, len(keep))) + (0,)
    assert any(
        keep[destination].quartet_base != keep[source].quartet_base
        for destination, source in enumerate(wrong_global_roll)
    )

    current = [
        replace(
            _spec("CURRENT", y=y), consumer="checkpoint", panel="4096",
            quartet_base=f"mirror_current_{y}", nonce=y,
        )
        for y in b2.ACTIONS
    ]
    reset = [
        replace(
            _spec("RESET", y=y, reset_y=reset_y), consumer="checkpoint",
            panel="4096", quartet_base=f"mirror_reset_{y}_{reset_y}",
            nonce=y * 4 + reset_y,
        )
        for y in b2.ACTIONS for reset_y in b2.ACTIONS
    ]
    current_partition, changed_reset = b2._control_partitions(
        current + reset, expected_current=4, expected_reset=16,
        expected_changed_reset=12, expected_joint=1,
    )
    assert all(spec.branch == "CURRENT" for spec in current_partition)
    assert all(spec.reset_y != spec.y for spec in changed_reset)
    assert len(changed_reset) == 12
    with pytest.raises(b2.B2ContractError, match="cardinality"):
        b2._control_partitions(
            keep + reset, expected_current=4, expected_reset=16,
            expected_changed_reset=12, expected_joint=1,
        )


def test_aulc_and_fail_closed_precedence() -> None:
    assert b2.normalized_keep_aulc([0.25] * len(b2.CHECKPOINTS)) == 0.0
    evidence = {
        "contract_valid": True, "activity_nonzero": True, "caps_valid": True,
        "paired_exposure": True, "matched_shapes_counts_state": True,
        "terminal_ppo_only": True, "no_side_channel": True,
        "candidate_minus_generic_keep_aulc": 0.08,
        "candidate_final_keep": 0.55, "selected_p_mediation": 0.20,
        "cross_swap_follow_rate": 0.80, "candidate_decoy_accuracy_change": 0.02,
        "candidate_decoy_kernel_tv_change": -0.02, "current_arm_aulc_gap": 0.05,
        "reset_stale_target_rate": 0.15,
    }
    assert b2.classify_result(evidence) == b2.SUPPORTED
    evidence["contract_valid"] = False
    assert b2.classify_result(evidence) == b2.INVALID


def test_unique_registered_full_path_claims_before_activity_and_binds_exact_counts() -> None:
    runner_source = RUNNER_PATH.read_text(encoding="utf-8")
    assert 'sub.add_parser("run-full")' in runner_source
    assert "admit-full" not in runner_source
    source = inspect.getsource(b2.run_registered_full)
    assert source.index("selector.write_exclusive(claim_path") < source.index("paired_models(\"calibration\")")
    assert "gate.reload" in source
    assert "registered_full_failure.json" in source
    assert "retry_authorized\": False" in source
    assert b2.EXPECTED_FULL_ACTIVITY == {
        "model_fits": 10, "trainer_invocations": 10,
        "environment_episodes": 44288, "environment_transitions": 440320,
        "production_policy_forwards": 473280, "learner_updates": 1056,
        "optimizer_steps": 1056, "evaluator_calls": 74,
        "evaluation_episodes": 10496, "environment_rng_draws": 0,
        "action_rng_draws": 47584,
    }


def test_registered_full_missing_manifest_fails_before_claim(output_root: Path) -> None:
    session = output_root / "session"
    run_root = session / "registered_full"
    with pytest.raises(b2.B2ContractError, match="manifest is absent"):
        b2.run_registered_full(
            manifest_path=session / "frozen_manifest.json",
            manifest_content_digest="0" * 64,
            session_root=session,
            selector_receipt_path=session / "selector/selector_success_receipt.json",
            verifier_report_path=session / "selector/independent_verifier_report.json",
            run_root=run_root,
            result_path=output_root / "synthetic_result_must_not_exist.json",
        )
    assert not run_root.exists()


def test_cli_full_failure_classification_without_full_execution(output_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER_PATH), "run-full"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2 and completed.stdout == ""
    payload = json.loads(completed.stderr)
    assert payload["branch"] == runner.FULL_NOT_STARTED
    assert payload["failure_path"] is None and payload["activity_counts"] is None
    assert payload["branch"] != selector.INVALID

    synthetic_run = _long_path(output_root / "claimed")
    synthetic_run.mkdir()
    _write_json(synthetic_run / "registered_full_claim.json", {"claim": 1})
    activity = {"environment_episodes": 7, "optimizer_steps": 1}
    _write_json(synthetic_run / "registered_full_failure.json", {"activity_counts": activity})
    terminal = runner._full_failure_payload(RuntimeError("synthetic"), synthetic_run)
    assert terminal["branch"] == runner.FULL_TERMINAL
    assert terminal["activity_counts"] == activity
    assert terminal["failure_path"].endswith("registered_full_failure.json")


def test_registered_result_was_not_created() -> None:
    assert not (REPO / "docs/research/candidates/vsp_06_mssr/VSP06_B2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json").exists()
