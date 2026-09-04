import json
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency import cli
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core
from experiments.candidates.finite_resource_relational_inductive_efficiency.runner import (
    INFERENCE_BLOCKER as RUNNER_BLOCKER, ProductionTrainingUnavailable,
    guard_v2_production_run,
)


def _packet(manifest):
    return {
        "schema": core.FRRIE_SEALED_SEED_PACKET_V2,
        "version": 2,
        "manifest_contract": core.manifest_packet_contract(manifest),
        "blocks": manifest["seed_blocks"],
        "addressed_rng_roots": [f"{index:064x}" for index in range(1, 25)],
        "generation_provenance": "TEST_ONLY_DIRECT_PACKET",
        "no_prior_use": True,
        "sealed": True,
        "complete": True,
    }


def _write_manifest(manifest, path):
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_describe_is_v2_structural_and_value_blind(capsys):
    assert cli.main(["describe"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["schema"] == core.FRRIE_MANIFEST_V2
    assert value["production_native_source_bundled"] is True
    assert value["inference_ready"] is False
    assert "thresholds" not in value


def test_check_directly_validates_packet_and_publishes_prospective_v2(
    manifest_factory, tmp_path,
):
    manifest = manifest_factory()
    Path(manifest["sealed_seed_packet"]["path"]).write_text(
        json.dumps(_packet(manifest)), encoding="utf-8"
    )
    manifest_path = _write_manifest(manifest, tmp_path / "manifest.json")
    output = Path(manifest["preflight_receipt"]["path"])
    exit_code = cli.main([
        "check", "--manifest", str(manifest_path), "--output", str(output),
    ])
    assert exit_code in {
        cli.EXIT_MISSING_NATIVE_BACKEND, cli.EXIT_NATIVE_BUILD_REQUIRED,
        cli.EXIT_FAILED_PREFLIGHT, cli.EXIT_NOT_READY,
    }
    report = json.loads(output.read_text(encoding="ascii"))
    assert report["schema"] == "FRRIE_PROSPECTIVE_PREFLIGHT_V2"
    assert report["ready"] is False
    assert cli.INFERENCE_BLOCKER in report["blockers"]
    assert report["input"]["seed_packet_directly_bound"] is True
    assert report["fresh_roots"]["created"] is False
    assert report["scientific_activity_started"] is False
    # This is the newly generated receipt at the exactly bound path; no
    # prewritten receipt was read.
    assert output == Path(manifest["preflight_receipt"]["path"])


def test_check_rejects_unbound_receipt_location_before_publication(manifest_factory, tmp_path):
    manifest = manifest_factory()
    Path(manifest["sealed_seed_packet"]["path"]).write_text(
        json.dumps(_packet(manifest)), encoding="utf-8"
    )
    manifest_path = _write_manifest(manifest, tmp_path / "manifest.json")
    wrong = tmp_path / "unbound-preflight.json"
    assert cli.main([
        "check", "--manifest", str(manifest_path), "--output", str(wrong),
    ]) == cli.EXIT_INVALID_CONTRACT
    assert not wrong.exists()
    assert not Path(manifest["preflight_receipt"]["path"]).exists()


def test_run_refuses_exact_inference_blocker_before_root_or_output_binding(
    manifest_factory, tmp_path, capsys,
):
    manifest = manifest_factory()
    manifest_path = _write_manifest(manifest, tmp_path / "manifest.json")
    wrong_output = tmp_path / "deliberately-wrong"
    assert cli.main([
        "run", "--manifest", str(manifest_path),
        "--output-root", str(wrong_output),
    ]) == cli.EXIT_NOT_READY
    assert capsys.readouterr().err.strip() == cli.INFERENCE_BLOCKER
    assert not Path(manifest["roots"]["output"]).exists()
    assert not Path(manifest["roots"]["checkpoint"]).exists()
    assert not wrong_output.exists()


def test_runner_guard_compares_validated_exact_inference_record(manifest_factory):
    manifest = manifest_factory()
    with pytest.raises(ProductionTrainingUnavailable, match=f"^{RUNNER_BLOCKER}$"):
        guard_v2_production_run(manifest)


def test_v1_manifest_is_rejected_for_check_and_run(manifest_factory, tmp_path):
    manifest = manifest_factory()
    manifest["schema"] = core.FRRIE_MANIFEST_V1
    manifest_path = _write_manifest(manifest, tmp_path / "legacy.json")
    assert cli.main([
        "check", "--manifest", str(manifest_path),
        "--output", str(tmp_path / "out.json"),
    ]) == cli.EXIT_INVALID_CONTRACT
    assert cli.main([
        "run", "--manifest", str(manifest_path),
        "--output-root", manifest["roots"]["output"],
    ]) == cli.EXIT_INVALID_CONTRACT
