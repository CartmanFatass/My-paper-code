"""Focused contract tests for the frozen FSD E3 runner."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_flexible_skill_duration_e3 as e3  # noqa: E402


def _passed_receipt(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True,
        "effective_floor_pass": True, "minimum_available_bytes": 4 * 1024**3,
        "external_receipt_sentinel": "do-not-overwrite",
    }), encoding="utf-8")


def test_registered_rows_and_exact_arm_parameters() -> None:
    expected = {
        "small": ((0.005, 0.02), 0.4, 20, 0.057037),
        "medium": ((0.005, 0.10), 0.6, 5, 0.144358),
        "large": ((0.02, 0.20), 1.0, 5, 0.271219),
    }
    for row, (hazards, delta, best_k, margin) in expected.items():
        config = e3.row_config(row)
        assert config.lambda_regions == hazards
        assert config.delta == delta
        assert e3.PROPOSAL_GRID[row]["m_dur"] == margin
        d0 = e3.arm_parameters(row, "d0")
        assert math.isinf(d0["interruption_cost_c"])
        assert math.isinf(d0["interruption_cost_c_Z"])
        assert d0["skill_cap_k_max"] == best_k
        assert d0["team_cap_k_Z"] == best_k
        d2 = e3.arm_parameters(row, "d2")
        assert d2 == {
            "policy_interruption_mode": "d2", "interruption_delta": 1,
            "interruption_cost_c": 0.25, "interruption_cost_c_Z": 0.25,
            "skill_cap_k_max": 40, "team_cap_k_Z": 400, "age_feature": "off",
        }


def test_external_receipt_is_consumed_without_internal_admission(tmp_path: Path) -> None:
    run_dir = tmp_path / "small_d0_seed1"
    receipt = run_dir / "preflight.json"
    _passed_receipt(receipt)
    e3._PREFLIGHT_RECEIPT = receipt
    assert e3.load_preflight(run_dir)["passed"] is True
    receipt.write_text(json.dumps({"passed": False}), encoding="utf-8")
    with pytest.raises(ValueError, match="did not pass"):
        e3.load_preflight(run_dir)


def test_parser_restricts_frozen_seed_set() -> None:
    with pytest.raises(SystemExit):
        e3.build_parser().parse_args([
            "--row", "small", "--arm", "d0", "--seed", "4",
            "--preflight-receipt", "x", "--output-root", "y",
            "--launch-commit", "z",
        ])


def test_terminal_partial_manifest_drops_inherited_version(tmp_path: Path) -> None:
    run_dir = tmp_path / "terminal_partial"
    run_dir.mkdir()
    manifest = run_dir / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": 1, "ended_at": None}),
                        encoding="utf-8")
    e3.strip_inherited_versions(run_dir)
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"ended_at": None}
    assert not (run_dir / "summary.json").exists()


def test_paired_return_uses_ordered_episode_inputs() -> None:
    out = e3.paired_return([0.1, 0.3, 0.2], [0.2, 0.1, 0.5], 0.2)
    differences = np.asarray([0.1, -0.2, 0.3])
    assert out["episode_count"] == 3
    assert out["G"] == pytest.approx(differences.mean())
    assert out["paired_stderr"] == pytest.approx(
        differences.std(ddof=1) / np.sqrt(3))
    assert out["Q"] == pytest.approx(differences.mean() / 0.2)


def _path_fixture() -> dict:
    # T=4, B=1, N=2. Region 1 has event flags at t=1 and gap renewals at t=2,
    # which is inside {t_event,t_event+1}; region 0 has neither.
    sampled = np.asarray([[[1, 1]], [[0, 0]], [[0, 1]], [[0, 0]]], dtype=bool)
    causes = np.asarray(
        [[[1, 1]], [[0, 0]], [[0, e3.e2.CAUSE_GAP]], [[0, 0]]], dtype=np.int64)
    team = np.asarray([[1], [0], [0], [0]], dtype=np.int64)
    flags = np.zeros((4, 1, 2), dtype=bool)
    flags[1, 0, 1] = True
    fresh = np.ones((4, 1, 2), dtype=bool)
    fresh[3, 0, 1] = False
    consequence = {
        "lease_fresh": fresh,
        "role_correct": np.ones((4, 1, 2), dtype=bool),
        "service": np.asarray([[[0, 0]], [[1, 1]], [[1, 0]], [[1, 0]]], dtype=bool),
        "per_agent_reward": np.asarray(
            [[[0, 0]], [[0.1, 0.1]], [[0.1, 0]], [[0.1, 0]]], dtype=float),
    }
    return e3.regional_path_record(
        sampled, causes, team, flags, np.asarray([0, 1]), consequence)


def test_regional_accounting_and_event_window_rule() -> None:
    path = _path_fixture()
    low, high = path["0"], path["1"]
    assert low["segment_lengths"] == [4]
    assert high["segment_lengths"] == [2, 2]
    assert high["gap_renewal_count"] == 1
    assert high["gap_renewal_event_window_count"] == 1
    assert high["event_precision"] == 1.0
    assert high["event_recall"] == 1.0
    assert high["renewal_outage_count"] == 2
    assert high["fresh_correct_role_service_count"] == 1
    assert high["stale_service_count"] == 0
    assert high["stale_correct_role_opportunity_count"] == 1
    assert high["shared_return_contribution"] == pytest.approx(0.1 / 4)
    assert e3.event_path(path) is True


@pytest.mark.parametrize(("pairs", "expected"), [
    ([{"d0_competence_ratio": 0.9, "G": 1, "event_path": True},
      {"d0_competence_ratio": 0.8, "G": 1, "event_path": True},
      {"d0_competence_ratio": 0.7, "G": 1, "event_path": True}],
     "E3-COMPETENCE-BLOCKED"),
    ([{"d0_competence_ratio": 0.9, "G": 1, "event_path": True},
      {"d0_competence_ratio": 0.9, "G": 1, "event_path": True},
      {"d0_competence_ratio": 0.9, "G": -1, "event_path": False}],
     "E3-H1-ACTIONABLE"),
    ([{"d0_competence_ratio": 0.9, "G": 1, "event_path": True},
      {"d0_competence_ratio": 0.9, "G": 1, "event_path": False},
      {"d0_competence_ratio": 0.9, "G": -1, "event_path": False}],
     "E3-RETURN-WITHOUT-PATH"),
    ([{"d0_competence_ratio": 0.9, "G": 0, "event_path": False},
      {"d0_competence_ratio": 0.9, "G": -1, "event_path": False},
      {"d0_competence_ratio": 0.9, "G": 1, "event_path": True}],
     "E3-H0-NO-ADVANTAGE"),
    ([{"d0_competence_ratio": 0.9, "G": 1, "event_path": False},
      {"d0_competence_ratio": 0.9, "G": -1, "event_path": False},
      {"d0_competence_ratio": 0.8, "G": 1, "event_path": True}],
     "E3-UNSTABLE"),
])
def test_all_frozen_result_branches(pairs, expected) -> None:
    assert e3.apply_result_rule(pairs) == expected


def test_postprocess_publishes_when_peak_rss_is_unavailable(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = tmp_path / "small_d0_seed1"
    run_dir.mkdir()
    evaluations = [
        {"rollout": rollout, "episodes": episodes,
         "episode_returns": [0.0] * episodes}
        for rollout, episodes in ((5, 512), (10, 512), (15, 512), (20, 2048))
    ]
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps({
        "schema_version": 1,
        "references": {
            "J_fixed_k": {"20": 1.0},
            "m_dur": e3.PROPOSAL_GRID["small"]["m_dur"],
        },
        "final_evaluation_return_mean": 0.9,
        "evaluations": evaluations,
        "wall_seconds_total": 123.0,
        "seconds_per_rollout_mean": 6.15,
    }), encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "evaluation": {"tapes": {"keying": "(master_seed, episode_id, entity_or_region_id)"}},
    }), encoding="utf-8")
    (run_dir / "interruptions.jsonl").write_text(json.dumps({
        "rollout": 20,
        "regional_path": _path_fixture(),
    }) + "\n", encoding="utf-8")
    receipt = run_dir / "preflight.json"
    _passed_receipt(receipt)
    monkeypatch.setattr(e3, "_PREFLIGHT_RECEIPT", receipt)
    monkeypatch.delattr(e3.ctypes, "windll", raising=False)
    e3._postprocess(run_dir, "small", "d0")

    published = json.loads(summary_path.read_text(encoding="utf-8"))
    assert published["d0_competence_ratio_input"] == pytest.approx(0.9)
    assert published["cumulative_regional_path"] is not None
    assert published["evaluation_episodes_total"] == 3584
    assert published["peak_rss_bytes"] is None
    assert published["resource_telemetry_status"] == "resources_unmeasured"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["evaluation"]["reduced_from_contract"] is False
    assert manifest["evaluation"]["e3_expected_counts"] == {
        "checkpoints": [5, 10, 15, 20],
        "intermediate_episodes": 512,
        "final_episodes": 2048,
        "full_run_records": 4,
    }


def test_toy_end_to_end_writes_exact_e3_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "E3_toy"
    run_dir = root / "small_d2_seed1"
    receipt = run_dir / "preflight.json"
    _passed_receipt(receipt)
    code = e3.main([
        "--row", "small", "--arm", "d2", "--seed", "1",
        "--preflight-receipt", str(receipt), "--output-root", str(root),
        "--launch-commit", "deadbeef", "--rollouts", "1", "--num-envs", "1",
        "--threads", "1", "--horizon", "40", "--eval-interval", "1",
        "--eval-episodes", "4", "--eval-intermediate-episodes", "4",
        "--eval-chunk", "2",
    ])
    assert code == 0
    assert not (run_dir / "QUARANTINED").exists()
    consumed = json.loads(receipt.read_text(encoding="utf-8"))
    assert consumed["external_receipt_sentinel"] == "do-not-overwrite"
    for name in ("summary.json", "preflight.json", "eval.jsonl", "path.jsonl",
                 "checkpoint_final.pt"):
        assert (run_dir / name).exists(), name
    evaluations = [json.loads(line) for line in
                   (run_dir / "eval.jsonl").read_text(encoding="utf-8").splitlines()]
    paths = [json.loads(line) for line in
             (run_dir / "path.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(evaluations) == 1
    assert evaluations[0]["episode_ids"] == [0, 1, 2, 3]
    assert len(evaluations[0]["episode_returns"]) == 4
    assert len(paths) == 1 and set(paths[0]["regional_path"]) == {"0", "1"}
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert "schema_version" not in summary
    assert summary["completed"] is True
    assert summary["row"] == "small" and summary["arm"] == "d2"
    assert summary["transitions_total"] == 40
    assert summary["evaluation_count"] == 1
    assert summary["reference_m_dur"] == summary["references"]["m_dur"]
    assert summary["exposure_line_rollout_1"] == summary["exposure_line_rollout_last"]
    if summary["peak_rss_bytes"] is None:
        assert summary["resource_telemetry_status"] == "resources_unmeasured"
    else:
        assert summary["peak_rss_bytes"] > 0
        assert summary["resource_telemetry_status"] == "measured"
    assert summary["artifact_names"]["preflight"] == "preflight.json"
    assert Path(summary["preflight_receipt_path"]) == receipt.resolve()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "schema_version" not in manifest
    assert "content_sha256" not in manifest["evaluation"]["tapes"]
    assert "digest_recipe" not in manifest["evaluation"]["tapes"]
    assert manifest["evaluation"]["e3_expected_counts"]["final_episodes"] == 2048
    assert manifest["evaluation"]["reduced_from_contract"] is True
