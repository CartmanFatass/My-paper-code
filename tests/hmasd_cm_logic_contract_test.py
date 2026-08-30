from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md"
CM_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-cm.md"
SHARED_AGENTS = REPO_ROOT / ".omp" / "AGENTS.md"
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


def test_cm_contract_gate_precedes_effects_and_uses_shared_carrier() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "Before any source, state, or note write; specialist assignment; "
            "external consultation; or result launch",
            "observable acceptance and competing expected outcomes",
            "explicit non-goals",
            "protected scientific, numerical, RNG, checkpoint, bit-identity",
            "authority references, exact Git baseline, owned paths, and interface boundaries",
            "baseline, config, data, and RNG identities",
            "authorized filesystem, process, network, provider, result, and Git Effects",
            "completion checks and the stop condition",
            "missing, contradictory, technically impossible, or outside supplied authority",
            "common v2 `BLOCKED` conflict",
            "Never narrow acceptance or change a comparator, metric, seed, data, stop rule",
        ),
    )

    shared = _text(SHARED_AGENTS)
    _assert_all(
        shared,
        (
            "Every cross-role dispatch uses an OMP `task` or Hub carrier with identity, "
            "generation, and assignment fields",
            "objective/decision relevance",
            "authorities, inputs, and evidence boundary",
            "scope, protected non-goals, and preserved semantics",
            "authorized Effects",
            "acceptance/stop",
            "return route, durable references, and reentry",
            "Results use the common v2 result envelope and role payload",
        ),
    )
    _assert_all(
        shared,
        (
            "common v2 result carrier requires `next_actions` as an array",
            "has no singular `next_action` alias",
            "`action_id`, `kind`, `owner` (including `CLERK`), `input_refs`, strict `dependencies`",
            "`authorized_effect_ref`, and `stop_or_reentry_ref`",
        ),
    )


def test_cm_uses_gap_driven_dual_disjoint_writers_and_one_boundary_owner() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "One vertically complete Implementer normally owns the bounded slice's code",
            "Use `hmasd-project-scout` or `hmasd-code-scout` only when the requested",
            "Never put a separate Scout in front of an Implementer for the same slice",
            "Writer cardinality follows those gaps, not a fixed staffing count or wave",
            "use `hmasd-implementer` when probability, gradients, native execution",
            "use `hmasd-implementer-terra` only for genuinely behavior-preserving local work",
            "CM may dispatch concurrent implementers only after freezing shared interfaces",
            "both their path ownership and their semantic/interface ownership are disjoint",
            "Different files are insufficient when they jointly implement or mutate one live protocol",
            "exactly one writer owns every overlapping boundary",
            "stop the affected assignment rather than broadening it",
            "no second writer may reinterpret or repair another writer's live boundary",
            "Refuse dirty or stale worktrees, conflicts, out-of-scope paths",
            "duplicate writers or command owners",
            "missing required symbol-refactor evidence",
        ),
    )

    assert "Select exactly one appropriate implementer for a nontrivial change" not in skill

    cm_agent = _text(CM_AGENT)
    _assert_all(
        cm_agent,
        (
            "Writer cardinality follows genuinely disjoint unresolved technical gaps",
            "Default to one vertically complete Implementer",
            "Do not create a scout-to-implementer-to-reviewer chain",
            "Concurrent Implementers are allowed only when both their path ownership and their semantic/interface ownership are disjoint",
            "assigns exactly one writer to every overlapping boundary",
            "Require native LSP evidence for exported-symbol work",
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
            "Return a common v2 result envelope as `hmasd-implementer-terra`",
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
            "Reserve `hmasd-reviewer` for a genuinely high-risk delta",
            "protected scientific, numerical, RNG, checkpoint, bit-identity, concurrency, "
            "resource-critical, or external-effect semantics",
            "Never invoke Reviewer for a simple reversible change",
            "Reviewer is neither approval nor a required generic step",
            "Add an independent `hmasd-verifier` only when one exact runtime, equivalence, "
            "or environment fact can change technical acceptance",
            "Exactly one Experiment Operator owns that one command",
            "CM, Reviewer, and Verifier never duplicate or share command ownership",
        ),
    )

    shared = _text(SHARED_AGENTS)
    _assert_all(
        shared,
        (
            "missing reviewer, test, Dashboard, or Advisor output is an evidence gap",
            "not a permission failure",
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
    assert {
        "semantic_product_ref",
        "persistence_status",
        "durable_state_ref",
        "candidate_sha",
        "integrated_sha",
    } <= set(cm_payload["required"])
    assert "PREPARED" in cm_payload["properties"]["persistence_status"]["enum"]
    for field, values in (
        ("engineering_status", ENGINEERING_STATUSES),
        ("observation_status", OBSERVATION_STATUSES),
        ("verification_status", VERIFICATION_STATUSES),
    ):
        assert set(cm_payload["properties"][field]["enum"]) == values



def test_cm_semantic_product_is_split_from_clerk_persistence_and_exact_handoffs() -> None:
    skill = _text(CM_SKILL)
    agent = _text(CM_AGENT)

    _assert_all(
        skill,
        (
            "exact accepted same-direction EM `integrated_sha` as the `omp/workflow` base",
            "A semantic-only EM result, packet presence, job settlement, or later target SHA "
            "cannot satisfy this edge",
            "Return the semantic product promptly with `semantic_product_ref` and "
            "`persistence_status=PREPARED`",
            "leave unobserved durable, `candidate_sha`, and `integrated_sha` fields null",
            "each mechanical obligation as an independent `next_actions` item with "
            "`owner: CLERK`",
            "CM performs no target Git, staging, commit, apply, fetch, or push",
            "Terminal handoff ends CM's physical writer lease",
            "CM resumes writing only after every Clerk mutation is terminal",
            "Root issues a new assignment",
            "Clerk refusal, stale CAS, conflict, or `UNKNOWN` blocks only the exact "
            "mechanical edge",
            "preserves CM's accepted technical semantic product",
            "Every CM-to-EM result-interpretation dispatch has a strict dependency",
            "new assignment ID in the same generation",
            "material scope change increments generation",
        ),
    )
    _assert_all(
        agent,
        (
            "`semantic_product_ref` and `persistence_status=PREPARED`",
            "emit every independent Clerk/Transport/Run/Root obligation simultaneously",
            "CM performs no target Git",
            "CM-to-EM result interpretation remains blocked on the exact accepted CM "
            "`integrated_sha`",
        ),
    )

def test_cm_disclaims_science_lifecycle_and_success_inference() -> None:
    skill = _text(CM_SKILL)
    _assert_all(
        skill,
        (
            "without making scientific, direction-lifecycle, Portfolio-allocation, "
            "or investment judgments",
            "Implementation, test, provider, transport, or command success is not "
            "scientific acceptance",
            "EM alone interprets scientific meaning",
            "Never reinterpret a scientific claim, infer a Portfolio or lifecycle action",
            "provider, transport, test, or command output as scientific authority",
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
