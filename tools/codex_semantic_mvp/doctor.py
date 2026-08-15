"""Read-only, machine-readable activation checks for the semantic MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


MCP_VERSION = "2.0.0"
BEGIN_MARKER = "# BEGIN HMASD CODEX SEMANTIC MVP"
END_MARKER = "# END HMASD CODEX SEMANTIC MVP"
PYTHON_EXECUTABLE = r"C:\Users\wu\.conda\envs\SB3\python.exe"


def _file_baseline(path: Path, display_path: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "path": display_path,
    }


def _marker_block(config_text: str) -> str | None:
    begins = list(re.finditer(r"(?m)^# BEGIN HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)", config_text))
    ends = list(re.finditer(r"(?m)^# END HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)", config_text))
    if len(begins) != 1 or len(ends) != 1 or ends[0].start() <= begins[0].start():
        return None
    return config_text[begins[0].start() : ends[0].end()]


def _server_config(config_text: str) -> tuple[bool, bool, str | None]:
    block = _marker_block(config_text)
    if block is None:
        return False, False, None
    sections = list(re.finditer(r"(?m)^\[mcp_servers\.hmasd_orchestrator\][ \t]*(?:\r?$)", block))
    if len(sections) != 1:
        return False, False, block
    headings = list(re.finditer(r"(?m)^\[[^\r\n\]]+\][ \t]*(?:\r?$)", block))
    section_end = len(block)
    for heading in headings:
        if heading.start() > sections[0].start():
            section_end = heading.start()
            break
    section = block[sections[0].start() : section_end]
    enabled_matches = list(re.finditer(r"(?m)^[ \t]*enabled[ \t]*=[ \t]*(true|false)[ \t]*(?:\r?$)", section))
    escaped_python = PYTHON_EXECUTABLE.replace("\\", "\\\\")
    required = (
        len(enabled_matches) == 1
        and f'command = "{escaped_python}"' in section
        and re.search(r"(?m)^tool_timeout_sec[ \t]*=[ \t]*1800[ \t]*(?:\r?$)", section) is not None
        and re.search(r"(?m)^args[ \t]*=", section) is not None
    )
    enabled = bool(enabled_matches and enabled_matches[0].group(1).lower() == "true")
    return required, enabled, block


def _mode(repo_root: Path, hooks: bytes) -> str:
    if hooks == (repo_root / ".codex" / "hooks.semantic-mvp.shadow.json").read_bytes():
        return "shadow"
    if hooks == (repo_root / ".codex" / "hooks.semantic-mvp.active.json").read_bytes():
        return "active"
    try:
        value = json.loads(hooks.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "unknown"
    if isinstance(value, dict) and value.get("hooks") == {}:
        return "off"
    return "unknown"


def _runtime_writable(runtime_dir: Path) -> bool:
    """Report write capability without creating directories or probe files."""
    try:
        if runtime_dir.exists():
            return runtime_dir.is_dir() and os.access(runtime_dir, os.W_OK)
        parent = runtime_dir.parent
        return parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)
    except OSError:
        return False


def collect_baseline(repo_root: Path) -> dict[str, Any]:
    """Return legacy file entries plus machine-readable activation fields."""
    root = Path(repo_root).resolve()
    config_path = root / ".codex" / "config.toml"
    hooks_path = root / ".codex" / "hooks.json"
    config = _file_baseline(config_path, ".codex/config.toml")
    hooks = _file_baseline(hooks_path, ".codex/hooks.json")
    config_text = config_path.read_text(encoding="utf-8")
    present, enabled, _ = _server_config(config_text)
    return {
        "config_toml": config,
        "hooks_json": hooks,
        "live_hooks_hash": hooks["sha256"],
        "config_hash": config["sha256"],
        "mcp_version": MCP_VERSION,
        "server_config_present": present,
        "server_enabled": enabled,
        "runtime_writable": _runtime_writable(root / "runtime" / "codex-semantic-mvp"),
        "mode": _mode(root, hooks_path.read_bytes()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect semantic MVP activation state")
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = collect_baseline(args.repo_root)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
