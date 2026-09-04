from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents" / "skills" / "hmasd-chatgpt-pro-transport" / "scripts"


def _module(name: str, filename: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _project(tmp_path: Path) -> Path:
    portfolio = tmp_path / "docs" / "research" / "portfolio"
    portfolio.mkdir(parents=True)
    rows = []
    for direction_id in ("alpha", "beta"):
        direction = tmp_path / "docs" / "research" / "candidates" / direction_id
        direction.mkdir(parents=True)
        (direction / "DIRECTION.md").write_text(f"# {direction_id}\n", encoding="utf-8")
        rows.append(f"| {direction_id} | ACTIVE |")
    (portfolio / "PORTFOLIO.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return tmp_path


def _transport_request(**changes: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "alpha-innovator-01",
        "direction_id": "alpha",
        "direction_ids": ["alpha"],
        "workflow_node": "em_innovator",
        "conversation_binding_key": "em:alpha:innovator",
        "decision_authority": "pro_final",
        "source_thread_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "parent_thread_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "operator_thread_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "prompt": "Decide the next bounded object.",
    }
    request.update(changes)
    return request


def test_transport_validates_three_exact_decision_bindings(tmp_path: Path) -> None:
    validator = _module("hmasd_transport_validate_binding", "validate_request.py")
    project = _project(tmp_path)

    innovator = validator.validate(_transport_request(), project)
    convergence = validator.validate(
        _transport_request(
            request_id="alpha-convergence-01",
            workflow_node="em_convergence",
            conversation_binding_key="em:alpha:convergence",
        ),
        project,
    )
    portfolio = validator.validate(
        _transport_request(
            request_id="portfolio-01",
            direction_id="portfolio",
            direction_ids=["alpha", "beta"],
            workflow_node="portfolio_decision",
            conversation_binding_key="portfolio:cross_direction",
        ),
        project,
    )

    assert innovator["conversation_binding_key"] == "em:alpha:innovator"
    assert convergence["conversation_binding_key"] == "em:alpha:convergence"
    assert portfolio["conversation_binding_key"] == "portfolio:cross_direction"
    assert portfolio["direction_ids"] == ["alpha", "beta"]


def _bind_args(
    registry: Path,
    *,
    workflow_node: str,
    binding_key: str,
    direction_id: str,
    direction_ids: list[str],
    conversation_id: str,
    request_id: str,
    reset_invalid_provider_context: bool = False,
    provider_context_reset_evidence: dict[str, object] | None = None,
    observed_after_successful_send: bool = False,
    source_thread_id: str = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    parent_thread_id: str = "cccccccc-cccc-cccc-cccc-cccccccccccc",
    operator_thread_id: str = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
) -> argparse.Namespace:
    return argparse.Namespace(
        registry=registry,
        direction_id=direction_id,
        direction_ids_json=json.dumps(direction_ids),
        workflow_node=workflow_node,
        conversation_binding_key=binding_key,
        decision_authority="pro_final",
        conversation_id=conversation_id,
        provider_url=f"https://chatgpt.com/c/{conversation_id}",
        tab_id=None,
        request_id=request_id,
        visible_model="Pro",
        underlying_model="GPT-5.6 Sol",
        thinking_effort="5/5",
        source_mode="upload",
        prompt_sha256="0" * 64,
        reference_files_json="[]",
        source_thread_id=source_thread_id,
        parent_thread_id=parent_thread_id,
        operator_thread_id=operator_thread_id,
        packet_id=None,
        packet_manifest=None,
        tab_origin="agent",
        reset_invalid_provider_context=reset_invalid_provider_context,
        provider_context_reset_evidence=provider_context_reset_evidence,
        observed_after_successful_send=observed_after_successful_send,
    )


def _reset_evidence(previous_request_id: str, **changes: object) -> dict[str, object]:
    evidence: dict[str, object] = {
        "previous_request_id": previous_request_id,
        "decision_outcome": "DECISION_NOT_FORMED",
        "repository_paths_read": 0,
        "provider_context_contamination_acknowledged": True,
        "acknowledged_prompt_defect": "obsolete provider-visible dispatch instruction",
    }
    evidence.update(changes)
    return evidence


def _persist_reset_facts(contract, record: dict, *, outcome: str = "DECISION_NOT_FORMED", paths_read: int = 0) -> None:
    contract.persist_archived_provider_context_reset_facts(
        record,
        decision_outcome=outcome,
        repository_paths_read=paths_read,
        provider_context_contamination_acknowledged=True,
        acknowledged_prompt_defect="obsolete provider-visible dispatch instruction",
    )


def test_registry_binds_two_direction_nodes_and_one_portfolio_node_separately(
    tmp_path: Path,
) -> None:
    binder = _module("hmasd_transport_bind_nodes", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    ids = {
        "innovator": "11111111-1111-1111-1111-111111111111",
        "convergence": "22222222-2222-2222-2222-222222222222",
        "portfolio": "33333333-3333-3333-3333-333333333333",
    }

    assert binder.bind(
        _bind_args(
            registry,
            workflow_node="em_innovator",
            binding_key="em:alpha:innovator",
            direction_id="alpha",
            direction_ids=["alpha"],
            conversation_id=ids["innovator"],
            request_id="alpha-innovator-01",
        )
    ) == 0
    assert binder.bind(
        _bind_args(
            registry,
            workflow_node="em_convergence",
            binding_key="em:alpha:convergence",
            direction_id="alpha",
            direction_ids=["alpha"],
            conversation_id=ids["convergence"],
            request_id="alpha-convergence-01",
        )
    ) == 0
    assert binder.bind(
        _bind_args(
            registry,
            workflow_node="portfolio_decision",
            binding_key="portfolio:cross_direction",
            direction_id="portfolio",
            direction_ids=["alpha", "beta"],
            conversation_id=ids["portfolio"],
            request_id="portfolio-01",
        )
    ) == 0

    value = json.loads(registry.read_text(encoding="utf-8"))
    assert set(value["bindings"]) == {
        "em:alpha:innovator",
        "em:alpha:convergence",
        "portfolio:cross_direction",
    }
    assert value["bindings"]["em:alpha:innovator"]["conversation_id"] == ids["innovator"]
    assert value["bindings"]["em:alpha:convergence"]["conversation_id"] == ids["convergence"]
    assert value["bindings"]["portfolio:cross_direction"]["direction_ids"] == ["alpha", "beta"]


def test_one_provider_conversation_cannot_back_two_decision_bindings(tmp_path: Path) -> None:
    binder = _module("hmasd_transport_bind_unique", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    conversation_id = "44444444-4444-4444-4444-444444444444"
    assert binder.bind(
        _bind_args(
            registry,
            workflow_node="em_innovator",
            binding_key="em:alpha:innovator",
            direction_id="alpha",
            direction_ids=["alpha"],
            conversation_id=conversation_id,
            request_id="alpha-innovator-01",
        )
    ) == 0
    assert binder.bind(
        _bind_args(
            registry,
            workflow_node="em_convergence",
            binding_key="em:alpha:convergence",
            direction_id="alpha",
            direction_ids=["alpha"],
            conversation_id=conversation_id,
            request_id="alpha-convergence-01",
        )
    ) == 3

    value = json.loads(registry.read_text(encoding="utf-8"))
    assert set(value["bindings"]) == {"em:alpha:innovator"}


def test_persistent_binding_allows_next_round_only_after_archive(tmp_path: Path) -> None:
    binder = _module("hmasd_transport_bind_rounds", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    conversation_id = "55555555-5555-5555-5555-555555555555"
    first = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key="em:alpha:innovator",
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=conversation_id,
        request_id="alpha-innovator-01",
    )
    second = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key="em:alpha:innovator",
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=conversation_id,
        request_id="alpha-innovator-02",
        source_thread_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        parent_thread_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        operator_thread_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
    )

    assert binder.bind(first) == 0
    assert binder.bind(second) == 4

    value = json.loads(registry.read_text(encoding="utf-8"))
    value["bindings"]["em:alpha:innovator"]["state"] = "ARCHIVED"
    value["directions"]["alpha"]["state"] = "ARCHIVED"
    registry.write_text(json.dumps(value), encoding="utf-8")

    assert binder.bind(second) == 0
    current = json.loads(registry.read_text(encoding="utf-8"))["bindings"]["em:alpha:innovator"]
    assert current["conversation_id"] == conversation_id
    assert current["request_id"] == "alpha-innovator-02"
    assert current["state"] == "DIRECTION_VERIFIED"
    assert current["request_history"][-1]["request_id"] == "alpha-innovator-01"
    assert current["request_history"][-1]["creator_thread_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert current["request_history"][-1]["parent_thread_id"] == "cccccccc-cccc-cccc-cccc-cccccccccccc"
    assert current["request_history"][-1]["operator_thread_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert current["creator_thread_id"] == "cccccccc-cccc-cccc-cccc-cccccccccccc"
    assert current["parent_thread_id"] == "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    assert current["operator_thread_id"] == "dddddddd-dddd-dddd-dddd-dddddddddddd"


def test_evidenced_provider_context_reset_quarantines_then_binds_only_new_observed_url(
    tmp_path: Path,
) -> None:
    binder = _module("hmasd_transport_context_reset", "bind_conversation.py")
    contract = _module("hmasd_transport_context_reset_contract", "transport_contract.py")
    registry = tmp_path / "registry.json"
    old_id = "66666666-6666-6666-6666-666666666666"
    new_id = "77777777-7777-7777-7777-777777777777"
    binding_key = "em:alpha:innovator"
    first = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key=binding_key,
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=old_id,
        request_id="alpha-innovator-01",
    )
    assert binder.bind(first) == 0
    before_reset = json.loads(registry.read_text(encoding="utf-8"))
    before_reset["bindings"][binding_key]["state"] = "ARCHIVED"
    _persist_reset_facts(contract, before_reset["bindings"][binding_key])
    registry.write_text(json.dumps(before_reset), encoding="utf-8")
    evidence = _reset_evidence("alpha-innovator-01")

    prepared = binder.prepare_context_reset(
        registry,
        conversation_binding_key=binding_key,
        replacement_request_id="alpha-innovator-02",
        reset_invalid_provider_context=True,
        provider_context_reset_evidence=evidence,
    )
    assert prepared["state"] == "CONTEXT_RESET_PENDING"
    assert prepared["conversation_id"] is None
    assert prepared["provider_url"] is None
    assert prepared["request_history"][-1]["request_id"] == "alpha-innovator-01"
    assert prepared["quarantined_provider_conversations"][-1]["conversation_id"] == old_id
    pending = json.loads(registry.read_text(encoding="utf-8"))
    assert pending["quarantined_conversations"][old_id]["conversation_binding_key"] == binding_key

    unobserved = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key=binding_key,
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=new_id,
        request_id="alpha-innovator-02",
        reset_invalid_provider_context=True,
        provider_context_reset_evidence=evidence,
    )
    pending_bytes = registry.read_bytes()
    assert binder.bind(unobserved) == 3
    assert registry.read_bytes() == pending_bytes

    observed = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key=binding_key,
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=new_id,
        request_id="alpha-innovator-02",
        reset_invalid_provider_context=True,
        provider_context_reset_evidence=evidence,
        observed_after_successful_send=True,
    )
    assert binder.bind(observed) == 0
    current = json.loads(registry.read_text(encoding="utf-8"))["bindings"][binding_key]
    assert current["conversation_id"] == new_id
    assert current["provider_url"] == f"https://chatgpt.com/c/{new_id}"
    assert current["state"] == "SEND_CONFIRMED"
    assert current["send_click_count"] == 1
    assert current["send_evidence"]["post_send_replacement"] is True
    with pytest.raises(ValueError, match="invalid transport transition"):
        contract.validate_transition(current["state"], "SEND_ATTEMPTED")
    assert current["last_provider_context_reset"]["quarantined_conversation_id"] == old_id

    old_for_another_node = _bind_args(
        registry,
        workflow_node="em_convergence",
        binding_key="em:alpha:convergence",
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id=old_id,
        request_id="alpha-convergence-01",
    )
    assert binder.bind(old_for_another_node) == 3


@pytest.mark.parametrize(
    ("state", "flag", "evidence_changes"),
    [
        ("ARCHIVED", False, {}),
        ("DIRECTION_VERIFIED", True, {}),
        ("ARCHIVED", True, {"previous_request_id": "wrong-prior"}),
        ("ARCHIVED", True, {"decision_outcome": "DECISION_FORMED"}),
        ("ARCHIVED", True, {"repository_paths_read": 1}),
        ("ARCHIVED", True, {"provider_context_contamination_acknowledged": False}),
        ("ARCHIVED", True, {"acknowledged_prompt_defect": ""}),
    ],
)
def test_every_invalid_context_reset_gate_leaves_registry_unchanged(
    tmp_path: Path,
    state: str,
    flag: bool,
    evidence_changes: dict[str, object],
) -> None:
    binder = _module("hmasd_transport_context_reset_gates", "bind_conversation.py")
    contract = _module("hmasd_transport_context_reset_gates_contract", "transport_contract.py")
    registry = tmp_path / "registry.json"
    binding_key = "em:alpha:innovator"
    first = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key=binding_key,
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id="88888888-8888-8888-8888-888888888888",
        request_id="alpha-innovator-01",
    )
    assert binder.bind(first) == 0
    value = json.loads(registry.read_text(encoding="utf-8"))
    value["bindings"][binding_key]["state"] = state
    if state == "ARCHIVED":
        _persist_reset_facts(contract, value["bindings"][binding_key])
    registry.write_text(json.dumps(value), encoding="utf-8")
    before = registry.read_bytes()
    evidence = _reset_evidence("alpha-innovator-01")
    evidence.update(evidence_changes)

    with pytest.raises(ValueError):
        binder.prepare_context_reset(
            registry,
            conversation_binding_key=binding_key,
            replacement_request_id="alpha-innovator-02",
            reset_invalid_provider_context=flag,
            provider_context_reset_evidence=evidence,
        )

    assert registry.read_bytes() == before


def test_missing_or_contradicted_archived_reset_facts_refuse_without_mutation(tmp_path: Path) -> None:
    binder = _module("hmasd_transport_archived_facts", "bind_conversation.py")
    contract = _module("hmasd_transport_archived_facts_contract", "transport_contract.py")
    registry = tmp_path / "registry.json"
    binding_key = "em:alpha:innovator"
    first = _bind_args(
        registry,
        workflow_node="em_innovator",
        binding_key=binding_key,
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id="99999999-9999-9999-9999-999999999999",
        request_id="alpha-innovator-01",
    )
    assert binder.bind(first) == 0
    value = json.loads(registry.read_text(encoding="utf-8"))
    record = value["bindings"][binding_key]
    record["state"] = "ARCHIVED"
    registry.write_text(json.dumps(value), encoding="utf-8")
    evidence = _reset_evidence("alpha-innovator-01")
    missing_before = registry.read_bytes()
    with pytest.raises(ValueError, match="archived provider-context reset facts are missing"):
        binder.prepare_context_reset(
            registry,
            conversation_binding_key=binding_key,
            replacement_request_id="alpha-innovator-02",
            reset_invalid_provider_context=True,
            provider_context_reset_evidence=evidence,
        )
    assert registry.read_bytes() == missing_before

    _persist_reset_facts(contract, record, outcome="FINAL_DIRECTION_DECISION:CLOSE", paths_read=9)
    registry.write_text(json.dumps(value), encoding="utf-8")
    contradicted_before = registry.read_bytes()
    with pytest.raises(ValueError, match="caller evidence disagrees with archived decision_outcome"):
        binder.prepare_context_reset(
            registry,
            conversation_binding_key=binding_key,
            replacement_request_id="alpha-innovator-02",
            reset_invalid_provider_context=True,
            provider_context_reset_evidence=evidence,
        )
    assert registry.read_bytes() == contradicted_before
