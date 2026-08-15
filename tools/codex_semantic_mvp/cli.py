"""Deterministic JSON operator commands for local semantic-MVP diagnostics."""

from __future__ import annotations

import argparse
import json
from typing import Any

from . import mcp_server


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

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
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
