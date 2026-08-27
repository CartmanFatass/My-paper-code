from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import hmasd_protocol_contracts as contracts


ROOT = Path(__file__).resolve().parents[1]
BASE = "1" * 40


def _base_action(**overrides: object) -> dict:
    values = {
        "decision_owner": "Root",
        "base_sha": BASE,
        "paths": ["scripts/a.py", "tests/a_test.py"],
        "objective": "Change the exact shared implementation.",
        "non_goals": ["Change numerical semantics", "Change RNG semantics"],
        "allowed_effects": ["commit", "modify"],
    }
    values.update(overrides)
    return contracts.build_shared_core_action_record(**values)


def test_public_contract_is_only_the_shared_core_fence_seam() -> None:
    assert contracts.__all__ == [
        "FENCE_INFO",
        "ProtocolContractError",
        "build_shared_core_action_record",
        "parse_shared_core_action_records",
        "render_shared_core_action_record",
        "validate_shared_core_action_record",
    ]


def test_legacy_work_packet_and_worktree_modules_are_absent() -> None:
    for relative in ("scripts/hmasd_work_packet.py", "scripts/hmasd_worktree.py"):
        assert not (ROOT / relative).exists(), relative


def test_shared_core_record_round_trip_and_exact_binding() -> None:
    record = _base_action(
        paths=["tests/a_test.py", "scripts/a.py"],
        non_goals=["Change RNG semantics", "Change numerical semantics"],
        allowed_effects=["modify", "commit"],
    )
    assert record["paths"] == ["scripts/a.py", "tests/a_test.py"]
    assert record["non_goals"] == ["Change RNG semantics", "Change numerical semantics"]
    assert record["allowed_effects"] == ["commit", "modify"]

    markdown = "# Authority\n\n" + contracts.render_shared_core_action_record(record)
    selected = contracts.validate_shared_core_action_record(
        markdown,
        action_digest=record["action_digest"],
        decision_owner="Root",
        current_base_sha=BASE,
        owned_paths=["tests/a_test.py", "scripts/a.py"],
        objective=record["objective"],
        non_goals=list(reversed(record["non_goals"])),
        allowed_effects=list(reversed(record["allowed_effects"])),
    )
    assert selected == record


@pytest.mark.parametrize(
    "markdown",
    [
        "<!--\n{record}\n-->",
        "````markdown\nExample only:\n{record}\n````",
    ],
    ids=["html-comment", "outer-four-backtick-fence"],
)
def test_shared_core_record_ignores_non_authoritative_markdown_contexts(markdown: str) -> None:
    rendered = contracts.render_shared_core_action_record(_base_action())
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_RECORD_NOT_FOUND"):
        contracts.parse_shared_core_action_records(markdown.format(record=rendered))


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("decision_owner", "Portfolio"),
        ("current_base_sha", "2" * 40),
        ("owned_paths", ["scripts/b.py"]),
        ("objective", "Different objective"),
        ("non_goals", ["Different non-goal"]),
        ("allowed_effects", ["push"]),
    ],
)
def test_shared_core_record_rejects_every_bound_field_drift(
    field: str, replacement: object
) -> None:
    record = _base_action()
    kwargs = {
        "action_digest": record["action_digest"],
        "decision_owner": record["decision_owner"],
        "current_base_sha": record["base_sha"],
        "owned_paths": record["paths"],
        "objective": record["objective"],
        "non_goals": record["non_goals"],
        "allowed_effects": record["allowed_effects"],
    }
    kwargs[field] = replacement
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_FIELD_MISMATCH"):
        contracts.validate_shared_core_action_record(
            contracts.render_shared_core_action_record(record), **kwargs
        )


@pytest.mark.parametrize(
    "path",
    [
        "/absolute.py",
        "C:/absolute.py",
        "scripts\\a.py",
        "scripts//a.py",
        "./scripts/a.py",
        "scripts/../a.py",
        "scripts/a.py:stream",
        "scripts/a.py.",
        "scripts/a.py ",
    ],
)
def test_shared_core_paths_reject_noncanonical_or_windows_ambiguous_spellings(
    path: str,
) -> None:
    with pytest.raises(contracts.ProtocolContractError, match="INVALID_PATH"):
        _base_action(paths=[path])


def test_shared_core_record_rejects_ambiguous_invalid_or_noncanonical_fences() -> None:
    record = _base_action()
    fence = contracts.render_shared_core_action_record(record)
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_RECORD_NOT_UNIQUE"):
        contracts.validate_shared_core_action_record(
            fence + "\n" + fence,
            action_digest=record["action_digest"],
            decision_owner="Root",
            current_base_sha=BASE,
            owned_paths=record["paths"],
            objective=record["objective"],
            non_goals=record["non_goals"],
            allowed_effects=record["allowed_effects"],
        )

    for markdown, code in [
        ("```hmasd-shared-core-action-v1\n{bad json}\n```", "INVALID_SHARED_CORE_JSON"),
        ("# no record", "SHARED_CORE_RECORD_NOT_FOUND"),
    ]:
        with pytest.raises(contracts.ProtocolContractError, match=code):
            contracts.parse_shared_core_action_records(markdown)

    bad_digest = dict(record, action_digest="f" * 64)
    with pytest.raises(contracts.ProtocolContractError, match="ACTION_DIGEST_MISMATCH"):
        contracts.render_shared_core_action_record(bad_digest)
    with pytest.raises(contracts.ProtocolContractError, match="PATH_SCOPE_OVERLAP"):
        _base_action(paths=["scripts", "scripts/a.py"])

    unsorted = dict(record, paths=list(reversed(record["paths"])))
    unsigned = {key: value for key, value in unsorted.items() if key != "action_digest"}
    unsorted["action_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_PATHS_NOT_SORTED"):
        contracts.render_shared_core_action_record(unsorted)
