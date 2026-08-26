from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import hmasd_protocol_contracts as contracts
from scripts import hmasd_state


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "tests" / "fixtures" / "hmasd_phase0"
EXTERNAL = ROOT / "tests" / "fixtures" / "hmasd_external_review"
SHA = "a" * 64
BASE = "1" * 40


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(root: Path, relative: str, value: dict) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding="utf-8")


def test_work_packet_cli_supports_script_and_module_import_modes() -> None:
    """The protocol-contract import must not make direct CLI execution fail."""
    for command in (
        [sys.executable, "scripts/hmasd_work_packet.py", "--help"],
        [sys.executable, "-m", "scripts.hmasd_work_packet", "--help"],
    ):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout.lower()


def test_observe_run_manifest_validates_identity_and_maps_states(tmp_path: Path) -> None:
    manifest = _load(PHASE0 / "run_manifest.json")
    relative = "temp/directions/example-direction/exp/example-run/manifest.json"
    ref = {
        "kind": "run_manifest",
        "path": relative,
        "resource_id": "example-direction/example-run",
    }
    for source, expected in {
        "PREPARED": "IN_PROGRESS",
        "RUNNING": "IN_PROGRESS",
        "SUCCEEDED": "SUCCEEDED",
        "FAILED": "FAILED",
        "CANCELLED": "FAILED",
        "UNKNOWN": "UNKNOWN",
    }.items():
        current = copy.deepcopy(manifest)
        current["status"] = source
        _write(tmp_path, relative, current)
        observed = contracts.observe_effect_ref(tmp_path, ref)
        assert observed == contracts.EffectObservation(
            kind="run_manifest",
            resource_id="example-direction/example-run",
            state=expected,
            path=relative,
        )

    with pytest.raises(contracts.ProtocolContractError, match="EFFECT_IDENTITY_MISMATCH"):
        contracts.observe_effect_ref(tmp_path, {**ref, "resource_id": "example-direction/other"})

    invalid = copy.deepcopy(manifest)
    invalid["unexpected"] = True
    _write(tmp_path, relative, invalid)
    with pytest.raises(contracts.ProtocolContractError, match="INVALID_EFFECT_DOCUMENT"):
        contracts.observe_effect_ref(tmp_path, ref)


def test_typed_effect_operation_is_kind_closed_and_observation_only(tmp_path: Path) -> None:
    manifest = _load(PHASE0 / "run_manifest.json")
    relative = "temp/directions/example-direction/exp/example-run/manifest.json"
    _write(tmp_path, relative, manifest)
    original = {
        "kind": "run_manifest",
        "path": relative,
        "resource_id": "example-direction/example-run",
        "operation": "EXECUTE",
    }
    unchanged = copy.deepcopy(original)
    observed = contracts.observe_effect_ref(tmp_path, original)
    assert observed.operation == "EXECUTE"
    assert observed.resource_id == original["resource_id"]
    assert original == unchanged

    with pytest.raises(contracts.ProtocolContractError, match="INVALID_EFFECT_OPERATION"):
        contracts.observe_effect_ref(tmp_path, {**original, "operation": "SEND"})


def test_old_typed_effect_shape_defaults_to_observe_without_rewriting(tmp_path: Path) -> None:
    manifest = _load(PHASE0 / "run_manifest.json")
    relative = "temp/directions/example-direction/exp/example-run/manifest.json"
    _write(tmp_path, relative, manifest)
    old_shape = {
        "kind": "run_manifest",
        "path": relative,
        "resource_id": "example-direction/example-run",
    }
    unchanged = copy.deepcopy(old_shape)
    observed = contracts.observe_effect_ref(tmp_path, old_shape)
    assert observed.operation == "OBSERVE"
    assert observed.resource_id == "example-direction/example-run"
    assert old_shape == unchanged


def test_observe_worktree_requires_one_identity_and_maps_only_known_states(tmp_path: Path) -> None:
    runtime = _load(PHASE0 / "runtime_worktrees.json")
    relative = ".codex/runtime/worktrees.json"
    ref = {
        "kind": "worktree",
        "path": relative,
        "resource_id": "example-direction/run-example",
    }
    for lifecycle, expected in {
        "PROVISIONING": "IN_PROGRESS",
        "PROVISIONED": "IN_PROGRESS",
        "CANDIDATE_READY": "IN_PROGRESS",
        "PREPARED_FOR_INTEGRATION": "IN_PROGRESS",
        "RETAINED_FOR_RECOVERY": "FAILED",
        "INTEGRATED": "SUCCEEDED",
        "RELEASED": "SUCCEEDED",
        "APPLY_OUTCOME_UNKNOWN": "UNKNOWN",
        "RELEASE_OUTCOME_UNKNOWN": "UNKNOWN",
    }.items():
        current = copy.deepcopy(runtime)
        row = current["worktrees"][0]
        row["lifecycle"] = lifecycle
        if lifecycle == "PROVISIONING":
            row["operation_token"] = "operation-1"
        if lifecycle.endswith("OUTCOME_UNKNOWN"):
            row["unknown_outcome"] = {
                "operation": "APPLY" if lifecycle.startswith("APPLY") else "RELEASE",
                "status": "UNKNOWN",
                "recorded_at": "2026-08-24T00:00:00Z",
                "error": "outcome unavailable",
                "registry_revision_before": 1,
                "registry_revision_observed": 1,
                "observation": {
                    "target_sha": None,
                    "worktree_exists": True,
                    "registration_count": 1,
                    "registration_branch": "refs/heads/" + row["branch"],
                    "registration_head": row["base_sha"],
                    "branch_sha": row["base_sha"],
                },
            }
        _write(tmp_path, relative, current)
        assert contracts.observe_effect_ref(tmp_path, ref).state == expected

    duplicate = copy.deepcopy(runtime)
    duplicate["worktrees"].append(copy.deepcopy(duplicate["worktrees"][0]))
    duplicate["worktrees"][1]["worktree_ref"] = "wt-other"
    duplicate["worktrees"][1]["canonical_absolute_path"] += "-other"
    _write(tmp_path, relative, duplicate)
    with pytest.raises(contracts.ProtocolContractError, match="EFFECT_IDENTITY_NOT_UNIQUE"):
        contracts.observe_effect_ref(tmp_path, ref)


def test_external_operation_validates_exact_operation_contract_and_unknown(tmp_path: Path) -> None:
    operation = _load(EXTERNAL / "operation_ref.json")
    relative = "temp/external/operation.json"
    ref = {
        "kind": "external_operation",
        "path": relative,
        "resource_id": operation["operation_id"],
    }
    _write(tmp_path, relative, operation)
    assert contracts.observe_effect_ref(tmp_path, ref).state == "COMMITTED"

    operation["commitment_state"] = "UNKNOWN"
    _write(tmp_path, relative, operation)
    assert contracts.observe_effect_ref(tmp_path, ref).state == "UNKNOWN"

    operation["commitment_state"] = "NATURAL_COMPLETION_VERIFIED"
    _write(tmp_path, relative, operation)
    with pytest.raises(contracts.ProtocolContractError, match="INVALID_EFFECT_DOCUMENT"):
        contracts.observe_effect_ref(tmp_path, ref)

    operation["commitment_state"] = "COMMITTED"
    operation["archive_path"] = "wrong/path.json"
    _write(tmp_path, relative, operation)
    with pytest.raises(contracts.ProtocolContractError, match="INVALID_EFFECT_DOCUMENT"):
        contracts.observe_effect_ref(tmp_path, ref)


def test_external_operation_uses_public_validator_wrapper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    operation = _load(EXTERNAL / "operation_ref.json")
    relative = "temp/external/public-wrapper.json"
    _write(tmp_path, relative, operation)
    calls: list[dict] = []

    def public_validator(value: dict) -> dict:
        calls.append(dict(value))
        return dict(value)

    def forbidden_private_call(value: dict) -> dict:
        raise AssertionError("contracts must not depend on the private validator")

    monkeypatch.setattr(
        contracts.hmasd_external_review, "validate_operation_ref", public_validator
    )
    monkeypatch.setattr(
        contracts.hmasd_external_review, "_validate_operation_ref", forbidden_private_call
    )
    observed = contracts.observe_effect_ref(
        tmp_path,
        {
            "kind": "external_operation",
            "path": relative,
            "resource_id": operation["operation_id"],
        },
    )
    assert observed.state == "COMMITTED"
    assert len(calls) == 1


def test_legacy_effect_ref_is_read_compatible_but_untyped(tmp_path: Path) -> None:
    ref = {"path": "temp/legacy-effect.json"}
    _write(tmp_path, ref["path"], {"status": "SUCCEEDED"})
    assert contracts.observe_effect_ref(tmp_path, ref) == contracts.EffectObservation(
        kind="legacy",
        resource_id="",
        state="LEGACY_UNTYPED",
        path=ref["path"],
    )
    with pytest.raises(contracts.ProtocolContractError, match="UNKNOWN_EFFECT_KIND"):
        contracts.observe_effect_ref(
            tmp_path,
            {"kind": "invented", "path": ref["path"], "resource_id": "x"},
        )


@pytest.mark.parametrize("alias", ["temp//effect.json", "./temp/effect.json"])
def test_effect_ref_rejects_noncanonical_raw_posix_aliases(alias: str) -> None:
    with pytest.raises(contracts.ProtocolContractError, match="INVALID_PATH"):
        contracts.observe_effect_ref(ROOT, {"path": alias})


def test_effect_document_rejects_in_repository_symlink_or_reparse(tmp_path: Path) -> None:
    manifest = _load(PHASE0 / "run_manifest.json")
    target = tmp_path / "actual.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    link = tmp_path / "linked.json"
    try:
        link.symlink_to(target.name)
    except OSError as exc:
        pytest.skip(f"host cannot create a test symlink/reparse point: {exc}")
    ref = {
        "kind": "run_manifest",
        "path": "linked.json",
        "resource_id": "example-direction/example-run",
    }
    with pytest.raises(contracts.ProtocolContractError, match="EFFECT_PATH_ALIAS"):
        contracts.observe_effect_ref(tmp_path, ref)


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


def test_shared_core_record_round_trip_and_exact_packet_binding() -> None:
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
    record = contracts.render_shared_core_action_record(_base_action())
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_RECORD_NOT_FOUND"):
        contracts.parse_shared_core_action_records(markdown.format(record=record))


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
def test_shared_core_record_rejects_every_bound_field_drift(field: str, replacement: object) -> None:
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


def test_shared_core_record_rejects_ambiguous_or_invalid_fences_and_paths() -> None:
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
        contracts.parse_shared_core_action_records(
            contracts.render_shared_core_action_record(bad_digest)
        )
    with pytest.raises(contracts.ProtocolContractError, match="PATH_SCOPE_OVERLAP"):
        _base_action(paths=["scripts", "scripts/a.py"])

    unsorted = dict(record, paths=list(reversed(record["paths"])))
    unsigned = {key: value for key, value in unsorted.items() if key != "action_digest"}
    unsorted["action_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    with pytest.raises(contracts.ProtocolContractError, match="SHARED_CORE_PATHS_NOT_SORTED"):
        contracts.parse_shared_core_action_records(
            contracts.render_shared_core_action_record(unsorted)
        )


def test_agent_result_file_refs_are_structured_but_operation_ids_remain_opaque() -> None:
    document = _load(PHASE0 / "agent_result.json")
    document["payload"]["conclusion_refs"] = ["opaque-file"]
    with pytest.raises(hmasd_state.ValidationError):
        hmasd_state.validate_document("agent_result", document)

    transport = _load(PHASE0 / "agent_result.json")
    transport.update(
        role="hmasd-external-pro-transport",
        logical_identity="hmasd-external-pro-transport",
        payload={
            "kind": "transport",
            "provider": "chatgpt",
            "mode": "DIVERGENT",
            "round_id": "a" * 20,
            "operation_ref": "opaque-operation-id",
            "archive_ref": {"path": "docs/archive.json", "sha256": SHA},
            "handoff_ref": None,
        },
    )
    hmasd_state.validate_document("agent_result", transport)
    transport["payload"]["archive_ref"] = "opaque-file"
    with pytest.raises(hmasd_state.ValidationError):
        hmasd_state.validate_document("agent_result", transport)


@pytest.mark.parametrize(
    ("definition", "payload", "field"),
    [
        (
            "portfolio_payload",
            {
                "kind": "portfolio",
                "direction_actions": [],
                "portfolio_ref": {"path": "docs/portfolio.md", "sha256": SHA},
                "registry_revision": 1,
            },
            "portfolio_ref",
        ),
        (
            "em_payload",
            {
                "kind": "em",
                "direction_id": "example-direction",
                "question_sha256": SHA,
                "evidence_set_sha256": SHA,
                "conclusion_refs": [{"path": "docs/conclusion.md", "sha256": SHA}],
                "engineering_request_ref": {"path": "docs/request.md", "sha256": SHA},
            },
            "engineering_request_ref",
        ),
        (
            "em_payload",
            {
                "kind": "em",
                "direction_id": "example-direction",
                "question_sha256": SHA,
                "evidence_set_sha256": SHA,
                "conclusion_refs": [{"path": "docs/conclusion.md", "sha256": SHA}],
                "engineering_request_ref": None,
            },
            "conclusion_refs",
        ),
        (
            "cm_payload",
            {
                "kind": "cm",
                "direction_id": "example-direction",
                "scope_ref": {"path": "docs/scope.md", "sha256": SHA},
                "base_sha": BASE,
                "candidate_sha": None,
                "verification_refs": [{"path": "docs/verify.json", "sha256": SHA}],
                "integrated_sha": None,
            },
            "scope_ref",
        ),
        (
            "cm_payload",
            {
                "kind": "cm",
                "direction_id": "example-direction",
                "scope_ref": {"path": "docs/scope.md", "sha256": SHA},
                "base_sha": BASE,
                "candidate_sha": None,
                "verification_refs": [{"path": "docs/verify.json", "sha256": SHA}],
                "integrated_sha": None,
            },
            "verification_refs",
        ),
        (
            "implementation_payload",
            {
                "kind": "implementation",
                "changed_paths": ["scripts/a.py"],
                "preserved_invariants": ["RNG"],
                "lsp_evidence_refs": [{"path": "temp/lsp.json", "sha256": SHA}],
            },
            "lsp_evidence_refs",
        ),
        (
            "review_payload",
            {
                "kind": "review",
                "findings": [],
                "evidence_refs": [{"path": "temp/review.json", "sha256": SHA}],
            },
            "evidence_refs",
        ),
        (
            "verification_payload",
            {
                "kind": "verification",
                "checks": ["pytest"],
                "behavioral_evidence_refs": [{"path": "temp/test.json", "sha256": SHA}],
                "benchmark_refs": [{"path": "temp/bench.json", "sha256": SHA}],
            },
            "benchmark_refs",
        ),
        (
            "verification_payload",
            {
                "kind": "verification",
                "checks": ["pytest"],
                "behavioral_evidence_refs": [{"path": "temp/test.json", "sha256": SHA}],
                "benchmark_refs": [{"path": "temp/bench.json", "sha256": SHA}],
            },
            "behavioral_evidence_refs",
        ),
        (
            "run_payload",
            {
                "kind": "run",
                "run_id": "example-run",
                "manifest_ref": {"path": "temp/manifest.json", "sha256": SHA},
                "terminal_status": "SUCCEEDED",
                "exit_code": 0,
            },
            "manifest_ref",
        ),
        (
            "transport_payload",
            {
                "kind": "transport",
                "provider": "chatgpt",
                "mode": "DIVERGENT",
                "round_id": "a" * 20,
                "operation_ref": "opaque-operation-id",
                "archive_ref": {"path": "docs/archive.json", "sha256": SHA},
                "handoff_ref": {"path": "docs/handoff.json", "sha256": SHA},
            },
            "handoff_ref",
        ),
        (
            "transport_payload",
            {
                "kind": "transport",
                "provider": "chatgpt",
                "mode": "DIVERGENT",
                "round_id": "a" * 20,
                "operation_ref": "opaque-operation-id",
                "archive_ref": {"path": "docs/archive.json", "sha256": SHA},
                "handoff_ref": None,
            },
            "archive_ref",
        ),
    ],
)
def test_each_payload_file_evidence_field_rejects_opaque_strings(
    definition: str, payload: dict, field: str
) -> None:
    schema = _load(ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json")
    hmasd_state._validate_schema(payload, schema["$defs"][definition], schema, "$")
    invalid = copy.deepcopy(payload)
    invalid[field] = ["opaque-file"] if isinstance(invalid[field], list) else "opaque-file"
    with pytest.raises(Exception):
        hmasd_state._validate_schema(invalid, schema["$defs"][definition], schema, "$")


def test_work_packet_effect_ref_schema_accepts_closed_union_only() -> None:
    schema = _load(ROOT / "scripts" / "schemas" / "hmasd_work_packet.schema.json")
    valid_refs = [
        {"path": "temp/legacy.json"},
        {"kind": "run_manifest", "path": "temp/run.json", "resource_id": "direction/run"},
        {"kind": "worktree", "path": ".codex/runtime/worktrees.json", "resource_id": "direction/assignment"},
        {"kind": "external_operation", "path": "temp/op.json", "resource_id": "operation-1"},
        {"kind": "run_manifest", "path": "temp/run.json", "resource_id": "direction/run", "operation": "CANCEL"},
        {"kind": "worktree", "path": "temp/wt.json", "resource_id": "direction/assignment", "operation": "PUSH"},
        {"kind": "external_operation", "path": "temp/op.json", "resource_id": "operation-1", "operation": "ARCHIVE"},
    ]
    for ref in valid_refs:
        hmasd_state._validate_schema(ref, schema["$defs"]["effect_ref"], schema, "$")
    for ref in [
        {"kind": "invented", "path": "temp/x.json", "resource_id": "x"},
        {"kind": "run_manifest", "path": "temp/x.json"},
        {"kind": "run_manifest", "path": "temp/x.json", "resource_id": "d/r", "extra": True},
        {"kind": "run_manifest", "path": "temp/x.json", "resource_id": "direction/run", "operation": "SEND"},
        {"kind": "worktree", "path": "temp/x.json", "resource_id": "direction/run", "operation": "EXECUTE"},
        {"kind": "external_operation", "path": "temp/x.json", "resource_id": "operation", "operation": "RELEASE"},
    ]:
        with pytest.raises(Exception):
            hmasd_state._validate_schema(ref, schema["$defs"]["effect_ref"], schema, "$")
