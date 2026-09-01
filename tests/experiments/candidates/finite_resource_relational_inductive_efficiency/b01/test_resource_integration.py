from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import validate_resource_receipt


def test_real_admit_memory_receipt_is_accepted_without_invented_mode(tmp_path):
    receipt_path = (tmp_path / "actual-admit-memory.json").resolve()
    script = Path("scripts/hmasd_resource_preflight.py").resolve()
    completed = subprocess.run(
        [sys.executable, str(script), "admit-memory", "--out", str(receipt_path)],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert "mode" not in receipt
    assert validate_resource_receipt(receipt) == receipt
