"""Synthetic publication, dispatch and failure checks for B04."""

import json

import pytest

from experiments.candidates.ucope.scalar_feedback_b04 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def admission():
    return {
        "schema_version": 1,
        "direction": "ucope",
        "sha": "admitted-sha",
        "command_sha256": "command-digest",
        "parent_pid": 41,
        "child_pid": 42,
        "accepted_at_epoch": 123.5,
    }


def test_complete_fixture_dispatches_b_and_g_and_preserves_evidence(tmp_path):
    out = tmp_path / "complete"
    result = study.run(study.Config.engineering(), out, admission())

    assert result["status"] == "COMPLETE"
    assert result["object"] == "UCOPE_SCALAR_FEEDBACK_B04"
    assert result["launch_sha"] == result["admission"]["sha"] == "admitted-sha"
    assert result["admission"] == admission()
    assert "node" not in result["admission"]
    assert result["declared_execution_node"] == "local_linux"
    assert result["selected_masters"] == [8931, 8932, 8933]

    panel = result["panel"]
    assert panel["selected_contrast"] == "B_minus_G"
    assert panel["primary"] == panel["B_minus_G"]
    assert panel["complete"] and panel["all_panels_complete"]
    for arm in ("B", "G", "H"):
        assert len(panel["returns"][arm]) == 3
    for name in ("B_minus_G", "B_minus_H", "G_minus_H"):
        assert panel[name]["complete"]
        assert panel[name]["episode_ids"] == [0, 1, 2]
        assert len(panel[name]["differences"]) == 3
    assert "fresh innovations" in panel["interpretation"]
    assert "recurrent action means" in panel["interpretation"]

    accounting = result["fit_accounting"]
    assert accounting["allocated_fit_arms"] == ["B", "G"]
    assert accounting["allocated_fits_this_invocation"] == 2
    assert accounting["allocated_fits_complete_batch"] == 6
    assert accounting["exact_started_fits"] == 2
    assert accounting["completed_training_fits"] == 2

    counts = result["counts"]
    assert counts["train_episodes"] == 8
    assert counts["train_team_steps"] == 64
    assert counts["eval_episodes"] == 9
    assert counts["eval_team_steps"] == 72
    assert counts["team_steps"] == 136
    assert counts["optimizer_steps"] == 16
    assert result["evaluation_optimizer_steps"] == 0

    for arm in ("B", "G"):
        record = result["arms"][arm]
        assert record["train_complete"] and record["eval_complete"]
        assert record["evaluation_optimizer_steps"] == 0
        assert record["evaluation_parameter_exposure"]["total"]["displacement"] == 0
        assert record["training_generators_unchanged_by_evaluation"]
        assert record["exposure"]["common_actor"]["displacement"] > 0
        assert record["exposure"]["critic"]["displacement"] > 0
        assert record["checkpoint"]["present"] and record["checkpoint"]["sha256"]

    b_record, g_record = result["arms"]["B"], result["arms"]["G"]
    assert b_record["exposure"]["duration"]["parameters"] == 2
    assert b_record["exposure"]["duration"]["relative_displacement"] is None
    assert b_record["exposure"]["duration"]["displacement"] > 0
    assert b_record["endpoint_gate"]["input_independent"]
    assert sum(b_record["endpoint_gate"]["probabilities"]) == pytest.approx(1.0)
    assert b_record["gate_activity"]["train_gate_decisions"] > 0
    assert g_record["gate_activity"] is None
    assert "duration" not in g_record["exposure"]
    assert not g_record["endpoint_gate"]["present"]
    assert g_record["endpoint_gate"]["probabilities"] is None
    assert g_record["ordinary_activity"]["train_velocity_decisions"] == 160
    assert g_record["ordinary_activity"]["eval_velocity_decisions"] == 120
    assert g_record["ordinary_activity"]["train_duration_decisions"] == 0

    episode_rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    update_rows = [json.loads(line) for line in (out / "updates.jsonl").read_text().splitlines()]
    assert len(episode_rows) == 17 and len(update_rows) == 4
    assert all("gate_decisions" in row for row in episode_rows if row["arm"] == "B")
    assert all("duration_decisions" not in row for row in episode_rows if row["arm"] == "B")
    assert all("duration_decisions" in row for row in episode_rows if row["arm"] == "G")
    assert all("gate_decisions" not in row for row in episode_rows if row["arm"] == "G")
    assert all(
        "entropy" not in epoch
        for row in update_rows if row["arm"] == "B"
        for epoch in row["epochs"]
    )
    assert all(
        "entropy" in epoch
        for row in update_rows if row["arm"] == "G"
        for epoch in row["epochs"]
    )
    base = study.Config.engineering().seed * 100000
    for arm in ("B", "G", "H"):
        assert [
            row["reset_seed"] for row in episode_rows
            if row["arm"] == arm and row["phase"] == "eval"
        ] == [base + 20000 + episode for episode in range(3)]
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"
    assert all(result["artifacts"]["checkpoints"][arm]["present"] for arm in ("B", "G"))


def test_late_failure_retains_full_vectors_without_complete_result(tmp_path):
    class FailSecondClose(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances

        def close(self):
            if self.number == 2:
                raise RuntimeError("late close failure")

    result = study.run(
        study.Config.engineering(),
        tmp_path / "late-failure",
        admission(),
        factory=lambda seed: FailSecondClose(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["type"] == "RuntimeError"
    assert result["panel"]["all_panels_complete"]
    assert not result["panel"]["complete"]
    for name in ("B_minus_G", "B_minus_H", "G_minus_H"):
        assert result["panel"][name]["panel_complete"]
        assert not result["panel"][name]["complete"]
        assert result["panel"][name]["differences"]
    assert result["fit_accounting"]["exact_started_fits"] is None
    assert result["fit_accounting"]["completed_training_fits"] == 2


def test_g_constructor_failure_publishes_b_evidence_and_partial_accounting(tmp_path):
    calls = 0

    def factory(seed):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("G constructor failure")
        return SyntheticAdapter(seed, 8)

    out = tmp_path / "partial"
    result = study.run(
        study.Config.engineering(), out, admission(), factory=factory
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["message"] == "G constructor failure"
    assert not result["panel"]["all_panels_complete"]
    assert not result["panel"]["complete"]
    assert len(result["panel"]["returns"]["B"]) == 3
    assert result["panel"]["returns"]["G"] == []
    assert result["fit_accounting"]["observed_training_activity_arms"] == ["B"]
    assert result["fit_accounting"]["scientific_constructor_arms"] == ["B"]
    assert result["fit_accounting"]["exact_started_fits"] is None
    assert result["artifacts"]["checkpoints"]["B"]["present"]
    assert not result["artifacts"]["checkpoints"]["G"]["present"]
    assert json.loads((out / "summary.json").read_text())["status"] == "INCOMPLETE"


def test_scope_refuses_unselected_or_modified_config():
    for config in (
        study.Config(seed=8930),
        study.Config(seed=8934),
        study.Config(seed=8931, horizon=255),
        study.Config(seed=8931, train_episodes=2046),
        study.Config(seed=8931, eval_episodes=63),
        study.Config(seed=8931, chunk=16),
        study.Config(seed=8931, watchdog_seconds=5999),
    ):
        with pytest.raises(ValueError):
            study.require_config(config)
    with pytest.raises(ValueError, match="fixed engineering fixture"):
        study.require_config(study.Config(seed=9931, horizon=9, fixture=True))
