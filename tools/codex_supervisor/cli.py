"""Operator CLI for the Phase 1 App Server observer."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .codex_binary import resolve_codex_binary
from .config import load_observer_config
from .doctor import collect_doctor
from .host_control import HostControlChannel
from .host_state import READY_RECORD_SCHEMA, SupervisorReadyRecord, atomic_write_json
from .observer import ObserverService
from .runtime_profiles import RuntimeProfile
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
    serve.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in RuntimeProfile),
        default=RuntimeProfile.OBSERVER.value,
    )
    serve.add_argument("--semantic-state")
    serve.add_argument("--ready-file")
    serve.add_argument("--control-home")
    sub.add_parser("canary")
    timeline = sub.add_parser("timeline")
    timeline.add_argument("--thread-id", required=True)
    timeline.add_argument("--out")
    managed = sub.add_parser("managed")
    managed_sub = managed.add_subparsers(dest="managed_command", required=True)
    managed_sub.add_parser("list")
    show = managed_sub.add_parser("show")
    show.add_argument("--binding-id", required=True)
    mailbox = sub.add_parser("mailbox")
    mailbox_sub = mailbox.add_subparsers(dest="mailbox_command", required=True)
    mailbox_list = mailbox_sub.add_parser("list")
    mailbox_list.add_argument("--target")
    mailbox_show = mailbox_sub.add_parser("show")
    mailbox_show.add_argument("--message-id", required=True)
    scheduler = sub.add_parser("scheduler")
    scheduler_sub = scheduler.add_subparsers(dest="scheduler_command", required=True)
    scheduler_sub.add_parser("status")
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
    profile: RuntimeProfile | None = None
    semantic_state_path: Path | None = None
    if args.command == "serve":
        profile = RuntimeProfile(args.profile)
        semantic_state_path = _semantic_state_for_profile(
            repo_root,
            profile,
            args.semantic_state,
        )
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
            return _managed_command(args, store)
        if args.command == "mailbox":
            return _mailbox_command(args, store)
        if args.command == "scheduler":
            return _scheduler_command(args, store)
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
                assert profile is not None
                ready_file = (
                    _require_external_path(repo_root, Path(args.ready_file), "ready file")
                    if args.ready_file
                    else None
                )
                control_home = _require_external_path(
                    repo_root,
                    Path(args.control_home)
                    if args.control_home
                    else config.runtime_home / "control",
                    "control home",
                )
                if ready_file is not None:
                    _archive_host_signal(
                        ready_file,
                        config.runtime_home,
                        "ready-prelaunch",
                    )

                async def _ready_hook(payload: dict[str, object]) -> None:
                    if ready_file is None:
                        return
                    record = SupervisorReadyRecord(
                        schema=READY_RECORD_SCHEMA,
                        run_id=str(payload["run_id"]),
                        process_id=int(payload["process_id"]),
                        initialized_at=str(payload["initialized_at"]),
                        watcher_active=payload["watcher_active"] is True,
                        first_reconciliation_completed=(
                            payload["first_reconciliation_completed"] is True
                        ),
                        thread_count=int(payload["thread_count"]),
                        runtime_home=str(config.runtime_home),
                        profile=profile.value,
                    )
                    atomic_write_json(ready_file, asdict(record))

                try:
                    result = await service.serve(
                        args.duration_seconds,
                        _ready_hook,
                        control=HostControlChannel(
                            control_home,
                            profile=profile,
                            repo_root=repo_root,
                            semantic_state_path=semantic_state_path,
                        ),
                        profile=profile,
                    )
                finally:
                    if ready_file is not None:
                        _archive_host_signal(
                            ready_file,
                            config.runtime_home,
                            "ready-stopped",
                        )
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


def _require_external_path(repo_root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return resolved
    raise SystemExit(f"{label} must not live inside the repository")


def _semantic_state_for_profile(
    repo_root: Path,
    profile: RuntimeProfile,
    value: str | None,
) -> Path | None:
    if profile is RuntimeProfile.OBSERVER:
        if value is not None:
            raise SystemExit("OBSERVER profile forbids --semantic-state")
        return None
    if value is None or not value.strip():
        raise SystemExit(f"{profile.value} profile requires --semantic-state")
    try:
        resolved = Path(value).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SystemExit("semantic state must be an existing regular file") from exc
    if not resolved.is_file():
        raise SystemExit("semantic state must be an existing regular file")
    resolved = _require_external_path(repo_root, resolved, "semantic state")
    from tools.codex_semantic_mvp.db import (
        SemanticDatabaseValidationError,
        validate_existing_database,
    )

    try:
        return validate_existing_database(resolved)
    except SemanticDatabaseValidationError as exc:
        raise SystemExit(
            f"semantic state is not an initialized compatible HMASD database: {exc}"
        ) from exc


def _archive_host_signal(path: Path, runtime_home: Path, label: str) -> Path | None:
    """Remove one live signal while retaining its bytes as external audit evidence."""

    signal = Path(path)
    if not signal.is_file():
        return None
    archive = Path(runtime_home) / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = archive / f"{label}.{stamp}.{uuid.uuid4().hex}.json"
    shutil.copy2(signal, destination)
    signal.unlink()
    return destination


def _managed_command(args: argparse.Namespace, store: ObserverStore) -> int:
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
    raise SystemExit(f"unknown managed command: {args.managed_command}")


def _mailbox_command(args: argparse.Namespace, store: ObserverStore) -> int:
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
    raise SystemExit(f"unknown mailbox command: {args.mailbox_command}")


def _scheduler_command(args: argparse.Namespace, store: ObserverStore) -> int:
    from .mailbox_store import MailboxStore

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
    raise SystemExit(f"unknown scheduler command: {args.scheduler_command}")
