"""Operator CLI for the Phase 1 App Server observer."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .codex_binary import resolve_codex_binary
from .config import load_observer_config
from .doctor import collect_doctor
from .observer import ObserverService
from .schema_capture import capture_app_server_schema
from .store import ObserverStore
from .timeline import render_thread_timeline_markdown, thread_timeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-supervisor")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--runtime-home")
    parser.add_argument("--codex-bin")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("schema")
    sub.add_parser("snapshot")
    serve = sub.add_parser("serve")
    serve.add_argument("--duration-seconds", type=float, default=None)
    sub.add_parser("canary")
    timeline = sub.add_parser("timeline")
    timeline.add_argument("--thread-id", required=True)
    timeline.add_argument("--out")
    managed = sub.add_parser("managed")
    managed.add_argument("--operator")
    managed_sub = managed.add_subparsers(dest="managed_command", required=True)
    managed_sub.add_parser("list")
    show = managed_sub.add_parser("show")
    show.add_argument("--binding-id", required=True)
    create = managed_sub.add_parser("create")
    create.add_argument("--actor-context-id", required=True)
    create.add_argument("--semantic-state", required=True)
    create.add_argument("--confirm-global-memory-disabled", action="store_true")
    adopt = managed_sub.add_parser("adopt")
    adopt.add_argument("--actor-context-id", required=True)
    adopt.add_argument("--semantic-state", required=True)
    adopt.add_argument("--thread-id", required=True)
    adopt.add_argument("--allow-existing-history", action="store_true")
    adopt.add_argument("--confirm-history-nonauthoritative", action="store_true")
    verify = managed_sub.add_parser("verify")
    verify.add_argument("--binding-id", required=True)
    activate = managed_sub.add_parser("activate")
    activate.add_argument("--binding-id", required=True)
    turn = managed_sub.add_parser("turn")
    turn.add_argument("--binding-id", required=True)
    turn.add_argument("--text", required=True)
    suspend = managed_sub.add_parser("suspend")
    suspend.add_argument("--binding-id", required=True)
    revoke = managed_sub.add_parser("revoke")
    revoke.add_argument("--binding-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    runtime_home = Path(args.runtime_home) if args.runtime_home else None
    config = load_observer_config(repo_root, runtime_home)
    if args.command == "doctor":
        print(json.dumps(collect_doctor(repo_root, runtime_home=runtime_home, codex_bin=args.codex_bin), indent=2))
        return 0
    if args.command == "schema":
        binary = resolve_codex_binary(args.codex_bin)
        capture = capture_app_server_schema(binary, config.runtime_home / "schema", repo_root=repo_root)
        print(json.dumps({"codex_version": capture.version, "schema_root": str(capture.output_root)}, indent=2))
        return 0
    store = ObserverStore(config.runtime_home)
    try:
        if args.command == "timeline":
            rendered = render_thread_timeline_markdown(thread_timeline(store, args.thread_id))
            if args.out:
                Path(args.out).write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0
        if args.command == "managed":
            return _managed_command(args, repo_root, store)
        binary = resolve_codex_binary(args.codex_bin)
        service = ObserverService(config, binary=binary, store=store)

        async def _run() -> int:
            if args.command == "snapshot":
                await service.start()
                await service.initialize()
                result = await service.reconcile_threads()
                await service.stop("NORMAL")
                print(json.dumps(result, indent=2))
                return 0
            if args.command == "serve":
                result = await service.serve(args.duration_seconds)
                print(json.dumps({"run_id": result.run_id, "end_kind": result.end_kind}, indent=2))
                return 0
            if args.command == "canary":
                result = await service.run_ephemeral_canary()
                print(json.dumps(result.__dict__, indent=2))
                return 0 if result.outcome == "ok" else 1
            raise ValueError(args.command)

        return asyncio.run(_run())
    finally:
        store.close()


def _require_operator(args: argparse.Namespace) -> str:
    operator = str(getattr(args, "operator", None) or "").strip()
    if not operator:
        raise SystemExit("managed mutating commands require --operator")
    return operator


def _managed_command(args: argparse.Namespace, repo_root: Path, store: ObserverStore) -> int:
    from .binding_store import BindingStore

    bindings = BindingStore(store)
    if args.managed_command == "list":
        rows = [
            {
                "binding_id": item.binding_id,
                "actor_kind": item.actor_kind.value,
                "state": item.binding_state.value,
                "thread_id": item.thread_id,
            }
            for item in bindings.list_bindings()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.managed_command == "show":
        item = bindings.get(args.binding_id)
        if item is None:
            raise SystemExit("unknown binding")
        print(json.dumps(item.__dict__, indent=2, default=str))
        return 0
    operator = _require_operator(args)
    if args.managed_command == "suspend":
        print(json.dumps({"binding_id": bindings.suspend(args.binding_id).binding_id, "operator": operator}))
        return 0
    if args.managed_command == "revoke":
        print(json.dumps({"binding_id": bindings.revoke(args.binding_id).binding_id, "operator": operator}))
        return 0
    if args.managed_command == "activate":
        print(json.dumps({"binding_id": bindings.activate(args.binding_id).binding_id, "operator": operator}))
        return 0
    raise SystemExit(f"managed {args.managed_command} requires a live App Server session and is not run from doctor tests")
