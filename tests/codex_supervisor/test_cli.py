from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import write_fake_codex
from tools.codex_supervisor.cli import _parser, _semantic_state_for_profile, main
from tools.codex_supervisor.models import ProtocolIds, RpcShape
from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.runtime_profiles import RuntimeProfile
from tools.codex_supervisor.store import ObserverStore
from tools.codex_semantic_mvp.store import SemanticStore


def test_doctor_does_not_launch_app_server(tmp_path: Path, repo_root: Path, capsys) -> None:
    wrapper = (repo_root / "scripts/codex-supervisor-durability-doctor.ps1").read_text(encoding="utf-8")
    assert "-m tools.codex_supervisor --repo-root $RepoRoot doctor" in wrapper
    assert "exit $LASTEXITCODE" in wrapper
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    binary = write_fake_codex(tmp_path)
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "--codex-bin",
            str(binary),
            "doctor",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["observer_only"] is False
    assert payload["automatic_turn_start_enabled"] is False
    assert payload["managed_actor_binding_enabled"] is True
    assert payload["managed_actor_hosting_enabled"] is True
    assert payload["automatic_wake_code_present"] is True
    assert payload["automatic_wake_live_accepted"] is False
    assert payload["live_wake_accepted"] is False
    assert payload["synthetic_stage"] == 4
    assert payload["mailbox_enabled"] is True
    assert payload["automatic_turn_steer_enabled"] is False
    assert payload["automatic_approval_enabled"] is False
    assert payload["semantic_authority_mutation_enabled"] is False
    assert payload["semantic_delivery_mutation_enabled"] is True
    assert payload["canonical_artifact_write_enabled"] is False
    assert payload["unexpected_server_request_policy"] == "terminate"
    assert payload["codex_version"].startswith("codex-fake")


def test_timeline_cli(tmp_path: Path, repo_root: Path, capsys) -> None:
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    store = ObserverStore(runtime)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)
    message = {
        "method": "turn/completed",
        "params": {"threadId": "thr_cli", "turn": {"id": "turn", "status": "failed"}},
    }
    raw = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=1,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=ProtocolIds(None, "turn/completed", "thr_cli", "turn", None),
        payload=message,
    )
    event = normalize_message(message, raw, run_id, "t")
    assert event is not None
    apply_normalized_event(store, event)
    store.close()
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "timeline",
            "--thread-id",
            "thr_cli",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "TURN_COMPLETED_OBSERVED status=failed" in out


@pytest.mark.parametrize("command", ["once", "serve"])
def test_scheduler_mutating_commands_are_rejected_at_parse_time(command: str) -> None:
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["scheduler", command])
    assert exc.value.code == 2


def test_scheduler_status_remains_read_only(tmp_path: Path, repo_root: Path, capsys) -> None:
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "scheduler",
            "status",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"leases", "open_wake_batches", "mailbox"}


def test_serve_semantic_state_is_profile_bound_and_external(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    external = tmp_path / "semantic.sqlite3"
    external_semantic = SemanticStore(external).initialize()
    external_semantic.close()
    resident = repo / "semantic.sqlite3"
    resident_semantic = SemanticStore(resident).initialize()
    resident_semantic.close()

    assert (
        _semantic_state_for_profile(
            repo,
            RuntimeProfile.MANAGED_MANUAL,
            str(external),
        )
        == external.resolve()
    )
    with pytest.raises(SystemExit, match="requires"):
        _semantic_state_for_profile(repo, RuntimeProfile.MAILBOX_MANUAL, None)
    with pytest.raises(SystemExit, match="forbids"):
        _semantic_state_for_profile(repo, RuntimeProfile.OBSERVER, str(external))
    with pytest.raises(SystemExit, match="existing regular file"):
        _semantic_state_for_profile(
            repo,
            RuntimeProfile.SINGLE_WAKE,
            str(tmp_path / "missing.sqlite3"),
        )
    with pytest.raises(SystemExit, match="must not live"):
        _semantic_state_for_profile(
            repo,
            RuntimeProfile.MANAGED_MANUAL,
            str(resident),
        )
