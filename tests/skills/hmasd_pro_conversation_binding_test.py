from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


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
        source_thread_id=None,
        fallback_enabled=False,
        fallback_thread_id=None,
        packet_id=None,
        packet_manifest=None,
        tab_origin="agent",
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
