from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import cli
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    canonical_json_bytes, make_test_manifest, named_compute_profile,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.panel import validate_primitive_row
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.preflight import static_algorithm_receipt
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import create_test_seed_packet


def test_static_preflight_reads_actual_b01_and_reference_trainer_sources():
    receipt = static_algorithm_receipt()
    assert receipt["adam_before_projection"] is True
    assert receipt["full_batch_source_verified"] is True
    assert receipt["runtime_constants_verified"] is True


def test_primitive_row_recomputes_endpoint_and_requires_direct_counts():
    from experiments.candidates.finite_resource_relational_inductive_efficiency.host import native_endpoint

    row = {
        "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001", "arm": "PHY_TRUST",
        "checkpoint": 0, "roster": 6, "intervention": "INTACT", "episode": 0,
        "tape_binding": {
            "schema": "FRRIE_B01_EVALUATION_TAPE_V1",
            "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001", "roster": 6,
            "episode": 0, "checkpoint": 0, "checkpoint_role": "METADATA_ONLY",
            "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
            "arm_independent": True, "intervention_independent": True,
            "checkpoint_independent": True, "uniform_mapping": "TOP24 / 2**24",
        },
        "J": native_endpoint(2, 1, 0.25), "D_W": 2, "D_E": 1, "WASTE": 0.25,
        "role_action_counts": [[12, 12, 0, 0, 0, 0], [12, 12, 0, 0, 0, 0], [0, 0, 6, 6, 6, 6]],
        "successful_scan": 4, "successful_uplink": 3, "successful_receive": 2,
        "successful_delivery": 3, "expired": 1, "duplicate": 0,
        "collision": 1, "empty_radio": 2,
    }
    assert validate_primitive_row(
        row, seed_labels={"FRRIE-B01-TEST-ONLY-BLOCK-001"}, test_only=True,
    )["J"] == row["J"]


def test_cli_exposes_describe_check_and_test_smoke_but_no_production_run(capsys):
    parser = cli.parser()
    help_text = parser.format_help()
    assert "test-smoke" in help_text
    assert "describe" in help_text
    assert " run " not in help_text
    assert cli.main(["describe"]) == 0
    described = json.loads(capsys.readouterr().out)
    assert described["production_seed_creator_cli_exposed"] is False
    assert "production_seed_creator_exposed" not in described


def test_cli_contract_smoke_fresh_receipt_checkpoint_decode_and_create_once(tmp_path):
    packet_path = (tmp_path / "packet.json").resolve()
    create_test_seed_packet(packet_path)
    manifest = make_test_manifest(
        seed_packet_path=packet_path,
        roots={
            name: str((tmp_path / "smoke-run" / name).resolve())
            for name in ("output", "checkpoint", "scratch")
        },
        compute=named_compute_profile(), base_commit="2" * 40,
        worktree_state="DIRTY_UNCOMMITTED_TEST_ONLY",
    )
    manifest_path = (tmp_path / "manifest.json").resolve()
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    receipt_path = (tmp_path / "admit-memory.json").resolve()
    completed = subprocess.run(
        [
            sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
            "admit-memory", "--out", str(receipt_path),
        ],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    argv = ["test-smoke", "--manifest", str(manifest_path), "--receipt", str(receipt_path)]
    assert cli.main(argv) == 0
    smoke = json.loads((tmp_path / "smoke-run" / "output" / "smoke.json").read_text())
    assert smoke["checkpoint0_persisted_readback_decode_revalidated"] is True
    assert smoke["performance_disposition"] == "REPAIR_REQUIRED"
    assert all(smoke[field] is False for field in (
        "native_executed", "environment_executed", "update_executed", "evaluation_executed",
    ))
    assert (tmp_path / "smoke-run" / "checkpoint" / "checkpoint-000.json").is_file()
    assert cli.main(argv) == 2
