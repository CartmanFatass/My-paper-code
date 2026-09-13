"""Exact published input with real Agentify modules; all browser effects are fixtures."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AcpsSelectorRepair(unittest.TestCase):
    def test_same_unsent_operation_recovers_without_model_mutation(self):
        source = Path(os.environ.get("AGENTIFY_DESKTOP_SOURCE", "C:/Projects/agentify-desktop"))
        if not (source / "chatgpt-controller.mjs").exists():
            self.skipTest("Agentify source is not installed on this host")
        scratch_root = ROOT / "temp/tests"
        scratch_root.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix="acps-selector-repair-", dir=scratch_root))
        handoff_path = "docs/research/candidates/actuator_conditioned_partial_sharing/pro_packets/20260912_post_b02_use/delivery/HANDOFF.json"
        try:
            content = subprocess.check_output(["git", "show", "aaf0b977de1f547794ac0a540480be9778f1524e:" + handoff_path], cwd=ROOT)
            (scratch / "HANDOFF.json").write_bytes(content)
            run = subprocess.run(["node", str(ROOT / "tests/fixtures/native_transport/acps-selector-dry-run.mjs"),
                                  str(source), str(scratch), str(scratch / "HANDOFF.json")],
                                 cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["selector_cases"], 12)
            self.assertEqual(result["external_sends"], 0)
            self.assertTrue(result["same_operation_repair"])
            self.assertTrue(result["uncertain_observe_only"])
            self.assertTrue(result["archive_exact"])
        finally:
            (scratch / "HANDOFF.json").unlink(missing_ok=True)
            scratch.rmdir()


if __name__ == "__main__":
    unittest.main()
