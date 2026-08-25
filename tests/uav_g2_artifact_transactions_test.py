from __future__ import annotations

from pathlib import Path

import pytest

from ha_ctse_process import uav_g2_artifact_transactions as transactions


ARTIFACT_SCHEMA = "test.uav_g2.artifact.v1"


def test_json_and_jsonl_exact_round_trip_and_immutable_rejection(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "nested" / "value.json"
    value = {"z": [1], "a": {"b": True}}
    transactions._write_json(json_path, value)
    assert json_path.read_text(encoding="utf-8") == (
        '{\n  "a": {\n    "b": true\n  },\n  "z": [\n    1\n  ]\n}\n'
    )
    assert transactions._read_json(json_path) == value

    jsonl_path = tmp_path / "rows.jsonl"
    rows = [{"z": 2, "a": 1}, {"b": True}]
    transactions._write_jsonl(jsonl_path, rows)
    assert jsonl_path.read_text(encoding="utf-8") == (
        '{"a": 1, "z": 2}\n{"b": true}\n'
    )
    assert transactions._read_jsonl(jsonl_path) == rows

    immutable_path = tmp_path / "immutable.json"
    transactions._write_json_immutable(immutable_path, {"first": True})
    with pytest.raises(FileExistsError):
        transactions._write_json_immutable(immutable_path, {"second": True})
    assert transactions._read_json(immutable_path) == {"first": True}


def test_commit_marker_binding_validation_and_tamper_rejection(
    tmp_path: Path,
) -> None:
    reference = "artifacts/value.json"
    artifact = tmp_path / reference
    transactions._write_json_immutable(artifact, {"value": 1})
    binding = transactions._commit_artifact(tmp_path, reference, ARTIFACT_SCHEMA)

    assert binding == {
        "reference": reference,
        "complete_reference": f"{reference}.complete.json",
        "sha256": transactions._sha256_file(artifact),
    }
    marker = tmp_path / binding["complete_reference"]
    assert transactions._read_json(marker) == {
        "schema": transactions.COMMIT_SCHEMA,
        "artifact_schema": ARTIFACT_SCHEMA,
        "artifact_reference": reference,
        "artifact_sha256": binding["sha256"],
    }
    assert (
        transactions._validate_committed_artifact(
            tmp_path, binding, schema=ARTIFACT_SCHEMA
        )
        == artifact
    )

    transactions._write_json(artifact, {"value": 2})
    with pytest.raises(ValueError, match="artifact binding SHA-256 mismatch"):
        transactions._validate_committed_artifact(
            tmp_path, binding, schema=ARTIFACT_SCHEMA
        )


def test_root_escape_orphan_and_truncated_marker_recovery(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="artifact binding escapes run root"):
        transactions._validate_committed_artifact(
            tmp_path,
            {
                "reference": "../escape.json",
                "complete_reference": "../escape.json.complete.json",
                "sha256": "0" * 64,
            },
            schema=ARTIFACT_SCHEMA,
        )

    orphan_reference = "recovery/orphan.json"
    orphan = tmp_path / orphan_reference
    transactions._write_json_immutable(orphan, {"orphan": True})
    assert (
        transactions._recover_binding(
            tmp_path, orphan_reference, schema=ARTIFACT_SCHEMA
        )
        is None
    )
    assert not orphan.exists()

    truncated_reference = "recovery/truncated.json"
    truncated = tmp_path / truncated_reference
    transactions._write_json_immutable(truncated, {"truncated": True})
    marker = tmp_path / f"{truncated_reference}.complete.json"
    marker.write_text('{"partial":', encoding="utf-8")
    assert (
        transactions._recover_binding(
            tmp_path, truncated_reference, schema=ARTIFACT_SCHEMA
        )
        is None
    )
    assert not truncated.exists()
    assert not marker.exists()


def test_terminal_binding_rebuild_and_highest_valid_attempt_selection(
    tmp_path: Path,
) -> None:
    terminal_reference = "terminal.json"
    transactions._write_json_immutable(
        tmp_path / terminal_reference, {"terminal": True}
    )
    expected = transactions._commit_artifact(
        tmp_path, terminal_reference, ARTIFACT_SCHEMA
    )
    binding_path = tmp_path / "terminal.binding.json"
    binding_path.write_text('{"partial":', encoding="utf-8")
    assert (
        transactions._terminal_binding(
            tmp_path,
            binding_path,
            reference=terminal_reference,
            schema=ARTIFACT_SCHEMA,
        )
        == expected
    )
    assert transactions._read_json(binding_path) == expected

    attempts = tmp_path / "attempts"
    for attempt in (2, 5):
        reference = f"attempts/chunk.attempt-{attempt}.json"
        transactions._write_json_immutable(
            tmp_path / reference, {"attempt": attempt}
        )
        transactions._commit_artifact(tmp_path, reference, ARTIFACT_SCHEMA)
    transactions._write_json_immutable(
        attempts / "chunk.attempt-9.json", {"attempt": 9}
    )

    recovered = transactions._recover_attempt_binding(
        tmp_path,
        directory=attempts,
        artifact_pattern="chunk.attempt-*.json",
        artifact_name_pattern=r"chunk\.attempt-(\d+)\.json",
        schema=ARTIFACT_SCHEMA,
    )
    assert recovered is not None
    assert recovered["reference"] == "attempts/chunk.attempt-5.json"
    assert (
        transactions._validate_committed_artifact(
            tmp_path, recovered, schema=ARTIFACT_SCHEMA
        ).name
        == "chunk.attempt-5.json"
    )
