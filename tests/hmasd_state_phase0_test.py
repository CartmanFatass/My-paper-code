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

SCHEMA_KINDS = (
    *KINDS,
    "runtime_browser_assignments",
    "clerk_operation",
)


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


def clerk_packet() -> dict[str, Any]:
    packet: dict[str, Any] = {
        "schema_version": 1,
        "kind": "clerk_operation",
        "operation_id": "state-cas-operation-001",
        "clerk_assignment_id": "state-cas-clerk-001",
        "executor": {
            "role": "hmasd-clerk",
            "logical_identity": "Clerk-state-cas-clerk-001",
            "generation": 1,
        },
        "authorizer": {
            "role": "root",
            "logical_identity": "Root",
            "generation": 1,
            "assignment_id": "root-state-cas-authorizer",
        },
        "operation": "STATE_CAS",
        "requires": [
            {
                "authority_ref": {
                    "path": ".omp/runtime/agents.json",
                    "sha256": "1" * 64,
                },
                "revision_or_checkpoint": 1,
            }
        ],
        "authority": {
            "direction_id": None,
            "document_writer": "Root",
            "git_actor": None,
            "worktree_kind": None,
            "assignment_authority": "SHARED",
        },
        "mutation": {
            "class": "STATE_PATH",
            "resources": [
                {
                    "kind": "STATE_PATH",
                    "key": "/home/fires/hmasd/.omp/runtime/agents.json",
                }
            ],
        },
        "effect": {
            "attempt": 1,
            "attempt_token": "2" * 64,
            "authorized_effects": ["STATE_CAS"],
            "unknown_outcome": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "target": {
            "state_kind": "runtime_agents",
            "canonical_target_path": "/home/fires/hmasd/.omp/runtime/agents.json",
            "expected_revision": 1,
            "input_ref": {
                "path": "temp/clerk/state-cas-clerk-001/input.json",
                "sha256": "3" * 64,
            },
            "expected_document_writer": "Root",
        },
        "acceptance_refs": [
            {
                "path": "temp/clerk/state-cas-clerk-001/acceptance.json",
                "sha256": "4" * 64,
            }
        ],
        "postconditions": {
            "success": ["revision is exactly 2 and desired bytes match"],
            "refusal": ["target bytes and revision remain unchanged"],
            "unknown": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "stop_condition": "Return after one terminal claim receipt.",
        "return_owner": "ROOT",
    }
    packet["packet_sha256"] = hashlib.sha256(
        (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    ).hexdigest()
    return packet


def rehash_clerk_packet(packet: dict[str, Any]) -> None:
    packet.pop("packet_sha256", None)
    packet["packet_sha256"] = hashlib.sha256(
        (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    ).hexdigest()


def worktree_packet(operation: str) -> dict[str, Any]:
    assert operation in {"WORKTREE_PROVISION", "WORKTREE_RELEASE"}
    packet = clerk_packet()
    clerk_assignment_id = f"{operation.lower().replace('_', '-')}-clerk-001"
    packet["operation_id"] = f"{operation.lower().replace('_', '-')}-operation-001"
    packet["clerk_assignment_id"] = clerk_assignment_id
    packet["executor"]["logical_identity"] = f"Clerk-{clerk_assignment_id}"
    packet["operation"] = operation
    packet["authority"] = {
        "direction_id": "example-direction",
        "document_writer": None,
        "git_actor": "root",
        "worktree_kind": "research",
        "assignment_authority": "SHARED",
    }
    packet["mutation"] = {
        "class": "WORKTREE_REGISTRY",
        "resources": [
            {
                "kind": (
                    "CONTAINER"
                    if operation == "WORKTREE_PROVISION"
                    else "RUNTIME_WORKTREES_STATE"
                ),
                "key": (
                    "/home/fires/hmasd-worktrees"
                    if operation == "WORKTREE_PROVISION"
                    else "/home/fires/hmasd/.omp/runtime/worktrees.json"
                ),
            },
            {
                "kind": (
                    "RUNTIME_WORKTREES_STATE"
                    if operation == "WORKTREE_PROVISION"
                    else "WORKTREE"
                ),
                "key": (
                    "/home/fires/hmasd/.omp/runtime/worktrees.json"
                    if operation == "WORKTREE_PROVISION"
                    else "/home/fires/hmasd-worktrees/example-direction-research-assignment-001"
                ),
            },
        ],
    }
    packet["effect"]["authorized_effects"] = [operation]
    mutation_lease = {
        "manager_assignment_id": "root-worktree-manager-001",
        "clerk_assignment_id": clerk_assignment_id,
        "handoff_ref": {
            "path": f"temp/clerk/{clerk_assignment_id}/handoff.json",
            "sha256": "b" * 64,
        },
        "lease_token": "c" * 64,
    }
    common_target = {
        "canonical_repo_path": "/home/fires/hmasd",
        "canonical_container_path": "/home/fires/hmasd-worktrees",
        "canonical_worktree_path": (
            "/home/fires/hmasd-worktrees/example-direction-research-assignment-001"
        ),
        "worktree_ref": "example-direction-research-assignment-001",
        "direction_id": "example-direction",
        "worktree_kind": "research",
        "base_sha": "a" * 40,
        "expected_registry_revision": 1,
        "mutation_lease": mutation_lease,
    }
    if operation == "WORKTREE_PROVISION":
        packet["target"] = {
            **common_target,
            "integration_policy": "EXACT_HANDOFF",
            "parallel_set_manifest_ref": None,
            "expected_lifecycle": "ABSENT",
            "expected_receipt_sha256": None,
            "required_handoff_sha": "a" * 40,
            "required_dependency_refs": [],
            "prior_operation_receipt": None,
        }
    else:
        packet["target"] = {
            **common_target,
            "expected_lifecycle": "PROVISIONED",
            "expected_receipt_sha256": "d" * 64,
            "ignored_artifacts": "refuse",
            "policy": "EXACT_HANDOFF",
            "required_handoff_sha": "a" * 40,
            "required_dependency_refs": [],
            "prior_operation_receipt": None,
        }
    rehash_clerk_packet(packet)
    return packet


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
        "kind": "EXECUTE_CLERK_PACKET",
        "owner": "CLERK",
        "input_refs": [
            {
                "path": "temp/clerk/persist-research-state/packet.json",
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
            "path": "temp/clerk/persist-research-state/effect.json",
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


def test_clerk_result_identity_authority_and_no_decision_boundary(
    tmp_path: Path,
) -> None:
    packet = clerk_packet()
    document = fixture("agent_result")
    document.update(
        {
            "assignment_id": packet["clerk_assignment_id"],
            "logical_identity": packet["executor"]["logical_identity"],
            "materiality": "LOCAL",
            "role": "hmasd-clerk",
            "summary": "Observed one terminal Clerk operation receipt.",
            "payload": {
                "kind": "clerk",
                "operation_id": packet["operation_id"],
                "packet_ref": {
                    "path": "temp/clerk/state-cas-clerk-001/packet.json",
                    "sha256": packet["packet_sha256"],
                },
                "executor_identity": packet["executor"]["logical_identity"],
                "authorizer": packet["authorizer"],
                "operation": packet["operation"],
                "authority_actor_or_writer": "Root",
                "resources": packet["mutation"]["resources"],
                "attempt": 1,
                "outcome": "SUCCEEDED",
                "effect_state": "LANDED",
                "receipt_refs": [
                    {
                        "path": "temp/clerk/state-cas-clerk-001/receipt.json",
                        "sha256": "9" * 64,
                    }
                ],
                "observation_refs": [],
            },
        }
    )
    path = tmp_path / "clerk-result.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    wrong_identity = copy.deepcopy(document)
    wrong_identity["logical_identity"] = "Clerk-other-clerk-001"
    path.write_text(json.dumps(wrong_identity), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 5
    fallback = copy.deepcopy(document)
    fallback["payload"]["resolved_model_is_fallback"] = True
    path.write_text(json.dumps(fallback), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    wrong_model = copy.deepcopy(document)
    wrong_model["payload"]["resolved_model"] = "openai-codex/gpt-5.6-sol"
    path.write_text(json.dumps(wrong_model), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2

    changed_actor = copy.deepcopy(document)
    changed_actor["payload"]["authority_actor_or_writer"] = "cm:example-direction"
    path.write_text(json.dumps(changed_actor), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 5

    decision = copy.deepcopy(document)
    decision["materiality"] = "USER"
    decision["decision_requests"] = [
        {
            "kind": "USER_DECISION",
            "ref": {
                "path": "temp/clerk/state-cas-clerk-001/decision.json",
                "sha256": "a" * 64,
            },
        }
    ]
    path.write_text(json.dumps(decision), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 5

    extra = copy.deepcopy(document)
    extra["payload"]["successor"] = "ROOT"
    path.write_text(json.dumps(extra), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


def test_clerk_operation_packet_is_closed_content_addressed_and_inert(
    tmp_path: Path,
) -> None:
    packet = clerk_packet()
    path = tmp_path / "clerk-operation.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 0, result.stderr
    provision = worktree_packet("WORKTREE_PROVISION")
    path.write_text(json.dumps(provision), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 0, result.stderr

    missing_policy = copy.deepcopy(provision)
    del missing_policy["target"]["integration_policy"]
    rehash_clerk_packet(missing_policy)
    path.write_text(json.dumps(missing_policy), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    exact_with_parallel_set = copy.deepcopy(provision)
    exact_with_parallel_set["target"]["parallel_set_manifest_ref"] = {
        "path": "docs/project/parallel-sets/example.json",
        "sha256": "e" * 64,
    }
    rehash_clerk_packet(exact_with_parallel_set)
    path.write_text(json.dumps(exact_with_parallel_set), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    orthogonal = copy.deepcopy(provision)
    orthogonal["target"]["integration_policy"] = "ORTHOGONAL_DIRECTION"
    orthogonal["target"]["parallel_set_manifest_ref"] = {
        "path": "docs/project/parallel-sets/example.json",
        "sha256": "e" * 64,
    }
    orthogonal["target"]["required_handoff_sha"] = None
    rehash_clerk_packet(orthogonal)
    path.write_text(json.dumps(orthogonal), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 0, result.stderr

    orthogonal_without_parallel_set = copy.deepcopy(orthogonal)
    orthogonal_without_parallel_set["target"]["parallel_set_manifest_ref"] = None
    rehash_clerk_packet(orthogonal_without_parallel_set)
    path.write_text(json.dumps(orthogonal_without_parallel_set), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    release = worktree_packet("WORKTREE_RELEASE")
    path.write_text(json.dumps(release), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 0, result.stderr

    implicit_release_disposition = copy.deepcopy(release)
    del implicit_release_disposition["target"]["ignored_artifacts"]
    rehash_clerk_packet(implicit_release_disposition)
    path.write_text(json.dumps(implicit_release_disposition), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    invalid_release_disposition = copy.deepcopy(release)
    invalid_release_disposition["target"]["ignored_artifacts"] = "default"
    rehash_clerk_packet(invalid_release_disposition)
    path.write_text(json.dumps(invalid_release_disposition), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    malformed_identity = copy.deepcopy(packet)
    malformed_identity["executor"]["logical_identity"] = "Clerk-other-clerk-001"
    rehash_clerk_packet(malformed_identity)
    path.write_text(json.dumps(malformed_identity), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 5

    changed_writer = copy.deepcopy(packet)
    changed_writer["authority"]["document_writer"] = "CM-example-direction"
    changed_writer["target"]["expected_document_writer"] = "CM-example-direction"
    rehash_clerk_packet(changed_writer)
    path.write_text(json.dumps(changed_writer), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 5
    changed_actor = copy.deepcopy(packet)
    changed_actor["authority"]["git_actor"] = "cm:example-direction"
    rehash_clerk_packet(changed_actor)
    path.write_text(json.dumps(changed_actor), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 5

    wrong_model = copy.deepcopy(packet)
    wrong_model["executor"]["model"] = "openai-codex/gpt-5.6-sol"
    rehash_clerk_packet(wrong_model)
    path.write_text(json.dumps(wrong_model), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    wrong_return = copy.deepcopy(packet)
    wrong_return["return_owner"] = "CLERK"
    rehash_clerk_packet(wrong_return)
    path.write_text(json.dumps(wrong_return), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    extra = copy.deepcopy(packet)
    extra["decision_request"] = "RETRY"
    rehash_clerk_packet(extra)
    path.write_text(json.dumps(extra), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2

    wrong_hash = copy.deepcopy(packet)
    wrong_hash["packet_sha256"] = "0" * 64
    path.write_text(json.dumps(wrong_hash), encoding="utf-8")
    result = run_cli("validate", "--kind", "clerk_operation", "--path", str(path))
    assert result.returncode == 2


def test_runtime_clerks_are_unique_per_assignment_root_children(
    tmp_path: Path,
) -> None:
    document = fixture("runtime_agents")
    document["agents"].append(
        {
            "logical_identity": "Clerk-state-cas-clerk-001",
            "agent_type": "hmasd-clerk",
            "generation": 1,
            "assignment_id": "state-cas-clerk-001",
            "parent_identity": "Root",
            "session_ref": "session-clerk-state-cas",
            "job_ref": "job-clerk-state-cas",
            "runtime_ref": "runtime-clerk-state-cas",
            "lifecycle": "RUNNING",
            "last_seen_at": "2026-08-24T00:00:00Z",
        }
    )
    path = tmp_path / "runtime-agents-clerk.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "runtime_agents", "--path", str(path))
    assert result.returncode == 0, result.stderr

    wrong_assignment = copy.deepcopy(document)
    wrong_assignment["agents"][-1]["assignment_id"] = "other-clerk-001"
    path.write_text(json.dumps(wrong_assignment), encoding="utf-8")
    result = run_cli("validate", "--kind", "runtime_agents", "--path", str(path))
    assert result.returncode == 5

    wrong_parent = copy.deepcopy(document)
    wrong_parent["agents"][-1]["parent_identity"] = "EM-example-direction"
    path.write_text(json.dumps(wrong_parent), encoding="utf-8")
    result = run_cli("validate", "--kind", "runtime_agents", "--path", str(path))
    assert result.returncode == 2
    parked = copy.deepcopy(document)
    parked["agents"][-1]["lifecycle"] = "PARKED"
    path.write_text(json.dumps(parked), encoding="utf-8")
    result = run_cli("validate", "--kind", "runtime_agents", "--path", str(path))
    assert result.returncode == 2

    extra = copy.deepcopy(document)
    extra["agents"][-1]["advisor"] = "off"
    path.write_text(json.dumps(extra), encoding="utf-8")
    result = run_cli("validate", "--kind", "runtime_agents", "--path", str(path))
    assert result.returncode == 2


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
        "operation_id": "operation-a",
        "idempotency_key": "idempotency-a",
        "operation_ref": {
            "path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/chatgpt/operation_ref.json",
            "sha256": "1" * 64,
        },
        "provider_conversation_ref": "https://chatgpt.com/c/conversation-a",
        "provider_conversation_id": "conversation-a",
        "phase": "TERMINAL",
        "commitment": "ONE_EXACT",
        "recoverability": "NONE",
        "observability": "FRESH_COMPLETE",
        "message_capability": "SEALED",
        "failure": {"locus": "NONE", "code": "NONE"},
        "provider_user_message_count": 1,
        "send_activation_count": 1,
        "user_message_id": "user-message-a",
        "assistant_message_id": "assistant-message-a",
        "archive_ref": {
            "path": "docs/external-review/directions/example-direction/038544507c6e759ace8b/pro_innovator/chatgpt/response.md",
            "sha256": "2" * 64,
        },
        "handoff_ref": None,
        "completed_at": "2026-08-24T00:01:00Z",
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
