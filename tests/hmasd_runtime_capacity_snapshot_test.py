"""Proof-sized tests for the one-shot capacity observation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / ".agents/skills/hmasd-agile-research-development/scripts/hmasd_runtime_capacity_snapshot.py"
MODULE_SPEC = importlib.util.spec_from_file_location("hmasd_capacity_snapshot", SCRIPT)
assert MODULE_SPEC and MODULE_SPEC.loader
SNAPSHOT = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(SNAPSHOT)


def _live(*, complete: bool = True) -> dict[str, object]:
    return {
        "complete": complete,
        "cpu": {"logical_processors": 8},
        "memory": {"memory_load_percent": 25, "available_physical_bytes": 1000, "total_physical_bytes": 4000},
        "processes": {
            "observed_process_count": 4,
            "known_process_ids": [101, 102],
            "running_known_process_ids": [101, 102],
            "missing_known_process_ids": [],
        },
        "errors": [] if complete else [{"field": "live.memory", "message": "fixture incomplete"}],
    }


def _payload() -> dict[str, object]:
    return {
        "assignment_id": "WDM-STATELESS-CAPACITY-SNAPSHOT-2026-08-09",
        "active_treatments": [
            {
                "treatment_id": "active-a",
                "process_ids": [101],
                "units": 1,
                "cpu_units": 1,
                "memory_bytes": 100,
                "gpu_claims": ["gpu:0"],
                "paid_service_claims": ["service:active-a"],
                "output_paths": ["C:/work/active-a/result.json"],
                "writable_paths": ["C:/work/active-a"],
            },
            {
                "treatment_id": "active-b",
                "process_ids": [102],
                "units": 1,
                "cpu_units": 1,
                "memory_bytes": 100,
                "gpu_claims": ["gpu:1"],
                "paid_service_claims": ["service:active-b"],
                "output_paths": ["C:/work/active-b/result.json"],
                "writable_paths": ["C:/work/active-b"],
            },
        ],
        "prospective": {
            "class": "result-bearing",
            "units": 1,
            "process_ids": [201],
            "cpu_units": 1,
            "memory_bytes": 100,
            "gpu_claims": ["gpu:2"],
            "paid_service_claims": ["service:prospective"],
            "output_paths": ["C:/work/prospective/result.json"],
            "writable_paths": ["C:/work/prospective"],
        },
    }


class CapacitySnapshotTest(unittest.TestCase):
    def test_success_records_three_unit_arithmetic_and_exact_facts(self) -> None:
        snapshot = SNAPSHOT.build_snapshot(_payload(), _live())
        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(snapshot["status"], "SUCCESS")
        facts = snapshot["facts"]
        self.assertEqual(facts["capacity_units_total"], 3)
        self.assertEqual(facts["active_units"], 2)
        self.assertEqual(facts["reserved_units"], 2)
        self.assertEqual(facts["requested_units"], 1)
        self.assertEqual(facts["free_units"], 1)
        self.assertEqual(facts["available_units_before_request"], 1)
        self.assertEqual(facts["projected_units"], 3)
        self.assertEqual(facts["free_units_after_request"], 0)
        self.assertEqual(facts["reserved_cpu_units"], 2)
        self.assertEqual(facts["free_cpu_units_before_request"], 6)
        self.assertEqual(facts["reserved_memory_bytes"], 200)
        self.assertEqual(facts["free_memory_bytes_before_request"], 800)
        self.assertEqual(facts["remaining_units_after_request"], 0)
        self.assertEqual(facts["prospective_process_ids"], [201])
        self.assertEqual(facts["process_conflicts"], [])
        self.assertEqual(facts["gpu_conflicts"], [])
        self.assertEqual(facts["paid_service_conflicts"], [])
        self.assertEqual(facts["gpu_claims"]["prospective"], ["gpu:2"])
        self.assertEqual(facts["paid_service_claims"]["prospective"], ["service:prospective"])
        self.assertEqual(facts["cpu_conflicts"], [])
        self.assertEqual(facts["memory_conflicts"], [])
        self.assertEqual(facts["path_conflicts"], [])
        self.assertNotIn("decision", snapshot)
        self.assertNotIn("admission", snapshot)

    def test_active_treatment_summary_preserves_identity_order_and_all_claims(self) -> None:
        snapshot = SNAPSHOT.build_snapshot(_payload(), _live())
        self.assertEqual(snapshot["status"], "SUCCESS")
        self.assertEqual(snapshot["facts"]["active_treatments"], _payload()["active_treatments"])

    def test_conflicting_exact_claim_is_a_direct_error_without_inference(self) -> None:
        payload = _payload()
        prospective = payload["prospective"]
        assert isinstance(prospective, dict)
        prospective["output_paths"] = ["C:/work/active-a/result.json"]
        snapshot = SNAPSHOT.build_snapshot(payload, _live())
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "PATH_CONFLICT")
        self.assertEqual(snapshot["facts"]["projected_units"], 3)
        self.assertTrue(snapshot["facts"]["path_conflicts"])

    def test_gpu_and_paid_service_claim_conflicts_are_explicit(self) -> None:
        payload = _payload()
        prospective = payload["prospective"]
        assert isinstance(prospective, dict)
        prospective["gpu_claims"] = ["GPU:0"]
        prospective["paid_service_claims"] = ["SERVICE:ACTIVE-B"]
        snapshot = SNAPSHOT.build_snapshot(payload, _live())
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "GPU_CONFLICT")
        self.assertEqual(snapshot["facts"]["gpu_conflicts"][0]["claim"], "gpu:0")
        self.assertEqual(snapshot["facts"]["paid_service_conflicts"][0]["claim"], "service:active-b")

    def test_prospective_process_conflict_is_explicit(self) -> None:
        payload = _payload()
        prospective = payload["prospective"]
        assert isinstance(prospective, dict)
        prospective["process_ids"] = [101]
        snapshot = SNAPSHOT.build_snapshot(payload, _live())
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "PROCESS_CONFLICT")
        self.assertEqual(snapshot["facts"]["process_conflicts"][0]["claim"], "101")

    def test_declared_cpu_and_memory_claims_report_direct_pressure(self) -> None:
        payload = _payload()
        prospective = payload["prospective"]
        assert isinstance(prospective, dict)
        prospective["cpu_units"] = 7
        prospective["memory_bytes"] = 900
        snapshot = SNAPSHOT.build_snapshot(payload, _live())
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "CPU_CONFLICT")
        self.assertEqual(snapshot["facts"]["cpu_conflicts"][0]["kind"], "prospective_claim_exceeds_free")
        self.assertEqual(snapshot["facts"]["memory_conflicts"][0]["kind"], "prospective_claim_exceeds_free")

    def test_incomplete_live_facts_are_reported_not_filled_in(self) -> None:
        snapshot = SNAPSHOT.build_snapshot(_payload(), _live(complete=False))
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "LIVE_FACTS_INCOMPLETE")
        self.assertEqual(snapshot["facts"]["live"]["memory"], {"memory_load_percent": 25, "available_physical_bytes": 1000, "total_physical_bytes": 4000})

    def test_cli_writes_assignment_named_snapshot_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            input_path = directory / "input.json"
            output_path = directory / "WDM-STATELESS-CAPACITY-SNAPSHOT-2026-08-09.json"
            input_path.write_text(json.dumps(_payload()), encoding="utf-8")
            # The CLI's live host observation is intentionally not made part of
            # this proof-sized test; module behavior above supplies deterministic
            # live facts.  Exercise the write/error terminal path directly.
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertTrue(output_path.is_file())
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written["assignment_id"], _payload()["assignment_id"])
            self.assertIn(written["status"], {"SUCCESS", "ERROR"})
            self.assertEqual(completed.returncode, 0 if written["status"] == "SUCCESS" else 1)

    def test_unknown_input_key_is_rejected(self) -> None:
        payload = _payload()
        payload["local_research"] = "must not be read"
        snapshot = SNAPSHOT.build_snapshot(payload, _live())
        self.assertEqual(snapshot["status"], "ERROR")
        self.assertEqual(snapshot["error"]["code"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
