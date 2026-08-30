"""Focused contract tests for stage-safe external-review prompt registration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import scripts.hmasd_external_review as external_review
from scripts.hmasd_external_review import (
    ExternalReviewError,
    RegistrationUnknown,
    RevisionConflict,
    recover_registration,
    register_prompt,
    round_id,
    validate_prompt,
)


DIRECTION = "example-direction"
QUESTION_SHA = "1" * 64
EVIDENCE_SHA = "2" * 64
WORKFLOW_VERSION = "hmasd-external-review-v1"
ROUND_ID = round_id(DIRECTION, QUESTION_SHA, EVIDENCE_SHA, WORKFLOW_VERSION)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _index_path(project: Path) -> Path:
    return (
        project
        / "docs"
        / "research"
        / "candidates"
        / DIRECTION
        / "workflow"
        / "external-review"
        / "index.json"
    )


def _canonical_prompt(project: Path, stage: str) -> Path:
    filename = {
        "pro_innovator": "PRO_INNOVATOR_PROMPT.md",
        "pro_convergence": "PRO_CONVERGENCE_PROMPT.md",
    }[stage]
    return (
        project
        / "docs"
        / "external-review"
        / "directions"
        / DIRECTION
        / ROUND_ID
        / stage
        / filename
    )


def _empty_index() -> dict[str, Any]:
    return {
        "schema_version": 4,
        "revision": 1,
        "updated_at": "2026-08-30T00:00:00Z",
        "writer": f"EM-{DIRECTION}",
        "direction_id": DIRECTION,
        "workflow_version": WORKFLOW_VERSION,
        "rounds": [],
    }


def _prompt_text(stage: str) -> str:
    identity = (
        f"review_stage: {stage}\n"
        f"question_sha256: {QUESTION_SHA}\n"
        f"evidence_set_sha256: {EVIDENCE_SHA}\n"
        f"workflow_version: {WORKFLOW_VERSION}\n"
    )
    if stage == "pro_innovator":
        return (
            identity
            + "Independently explore mechanisms and counterexamples for the neutral frozen "
            "question using declared repository evidence.\n"
        )
    return (
        identity
        + "Assess the EM-authored local synthesis against the declared repository evidence "
        "while keeping provider provenance isolated.\n"
    )


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    project = tmp_path / "project"
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", project)
    index = _index_path(project)
    _write_json(index, _empty_index())
    prompt = tmp_path / "disposable-prompt.md"
    prompt.write_text(_prompt_text("pro_innovator"), encoding="utf-8")
    return project, index, prompt


def _common(index: Path) -> dict[str, Any]:
    return {
        "external_index": index,
        "direction_id": DIRECTION,
        "round_id_value": ROUND_ID,
        "question_sha256": QUESTION_SHA,
        "evidence_set_sha256": EVIDENCE_SHA,
        "workflow_version": WORKFLOW_VERSION,
    }


def _register_innovator(project: Path, index: Path, prompt: Path) -> dict[str, Any]:
    raw = prompt.read_bytes()
    result = register_prompt(
        "pro_innovator",
        prompt,
        expected_revision=1,
        prompt_sha256=_sha(raw),
        **_common(index),
    )
    assert _canonical_prompt(project, "pro_innovator").read_bytes() == raw
    return result


def _prepare_synthesis(project: Path, index: Path) -> tuple[dict[str, str], dict[str, str]]:
    document = json.loads(index.read_text(encoding="utf-8"))
    review_round = document["rounds"][0]
    synthesis = (
        project
        / "docs"
        / "research"
        / "candidates"
        / DIRECTION
        / "LOCAL_SYNTHESIS.md"
    )
    synthesis.write_bytes(b"Durable EM-authored local synthesis.\n")
    synthesis_ref = {
        "path": str(synthesis.relative_to(project).as_posix()),
        "sha256": _sha(synthesis.read_bytes()),
    }
    innovator_ref = dict(review_round["prompt_refs"]["pro_innovator"])
    review_round["local_synthesis_ref"] = synthesis_ref
    review_round["status"] = "SYNTHESIS_READY"
    document["revision"] = 3
    document["updated_at"] = "2026-08-30T00:02:00Z"
    _write_json(index, document)
    return synthesis_ref, innovator_ref


class _ProcessInterrupted(BaseException):
    """Simulated process loss: bypass in-process Exception recovery."""


def _only_transaction_id(project: Path) -> str:
    journal_root = project / ".omp" / "runtime" / "external-review-registrations"
    transaction_ids = sorted(
        path.name
        for path in journal_root.iterdir()
        if (path / "journal.json").is_file()
    )
    assert len(transaction_ids) == 1
    return transaction_ids[0]


def _registration_call(index: Path, prompt: Path) -> dict[str, Any]:
    return {
        "review_stage": "pro_innovator",
        "prompt": prompt,
        "expected_revision": 1,
        "prompt_sha256": _sha(prompt.read_bytes()),
        **_common(index),
    }


def test_active_cli_exposes_only_stage_specific_prompt_commands() -> None:
    parser = external_review._parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    assert set(subparsers.choices) == {
        "validate-prompt",
        "register-prompt",
        "recover-registration",
    }
    for command in ("validate-prompt", "register-prompt"):
        options = {
            option
            for action in subparsers.choices[command]._actions
            for option in action.option_strings
        }
        assert "--review-stage" in options
        assert "--round-dir" not in options


def test_valid_innovator_only_registration_is_exact_and_leaves_convergence_null(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    raw = prompt.read_bytes()

    validated = validate_prompt("pro_innovator", prompt, **_common(index))
    assert validated["status"] == "VALID"
    assert validated["prompt_sha256"] == _sha(raw)
    assert not _canonical_prompt(project, "pro_innovator").exists()

    registered = register_prompt(
        "pro_innovator",
        prompt,
        expected_revision=1,
        prompt_sha256=validated["prompt_sha256"],
        **_common(index),
    )

    document = json.loads(index.read_text(encoding="utf-8"))
    assert registered["status"] == "REGISTERED"
    assert registered["external_index_revision"] == 2
    assert _canonical_prompt(project, "pro_innovator").read_bytes() == raw
    assert len(document["rounds"]) == 1
    review_round = document["rounds"][0]
    assert review_round["status"] == "INNOVATOR_PENDING"
    assert review_round["prompt_refs"]["pro_innovator"] == registered["prompt_ref"]
    assert review_round["prompt_refs"]["pro_convergence"] is None


def test_registered_innovator_prompt_and_ref_are_immutable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    _register_innovator(project, index, prompt)
    canonical = _canonical_prompt(project, "pro_innovator")
    before_index = index.read_bytes()
    before_prompt = canonical.read_bytes()

    with pytest.raises(ExternalReviewError, match="already registered and immutable"):
        register_prompt(
            "pro_innovator",
            prompt,
            expected_revision=2,
            prompt_sha256=_sha(prompt.read_bytes()),
            **_common(index),
        )

    assert index.read_bytes() == before_index
    assert canonical.read_bytes() == before_prompt


def test_invalid_disposable_prompt_has_zero_durable_effect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    prompt.write_text(
        _prompt_text("pro_innovator")
        + "The local scientific conclusion is that the preferred mechanism wins.\n",
        encoding="utf-8",
    )
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="forbidden review reference"):
        register_prompt(
            "pro_innovator",
            prompt,
            expected_revision=1,
            prompt_sha256=_sha(prompt.read_bytes()),
            **_common(index),
        )

    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_innovator").exists()


def test_current_prompt_validation_refuses_v2_without_canonical_effect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    document = _empty_index()
    document["schema_version"] = 2
    _write_json(index, document)
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="expected 4"):
        validate_prompt("pro_innovator", prompt, **_common(index))

    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_innovator").exists()


def test_innovator_requires_exact_prompt_identities_without_creating_facts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    prompt.write_text(
        _prompt_text("pro_innovator").replace(QUESTION_SHA, "5" * 64),
        encoding="utf-8",
    )
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="exact question_sha256"):
        validate_prompt("pro_innovator", prompt, **_common(index))

    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_innovator").exists()


def test_convergence_refuses_before_durable_synthesis(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    _register_innovator(project, index, prompt)
    convergence = tmp_path / "disposable-convergence.md"
    convergence.write_text(_prompt_text("pro_convergence"), encoding="utf-8")
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="SYNTHESIS_READY"):
        validate_prompt(
            "pro_convergence",
            convergence,
            **_common(index),
        )

    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_convergence").exists()


def test_convergence_registers_after_synthesis_with_exact_prerequisites(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    _register_innovator(project, index, prompt)
    synthesis_ref, innovator_ref = _prepare_synthesis(project, index)
    convergence = tmp_path / "disposable-convergence.md"
    convergence.write_text(_prompt_text("pro_convergence"), encoding="utf-8")
    raw = convergence.read_bytes()

    validated = validate_prompt(
        "pro_convergence",
        convergence,
        local_synthesis_ref=synthesis_ref,
        innovator_prompt_ref=innovator_ref,
        **_common(index),
    )
    registered = register_prompt(
        "pro_convergence",
        convergence,
        expected_revision=3,
        prompt_sha256=validated["prompt_sha256"],
        local_synthesis_ref=synthesis_ref,
        innovator_prompt_ref=innovator_ref,
        **_common(index),
    )

    document = json.loads(index.read_text(encoding="utf-8"))
    review_round = document["rounds"][0]
    assert registered["external_index_revision"] == 4
    assert _canonical_prompt(project, "pro_convergence").read_bytes() == raw
    assert review_round["prompt_refs"]["pro_innovator"] == innovator_ref
    assert review_round["prompt_refs"]["pro_convergence"] == registered["prompt_ref"]
    assert review_round["local_synthesis_ref"] == synthesis_ref


def test_path_mismatch_is_refused_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    _register_innovator(project, index, prompt)
    synthesis_ref, innovator_ref = _prepare_synthesis(project, index)
    convergence = tmp_path / "disposable-convergence.md"
    convergence.write_text(_prompt_text("pro_convergence"), encoding="utf-8")
    wrong_ref = dict(innovator_ref)
    wrong_ref["path"] = wrong_ref["path"].replace(
        "/pro_innovator/", "/wrong-stage/"
    )
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="does not match"):
        validate_prompt(
            "pro_convergence",
            convergence,
            local_synthesis_ref=synthesis_ref,
            innovator_prompt_ref=wrong_ref,
            **_common(index),
        )

    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_convergence").exists()


def test_prompt_hash_and_revision_mismatches_leave_both_files_absent_or_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    before = index.read_bytes()

    with pytest.raises(ExternalReviewError, match="hash changed"):
        register_prompt(
            "pro_innovator",
            prompt,
            expected_revision=1,
            prompt_sha256="f" * 64,
            **_common(index),
        )
    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_innovator").exists()

    with pytest.raises(RevisionConflict, match="expected revision"):
        register_prompt(
            "pro_innovator",
            prompt,
            expected_revision=9,
            prompt_sha256=_sha(prompt.read_bytes()),
            **_common(index),
        )
    assert index.read_bytes() == before
    assert not _canonical_prompt(project, "pro_innovator").exists()


@pytest.mark.parametrize(
    ("interrupted_phase", "expected_status"),
    [
        ("STAGED", "ROLLED_BACK"),
        ("PROMPT_PUBLISHED", "REGISTERED"),
        ("INDEX_PUBLISHED", "REGISTERED"),
        ("VERIFIED", "REGISTERED"),
        ("CLEANING", "REGISTERED"),
        ("COMMITTED", "REGISTERED"),
    ],
)
def test_phase_journal_recovery_reaches_exactly_one_consistent_terminal_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    interrupted_phase: str,
    expected_status: str,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    old_index = index.read_bytes()
    original_phase = external_review._registration_phase

    def interrupt_after_phase(
        journal: dict[str, Any],
        phase: str,
        *,
        observation: str | None = None,
    ) -> dict[str, Any]:
        updated = original_phase(journal, phase, observation=observation)
        if phase == interrupted_phase:
            raise _ProcessInterrupted(phase)
        return updated

    monkeypatch.setattr(
        external_review,
        "_registration_phase",
        interrupt_after_phase,
    )
    with pytest.raises(_ProcessInterrupted, match=interrupted_phase):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(external_review, "_registration_phase", original_phase)

    recovered = recover_registration(transaction_id)
    canonical = _canonical_prompt(project, "pro_innovator")
    assert recovered["status"] == expected_status
    if expected_status == "ROLLED_BACK":
        assert index.read_bytes() == old_index
        assert not canonical.exists()
    else:
        assert json.loads(index.read_text(encoding="utf-8"))["revision"] == 2
        assert canonical.read_bytes() == prompt.read_bytes()


@pytest.mark.parametrize("interrupt_after_write", [False, True])
def test_before_or_after_initial_journal_fsync_has_no_inconsistent_canonical_effect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    interrupt_after_write: bool,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    old_index = index.read_bytes()
    original_write = external_review._write_registration_journal

    def interrupt_preparing(journal: dict[str, Any]) -> None:
        if journal["phase"] == "PREPARING":
            if interrupt_after_write:
                original_write(journal)
            raise _ProcessInterrupted("PREPARING")
        original_write(journal)

    monkeypatch.setattr(
        external_review,
        "_write_registration_journal",
        interrupt_preparing,
    )
    with pytest.raises(_ProcessInterrupted, match="PREPARING"):
        register_prompt(**_registration_call(index, prompt))
    monkeypatch.setattr(
        external_review,
        "_write_registration_journal",
        original_write,
    )

    assert index.read_bytes() == old_index
    assert not _canonical_prompt(project, "pro_innovator").exists()
    if interrupt_after_write:
        recovered = recover_registration(_only_transaction_id(project))
        assert recovered["status"] == "ROLLED_BACK"


@pytest.mark.parametrize(
    "publication_helper",
    ["_publish_registration_prompt", "_publish_registration_index"],
)
def test_process_loss_after_each_canonical_publication_boundary_rolls_forward(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    publication_helper: str,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    original = getattr(external_review, publication_helper)

    def interrupt_after_publication(journal: dict[str, Any]) -> None:
        original(journal)
        raise _ProcessInterrupted(publication_helper)

    monkeypatch.setattr(
        external_review,
        publication_helper,
        interrupt_after_publication,
    )
    with pytest.raises(_ProcessInterrupted, match=publication_helper):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(external_review, publication_helper, original)

    recovered = recover_registration(transaction_id)
    assert recovered["status"] == "REGISTERED"
    assert json.loads(index.read_text(encoding="utf-8"))["revision"] == 2
    assert _canonical_prompt(project, "pro_innovator").read_bytes() == prompt.read_bytes()


@pytest.mark.parametrize(
    ("publication", "interrupt_before_fsync"),
    [
        ("prompt", True),
        ("prompt", False),
        ("index", True),
        ("index", False),
    ],
)
def test_process_loss_before_or_after_each_canonical_directory_fsync_recovers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    publication: str,
    interrupt_before_fsync: bool,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    canonical = _canonical_prompt(project, "pro_innovator")
    original_fsync = external_review._fsync_directory
    interrupted = False

    def interrupt_publication_fsync(path: Path) -> None:
        nonlocal interrupted
        current_revision = json.loads(index.read_text(encoding="utf-8"))["revision"]
        is_boundary = (
            publication == "prompt"
            and path == canonical.parent
            and canonical.exists()
            and current_revision == 1
        ) or (
            publication == "index"
            and path == index.parent
            and current_revision == 2
        )
        if is_boundary and not interrupted:
            interrupted = True
            if not interrupt_before_fsync:
                original_fsync(path)
            raise _ProcessInterrupted(f"{publication} fsync")
        original_fsync(path)

    monkeypatch.setattr(
        external_review,
        "_fsync_directory",
        interrupt_publication_fsync,
    )
    with pytest.raises(_ProcessInterrupted, match=f"{publication} fsync"):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(external_review, "_fsync_directory", original_fsync)

    recovered = recover_registration(transaction_id)
    assert recovered["status"] == "REGISTERED"
    assert canonical.read_bytes() == prompt.read_bytes()
    assert json.loads(index.read_text(encoding="utf-8"))["revision"] == 2


def test_index_pointing_to_absent_prompt_is_repaired_from_exact_staged_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    original = external_review._publish_registration_index

    def interrupt_after_index(journal: dict[str, Any]) -> None:
        original(journal)
        raise _ProcessInterrupted("index replaced")

    monkeypatch.setattr(
        external_review,
        "_publish_registration_index",
        interrupt_after_index,
    )
    with pytest.raises(_ProcessInterrupted, match="index replaced"):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    canonical = _canonical_prompt(project, "pro_innovator")
    canonical.unlink()
    monkeypatch.setattr(external_review, "_publish_registration_index", original)

    recovered = recover_registration(transaction_id)
    assert recovered["status"] == "REGISTERED"
    assert canonical.read_bytes() == prompt.read_bytes()
    assert json.loads(index.read_text(encoding="utf-8"))["revision"] == 2


def test_terminal_cleanup_interruption_is_idempotently_completed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    original = external_review._cleanup_registration_stages

    def interrupt_during_cleanup(journal: dict[str, Any]) -> None:
        external_review._registration_blob_path(journal, "prompt").unlink()
        raise _ProcessInterrupted("terminal cleanup")

    monkeypatch.setattr(
        external_review,
        "_cleanup_registration_stages",
        interrupt_during_cleanup,
    )
    with pytest.raises(_ProcessInterrupted, match="terminal cleanup"):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(
        external_review,
        "_cleanup_registration_stages",
        original,
    )

    first = recover_registration(transaction_id)
    second = recover_registration(transaction_id)
    assert first["status"] == second["status"] == "REGISTERED"
    assert _canonical_prompt(project, "pro_innovator").read_bytes() == prompt.read_bytes()


def test_rollback_cleanup_interruption_restores_old_terminal_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    old_index = index.read_bytes()
    original_phase = external_review._registration_phase

    def interrupt_staged(
        journal: dict[str, Any],
        phase: str,
        *,
        observation: str | None = None,
    ) -> dict[str, Any]:
        updated = original_phase(journal, phase, observation=observation)
        if phase == "STAGED":
            raise _ProcessInterrupted("STAGED")
        return updated

    monkeypatch.setattr(external_review, "_registration_phase", interrupt_staged)
    with pytest.raises(_ProcessInterrupted, match="STAGED"):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(external_review, "_registration_phase", original_phase)

    original_cleanup = external_review._cleanup_registration_stages

    def interrupt_rollback_cleanup(journal: dict[str, Any]) -> None:
        external_review._registration_blob_path(journal, "old_index").unlink()
        raise _ProcessInterrupted("rollback cleanup")

    monkeypatch.setattr(
        external_review,
        "_cleanup_registration_stages",
        interrupt_rollback_cleanup,
    )
    with pytest.raises(_ProcessInterrupted, match="rollback cleanup"):
        recover_registration(transaction_id)
    monkeypatch.setattr(
        external_review,
        "_cleanup_registration_stages",
        original_cleanup,
    )

    recovered = recover_registration(transaction_id)
    assert recovered["status"] == "ROLLED_BACK"
    assert index.read_bytes() == old_index
    assert not _canonical_prompt(project, "pro_innovator").exists()


def test_same_exact_registration_and_recovery_are_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    first = register_prompt(**_registration_call(index, prompt))
    before_index = index.read_bytes()
    before_prompt = _canonical_prompt(project, "pro_innovator").read_bytes()

    recovered = recover_registration(first["transaction_id"])
    repeated = register_prompt(**_registration_call(index, prompt))

    assert recovered["status"] == repeated["status"] == "REGISTERED"
    assert index.read_bytes() == before_index
    assert _canonical_prompt(project, "pro_innovator").read_bytes() == before_prompt


def test_staged_hash_collision_refuses_unknown_without_canonical_rewrite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    old_index = index.read_bytes()
    original_phase = external_review._registration_phase

    def interrupt_staged(
        journal: dict[str, Any],
        phase: str,
        *,
        observation: str | None = None,
    ) -> dict[str, Any]:
        updated = original_phase(journal, phase, observation=observation)
        if phase == "STAGED":
            raise _ProcessInterrupted("STAGED")
        return updated

    monkeypatch.setattr(external_review, "_registration_phase", interrupt_staged)
    with pytest.raises(_ProcessInterrupted, match="STAGED"):
        register_prompt(**_registration_call(index, prompt))
    transaction_id = _only_transaction_id(project)
    monkeypatch.setattr(external_review, "_registration_phase", original_phase)
    journal = external_review._load_registration_journal(transaction_id)
    external_review._registration_blob_path(journal, "prompt").write_bytes(
        b"collision"
    )

    with pytest.raises(RegistrationUnknown, match="UNKNOWN"):
        recover_registration(transaction_id)
    assert index.read_bytes() == old_index
    assert not _canonical_prompt(project, "pro_innovator").exists()


def test_wrong_canonical_bytes_after_registration_are_immutable_and_unknown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project, index, prompt = _setup(monkeypatch, tmp_path)
    registered = register_prompt(**_registration_call(index, prompt))
    canonical = _canonical_prompt(project, "pro_innovator")
    canonical.write_bytes(b"wrong immutable bytes")
    before_index = index.read_bytes()
    before_prompt = canonical.read_bytes()

    with pytest.raises(RegistrationUnknown, match="UNKNOWN"):
        recover_registration(registered["transaction_id"])

    assert index.read_bytes() == before_index
    assert canonical.read_bytes() == before_prompt
