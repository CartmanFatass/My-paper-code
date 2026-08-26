"""Public-CLI acceptance for four bounded, independent ``run-chain`` calls.

This is deterministic fake-transport evidence.  Real Workflow-Clerk and native
Codex task provenance remain the Ticket 07 acceptance seam.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import textwrap
from typing import Any
from scripts import hmasd_work_packet as packets


ROOT = Path(__file__).resolve().parents[1]
TASKS_SCRIPT = ROOT / "scripts" / "hmasd_codex_tasks.py"
PRIORITY = ("uav_ready", "ground_transport", "duration_policy", "semantic_boundary")
FAKE_APP_SERVER = r'''
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
source_root = Path(sys.argv[1])
repo = Path(sys.argv[2])
barrier = Path(sys.argv[3])
barrier_parties = int(sys.argv[4])
sys.path.insert(0, str(source_root))
from scripts import hmasd_platform
from scripts import hmasd_work_packet as packets

state_path = repo / ".codex" / "runtime" / "four-direction-state.json"
lock_path = state_path.with_suffix(".lock")
def locked_state(update=None):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as stream, hmasd_platform.exclusive_file_lock(stream.fileno()):
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if update is not None:
            update(state)
            temporary = state_path.with_name(f"{state_path.name}.{os.getpid()}.tmp")
            temporary.write_text(
                json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            os.replace(temporary, state_path)
        return state
def thread_fact(thread_id):
    state = locked_state()
    return next(row for row in state["threads"] if row["id"] == thread_id)
def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()
for raw in sys.stdin:
    request = json.loads(raw)
    request_id = request.get("id")
    if request_id is None:
        continue
    method = request.get("method")
    params = request.get("params", {})
    if method == "initialize":
        emit({"id": request_id, "result": {"serverInfo": {"name": "four-direction-fake", "version": "1"}}})
        continue
    if method == "thread/list":
        emit({"id": request_id, "result": {"data": locked_state()["threads"], "nextCursor": None}})
        continue
    if method == "thread/read":
        emit({"id": request_id, "result": {"thread": thread_fact(params["threadId"])}})
        continue
    if method == "thread/resume":
        thread = thread_fact(params["threadId"])
        emit({"id": request_id, "result": {
            "thread": thread, "model": "fake", "modelProvider": "fake",
            "cwd": str(repo), "approvalPolicy": "never",
            "sandbox": {"type": "dangerFullAccess"},
        }})
        continue
    if method != "turn/start":
        raise AssertionError(f"unexpected method: {method}")

    thread = thread_fact(params["threadId"])
    envelope = json.loads(params["input"][0]["text"])
    work_id = envelope["work_id"]
    direction = thread["name"].removeprefix("EM-")
    turn_id = f"turn-{work_id[:12]}"
    emit({"id": request_id, "result": {"turn": {"id": turn_id, "status": "inProgress", "items": []}}})

    barrier.mkdir(parents=True, exist_ok=True)
    entered = time.monotonic_ns()
    (barrier / f"{work_id}.entered").write_text(str(entered), encoding="ascii")
    deadline = time.monotonic() + 15.0
    while len(list(barrier.glob("*.entered"))) < barrier_parties:
        if time.monotonic() >= deadline:
            raise TimeoutError("four-direction fake barrier timed out")
        time.sleep(0.01)
    released = time.monotonic_ns()

    task = {
        "logical_identity": f"EM-{direction}", "kind": "em",
        "direction_id": direction, "generation": 1, "lifecycle": "PARKED",
        "thread_id": thread["id"],
    }
    result = {
        "schema_version": 1, "role": "hmasd-em",
        "logical_identity": f"EM-{direction}", "generation": 1,
        "assignment_id": work_id, "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": f"Completed only the exact {direction} synthetic slice.",
        "changed_paths": [], "state_refs": [], "artifact_refs": [],
        "checkpoint_sha": None, "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "em", "direction_id": direction,
            "question_sha256": "a" * 64, "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [], "engineering_request_ref": None,
        },
    }
    packets.publish_return(repo=repo, work_id=work_id, observed_tasks=[task], agent_result=result)
    turn = {
        "id": turn_id, "status": "completed",
        "items": [{"type": "userMessage", "content": params["input"]}],
    }

    def record(state):
        current = next(row for row in state["threads"] if row["id"] == thread["id"])
        if not any(row.get("id") == turn_id for row in current["turns"]):
            current["turns"].append(turn)
            state["deliveries"][work_id] = state["deliveries"].get(work_id, 0) + 1
            state["timings"][work_id] = {"entered": entered, "released": released}

    locked_state(record)
    emit({"method": "turn/completed", "params": {"threadId": thread["id"], "turn": turn}})
'''


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest(repo: Path, direction: str) -> dict[str, Any]:
    run_id = f"{direction}-observe"
    command = [sys.executable, "-c", f"print('{direction}')"]
    document = json.loads(
        (ROOT / "tests/fixtures/hmasd_phase0/run_manifest.json").read_text(encoding="utf-8")
    )
    document.update(
        {
            "writer": f"Operator-{run_id}", "operator_identity": f"Operator-{run_id}",
            "run_id": run_id, "direction_id": direction,
            "assignment_id": f"synthetic-{direction}", "command": command,
            "command_sha256": hashlib.sha256(
                b"\0".join(part.encode("utf-8") for part in command)
            ).hexdigest(),
            "cwd": str(repo), "parameters": {"synthetic": True}, "code_sha": "1" * 40,
        }
    )
    return document


def _fixture(
    repo: Path, *, wave: str, overlap: bool
) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    documents: list[dict[str, Any]] = []
    effect_bytes: dict[str, bytes] = {}
    for index, direction in enumerate(PRIORITY, start=1):
        state_path = repo / "docs" / "research" / "candidates" / direction / "STATE.json"
        direction_path = state_path.with_name("DIRECTION.json")
        _write_json(state_path, {"direction": direction, "revision": 1})
        _write_json(direction_path, {"direction": direction, "revision": 1})
        effect_path = repo / "temp" / "directions" / direction / "exp" / "observe" / "manifest.json"
        _write_json(effect_path, _manifest(repo, direction))
        relative_effect = effect_path.relative_to(repo).as_posix()
        owned = (
            "experiments/candidates/pair_overlap"
            if overlap and direction in PRIORITY[:2]
            else f"docs/research/candidates/{direction}/em/{wave}"
        )
        packet = packets.build_packet(
            {
                "schema_version": 1,
                "scope_ref": {"path": state_path.relative_to(repo).as_posix(), "revision": 1},
                "sender_identity": "Workflow-Clerk",
                "target_identity": f"EM-{direction}",
                "authority_refs": [{"path": direction_path.relative_to(repo).as_posix(), "revision": 1}],
                "objective": f"Complete priority {index} synthetic {direction} {wave} slice.",
                "non_goals": ["do not coordinate another direction or invoke Root"],
                "owned_paths": [owned],
                "done_criteria": ["publish one immutable typed terminal return"],
                "effect_refs": [{
                    "kind": "run_manifest", "path": relative_effect,
                    "resource_id": f"{direction}/{direction}-observe",
                }],
            },
            repo=repo,
        )
        packets.publish_packet(packet, repo=repo)
        documents.append(packet)
        effect_bytes[relative_effect] = effect_path.read_bytes()
    return documents, effect_bytes


def _initialize_shared_state(repo: Path) -> Path:
    state_path = repo / ".codex" / "runtime" / "four-direction-state.json"
    _write_json(
        state_path,
        {
            "threads": [
                {
                    "id": f"thread-em-{direction}", "name": f"EM-{direction}",
                    "cwd": str(repo), "threadSource": f"hmasd-manager:EM-{direction}:g1",
                    "status": {"type": "idle"}, "turns": [],
                }
                for direction in PRIORITY
            ],
            "deliveries": {}, "timings": {},
            "operator_count": 0, "command_count": 0, "external_effect_count": 0,
        },
    )
    return state_path


def _server_command(fake: Path, repo: Path, barrier: Path, parties: int) -> str:
    return subprocess.list2cmdline(
        [sys.executable, str(fake), str(ROOT), str(repo), str(barrier), str(parties)]
    )


def _call(repo: Path, server: str, packet: dict[str, Any], peers: list[str]) -> dict[str, Any]:
    command = [
        sys.executable, str(TASKS_SCRIPT), "--timeout", "20",
        "--server-command", server, "run-chain", "--work-id", packet["work_id"],
        "--cwd", str(repo),
    ]
    for peer in peers:
        command.extend(["--peer-work-id", peer])
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _fan_out(repo: Path, server: str, documents: list[dict[str, Any]], peer_sets: list[list[str]]) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(_call, repo, server, packet, peers)
            for packet, peers in zip(documents, peer_sets, strict=True)
        ]
        return [future.result(timeout=35) for future in futures]


def test_four_public_run_chains_overlap_idempotently_and_isolate_one_conflicting_pair(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fake = tmp_path / "fake_app_server.py"
    fake.write_text(textwrap.dedent(FAKE_APP_SERVER), encoding="utf-8")
    state_path = _initialize_shared_state(repo)

    documents, original_effects = _fixture(repo, wave="disjoint", overlap=False)
    all_ids = [packet["work_id"] for packet in documents]
    peers = [[other for other in all_ids if other != work_id] for work_id in all_ids]
    server = _server_command(fake, repo, tmp_path / "barrier-disjoint", 4)
    first = _fan_out(repo, server, documents, peers)
    repeated = _fan_out(repo, server, documents, peers)

    assert [packet["target_identity"].removeprefix("EM-") for packet in documents] == list(PRIORITY)
    assert packets.compare_work_ids(repo, all_ids)["outcome"] == "DISJOINT"
    assert [result["stop"]["reason"] for result in first] == ["TERMINAL_NO_NEXT"] * 4
    assert [result["stop"]["reason"] for result in repeated] == ["TERMINAL_NO_NEXT"] * 4
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["deliveries"] == {work_id: 1 for work_id in all_ids}
    assert len(state["threads"]) == 4
    assert len({row["id"] for row in state["threads"]}) == 4
    assert len({row["threadSource"] for row in state["threads"]}) == 4
    assert all(len(row["turns"]) == 1 for row in state["threads"])
    entered = [fact["entered"] for fact in state["timings"].values()]
    released = [fact["released"] for fact in state["timings"].values()]
    assert len(entered) == 4 and max(entered) <= min(released)
    for packet, thread in zip(documents, state["threads"], strict=True):
        turn_input = thread["turns"][0]["items"][0]["content"]
        assert json.loads(turn_input[0]["text"])["work_id"] == packet["work_id"]
        assert all(other not in json.dumps(turn_input) for other in all_ids if other != packet["work_id"])
        assert "Root" not in json.dumps(turn_input)
    assert (state["operator_count"], state["command_count"], state["external_effect_count"]) == (0, 0, 0)
    assert {
        path: (repo / Path(*path.split("/"))).read_bytes() for path in original_effects
    } == original_effects

    list_result = _call_list(repo, server)
    assert [(row["name"], row["threadSource"]) for row in list_result["threads"]] == [
        (f"EM-{direction}", f"hmasd-manager:EM-{direction}:g1") for direction in PRIORITY
    ]
    assert all(_call_read(repo, server, row["id"])["thread"]["id"] == row["id"] for row in list_result["threads"])

    overlapping, _ = _fixture(repo, wave="overlap", overlap=True)
    overlap_ids = [packet["work_id"] for packet in overlapping]
    overlap_peers = [[overlap_ids[1]], [overlap_ids[0]], [overlap_ids[3]], [overlap_ids[2]]]
    overlap_server = _server_command(fake, repo, tmp_path / "barrier-overlap", 2)
    isolated = _fan_out(repo, overlap_server, overlapping, overlap_peers)
    assert [result["stop"]["reason"] for result in isolated] == [
        "EXECUTE_PLAN_STOP", "EXECUTE_PLAN_STOP", "TERMINAL_NO_NEXT", "TERMINAL_NO_NEXT"
    ]
    for result in isolated[:2]:
        assert result["stop"]["result"] == {
            "status": "WORK_OVERLAP_CONFLICT", "compare_outcome": "CONFLICT",
            "work_ids": sorted(overlap_ids[:2]),
        }
    final_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert all(work_id not in final_state["deliveries"] for work_id in overlap_ids[:2])
    assert all(final_state["deliveries"][work_id] == 1 for work_id in overlap_ids[2:])
    overlap_timings = [final_state["timings"][work_id] for work_id in overlap_ids[2:]]
    assert max(fact["entered"] for fact in overlap_timings) <= min(
        fact["released"] for fact in overlap_timings
    )
    assert "ROOT_OVERRIDE_ACTIVE" not in json.dumps([first, repeated, isolated])


def _call_list(repo: Path, server: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(TASKS_SCRIPT), "--server-command", server, "list", "--cwd", str(repo)],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _call_read(repo: Path, server: str, thread_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(TASKS_SCRIPT), "--server-command", server, "read", "--thread-id", thread_id],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)
