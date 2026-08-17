import json
from pathlib import Path

from tools.codex_context_lifecycle.cli import main


def test_gc_cli_dry_run_has_empty_deletions(tmp_path: Path, capsys) -> None:
    code = main(["gc", "--state", str(tmp_path / "state.sqlite3"), "--dry-run"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "DRY_RUN"
    assert payload["deletions"] == []
    assert payload["applied"] is False
