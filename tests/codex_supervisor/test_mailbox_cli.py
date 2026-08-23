import json
import tempfile
from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.cli import _parser, main
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem


def test_mailbox_list_and_show_remain_read_only(tmp_path: Path, repo_root: Path, capsys) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    from tools.codex_supervisor.mailbox_store import MailboxStore
    from tools.codex_supervisor.store import ObserverStore

    observer = ObserverStore(runtime)
    sent = MailboxStore(observer).enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="fixture:read-only-cli",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="attn",
        payload_ref="ref2",
        priority=20,
    )
    observer.close()
    code = main(["--repo-root", str(repo_root), "--runtime-home", str(runtime), "mailbox", "list"])
    assert code == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["message_id"] == sent.message_id
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "mailbox",
            "show",
            "--message-id",
            sent.message_id,
        ]
    )
    assert code == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["subject_ref"] == "attn"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("command", ["send-operator", "dead-letter"])
def test_mailbox_mutating_commands_are_rejected_at_parse_time(command: str) -> None:
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["mailbox", command])
    assert exc.value.code == 2
