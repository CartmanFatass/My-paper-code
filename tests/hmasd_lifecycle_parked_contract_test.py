"""PARKED lifecycle representation and BrowserTransport state contracts."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
FIXTURES = ROOT / "tests" / "fixtures" / "hmasd_phase0"
REGISTRY_PATH = ROOT / "docs" / "research" / "portfolio" / "workflow" / "registry.json"
PORTFOLIO_PATH = ROOT / "docs" / "research" / "portfolio" / "PORTFOLIO.md"
AGENTS_PATH = ROOT / ".omp" / "AGENTS.md"

PARKED_DIRECTION_IDS = {
    "active_post_churn_population_flow_identification",
    "commitment_residual_triggered_options",
    "covariance_calibrated_information_clock",
    "dual_epoch_receipt_survival",
    "eociv_lite",
    "expressibility_gated_renewal_credit_relay",
    "finite_semantic_boundary_support",
    "roster_consistent_latent_exploration",
    "ucope",
}


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fixture(kind: str) -> dict:
    return json.loads((FIXTURES / f"{kind}.json").read_text(encoding="utf-8"))


def test_registry_has_exactly_the_source_known_parked_rows() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    parked = {
        direction["id"]
        for direction in registry["directions"]
        if direction["lifecycle"] == "PARKED"
    }
    assert parked == PARKED_DIRECTION_IDS
    assert all(
        direction["reactivation_condition_ref"] is not None
        for direction in registry["directions"]
        if direction["lifecycle"] == "PARKED"
    )
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(REGISTRY_PATH))
    assert result.returncode == 0, result.stderr


def test_parked_requires_a_reactivation_condition_without_changing_other_lifecycles(
    tmp_path: Path,
) -> None:
    source = fixture("portfolio_registry")
    direction = source["directions"][0]
    assert direction["lifecycle"] == "REGISTERED"
    assert direction["reactivation_condition_ref"] is None

    registered_path = tmp_path / "registered.json"
    write_json(registered_path, source)
    registered = run_cli(
        "validate", "--kind", "portfolio_registry", "--path", str(registered_path)
    )
    assert registered.returncode == 0, registered.stderr

    invalid = copy.deepcopy(source)
    invalid["directions"][0]["lifecycle"] = "PARKED"
    invalid_path = tmp_path / "parked-without-condition.json"
    write_json(invalid_path, invalid)
    rejected = run_cli(
        "validate", "--kind", "portfolio_registry", "--path", str(invalid_path)
    )
    assert rejected.returncode == 2, rejected.stderr

    valid = copy.deepcopy(invalid)
    valid["directions"][0]["reactivation_condition_ref"] = copy.deepcopy(
        valid["directions"][0]["lifecycle_decision_ref"]
    )
    valid_path = tmp_path / "parked-with-condition.json"
    write_json(valid_path, valid)
    accepted = run_cli(
        "validate", "--kind", "portfolio_registry", "--path", str(valid_path)
    )
    assert accepted.returncode == 0, accepted.stderr

    closed = copy.deepcopy(source)
    closed["directions"][0]["lifecycle"] = "CLOSED"
    closed_path = tmp_path / "closed.json"
    write_json(closed_path, closed)
    accepted = run_cli(
        "validate", "--kind", "portfolio_registry", "--path", str(closed_path)
    )
    assert accepted.returncode == 0, accepted.stderr


def test_browser_transport_is_a_root_child_and_retired_provider_roles_are_rejected(
    tmp_path: Path,
) -> None:
    runtime = fixture("runtime_agents")
    runtime["agents"] = [
        {
            "agent_type": "hmasd-browser-transport",
            "generation": 1,
            "last_seen_at": "2026-08-29T00:00:00Z",
            "lifecycle": "RUNNING",
            "logical_identity": "BrowserTransport",
            "job_ref": "BrowserTransport",
            "parent_identity": "Root",
            "runtime_ref": "runtime-browser-transport",
            "session_ref": "session-browser-transport",
        }
    ]
    runtime_path = tmp_path / "runtime-agents.json"
    write_json(runtime_path, runtime)
    accepted = run_cli("validate", "--kind", "runtime_agents", "--path", str(runtime_path))
    assert accepted.returncode == 0, accepted.stderr

    runtime["agents"][0]["agent_type"] = "hmasd-external-pro-transport"
    retired_path = tmp_path / "retired-runtime-agent.json"
    write_json(retired_path, runtime)
    rejected = run_cli("validate", "--kind", "runtime_agents", "--path", str(retired_path))
    assert rejected.returncode == 2, rejected.stderr


def test_browser_transport_owns_the_common_transport_result_payload(tmp_path: Path) -> None:
    result = fixture("agent_result")
    result.update(
        {
            "assignment_id": "cycle-1-innovator",
            "logical_identity": "BrowserTransport",
            "payload": {
                "archive_ref": None,
                "assistant_message_id": None,
                "browser_identity": "BrowserTransport",
                "browser_tab_ref": None,
                "commitment": "ZERO_PROVEN",
                "effect_ref": None,
                "failure": {"code": "NONE", "locus": "NONE"},
                "handoff_ref": None,
                "idempotency_key": "cycle-1-innovator",
                "kind": "transport",
                "message_capability": "AVAILABLE",
                "mode": "INNOVATOR",
                "observability": "UNOBSERVED",
                "operation_id": "cycle-1-innovator",
                "operation_ref": "agentify:cycle-1-innovator",
                "phase": "VALIDATE",
                "product_model": "GPT-5.6 Sol",
                "provider": "chatgpt",
                "provider_conversation_id": None,
                "provider_conversation_ref": None,
                "provider_user_message_count": 0,
                "reasoning_effort": "Pro",
                "recoverability": "PRECOMMIT_REPAIR",
                "requester": "EM-example-direction",
                "send_activation_count": 0,
                "transport_assignment": "cycle-1-innovator",
                "user_message_id": None,
            },
            "role": "hmasd-browser-transport",
            "summary": "BrowserTransport retained an unsent assignment.",
        }
    )
    path = tmp_path / "browser-result.json"
    write_json(path, result)
    accepted = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert accepted.returncode == 0, accepted.stderr

    result["role"] = "hmasd-external-pro-transport"
    retired_path = tmp_path / "retired-browser-result.json"
    write_json(retired_path, result)
    rejected = run_cli("validate", "--kind", "agent_result", "--path", str(retired_path))
    assert rejected.returncode == 2, rejected.stderr


def test_root_owned_browser_assignment_map_validates(tmp_path: Path) -> None:
    document = {
        "assignments": [
            {
                "archive_ref": None,
                "assistant_message_id": None,
                "assignment_id": "cycle-1-innovator",
                "browser_identity": "BrowserTransport",
                "browser_tab_ref": None,
                "commitment": "ZERO_PROVEN",
                "direction_id": "example-direction",
                "effect_ref": None,
                "failure": {"code": "NONE", "locus": "NONE"},
                "handoff_ref": None,
                "idempotency_key": "cycle-1-innovator",
                "message_capability": "AVAILABLE",
                "mode": "INNOVATOR",
                "observability": "UNOBSERVED",
                "operation_id": "cycle-1-innovator",
                "operation_ref": "agentify:cycle-1-innovator",
                "paused": True,
                "phase": "VALIDATE",
                "product_model": "GPT-5.6 Sol",
                "provider": "chatgpt",
                "provider_conversation_id": None,
                "provider_conversation_ref": None,
                "provider_user_message_count": 0,
                "reasoning_effort": "Pro",
                "recoverability": "PRECOMMIT_REPAIR",
                "request_ref": "request:cycle-1-innovator",
                "requester_identity": "EM-example-direction",
                "send_activation_count": 0,
                "updated_at": "2026-08-29T00:00:00Z",
                "user_message_id": None,
            }
        ],
        "revision": 1,
        "schema_version": 2,
        "updated_at": "2026-08-29T00:00:00Z",
        "writer": "Root",
    }
    path = tmp_path / "browser-assignments.json"
    write_json(path, document)
    result = run_cli(
        "validate", "--kind", "runtime_browser_assignments", "--path", str(path)
    )
    assert result.returncode == 0, result.stderr


def test_portfolio_records_representation_migration_and_current_resume_boundary() -> None:
    portfolio = " ".join(PORTFOLIO_PATH.read_text(encoding="utf-8").split())
    agents = " ".join(AGENTS_PATH.read_text(encoding="utf-8").split())

    for migration_anchor in (
        "## OMP non-control migration boundary",
        "This file is the OMP durable scientific authority after this migration",
        "user PAUSE/RESUME boundaries are migrated as non-control facts",
        "Root therefore adopts the user's current instruction as `RESUME`",
        "Representation migration restored the `PARKED` schema representation only",
        "for the eight source-known parked rows",
        "It did not reinterpret science or change any reactivation condition",
        "`PARK`: `dual_epoch_receipt_survival`",
        "The fourth authorized slot is intentionally unused",
    ):
        assert migration_anchor in portfolio

    assert (
        "`PARKED` has no live direction work, requires "
        "`reactivation_condition_ref`, and is not `CLOSED`"
    ) in agents
    assert (
        "`PAUSE` admits no fresh task or Effect, including Clerk, CAS, Git, send, "
        "Run, refill, or manager revival"
    ) in agents
    assert (
        "may validate deliveries and non-sendingly observe only an already-committed "
        "Effect through its existing owner"
    ) in agents
