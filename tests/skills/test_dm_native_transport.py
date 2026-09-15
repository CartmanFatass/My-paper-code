from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from hmasd_pro_research_prompt_author_test import _renderer, _request, project_root


def native(project_root):
    config = Path(__file__).resolve().parents[2] / ".codex/hmasd-transport.toml"
    (project_root / ".codex/hmasd-transport.toml").write_bytes(config.read_bytes())
    req = _request()
    req.update(source_thread_id="/root/dm_demo", parent_thread_id="/root/dm_demo",
               operator_thread_id="/root/dm_demo/transport", repository="example/repo",
               github_delivery={"branch": "codex/demo", "base_sha": "a" * 40,
               "response_path": "docs/research/candidates/demo_direction/pro_packets/test/archive/RESPONSE.md",
               "issue_url": "https://github.com/example/repo/issues/1"})
    return req


def validator():
    scripts = Path(__file__).resolve().parents[2] / ".agents/skills/hmasd-chatgpt-pro-transport/scripts"
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("native_request_validator", scripts / "validate_request.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_published_native_round_trip_and_no_rebind(project_root, monkeypatch):
    req = native(project_root)
    render = _renderer()
    out = project_root / "packet"
    render.prepare_github_delivery(req, project_root, out)
    path = out / "HANDOFF.json"
    h = json.loads(path.read_text())
    assert h["dispatch_state"] == "TASK_NOT_PUBLISHED"
    monkeypatch.setattr(render.subprocess, "check_output", lambda *a, **kw: (out / "TASK.md").read_bytes())
    render.bind_github_task(path, "b" * 40, project_root)
    h = json.loads(path.read_text())
    result = validator().validate(h["transport_request"], project_root)
    assert result["dispatch_mode"] == "REUSE_DM_TRANSPORT"
    assert result["parent_thread_id"] == req["source_thread_id"]
    assert result["operator_thread_id"] == req["operator_thread_id"]
    assert result["conversation_binding_key"] == "em:demo_direction:convergence"
    assert h["operator_thread_url"] is None
    assert "collaboration.followup_task" in h["dispatch_instruction"]
    assert "send_message_to_thread" not in h["dispatch_instruction"]
    before = path.read_bytes()
    render.record_operator_thread_id(path, req["operator_thread_id"])
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="routing mismatch"):
        render.record_operator_thread_id(path, "/root/dm_demo/replacement")
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="unpublished"):
        render.bind_github_task(path, "c" * 40, project_root)


@pytest.mark.parametrize("change", [
    {"parent_thread_id": "/root/other_dm"},
    {"operator_thread_id": "/root/other_dm/transport"},
    {"operator_thread_id": "/root/dm_demo"},
    {"execution_mode": "REUSE_SINGLETON"},
    {"operator_thread_id": ""},
])
def test_reject_cross_dm_or_missing_operator(project_root, change):
    req = native(project_root)
    req.update(change)
    with pytest.raises(ValueError):
        _renderer().validate(req, project_root)


def test_two_dms_have_distinct_operators_without_changing_nodes(project_root):
    req = native(project_root)
    r = _renderer()
    first = r.validate(req, project_root)
    req.update(source_thread_id="/root/dm_second", parent_thread_id="/root/dm_second",
               operator_thread_id="/root/dm_second/transport", direction_id="second_direction")
    second = r.validate(req, project_root)
    assert first["operator_thread_id"] != second["operator_thread_id"]
    assert second["conversation_binding_key"] == "em:second_direction:convergence"


def test_root_portfolio_replacement_routes_to_own_child(project_root, monkeypatch):
    req = native(project_root)
    req.update(source_thread_id="/root", parent_thread_id="/root",
               operator_thread_id="/root/transport", caller_role="portfolio",
               workflow_node="portfolio_decision", direction_ids=["demo_direction"])
    req["github_delivery"]["response_path"] = "docs/research/portfolio/pro_packets/replacement/archive/RESPONSE.md"
    render = _renderer()
    out = project_root / "replacement"
    render.prepare_github_delivery(req, project_root, out)
    monkeypatch.setattr(render.subprocess, "check_output", lambda *a, **kw: (out / "TASK.md").read_bytes())
    render.bind_github_task(out / "HANDOFF.json", "b" * 40, project_root)
    handoff = json.loads((out / "HANDOFF.json").read_text(encoding="utf-8"))
    result = validator().validate(handoff["transport_request"], project_root)
    assert result["parent_thread_id"] == "/root"
    assert result["operator_thread_id"] == "/root/transport"
    assert result["conversation_binding_key"] == "portfolio:cross_direction"
    req["operator_thread_id"] = "/root/dm_demo/transport"
    with pytest.raises(ValueError, match="direct child"):
        render.validate(req, project_root)


def test_agentify_generation_key_is_bounded_and_identity_specific():
    from hmasd_pro_conversation_binding_test import _module
    binder = _module("native_agentify_generation", "bind_conversation.py")
    node = "em:finite_resource_relational_inductive_efficiency:innovator"
    request = "portfolio-frrie-r02-exact-law-20260831-01-" + "x" * 150
    key = binder._agentify_generation_key(node, request)
    assert key.isascii() and len(key) <= 128
    assert key == binder._agentify_generation_key(node, request)
    assert key != binder._agentify_generation_key(node, request + "2")
    assert key != binder._agentify_generation_key(node + "2", request)
