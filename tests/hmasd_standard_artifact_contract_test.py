from __future__ import annotations
import unittest

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md"
CM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md"
DIRECTION_ROOT = "docs/research/candidates/<direction-id>"

EM_ARTIFACT_PATHS = (
    f"{DIRECTION_ROOT}/evidence/<cycle-id>-scope-freeze.md",
    f"{DIRECTION_ROOT}/evidence/<cycle-id>-local-route-<route-id>.md",
    f"{DIRECTION_ROOT}/evidence/<cycle-id>-synthesis.md",
    f"{DIRECTION_ROOT}/external/<cycle-id>-innovator-prompt.md",
    f"{DIRECTION_ROOT}/external/<cycle-id>-convergence-prompt.md",
    f"{DIRECTION_ROOT}/external/<cycle-id>-convergence-disposition.md",
    f"{DIRECTION_ROOT}/evidence/<cycle-id>-terminal-gap.md",
    f"{DIRECTION_ROOT}/evidence/<cycle-id>-handoff.md",
    f"{DIRECTION_ROOT}/workflow/research/engineering-request.md",
)

CM_ARTIFACT_PATHS = (
    f"{DIRECTION_ROOT}/workflow/engineering/<cycle-id>-contract.md",
    "<cycle-id>-implementation.md",
    "<cycle-id>-review.md",
    "<cycle-id>-verification.md",
    "<cycle-id>-result.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_standard_artifacts_use_the_layered_direction_layout() -> None:
    em = _text(EM_SKILL)
    cm = _text(CM_SKILL)

    for directory in (
        f"{DIRECTION_ROOT}/evidence/",
        f"{DIRECTION_ROOT}/external/",
        f"{DIRECTION_ROOT}/workflow/research/",
    ):
        assert directory in em, directory
    assert f"{DIRECTION_ROOT}/workflow/engineering/" in cm

    for path in EM_ARTIFACT_PATHS:
        assert path in em, path
    for path in CM_ARTIFACT_PATHS:
        assert path in cm, path


def test_engineering_contract_has_a_durable_em_request_and_complete_fields() -> None:
    em = _text(EM_SKILL)
    cm = _text(CM_SKILL)
    request_path = f"{DIRECTION_ROOT}/workflow/research/engineering-request.md"
    contract_path = f"{DIRECTION_ROOT}/workflow/engineering/<cycle-id>-contract.md"

    assert request_path in em
    assert request_path in cm
    assert contract_path in cm
    for field in (
        "exact\nobservable",
        "expected alternatives",
        "baseline/config/data/RNG identities",
        "affected and owned paths",
        "protected semantics",
        "Effects",
        "resource bounds",
        "completion checks",
        "stop condition",
    ):
        assert field in cm, field


def test_artifacts_are_content_addressed_and_phase_conditioned() -> None:
    em = _text(EM_SKILL)
    cm = _text(CM_SKILL)

    assert "Use these standard direction-owned artifacts only when their phase is reached" in em
    assert "Create the remaining standard artifacts only when the cycle reaches their\nphase" in cm
    assert "Every durable ref is `{path, sha256}`" in em
    assert '`{"path": "<repo-relative-path>", "sha256": "<sha256>"}`' in cm
    assert "`state.json` is current CAS-managed workflow state, not an event log" in cm


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
