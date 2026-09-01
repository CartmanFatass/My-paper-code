from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, validate_test_manifest,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.lifecycle import (
    claim_fresh_roots, publish_complete_panel, publish_quarantine,
)


def test_test_roots_are_one_atomic_sibling_transaction(b01_test_manifest):
    roots = claim_fresh_roots(b01_test_manifest)
    assert set(roots) == {"output", "checkpoint", "scratch"}
    assert all((path / ".FRRIE_B01_ROOT.json").is_file() for path in roots.values())
    assert len({path.parent for path in roots.values()}) == 1


def test_nested_or_overlapping_test_roots_are_rejected(b01_test_manifest):
    altered = deepcopy(b01_test_manifest)
    altered["roots"]["scratch"] = altered["roots"]["output"] + "/nested"
    with pytest.raises(B01ContractError, match="siblings"):
        validate_test_manifest(altered)


def test_repair_required_cannot_publish_and_quarantine_requires_binding(
    b01_test_manifest, b01_resource_binding, b01_manifest, b01_production_binding,
):
    roots = claim_fresh_roots(b01_test_manifest)
    repair = {
        "schema": "FRRIE_B01_PERFORMANCE_TELEMETRY_V1",
        "disposition": "REPAIR_REQUIRED", "blocker": "TEST_TOOLCHAIN_UNAVAILABLE",
        "measured_at": None, "end_to_end_wall_seconds": None,
        "scientific_slots": None, "slots_per_second": None, "cpu_seconds": None,
        "cpu_occupancy_fraction": None, "process_tree_peak_rss_bytes": None,
        "scratch_peak_bytes": None, "durable_peak_bytes": None,
        "read_bytes": None, "write_bytes": None, "worker_peak": None,
        "scalar_batch_equivalence": None, "worker_equivalence": None,
    }
    panel = {
        "schema": "FRRIE_B01_COMPLETE_PANEL_V1", "manifest_contract": b01_manifest,
        "invocation_binding": b01_production_binding, "performance_evidence": repair,
        "rows": [], "training_primitives": [], "checkpoint_restore_receipts": [],
        "action_probability_rows": [], "raw_control_receipt": {}, "complete": True,
    }
    with pytest.raises(B01ContractError, match="PRODUCTION_PANEL_VALIDATION_UNAVAILABLE"):
        publish_complete_panel(
            roots["output"] / "panel.json", panel=panel, manifest=b01_manifest,
        )
    quarantine = publish_quarantine(
        roots["output"], invocation_binding=b01_resource_binding,
        technical_reason="TEST_ONLY deliberate incomplete path",
    )
    assert quarantine.is_file()
