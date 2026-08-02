"""Proof-sized tests for the read-only Explorer toy packet contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents" / "skills" / "hmasd-explorer-project-validation" / "scripts" / "explorer_project_packet.py"


def _run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == expect, (result.stdout, result.stderr)
    return result


def _fixture() -> tuple[tempfile.TemporaryDirectory[str], Path, dict]:
    temporary = tempfile.TemporaryDirectory()
    repo = Path(temporary.name)
    local = repo / "local_research" / "campaign-1"
    local.mkdir(parents=True)
    campaign = local / "campaign.json"
    candidate = local / "candidate.json"
    campaign.write_text('{"campaign":1}\n', encoding="utf-8")
    candidate.write_text('{"candidate":1}\n', encoding="utf-8")
    built = _run(
        "build",
        "--repo",
        str(repo),
        "--workflow-id",
        "EXPLORER-TOY-VALIDATION-2026-07-31-P1",
        "--user-authorization-reference",
        "opaque-user-ref",
        "--campaign-id",
        "campaign-1",
        "--campaign-workflow-commit",
        "workflow-commit-1",
        "--campaign-path",
        "local_research/campaign-1/campaign.json",
        "--candidate-id",
        "CAND-VAP-FOLR-CORE",
        "--candidate-path",
        "local_research/campaign-1/candidate.json",
        "--current-index",
        "0",
        "--ordered-candidate",
        "CAND-VAP-FOLR-CORE",
        "--ordered-candidate",
        "CAND-VSP-02",
        "--ordered-candidate",
        "CAND-VSP-05",
    )
    packet = json.loads(built.stdout)
    return temporary, repo, packet


def _check(repo: Path, packet: dict, *, expected: int = 0) -> subprocess.CompletedProcess[str]:
    path = repo / "local_research" / "packet.json"
    path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return _run("check", "--repo", str(repo), "--packet", str(path), expect=expected)


def _check_text(repo: Path, packet_text: str, *, name: str = "packet.json", expected: int = 0) -> subprocess.CompletedProcess[str]:
    path = repo / "local_research" / name
    path.write_text(packet_text, encoding="utf-8")
    return _run("check", "--repo", str(repo), "--packet", str(path), expect=expected)


def test_build_and_check_happy_path() -> None:
    temporary, repo, packet = _fixture()
    try:
        assert packet["document_kind"] == "explorer_project_candidate_packet_v1"
        assert packet["evidence_tier"] == "nonformal_toy"
        assert packet["origin_campaign"]["artifact"] == "local_research/campaign-1/campaign.json"
        assert packet["candidate"]["artifact"] == "local_research/campaign-1/candidate.json"
        checked = _check(repo, packet)
        assert checked.stderr == ""
        assert json.loads(checked.stdout)["status"] == "EXPLORER_PROJECT_PACKET_OK"
    finally:
        temporary.cleanup()


def test_rejects_authority_path_and_package_negatives() -> None:
    temporary, repo, packet = _fixture()
    try:
        for field in ("scientific_authority", "code_authority", "compute_authority", "project_state_effect"):
            broken = copy.deepcopy(packet)
            broken["authority"][field] = "exclusive"
            _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["compute_authority"] = "exclusive"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["authority"]["unexpected_authority"] = "none"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["review_request"]["candidate_count"] = 2
        _check(repo, broken, expected=2)
        broken = copy.deepcopy(packet)
        broken["review_request"]["cross_direction_competition"] = True
        _check(repo, broken, expected=2)
        broken = copy.deepcopy(packet)
        broken["cohort"]["ordered_candidate_ids"] = ["candidate-1", "candidate-1"]
        _check(repo, broken, expected=2)
        broken = copy.deepcopy(packet)
        broken["candidate"]["id"] = "CAND-VSP-02"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["workflow_id"] = " EXPLORER-TOY-VALIDATION-2026-07-31-P1"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["workflow_id"] = "EXPLORER-TOY-VALIDATION-OTHER"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["cohort"]["ordered_candidate_ids"] = ["CAND-VSP-02", "CAND-VAP-FOLR-CORE", "CAND-VSP-05"]
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["cohort"]["ordered_candidate_ids"] = ["CAND-VAP-FOLR-CORE", "CAND-VSP-02", "UNKNOWN"]
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["packet_version"] = True
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["review_request"]["candidate_count"] = True
        _check(repo, broken, expected=2)
    finally:
        temporary.cleanup()


def test_rejects_traversal_pro_reviews_and_missing_artifacts() -> None:
    temporary, repo, packet = _fixture()
    try:
        broken = copy.deepcopy(packet)
        broken["candidate"]["artifact"] = "local_research/../outside.json"
        _check(repo, broken, expected=2)

        pro = repo / "local_research" / "pro_reviews"
        pro.mkdir()
        (pro / "forbidden.json").write_text("{}", encoding="utf-8")
        broken = copy.deepcopy(packet)
        broken["candidate"]["artifact"] = "local_research/pro_reviews/forbidden.json"
        _check(repo, broken, expected=2)

        broken = copy.deepcopy(packet)
        broken["candidate"]["artifact"] = "local_research/campaign-1/missing.json"
        _check(repo, broken, expected=2)

        duplicate = json.dumps(packet).replace(
            '"packet_version": 1,',
            '"packet_version": 1, "packet_version": 1,',
            1,
        )
        _check_text(repo, duplicate, expected=2)

    finally:
        temporary.cleanup()


def test_rejects_packet_path_link_or_reparse(monkeypatch: pytest.MonkeyPatch) -> None:
    temporary, repo, packet = _fixture()
    try:
        packet_path = repo / "local_research" / "packet.json"
        packet_path.write_text(json.dumps(packet), encoding="utf-8")
        link_path = repo / "local_research" / "packet-link.json"
        try:
            link_path.symlink_to(packet_path)
        except OSError:
            spec = importlib.util.spec_from_file_location("explorer_project_packet_test_module", SCRIPT)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            monkeypatch.setattr(module, "_is_reparse", lambda path: path == packet_path)
            with pytest.raises(module.PacketError, match="symlink/reparse"):
                module._safe_file(repo, "local_research/packet.json", "packet path")
        else:
            _run("check", "--repo", str(repo), "--packet", str(link_path), expect=2)
    finally:
        temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__]))
