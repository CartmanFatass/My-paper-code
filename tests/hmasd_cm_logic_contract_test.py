from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md"
RESULT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-result-run" / "SKILL.md"
TERRA_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-implementer-terra.md"
ENGINEERING_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_engineering_state.schema.json"
RESULT_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json"

ENGINEERING_STATUSES = {
    "IN_PROGRESS",
    "IMPLEMENTED",
    "UNCHANGED",
    "BLOCKED",
    "NOT_REACHED",
}
OBSERVATION_STATUSES = {
    "IN_PROGRESS",
    "OBSERVED",
    "NOT_OBSERVED",
    "NOT_REQUIRED",
}
VERIFICATION_STATUSES = {
    "IN_PROGRESS",
    "SATISFIED",
    "UNSATISFIED",
    "NOT_RUN",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(_text(path))


def _assert_all(text: str, fragments: tuple[str, ...]) -> None:
    normalized = " ".join(text.split())
    for fragment in fragments:
        assert " ".join(fragment.split()) in normalized, fragment


def test_cm_contract_gate_precedes_every_effectful_boundary() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "Before **any** source/state/artifact write, leaf assignment",
            "Root-mediated\nBrowserTransport request, or result launch",
            "observable acceptance and its expected alternatives",
            "explicit non-goals",
            "protected semantics and invariants",
            "authority references and exact Git baseline",
            "assignment-owned paths and interface boundaries",
            "resource bounds",
            "committed filesystem, process, network, provider, result, and Git Effects",
            "missing, contradictory, technically impossible",
            "returns a common\nv1 `BLOCKED` conflict result before writing or launching anything",
        ),
    )
    _assert_all(
        skill,
        (
            "`Goal`",
            "`Non-goals`",
            "`Owned paths`",
            "`Effects`",
            "`Acceptance`",
            "`Refs`",
            "`Resources and stop condition`",
            "`Return identity`",
            "common v1 result envelope",
        ),
    )


def test_cm_uses_specialized_scouts_and_one_overlapping_implementer_owner() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "trustworthy current map",
            "`hmasd-project-scout` for repository layout, build and test surfaces",
            "`hmasd-code-scout` for code, callers, interfaces, state ownership",
            "Assign exactly one implementer owner to each nontrivial edit boundary",
            "paths, symbols, or runtime semantics overlap",
            "Use `hmasd-implementer` for semantic or protected changes",
            "Use `hmasd-implementer-terra` only for routine, behavior-preserving work",
            "native LSP references before exported-symbol modification",
            "native LSP rename for every\ncross-file rename",
        ),
    )

    terra = _text(TERRA_AGENT)
    _assert_all(
        terra,
        (
            "OMP routine behavior-preserving implementation worker",
            "stop before modifying it and return the exact boundary to CM",
            "replacement by `hmasd-implementer`",
            "Run only focused non-result checks",
            "Never launch a result-bearing\ncommand",
            "Return a common v1 result envelope as `hmasd-implementer-terra`",
            "Do not\ncommit or push",
        ),
    )


def test_cm_preserves_the_complete_production_chain() -> None:
    skill = _text(CM_SKILL)
    for item in (
        "loader/cache",
        "native batching",
        "bounded workers/threads",
        "rollout packing",
        "recurrent state",
        "optimizer",
        "serialization",
        "checkpoint/resume",
        "evaluation",
        "rollback",
        "observability",
    ):
        assert item in skill, item
    _assert_all(
        skill,
        (
            "ordering, pairing, counts, endpoints, dtype,\nRNG, and resume equivalence",
            "serial or unbounded scaffold is not a production\nreplacement",
        ),
    )


def test_high_risk_evidence_roles_have_narrow_non_authoritative_jobs() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "Attempt `hmasd-reviewer`",
            "shared core",
            "scientific, numerical, RNG, checkpoint, bit-identity, external-effect",
            "concurrency, or resource-critical semantics",
            "Reviewer unavailability is\n  an explicit evidence gap, not approval or a policy veto",
            "Use `hmasd-verifier` only when one exact independent\n  runtime/equivalence/environment fact",
            "Exactly one Experiment\n  Operator owns exactly one frozen result-bearing command",
            "CM, Reviewer, and Verifier never share or duplicate\n  that command ownership",
        ),
    )

    result_skill = _text(RESULT_SKILL)
    _assert_all(
        result_skill,
        (
            "shell-free exact argv and canonical cwd",
            "config, data, RNG, parameter, and environment\n  identities",
            "duration, peak-memory, worker/thread/device",
            "scientific activity predicate, completion checks, and stop condition",
            "Exactly one Experiment Operator owns exactly\none command",
            "one `scripts/hmasd_run.py execute` process",
            "one immutable\n   `scripts/hmasd_operator_result.py` witness",
            "terminal `SUCCEEDED` mean only that the frozen command\n  completed as observed",
        ),
    )


def test_cm_status_axes_are_distinct_in_skill_and_schemas() -> None:
    skill = _text(CM_SKILL)
    for field, values in (
        ("engineering_status", ENGINEERING_STATUSES),
        ("observation_status", OBSERVATION_STATUSES),
        ("verification_status", VERIFICATION_STATUSES),
    ):
        assert f"`{field}`" in skill
        for value in values:
            assert value in skill

    engineering = _schema(ENGINEERING_SCHEMA)
    engineering_properties = engineering["properties"]
    assert "contract_ref" in engineering_properties
    assert "contract_ref" not in engineering["required"]
    for field, values in (
        ("engineering_status", ENGINEERING_STATUSES),
        ("observation_status", OBSERVATION_STATUSES),
        ("verification_status", VERIFICATION_STATUSES),
    ):
        assert set(engineering_properties[field]["enum"]) == values
        assert field not in engineering["required"]

    result = _schema(RESULT_SCHEMA)
    cm_payload = result["$defs"]["cm_payload"]
    assert {
        "contract_ref",
        "engineering_status",
        "observation_status",
        "verification_status",
    } <= set(cm_payload["required"])
    for field, values in (
        ("engineering_status", ENGINEERING_STATUSES),
        ("observation_status", OBSERVATION_STATUSES),
        ("verification_status", VERIFICATION_STATUSES),
    ):
        assert set(cm_payload["properties"][field]["enum"]) == values


def test_cm_disclaims_science_lifecycle_and_success_inference() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "CM never decides scientific acceptance, direction\nlifecycle, Portfolio allocation",
            "Implementation, test, command, or BrowserTransport success is not\nscientific acceptance",
            "EM alone interprets\nscientific meaning",
            "Never reinterpret a scientific claim, infer a lifecycle action",
        ),
    )


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
