from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

import tools.codex_supervisor.cli as cli_module
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.cli import main
from tools.codex_supervisor.durability.outbox import AppServerOutbox, MutationSpec
from tools.codex_supervisor.runtime_inspect import (
    explain_why_not_wake,
    inspect_actor,
    inspect_binding,
    inspect_effect,
    inspect_incident,
    inspect_thread,
)
from tools.codex_supervisor.store import ObserverStore


def test_exact_runtime_inspectors_use_local_durable_rows(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    store = seeded["supervisor"]
    binding_id = seeded["portfolio_binding_id"]
    binding = seeded["bindings"].get(binding_id)
    run_id = store.start_run(
        codex_binary="fake", codex_version="1", client_name="inspect", process_id=None
    )
    outbox = AppServerOutbox(store.connection)
    operation = outbox.enqueue(MutationSpec(
        "inspect-resume", run_id, run_id, "thread/resume",
        {"threadId": binding.thread_id}, f"binding:{binding_id}",
        binding.thread_id, binding_id,
    ))
    claim = outbox.claim(
        operation.operation_id, protocol_session_id=run_id,
        target=f"binding:{binding_id}", thread_id=binding.thread_id,
    )
    outbox.mark_unknown(claim, error="inspect-ambiguous")

    assert inspect_actor(store, binding.actor_context_id)["bindings"][0]["binding_id"] == binding_id
    assert inspect_binding(store, binding_id)["binding"]["thread_id"] == "thr_port"
    assert inspect_thread(store, "thr_port")["binding"]["binding_id"] == binding_id
    assert inspect_effect(store, operation.operation_id)["operation"]["state"] == "UNKNOWN"
    incident = inspect_incident(store, operation.operation_id)
    assert incident["records"][0]["kind"] == "operation"
    reasons = explain_why_not_wake(store, binding_id, single_wake_state="CONSUMED")["reasons"]
    assert "single_wake_consumed" in reasons
    assert "effect_unreconciled" in reasons
    seeded["bridge"].close(); store.close(); seeded["semantic"].close()


def test_explain_reasons_are_bounded_and_factual(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    result = explain_why_not_wake(store, "missing", single_wake_state="UNARMED")
    assert result["reasons"] == [
        "binding_not_active", "unknown_readiness", "mailbox_empty", "single_wake_not_armed"
    ]
    allowed = {
        "binding_not_active", "semantic_actor_not_eligible", "thread_not_idle",
        "unknown_readiness", "open_batch_exists", "mailbox_empty", "lease_missing",
        "single_wake_not_armed", "single_wake_consumed", "effect_unreconciled",
        "incident_requires_operator",
    }
    assert set(result["reasons"]) <= allowed
    store.close()


def test_read_only_cli_inspect_and_explain(
    tmp_path: Path, repo_root: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-runtime-inspect-"))
    ObserverStore(runtime).close()
    database = runtime / "state.sqlite3"
    before = (database.read_bytes(), database.stat().st_mtime_ns)
    monkeypatch.setattr(
        cli_module, "ObserverStore",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("ObserverStore used")),
    )
    common = ["--repo-root", str(repo_root), "--runtime-home", str(runtime)]
    assert main([*common, "inspect", "--binding-id", "missing"]) == 0
    assert json.loads(capsys.readouterr().out)["binding"] is None
    assert main([*common, "explain", "--binding-id", "missing"]) == 0
    assert "binding_not_active" in json.loads(capsys.readouterr().out)["reasons"]
    assert (database.read_bytes(), database.stat().st_mtime_ns) == before
    absent = Path(tempfile.mkdtemp(prefix="hmasd-runtime-absent-")) / "missing"
    with pytest.raises(FileNotFoundError):
        main(["--repo-root", str(repo_root), "--runtime-home", str(absent), "inspect", "--binding-id", "x"])
    assert not absent.exists()


def test_inspection_module_has_no_transport_or_mutation_dependency(repo_root: Path) -> None:
    source = (repo_root / "tools/codex_supervisor/runtime_inspect.py").read_text(encoding="utf-8")
    for forbidden in ("transport", "AppServerClient", "send(", "send_bytes", "mcp"):
        assert forbidden not in source
