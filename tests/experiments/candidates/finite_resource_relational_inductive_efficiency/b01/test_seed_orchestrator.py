from __future__ import annotations

import json
import time
from pathlib import Path

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    TEST_SEED_LABELS,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    bind_invocation_resource, manifest_template,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    bounded_test_seed_worker_map, formal_seed_worker_plan_from_manifest,
    make_test_only_seed_worker_tasks,
)


def _receipt():
    return {
        "schema_version": 1, "captured_at": "2026-09-01T00:00:00Z",
        "assessed_at": "2026-09-01T00:00:01Z", "measurement_source": "TEST_LITERAL",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 8 * 1024**3,
        "cgroup_memory_max_bytes": None, "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None, "effective_available_bytes": 8 * 1024**3,
        "physical_floor_pass": True, "effective_floor_pass": True,
        "passed": True, "failure_reasons": [],
    }


def _test_tasks(tmp_path: Path):
    bindings = {}
    for index, label in enumerate(TEST_SEED_LABELS[:3], start=1):
        receipt = _receipt()
        path = (tmp_path / f"receipt-{index}.json").resolve()
        path.write_text(json.dumps(receipt), encoding="utf-8")
        bindings[label] = bind_invocation_resource(
            invocation_id=f"FRRIE-B01-TEST-SEED-{index}", operation="TEST_SMOKE",
            receipt_path=path, receipt=receipt, test_only=True,
        )
    roots = {
        name: str((tmp_path / f"test-{name}").resolve())
        for name in ("output", "checkpoint", "scratch")
    }
    return make_test_only_seed_worker_tasks(
        seed_labels=TEST_SEED_LABELS[:3], invocation_bindings=bindings, roots=roots,
    )


def _static_worker(task):
    # Deliberately fabricated/reused IDs demonstrate that Python object IDs are
    # diagnostic only and cannot become a formal isolation authority.
    time.sleep(0.002 if task.seed_label.endswith("001") else 0.0)
    return {
        "seed_label": task.seed_label,
        "invocation_id": task.invocation_binding["invocation_id"],
        "effect_paths": [str((Path(task.output_root) / "candidate.json").resolve())],
        "runtime_identity": {
            "model_object_id": 7, "optimizer_object_id": 7,
            "torch_threads": 1, "native_width": 32,
        },
        "payload": {"direct_test_value": task.seed_label},
    }


def test_test_only_seed_mapper_is_1_2_4_order_equivalent_without_id_authority(tmp_path):
    tasks = _test_tasks(tmp_path)
    results = {
        workers: bounded_test_seed_worker_map(tasks, workers=workers, worker_fn=_static_worker)
        for workers in (1, 2, 4)
    }
    expected_order = list(TEST_SEED_LABELS[:3])
    for workers, result in results.items():
        assert result["seed_order"] == expected_order
        assert [row["seed_label"] for row in result["rows"]] == expected_order
        assert [row["payload"] for row in result["rows"]] == [
            {"direct_test_value": label} for label in expected_order
        ]
        assert result["actual_worker_ceiling"] == min(workers, 3)
        assert result["runtime_object_ids_authoritative"] is False
        assert result["formal_launch_capable"] is False
        assert result["duplicate_launches"] == 0


def test_test_only_seed_mapper_quarantines_failure_in_manifest_order_without_retry(tmp_path):
    tasks = _test_tasks(tmp_path)
    calls = {label: 0 for label in TEST_SEED_LABELS[:3]}

    def worker(task):
        calls[task.seed_label] += 1
        if task.seed_label.endswith("002"):
            raise RuntimeError("deliberate isolated failure")
        return _static_worker(task)

    result = bounded_test_seed_worker_map(tasks, workers=4, worker_fn=worker)
    assert calls == {label: 1 for label in TEST_SEED_LABELS[:3]}
    assert [row["status"] for row in result["rows"]] == [
        "COMPLETE", "INCOMPLETE_QUARANTINE_REQUIRED", "COMPLETE",
    ]
    assert result["failed_seed_count"] == 1
    assert result["duplicate_launches"] == 0


def test_formal_initial_and_extension_plans_have_no_precreated_receipts_or_launch_seam(
    tmp_path, b01_manifest,
):
    def planned(manifest, prefix):
        return {
            label: {
                "invocation_id": f"{prefix}-{index}",
                "receipt_path": str((tmp_path / f"{prefix}-{index}-receipt.json").resolve()),
            }
            for index, label in enumerate(manifest["execution_labels"], start=1)
        }

    initial = formal_seed_worker_plan_from_manifest(
        b01_manifest, planned(b01_manifest, "INITIAL"),
    )
    assert initial["actual_seed_task_count"] == 3
    assert initial["capacity"] == 4 and initial["launch_capable"] is False
    assert all(not Path(row.planned_receipt_path).exists() for row in initial["tasks"])
    assert initial["worker_runtime_contract"]["admission"].startswith("WORKER_LOCAL_FRESH")

    parent_path = (tmp_path / "persisted-initial-manifest.json").resolve()
    parent_path.write_text(json.dumps(b01_manifest), encoding="utf-8")
    extension = manifest_template(
        seed_packet_path=b01_manifest["seed_packet"]["path"], phase="EXTENSION_004_005",
        roots={
            name: str((tmp_path / "extension" / name).resolve())
            for name in ("output", "checkpoint", "scratch")
        },
        compute=b01_manifest["compute"], code_revision=b01_manifest["code_revision"],
        parent_initial={"locator": str(parent_path), "manifest_contract": b01_manifest},
    )
    extension_plan = formal_seed_worker_plan_from_manifest(
        extension, planned(extension, "EXTENSION"),
    )
    assert extension_plan["actual_seed_task_count"] == 2
    assert extension_plan["seed_order"] == list(extension["execution_labels"])
    assert extension_plan["launch_capable"] is False
