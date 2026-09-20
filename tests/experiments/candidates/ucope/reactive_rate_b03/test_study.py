"""Synthetic publication and failure-accounting checks for B03."""

import json

import pytest

from experiments.candidates.ucope.reactive_rate_b03 import study
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


def test_small_complete_study_preserves_fixed_scope_and_scientific_evidence(tmp_path):
    out = tmp_path / "complete"
    result = study.run(study.Config.engineering(), out, admission())

    assert result["status"] == "COMPLETE"
    assert result["object"] == "UCOPE_REACTIVE_RATE_B03"
    assert result["notebook"] == "docs/research/candidates/ucope/NOTES.md"
    assert result["launch_sha"] == result["admission"]["sha"] == "admitted-sha"
    assert result["admission"] == admission()
    assert "node" not in result["admission"]
    assert result["declared_execution_node"] == "local_linux"
    assert "launch manifest" in result["node_evidence_scope"]
    assert result["selected_masters"] == [8921, 8922, 8923]

    panel = result["panel"]
    assert panel["selected_contrast"] == "R_minus_B"
    assert panel["primary"] == panel["R_minus_B"]
    assert panel["complete"] and panel["all_panels_complete"]
    for arm in ("R", "B", "H"):
        assert len(panel["returns"][arm]) == 3
    for name in ("R_minus_B", "R_minus_H", "B_minus_H"):
        assert panel[name]["complete"]
        assert panel[name]["episode_ids"] == [0, 1, 2]
        assert len(panel[name]["differences"]) == 3
    assert "significance" not in panel and "equivalence" not in panel

    accounting = result["fit_accounting"]
    assert accounting["allocated_fit_arms"] == ["R", "B"]
    assert accounting["allocated_fits_this_invocation"] == 2
    assert accounting["allocated_fits_complete_batch"] == 6
    assert accounting["exact_started_fits"] == 2
    assert accounting["completed_training_fits"] == 2
    assert accounting["observed_training_activity_arms"] == ["R", "B"]

    assert result["counts"]["train_episodes"] == 8
    assert result["counts"]["train_team_steps"] == 64
    assert result["counts"]["eval_episodes"] == 9
    assert result["counts"]["eval_team_steps"] == 72
    assert result["counts"]["team_steps"] == 136
    assert result["counts"]["optimizer_steps"] == 16
    assert result["evaluation_optimizer_steps"] == 0
    assert result["arms"]["H"]["evaluation_optimizer_steps"] == 0

    for arm in ("R", "B"):
        record = result["arms"][arm]
        assert record["train_complete"] and record["eval_complete"]
        assert record["evaluation_optimizer_steps"] == 0
        assert record["evaluation_parameter_exposure"]["total"]["displacement"] == 0
        assert record["training_generators_unchanged_by_evaluation"]
        assert record["exposure"]["total"]["displacement"] > 0
        assert record["checkpoint"]["present"]
        assert record["checkpoint"]["sha256"]
        assert record["gate_activity"]["train_gate_decisions"] > 0
        assert record["gate_activity"]["train_final_gate_credit_decisions"] > 0

    scalar = result["arms"]["B"]
    assert scalar["exposure"]["duration"]["parameters"] == 2
    assert scalar["exposure"]["duration"]["relative_displacement"] is None
    assert scalar["exposure"]["duration"]["displacement"] > 0
    assert scalar["endpoint_gate"]["input_independent"]
    assert sum(scalar["endpoint_gate"]["probabilities"]) == pytest.approx(1.0)
    assert result["arms"]["R"]["endpoint_gate"]["mean_probabilities"] is None
    assert "not retained" in result["arms"]["R"]["endpoint_gate"]["qualification"]

    assert result["telemetry"]["wall_seconds"] >= 0
    assert result["telemetry"]["process_cpu_seconds"] >= 0
    assert result["telemetry"]["complete_process_exit_wall"] is None
    assert all(result["artifacts"]["checkpoints"][arm]["present"] for arm in ("R", "B"))
    episode_rows = [
        json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()
    ]
    assert len(episode_rows) == 17
    base = study.Config.engineering().seed * 100000
    for arm in ("R", "B", "H"):
        assert [
            row["reset_seed"]
            for row in episode_rows
            if row["arm"] == arm and row["phase"] == "eval"
        ] == [base + 20000 + episode for episode in range(3)]
    for arm in ("R", "B"):
        assert [
            row["reset_seed"]
            for row in episode_rows
            if row["arm"] == arm and row["phase"] == "train"
        ] == [base + 10000 + episode for episode in range(4)]
    assert len((out / "updates.jsonl").read_text().splitlines()) == 4
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"


def test_late_failure_keeps_vectors_but_never_publishes_complete_result(tmp_path):
    class FailSecondClose(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances

        def close(self):
            if self.number == 2:
                raise RuntimeError("late close failure")

    def factory(seed):
        return FailSecondClose(seed, study.Config.engineering().horizon)

    result = study.run(
        study.Config.engineering(),
        tmp_path / "late-failure",
        admission(),
        factory=factory,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["error"]["type"] == "RuntimeError"
    assert result["panel"]["all_panels_complete"]
    assert not result["panel"]["complete"]
    for name in ("R_minus_B", "R_minus_H", "B_minus_H"):
        assert result["panel"][name]["panel_complete"]
        assert not result["panel"][name]["complete"]
        assert result["panel"][name]["differences"]
    accounting = result["fit_accounting"]
    assert accounting["exact_started_fits"] is None
    assert accounting["completed_training_fits"] == 2
    assert accounting["observed_training_activity_arms"] == ["R", "B"]
    assert all(result["artifacts"]["checkpoints"][arm]["present"] for arm in ("R", "B"))


def test_scope_rejects_unselected_or_modified_scientific_config():
    for config in (
        study.Config(seed=8920),
        study.Config(seed=8924),
        study.Config(seed=8921, horizon=255),
        study.Config(seed=8921, train_episodes=2046),
        study.Config(seed=8921, eval_episodes=63),
        study.Config(seed=8921, chunk=16),
        study.Config(seed=8921, watchdog_seconds=5999),
    ):
        with pytest.raises(ValueError):
            study.require_config(config)
    with pytest.raises(ValueError, match="fixed engineering fixture"):
        study.require_config(study.Config(seed=9921, horizon=9, fixture=True))
