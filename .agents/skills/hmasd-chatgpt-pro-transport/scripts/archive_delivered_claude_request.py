"""Record a completed, GitHub-delivered Claude-transport request as ARCHIVED in the registry.

The caller supplies verified completion evidence: the request has one
Send, provider message ids, an archived short receipt, an archived GitHub response and closed
tabs, but bind_conversation.py (which the Claude transport agent runs) leaves the record at
DIRECTION_VERIFIED. This walks the contract's own validated transitions to ARCHIVED for that
exact request id only. It never changes the conversation id and never rebinds a key.

Run with PYTHONUTF8=1 from the repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transport_contract import receipt_has_delivery_evidence, registry_lock, stage_receipt, transition_record, utc_now  # noqa: E402

CHAIN = (
    "TAB_OPEN", "PAGE_READY", "PRO_VERIFIED", "PROMPT_READY", "SEND_ATTEMPTED",
    "SEND_CONFIRMED", "WAITING_GENERATION", "NATURAL_COMPLETION", "ARCHIVE_PENDING", "ARCHIVED",
)


def _read_bytes(path: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except (FileNotFoundError, OSError):
        text = str(Path(path).resolve())
        if os.name == "nt" and not text.startswith("\\\\?\\"):
            text = "\\\\?\\" + text
        return Path(text).read_bytes()


def _sha(path: str) -> str:
    return hashlib.sha256(_read_bytes(path)).hexdigest()


def _iso(value: str) -> str:
    if value.isdigit():
        stamp = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).replace(microsecond=0)
        return stamp.isoformat().replace("+00:00", "Z")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--binding-key", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--user-message-id", required=True)
    parser.add_argument("--assistant-message-id", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--short-receipt", required=True)
    parser.add_argument("--transport-facts", required=True)
    parser.add_argument("--github-response", required=True)
    parser.add_argument("--github-commit", required=True)
    parser.add_argument("--send-attempted-at", required=True)
    parser.add_argument("--completed-at", required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)

    prompt_sha = _sha(args.prompt_file)
    receipt_sha = _sha(args.short_receipt)
    github_sha = _sha(args.github_response)
    now = utc_now()
    sent_at = _iso(args.send_attempted_at)
    completed_at = _iso(args.completed_at)
    archive_map = {
        "prompt_file": str(Path(args.prompt_file).resolve()),
        "response_file": str(Path(args.github_response).resolve()),
        "short_receipt_file": str(Path(args.short_receipt).resolve()),
        "short_receipt_sha256": receipt_sha,
        "transport_fact_file": str(Path(args.transport_facts).resolve()),
        "github_response_file": str(Path(args.github_response).resolve()),
        "github_response_sha256": github_sha,
        "github_commit": args.github_commit,
        "response_sha256": github_sha,
    }

    regpath = Path(args.registry)
    with registry_lock(regpath):
        data = json.loads(regpath.read_text(encoding="utf-8"))
        rec = data["bindings"].get(args.binding_key)
        if not isinstance(rec, dict):
            print(json.dumps({"archived": False, "error": "binding key not found"}))
            return 2
        if rec.get("request_id") != args.request_id:
            print(json.dumps({"archived": False, "error": "request id mismatch",
                              "active_request_id": rec.get("request_id")}))
            return 3
        if rec.get("state") == "ARCHIVED":
            print(json.dumps({"archived": True, "idempotent": True}))
            return 0
        if rec.get("prompt_sha256") not in (None, prompt_sha):
            print(json.dumps({"archived": False, "error": "prompt sha mismatch",
                              "recorded": rec.get("prompt_sha256"), "computed": prompt_sha}))
            return 4
        timestamps = dict(rec.get("timestamps") or {})
        timestamps.setdefault("send_attempted_at", sent_at)
        timestamps.setdefault("completed_at", completed_at)
        timestamps["captured_at"] = timestamps.get("captured_at") or completed_at
        timestamps["archived_at"] = now
        state = str(rec.get("state"))
        start = CHAIN.index(state) + 1 if state in CHAIN else 0
        for next_state in CHAIN[start:]:
            updates: dict = {}
            if next_state == "SEND_ATTEMPTED":
                updates = {"send_click_count": rec.get("send_click_count", 1),
                           "user_message_id": args.user_message_id}
            elif next_state == "NATURAL_COMPLETION":
                updates = {"assistant_message_id": args.assistant_message_id}
            elif next_state == "ARCHIVED":
                updates = {"response_sha256": github_sha, "archive": archive_map,
                           "timestamps": timestamps, "tab_id": None, "tab_lifecycle": "CLOSED"}
            transition_record(rec, next_state, now=now, **updates)
        lease = dict(rec.get("tab_lease") or {})
        lease.update({"handle": None, "lifecycle": "CLOSED", "last_observed_at": completed_at})
        rec["tab_lease"] = lease
        rec["heartbeat"] = {"automation_id": None, "status": "PAUSED", "next_wake_at": None,
                            "retired_at": now, "retirement_verified": True}
        # Archiving proves artifact availability, not parent receipt delivery. Preserve
        # existing routing, attempts and historical message keys without reinterpretation.
        # A fresh receipt uses the normal parent-route contract and remains unsent.
        receipt = rec.get("return_receipt") or {}
        if receipt.get("kind") == "TERMINAL_BLOCKER" or not receipt_has_delivery_evidence(receipt):
            stage_receipt(rec, archive_map, github_sha, now=now)
        rec["delivery"] = {"mode": "github", "commit": args.github_commit,
                           "github_response_sha256": github_sha, "note": args.note}
        rec["updated_at"] = now
        drec = (data.get("directions") or {}).get(str(rec.get("direction_id")))
        if isinstance(drec, dict) and drec.get("request_id") == args.request_id:
            for key in ("state", "response_sha256", "archive", "tab_id", "tab_lifecycle",
                        "tab_lease", "send_click_count", "user_message_id",
                        "assistant_message_id", "timestamps", "heartbeat", "return_receipt",
                        "return_receipt_state",
                        "return_receipt_history",
                        "delivery"):
                if key in rec:
                    drec[key] = json.loads(json.dumps(rec[key]))
            drec["updated_at"] = now
            drec["binding_reconciliation"] = {
                "kind": "archived_direction_mirror", "binding_key": args.binding_key,
                "binding_state": "ARCHIVED", "binding_updated_at": now}
        data["updated_at"] = now
        tmp = regpath.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, regpath)
    print(json.dumps({"archived": True, "state": "ARCHIVED", "request_id": args.request_id,
                      "binding_key": args.binding_key, "response_sha256": github_sha,
                      "github_response_sha256": github_sha}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
