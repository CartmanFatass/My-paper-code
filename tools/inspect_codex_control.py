"""Inspect repository Codex declarations; never resolve or certify a live session.

Python 3.11+, standard library only. This is an optional maintenance command, not a
research launch gate. It reads repository TOML and prints to stdout; it does not
run Codex, Git, a publisher, a browser, SSH, or any configured command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("model", "model_reasoning_effort", "sandbox_mode", "approval_policy")
AGENT_SETTINGS = (
    "enabled", "max_concurrent_threads_per_session", "max_threads",
    "default_subagent_model", "default_subagent_reasoning_effort", "interrupt_message",
)
LIMITS = (
    "Declared values are not effective runtime settings. Unset values remain unknown.",
    "User/managed config, profiles, App/spawn choices and live permission overrides are not inspected.",
    "A parsed file does not prove native schema support, role selection, instruction adoption or isolation.",
    "Open-thread capacity is not a DM target, an experiment allowance or a research resume.",
)


def inspect_repository(root: Path) -> dict[str, Any]:
    """Return selected source declarations, retaining errors without inventing defaults."""
    root = root.resolve()
    report: dict[str, Any] = {
        "scope": "repository source declarations only",
        "runtime_verified": False,
        "root": None,
        "agent_settings": {},
        "registered_roles": [],
        "unregistered_agent_files": [],
        "errors": [],
        "limitations": list(LIMITS),
    }

    def error(path: str, message: str) -> None:
        report["errors"].append({"path": path, "message": message})

    def contained(path: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("outside selected checkout; not inspected")
        return resolved

    def read_layer(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        try:
            path = contained(path)
            if not path.is_file():
                raise ValueError("missing or not a regular file")
            data = path.read_bytes()
            config = tomllib.loads(data.decode("utf-8"))
        except (OSError, ValueError, RuntimeError) as exc:
            error(label, str(exc))
            return None
        source = {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "declared": {field: config.get(field) for field in FIELDS},
        }
        return config, source

    config_path = root / ".codex/config.toml"
    loaded = read_layer(config_path, ".codex/config.toml")
    if loaded is None:
        return report
    config, report["root"] = loaded
    agents = config.get("agents", {})
    if not isinstance(agents, dict):
        error(".codex/config.toml", "agents is not a TOML table")
        agents = {}
    report["agent_settings"] = {key: agents[key] for key in AGENT_SETTINGS if key in agents}

    referenced: set[Path] = set()
    for name, entry in sorted(agents.items()):
        if name in AGENT_SETTINGS or not isinstance(entry, dict):
            continue
        row: dict[str, Any] = {"registration": name, "config_file": entry.get("config_file"), "source": None}
        report["registered_roles"].append(row)
        if "config_file" not in entry:
            # A description-only role need not have a separate config layer.
            continue
        reference = entry["config_file"]
        if not isinstance(reference, str) or not reference.strip():
            error(f"agents.{name}.config_file", "expected a nonempty path string")
            continue
        # Codex resolves relative role paths from the declaring config, not the CWD.
        path = config_path.parent / reference
        try:
            referenced.add(contained(path))
        except (OSError, ValueError, RuntimeError) as exc:
            error(f"agents.{name}.config_file", str(exc))
            continue
        layer = read_layer(path, f"agents.{name}.config_file ({reference})")
        if layer is not None:
            row["source"] = layer[1]

    # Native versions may discover standalone files too. Absence from [agents]
    # does NOT mean a file is retired or inactive; list it without changing it.
    directory = root / ".codex/agents"
    try:
        directory = contained(directory)
        paths = sorted(directory.iterdir()) if directory.exists() else []
        for path in paths:
            if path.suffix != ".toml":
                continue
            try:
                resolved = contained(path)
            except (OSError, ValueError, RuntimeError) as exc:
                error(path.relative_to(root).as_posix(), str(exc))
                continue
            if resolved in referenced:
                continue
            layer = read_layer(path, path.relative_to(root).as_posix())
            if layer is not None:
                report["unregistered_agent_files"].append({"name": layer[0].get("name"), "source": layer[1]})
    except (OSError, ValueError, RuntimeError) as exc:
        error(".codex/agents", str(exc))
    return report


def render_text(report: dict[str, Any]) -> str:
    lines = ["Codex source inspection — runtime NOT verified"]

    def show(name: str, source: dict[str, Any] | None) -> None:
        lines.append(name)
        if source is None:
            lines.append("  No inspected config layer; do not infer inherited or effective values.")
            return
        lines.append(f"  {json.dumps(source['path'])} (sha256 {source['sha256']})")
        for field, value in source["declared"].items():
            text = "<not declared here>" if value is None else json.dumps(value, ensure_ascii=True, default=str)
            lines.append(f"  {field}: {text}")

    show("Root/project config", report["root"])
    lines.append("Agent settings (declared): " + json.dumps(report["agent_settings"], sort_keys=True, default=str))
    for row in report["registered_roles"]:
        show("Registered role " + json.dumps(row["registration"]), row["source"])
    for row in report["unregistered_agent_files"]:
        show("Standalone file, not referenced by [agents] (NOT proof of inactivity)", row["source"])
    lines.append(f"Inspection errors: {len(report['errors'])}")
    for item in report["errors"]:
        lines.append("  " + json.dumps(item, ensure_ascii=True))
    lines.extend("Note: " + text for text in report["limitations"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Checkout to inspect; no user-level configuration is read")
    parser.add_argument("--json", action="store_true", help="Print the same source-only report as JSON to stdout")
    args = parser.parse_args(argv)
    report = inspect_repository(args.root)
    print(json.dumps(report, indent=2, ensure_ascii=True, default=str) if args.json else render_text(report))
    # Nonzero means inspection failed, not that research is denied. Zero is not
    # certification of permissions, native configuration validity or adoption.
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
