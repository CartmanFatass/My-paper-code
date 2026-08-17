"""Read-only, machine-readable activation checks for the semantic MVP."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version as distribution_version
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


BEGIN_MARKER = "# BEGIN HMASD CODEX SEMANTIC MVP"
END_MARKER = "# END HMASD CODEX SEMANTIC MVP"
HOOK_BEGIN_MARKER = "# BEGIN HMASD CODEX SEMANTIC HOOKS"
HOOK_END_MARKER = "# END HMASD CODEX SEMANTIC HOOKS"
PYTHON_EXECUTABLE = r"C:\Users\wu\.conda\envs\SB3\python.exe"
USER_TRUST_STATUS = "unknown"
USER_TRUST_SCOPE = "repository_only"
USER_TRUST_MESSAGE = "Repository-only doctor cannot establish user-level Codex trust."


def _file_baseline(path: Path, display_path: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "path": display_path,
    }


def installed_mcp_version(version_reader: Any = distribution_version) -> str | None:
    """Return the installed ``mcp`` distribution version, without guessing."""
    try:
        value = version_reader("mcp")
    except Exception:
        return None
    return str(value) if value else None


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
    args_match = re.search(r"(?ms)^args[ \t]*=[ \t]*\[\s*(.*?)^\s*\][ \t]*(?:\r?$)", section)
    args = []
    if args_match:
        args = [line.strip().rstrip(",") for line in args_match.group(1).splitlines() if line.strip()]
    expected_args = [
        '"-m"',
        '"tools.codex_semantic_mvp.mcp_server"',
        '"--state-dir"',
        '"runtime/codex-semantic-mvp"',
    ]
    required = (
        len(enabled_matches) == 1
        and len(re.findall(r"(?m)^[ \t]*command[ \t]*=", section)) == 1
        and re.search(rf'(?m)^[ \t]*command[ \t]*=[ \t]*"{re.escape(escaped_python)}"[ \t]*(?:\r?$)', section) is not None
        and len(re.findall(r"(?m)^[ \t]*tool_timeout_sec[ \t]*=", section)) == 1
        and re.search(r"(?m)^[ \t]*tool_timeout_sec[ \t]*=[ \t]*1800[ \t]*(?:\r?$)", section) is not None
        and len(re.findall(r"(?m)^[ \t]*args[ \t]*=", section)) == 1
        and args == expected_args
    )
    enabled = bool(enabled_matches and enabled_matches[0].group(1).lower() == "true")
    return required, enabled, block


def _inline_hook_mode(config_text: str) -> str:
    """Return the mode encoded by a complete managed inline hook block."""
    begins = list(re.finditer(r"(?m)^# BEGIN HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)", config_text))
    ends = list(re.finditer(r"(?m)^# END HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)", config_text))
    if not begins and not ends:
        return "absent"
    if len(begins) != 1 or len(ends) != 1 or ends[0].start() <= begins[0].start():
        return "unknown"
    block = config_text[begins[0].end() : ends[0].start()]
    modes: list[str] = []
    for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse"):
        header = re.compile(rf"(?m)^\[\[hooks\.{event}\]\][ \t]*(?:\r?$)")
        if len(header.findall(block)) != 1:
            return "unknown"
        section_match = re.search(
            rf"(?ms)^\[\[hooks\.{event}\]\][ \t]*\r?\n(.*?)(?=^\[\[hooks\.[A-Za-z]+\]\][ \t]*\r?$|\Z)",
            block,
        )
        if section_match is None:
            return "unknown"
        section = section_match.group(1)
        nested = [value.strip() for value in re.findall(r"(?m)^[ \t]*\[\[hooks\.[^\]]+\]\][ \t]*(?:\r?$)", section)]
        if nested != [f"[[hooks.{event}.hooks]]"]:
            return "unknown"
        if len(re.findall(r'(?m)^[ \t]*type[ \t]*=[ \t]*"[^"]*"[ \t]*(?:\r?$)', section)) != 1:
            return "unknown"
        if not re.search(r'(?m)^[ \t]*type[ \t]*=[ \t]*"command"[ \t]*(?:\r?$)', section):
            return "unknown"
        commands = re.findall(r'(?m)^[ \t]*command[ \t]*=[ \t]*"([^"]*)"[ \t]*(?:\r?$)', section)
        command_windows = re.findall(
            r'(?m)^[ \t]*commandWindows[ \t]*=[ \t]*"([^"]*)"[ \t]*(?:\r?$)', section
        )
        if len(commands) != 1 or len(command_windows) != 1 or command_windows != commands:
            return "unknown"
        escaped_python = PYTHON_EXECUTABLE.replace("\\", "\\\\")
        match = re.fullmatch(
            rf'{re.escape(escaped_python)} -m tools\.codex_semantic_mvp\.hook_entry --mode (active|shadow)',
            commands[0],
        )
        if match is None:
            return "unknown"
        modes.append(match.group(1))
    return modes[0] if len(set(modes)) == 1 else "unknown"


def _mode(
    config_text: str,
    server_valid: bool,
    server_enabled: bool,
    hooks_enabled: bool,
    config_valid: bool = True,
) -> str:
    if not config_valid or not server_valid or not hooks_enabled:
        return "unknown"
    hook_mode = _inline_hook_mode(config_text)
    if hook_mode == "absent":
        return "off" if not server_enabled else "unknown"
    if hook_mode in {"active", "shadow"}:
        if hook_mode == "active" and server_enabled:
            return "active"
        if hook_mode == "shadow" and not server_enabled:
            return "shadow"
    return "unknown"


def _features_hooks_enabled(config_text: str) -> bool:
    match = re.search(r"(?ms)^\[features\][ \t]*\r?\n(.*?)(?=^\[|\Z)", config_text)
    if match is None:
        return False
    section = match.group(1)
    for name in ("hooks",):
        values = re.findall(
            rf"(?m)^[ \t]*{name}[ \t]*=[ \t]*(true|false)[ \t]*(?:\r?$)", section
        )
        if len(values) != 1 or values[0] != "true":
            return False
    return True


def _runtime_writable(runtime_dir: Path) -> bool:
    """Report write capability without creating directories or probe files."""
    try:
        if runtime_dir.exists():
            return runtime_dir.is_dir() and os.access(runtime_dir, os.W_OK)
        parent = runtime_dir.parent
        return parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)
    except OSError:
        return False


def collect_baseline(repo_root: Path, mcp_version_reader: Any = distribution_version) -> dict[str, Any]:
    """Return legacy file entries plus machine-readable activation fields."""
    root = Path(repo_root).resolve()
    config_path = root / ".codex" / "config.toml"
    hooks_path = root / ".codex" / "hooks.json"
    config = _file_baseline(config_path, ".codex/config.toml")
    hooks = _file_baseline(hooks_path, ".codex/hooks.json")
    config_text = config_path.read_text(encoding="utf-8")
    try:
        tomllib.loads(config_text)
    except tomllib.TOMLDecodeError:
        config_valid = False
    else:
        config_valid = True
    present, enabled, _ = _server_config(config_text)
    hooks_enabled = _features_hooks_enabled(config_text)
    return {
        "config_toml": config,
        "hooks_json": hooks,
        "live_hooks_hash": hooks["sha256"],
        "config_hash": config["sha256"],
        "mcp_version": installed_mcp_version(mcp_version_reader),
        "server_config_present": present,
        "server_enabled": enabled,
        "runtime_writable": _runtime_writable(root / "runtime" / "codex-semantic-mvp"),
        "mode": _mode(config_text, present, enabled, hooks_enabled, config_valid),
        "user_trust": {
            "status": USER_TRUST_STATUS,
            "scope": USER_TRUST_SCOPE,
            "message": USER_TRUST_MESSAGE,
        },
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
