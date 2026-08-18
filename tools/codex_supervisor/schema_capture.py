"""Capture the installed App Server JSON Schema into external runtime state."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .codex_binary import read_codex_version, resolve_codex_binary
from .config import load_observer_config
from .models import SchemaCapture

import subprocess

REQUIRED_METHOD_STRINGS = (
    "initialize",
    "thread/start",
    "thread/list",
    "thread/read",
    "turn/start",
    "turn/completed",
    "item/started",
    "item/completed",
)


class SchemaCaptureError(RuntimeError):
    """Raised when schema capture is incomplete or writes into the repository."""


def _normalize_version(version: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", version.strip())
    return cleaned or "unknown"


def capture_app_server_schema(binary: Path, output_root: Path, repo_root: Path | None = None) -> SchemaCapture:
    resolved = Path(binary).resolve()
    version = read_codex_version(resolved)
    destination = Path(output_root) / _normalize_version(version)
    if repo_root is not None:
        try:
            destination.resolve().relative_to(Path(repo_root).resolve())
        except ValueError:
            pass
        else:
            raise SchemaCaptureError("schema capture must not write inside the repository")
    destination.mkdir(parents=True, exist_ok=True)
    command = [str(resolved), "app-server", "generate-json-schema", "--out", str(destination)]
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )
    files = sorted(str(path.relative_to(destination)) for path in destination.rglob("*") if path.is_file())
    if not files:
        raise SchemaCaptureError("schema capture produced no files")
    blob = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in destination.rglob("*") if path.is_file())
    missing = [item for item in REQUIRED_METHOD_STRINGS if item not in blob]
    if missing:
        raise SchemaCaptureError(f"generated schema missing required method strings: {missing}")
    observed = tuple(item for item in REQUIRED_METHOD_STRINGS if item in blob)
    manifest = {
        "codex_binary": str(resolved),
        "codex_version": version,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "schema_files": files,
        "observed_methods": list(observed),
    }
    manifest_path = destination / "capture-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return SchemaCapture(
        binary=resolved,
        version=version,
        output_root=destination,
        schema_files=tuple(files),
        observed_methods=observed,
        manifest_path=manifest_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture the installed Codex App Server schema.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--codex-bin")
    parser.add_argument("--runtime-home")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    config = load_observer_config(repo_root, Path(args.runtime_home) if args.runtime_home else None)
    binary = resolve_codex_binary(args.codex_bin)
    capture = capture_app_server_schema(binary, config.runtime_home / "schema", repo_root=repo_root)
    print(json.dumps({"codex_version": capture.version, "schema_root": str(capture.output_root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
