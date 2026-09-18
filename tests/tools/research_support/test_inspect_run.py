"""Single-run report tests: boundary honesty, invalid counts, and safe output.

All fixtures are generated under ``tmp_path``; the report writer is exercised against new
directories only, and one test asserts that it refuses to write into a run directory that
already holds evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# See the note in ``test_readers.py``: ``tests/tools/`` shadows the checkout's ``tools``
# namespace package, so the checkout root has to come first on ``sys.path``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_TOOLS = str(Path(__file__).resolve().parents[1])
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
    _origin = getattr(sys.modules[_name], "__file__", None)
    if _origin and _origin.startswith(_TESTS_TOOLS):
        del sys.modules[_name]

from tools.research_support.inspect_run import (  # noqa: E402
    RUN_REPORT_SCHEMA,
    inspect_run,
    write_run_report,
)
from tools.research_support.readers import UnsupportedSourceError  # noqa: E402
from tools.research_support.records import file_hash, loads  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_readers import (  # noqa: E402
    build_legacy_tree,
    build_process_core,
    build_service_restoration,
)


def test_report_separates_declared_and_observed_boundary_semantics(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run", boundary_declared=True)
    report = inspect_run(root)

    assert report.schema == RUN_REPORT_SCHEMA
    assert report.boundary_semantics["declared"]["semantics"] == (
        "collapsed_truncation_as_termination"
    )
    assert report.boundary_semantics["observed"]["semantics"] is None
    assert report.boundary_semantics["unverified"] is True
    assert report.coverage["reader"] == "process_core"
    assert report.coverage["metric_record_count"] > 0

    names = {Path(entry["path"]).name for entry in report.artifacts}
    assert {"train_manifest.json", "evaluation_manifest.json", "analysis_result.json"} <= names
    train = [entry for entry in report.artifacts if entry["path"].endswith("train_manifest.json")][0]
    assert train["kind"] == "manifest"
    assert train["readable"] is True
    assert train["bytes"] > 0
    assert train["sha256"].startswith("sha256:")


def test_report_counts_invalid_metric_rows(tmp_path: Path) -> None:
    root = build_legacy_tree(tmp_path / "paper_root")
    report = inspect_run(root)

    reward = [row for row in report.metric_summary if row["metric_name"] == "reward"][0]
    assert reward["n_rows"] == 7
    assert reward["n_valid"] == 6
    assert reward["n_invalid"] == 1
    assert reward["x_kind"] == ["checkpoint_step"]
    assert reward["range"] == [0.1, 0.6]
    assert reward["validity_counts"] == {"ok": 6, "invalid": 1}
    # A run that never records a boundary flag says so rather than implying correctness.
    assert report.boundary_semantics["unverified"] is True
    assert any("records neither" in note for note in report.boundary_semantics["notes"])


def test_report_lists_every_run_record_from_a_multi_record_source(tmp_path: Path) -> None:
    root = build_service_restoration(tmp_path / "diag")
    report = inspect_run(root)

    assert report.coverage["run_record_count"] == 2
    assert len(report.coverage["additional_run_records"]) == 1
    assert any(
        "run_record is the first" in warning for warning in report.coverage["warnings"]
    )
    # Nothing is merged: the two controllers keep separate identities.
    first = report.run_record.run_id
    second = report.coverage["additional_run_records"][0]["run_id"]
    assert first != second


def test_write_run_report_creates_a_new_directory(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run", boundary_declared=True)
    report = inspect_run(root)
    output = tmp_path / "reports" / "run-001"

    written = write_run_report(report, output)
    assert written == output
    payload = loads((output / "run_report.json").read_text(encoding="utf-8"))
    assert payload["schema"] == RUN_REPORT_SCHEMA
    assert payload["run_record"]["fields"]["source_sha"]["value"] == "a" * 40
    assert payload["report_content_hash"].startswith("sha256:")

    markdown = (output / "run_report.md").read_text(encoding="utf-8")
    assert "# Run report:" in markdown
    assert "UNVERIFIED" in markdown
    assert "termination_semantics_observed" in markdown


def test_write_run_report_refuses_a_non_empty_directory(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run")
    report = inspect_run(root)
    output = tmp_path / "already-here"
    output.mkdir()
    (output / "existing.txt").write_text("evidence", encoding="utf-8")

    with pytest.raises(FileExistsError) as error:
        write_run_report(report, output)
    assert "not empty" in str(error.value)
    assert (output / "existing.txt").read_text(encoding="utf-8") == "evidence"
    assert not (output / "run_report.json").exists()

    # An empty directory is a legitimate destination.
    empty = tmp_path / "empty-destination"
    empty.mkdir()
    assert write_run_report(report, empty) == empty
    assert (empty / "run_report.json").is_file()


def test_write_run_report_never_touches_the_run_directory(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run", boundary_declared=False)
    before = {path.name: file_hash(str(path)) for path in sorted(root.iterdir())}
    report = inspect_run(root)

    with pytest.raises(FileExistsError):
        write_run_report(report, root)
    write_run_report(report, tmp_path / "out")

    after = {path.name: file_hash(str(path)) for path in sorted(root.iterdir())}
    assert after == before
    assert not (root / "run_report.json").exists()


def test_inspect_run_refuses_an_unrecognised_directory(tmp_path: Path) -> None:
    root = tmp_path / "mystery"
    root.mkdir()
    (root / "output.json").write_text(json.dumps({"value": 1}), encoding="utf-8")
    with pytest.raises(UnsupportedSourceError):
        inspect_run(root)


def test_report_lists_files_the_reader_did_not_consume(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run")
    (root / "checkpoints").mkdir()
    (root / "stray_notes.txt").write_text("hand note", encoding="utf-8")
    report = inspect_run(root)

    stray = [entry for entry in report.artifacts if entry["path"].endswith("stray_notes.txt")]
    assert stray and stray[0]["status"] == "not_read"
    assert "no reader consumed it" in stray[0]["detail"]
