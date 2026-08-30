from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md"
CM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md"
DIRECTION_ROOT = "docs/research/candidates/<direction-id>"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.lower().split())


def test_artifacts_are_material_records_not_a_default_document_bundle() -> None:
    em = _compact(_text(EM_SKILL))
    cm = _compact(_text(CM_SKILL))

    assert "artifacts only at material milestones" in em
    assert "no fixed document bundle" in em
    assert "separate local-route file is optional" in em
    assert "never a default document tax" in em
    assert "write a terminal-gap note only when needed" in em

    assert "no mandatory engineering document suite" in cm
    assert "only at a material milestone" in cm
    assert (
        "losing material scope, observation, limitations, or reentry information "
        "would cause costly repetition"
    ) in cm
    assert "do not create a note merely because a phase was reached" in cm


def test_durable_records_are_content_addressed_and_state_remains_current() -> None:
    em = _compact(_text(EM_SKILL))
    cm = _compact(_text(CM_SKILL))

    assert "every durable ref is `{path, sha256}`" in em
    assert "content-address every note that is referenced" in cm
    assert "state is the latest accepted milestone, not an event log" in cm
    assert "preserve bytes on cas conflict" in cm


def test_engineering_request_is_the_durable_scope_reference_without_note_tax() -> None:
    em = _compact(_text(EM_SKILL))
    cm = _compact(_text(CM_SKILL))
    request_path = f"{DIRECTION_ROOT}/workflow/research/engineering-request.md"

    assert request_path in em
    assert request_path in cm
    assert "write one meaning-complete direction-owned engineering request" in em
    assert "hash the request" in em
    assert "next_action.owner=cm" in em
    assert (
        "when no cm note is warranted, the exact durable em request that "
        "satisfied the gate remains the contract and scope reference"
    ) in cm


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del loader, tests, pattern
    return unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    )


if __name__ == "__main__":
    unittest.main()
