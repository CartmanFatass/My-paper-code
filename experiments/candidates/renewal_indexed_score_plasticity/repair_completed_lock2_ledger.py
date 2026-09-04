"""Apply the accepted namespace-accounting correction to the complete RISP r07 result."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCIENCE_REVISION = "RISP-B1-SCIENCE-20260813-07"
RESULT_SCHEMA = "RISP-B1-LOCK2-RESULT-20260813-07"
SOURCE_COMMIT_SCHEMA = "RISP-B1-LOCK2-FINAL-COMMIT-20260813-07"
CORRECTION_COMMIT_SCHEMA = "RISP-B1-LOCK2-TECHNICAL-CORRECTION-COMMIT-20260813-07"
EXPECTED_BASE = {"INIT": 161_792, "ACTION": 5_652_480, "Y": 5_652_480, "ALT": 5_652_480, "TWIN": 301_056}
EXPECTED_FORK = {"FORK_ACTION": 12_288, "FORK_Y": 12_288, "FORK_ALT": 12_288}
EXPECTED_AGGREGATE = {"INIT": 161_792, "ACTION": 5_664_768, "Y": 5_664_768, "ALT": 5_664_768, "TWIN": 301_056}
EXPECTED_TOTAL_CALLS = 17_457_152


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _atomic_create(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError(f"refusing to replace retained artifact: {path}")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def repair(source: Path, source_commit_path: Path, output: Path, correction_commit_path: Path) -> dict[str, Any]:
    source_commit = _load(source_commit_path)
    if (
        source_commit.get("schema") != SOURCE_COMMIT_SCHEMA
        or source_commit.get("science_revision") != SCIENCE_REVISION
        or source_commit.get("result") != str(source.resolve())
        or source_commit.get("bytes") != source.stat().st_size
        or source_commit.get("complete_units") != 256
        or source_commit.get("sha256") != _sha256(source)
    ):
        raise RuntimeError("source complete-result commit identity failed")

    result = _load(source)
    if result.get("schema") != RESULT_SCHEMA or result.get("science_revision") != SCIENCE_REVISION:
        raise RuntimeError("source result identity failed")
    if result.get("activity", {}).get("complete_panel_retained") is not True or len(result.get("seed_results", [])) != 8:
        raise RuntimeError("source result is not the complete eight-seed panel")

    calls = result["sampler_audit"]["calls"]
    if any(calls.get(name) != expected for name, expected in EXPECTED_BASE.items()):
        raise RuntimeError("base categorical namespace ledger differs from the frozen panel")
    if any(calls.get(name) != expected for name, expected in EXPECTED_FORK.items()):
        raise RuntimeError("fork categorical namespace ledger differs from the frozen panel")
    aggregate = {
        "INIT": calls["INIT"],
        "ACTION": calls["ACTION"] + calls["FORK_ACTION"],
        "Y": calls["Y"] + calls["FORK_Y"],
        "ALT": calls["ALT"] + calls["FORK_ALT"],
        "TWIN": calls["TWIN"],
    }
    if aggregate != EXPECTED_AGGREGATE or result["sampler_audit"].get("total_calls") != EXPECTED_TOTAL_CALLS:
        raise RuntimeError("aggregate categorical ledger differs from the frozen panel")

    conditions = result["analysis"]["validity"]["conditions"]
    if conditions.get("exact_categorical_call_ledger") is not False:
        raise RuntimeError("source result does not contain the expected deterministic false negative")
    conditions["exact_categorical_call_ledger"] = True
    result["analysis"]["validity"]["all_conditions_pass"] = all(bool(value) for value in conditions.values())
    if result["analysis"]["validity"]["all_conditions_pass"] is not False:
        raise RuntimeError("ledger repair unexpectedly changed the complete-panel validity branch")
    disposition = result["analysis"]["disposition"]
    if disposition != {
        "primary": "INVALID_OR_NONIDENTIFYING",
        "secondary_labels": [],
        "narrow_ood_finite_budget_prior_reading": False,
    }:
        raise RuntimeError("ledger repair would require a disposition recomputation")

    payload = _encoded(result)
    source_sha256 = _sha256(source)
    corrected_sha256 = hashlib.sha256(payload).hexdigest()
    commit = {
        "schema": CORRECTION_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "source_result": str(source.resolve()),
        "source_sha256": source_sha256,
        "result": str(output.resolve()),
        "bytes": len(payload),
        "sha256": corrected_sha256,
        "changed_field": "analysis.validity.conditions.exact_categorical_call_ledger:false->true",
        "all_other_scientific_values_unchanged": True,
        "primary_disposition_unchanged": True,
    }

    if output.exists() or correction_commit_path.exists():
        observed_commit = _load(correction_commit_path)
        if observed_commit != commit or output.stat().st_size != len(payload) or _sha256(output) != corrected_sha256:
            raise RuntimeError("retained corrected result differs from the accepted correction")
    else:
        _atomic_create(output, payload)
        _atomic_create(correction_commit_path, (json.dumps(commit, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))
    return commit


def main() -> None:
    here = Path(__file__).resolve().parent
    resume_root = here / "RISP_B1_LOCK2_RESUME_20260813_07"
    commit = repair(
        here / "RISP_B1_LOCK2_20260813_07.json",
        resume_root / "FINAL_COMPLETE.commit.json",
        here / "RISP_B1_LOCK2_20260813_07_TECHNICALLY_ACCEPTED.json",
        resume_root / "FINAL_COMPLETE_TECHNICALLY_ACCEPTED.commit.json",
    )
    print(json.dumps({
        "status": "TECHNICALLY_CORRECTED_COMPLETE",
        "result": commit["result"],
        "commit": str((resume_root / "FINAL_COMPLETE_TECHNICALLY_ACCEPTED.commit.json").resolve()),
        "partial_scientific_values_exposed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
