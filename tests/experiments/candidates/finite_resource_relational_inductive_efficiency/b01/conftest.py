from __future__ import annotations

import json

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    canonical_json_bytes, make_test_manifest, manifest_template, named_compute_profile,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import create_test_seed_packet

CODE_REVISION = "1" * 40


@pytest.fixture
def b01_manifest(tmp_path):
    roots = [(bytes([index]) * 32).hex() for index in range(1, 6)]
    packet_path = (tmp_path / "production-contract-fixture-packet.json").resolve()
    packet_path.write_bytes(canonical_json_bytes({
        "schema": "FRRIE_B01_SEED_PACKET_V1",
        "labels": [f"FRRIE-B01-FRESH-BLOCK-{index:03d}" for index in range(1, 6)],
        "roots_hex": roots, "created_at": "2026-09-01T00:00:00+00:00",
        "generation_source": "OS_CSPRNG", "complete": True, "test_only": False,
    }))
    return manifest_template(
        seed_packet_path=packet_path,
        phase="INITIAL_001_003",
        roots={
            "output": str((tmp_path / "run" / "output").resolve()),
            "checkpoint": str((tmp_path / "run" / "checkpoint").resolve()),
            "scratch": str((tmp_path / "run" / "scratch").resolve()),
        },
        compute=named_compute_profile(),
        code_revision=CODE_REVISION,
    )


@pytest.fixture
def b01_test_manifest(tmp_path):
    packet_path = (tmp_path / "test-seed-packet.json").resolve()
    create_test_seed_packet(packet_path)
    return make_test_manifest(
        seed_packet_path=packet_path,
        roots={
            "output": str((tmp_path / "test-run" / "output").resolve()),
            "checkpoint": str((tmp_path / "test-run" / "checkpoint").resolve()),
            "scratch": str((tmp_path / "test-run" / "scratch").resolve()),
        },
        compute=named_compute_profile(),
        base_commit=CODE_REVISION,
        worktree_state="DIRTY_UNCOMMITTED_TEST_ONLY",
    )


@pytest.fixture
def b01_resource_binding(tmp_path):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import bind_invocation_resource

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
        "effective_available_bytes": 8 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }
    path = (tmp_path / "test-resource-receipt.json").resolve()
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return bind_invocation_resource(
        invocation_id="FRRIE-B01-TEST-SMOKE-001", operation="TEST_SMOKE",
        receipt_path=path, receipt=receipt, test_only=True,
    )


@pytest.fixture
def b01_production_binding(tmp_path):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import bind_invocation_resource

    receipt = {
        "schema_version": 1,
        "captured_at": "2026-09-01T00:00:00Z",
        "assessed_at": "2026-09-01T00:00:01Z",
        "measurement_source": "TEST_ONLY_LITERAL_FOR_PRODUCTION_SCHEMA_VALIDATION",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 8 * 1024**3,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None,
        "effective_available_bytes": 8 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }
    path = (tmp_path / "production-schema-resource-receipt.json").resolve()
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return bind_invocation_resource(
        invocation_id="FRRIE-B01-PRODUCTION-SCHEMA-TEST", operation="TRAIN",
        receipt_path=path, receipt=receipt, test_only=False,
    )
