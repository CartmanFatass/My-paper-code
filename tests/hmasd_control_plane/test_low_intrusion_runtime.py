import json
from pathlib import Path


def test_config_has_no_behavioral_hook_tables():
    config = Path(".codex/config.toml").read_text(encoding="utf-8")
    hooks = json.loads(Path(".codex/hooks.json").read_text(encoding="utf-8"))
    assert "hooks = false" in config
    assert "[[hooks." not in config
    assert hooks["hooks"] == {}
    assert hooks["mode"] == "disabled_low_intrusion"
    assert "automatic_wake" in Path("scripts/hmasd-root-supervisor-start.ps1").read_text(encoding="utf-8")
