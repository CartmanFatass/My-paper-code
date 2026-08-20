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
from .timeline import mailbox_timeline, render_thread_timeline_markdown, thread_timeline, wake_timeline


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
    mailbox = sub.add_parser("mailbox")
    mailbox_sub = mailbox.add_subparsers(dest="mailbox_command", required=True)
    mailbox_list = mailbox_sub.add_parser("list")
    mailbox_list.add_argument("--target")
    mailbox_show = mailbox_sub.add_parser("show")
    mailbox_show.add_argument("--message-id", required=True)
    mailbox_send = mailbox_sub.add_parser("send-operator")
    mailbox_send.add_argument("--operator", required=True)
    mailbox_send.add_argument("--target-actor-context-id", required=True)
    mailbox_send.add_argument("--subject-ref", required=True)
    mailbox_send.add_argument("--payload-ref", required=True)
    mailbox_dead = mailbox_sub.add_parser("dead-letter")
    mailbox_dead.add_argument("--operator", required=True)
    mailbox_dead.add_argument("--message-id", required=True)
    mailbox_dead.add_argument("--reason", required=True)
    scheduler = sub.add_parser("scheduler")
    scheduler_sub = scheduler.add_subparsers(dest="scheduler_command", required=True)
    scheduler_once = scheduler_sub.add_parser("once")
    scheduler_once.add_argument("--semantic-state", required=True)
    scheduler_once.add_argument("--operator", required=True)
    scheduler_sub.add_parser("status")
    serve_sched = scheduler_sub.add_parser("serve")
    serve_sched.add_argument("--semantic-state", required=True)
    serve_sched.add_argument("--operator", required=True)
    serve_sched.add_argument("--duration-seconds", type=float, default=None)
    wake = sub.add_parser("wake")
    wake_sub = wake.add_subparsers(dest="wake_command", required=True)
    wake_show = wake_sub.add_parser("show")
    wake_show.add_argument("--wake-batch-id")
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
                export_root = (config.runtime_home / "exports").resolve()
                export_root.mkdir(parents=True, exist_ok=True)
                dest = Path(args.out)
                resolved = dest.resolve() if dest.is_absolute() else (export_root / dest).resolve()
                try:
                    resolved.relative_to(export_root)
                except ValueError as exc:
                    raise SystemExit("timeline --out must be under <runtime_home>/exports/") from exc
                resolved.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0
        if args.command == "managed":
            return _managed_command(args, repo_root, store)
        if args.command == "mailbox":
            return _mailbox_command(args, store)
        if args.command == "scheduler":
            return _scheduler_command(args, repo_root, store)
        if args.command == "wake":
            print(json.dumps(wake_timeline(store, args.wake_batch_id), indent=2, default=str))
            return 0
        binary = resolve_codex_binary(args.codex_bin)
        service = ObserverService(config, binary=binary, store=store)

        async def _run() -> int:
            if args.command == "snapshot":
                result = await service.run_snapshot()
                if hasattr(result, "end_kind"):
                    print(json.dumps({"run_id": result.run_id, "end_kind": result.end_kind}, indent=2))
                    return 0 if result.end_kind == "NORMAL" else 1
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
        raise SystemExit("managed activate cannot bypass verification; use the verification receipt API")
    raise SystemExit(f"managed {args.managed_command} requires a live App Server session and is not run from doctor tests")


def _mailbox_command(args: argparse.Namespace, store: ObserverStore) -> int:
    from .mailbox_models import MailboxMessageKind, MailboxSourceSystem
    from .mailbox_store import MailboxStore

    mailbox = MailboxStore(store)
    if args.mailbox_command == "list":
        rows = [item.__dict__ for item in mailbox.list_messages(target_actor_context_id=args.target)]
        print(json.dumps(rows, indent=2, default=str))
        return 0
    if args.mailbox_command == "show":
        item = mailbox.get(args.message_id)
        if item is None:
            raise SystemExit("unknown mailbox message")
        print(json.dumps(item.__dict__, indent=2, default=str))
        return 0
    if args.mailbox_command == "send-operator":
        if not str(args.operator).strip():
            raise SystemExit("operator identity is required")
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key=f"operator:{args.operator}:{args.target_actor_context_id}:{args.subject_ref}",
            target_actor_context_id=args.target_actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref=args.subject_ref,
            payload_ref=args.payload_ref,
            priority=20,
        )
        print(json.dumps(message.__dict__, indent=2, default=str))
        return 0
    if args.mailbox_command == "dead-letter":
        if not str(args.operator).strip():
            raise SystemExit("operator identity is required")
        message = mailbox.dead_letter(args.message_id, args.reason)
        print(json.dumps(message.__dict__, indent=2, default=str))
        return 0
    raise SystemExit(f"unknown mailbox command: {args.mailbox_command}")


def _scheduler_command(args: argparse.Namespace, repo_root: Path, store: ObserverStore) -> int:
    from .binding_store import BindingStore
    from .mailbox_store import MailboxStore
    from .scheduler_leases import SchedulerLeases
    from .semantic_bridge import SemanticBridge
    from .semantic_scanner import SemanticScanner
    from .wake_batches import WakeBatchStore
    from .wake_recovery import WakeRecovery
    from .wake_scheduler import WakeScheduler

    mailbox = MailboxStore(store)
    if args.scheduler_command == "status":
        print(
            json.dumps(
                {
                    "leases": [
                        dict(row)
                        for row in store.connection.execute("SELECT * FROM scheduler_leases").fetchall()
                    ],
                    "open_wake_batches": [
                        dict(row)
                        for row in store.connection.execute(
                            "SELECT * FROM wake_batches WHERE state IN ('PREPARED','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE')"
                        ).fetchall()
                    ],
                    "mailbox": mailbox_timeline(store),
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.scheduler_command in {"once", "serve"}:
        bridge = SemanticBridge(Path(args.semantic_state), store)
        try:
            bindings = BindingStore(store, bridge)
            batches = WakeBatchStore(store, mailbox)
            scheduler = WakeScheduler(
                bindings,
                mailbox,
                batches,
                SchedulerLeases(store),
                WakeRecovery(bindings, mailbox, batches, None, bridge=bridge),
                SemanticScanner(mailbox, bridge),
                bridge,
                None,
                instance_id=f"cli:{args.operator}",
            )
            if args.scheduler_command == "once":
                scanned = scheduler.scanner.scan()
                print(json.dumps({"scanned": scanned, "live_wake": False}, indent=2))
                return 0
            raise SystemExit("scheduler serve requires a live App Server session and is deferred until quota restore")
        finally:
            bridge.close()
    raise SystemExit(f"unknown scheduler command: {args.scheduler_command}")
