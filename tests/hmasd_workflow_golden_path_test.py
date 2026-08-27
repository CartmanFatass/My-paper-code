"""Lower-layer workflow conformance with a fake App Server transport.

This module proves ``LOCAL_FAKE_TRANSPORT_GOLDEN`` only. It deliberately does
not exercise canonical Workflow-Clerk provenance and does not claim that a real
Codex desktop task was created, resumed, or observed. It is neither zero-Clerk
nor full-workflow acceptance.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from scripts import hmasd_codex_tasks as native
from scripts import hmasd_work_packet as packets


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "hmasd_run.py"
LOCAL_FAKE_TRANSPORT_GOLDEN = "LOCAL_FAKE_TRANSPORT_GOLDEN"


def _canonical_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(packets.hmasd_state.canonical_bytes(value))


def _file_ref(repo: Path, relative: str) -> dict[str, str]:
    path = repo / relative
    return {
        "path": relative,
        "sha256": packets.hmasd_state.sha256_bytes(path.read_bytes()),
    }


def _run(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _native_worktree(tmp_path: Path) -> tuple[Path, str]:
    seed = tmp_path / "seed"
    worktree = tmp_path / "alpha-worktree"
    _run(["git", "init", "-b", "main", str(seed)], cwd=tmp_path)
    _run(["git", "config", "user.email", "golden@example.invalid"], cwd=seed)
    _run(["git", "config", "user.name", "HMASD Golden"], cwd=seed)
    (seed / "README.md").write_text("golden fixture\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=seed)
    _run(["git", "commit", "-m", "golden fixture"], cwd=seed)
    _run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "omp/alpha/operator-golden",
            str(worktree),
            "HEAD",
        ],
        cwd=seed,
    )
    sha = _run(["git", "rev-parse", "HEAD"], cwd=worktree).stdout.strip()
    return worktree, sha


def _prepare_run(repo: Path, code_sha: str) -> Path:
    output = repo / "temp" / "directions" / "alpha" / "exp" / "golden-run"
    prepared = _run(
        [
            sys.executable,
            str(RUN_SCRIPT),
            "prepare",
            "--direction",
            "alpha",
            "--run-id",
            "golden-run",
            "--assignment",
            "cm-owned-operator-golden",
            "--code-sha",
            code_sha,
            "--parameters",
            json.dumps(
                {
                    "seed": 7,
                    "expected_stdout_marker": "HMASD_LOCAL_GOLDEN_OPERATOR_OK",
                }
            ),
            "--estimate",
            json.dumps(
                {
                    "wall_seconds": 1,
                    "peak_memory_gib": 0.01,
                    "basis": "local fake transport golden",
                    "workers": 1,
                    "threads_per_worker": 1,
                }
            ),
            "--output-root",
            str(output),
            "--",
            sys.executable,
            "-c",
            "print('HMASD_LOCAL_GOLDEN_OPERATOR_OK')",
        ],
        cwd=repo,
    )
    assert prepared.returncode == 0
    manifest = output / "manifest.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["status"] == "PREPARED"
    return manifest


def _packet_source(
    repo: Path,
    *,
    direction: str,
    sender: str,
    target: str,
    objective: str,
    owned_paths: list[str],
    effect_refs: list[dict[str, Any]] | None = None,
    authority_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    state_path = f"docs/research/candidates/{direction}/STATE.json"
    if not (repo / state_path).is_file():
        _canonical_write(repo / state_path, {"direction": direction, "revision": 1})
    return {
        "schema_version": 1,
        "scope_ref": {"path": state_path, "revision": 1},
        "sender_identity": sender,
        "target_identity": target,
        "authority_refs": authority_refs or [],
        "objective": objective,
        "non_goals": ["do not infer coordination from natural-language messages"],
        "owned_paths": owned_paths,
        "done_criteria": ["publish one immutable typed return witness"],
        "effect_refs": effect_refs or [],
    }


def _task(identity: str, thread_id: str, *, direction: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "logical_identity": identity,
        "generation": 1,
        "lifecycle": "ACTIVE",
        "thread_id": thread_id,
    }
    if identity.startswith("EM-"):
        row["kind"] = "em"
    elif identity.startswith("CM-"):
        row["kind"] = "cm"
    if direction is not None:
        row["direction_id"] = direction
    return row


def _locator(work_id: str) -> str:
    return f".codex/runtime/work/ready/{work_id}/packet.json"


class _LocalFakeAppServer:
    """In-memory JSONL peer; protocol/client production code remains real."""

    def __init__(self, cwd: Path) -> None:
        identities = {
            "thread-em-alpha": "EM-alpha",
            "thread-cm-alpha": "CM-alpha",
            "thread-em-beta": "EM-beta",
            "thread-root": "Root",
        }
        self.cwd = str(cwd)
        self.threads: dict[str, dict[str, Any]] = {
            thread_id: {
                "id": thread_id,
                "name": name,
                "status": {"type": "active"},
                "cwd": self.cwd,
                "turns": [],
            }
            for thread_id, name in identities.items()
        }
        self.requests: list[dict[str, Any]] = []
        self.pending: list[bytes] = []
        self.closed = False
        self._turn_counter = 0

    def _emit(self, request_id: int, result: dict[str, Any]) -> None:
        self.pending.append(
            (json.dumps({"id": request_id, "result": result}) + "\n").encode("utf-8")
        )

    def write_line(self, data: bytes) -> None:
        request = json.loads(data)
        self.requests.append(request)
        request_id = request.get("id")
        if request_id is None:
            return
        method = request.get("method")
        params = request.get("params", {})
        if method == "initialize":
            self._emit(request_id, {"serverInfo": {"name": "local-fake", "version": "1"}})
            return
        if method == "thread/list":
            rows = [
                {
                    "id": thread["id"],
                    "sessionId": thread["id"],
                    "name": thread["name"],
                    "status": thread["status"],
                    "cwd": thread["cwd"],
                    "source": "appServer",
                    "modelProvider": "fake",
                    "ephemeral": False,
                }
                for thread in self.threads.values()
            ]
            self._emit(request_id, {"data": rows, "nextCursor": None})
            return
        thread_id = params.get("threadId")
        if thread_id not in self.threads:
            raise AssertionError(f"unexpected fake thread: {thread_id!r}")
        thread = self.threads[thread_id]
        if method == "thread/read":
            self._emit(request_id, {"thread": thread})
        elif method == "thread/resume":
            self._emit(
                request_id,
                {
                    "thread": thread,
                    "cwd": self.cwd,
                    "approvalPolicy": "never",
                    "sandbox": {"type": "dangerFullAccess"},
                },
            )
        elif method == "turn/start":
            self._turn_counter += 1
            turn_id = f"fake-turn-{self._turn_counter}"
            thread["turns"].append(
                {
                    "id": turn_id,
                    "status": "inProgress",
                    "items": [
                        {
                            "type": "userMessage",
                            "id": f"fake-user-{self._turn_counter}",
                            "content": params["input"],
                        }
                    ],
                }
            )
            self._emit(
                request_id,
                {"turn": {"id": turn_id, "status": "inProgress", "items": []}},
            )
        else:
            raise AssertionError(f"unexpected fake App Server method: {method!r}")

    def read_line(self, timeout: float) -> bytes | None:
        del timeout
        if not self.pending:
            raise TimeoutError("local fake App Server has no queued response")
        return self.pending.pop(0)

    def close(self) -> None:
        self.closed = True

    def semantic_turns(self, thread_id: str, work_id: str) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for turn in self.threads[thread_id]["turns"]:
            for item in turn["items"]:
                for content in item["content"]:
                    if content.get("type") != "text":
                        continue
                    try:
                        document = json.loads(content["text"])
                    except (KeyError, TypeError, json.JSONDecodeError):
                        continue
                    if document.get("work_id") == work_id:
                        matches.append(turn)
        return matches


def _em_result(
    packet: dict[str, Any],
    *,
    conclusion_ref: dict[str, str],
    request_ref: dict[str, str],
    next_work_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": "EM-alpha",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Fresh scientific authority requests one bounded CM slice.",
        "changed_paths": [conclusion_ref["path"], request_ref["path"]],
        "state_refs": [conclusion_ref],
        "artifact_refs": [request_ref],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {
            "kind": "REQUEST_CM_ENGINEERING",
            "input_refs": [next_work_id],
        },
        "payload": {
            "kind": "em",
            "direction_id": "alpha",
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [conclusion_ref],
            "engineering_request_ref": request_ref,
        },
    }


def _cm_result(
    packet: dict[str, Any],
    *,
    manifest_ref: dict[str, str],
    scope_ref: dict[str, str],
    code_sha: str,
    next_work_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "hmasd-cm",
        "logical_identity": "CM-alpha",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "CM-owned Operator slice succeeded and is quiescent.",
        "changed_paths": [manifest_ref["path"]],
        "state_refs": [manifest_ref],
        "artifact_refs": [manifest_ref],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {
            "kind": "REQUEST_ROOT_ACTION",
            "input_refs": [next_work_id],
        },
        "payload": {
            "kind": "cm",
            "direction_id": "alpha",
            "scope_ref": scope_ref,
            "base_sha": code_sha,
            "candidate_sha": None,
            "verification_refs": [manifest_ref],
            "integrated_sha": None,
        },
    }


def _root_result(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "root",
        "logical_identity": "Root",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "NONE",
        "summary": "Root observed the terminal local result.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {"kind": "root", "wake_reason": "completion"},
    }


def test_em_cm_operator_root_local_fake_transport_golden(tmp_path: Path) -> None:
    repo, code_sha = _native_worktree(tmp_path)
    direction = repo / "docs" / "research" / "candidates" / "alpha"
    _canonical_write(direction / "STATE.json", {"direction": "alpha", "revision": 1})
    _canonical_write(direction / "DIRECTION.json", {"direction": "alpha", "revision": 1})

    em_packet = packets.build_packet(
        _packet_source(
            repo,
            direction="alpha",
            sender="Portfolio",
            target="EM-alpha",
            objective="Produce one fresh authority and exact engineering request.",
            owned_paths=["docs/research/candidates/alpha"],
            authority_refs=[
                {
                    "path": "docs/research/candidates/alpha/DIRECTION.json",
                    "revision": 1,
                }
            ],
        ),
        repo=repo,
    )
    packets.publish_packet(em_packet, repo=repo)
    em_task = _task("EM-alpha", "thread-em-alpha", direction="alpha")
    em_plan = packets.reconcile_once(
        repo=repo, work_id=em_packet["work_id"], observed_tasks=[em_task]
    )["plan"]
    assert em_plan["verb"] == "DISPATCH_EXISTING"

    peer = _LocalFakeAppServer(repo)
    with native.AppServerClient(transport=peer, timeout=0.2) as client:
        em_first = client.execute_plan(
            em_plan,
            packet_locator=_locator(em_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[em_task],
        )
        em_duplicate = client.execute_plan(
            em_plan,
            packet_locator=_locator(em_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[em_task],
        )
        assert em_first["status"] == "DELIVERED"
        assert em_duplicate["status"] == "ALREADY_DELIVERED"
        assert len(peer.semantic_turns("thread-em-alpha", em_packet["work_id"])) == 1

        manifest = _prepare_run(repo, code_sha)
        run_effect = {
            "kind": "run_manifest",
            "operation": "EXECUTE",
            "path": "temp/directions/alpha/exp/golden-run/manifest.json",
            "resource_id": "alpha/golden-run",
        }
        _canonical_write(
            direction / "em" / "CONCLUSION.json",
            {"decision_owner": "EM-alpha", "result": "invest engineering"},
        )
        _canonical_write(
            direction / "em" / "ENGINEERING_REQUEST.json",
            {"owner": "CM-alpha", "run_id": "golden-run"},
        )
        conclusion_ref = _file_ref(
            repo, "docs/research/candidates/alpha/em/CONCLUSION.json"
        )
        request_ref = _file_ref(
            repo, "docs/research/candidates/alpha/em/ENGINEERING_REQUEST.json"
        )
        cm_packet = packets.build_packet(
            _packet_source(
                repo,
                direction="alpha",
                sender="EM-alpha",
                target="CM-alpha",
                objective="Own one Operator slice through terminal manifest observation.",
                owned_paths=[
                    "experiments/candidates/alpha/golden",
                    "temp/directions/alpha/exp/golden-run",
                ],
                authority_refs=[conclusion_ref, request_ref],
                effect_refs=[run_effect],
            ),
            repo=repo,
        )
        em_result = _em_result(
            em_packet,
            conclusion_ref=conclusion_ref,
            request_ref=request_ref,
            next_work_id=cm_packet["work_id"],
        )
        published_em_return = packets.publish_return(
            repo=repo,
            work_id=em_packet["work_id"],
            observed_tasks=[em_task],
            agent_result=em_result,
            next_packet_draft=cm_packet,
        )
        assert published_em_return["plan"]["verb"] == "PUBLISH_PACKET_INTENT"

        # The natural-language completion message is intentionally lost. The
        # immutable witness alone reconstructs the exact publish intent and
        # never starts another semantic native turn.
        request_count = len(peer.requests)
        reconstructed = packets.reconcile_once(
            repo=repo, work_id=em_packet["work_id"], observed_tasks=[]
        )["plan"]
        assert reconstructed["verb"] == "PUBLISH_PACKET_INTENT"
        assert reconstructed["task_resolution"]["status"] == "RETURN_WITNESS"
        assert client.execute_plan(reconstructed)["status"] == "NO_EFFECT"
        assert len(peer.requests) == request_count
        assert len(peer.semantic_turns("thread-em-alpha", em_packet["work_id"])) == 1

        packets.publish_packet(reconstructed["packet"], repo=repo)
        beta_packet = packets.build_packet(
            _packet_source(
                repo,
                direction="beta",
                sender="Portfolio",
                target="EM-beta",
                objective="Run a resource-disjoint beta slice.",
                owned_paths=["experiments/candidates/beta/golden"],
            ),
            repo=repo,
        )
        packets.publish_packet(beta_packet, repo=repo)
        comparison = packets.compare_work_ids(
            repo, [cm_packet["work_id"], beta_packet["work_id"]]
        )
        assert comparison["outcome"] == "DISJOINT"

        cm_task = _task("CM-alpha", "thread-cm-alpha", direction="alpha")
        cm_plan = packets.reconcile_once(
            repo=repo, work_id=cm_packet["work_id"], observed_tasks=[cm_task]
        )["plan"]
        cm_first = client.execute_plan(
            cm_plan,
            packet_locator=_locator(cm_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[cm_task],
            peer_work_ids=[beta_packet["work_id"]],
        )
        cm_duplicate = client.execute_plan(
            cm_plan,
            packet_locator=_locator(cm_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[cm_task],
            peer_work_ids=[beta_packet["work_id"]],
        )
        assert cm_first["status"] == "DELIVERED"
        assert cm_duplicate["status"] == "ALREADY_DELIVERED"
        assert len(peer.semantic_turns("thread-cm-alpha", cm_packet["work_id"])) == 1

        beta_task = _task("EM-beta", "thread-em-beta", direction="beta")
        beta_plan = packets.reconcile_once(
            repo=repo, work_id=beta_packet["work_id"], observed_tasks=[beta_task]
        )["plan"]
        beta_delivery = client.execute_plan(
            beta_plan,
            packet_locator=_locator(beta_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[beta_task],
            peer_work_ids=[cm_packet["work_id"]],
        )
        assert beta_delivery["status"] == "DELIVERED"

        executed = _run(
            [sys.executable, str(RUN_SCRIPT), "execute", "--manifest", str(manifest)],
            cwd=repo,
        )
        assert executed.returncode == 0
        manifest_document = json.loads(manifest.read_text(encoding="utf-8"))
        assert manifest_document["status"] == "SUCCEEDED"
        assert manifest_document["process"]["exit_code"] == 0
        assert manifest_document["process"]["group_quiescent"] is True
        assert "HMASD_LOCAL_GOLDEN_OPERATOR_OK" in (
            manifest.parent / "stdout.log"
        ).read_text(encoding="utf-8")

        manifest_ref = _file_ref(
            repo, "temp/directions/alpha/exp/golden-run/manifest.json"
        )
        root_packet = packets.build_packet(
            _packet_source(
                repo,
                direction="alpha",
                sender="CM-alpha",
                target="Root",
                objective="Observe the exact terminal CM and run evidence.",
                owned_paths=["temp/directions/alpha/test/root-golden"],
                authority_refs=[manifest_ref],
                effect_refs=[{**run_effect, "operation": "OBSERVE"}],
            ),
            repo=repo,
        )
        cm_result = _cm_result(
            cm_packet,
            manifest_ref=manifest_ref,
            scope_ref=request_ref,
            code_sha=code_sha,
            next_work_id=root_packet["work_id"],
        )
        published_cm_return = packets.publish_return(
            repo=repo,
            work_id=cm_packet["work_id"],
            observed_tasks=[cm_task],
            agent_result=cm_result,
            next_packet_draft=root_packet,
        )
        assert published_cm_return["plan"]["verb"] == "PUBLISH_PACKET_INTENT"
        packets.publish_packet(published_cm_return["plan"]["packet"], repo=repo)

        root_task = _task("Root", "thread-root")
        root_plan = packets.reconcile_once(
            repo=repo, work_id=root_packet["work_id"], observed_tasks=[root_task]
        )["plan"]
        root_delivery = client.execute_plan(
            root_plan,
            packet_locator=_locator(root_packet["work_id"]),
            cwd=str(repo),
            observed_tasks=[root_task],
        )
        assert root_delivery["status"] == "DELIVERED"
        packets.publish_return(
            repo=repo,
            work_id=root_packet["work_id"],
            observed_tasks=[root_task],
            agent_result=_root_result(root_packet),
        )
        terminal = packets.reconcile_once(
            repo=repo, work_id=root_packet["work_id"], observed_tasks=[]
        )["plan"]
        assert terminal["verb"] == "NOOP_TERMINAL"
        assert terminal["task_resolution"]["status"] == "RETURN_WITNESS"

        # A typed UNKNOWN run Effect is locally scoped to observation. It does
        # not become a global stop signal and was never part of the explicit
        # alpha/beta resource comparison above.
        unknown_path = repo / "temp/directions/gamma/exp/unknown-run/manifest.json"
        unknown_document = dict(manifest_document)
        unknown_document.update(
            {
                "direction_id": "gamma",
                "run_id": "unknown-run",
                "assignment_id": "gamma-unknown",
                "writer": "Operator-unknown-run",
                "operator_identity": "Operator-unknown-run",
                "status": "UNKNOWN",
            }
        )
        _canonical_write(unknown_path, unknown_document)
        unknown_packet = packets.build_packet(
            _packet_source(
                repo,
                direction="gamma",
                sender="Portfolio",
                target="EM-gamma",
                objective="Observe one exact uncertain gamma run without replay.",
                owned_paths=["experiments/candidates/gamma/golden"],
                effect_refs=[
                    {
                        "kind": "run_manifest",
                        "operation": "OBSERVE",
                        "path": "temp/directions/gamma/exp/unknown-run/manifest.json",
                        "resource_id": "gamma/unknown-run",
                    }
                ],
            ),
            repo=repo,
        )
        packets.publish_packet(unknown_packet, repo=repo)
        unknown_plan = packets.reconcile_once(
            repo=repo, work_id=unknown_packet["work_id"], observed_tasks=[]
        )["plan"]
        assert unknown_plan["verb"] == "OBSERVE_EFFECT_ONLY"
        assert client.execute_plan(unknown_plan)["status"] == "NO_EFFECT"

    assert peer.closed
    transport_and_paths = json.dumps(
        {
            "requests": peer.requests,
            "identities": [thread["name"] for thread in peer.threads.values()],
            "runtime_paths": [
                path.relative_to(repo).as_posix()
                for path in (repo / ".codex/runtime/work").rglob("*")
            ],
        },
        sort_keys=True,
    ).lower()
    assert "workflow-clerk" not in transport_and_paths
    assert "clerk" not in transport_and_paths
    runtime_names = {
        path.name.lower() for path in (repo / ".codex/runtime/work").rglob("*")
    }
    assert not runtime_names & {
        "queue.json",
        "ledger.json",
        "lease.json",
        "cursor.json",
        "status.json",
        "authority.json",
    }
    assert LOCAL_FAKE_TRANSPORT_GOLDEN == "LOCAL_FAKE_TRANSPORT_GOLDEN"


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    [
        ("valid", None),
        ("valid_list_nonexact_parent_exact", None),
        ("wrong_identity", "OPERATOR_RESULT_IDENTITY_MISMATCH"),
        ("wrong_role", "OPERATOR_RESULT_IDENTITY_MISMATCH"),
        ("malformed_payload", "OPERATOR_RESULT_SCHEMA_INVALID"),
        ("child_nonterminal", "OPERATOR_CHILD_NOT_TERMINAL"),
        ("wrong_manifest_ref", "OPERATOR_MANIFEST_REF_MISMATCH"),
        ("wrong_manifest_owner", "TYPED_CONFLICT"),
        ("wrong_manifest_run", "TYPED_CONFLICT"),
        ("wrong_manifest_command", "TYPED_CONFLICT"),
        ("manifest_nonterminal", "OPERATOR_MANIFEST_TERMINAL_MISMATCH"),
        ("manifest_nonzero", "OPERATOR_MANIFEST_TERMINAL_MISMATCH"),
        ("manifest_nonquiescent", "OPERATOR_MANIFEST_TERMINAL_MISMATCH"),
        ("stdout_marker_wrong", "OPERATOR_STDOUT_MARKER_MISMATCH"),
        ("cm_early_return", "OPERATOR_CHILD_NOT_TERMINAL"),
        ("cm_refs_empty", "CM_OPERATOR_REFS_MISMATCH"),
        ("cm_refs_wrong_fresh", "CM_OPERATOR_REFS_MISMATCH"),
        ("candidate_read_unknown", "OPERATOR_CHILD_READ_UNKNOWN"),
        ("candidate_binding_unknown", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("candidate_ambiguous", "MULTIPLE_OPERATOR_CHILDREN_FOR_RUN"),
        ("candidate_split_ambiguous", "MULTIPLE_OPERATOR_CHILDREN_FOR_RUN"),
        ("parent_activity_malformed", "OPERATOR_PARENT_ACTIVITY_INVALID"),
        ("parent_turn_nonmapping", "OPERATOR_PARENT_ACTIVITY_INVALID"),
        ("parent_turn_items_missing", "OPERATOR_PARENT_ACTIVITY_INVALID"),
        ("parent_turn_items_nonlist", "OPERATOR_PARENT_ACTIVITY_INVALID"),
        ("composite_instruction_missing", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("composite_instruction_multiple", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("composite_prefix_malformed", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("composite_prefix_protocol_wrong", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("composite_suffix_malformed", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN"),
        ("natural_language_only", "OPERATOR_RESULT_MISSING"),
        ("typed_result_ambiguous", "OPERATOR_RESULT_AMBIGUOUS"),
    ],
)
def test_run_chain_reuses_one_operator_after_cm_interrupt_and_returns_terminal_refs(
    tmp_path: Path, case: str, expected_reason: str | None
) -> None:
    repo, code_sha = _native_worktree(tmp_path)
    direction = repo / "docs" / "research" / "candidates" / "alpha"
    _canonical_write(direction / "STATE.json", {"direction": "alpha", "revision": 1})
    _canonical_write(direction / "DIRECTION.json", {"direction": "alpha", "revision": 1})
    _canonical_write(
        direction / "em" / "ENGINEERING_REQUEST.json",
        {"owner": "CM-alpha", "run_id": "golden-run"},
    )
    request_ref = _file_ref(
        repo, "docs/research/candidates/alpha/em/ENGINEERING_REQUEST.json"
    )
    manifest = _prepare_run(repo, code_sha)
    manifest_locator = "temp/directions/alpha/exp/golden-run/manifest.json"
    run_effect = {
        "kind": "run_manifest",
        "operation": "EXECUTE",
        "path": manifest_locator,
        "resource_id": "alpha/golden-run",
    }
    cm_packet = packets.build_packet(
        _packet_source(
            repo,
            direction="alpha",
            sender="EM-alpha",
            target="CM-alpha",
            objective="Run the one frozen golden command and return its terminal refs.",
            owned_paths=[
                "experiments/candidates/alpha/golden",
                "temp/directions/alpha/exp/golden-run",
            ],
            authority_refs=[request_ref],
            effect_refs=[run_effect],
        ),
        repo=repo,
    )
    packets.publish_packet(cm_packet, repo=repo)
    cm_task = _task("CM-alpha", "thread-cm-alpha", direction="alpha")
    projection = repo / ".codex" / "runtime" / "tasks.json"
    projection.parent.mkdir(parents=True, exist_ok=True)
    _canonical_write(projection, {"tasks": [{**cm_task, "lifecycle": "PARKED"}]})

    marker = "HMASD_LOCAL_GOLDEN_OPERATOR_OK"
    cm_return_count = 0
    operator_create_count = 0
    execute_count = 0
    cm_turn_inputs: list[list[dict[str, Any]]] = []
    participant_instruction = (
        "Complete only the exact Work Packet slice above. First reuse any existing exact "
        "return; otherwise read the packet, complete its bounded assignment, publish its "
        "typed result, and return that immutable witness."
    )

    def composite_input(document: dict[str, Any], *, variant: str = "valid") -> str:
        prefix = native.dispatch_envelope_bytes(
            cm_packet["work_id"], _locator(cm_packet["work_id"]), "CM-alpha"
        ).decode()
        suffix = json.dumps(document, separators=(",", ":"), sort_keys=True)
        if variant == "composite_instruction_missing":
            return prefix + suffix
        if variant == "composite_instruction_multiple":
            return prefix + participant_instruction * 2 + suffix
        if variant == "composite_prefix_malformed":
            return "not-json\n" + participant_instruction + suffix
        if variant == "composite_prefix_protocol_wrong":
            wrong = json.loads(prefix)
            wrong["protocol"] = "wrong.protocol"
            return json.dumps(wrong) + "\n" + participant_instruction + suffix
        if variant == "composite_suffix_malformed":
            return prefix + participant_instruction + "not-json"
        return prefix + participant_instruction + suffix

    def child_stub(thread_id: str, run_id: str, *, bound: bool = True) -> dict[str, Any]:
        document = {
            "protocol": "hmasd.experiment-operator.assignment.v1",
            "agent_role": "hmasd-experiment-operator",
            "logical_identity": "hmasd-experiment-operator",
            "run_id": run_id,
        }
        return {
            "id": thread_id,
            "name": (
                "native_ll_golden_run_68428496c0"
                if run_id == "golden_run"
                else "native_ll_golden_run_493d823df1"
            ),
            "parentThreadId": "thread-cm-alpha",
            "agentRole": "hmasd-experiment-operator",
            "cwd": str(repo),
            "status": {"type": "idle"},
            "turns": [
                {
                    "id": f"turn-{thread_id}",
                    "status": "completed",
                    "items": [
                        {
                            "type": "userMessage",
                            "content": [
                                {
                                    "type": "text",
                                    "text": composite_input(
                                        document if bound else {"run_id": run_id}
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    class InterruptedCmPeer:
        def __init__(self) -> None:
            collision = child_stub(
                "thread-operator-collision",
                "golden_run",
                bound=case != "candidate_binding_unknown",
            )
            self.collision_id = str(collision["id"])
            self.threads: dict[str, dict[str, Any]] = {
                "thread-cm-alpha": {
                    "id": "thread-cm-alpha",
                    "name": "CM-alpha",
                    "cwd": str(repo),
                    "threadSource": "hmasd-manager:CM-alpha:g1",
                    "status": {"type": "idle"},
                    "turns": [],
                },
                collision["id"]: collision,
            }
            if case in {"candidate_ambiguous", "candidate_split_ambiguous"}:
                for suffix in ("a", "b"):
                    child = child_stub(f"thread-operator-exact-{suffix}", "golden-run")
                    self.threads[child["id"]] = child
            discovered = []
            if case in {"candidate_read_unknown", "candidate_binding_unknown"}:
                discovered = [self.collision_id]
            elif case == "candidate_ambiguous":
                discovered = ["thread-operator-exact-a", "thread-operator-exact-b"]
            elif case == "candidate_split_ambiguous":
                discovered = ["thread-operator-exact-b"]
            if discovered or case == "parent_activity_malformed":
                activities = [
                    {
                        "type": "subAgentActivity",
                        "kind": "started",
                        "agentThreadId": child_id,
                        "agentPath": f"/root/{child_id}",
                    }
                    for child_id in discovered
                ]
                if case == "parent_activity_malformed":
                    activities.append(
                        {
                            "type": "subAgentActivity",
                            "kind": "started",
                            "agentPath": "/root/native_ll_missing_child_id",
                        }
                    )
                self.threads["thread-cm-alpha"]["turns"].append(
                    {"id": "turn-parent-activity", "status": "interrupted", "items": activities}
                )
            if case == "parent_turn_nonmapping":
                self.threads["thread-cm-alpha"]["turns"].append("malformed-turn")
            elif case == "parent_turn_items_missing":
                self.threads["thread-cm-alpha"]["turns"].append(
                    {"id": "turn-items-missing", "status": "interrupted"}
                )
            elif case == "parent_turn_items_nonlist":
                self.threads["thread-cm-alpha"]["turns"].append(
                    {"id": "turn-items-nonlist", "status": "interrupted", "items": {}}
                )
            self.transport = _LocalFakeAppServer(repo)
            self.transport.threads = self.threads
            self.transport.requests = []

        def write_line(self, data: bytes) -> None:
            nonlocal cm_return_count, operator_create_count, execute_count
            request = json.loads(data)
            self.transport.requests.append(request)
            request_id = request.get("id")
            if request_id is None:
                return
            method = request.get("method")
            params = request.get("params", {})
            if method == "initialize":
                self.transport._emit(
                    request_id,
                    {"serverInfo": {"name": "local-fake", "version": "1"}},
                )
                return
            if method == "thread/list":
                listed = [
                    thread
                    for thread in self.threads.values()
                    if thread.get("parentThreadId") is None
                ]
                if case == "valid_list_nonexact_parent_exact":
                    listed.append(self.threads[self.collision_id])
                elif case == "candidate_split_ambiguous":
                    listed.append(self.threads["thread-operator-exact-a"])
                self.transport._emit(
                    request_id,
                    {"data": listed, "nextCursor": None},
                )
                return
            thread_id = params.get("threadId")
            if method == "thread/read":
                if case == "candidate_read_unknown" and thread_id == self.collision_id:
                    self.transport.pending.append(
                        (json.dumps({"id": request_id, "error": {"code": -32001}}) + "\n").encode()
                    )
                    return
                self.transport._emit(request_id, {"thread": self.threads[thread_id]})
                return
            if method == "thread/resume":
                self.transport._emit(request_id, {"thread": self.threads[thread_id]})
                return
            if method != "turn/start":
                raise AssertionError(f"unexpected fake App Server method: {method!r}")
            assert thread_id == "thread-cm-alpha"
            cm_turn_inputs.append(params["input"])
            attempt = len(self.threads[thread_id]["turns"]) + 1
            turn = {
                "id": f"turn-cm-{attempt}",
                "status": "interrupted" if attempt == 1 else "completed",
                "items": [{"type": "userMessage", "content": params["input"]}],
            }
            self.threads[thread_id]["turns"].append(turn)
            if attempt == 1:
                operator_create_count += 1
                spawn_assignment = next(
                    json.loads(item["text"])
                    for item in params["input"]
                    if item.get("type") == "text"
                    and '"protocol":"hmasd.experiment-operator.assignment.v1"'
                    in item.get("text", "")
                )
                operator_thread = {
                    "id": "thread-operator-golden-run",
                    "name": spawn_assignment["task_name"],
                    "parentThreadId": "thread-cm-alpha",
                    "agentRole": "hmasd-experiment-operator",
                    "cwd": str(repo),
                    "status": {"type": "idle"},
                    "turns": [
                        {
                            "id": "turn-operator-inherited",
                            "status": "interrupted",
                            "items": [
                                {
                                    "type": "userMessage",
                                    "content": [
                                            {
                                                "type": "text",
                                                "text": composite_input(
                                                    spawn_assignment, variant=case
                                                ),
                                            }
                                        ],
                                    }
                            ],
                        },
                        {
                            "id": "turn-operator-golden-run",
                            "status": "completed",
                            "items": [],
                        },
                    ],
                }
                self.threads[operator_thread["id"]] = operator_thread
                turn["items"].append(
                    {
                        "type": "subAgentActivity",
                        "kind": "started",
                        "agentThreadId": operator_thread["id"],
                        "agentPath": f"/root/{spawn_assignment['task_name']}",
                    }
                )
                # Native history may persist the same start activity more than
                # once; identity is the exact child thread ID, so duplicates
                # are harmless.
                turn["items"].append(dict(turn["items"][-1]))
                execute_count += 1
                completed = _run(
                    [sys.executable, str(RUN_SCRIPT), "execute", "--manifest", str(manifest)],
                    cwd=repo,
                )
                assert completed.returncode == 0
                manifest_document = json.loads(manifest.read_text(encoding="utf-8"))
                if case == "wrong_manifest_owner":
                    manifest_document["writer"] = "Operator-other"
                elif case == "wrong_manifest_run":
                    manifest_document["run_id"] = "other-run"
                elif case == "wrong_manifest_command":
                    manifest_document["command"] = [sys.executable, "-c", "print('other')"]
                elif case == "manifest_nonterminal":
                    manifest_document["status"] = "RUNNING"
                elif case == "manifest_nonzero":
                    manifest_document["process"]["exit_code"] = 1
                elif case == "manifest_nonquiescent":
                    manifest_document["process"]["group_quiescent"] = False
                if case.startswith("wrong_manifest") or case.startswith("manifest_"):
                    _canonical_write(manifest, manifest_document)
                if case == "stdout_marker_wrong":
                    (manifest.parent / "stdout.log").write_text("WRONG_MARKER\n", encoding="utf-8")
                manifest_ref = _file_ref(repo, manifest_locator)
                stdout_ref = _file_ref(
                    repo, "temp/directions/alpha/exp/golden-run/stdout.log"
                )
                stderr_ref = _file_ref(
                    repo, "temp/directions/alpha/exp/golden-run/stderr.log"
                )
                operator_result = {
                    "schema_version": 1,
                    "role": (
                        "hmasd-verifier" if case == "wrong_role" else "hmasd-experiment-operator"
                    ),
                    "logical_identity": (
                        "hmasd-verifier"
                        if case == "wrong_identity"
                        else "hmasd-experiment-operator"
                    ),
                    "generation": 1,
                    "assignment_id": "cm-owned-operator-golden",
                    "status": "COMPLETED",
                    "materiality": "LOCAL",
                    "summary": "The exact frozen run reached terminal success.",
                    "changed_paths": [manifest_ref["path"]],
                    "state_refs": [manifest_ref],
                    "artifact_refs": [stdout_ref, stderr_ref],
                    "checkpoint_sha": None,
                    "decision_requests": [],
                    "next_action": {"kind": "NONE", "input_refs": []},
                    "payload": {
                        "kind": "run",
                        "run_id": "golden-run",
                        "manifest_ref": manifest_ref,
                        "terminal_status": "SUCCEEDED",
                        "exit_code": 0,
                    },
                }
                if case == "wrong_manifest_ref":
                    operator_result["payload"]["manifest_ref"] = stdout_ref
                elif case == "malformed_payload":
                    operator_result["payload"] = "bad"
                if case in {"child_nonterminal", "cm_early_return"}:
                    operator_thread["turns"][-1]["status"] = "inProgress"
                elif case == "natural_language_only":
                    operator_thread["turns"][-1]["items"].append(
                        {
                            "type": "agentMessage",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Run succeeded; manifest and logs are available.",
                                }
                            ],
                        }
                    )
                else:
                    operator_thread["turns"][-1]["items"].append(
                        {
                            "type": "agentMessage",
                            "content": [
                                {"type": "output_text", "text": json.dumps(operator_result)}
                            ],
                        }
                    )
                    if case == "typed_result_ambiguous":
                        second_result = {**operator_result, "summary": "A second typed result."}
                        operator_thread["turns"][-1]["items"].append(
                            {
                                "type": "agentMessage",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": json.dumps(second_result),
                                    }
                                ],
                            }
                        )
            if attempt != 1 or case == "cm_early_return":
                manifest_ref = _file_ref(repo, manifest_locator)
                stdout_ref = _file_ref(
                    repo, "temp/directions/alpha/exp/golden-run/stdout.log"
                )
                stderr_ref = _file_ref(
                    repo, "temp/directions/alpha/exp/golden-run/stderr.log"
                )
                cm_result = {
                    "schema_version": 1,
                    "role": "hmasd-cm",
                    "logical_identity": "CM-alpha",
                    "generation": 1,
                    "assignment_id": cm_packet["work_id"],
                    "status": "COMPLETED",
                    "materiality": "DIRECTION",
                    "summary": "The frozen Operator run reached one terminal result.",
                    "changed_paths": [manifest_ref["path"]],
                    "state_refs": [manifest_ref],
                    "artifact_refs": [stdout_ref, stderr_ref],
                    "checkpoint_sha": None,
                    "decision_requests": [],
                    "next_action": {"kind": "NONE", "input_refs": []},
                    "payload": {
                        "kind": "cm",
                        "direction_id": "alpha",
                        "scope_ref": request_ref,
                        "base_sha": code_sha,
                        "candidate_sha": None,
                        "verification_refs": [manifest_ref, stdout_ref, stderr_ref],
                        "integrated_sha": None,
                    },
                }
                if case == "cm_refs_empty":
                    cm_result["state_refs"] = []
                    cm_result["artifact_refs"] = []
                    cm_result["payload"]["verification_refs"] = []
                elif case == "cm_refs_wrong_fresh":
                    cm_result["state_refs"] = [request_ref]
                    cm_result["artifact_refs"] = [request_ref]
                    cm_result["payload"]["verification_refs"] = [request_ref]
                packets.publish_return(
                    repo=repo,
                    work_id=cm_packet["work_id"],
                    observed_tasks=[cm_task],
                    agent_result=cm_result,
                )
                cm_return_count += 1
            self.transport._emit(
                request_id,
                {"turn": {"id": turn["id"], "status": "inProgress", "items": []}},
            )
            self.transport.pending.append(
                (
                    json.dumps(
                        {
                            "method": "turn/completed",
                            "params": {"threadId": thread_id, "turn": turn},
                        }
                    )
                    + "\n"
                ).encode("utf-8")
            )

        def read_line(self, timeout: float) -> bytes | None:
            return self.transport.read_line(timeout)

        def close(self) -> None:
            self.transport.close()

    peer = InterruptedCmPeer()
    with native.AppServerClient(transport=peer, timeout=0.2) as client:
        first = client.run_chain(start_work_id=cm_packet["work_id"], cwd=str(repo))
        repeated = client.run_chain(start_work_id=cm_packet["work_id"], cwd=str(repo))
    if expected_reason is not None:
        stops = [first["stop"], repeated["stop"]]
        assert expected_reason in json.dumps(stops, sort_keys=True)
        assert all(stop["reason"] != "TERMINAL_NO_NEXT" for stop in stops)
        assert operator_create_count <= 1
        assert execute_count <= 1
        assert cm_return_count <= 1
        if case in {"natural_language_only", "typed_result_ambiguous"}:
            assert operator_create_count == execute_count == cm_return_count == 1
            assert len(peer.threads["thread-cm-alpha"]["turns"]) == 2
        return
    assert first["stop"]["reason"] == "TERMINAL_NO_NEXT", first
    assert "RETURN_WITNESS_PRESENT" in json.dumps(first["events"], sort_keys=True)
    assert first["stop"]["return_witness"]["agent_result"]["artifact_refs"] == [
        _file_ref(repo, "temp/directions/alpha/exp/golden-run/stdout.log"),
        _file_ref(repo, "temp/directions/alpha/exp/golden-run/stderr.log"),
    ]
    assert repeated["stop"]["reason"] == "TERMINAL_NO_NEXT"
    operator_contracts = [
        json.loads(item["text"])
        for turn_inputs in cm_turn_inputs
        for item in turn_inputs
        if item.get("type") == "text"
        and '"protocol":"hmasd.experiment-operator.assignment.v1"'
        in item.get("text", "")
    ]
    contract_base = {
        "agent_role": "hmasd-experiment-operator",
        "assignment_id": "cm-owned-operator-golden",
        "command": [sys.executable, "-c", f"print('{marker}')"],
        "cwd": str(repo),
        "expected_stdout_marker": marker,
        "execute_argv": [
            sys.executable,
            str(RUN_SCRIPT),
            "execute",
            "--manifest",
            str(manifest),
        ],
        "logical_identity": "hmasd-experiment-operator",
        "manifest": manifest_locator,
        "output_root": str(manifest.parent),
        "parent_identity": "CM-alpha",
        "protocol": "hmasd.experiment-operator.assignment.v1",
        "run_id": "golden-run",
        "run_owner": "Operator-golden-run",
        "result_contract": {
            "artifact_refs": [
                "temp/directions/alpha/exp/golden-run/stdout.log",
                "temp/directions/alpha/exp/golden-run/stderr.log",
            ],
            "assignment_id": "cm-owned-operator-golden",
            "logical_identity": "hmasd-experiment-operator",
            "role": "hmasd-experiment-operator",
            "run_id": "golden-run",
            "schema_path": "scripts/schemas/hmasd_agent_result.schema.json",
            "state_refs": [manifest_locator],
            "verification_refs": [
                manifest_locator,
                "temp/directions/alpha/exp/golden-run/stdout.log",
                "temp/directions/alpha/exp/golden-run/stderr.log",
            ],
            "work_id": cm_packet["work_id"],
        },
        "task_name": "native_ll_golden_run_493d823df1",
    }
    assert contract_base["task_name"] != "native_ll_golden_run_68428496c0"
    assert operator_contracts == [
        {**contract_base, "action": "CREATE_EXACT"},
        {
            **contract_base,
            "action": "RESUME_EXACT",
            "observed_child_thread_id": "thread-operator-golden-run",
        },
    ]
    manifest_document = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_document["status"] == "SUCCEEDED"
    assert manifest_document["process"]["exit_code"] == 0
    assert manifest_document["process"]["group_quiescent"] is True
    assert (manifest.parent / "stdout.log").read_text(encoding="utf-8").count(marker) == 1
    assert operator_create_count == 1
    assert execute_count == 1
    assert cm_return_count == 1
    assert len(peer.threads["thread-cm-alpha"]["turns"]) == 2
    assert [
        thread["id"]
        for thread in peer.threads.values()
        if thread.get("parentThreadId") == "thread-cm-alpha"
        and thread.get("agentRole") == "hmasd-experiment-operator"
        and any(
            '"run_id": "golden-run"' in item.get("text", "")
            for turn in thread.get("turns", [])
            for entry in turn.get("items", [])
            for item in entry.get("content", [])
        )
    ] == ["thread-operator-golden-run"]
