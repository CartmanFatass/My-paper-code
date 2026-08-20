"""Deterministic JSON operator commands for local semantic-MVP diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-semantic-mvp")
    parser.add_argument("--state-dir", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("runtime-health")
    open_parser = sub.add_parser("workflow-open")
    open_parser.add_argument("session_id")
    open_parser.add_argument("opened_turn_id")
    open_parser.add_argument("scope")
    open_parser.add_argument("objective")

    state_parser = sub.add_parser("workflow-state")
    state_parser.add_argument("workflow_id")

    events_parser = sub.add_parser("events-after")
    events_parser.add_argument("workflow_id")
    events_parser.add_argument("--after-seq", type=int, default=0)

    close_parser = sub.add_parser("workflow-close")
    close_parser.add_argument("workflow_id")
    close_parser.add_argument("closure_kind")
    close_parser.add_argument("--summary", default="")

    reconcile_parser = sub.add_parser("workflow-reconcile")
    reconcile_parser.add_argument("--workflow-id", required=True)
    reconcile_parser.add_argument("--expected-state-version", required=True, type=int)
    reconcile_parser.add_argument("--expected-await-cursor", required=True, type=int)
    reconcile_parser.add_argument("--reconciliation-id", required=True)
    reconcile_parser.add_argument("--reason", required=True)
    mode = reconcile_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    reconcile_parser.add_argument("--operator-id")
    reconcile_parser.add_argument("--confirm-workflow-id")

    return parser


def _require_reconcile_pause(repo_root: Path) -> None:
    """Fail closed unless semantic hooks are explicitly paused."""
    sentinel = repo_root / ".codex" / "semantic-hooks.paused"
    if not sentinel.is_file():
        raise RuntimeError("workflow-reconcile requires .codex/semantic-hooks.paused")
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10 project environment
        import tomli as tomllib

    config_path = repo_root / ".codex" / "config.toml"
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError("workflow-reconcile could not read .codex/config.toml") from exc
    if config.get("features", {}).get("hooks") is not False:
        raise RuntimeError("workflow-reconcile requires features.hooks=false")


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "workflow-reconcile":
        # Check the operator-owned pause boundary before even opening or
        # migrating the selected ledger.
        _require_reconcile_pause(Path.cwd())
        if args.apply:
            if args.confirm_workflow_id != args.workflow_id:
                raise ValueError("--confirm-workflow-id must exactly match --workflow-id")
            if args.operator_id != "/root":
                raise ValueError("--apply requires --operator-id /root")
        elif args.operator_id is not None or args.confirm_workflow_id is not None:
            raise ValueError("operator confirmation arguments are valid only with --apply")

    from . import mcp_server

    mcp_server.build_server(args.state_dir)
    store = mcp_server._get_store()
    if args.command == "runtime-health":
        return {"status": "OK", "server": mcp_server.SERVER_NAME, "schema_version": 1}
    if args.command == "workflow-open":
        workflow_id = store.open_workflow(
            session_id=args.session_id,
            opened_turn_id=args.opened_turn_id,
            scope=args.scope,
            objective=args.objective,
        )
        return {"workflow_id": workflow_id, "state": "ACTIVE"}
    if args.command == "workflow-state":
        return store.workflow_state(args.workflow_id)
    if args.command == "events-after":
        return {"workflow_id": args.workflow_id, "events": store.events_after(args.workflow_id, args.after_seq)}
    if args.command == "workflow-close":
        receipt_id = store.create_closure_receipt(args.workflow_id, args.closure_kind, args.summary)
        return {"workflow_id": args.workflow_id, "receipt_id": receipt_id, "closure_kind": args.closure_kind}
    if args.command == "workflow-reconcile":
        return store.reconcile_workflow(
            args.workflow_id,
            expected_state_version=args.expected_state_version,
            expected_await_cursor=args.expected_await_cursor,
            reconciliation_id=args.reconciliation_id,
            reason=args.reason,
            apply=bool(args.apply),
            operator_id=args.operator_id,
        )
    raise ValueError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        print(json.dumps(_dispatch(args), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
