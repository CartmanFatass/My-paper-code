import pytest

from tools import hmasd_pi_wait


@pytest.mark.parametrize("content,expected", [
    ("### Answer\n\n### Next question\nNot an answer\n", 1),
    ("### Answer\n\n## Next topic\nNot an answer\n", 1),
    ("Intro mentioning ### Answer\nNot an answer\n", 1),
    ("### Answer pending\nNot an answer\n", 1),
    ("### Answer\nA complete answer.\n### Next question\n", 0),
    ("### Answer\n#### Detail\nAn answer subsection.\n", 0),
])
def test_section_wait_respects_exact_heading_and_boundary(tmp_path, monkeypatch, content, expected):
    target = tmp_path / "NOTES.md"
    target.write_text(content)
    ticks = iter((0.0, 0.0, 2.0, 2.0))
    monkeypatch.setattr(hmasd_pi_wait.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(hmasd_pi_wait.time, "sleep", lambda _: None)
    assert hmasd_pi_wait.wait_section(str(target), "### Answer", timeout=1) == expected
