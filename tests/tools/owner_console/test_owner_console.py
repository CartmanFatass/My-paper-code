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


def test_export_selected(tmp_path):
    import datetime as dt
    today = dt.date.today().isoformat()
    root = make_repo(tmp_path, today)
    srv.write_reply(root, "20260905-fsd-001", "b", "x")
    out = srv.export_selected(root, ["20260905-fsd-001"], "pro packet")
    assert out.name.endswith("_pro-packet.md")
    assert "(a) E2b ★" in out.read_text(encoding="utf-8")
