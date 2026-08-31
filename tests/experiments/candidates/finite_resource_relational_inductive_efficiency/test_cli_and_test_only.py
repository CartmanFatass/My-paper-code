import json
from dataclasses import asdict

from experiments.candidates.finite_resource_relational_inductive_efficiency.cli import (
    EXIT_MISSING_NATIVE_BACKEND,
    main,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import NativeContract
from experiments.candidates.finite_resource_relational_inductive_efficiency.runner import run_test_only_chain


def test_describe_is_structural_and_value_blind(capsys):
    assert main(["describe"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["production_native_backend_bundled"] is False
    assert "thresholds" not in value


def test_tiny_chain_is_unmistakably_test_only():
    result = run_test_only_chain(steps=2)
    assert result["TEST_ONLY"] is True and result["production_admissible"] is False


def test_check_reads_only_direct_structures_and_reports_native_absent(manifest_factory, tmp_path):
    manifest = manifest_factory()
    packet = {
        "schema": core.FRRIE_SEALED_SEED_PACKET_V1,
        "manifest_contract": core.manifest_packet_contract(manifest),
        "blocks": manifest["seed_blocks"],
        "sealed_payload": {block: "TEST_ONLY_OPAQUE" for block in manifest["seed_blocks"]},
        "sealed": True,
        "complete": True,
    }
    native = NativeContract(
        core.HOST_ID, core.SOURCE_ID, core.NATIVE_COMPONENT, core.NATIVE_ABI,
        "FRRIE_NATIVE_CTYPES_V1", 8, 1, 1,
    )
    preflight = {
        "schema": "FRRIE_NATIVE_PREFLIGHT_V1",
        "ok": True,
        "fresh": True,
        "complete": True,
        "native_contract": asdict(native),
        "resource_ceiling": manifest["resource_ceiling"],
    }
    packet_path = tmp_path / "packet.json"
    preflight_path = tmp_path / "preflight.json"
    manifest_path = tmp_path / "manifest.json"
    output_path = tmp_path / "check.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["check", "--manifest", str(manifest_path), "--output", str(output_path)]) == EXIT_MISSING_NATIVE_BACKEND
    facts = json.loads(output_path.read_text(encoding="utf-8"))
    assert facts["contract_valid"] is True
    assert facts["native_callable_available"] is False
    assert facts["scientific_values_read"] is False
