"""Trust the repository semantic hooks in the user-level Codex config.

Uses the official app-server methods ``hooks/list`` and ``config/batchWrite``.
This writes only ``hooks.state.<key>.trusted_hash`` records. It does not change
repository configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .constants import ACTIVE_HOOK_EVENTS, HOOK_ENTRY_MODULE, SHADOW_HOOK_EVENTS


REPO_MARKER = "tools.codex_semantic_mvp.hook_entry"
DEFAULT_CLIENT = {"name": "hmasd-semantic-mvp-trust", "version": "1.0"}


class AppServerError(RuntimeError):
    """Raised when the Codex app-server protocol cannot complete a request."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_codex() -> list[str]:
    env_cmd = os.environ.get("CODEX_BIN")
    if env_cmd:
        return [env_cmd]
    for name in ("codex.cmd", "codex"):
        resolved = shutil.which(name)
        if resolved:
            return [resolved]
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        bin_root = Path(local_app) / "OpenAI" / "Codex" / "bin"
        if bin_root.is_dir():
            direct = bin_root / "codex.exe"
            if direct.is_file():
                return [str(direct)]
            hashed = sorted(bin_root.glob("*/codex.exe"), key=lambda path: path.stat().st_mtime, reverse=True)
            if hashed:
                return [str(hashed[0])]
    roaming = os.environ.get("APPDATA")
    if roaming:
        npm_js = Path(roaming) / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        if npm_js.is_file() and shutil.which("node"):
            return ["node", str(npm_js)]
    raise AppServerError("cannot resolve a Codex executable")


def _encode(message: dict[str, Any]) -> bytes:
    payload = {"jsonrpc": "2.0", **message}
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def _read_message(stream) -> dict[str, Any]:
    line = stream.readline()
    if not line:
        raise AppServerError("app-server closed stdout")
    try:
        return json.loads(line.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AppServerError(f"invalid app-server payload: {line!r}") from exc


class AppServer:
    def __init__(self, cwd: Path) -> None:
        self._cwd = cwd
        self._next_id = 1
        command = [*_resolve_codex(), "app-server", "--listen", "stdio://"]
        self._proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self._proc.stdin is None or self._proc.stdout is None:
            raise AppServerError("app-server pipes were not created")

    def close(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self._next_id
        self._next_id += 1
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None
        self._proc.stdin.write(_encode({"id": request_id, "method": method, "params": params or {}}))
        self._proc.stdin.flush()
        while True:
            message = _read_message(self._proc.stdout)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise AppServerError(f"{method} failed: {message['error']}")
            return message.get("result")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.write(_encode({"method": method, "params": params or {}}))
        self._proc.stdin.flush()


def expected_config_path(repo_root: Path) -> Path:
    return (repo_root / ".codex" / "config.toml").resolve()


def expected_hook_key(repo_root: Path, event: str) -> str:
    return f"{expected_config_path(repo_root)}:{event}:0:0"


def _normalize_hash(value: str) -> str:
    return value if value.startswith("sha256:") else f"sha256:{value}"


def _trusted_hash_key_path(key: str) -> str:
    return "hooks.state.'" + key.replace("'", "''") + "'.trusted_hash"


def select_and_validate_hooks(
    entries: list[dict[str, Any]],
    repo_root: Path,
) -> list[dict[str, Any]]:
    """Return the exact managed hook set, or raise if the allowlist does not match."""
    repo = repo_root.resolve()
    expected_source = expected_config_path(repo)
    selected: list[dict[str, Any]] = []
    extras: list[str] = []
    for entry in entries:
        for hook in entry.get("hooks") or []:
            command = str(hook.get("command") or "")
            if REPO_MARKER not in command:
                continue
            source_path = str(hook.get("sourcePath") or "")
            event = str(hook.get("eventName") or "")
            key = str(hook.get("key") or "")
            if not source_path:
                extras.append(f"{event or 'unknown'}:missing_sourcePath")
                continue
            try:
                resolved_source = Path(source_path).resolve()
            except OSError as exc:
                raise AppServerError(f"unresolvable hook sourcePath: {source_path}") from exc
            if resolved_source != expected_source:
                extras.append(f"{event}:{source_path}")
                continue
            selected.append(hook)
            if HOOK_ENTRY_MODULE not in command or "--mode " not in command:
                extras.append(f"{event}:command")
            if key != expected_hook_key(repo, event):
                extras.append(f"{event}:key")
    events = [str(hook.get("eventName") or "") for hook in selected]
    event_set = set(events)
    if extras:
        raise AppServerError(f"hook allowlist extras or mismatches: {extras}")
    if event_set == set(ACTIVE_HOOK_EVENTS) and len(events) == len(ACTIVE_HOOK_EVENTS):
        expected_mode = "active"
        expected_events = ACTIVE_HOOK_EVENTS
    elif event_set == set(SHADOW_HOOK_EVENTS) and len(events) == len(SHADOW_HOOK_EVENTS):
        expected_mode = "shadow"
        expected_events = SHADOW_HOOK_EVENTS
    else:
        raise AppServerError(
            f"expected exact {list(ACTIVE_HOOK_EVENTS)} or {list(SHADOW_HOOK_EVENTS)}, got {events}"
        )
    commands = {str(hook.get("command") or "") for hook in selected}
    if len(commands) != 1:
        raise AppServerError("managed hooks must share one reviewed command")
    command = next(iter(commands))
    if f"{HOOK_ENTRY_MODULE} --mode {expected_mode}" not in command:
        raise AppServerError(f"reviewed command must use --mode {expected_mode}")
    hashes = {_normalize_hash(str(hook.get("currentHash") or "")) for hook in selected}
    if any(not item or item == "sha256:" for item in hashes):
        raise AppServerError("hook metadata missing currentHash")
    if len(hashes) != 1:
        raise AppServerError("managed hooks must share one currentHash")
    missing = [event for event in expected_events if event not in event_set]
    if missing:
        raise AppServerError(f"missing managed hook events: {missing}")
    return selected


def _semantic_hooks(entries: list[dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    return select_and_validate_hooks(entries, repo_root)


def trust_repository_hooks(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or _repo_root()).resolve()
    server = AppServer(root)
    try:
        server.request(
            "initialize",
            {"clientInfo": DEFAULT_CLIENT, "capabilities": None},
        )
        listed = server.request("hooks/list", {"cwds": [str(root)]})
        entries = listed.get("data") if isinstance(listed, dict) else listed
        if not isinstance(entries, list):
            raise AppServerError(f"unexpected hooks/list payload: {listed!r}")
        hooks = _semantic_hooks(entries, root)
        edits = []
        report = []
        already = 0
        for hook in hooks:
            key = str(hook.get("key") or "")
            current = _normalize_hash(str(hook.get("currentHash") or ""))
            status = str(hook.get("trustStatus") or "")
            report.append(
                {
                    "eventName": hook.get("eventName"),
                    "key": key,
                    "currentHash": current,
                    "trustStatus": status,
                    "keyPath": _trusted_hash_key_path(key),
                }
            )
            if status == "trusted" and current:
                already += 1
                continue
            edits.append(
                {
                    "keyPath": _trusted_hash_key_path(key),
                    "mergeStrategy": "upsert",
                    "value": current,
                }
            )
        if edits:
            server.request("config/batchWrite", {"edits": edits, "reloadUserConfig": True})
        listed_after = server.request("hooks/list", {"cwds": [str(root)]})
        after_entries = listed_after.get("data") if isinstance(listed_after, dict) else listed_after
        if not isinstance(after_entries, list):
            raise AppServerError(f"unexpected hooks/list payload after write: {listed_after!r}")
        verified = select_and_validate_hooks(after_entries, root)
        before_hashes = {
            str(hook.get("eventName") or ""): _normalize_hash(str(hook.get("currentHash") or ""))
            for hook in hooks
        }
        for hook in verified:
            event = str(hook.get("eventName") or "")
            if str(hook.get("trustStatus") or "") != "trusted":
                raise AppServerError(f"hook {event} is not trusted after write-back")
            if _normalize_hash(str(hook.get("currentHash") or "")) != before_hashes.get(event):
                raise AppServerError(f"hook {event} currentHash changed after write-back")
        return {
            "trusted": len(edits),
            "already_trusted": already,
            "hooks": report,
            "verified": True,
        }
    finally:
        server.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trust HMASD semantic hooks in the user Codex config")
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)
    try:
        result = trust_repository_hooks(args.repo_root)
    except AppServerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
