#!/usr/bin/env python3
"""Build and verify HMASD v2 session-envelope transport artifacts."""
from __future__ import annotations

import argparse, hashlib, json, os, re, subprocess, sys, uuid
from pathlib import Path
from typing import Any, Mapping

EPOCH = 2
DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}")
MANAGER = re.compile(r"(EM|CM)/([a-z0-9][a-z0-9_-]{1,63})/g[1-9][0-9]*")
SHA = re.compile(r"[0-9a-f]{64}")
KINDS = {"ASSIGNMENT", "RETURN", "PORTFOLIO_RETURN", "CONTROL_NOTICE"}
STATUSES = {"REQUEST_EM", "REQUEST_CM", "REQUEST_PORTFOLIO", "REQUEST_USER", "WAIT_RESOURCE", "FAILED"}
ASSIGN_FIELDS = {"objective", "context_refs", "owned_paths", "effects", "constraints", "done_when", "workspace_mode"}
RETURN_FIELDS = {"status", "summary", "changed_paths", "artifact_refs", "next_objective", "failure"}
FAIL_FIELDS = {"scope", "code", "fingerprint", "responsible_role", "retryable", "attempt", "max_attempts", "summary"}
PORT_FIELDS = {"registry_revision", "snapshot_digest", "considered", "transitions", "capacity", "summary", "artifact_refs", "failure"}
NOTICE_FIELDS = {"action", "reason", "target_identity", "scope"}
ACTIONS = {"PAUSE", "RESUME", "OVERRIDE", "CANCEL", "REANCHOR"}
LINE = re.compile(r"HMASD_SESSION_ENVELOPE_V2 kind=(?P<kind>ASSIGNMENT|RETURN|PORTFOLIO_RETURN|CONTROL_NOTICE) direction=(?P<direction>\S+) from=(?P<sender>\S+) to=(?P<recipient>\S+) next=(?P<next>\S+) id=(?P<id>[0-9a-f-]{36}) sha256=(?P<sha>[0-9a-f]{64}) locator=(?P<locator>\S+)")

class EnvelopeError(ValueError): pass

def load(path: Path, label: str) -> dict[str, Any]:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise EnvelopeError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, Mapping): raise EnvelopeError(f"{label} must be a JSON object")
    return dict(value)

def body_sha(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def path_value(value: Any, label: str) -> str:
    if not isinstance(value, str): raise EnvelopeError(f"{label} must be a repository-relative POSIX path")
    normalized = value[:-1] if value.endswith("/") else value
    if not normalized or "\\" in value or Path(value).is_absolute() or any(p in {"", ".", ".."} for p in normalized.split("/")):
        raise EnvelopeError(f"{label} must be a repository-relative POSIX path")
    return value

def target(repo: Path, relative: str, label: str) -> Path:
    result = (repo / relative).resolve()
    try: result.relative_to(repo.resolve())
    except ValueError as exc: raise EnvelopeError(f"{label} resolves outside repository") from exc
    return result

def strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value): raise EnvelopeError(f"{label} must be a list of non-empty strings")
    return list(value)

def refs(value: Any, label: str, repo: Path, verify: bool = True) -> list[dict[str, str]]:
    if not isinstance(value, list): raise EnvelopeError(f"{label} must be a list")
    result = []
    for i, ref in enumerate(value):
        item = f"{label}[{i}]"
        if not isinstance(ref, Mapping) or set(ref) != {"path", "sha256"}: raise EnvelopeError(f"{item} must contain path and sha256")
        path = path_value(ref["path"], f"{item}.path"); digest = ref["sha256"]
        if not isinstance(digest, str) or SHA.fullmatch(digest) is None: raise EnvelopeError(f"{item}.sha256 is invalid")
        if verify:
            try: observed = hashlib.sha256(target(repo, path, f"{item}.path").read_bytes()).hexdigest()
            except OSError as exc: raise EnvelopeError(f"{item}.path is not readable") from exc
            if observed != digest: raise EnvelopeError(f"{item}.sha256 does not match path bytes")
        result.append({"path": path, "sha256": digest})
    return result

def endpoint(value: Any, direction: str, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"identity", "thread_id"}: raise EnvelopeError(f"{label} must contain identity and thread_id")
    identity, thread_id = value["identity"], value["thread_id"]
    if not isinstance(identity, str) or not identity or not isinstance(thread_id, str) or not thread_id: raise EnvelopeError(f"{label} is invalid")
    match = MANAGER.fullmatch(identity)
    if match and match.group(2) != direction: raise EnvelopeError(f"{label} direction does not match direction_id")
    return {"identity": identity, "thread_id": thread_id}

def role(identity: str) -> str:
    match = MANAGER.fullmatch(identity); return match.group(1) if match else identity

def assignment_body(value: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    if set(value) != ASSIGN_FIELDS: raise EnvelopeError("assignment body fields are invalid")
    if not isinstance(value["objective"], str) or not value["objective"]: raise EnvelopeError("assignment objective must be non-empty")
    if value["workspace_mode"] not in {"shared-main", "separate-worktree"}: raise EnvelopeError("assignment workspace_mode is invalid")
    owned = [path_value(x, f"assignment owned_paths[{i}]") for i, x in enumerate(strings(value["owned_paths"], "assignment owned_paths"))]
    return {"objective": value["objective"], "context_refs": refs(value["context_refs"], "assignment context_refs", repo), "owned_paths": owned, "effects": strings(value["effects"], "assignment effects"), "constraints": strings(value["constraints"], "assignment constraints"), "done_when": strings(value["done_when"], "assignment done_when"), "workspace_mode": value["workspace_mode"]}

def failure(value: Any) -> dict[str, Any] | None:
    if value is None: return None
    if not isinstance(value, Mapping) or set(value) != FAIL_FIELDS: raise EnvelopeError("failure fields are invalid")
    if value["scope"] not in {"project", "direction", "feature", "effect"}: raise EnvelopeError("failure scope is invalid")
    for key in ("code", "fingerprint", "responsible_role", "summary"):
        if not isinstance(value[key], str) or not value[key]: raise EnvelopeError(f"failure {key} must be non-empty")
    if not isinstance(value["retryable"], bool): raise EnvelopeError("failure retryable must be boolean")
    a, m = value["attempt"], value["max_attempts"]
    if not isinstance(a, int) or isinstance(a, bool) or not isinstance(m, int) or isinstance(m, bool) or not 1 <= a <= m <= 3: raise EnvelopeError("failure attempts must satisfy 1 <= attempt <= max_attempts <= 3")
    return dict(value)

def contained(path: str, owned: list[str]) -> bool:
    folded = path.casefold(); return any(folded.startswith(x.casefold()) if x.endswith("/") else folded == x.casefold() for x in owned)

def return_body(value: Mapping[str, Any], repo: Path, owned: list[str]) -> dict[str, Any]:
    if set(value) != RETURN_FIELDS: raise EnvelopeError("return body fields are invalid")
    status, summary, nxt = value["status"], value["summary"], value["next_objective"]
    if status not in STATUSES: raise EnvelopeError("return status is invalid")
    if not isinstance(summary, str) or not summary: raise EnvelopeError("return summary must be non-empty")
    if status.startswith("REQUEST_") and (not isinstance(nxt, str) or not nxt): raise EnvelopeError("request return requires next_objective")
    if nxt is not None and (not isinstance(nxt, str) or not nxt): raise EnvelopeError("next_objective must be null or non-empty")
    fail = failure(value["failure"])
    if (status == "FAILED") != (fail is not None): raise EnvelopeError("only FAILED return requires typed failure")
    changed = [path_value(x, f"return changed_paths[{i}]") for i, x in enumerate(strings(value["changed_paths"], "return changed_paths"))]
    for i, path in enumerate(changed):
        if not contained(path, owned): raise EnvelopeError(f"return changed_paths[{i}] is outside assignment owned_paths")
    return {"status": status, "summary": summary, "changed_paths": changed, "artifact_refs": refs(value["artifact_refs"], "return artifact_refs", repo), "next_objective": nxt, "failure": fail}

def portfolio_body(value: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    if set(value) != PORT_FIELDS: raise EnvelopeError("portfolio return body fields are invalid")
    if not isinstance(value["summary"], str) or not value["summary"]: raise EnvelopeError("portfolio return summary must be non-empty")
    if not isinstance(value["snapshot_digest"], str) or SHA.fullmatch(value["snapshot_digest"]) is None: raise EnvelopeError("portfolio return snapshot_digest is invalid")
    if not isinstance(value["considered"], list) or not isinstance(value["transitions"], list) or not isinstance(value["capacity"], Mapping): raise EnvelopeError("portfolio return considered/transitions/capacity are invalid")
    fail = failure(value["failure"])
    return {"registry_revision": value["registry_revision"], "snapshot_digest": value["snapshot_digest"], "considered": value["considered"], "transitions": value["transitions"], "capacity": dict(value["capacity"]), "summary": value["summary"], "artifact_refs": refs(value["artifact_refs"], "portfolio artifact_refs", repo), "failure": fail}

def notice_body(value: Mapping[str, Any]) -> dict[str, Any]:
    if set(value) != NOTICE_FIELDS or value.get("action") not in ACTIONS: raise EnvelopeError("control notice body is invalid")
    if not isinstance(value["reason"], str) or not value["reason"] or not isinstance(value["target_identity"], str) or not value["target_identity"] or not isinstance(value["scope"], Mapping): raise EnvelopeError("control notice body is invalid")
    if value["action"] == "REANCHOR" and (not isinstance(value["scope"].get("expected_control_release_id"), str) or SHA.fullmatch(value["scope"]["expected_control_release_id"]) is None): raise EnvelopeError("REANCHOR requires scope.expected_control_release_id")
    return {"action": value["action"], "reason": value["reason"], "target_identity": value["target_identity"], "scope": dict(value["scope"])}

def git(repo: Path, *args: str) -> str | None:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return run.stdout.strip() if run.returncode == 0 else None

def git_facts(repo: Path) -> dict[str, Any]:
    branch, head, origin = git(repo, "branch", "--show-current"), git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "--verify", "origin/main")
    status_run = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=all"], capture_output=True, text=True, check=False)
    status = status_run.stdout if status_run.returncode == 0 else ""
    dirty = sorted(line[3:].replace("\\", "/") for line in status.splitlines() if len(line) >= 4)
    return {"branch": branch, "head": head, "origin_main": origin, "dirty_paths": dirty, "head_published": bool(head and origin and head == origin)}

def release(repo: Path) -> dict[str, Any]:
    try:
        from hmasd_control_release import inspect_repo
        return inspect_repo(repo)
    except ImportError:
        return {"control_release_id": None, "protocol_epoch": 2, "head": None, "origin_main": None, "branch": None, "control_paths": [], "dirty_control_paths": [], "publishable": False, "observed_at": None}

def write_new(path: Path, value: Mapping[str, Any]) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(); path.parent.mkdir(parents=True, exist_ok=True)
    try: fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        if path.read_bytes() == payload: return
        raise EnvelopeError("existing envelope content conflicts") from exc
    with os.fdopen(fd, "wb") as stream: stream.write(payload); stream.flush(); os.fsync(stream.fileno())

def make(kind: str, direction: str, sender: dict[str, str], recipient: dict[str, str], body: dict[str, Any], repo: Path, reply: str | None) -> dict[str, Any]:
    return {"schema_version": 2, "protocol_epoch": 2, "message_id": str(uuid.uuid4()), "direction_id": direction, "sender": sender, "recipient": recipient, "kind": kind, "reply_to": reply, "body_sha256": body_sha(body), "control_release": release(repo), "git_facts": git_facts(repo), "body": body}

def next_role(env: Mapping[str, Any]) -> str:
    if env["kind"] in {"ASSIGNMENT", "PORTFOLIO_RETURN", "CONTROL_NOTICE"}: return "NONE"
    status = env["body"]["status"]
    mapping = {"REQUEST_EM": "EM", "REQUEST_CM": "CM", "REQUEST_PORTFOLIO": "Portfolio", "REQUEST_USER": "Root"}
    if status in mapping: return mapping[status]
    if status == "WAIT_RESOURCE": return role(env["sender"]["identity"])
    responsible = env["body"]["failure"]["responsible_role"]
    return responsible if responsible in {"Root", "Workflow-Clerk", "Portfolio", "EM", "CM"} else "NONE"

def message(env: Mapping[str, Any], locator: str) -> str:
    return f"HMASD_SESSION_ENVELOPE_V2 kind={env['kind']} direction={env['direction_id']} from={env['sender']['identity']} to={env['recipient']['identity']} next={next_role(env)} id={env['message_id']} sha256={env['body_sha256']} locator={locator}"

def output(env: Mapping[str, Any], locator: str) -> dict[str, Any]: return {"locator": locator, "message": message(env, locator), "recipient_thread_id": env["recipient"]["thread_id"]}

def route(sender: str, recipient: str, direction: str) -> None:
    if sender == "Root" and recipient == "Workflow-Clerk": return
    if sender != "Workflow-Clerk": raise EnvelopeError("only Root or Workflow-Clerk may create an assignment")
    if recipient == "Root" or (recipient == "Portfolio" and direction == "portfolio"): return
    match = MANAGER.fullmatch(recipient)
    if not match or match.group(2) != direction: raise EnvelopeError("assignment recipient route is invalid")

def create_assignment(args: argparse.Namespace) -> dict[str, Any]:
    repo, direction = Path(args.repo).resolve(), args.direction_id
    if DIRECTION.fullmatch(direction) is None: raise EnvelopeError("direction_id is invalid")
    sender = endpoint({"identity": args.sender_identity, "thread_id": args.sender_thread_id}, direction, "sender"); recipient = endpoint({"identity": args.recipient_identity, "thread_id": args.recipient_thread_id}, direction, "recipient")
    route(sender["identity"], recipient["identity"], direction); body = assignment_body(load(Path(args.body), "assignment body"), repo); env = make("ASSIGNMENT", direction, sender, recipient, body, repo, None)
    relative = Path(".codex/runtime/session-envelopes") / direction / f"{env['message_id']}.assignment.json"; write_new(repo / relative, env); return output(env, relative.as_posix())

def raw(repo: Path, locator: str) -> tuple[Path, dict[str, Any]]:
    relative = Path(path_value(Path(locator).as_posix(), "envelope locator")); return relative, load(target(repo, relative.as_posix(), "envelope locator"), "session envelope")

def common(value: Mapping[str, Any], repo: Path, kind: str) -> dict[str, Any]:
    fields = {"schema_version", "protocol_epoch", "message_id", "direction_id", "sender", "recipient", "kind", "reply_to", "body_sha256", "control_release", "git_facts", "body"}
    if set(value) != fields or value.get("schema_version") != 2 or value.get("protocol_epoch") != 2 or value.get("kind") != kind: raise EnvelopeError("envelope header is invalid")
    try: uuid.UUID(str(value["message_id"]))
    except (ValueError, TypeError) as exc: raise EnvelopeError("message_id is invalid") from exc
    direction = value["direction_id"]
    if not isinstance(direction, str) or DIRECTION.fullmatch(direction) is None: raise EnvelopeError("direction_id is invalid")
    result = dict(value); result["sender"] = endpoint(value["sender"], direction, "sender"); result["recipient"] = endpoint(value["recipient"], direction, "recipient")
    if not isinstance(value["body"], Mapping) or value["body_sha256"] != body_sha(value["body"]): raise EnvelopeError("body_sha256 does not match body")
    if not isinstance(value["control_release"], Mapping) or not isinstance(value["git_facts"], Mapping): raise EnvelopeError("control_release and git_facts must be objects")
    result["body"] = dict(value["body"]); return result

def read_assignment(repo: Path, locator: str) -> tuple[Path, dict[str, Any]]:
    relative, value = raw(repo, locator); env = common(value, repo, "ASSIGNMENT"); env["body"] = assignment_body(env["body"], repo)
    if env["reply_to"] is not None: raise EnvelopeError("assignment reply_to must be null")
    return relative, env

def create_return(args: argparse.Namespace, portfolio: bool = False) -> dict[str, Any]:
    repo = Path(args.repo).resolve(); assignment_path, assignment = read_assignment(repo, args.assignment)
    if portfolio:
        if assignment["recipient"]["identity"] != "Portfolio" or assignment["direction_id"] != "portfolio": raise EnvelopeError("portfolio-return requires global Portfolio assignment")
        kind, suffix, body = "PORTFOLIO_RETURN", ".portfolio-return.json", portfolio_body(load(Path(args.body), "portfolio return body"), repo)
    else:
        if assignment["recipient"]["identity"] == "Portfolio": raise EnvelopeError("global Portfolio assignment requires portfolio-return")
        kind, suffix, body = "RETURN", ".return.json", return_body(load(Path(args.body), "return body"), repo, assignment["body"]["owned_paths"])
    base = assignment_path.name.removesuffix(".assignment.json")
    if base == assignment_path.name: raise EnvelopeError("assignment locator must end with .assignment.json")
    relative = assignment_path.with_name(base + suffix)
    if (repo / relative).exists():
        existing = read_envelope(argparse.Namespace(repo=str(repo), envelope=relative.as_posix()))["envelope"]
        if existing["body"] != body: raise EnvelopeError("existing envelope content conflicts")
        return output(existing, relative.as_posix())
    env = make(kind, assignment["direction_id"], assignment["recipient"], assignment["sender"], body, repo, assignment["message_id"]); write_new(repo / relative, env); return output(env, relative.as_posix())

def create_notice(args: argparse.Namespace) -> dict[str, Any]:
    repo, direction = Path(args.repo).resolve(), args.direction_id
    if DIRECTION.fullmatch(direction) is None: raise EnvelopeError("direction_id is invalid")
    sender = endpoint({"identity": args.sender_identity, "thread_id": args.sender_thread_id}, direction, "sender"); recipient = endpoint({"identity": args.recipient_identity, "thread_id": args.recipient_thread_id}, direction, "recipient"); body = notice_body(load(Path(args.body), "control notice body"))
    if body["target_identity"] != recipient["identity"]: raise EnvelopeError("control notice target_identity must match recipient")
    env = make("CONTROL_NOTICE", direction, sender, recipient, body, repo, None); relative = Path(".codex/runtime/session-envelopes") / direction / f"{env['message_id']}.control-notice.json"; write_new(repo / relative, env); return output(env, relative.as_posix())

def read_envelope(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve(); relative, value = raw(repo, args.envelope); kind = value.get("kind")
    if kind not in KINDS: raise EnvelopeError("session envelope kind is invalid")
    env = common(value, repo, kind)
    if kind == "ASSIGNMENT": env["body"] = assignment_body(env["body"], repo)
    elif kind in {"RETURN", "PORTFOLIO_RETURN"}:
        suffix = ".return.json" if kind == "RETURN" else ".portfolio-return.json"
        if not relative.name.endswith(suffix): raise EnvelopeError("return locator suffix is invalid")
        paired = relative.with_name(relative.name.removesuffix(suffix) + ".assignment.json"); _, assignment = read_assignment(repo, paired.as_posix())
        if env["reply_to"] != assignment["message_id"] or env["sender"] != assignment["recipient"] or env["recipient"] != assignment["sender"] or env["direction_id"] != assignment["direction_id"]: raise EnvelopeError("return correlation or endpoints are invalid")
        env["body"] = return_body(env["body"], repo, assignment["body"]["owned_paths"]) if kind == "RETURN" else portfolio_body(env["body"], repo)
    else: env["body"] = notice_body(env["body"])
    locator = relative.as_posix(); return {"envelope": env, **output(env, locator)}

def read_message(args: argparse.Namespace) -> dict[str, Any]:
    match = LINE.fullmatch(args.message)
    if not match: raise EnvelopeError("message must be exactly one HMASD_SESSION_ENVELOPE_V2 locator line")
    result = read_envelope(argparse.Namespace(repo=args.repo, envelope=match.group("locator")))
    if result["message"] != args.message: raise EnvelopeError("message metadata does not match envelope")
    return result

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(); commands = p.add_subparsers(dest="command", required=True)
    for name in ("assignment", "control-notice"):
        c = commands.add_parser(name)
        for flag in ("repo", "direction-id", "sender-identity", "sender-thread-id", "recipient-identity", "recipient-thread-id", "body"): c.add_argument(f"--{flag}", required=True)
    for name in ("return", "portfolio-return"):
        c = commands.add_parser(name); c.add_argument("--repo", required=True); c.add_argument("--assignment", required=True); c.add_argument("--body", required=True)
    c = commands.add_parser("read"); c.add_argument("--repo", required=True); c.add_argument("--envelope", required=True)
    c = commands.add_parser("read-message"); c.add_argument("--repo", required=True); c.add_argument("--message", required=True)
    return p

def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "assignment": result = create_assignment(args)
        elif args.command == "return": result = create_return(args)
        elif args.command == "portfolio-return": result = create_return(args, True)
        elif args.command == "control-notice": result = create_notice(args)
        elif args.command == "read": result = read_envelope(args)
        else: result = read_message(args)
    except EnvelopeError as exc: print(str(exc), file=sys.stderr); return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
