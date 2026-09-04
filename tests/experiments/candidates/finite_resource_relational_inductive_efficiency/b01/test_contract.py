from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    CHECKPOINTS, REDUCTION_DTYPE, ROOT_LABELS, TRAIN_ROSTER_ORDER,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, bind_invocation_resource, named_compute_profile,
    validate_invocation_binding, validate_manifest, validate_test_manifest,
    validate_formal_source_gate,
)


def test_manifest_freezes_literal_b01_panel_and_named_compute_profile(b01_manifest):
    validated = validate_manifest(b01_manifest)
    science = validated["scientific_contract"]
    assert validated["seed_packet"]["contract"]["labels"] == list(ROOT_LABELS)
    assert science["train_roster_order"] == list(TRAIN_ROSTER_ORDER)
    assert science["checkpoints"] == list(CHECKPOINTS)
    assert science["checkpoint_randomness_role"] == "METADATA_ONLY"
    assert validated["compute"] == named_compute_profile()
    assert validated["compute"]["reduction_dtype"] == REDUCTION_DTYPE == "float64"


def test_formal_source_gate_reads_actual_head_and_blocks_scoped_uncommitted_drift(
    b01_manifest,
):
    import subprocess
    altered = deepcopy(b01_manifest)
    altered["code_revision"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    with pytest.raises(B01ContractError, match="BLOCKED_UNCOMMITTED"):
        validate_formal_source_gate(altered)


def test_formal_source_cli_exposes_same_fail_closed_gate(tmp_path, b01_manifest):
    import json
    import subprocess
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.cli import main
    altered = deepcopy(b01_manifest)
    altered["code_revision"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    path = (tmp_path / "formal-source-manifest.json").resolve()
    path.write_text(json.dumps(altered), encoding="utf-8")
    assert main(["formal-source-check", "--manifest", str(path)]) == 2


@pytest.mark.parametrize("field,value", [
    ("reduction_dtype", "float32"),
    ("native_width", 16),
    ("workers", 2),
    ("threads", 8),
])
def test_named_compute_profile_rejects_semantic_or_profile_alias(b01_manifest, field, value):
    altered = deepcopy(b01_manifest)
    altered["compute"][field] = value
    with pytest.raises(B01ContractError):
        validate_manifest(altered)


def test_root_bytes_require_unique_canonical_lowercase_hex(b01_manifest):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import validate_production_seed_packet
    packet = deepcopy(b01_manifest["seed_packet"]["contract"])
    packet["roots_hex"][0] = "ab" * 32
    assert validate_production_seed_packet(packet)["roots_hex"][0] == "ab" * 32
    uppercase = deepcopy(packet)
    uppercase["roots_hex"][0] = ("ab" * 32).upper()
    with pytest.raises(B01ContractError, match="canonical .*lowercase"):
        validate_production_seed_packet(uppercase)

    alias = deepcopy(packet)
    alias["roots_hex"][1] = alias["roots_hex"][0]
    with pytest.raises(B01ContractError, match="bytes must be unique"):
        validate_production_seed_packet(alias)

    whitespace = deepcopy(packet)
    whitespace["roots_hex"][0] = " " + whitespace["roots_hex"][0][1:]
    with pytest.raises(B01ContractError):
        validate_production_seed_packet(whitespace)


def test_each_invocation_binds_a_passing_four_gib_receipt(tmp_path):
    import json
    receipt = {
        "schema_version": 1,
        "captured_at": "2026-09-01T00:00:00Z",
        "assessed_at": "2026-09-01T00:00:01Z",
        "measurement_source": "TEST_ONLY_LITERAL",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 8 * 1024**3,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None,
        "effective_available_bytes": 7 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }
    path = (tmp_path / "receipt.json").resolve()
    path.write_text(json.dumps(receipt), encoding="utf-8")
    binding = bind_invocation_resource(
        invocation_id="FRRIE-B01-TEST-SMOKE-001", operation="TEST_SMOKE",
        receipt_path=path, receipt=receipt, test_only=True,
    )
    assert binding["receipt"] == receipt
    assert binding["test_only"] is True
    bad = dict(receipt, effective_available_bytes=3 * 1024**3)
    bad_path = (tmp_path / "bad.json").resolve()
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(B01ContractError, match="below 4 GiB"):
        bind_invocation_resource(
            invocation_id="x", operation="TEST_SMOKE",
            receipt_path=bad_path, receipt=bad, test_only=True,
        )
    wrong = deepcopy(binding)
    wrong["test_only"] = False
    with pytest.raises(B01ContractError, match="requires"):
        validate_invocation_binding(wrong)
    resume = deepcopy(binding)
    resume["operation"] = "RESUME"
    assert validate_invocation_binding(resume)["test_only"] is True


def test_extension_requires_parent_and_preserves_frozen_configuration(b01_manifest, tmp_path):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import manifest_template
    extension_roots = {
        key: str((tmp_path / "extension" / key).resolve())
        for key in ("output", "checkpoint", "scratch")
    }
    with pytest.raises(B01ContractError, match="parent_initial"):
        manifest_template(
            seed_packet_path=b01_manifest["seed_packet"]["path"],
            phase="EXTENSION_004_005", roots=extension_roots,
            compute=named_compute_profile(), code_revision="1" * 40,
        )
    import json
    parent_path = (tmp_path / "persisted-initial.json").resolve()
    parent_path.write_text(json.dumps(b01_manifest), encoding="utf-8")
    extension = manifest_template(
        seed_packet_path=b01_manifest["seed_packet"]["path"],
        phase="EXTENSION_004_005", roots=extension_roots,
        compute=named_compute_profile(), code_revision="1" * 40,
        parent_initial={"locator": str(parent_path), "manifest_contract": b01_manifest},
    )
    assert extension["execution_labels"] == list(ROOT_LABELS[3:])
    changed = deepcopy(extension)
    changed["compute"]["workers"] = 2
    with pytest.raises(B01ContractError):
        validate_manifest(changed)


def test_manifest_binds_exact_algorithm_and_full_code_revision(b01_manifest):
    altered = deepcopy(b01_manifest)
    altered["algorithm_contract"]["optimizer"]["learning_rate"] = 1e-3
    with pytest.raises(B01ContractError, match="algorithm/tuning"):
        validate_manifest(altered)
    shortened = deepcopy(b01_manifest)
    shortened["code_revision"] = "1" * 12
    with pytest.raises(B01ContractError, match="full 40-character"):
        validate_manifest(shortened)


def test_exact_optimizer_contract_binds_runtime_flags(b01_manifest):
    optimizer = b01_manifest["algorithm_contract"]["optimizer"]
    assert optimizer["maximize"] is False
    assert optimizer["capturable"] is False
    assert optimizer["differentiable"] is False
    assert optimizer["zero_grad_set_to_none"] is True
    altered = deepcopy(b01_manifest)
    altered["algorithm_contract"]["optimizer"]["maximize"] = True
    with pytest.raises(B01ContractError, match="algorithm/tuning"):
        validate_manifest(altered)


def test_test_manifest_records_base_commit_without_claiming_candidate_revision(b01_test_manifest):
    assert "code_revision" not in b01_test_manifest
    assert b01_test_manifest["source_state"] == {
        "base_commit": "1" * 40,
        "worktree_state": "DIRTY_UNCOMMITTED_TEST_ONLY",
    }
    altered = deepcopy(b01_test_manifest)
    altered["source_state"]["worktree_state"] = "CLEAN"
    with pytest.raises(B01ContractError, match="uncommitted TEST source"):
        validate_test_manifest(altered)
