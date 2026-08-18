import json
import tempfile
from pathlib import Path

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.cli import main


def test_mailbox_list_show_and_operator_send(tmp_path: Path, repo_root: Path, capsys) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "mailbox",
            "send-operator",
            "--operator",
            "operator",
            "--target-actor-context-id",
            seeded["portfolio"].actor_context_id,
            "--subject-ref",
            "attn",
            "--payload-ref",
            "ref2",
        ]
    )
    assert code == 0
    sent = json.loads(capsys.readouterr().out)
    assert sent["message_kind"] == "OPERATOR_ATTENTION_REQUEST"
    code = main(["--repo-root", str(repo_root), "--runtime-home", str(runtime), "mailbox", "list"])
    assert code == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["message_id"] == sent["message_id"]
    code = main(
        [
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime),
            "mailbox",
            "show",
            "--message-id",
            sent["message_id"],
        ]
    )
    assert code == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["subject_ref"] == "attn"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
