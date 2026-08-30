"""Phase 0 RED tests for HMASD durable state contracts.

These tests intentionally describe the contract before the implementation exists.
They are kept narrow so later phases can reuse the fixtures without importing
workflow behavior.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_phase0"
KINDS = (
    "portfolio_registry",
    "research_state",
    "engineering_state",
    "external_review_index",
    "run_manifest",
    "accepted_result",
    "agent_result",
    "runtime_agents",
    "runtime_worktrees",
)

SCHEMA_KINDS = (*KINDS, "runtime_browser_assignments")


def fixture(kind: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{kind}.json").read_text(encoding="utf-8"))



def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )




def test_all_phase0_schema_contracts_are_present_and_strict() -> None:
    schema_dir = ROOT / "scripts" / "schemas"
    for kind in SCHEMA_KINDS:
        schema = json.loads(
            (schema_dir / f"hmasd_{kind}.schema.json").read_text(encoding="utf-8")
        )
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]




def test_valid_phase0_fixtures_validate(tmp_path: Path) -> None:
    for kind in KINDS:
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(fixture(kind)), encoding="utf-8")
        result = run_cli("validate", "--kind", kind, "--path", str(path))
        assert result.returncode == 0, (kind, result.stderr)


def test_external_review_status_transitions_use_the_exact_pro_pair(
    tmp_path: Path,
) -> None:
    current = fixture("external_review_index")
    assert set(current["rounds"][0]["prompt_refs"]) == {
        "pro_innovator",
        "pro_convergence",
    }
    assert set(current["rounds"][0]["providers"]) == {
        "pro_innovator",
        "pro_convergence",
    }
    target = tmp_path / "external-review-index.json"
    source = tmp_path / "external-review-initial.json"
    source.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
    initialized = run_cli(
        "initialize",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        current["writer"],
        "--input",
        str(source),
    )
    assert initialized.returncode == 0, initialized.stderr

    for revision, status in enumerate(
        (
            "INNOVATOR_RUNNING",
            "LOCAL_RESEARCH",
            "SYNTHESIS_READY",
            "CONVERGENCE_RUNNING",
            "COMPLETE",
        ),
        start=2,
    ):
        replacement = copy.deepcopy(current)
        replacement["revision"] = revision
        replacement["rounds"][0]["status"] = status
        if status == "COMPLETE":
            replacement["rounds"][0]["completed_at"] = "2026-08-24T00:05:00Z"
        replacement_path = tmp_path / f"external-review-r{revision}.json"
        replacement_path.write_text(
            json.dumps(replacement, sort_keys=True),
            encoding="utf-8",
        )
        result = run_cli(
            "replace",
            "--kind",
            "external_review_index",
            "--path",
            str(target),
            "--writer",
            current["writer"],
            "--expected-revision",
            str(current["revision"]),
            "--input",
            str(replacement_path),
        )
        assert result.returncode == 0, (status, result.stdout, result.stderr)
        current = replacement


def test_external_review_rejects_old_three_stage_fields(tmp_path: Path) -> None:
    document = fixture("external_review_index")
    review_round = document["rounds"][0]
    innovator_prompt = review_round["prompt_refs"]["pro_innovator"]
    review_round["prompt_refs"] = {
        "gemini_divergent": innovator_prompt,
        "pro_divergent": innovator_prompt,
        "pro_convergence": None,
    }
    review_round["providers"] = {
        "gemini_divergent": None,
        "pro_divergent": None,
        "pro_convergence": None,
    }
    review_round["status"] = "DIVERGENT_PENDING"
    path = tmp_path / "external-review-v1-fields.json"
    path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")

    result = run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(path),
    )

    assert result.returncode == 2








def test_portfolio_payload_is_root_owned_after_manager_merge(tmp_path: Path) -> None:
    document = fixture("agent_result")
    document.update(
        {
            "assignment_id": "root-portfolio-wake",
            "logical_identity": "Root",
            "materiality": "PORTFOLIO",
            "payload": {
                "kind": "portfolio",
                "direction_actions": [],
                "capacity_action": {
                    "action": "NONE",
                    "direction_id": None,
                    "decision_ref": None,
                },
                "portfolio_ref": {
                    "path": "docs/research/portfolio/PORTFOLIO.md",
                    "sha256": "a" * 64,
                },
                "registry_revision": 1,
            },
            "role": "root",
            "summary": "Root reconciled portfolio lifecycle.",
        }
    )
    path = tmp_path / "root-portfolio.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    document["role"] = "hmasd-portfolio"
    document["logical_identity"] = "Portfolio"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


def test_common_result_requires_closed_next_actions_and_exact_dependencies(
    tmp_path: Path,
) -> None:
    document = fixture("agent_result")
    action = {
        "action_id": "persist-research-state",
        "kind": "RUN_CLERK_JOB",
        "owner": "CLERK",
        "input_refs": [
            {
                "path": "temp/clerk/persist-research-state/state-input.json",
                "sha256": "5" * 64,
            }
        ],
        "dependencies": [
            {
                "authority_ref": {
                    "path": "docs/research/candidates/example-direction/STATE.json",
                    "sha256": "6" * 64,
                },
                "revision_or_checkpoint": 1,
            }
        ],
        "authorized_effect_ref": {
            "path": "docs/research/candidates/example-direction/STATE.json",
            "sha256": "7" * 64,
        },
        "stop_or_reentry_ref": {
            "path": "temp/clerk/persist-research-state/stop.json",
            "sha256": "8" * 64,
        },
    }
    document["next_actions"] = [action]
    path = tmp_path / "agent-result-actions.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    bad_owner = copy.deepcopy(document)
    bad_owner["next_actions"][0]["owner"] = "PORTFOLIO"
    path.write_text(json.dumps(bad_owner), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    implicit_dependency = copy.deepcopy(document)
    implicit_dependency["next_actions"][0]["dependencies"] = [
        {"authority_ref": action["dependencies"][0]["authority_ref"]}
    ]
    path.write_text(json.dumps(implicit_dependency), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    legacy_alias = copy.deepcopy(document)
    legacy_alias["next_action"] = None
    path.write_text(json.dumps(legacy_alias), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    duplicate = copy.deepcopy(document)
    duplicate["next_actions"].append(copy.deepcopy(action))
    path.write_text(json.dumps(duplicate), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


def test_clerk_result_uses_stable_identity_and_sequential_job_id(
    tmp_path: Path,
) -> None:
    document = fixture("agent_result")
    document.update(
        {
            "assignment_id": "clerk-job-001",
            "logical_identity": "Clerk",
            "materiality": "LOCAL",
            "role": "hmasd-clerk",
            "summary": "Completed one bounded Clerk job.",
            "payload": {
                "kind": "clerk",
                "job_id": "clerk-job-001",
                "operation": "integrate-candidate",
                "outcome": "COMPLETED",
                "observations": [
                    {
                        "kind": "integration",
                        "integrated_sha": "a" * 40,
                        "push_attempts": 1,
                    }
                ],
            },
        }
    )
    path = tmp_path / "clerk-result.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    wrong_identity = copy.deepcopy(document)
    wrong_identity["logical_identity"] = "Clerk-clerk-job-001"
    path.write_text(json.dumps(wrong_identity), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    wrong_job = copy.deepcopy(document)
    wrong_job["payload"]["job_id"] = "clerk-job-002"
    path.write_text(json.dumps(wrong_job), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 5

    decision = copy.deepcopy(document)
    decision["materiality"] = "USER"
    decision["decision_requests"] = [
        {
            "kind": "USER_DECISION",
            "ref": {
                "path": "temp/clerk/decision.json",
                "sha256": "b" * 64,
            },
        }
    ]
    path.write_text(json.dumps(decision), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 5

    obsolete = copy.deepcopy(document)
    obsolete["payload"]["packet_ref"] = {
        "path": "temp/clerk/operation.json",
        "sha256": "c" * 64,
    }
    path.write_text(json.dumps(obsolete), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


def test_runtime_clerk_identity_is_stable_across_sequential_jobs(
    tmp_path: Path,
) -> None:
    current = fixture("runtime_agents")
    current["agents"].append(
        {
            "logical_identity": "Clerk",
            "agent_type": "hmasd-clerk",
            "generation": 1,
            "assignment_id": "clerk-job-001",
            "parent_identity": "Root",
            "session_ref": "session-clerk",
            "job_ref": "job-clerk-001",
            "runtime_ref": "runtime-clerk",
            "lifecycle": "IDLE",
            "last_seen_at": "2026-08-24T00:00:00Z",
        }
    )
    current_input = tmp_path / "runtime-current.json"
    current_input.write_text(json.dumps(current), encoding="utf-8")
    target = tmp_path / "runtime-agents.json"
    initialized = run_cli(
        "initialize",
        "--kind",
        "runtime_agents",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--input",
        str(current_input),
    )
    assert initialized.returncode == 0, initialized.stderr

    running = copy.deepcopy(current)
    running["revision"] = 2
    running["updated_at"] = "2026-08-24T00:00:01Z"
    running["agents"][-1]["assignment_id"] = "clerk-job-002"
    running["agents"][-1]["job_ref"] = "job-clerk-002"
    running["agents"][-1]["lifecycle"] = "RUNNING"
    running["agents"][-1]["last_seen_at"] = "2026-08-24T00:00:01Z"
    running_input = tmp_path / "runtime-running.json"
    running_input.write_text(json.dumps(running), encoding="utf-8")
    replaced = run_cli(
        "replace",
        "--kind",
        "runtime_agents",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "1",
        "--input",
        str(running_input),
    )
    assert replaced.returncode == 0, replaced.stderr

    parked = copy.deepcopy(running)
    parked["revision"] = 3
    parked["updated_at"] = "2026-08-24T00:00:02Z"
    parked["agents"][-1]["lifecycle"] = "PARKED"
    parked["agents"][-1]["last_seen_at"] = "2026-08-24T00:00:02Z"
    parked_input = tmp_path / "runtime-parked.json"
    parked_input.write_text(json.dumps(parked), encoding="utf-8")
    parked_result = run_cli(
        "replace",
        "--kind",
        "runtime_agents",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "2",
        "--input",
        str(parked_input),
    )
    assert parked_result.returncode == 0, parked_result.stderr
    assert json.loads(target.read_text(encoding="utf-8"))["agents"][-1][
        "logical_identity"
    ] == "Clerk"

    obsolete_identity = copy.deepcopy(parked)
    obsolete_identity["agents"][-1]["logical_identity"] = "Clerk-clerk-job-002"
    obsolete_path = tmp_path / "runtime-obsolete-identity.json"
    obsolete_path.write_text(json.dumps(obsolete_identity), encoding="utf-8")
    obsolete_result = run_cli(
        "validate",
        "--kind",
        "runtime_agents",
        "--path",
        str(obsolete_path),
    )
    assert obsolete_result.returncode == 2


def test_obsolete_clerk_operation_schema_is_unregistered(tmp_path: Path) -> None:
    path = tmp_path / "operation.json"
    path.write_text("{}\n", encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2
    assert not (ROOT / "scripts/schemas/hmasd_clerk_operation.schema.json").exists()


def test_unknown_version_extra_key_and_invalid_path_are_refused_without_rewrite(
    tmp_path: Path,
) -> None:
    source = fixture("research_state")
    path = tmp_path / "state.json"
    path.write_bytes(json.dumps(source, indent=2, sort_keys=True).encode() + b"\n")

    original = path.read_bytes()
    unknown = dict(source, schema_version=3)
    unknown_path = tmp_path / "unknown.json"
    unknown_path.write_bytes(json.dumps(unknown, indent=2, sort_keys=True).encode() + b"\n")
    result = run_cli("validate", "--kind", "research_state", "--path", str(unknown_path))
    assert result.returncode == 3
    assert unknown_path.read_bytes() == original.replace(b'"schema_version": 2', b'"schema_version": 3')

    extra_path = tmp_path / "extra.json"
    extra_path.write_bytes(
        json.dumps(dict(source, unexpected=True), indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(extra_path))
    assert result.returncode == 2
    assert extra_path.read_bytes().endswith(b"\n")

    invalid_path = dict(source)
    invalid_path["direction_ref"] = dict(source["direction_ref"], path="../outside.md")
    invalid_path_file = tmp_path / "invalid-path.json"
    invalid_path_file.write_bytes(
        json.dumps(invalid_path, indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(invalid_path_file))
    assert result.returncode == 2


def test_writer_and_path_ownership_are_enforced(tmp_path: Path) -> None:
    state = fixture("research_state")
    wrong_writer = tmp_path / "wrong-writer.json"
    wrong_writer.write_bytes(json.dumps(dict(state, writer="CM-example-direction")).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_writer))
    assert result.returncode == 5

    wrong_ref = tmp_path / "wrong-ref.json"
    bad = dict(state)
    bad["direction_ref"] = dict(state["direction_ref"], path="docs/research/candidates/other/DIRECTION.md")
    wrong_ref.write_bytes(json.dumps(bad).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_ref))
    assert result.returncode == 5


def test_replace_refuses_cross_writer_and_immutable_record_rewrites(tmp_path: Path) -> None:
    """A CAS replacement may advance facts, never reassign their durable record."""

    def assert_refused(
        label: str,
        kind: str,
        current: dict[str, Any],
        replacement: dict[str, Any],
        writer: str,
        expected_code: int,
    ) -> None:
        target = tmp_path / f"{label}.json"
        initial_path = tmp_path / f"{label}-initial.json"
        replacement_path = tmp_path / f"{label}-replacement.json"
        initial_path.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
        initialized = run_cli(
            "initialize",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            current["writer"],
            "--input",
            str(initial_path),
        )
        assert initialized.returncode == 0, initialized.stderr
        before = target.read_bytes()
        replacement_path.write_text(json.dumps(replacement, sort_keys=True), encoding="utf-8")
        result = run_cli(
            "replace",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            writer,
            "--expected-revision",
            "1",
            "--input",
            str(replacement_path),
        )
        assert result.returncode == expected_code, (label, result.stdout, result.stderr)
        assert target.read_bytes() == before

    direction_current = fixture("research_state")
    direction_replacement = copy.deepcopy(direction_current)
    direction_replacement.update(
        {
            "revision": 2,
            "writer": "EM-other-direction",
            "direction_id": "other-direction",
        }
    )
    direction_replacement["direction_ref"]["path"] = (
        "docs/research/candidates/other-direction/DIRECTION.md"
    )
    assert_refused(
        "direction-takeover",
        "research_state",
        direction_current,
        direction_replacement,
        "EM-other-direction",
        5,
    )

    run_current = fixture("run_manifest")
    run_replacement = copy.deepcopy(run_current)
    run_replacement.update(
        {
            "revision": 2,
            "run_id": "other-run",
            "command": ["python3", "evaluate.py", "--seed", "7"],
        }
    )
    run_replacement["command_sha256"] = hashlib.sha256(
        "\0".join(run_replacement["command"]).encode("utf-8")
    ).hexdigest()
    assert_refused(
        "run-command",
        "run_manifest",
        run_current,
        run_replacement,
        "Operator-example-run",
        6,
    )

    operator_replacement = copy.deepcopy(run_current)
    operator_replacement.update(
        {
            "revision": 2,
            "writer": "Operator-other-run",
            "operator_identity": "Operator-other-run",
        }
    )
    assert_refused(
        "operator-takeover",
        "run_manifest",
        run_current,
        operator_replacement,
        "Operator-other-run",
        5,
    )

    external_current = fixture("external_review_index")
    provider = {
        "provider": "chatgpt",
        "product_model": "GPT-5.6 Sol",
        "reasoning_effort": "Pro",
        "target_conversation_url": None,
        "target_conversation_id": None,
        "prompt_ref": {
            "path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/PRO_INNOVATOR_PROMPT.md",
            "sha256": "0" * 64,
        },
        "response_path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/chatgpt/response.md",
        "operation_id": "operation-a",
        "idempotency_key": "idempotency-a",
        "request_fingerprint": "3" * 64,
        "stable_key": "stable-a",
        "operation_ref": {
            "path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/chatgpt/operation_ref.json",
            "sha256": "1" * 64,
        },
        "created_at": 1788000000000,
        "updated_at": 1788000002000,
        "send_attempted": True,
        "send_attempted_at": 1788000001000,
        "observed_conversation_url": "https://chatgpt.com/c/conversation-a",
        "observed_conversation_id": "conversation-a",
        "provider_user_message_id": "user-message-a",
        "provider_assistant_message_id": "assistant-message-a",
        "archive": {
            "path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/chatgpt/response.md",
            "sha256": "2" * 64,
            "size_bytes": 5,
            "projection": "exact",
            "verified_at": 1788000000000,
        },
        "error": None,
    }
    external_current["rounds"][0]["providers"]["pro_innovator"] = provider
    external_replacement = copy.deepcopy(external_current)
    external_replacement["revision"] = 2
    external_replacement["rounds"][0]["providers"]["pro_innovator"]["operation_id"] = "operation-b"
    assert_refused(
        "external-operation",
        "external_review_index",
        external_current,
        external_replacement,
        "EM-example-direction",
        6,
    )

    external_round_replacement = copy.deepcopy(external_current)
    external_round_replacement["revision"] = 2
    external_round_replacement["rounds"][0]["question_sha256"] = "e" * 64
    external_round_replacement["rounds"][0]["round_id"] = hashlib.sha256(
        (
            external_round_replacement["direction_id"]
            + "\n"
            + external_round_replacement["rounds"][0]["question_sha256"]
            + "\n"
            + external_round_replacement["rounds"][0]["evidence_set_sha256"]
            + "\n"
            + external_round_replacement["workflow_version"]
        ).encode("utf-8")
    ).hexdigest()[:20]
    assert_refused(
        "external-round",
        "external_review_index",
        external_current,
        external_round_replacement,
        "EM-example-direction",
        6,
    )

    result_current = fixture("accepted_result")
    result_replacement = copy.deepcopy(result_current)
    result_replacement.update(
        {
            "revision": 2,
            "result_id": "other-result",
            "conclusion_path": "docs/research/candidates/example-direction/results/other-result.md",
        }
    )
    assert_refused(
        "result-identity",
        "accepted_result",
        result_current,
        result_replacement,
        "EM-example-direction",
        6,
    )

    terminal_current = copy.deepcopy(run_current)
    terminal_current["status"] = "SUCCEEDED"
    terminal_current["process"].update(
        {
            "execution_token": "token-a",
            "pid": 123,
            "process_group_id": 123,
            "linux_boot_id": "boot-a",
            "proc_start_ticks": 99,
            "started_at": "2026-08-24T00:00:00Z",
            "ended_at": "2026-08-24T00:01:00Z",
            "exit_code": 0,
            "terminal_reason": "CHILD_EXIT_0",
        }
    )
    terminal_replacement = copy.deepcopy(terminal_current)
    terminal_replacement["revision"] = 2
    terminal_replacement["process"]["terminal_reason"] = "REWRITTEN"
    assert_refused(
        "terminal-provenance",
        "run_manifest",
        terminal_current,
        terminal_replacement,
        "Operator-example-run",
        6,
    )

    worktree_current = fixture("runtime_worktrees")
    worktree_replacement = copy.deepcopy(worktree_current)
    worktree_replacement["revision"] = 2
    worktree_replacement["worktrees"][0]["canonical_absolute_path"] = "/tmp/other-worktree"
    assert_refused(
        "worktree-target",
        "runtime_worktrees",
        worktree_current,
        worktree_replacement,
        "Root",
        6,
    )

    worktree_ref_replacement = copy.deepcopy(worktree_current)
    worktree_ref_replacement["revision"] = 2
    worktree_ref_replacement["worktrees"][0]["worktree_ref"] = "wt-other"
    assert_refused(
        "worktree-ref",
        "runtime_worktrees",
        worktree_current,
        worktree_ref_replacement,
        "Root",
        6,
    )

    runtime_agents_current = fixture("runtime_agents")
    runtime_agents_replacement = copy.deepcopy(runtime_agents_current)
    runtime_agents_replacement["revision"] = 2
    runtime_agents_replacement["agents"][0]["runtime_ref"] = "runtime-other-em"
    assert_refused(
        "runtime-agent-ref",
        "runtime_agents",
        runtime_agents_current,
        runtime_agents_replacement,
        "Root",
        6,
    )


def test_registry_enforces_uniqueness_dependencies_and_active_limit(tmp_path: Path) -> None:
    registry = fixture("portfolio_registry")
    registry["directions"] = registry["directions"] * 9
    for index, direction in enumerate(registry["directions"]):
        direction["id"] = f"direction-{index}"
        direction["abbreviation"] = f"D{index}"
        direction["path"] = f"docs/research/candidates/direction-{index}"
        direction["lifecycle_decision_ref"]["heading"] = f"Direction direction-{index}"
        direction["agent"]["logical_identity"] = f"EM-direction-{index}"
        direction["agent"]["job_name"] = f"EMDirection{index}"
        direction["research_state_path"] = f"docs/research/candidates/direction-{index}/workflow/research/state.json"
        direction["engineering_state_path"] = f"docs/research/candidates/direction-{index}/workflow/engineering/state.json"
        direction["external_review_index_path"] = f"docs/research/candidates/direction-{index}/workflow/external-review/index.json"
        direction["lifecycle"] = "ACTIVE"
        direction["dependencies"] = []
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(path))
    assert result.returncode == 2

    cyclic = fixture("portfolio_registry")
    cyclic["directions"][0]["dependencies"] = ["example-direction"]
    cyclic["directions"].append(dict(cyclic["directions"][0], id="second-direction", dependencies=["example-direction"]))
    cyclic["directions"][0]["dependencies"] = ["second-direction"]
    cyclic_path = tmp_path / "cyclic.json"
    cyclic_path.write_text(json.dumps(cyclic), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(cyclic_path))
    assert result.returncode == 2




def test_initialize_and_replace_are_revision_cas_and_current_only(tmp_path: Path) -> None:
    source = fixture("research_state")
    target = tmp_path / "state.json"
    initialized = run_cli(
        "initialize",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        source["writer"],
        "--input",
        str(FIXTURES / "research_state.json"),
    )
    assert initialized.returncode == 0, initialized.stderr

    replacement = copy.deepcopy(source)
    replacement["revision"] += 1
    replacement["updated_at"] = "2026-08-24T00:01:00Z"
    replacement_path = tmp_path / "replacement.json"
    replacement_path.write_text(json.dumps(replacement), encoding="utf-8")
    replaced = run_cli(
        "replace",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        source["writer"],
        "--expected-revision",
        "1",
        "--input",
        str(replacement_path),
    )
    assert replaced.returncode == 0, replaced.stderr

    old_schema = copy.deepcopy(source)
    old_schema["schema_version"] = 1
    old_path = tmp_path / "old-schema.json"
    old_path.write_text(json.dumps(old_schema), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "research_state",
        "--path",
        str(old_path),
    ).returncode == 2

    no_migration = run_cli("--help")
    assert "migrate" not in no_migration.stdout


def test_replace_repairs_only_stale_current_research_direction_ref(
    tmp_path: Path, monkeypatch
) -> None:
    spec = importlib.util.spec_from_file_location("hmasd_state_live_ref", SCRIPT)
    assert spec is not None and spec.loader is not None
    state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state)

    isolated_root = tmp_path / "root"
    direction_ref = "docs/research/candidates/example-direction/DIRECTION.md"
    authority = isolated_root / direction_ref
    authority.parent.mkdir(parents=True)
    authority.write_text("# current authority\n", encoding="utf-8")
    live_sha = hashlib.sha256(authority.read_bytes()).hexdigest()
    registry_path = isolated_root / "docs/research/portfolio/workflow/registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "directions": [
                    {
                        "id": "example-direction",
                        "path": "docs/research/candidates/example-direction",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(state, "ROOT", isolated_root)

    current = fixture("research_state")
    current["direction_ref"]["sha256"] = "a" * 64
    target = tmp_path / "state.json"
    target.write_text(json.dumps(current), encoding="utf-8")
    candidate = copy.deepcopy(current)
    candidate["direction_ref"]["sha256"] = live_sha
    candidate["revision"] = 2

    with pytest.raises(state.ValidationError, match="research direction_ref SHA"):
        state.validate_document("research_state", current, writer=current["writer"])
    assert state.validate_document("research_state", candidate, writer=candidate["writer"]) == candidate

    before = target.read_bytes()
    stale_candidate = copy.deepcopy(candidate)
    stale_candidate["direction_ref"]["sha256"] = "b" * 64
    with pytest.raises(state.ValidationError, match="research direction_ref SHA"):
        state.replace(
            "research_state",
            target,
            candidate["writer"],
            expected_revision=1,
            input=stale_candidate,
        )
    assert target.read_bytes() == before

    with pytest.raises(state.RevisionConflictError, match="expected revision 2, observed 1"):
        state.replace(
            "research_state",
            target,
            candidate["writer"],
            expected_revision=2,
            input=candidate,
        )
    assert target.read_bytes() == before

    assert state.replace(
        "research_state",
        target,
        candidate["writer"],
        expected_revision=1,
        input=candidate,
    ) == candidate
    assert json.loads(target.read_text(encoding="utf-8")) == candidate

def test_concurrent_initialize_has_one_winner_and_losers_preserve_bytes(tmp_path: Path) -> None:
    source = FIXTURES / "research_state.json"
    target = tmp_path / "concurrent.json"

    def initialize() -> int:
        return run_cli(
            "initialize",
            "--kind",
            "research_state",
            "--path",
            str(target),
            "--writer",
            "EM-example-direction",
            "--input",
            str(source),
        ).returncode

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: initialize(), range(2)))
    assert sorted(outcomes) == [0, 4]
    assert target.read_bytes() == source.read_bytes()


def test_ignore_query_exposes_tracked_contracts_and_keeps_runtime_ignored() -> None:
    tracked = (
        ".omp/WATCHDOG.md",
        ".omp/RULES.md",
        ".omp/skills/hmasd-root-control/SKILL.md",
        "docs/research/portfolio/PORTFOLIO.md",
        "docs/research/portfolio/workflow/registry.json",
        "docs/external-review/directions/example/round/PRO_INNOVATOR_PROMPT.md",
    )
    ignored = (".omp/runtime/agents.json", "temp/directions/example/manifest.json")
    for path in tracked:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (path, result.stdout, result.stderr)
    for path in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (path, result.stdout, result.stderr)
