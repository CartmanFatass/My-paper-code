"""Read-only operators for the repository context lifecycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.codex_semantic_mvp.db import DEFAULT_STATE_PATH
from tools.codex_semantic_mvp.store import SemanticStore

from .decisions import write_decision_index
from .doctor import collect_doctor
from .retention import apply_gc_marks, record_dry_run
from .source_registry import load_registry, sources_for_actor
from .working_set import working_set_refs


def _store(state: str | None) -> SemanticStore:
    path = Path(state) if state else DEFAULT_STATE_PATH
    return SemanticStore(path).initialize()


def _print(payload: object) -> int:
    sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--repo-root", default=".")
    shared.add_argument("--state")
    parser = argparse.ArgumentParser(prog="context-lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", parents=[shared])
    sources = sub.add_parser("sources", parents=[shared])
    sources.add_argument("--actor", required=True)
    sources.add_argument("--requested", nargs="*", default=[])
    sub.add_parser("decisions-index", parents=[shared])
    working = sub.add_parser("working-set", parents=[shared])
    working.add_argument("--actor", required=True)
    promotions = sub.add_parser("promotion-list", parents=[shared])
    promotions.add_argument("--epoch", required=True)
    rollover = sub.add_parser("rollover-show", parents=[shared])
    rollover.add_argument("--actor", required=True)
    gc = sub.add_parser("gc", parents=[shared])
    gc.add_argument("--actor")
    gc.add_argument("--dry-run", action="store_true")
    gc.add_argument("--mark-archived", action="store_true")

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    if args.command == "doctor":
        return _print(collect_doctor(repo_root, args.state))
    if args.command == "sources":
        registry = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
        selected = sources_for_actor(
            registry, args.actor, requested_source_ids=tuple(args.requested)
        )
        return _print([source.id for source in selected])
    if args.command == "decisions-index":
        write_decision_index(repo_root)
        return 0
    store = _store(args.state)
    try:
        if args.command == "working-set":
            return _print(working_set_refs(store, args.actor))
        if args.command == "promotion-list":
            from .promotion import promotion_proposals_for_epoch

            return _print(promotion_proposals_for_epoch(store, args.epoch))
        if args.command == "rollover-show":
            from .rollover import current_rollover

            return _print(current_rollover(store, args.actor))
        if args.command == "gc":
            if args.mark_archived:
                return _print(apply_gc_marks(store, actor_context_id=args.actor))
            return _print(record_dry_run(store, actor_context_id=args.actor))
    finally:
        store.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
