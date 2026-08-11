"""Proof-sized contract tests for the Experiment Operator receipt helper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO
    / ".agents"
    / "skills"
    / "hmasd-agile-research-development"
    / "scripts"
    / "hmasd_experiment_operator_receipt.py"
)
INPUT_KEYS = {
    "run",
    "source_commit",
    "execution_mode",
    "phase",
    "exit_codes",
    "artifacts",
    "last_progress",
    "process_live",
    "direct_error",
}
OUTPUT_KEYS = INPUT_KEYS | {"terminal"}
TEST_TEMP_ROOT = (
    REPO
    / "temp"
    / "sessions"
    / "root"
    / "test-tmp"
    / "experiment-operator-receipt"
)


def temporary_directory() -> tempfile.TemporaryDirectory[str]:
    TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)


def complete_record() -> dict[str, object]:
    return {
        "run": "receipt-test-run",
        "source_commit": "a" * 40,
        "execution_mode": "fresh",
        "phase": "ANALYZE",
        "exit_codes": {"train": 0, "evaluate": 0, "analyze": 0},
        "artifacts": {"result": "terminal-result.json"},
        "last_progress": {"phase": "ANALYZE"},
        "process_live": False,
        "direct_error": None,
    }


class ExperimentOperatorReceiptTests(unittest.TestCase):
    def run_helper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_complete_write_check_exact_keys_and_utf8_without_bom(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            record_path = root / "record.json"
            receipt_path = root / "receipt.json"
            self.write_json(record_path, complete_record())

            written = self.run_helper(
                "write", "--record", str(record_path), "--receipt", str(receipt_path)
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertIn("terminal=COMPLETE", written.stdout)
            self.assertIn("receipt_path=", written.stdout)
            self.assertTrue(written.stdout.isascii())
            payload_bytes = receipt_path.read_bytes()
            self.assertFalse(payload_bytes.startswith(b"\xef\xbb\xbf"))
            payload = json.loads(payload_bytes.decode("utf-8"))
            self.assertEqual(set(payload), OUTPUT_KEYS)
            self.assertEqual(payload["terminal"], "COMPLETE")
            self.assertEqual(
                list(payload),
                [
                    "run",
                    "source_commit",
                    "execution_mode",
                    "phase",
                    "exit_codes",
                    "artifacts",
                    "last_progress",
                    "process_live",
                    "direct_error",
                    "terminal",
                ],
            )
            checked = self.run_helper("check", "--receipt", str(receipt_path))
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("terminal=COMPLETE", checked.stdout)
            self.assertEqual(list(root.glob(f".{receipt_path.name}.*.tmp")), [])

    def test_uppercase_exit_code_input_normalizes_to_lowercase_receipt(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            record = complete_record()
            record["exit_codes"] = {"TRAIN": 0, "EVALUATE": 0, "ANALYZE": 0}
            record_path = root / "record.json"
            receipt_path = root / "receipt.json"
            self.write_json(record_path, record)

            written = self.run_helper(
                "write", "--record", str(record_path), "--receipt", str(receipt_path)
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["exit_codes"], {"train": 0, "evaluate": 0, "analyze": 0}
            )
            checked = self.run_helper("check", "--receipt", str(receipt_path))
            self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_error_with_zero_exits_and_missing_artifact_direct_error(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            record = complete_record()
            record["direct_error"] = "required terminal artifact is missing"
            record["artifacts"] = {}
            record_path = root / "record.json"
            receipt_path = root / "receipt.json"
            self.write_json(record_path, record)
            result = self.run_helper(
                "write", "--record", str(record_path), "--receipt", str(receipt_path)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("terminal=ERROR", result.stdout)
            self.assertEqual(json.loads(receipt_path.read_text(encoding="utf-8"))["terminal"], "ERROR")

    def test_check_rejects_terminal_mismatch_without_writing(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            record_path = root / "record.json"
            receipt_path = root / "receipt.json"
            self.write_json(record_path, complete_record())
            self.assertEqual(
                self.run_helper(
                    "write", "--record", str(record_path), "--receipt", str(receipt_path)
                ).returncode,
                0,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["terminal"] = "ERROR"
            self.write_json(receipt_path, receipt)
            before = receipt_path.read_bytes()
            result = self.run_helper("check", "--receipt", str(receipt_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt_path.read_bytes(), before)

    def test_invalid_records_never_create_or_overwrite_receipt(self) -> None:
        invalid_records = []

        missing_field = complete_record()
        del missing_field["direct_error"]
        invalid_records.append(missing_field)

        legacy_error = complete_record()
        legacy_error["error"] = "legacy field"
        invalid_records.append(legacy_error)

        slash_phase = complete_record()
        slash_phase["phase"] = "ANALYZE/COMPLETE"
        invalid_records.append(slash_phase)

        live = complete_record()
        live["process_live"] = True
        invalid_records.append(live)

        incomplete = complete_record()
        incomplete["phase"] = "EVALUATE"
        incomplete["exit_codes"] = {"train": 0, "evaluate": None, "analyze": None}
        invalid_records.append(incomplete)

        nonzero_without_error = complete_record()
        nonzero_without_error["phase"] = "TRAIN"
        nonzero_without_error["exit_codes"] = {"train": 3, "evaluate": None, "analyze": None}
        invalid_records.append(nonzero_without_error)

        out_of_order = complete_record()
        out_of_order["phase"] = "EVALUATE"
        out_of_order["exit_codes"] = {"train": None, "evaluate": 0, "analyze": None}
        invalid_records.append(out_of_order)

        later_phase_after_train = complete_record()
        later_phase_after_train["phase"] = "TRAIN"
        later_phase_after_train["exit_codes"] = {"train": 0, "evaluate": 0, "analyze": None}
        invalid_records.append(later_phase_after_train)

        later_phase_after_evaluate = complete_record()
        later_phase_after_evaluate["phase"] = "EVALUATE"
        later_phase_after_evaluate["exit_codes"] = {"train": 0, "evaluate": 0, "analyze": 0}
        invalid_records.append(later_phase_after_evaluate)

        mixed_case_keys = complete_record()
        mixed_case_keys["exit_codes"] = {"TRAIN": 0, "evaluate": 0, "analyze": 0}
        invalid_records.append(mixed_case_keys)

        missing_exit_code_key = complete_record()
        missing_exit_code_key["exit_codes"] = {"train": 0, "evaluate": 0}
        invalid_records.append(missing_exit_code_key)

        extra_exit_code_key = complete_record()
        extra_exit_code_key["exit_codes"] = {
            "train": 0,
            "evaluate": 0,
            "analyze": 0,
            "EXTRA": 0,
        }
        invalid_records.append(extra_exit_code_key)

        whitespace_run = complete_record()
        whitespace_run["run"] = "   "
        invalid_records.append(whitespace_run)

        whitespace_error = complete_record()
        whitespace_error["direct_error"] = "   "
        invalid_records.append(whitespace_error)

        for index, record in enumerate(invalid_records):
            with self.subTest(index=index):
                with temporary_directory() as temporary:
                    root = Path(temporary)
                    record_path = root / "record.json"
                    receipt_path = root / "receipt.json"
                    self.write_json(record_path, record)
                    receipt_path.write_bytes(b"existing-receipt")
                    result = self.run_helper(
                        "write", "--record", str(record_path), "--receipt", str(receipt_path)
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(receipt_path.read_bytes(), b"existing-receipt")
                    self.assertEqual(list(root.glob(f".{receipt_path.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
