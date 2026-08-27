from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_session_envelope.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, check=False,
        capture_output=True, text=True,
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def install_registry(repo: Path, *directions: tuple[str, str]) -> None:
    write_json(
        repo / "docs/research/portfolio/workflow/registry.json",
        {
            "schema_version": 1, "revision": 1,
            "updated_at": "2026-08-27T00:00:00Z", "writer": "Portfolio",
            "workflow_version": "hmasd-autonomous-v1",
            "goal": {"path": "docs/research/portfolio/PORTFOLIO.md", "sha256": "0" * 64},
            "directions": [
                {"id": direction_id, "lifecycle": lifecycle, "reactivation_condition_ref": None}
                for direction_id, lifecycle in directions
            ],
        },
    )


def create_assignment(
    repo: Path, direction_id: str, recipient_identity: str,
    recipient_thread_id: str, *, context_refs: list[str] | None = None,
) -> dict[str, str]:
    body_path = repo / f"{direction_id}-{recipient_thread_id}-assignment-body.json"
    write_json(
        body_path,
        {
            "objective": f"advance {direction_id}", "context_refs": context_refs or [],
            "owned_paths": ([f"docs/research/candidates/{direction_id}/"]
                            if direction_id != "portfolio" else ["docs/research/portfolio/"]),
            "constraints": ["bounded direction work"],
            "done_when": ["send one correlated RETURN"],
        },
    )
    result = run_cli(
        "assignment", "--repo", str(repo), "--direction-id", direction_id,
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk-thread",
        "--recipient-identity", recipient_identity,
        "--recipient-thread-id", recipient_thread_id, "--body", str(body_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def create_return(repo: Path, assignment: dict[str, str], *, status: str) -> dict[str, str]:
    body_path = repo / f"{Path(assignment['locator']).stem}-return-body.json"
    write_json(
        body_path,
        {
            "status": status, "summary": "bounded owner result",
            "changed_paths": [], "artifact_refs": [],
            "next_objective": "continue the exact routed slice",
            "failure": ({"scope": "feature", "summary": "bounded repair required"}
                        if status == "FAILED" else None),
        },
    )
    result = run_cli(
        "return", "--repo", str(repo), "--assignment", assignment["locator"],
        "--body", str(body_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def create_portfolio_return(
    repo: Path, assignment: dict[str, str], direction_id: str,
) -> dict[str, str]:
    body_path = repo / "portfolio-return-body.json"
    write_json(
        body_path,
        {
            "summary": "portfolio selected the next owner",
            "changed_paths": [], "artifact_refs": [],
            "actions": [{
                "direction_id": direction_id, "lifecycle": "ACTIVE",
                "status": "REQUEST_EM", "summary": "continue science",
                "artifact_refs": [], "next_objective": "continue science", "failure": None,
            }],
            "failure": None,
        },
    )
    result = run_cli(
        "portfolio-return", "--repo", str(repo), "--assignment", assignment["locator"],
        "--body", str(body_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def task(thread_id: str, name: str, status: str) -> dict[str, object]:
    return {"id": thread_id, "name": name, "status": {"type": status}}


def delivered(*messages: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"locator": item["locator"], "recipient_thread_id": item["recipient_thread_id"]}
        for item in messages
    ]


def liveness(
    repo: Path, tasks: list[dict[str, object]], delivered_messages: list[dict[str, str]],
    *, user_pauses: list[dict[str, str]] | None = None,
    resource_heartbeats: list[dict[str, str]] | None = None,
    experiments: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    observations_path = repo / "observations.json"
    write_json(
        observations_path,
        {
            "threads": tasks, "delivered": delivered_messages,
            "user_pauses": user_pauses or [],
            "resource_heartbeats": resource_heartbeats or [],
            "experiments": experiments or [],
        },
    )
    result = run_cli(
        "liveness", "--repo", str(repo), "--observations", str(observations_path),
        "--observed-at", "2026-08-27T14:30:00Z",
    )
    assert result.returncode == 0, result.stderr
    output_path = repo / ".codex/runtime/clerk-liveness.json"
    stdout = json.loads(result.stdout)
    assert stdout == json.loads(output_path.read_text(encoding="utf-8"))
    return stdout


def test_generated_but_unsent_return_is_not_a_delivery_receipt(tmp_path: Path) -> None:
    install_registry(tmp_path, ("alpha", "ACTIVE"))
    assignment = create_assignment(tmp_path, "alpha", "CM/alpha/g1", "cm-alpha")
    create_return(tmp_path, assignment, status="REQUEST_EM")
    result = liveness(
        tmp_path, [task("cm-alpha", "CM/alpha/g1", "active")], delivered(assignment)
    )
    assert result["directions"][0]["stage"] == "CM"
    assert result["directions"][0]["reason"] == "OWNED_WORK"
    assert result["actions"] == []


def test_all_delivered_returns_are_exposed_once(tmp_path: Path) -> None:
    install_registry(tmp_path, ("alpha", "ACTIVE"), ("beta", "ACTIVE"))
    alpha = create_assignment(tmp_path, "alpha", "CM/alpha/g1", "cm-alpha")
    beta = create_assignment(tmp_path, "beta", "CM/beta/g1", "cm-beta")
    alpha_return = create_return(tmp_path, alpha, status="REQUEST_EM")
    beta_return = create_return(tmp_path, beta, status="FAILED")
    result = liveness(
        tmp_path,
        [task("cm-alpha", "CM/alpha/g1", "idle"), task("cm-beta", "CM/beta/g1", "idle"),
         task("clerk-thread", "Workflow-Clerk", "active")],
        delivered(alpha, beta, alpha_return, beta_return),
    )
    assert {row["stage"] for row in result["directions"]} == {"TRANSPORT_GAP"}
    assert [action["locator"] for action in result["actions"]] == [
        alpha_return["locator"], beta_return["locator"]
    ]
    assert {action["kind"] for action in result["actions"]} == {"HANDLE_RETURN"}


def test_owner_identity_and_stopped_owner_recovery_are_exact(tmp_path: Path) -> None:
    install_registry(tmp_path, ("alpha", "ACTIVE"), ("beta", "ACTIVE"))
    alpha = create_assignment(tmp_path, "alpha", "CM/alpha/g1", "cm-alpha")
    beta = create_assignment(tmp_path, "beta", "EM/beta/g1", "em-beta")
    result = liveness(
        tmp_path,
        [task("cm-alpha", "CM/alpha/g1", "active"), task("em-beta", "EM/beta/g1", "idle")],
        delivered(alpha, beta),
    )
    rows = {row["direction_id"]: row for row in result["directions"]}
    assert rows["alpha"]["stage"] == "CM"
    assert rows["beta"]["reason"] == "OWNER_STOPPED_WITHOUT_RETURN"
    assert result["actions"] == [{
        "kind": "REDELIVER_ASSIGNMENT", "locator": beta["locator"],
        "message": beta["message"], "recipient_thread_id": "em-beta",
    }]


def test_duplicate_task_id_fails_closed(tmp_path: Path) -> None:
    install_registry(tmp_path, ("alpha", "ACTIVE"))
    assignment = create_assignment(tmp_path, "alpha", "CM/alpha/g1", "cm-alpha")
    observations = tmp_path / "observations.json"
    write_json(
        observations,
        {"threads": [task("cm-alpha", "CM/wrong/g1", "active"), task("cm-alpha", "CM/alpha/g1", "active")],
         "delivered": delivered(assignment), "user_pauses": [], "resource_heartbeats": [], "experiments": []},
    )
    result = run_cli(
        "liveness", "--repo", str(tmp_path), "--observations", str(observations),
        "--observed-at", "2026-08-27T14:30:00Z",
    )
    assert result.returncode == 2
    assert "duplicate" in result.stderr


def test_portfolio_transport_is_correlated_without_mtime(tmp_path: Path) -> None:
    install_registry(tmp_path, ("alpha", "ACTIVE"))
    cm = create_assignment(tmp_path, "alpha", "CM/alpha/g1", "cm-alpha")
    cm_return = create_return(tmp_path, cm, status="REQUEST_PORTFOLIO")
    portfolio = create_assignment(
        tmp_path, "portfolio", "Portfolio", "portfolio-thread",
        context_refs=[cm_return["locator"]],
    )
    result = liveness(
        tmp_path,
        [task("cm-alpha", "CM/alpha/g1", "idle"), task("portfolio-thread", "Portfolio", "active"),
         task("clerk-thread", "Workflow-Clerk", "active")],
        delivered(cm, cm_return, portfolio),
    )
    assert result["directions"][0]["stage"] == "PORTFOLIO"
    assert result["actions"] == []

    portfolio_return = create_portfolio_return(tmp_path, portfolio, "alpha")
    result = liveness(
        tmp_path,
        [task("cm-alpha", "CM/alpha/g1", "idle"), task("portfolio-thread", "Portfolio", "idle"),
         task("clerk-thread", "Workflow-Clerk", "active")],
        delivered(cm, cm_return, portfolio, portfolio_return),
    )
    assert result["directions"][0]["stage"] == "TRANSPORT_GAP"
    assert result["actions"] == [{
        "kind": "HANDLE_RETURN", "locator": portfolio_return["locator"],
        "message": portfolio_return["message"],
    }]


def test_pause_resource_and_experiment_require_correlated_observations(tmp_path: Path) -> None:
    install_registry(
        tmp_path, ("paused", "PARKED"), ("waiting", "ACTIVE"),
        ("running", "ACTIVE"), ("closed", "CLOSED"),
    )
    waiting = create_assignment(tmp_path, "waiting", "CM/waiting/g1", "cm-waiting")
    running = create_assignment(tmp_path, "running", "CM/running/g1", "cm-running")
    pause = create_assignment(tmp_path, "paused", "Root", "root-thread")
    write_json(
        tmp_path / "temp/directions/running/exp/run-1/manifest.json",
        {"direction_id": "running", "run_id": "run-1", "status": "RUNNING"},
    )
    result = liveness(
        tmp_path,
        [task("cm-waiting", "CM/waiting/g1", "idle"), task("cm-running", "CM/running/g1", "active"),
         task("root-thread", "Root", "idle")],
        delivered(waiting, running, pause),
        user_pauses=[{"direction_id": "paused", "assignment_locator": pause["locator"]}],
        resource_heartbeats=[{"direction_id": "waiting", "assignment_locator": waiting["locator"],
                              "owner_thread_id": "cm-waiting", "automation_id": "heartbeat-1", "status": "ACTIVE"}],
        experiments=[{"direction_id": "running", "assignment_locator": running["locator"],
                      "owner_thread_id": "cm-running", "manifest_locator": "temp/directions/running/exp/run-1/manifest.json"}],
    )
    rows = {row["direction_id"]: row for row in result["directions"]}
    assert rows["paused"]["stage"] == "USER_PAUSE"
    assert rows["waiting"]["stage"] == "WAITING_RESOURCE"
    assert rows["running"]["stage"] == "EXP"
    assert rows["closed"]["stage"] == "TERMINAL"


def test_output_is_fixed_inside_repo(tmp_path: Path) -> None:
    install_registry(tmp_path, ("closed", "CLOSED"))
    observations = tmp_path / "observations.json"
    write_json(observations, {"threads": [], "delivered": [], "user_pauses": [], "resource_heartbeats": [], "experiments": []})
    outside = tmp_path.parent / "outside.json"
    result = run_cli(
        "liveness", "--repo", str(tmp_path), "--observations", str(observations),
        "--observed-at", "2026-08-27T14:30:00Z", "--output", str(outside),
    )
    assert result.returncode == 2
    assert not outside.exists()
