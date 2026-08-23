from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.cli import _parser, main
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin


def test_managed_list_and_show_remain_read_only(tmp_path: Path, repo_root: Path, capsys) -> None:
    seeded = seed_managed_actors(tmp_path)
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    from tools.codex_supervisor.store import ObserverStore

    observer = ObserverStore(runtime)
    bindings = BindingStore(observer, seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = bindings.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    observer.close()
    code = main(["--repo-root", str(repo_root), "--runtime-home", str(runtime), "managed", "list"])
    assert code == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["binding_id"] == binding_id
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "managed",
            "show",
            "--binding-id",
            binding_id,
        ]
    )
    assert code == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["binding_id"] == binding_id
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize(
    "command",
    ["create", "adopt", "verify", "activate", "turn", "suspend", "revoke"],
)
def test_managed_mutating_commands_are_rejected_at_parse_time(command: str) -> None:
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["managed", command])
    assert exc.value.code == 2
