"""The paired-negative checker must not lie about whether a guard went red.

`.claude/skills/hmasd-acceptance-gate/scripts/paired_negative.py` is the mechanism
this repository uses to prove that every new assertion can fail. Nothing tested the
mechanism itself until now, which is the same shape of gap it exists to close: a
guard nobody has watched failing.

THE DEFECT THAT PROMPTED THIS, measured 2026-07-30. The tool classified a run by
`line.startswith("FAILED")` over pytest's output. This environment sets
`FORCE_COLOR=3`, and pytest honours it even when its output is captured, so the
summary lines arrive as `ESC[31mFAILED tests/...` and never match. A mutation that
genuinely reddened a guard was reported as:

    PAIRED NEGATIVE FAILED -- the suite stayed GREEN under this mutation.

**That is the most damaging direction for this particular tool to fail in.** It
tells the operator a working guard is broken, which invites "repairing" correct
code, and it teaches distrust of the one checker that makes the discipline real.

The fix is belt and braces -- the subprocess is told not to colour AND its output
is stripped before parsing -- so these tests exercise both halves.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "hmasd-acceptance-gate" / "scripts" / "paired_negative.py"


def _load():
    spec = importlib.util.spec_from_file_location("_paired_negative", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = _load()


def test_the_script_is_where_the_skill_says_it_is() -> None:
    assert SCRIPT.is_file(), (
        "the acceptance gate names this path; a missing script makes every "
        "'paired negative watched failing' claim unverifiable")


def test_ansi_is_stripped_before_classification() -> None:
    """The unit of the defect."""

    coloured = "\x1b[31m\x1b[1mFAILED tests/x_test.py::test_y\x1b[0m"
    assert TOOL._strip_ansi(coloured) == "FAILED tests/x_test.py::test_y"
    assert TOOL._strip_ansi(coloured).startswith("FAILED")


def test_plain_output_is_untouched() -> None:
    """Stripping must not corrupt the uncoloured case that used to work."""

    plain = "FAILED tests/x_test.py::test_y\n1 failed, 3 passed in 0.10s"
    assert TOOL._strip_ansi(plain) == plain


def test_the_source_contains_no_literal_escape_bytes() -> None:
    """A literal ESC byte in a control-plane script survives copy/paste badly and
    is invisible in review. The pattern is built from `chr(27)` instead."""

    assert b"\x1b" not in SCRIPT.read_bytes()


def test_it_reports_a_reddened_guard_as_PASSED_even_under_FORCE_COLOR(tmp_path) -> None:
    """END TO END, and this is the test that would have caught the defect.

    A real mutation, a real pytest run, with FORCE_COLOR set exactly as this
    environment sets it. Before the fix this printed 'the suite stayed GREEN'.
    """

    target = tmp_path / "subject.py"
    target.write_text("def guarded():\n    return True\n", encoding="utf-8")
    suite = tmp_path / "subject_test.py"
    suite.write_text(textwrap.dedent(f"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("subject", r"{target}")
        subject = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(subject)

        def test_guard():
            assert subject.guarded() is True
    """), encoding="utf-8")

    env = dict(os.environ)
    env["FORCE_COLOR"] = "3"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--file", str(target),
         "--old", "    return True",
         "--new", "    return False",
         "--test", str(suite),
         "--basetemp", str(tmp_path / "pt")],
        capture_output=True, text=True, env=env, cwd=str(ROOT))
    combined = proc.stdout + proc.stderr

    assert "PAIRED NEGATIVE PASSED" in combined, (
        f"a genuinely reddened guard was not recognised under FORCE_COLOR:\n{combined}")
    assert "stayed GREEN" not in combined
    assert proc.returncode == 0

    # and the subject must be restored byte-identically
    assert target.read_text(encoding="utf-8") == "def guarded():\n    return True\n"


def test_it_still_reports_a_guard_that_cannot_fail(tmp_path) -> None:
    """The other direction must keep working: a mutation that changes nothing the
    suite looks at is a real defect in the guard and must be reported as such."""

    target = tmp_path / "subject.py"
    target.write_text("UNUSED = 1\n\n\ndef guarded():\n    return True\n", encoding="utf-8")
    suite = tmp_path / "subject_test.py"
    suite.write_text(textwrap.dedent(f"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("subject2", r"{target}")
        subject = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(subject)

        def test_guard():
            assert subject.guarded() is True
    """), encoding="utf-8")

    env = dict(os.environ)
    env["FORCE_COLOR"] = "3"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--file", str(target),
         "--old", "UNUSED = 1",
         "--new", "UNUSED = 2",
         "--test", str(suite),
         "--basetemp", str(tmp_path / "pt")],
        capture_output=True, text=True, env=env, cwd=str(ROOT))
    combined = proc.stdout + proc.stderr

    assert "PAIRED NEGATIVE FAILED" in combined, (
        f"a guard that cannot detect its mutation must be reported:\n{combined}")
    assert proc.returncode == 1
