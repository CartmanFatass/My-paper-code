"""Owner console: item loading, reply writing, review rendering, ledger seeding, doc safety."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("owner_console_server", ROOT / "tools/owner_console/server.py")
srv = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = srv
SPEC.loader.exec_module(srv)

LEDGER = """# Unattended research decision audit — 2026-09-04

| time | direction | tier | options | chosen option | reversible | provenance label | evidence path | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02:45 PDT | `flexible_skill_duration` | object | (a) E2b transfer of `c=0.25` to UAV scenario 1; (b) E3 heterogeneous-hazard discriminator | (b) E3 | yes | `OWNER_DELEGATED` | `docs/research/candidates/flexible_skill_duration/FSD_E2_INTAKE.md` | |
| 03:00 PDT | `ucope` | object | accept valid complete TW-B; quarantine for missing RSS \\| exit code; rerun for execution fields | accept valid complete TW-B | yes | `OWNER_DELEGATED` | `docs/research/candidates/ucope/UCOPE_INTAKE.md#decision-1` | |
"""


def make_repo(tmp_path: Path, today: str) -> Path:
    root = tmp_path / "repo"
    (root / "docs/research/portfolio/audit").mkdir(parents=True)
    (root / "docs/research/portfolio/audit/2026-09-04.md").write_text(LEDGER, encoding="utf-8")
    (root / "docs/research/portfolio/PORTFOLIO.md").write_text(
        "# P\n\nUpdated at: 2026-09-04T13:41:57Z\n\n| Direction | Lifecycle | Priority |\n| --- | --- | --- |\n| ucope | ACTIVE | HIGH |\n",
        encoding="utf-8")
    inbox = root / "docs/research/portfolio/owner/inbox" / today
    inbox.mkdir(parents=True)
    item = {"id": "20260905-fsd-001", "created": f"{today}T03:12:00Z", "direction": "flexible_skill_duration",
            "tier": "object", "kind": "decision", "title": "next rung after E3",
            "options": [{"key": "a", "label": "E2b"}, {"key": "b", "label": "E4"}],
            "recommended": "a", "auto_applied": "a", "evidence": ["docs/research/candidates/x/INTAKE.md"]}
    (inbox / "20260905-fsd-001.json").write_text(json.dumps(item), encoding="utf-8")
    return root


def test_parse_md_table_handles_escaped_pipes_and_separator():
    rows = srv.parse_md_table(LEDGER)
    assert len(rows) == 2
    assert rows[1]["options"].count("|") == 1
    assert rows[0]["chosen option"] == "(b) E3"


def test_load_items_and_reply_roundtrip(tmp_path):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    items = srv.load_items(root, days=7)
    assert [i["id"] for i in items] == ["20260905-fsd-001"]
    assert items[0]["status"] == "open"

    with pytest.raises(ValueError):
        srv.write_reply(root, "20260905-fsd-001", "z", "")
    paths = srv.write_reply(root, "20260905-fsd-001", "b", "先看 E4")
    assert (root / paths["reply"]).exists()
    review = (root / paths["review"]).read_text(encoding="utf-8")
    assert "**owner: (b) E4**" in review
    assert "supersede the delegated (a)" in review
    assert "comment: 先看 E4" in review
    assert srv.load_items(root, days=7)[0]["status"] == "answered"

    # agree leaves the delegated decision standing
    srv.write_reply(root, "20260905-fsd-001", "agree", "")
    review = (root / paths["review"]).read_text(encoding="utf-8")
    assert "delegated decision stands" in review


def test_seed_from_ledger_builds_auto_applied_items(tmp_path):
    root = make_repo(tmp_path, "2026-09-01")
    written = srv.seed_from_ledger(root, "2026-09-04")
    assert len(written) == 2
    fsd = json.loads(written[0].read_text(encoding="utf-8"))
    assert fsd["id"] == "20260904-fsd-001"
    assert [o["key"] for o in fsd["options"]] == ["a", "b"]
    assert fsd["auto_applied"] == "b" and fsd["recommended"] == "b"
    assert fsd["evidence"] == ["docs/research/candidates/flexible_skill_duration/FSD_E2_INTAKE.md"]
    uc = json.loads(written[1].read_text(encoding="utf-8"))
    assert uc["auto_applied"] == "a"
    assert "RSS | exit code" in uc["options"][1]["label"]
    # idempotent
    assert srv.seed_from_ledger(root, "2026-09-04") == []


def test_read_doc_refuses_escape_and_binary(tmp_path):
    root = make_repo(tmp_path, "2026-09-01")
    (tmp_path / "secret.md").write_text("no", encoding="utf-8")
    with pytest.raises(PermissionError):
        srv.read_doc(root, "../secret.md")
    (root / "x.bin").write_bytes(b"\x00")
    with pytest.raises(PermissionError):
        srv.read_doc(root, "x.bin")
    assert "Updated at" in srv.read_doc(root, "docs/research/portfolio/PORTFOLIO.md#L3")


def test_parse_portfolio(tmp_path):
    root = make_repo(tmp_path, "2026-09-01")
    p = srv.parse_portfolio(root)
    assert p["updated"] == "2026-09-04T13:41:57Z"
    assert p["rows"][0]["Direction"] == "ucope"


def test_new_item_validates_and_numbers_ids(tmp_path):
    root = make_repo(tmp_path, "2026-09-01")
    opts = [{"key": "a", "label": "x"}, {"key": "b", "label": "y"}]
    with pytest.raises(ValueError):
        srv.new_item(root, "ucope", "nonsense", "t", opts)
    with pytest.raises(ValueError):
        srv.new_item(root, "ucope", "decision", "t", opts, recommended="z")
    p1 = srv.new_item(root, "ucope", "decision", "first", opts, recommended="a", auto_applied="a", day="2026-09-06")
    p2 = srv.new_item(root, "ucope", "new-card", "second", opts, day="2026-09-06")
    assert p1.name == "20260906-ucope-001.json" and p2.name == "20260906-ucope-002.json"
    item = json.loads(p1.read_text(encoding="utf-8"))
    assert item["status"] == "open" and item["auto_applied"] == "a"


def test_pending_instructions_and_mark_answered(tmp_path):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    assert srv.pending_instructions(root) == []
    srv.write_reply(root, "20260905-fsd-001", "b", "reason")
    rows = srv.pending_instructions(root)
    assert len(rows) == 1 and rows[0]["choice"] == "b" and "supersede" in rows[0]["instruction"]
    srv.mark_answered(root, "20260905-fsd-001")
    assert srv.pending_instructions(root) == []


def test_item_priority_buckets():
    assert srv.item_priority({"kind": "portfolio"}) == 1
    assert srv.item_priority({"kind": "new-card"}) == 2
    assert srv.item_priority({"kind": "decision", "tier": "direction"}) == 2
    assert srv.item_priority({"kind": "decision", "tier": "object"}) == 3
    assert srv.item_priority({"kind": "decision", "ledger_kind": "technical"}) == 4
    assert srv.item_priority({"kind": "brief"}) == 4


def test_active_board_and_wave(tmp_path):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    (root / "docs/research/portfolio/PORTFOLIO.md").write_text(
        "# P\n\nUpdated at: 2026-09-04T13:41:57Z\n\n"
        "| Direction | Lifecycle | Priority | Updated at | Reason/condition |\n| --- | --- | --- | --- | --- |\n"
        "| flexible_skill_duration | ACTIVE | HIGH | 2026-09-04T12:07:40Z | E3 running |\n"
        "| orbit_shadow_read | PARKED | LOW | 2026-09-01T09:55:33Z | parked |\n\n"
        "## First investment wave\n\n1. `finite_resource_relational_inductive_efficiency`\n2. `flexible_skill_duration`\n\n### Execution snapshot\n",
        encoding="utf-8")
    assert srv.investment_wave(root)["flexible_skill_duration"] == 2
    b = srv.active_board(root)
    assert b["totals"] == {"directions": 2, "active": 1, "parked": 1, "open": 1, "answered_today": 0}
    fsd = b["rows"][0]
    assert fsd["direction"] == "flexible_skill_duration" and fsd["code"] == "fsd" and fsd["wave"] == 2 and fsd["open"] == 1
    assert b["rows"][1]["lifecycle"] == "PARKED"


def test_item_cli_add_and_reviews(tmp_path, capsys):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    spec = importlib.util.spec_from_file_location("owner_console_item", ROOT / "tools/owner_console/item.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    rc = cli.main(["--root", str(root), "add", "--direction", "ucope", "--kind", "new-card", "--title", "card X",
                   "--context", "claim; structure (b)", "--evidence", "docs/x/CARD.md"])
    assert rc == 0
    printed = capsys.readouterr().out.strip()
    item = json.loads((root / printed).read_text(encoding="utf-8"))
    assert [o["key"] for o in item["options"]] == ["accept", "reject", "revise"]
    assert cli.main(["--root", str(root), "add", "--direction", "ucope", "--kind", "decision", "--title", "t"]) == 2
    srv.write_reply(root, item["id"], "reject", "not MARL")
    assert cli.main(["--root", str(root), "reviews"]) == 0
    out = capsys.readouterr().out
    assert item["id"] in out and "do not launch" in out


def test_skill_names_every_kind_and_command():
    text = (ROOT / ".agents/skills/hmasd-owner-item/SKILL.md").read_text(encoding="utf-8")
    for kind in srv.KINDS:
        assert f"`{kind}`" in text, kind
    for cmd in ("item.py add", "item.py reviews", "item.py mark-answered"):
        assert cmd in text, cmd
    dm = (ROOT / ".codex/agents/hmasd-direction-manager.toml").read_text(encoding="utf-8")
    assert "$hmasd-owner-item" in dm and "item.py add" in dm and "item.py reviews" in dm


def test_export_selected(tmp_path):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    srv.write_reply(root, "20260905-fsd-001", "b", "x")
    out = srv.export_selected(root, ["20260905-fsd-001"], "pro packet")
    assert out.name.endswith("_pro-packet.md")
    assert "(a) E2b ★" in out.read_text(encoding="utf-8")
