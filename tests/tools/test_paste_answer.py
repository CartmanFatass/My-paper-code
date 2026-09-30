import json
import runpy
from pathlib import Path

import pytest

MOD = Path(__file__).resolve().parents[2] / "tools" / "pro_transport" / "paste_answer.py"


def _load():
    return runpy.run_path(str(MOD), run_name="paste_answer")


def _notes(tmp_path, answer_body=""):
    notes = tmp_path / "NOTES.md"
    notes.write_text("# N\n\n## Pro question 2026-09-30 my-key\nQ\n\n### Answer\n" + answer_body +
                     "\n## Later entry\ntext\n", encoding="utf-8")
    return notes


def _operation(tmp_path, text="line one\n\nline two\n"):
    op = tmp_path / "op"
    op.mkdir()
    (op / "answer.txt").write_text(text, encoding="utf-8")
    import hashlib
    (op / "wait.json").write_text(json.dumps({"state": "COMPLETE", "kind": "chat answer",
                                              "answer_sha256": hashlib.sha256(text.encode()).hexdigest()}))
    return op


def test_paste_into_empty_answer_keeps_later_entries(tmp_path):
    m = _load()
    notes, op = _notes(tmp_path), _operation(tmp_path)
    assert m["main"](["--notes", str(notes), "--key", "my-key", "--operation", str(op)]) == 0
    out = notes.read_text(encoding="utf-8")
    assert "line one\n\nline two" in out
    assert out.index("### Answer") < out.index("line one") < out.index("## Later entry")
    assert "paste_answer.py" in out
    with pytest.raises(SystemExit, match="already holds"):
        m["main"](["--notes", str(notes), "--key", "my-key", "--operation", str(op)])


def test_refusals(tmp_path):
    m = _load()
    notes = _notes(tmp_path)
    with pytest.raises(SystemExit, match="need exactly 1"):
        m["main"](["--notes", str(notes), "--key", "other", "--operation", str(_operation(tmp_path)), "--check"])
    op2 = tmp_path / "op2"
    op2.mkdir()
    (op2 / "answer.txt").write_text("## a heading\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="headings"):
        m["main"](["--notes", str(notes), "--key", "my-key", "--operation", str(op2)])
    op3 = tmp_path / "op3"
    op3.mkdir()
    (op3 / "answer.txt").write_text("x\n", encoding="utf-8")
    (op3 / "wait.json").write_text(json.dumps({"answer_sha256": "0" * 64}))
    with pytest.raises(SystemExit, match="sha256"):
        m["main"](["--notes", str(notes), "--key", "my-key", "--operation", str(op3)])
    assert "### Answer\n\n## Later" in notes.read_text(encoding="utf-8")
