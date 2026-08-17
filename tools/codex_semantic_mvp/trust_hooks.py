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
    desktop = Path(r"C:\Users\fires\AppData\Local\OpenAI\Codex\bin\e305f1c75d8da435\codex.exe")
    if desktop.is_file():
        return [str(desktop)]
    npm_js = Path(r"C:\Users\fires\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js")
    if npm_js.is_file() and shutil.which("node"):
        return ["node", str(npm_js)]
    for name in ("codex.cmd", "codex"):
        resolved = shutil.which(name)
        if resolved:
            return [resolved]
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


def _semantic_hooks(entries: list[dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    repo = repo_root.resolve()
    for entry in entries:
        for hook in entry.get("hooks") or []:
            command = str(hook.get("command") or "")
            source_path = str(hook.get("sourcePath") or "")
            if REPO_MARKER not in command:
                continue
            if source_path:
                try:
                    if repo not in Path(source_path).resolve().parents and Path(source_path).resolve() != repo / ".codex" / "config.toml":
                        if repo.as_posix().lower() not in source_path.replace("\\", "/").lower():
                            continue
                except OSError:
                    if REPO_MARKER not in command:
                        continue
            selected.append(hook)
    return selected


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
        if not hooks:
            return {"trusted": 0, "already_trusted": 0, "hooks": [], "listed": entries}
        edits = []
        report = []
        already = 0
        for hook in hooks:
            key = str(hook.get("key") or "")
            current = str(hook.get("currentHash") or "")
            status = str(hook.get("trustStatus") or "")
            if not key or not current:
                raise AppServerError(f"hook metadata missing key/hash: {hook!r}")
            report.append(
                {
                    "eventName": hook.get("eventName"),
                    "key": key,
                    "currentHash": current,
                    "trustStatus": status,
                }
            )
            if status == "trusted" and current:
                already += 1
                continue
            edits.append(
                {
                    "keyPath": "hooks.state.'" + key.replace("'", "''") + "'.trusted_hash",
                    "mergeStrategy": "upsert",
                    "value": current if current.startswith("sha256:") else f"sha256:{current}",
                }
            )
        if edits:
            server.request("config/batchWrite", {"edits": edits, "reloadUserConfig": True})
        return {
            "trusted": len(edits),
            "already_trusted": already,
            "hooks": report,
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
