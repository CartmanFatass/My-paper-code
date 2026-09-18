"""Keep new CLI runners on the cooperative admission path; no scientific runs.

The rollout boundary preserves archived/frozen runner source at its old SHA.
This source check complements runtime handshake tests; it is not a proof against
arbitrary code or a substitute for reviewing that admission precedes side effects.
"""
import ast
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ROLLOUT_BASE = "8ba67835276d15a3392fc6e0a9c7adeeaa1cb388"
MIGRATED = {"scripts/run_folr_entity_augmentation_repeat_b01.py"}


def test_new_and_migrated_runners_call_admission():
    baseline = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", ROLLOUT_BASE, "scripts"],
        check=True, capture_output=True, text=True,
    )
    historical = set(baseline.stdout.splitlines())
    candidates = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "scripts").glob("run_*.py")
    }
    for relative in sorted((candidates - historical) | MIGRATED):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert any(
            isinstance(call.func, ast.Name) and call.func.id == "require_admission"
            and any(k.arg == "direction" for k in call.keywords)
            for call in calls
        ), f"{relative}: new result runner needs require_admission before result-bearing work"


def test_migrated_runner_direct_cli_refuses_before_output_creation(tmp_path):
    # Valid scientific identifiers reach the guard, but no model/environment is
    # constructed. No admission is minted and the owner's pause is unchanged.
    output = tmp_path / "never-created"
    result = subprocess.run(
        [sys.executable, str(ROOT / next(iter(MIGRATED))),
         "--block", "1", "--arm", "GENERIC_RETAIN", "--seed", "781901",
         "--evaluation-seed", "1781901", "--launch-sha", "0" * 40,
         "--out", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not output.exists()
