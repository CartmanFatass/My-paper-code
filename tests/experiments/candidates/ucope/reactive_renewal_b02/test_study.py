"""Synthetic publication checks for the thin B02 study adapter."""

import json

from experiments.candidates.ucope.reactive_renewal_b01 import study as b01
from experiments.candidates.ucope.reactive_renewal_b02 import study


def inherited_summary(status="COMPLETE", launch_sha="admitted-sha", seed=8911):
    rows = []
    values = {
        "R": [3.0 + episode / 100 for episode in range(64)],
        "F": [2.0 + episode / 100 for episode in range(64)],
        "G": [1.0 + episode / 200 for episode in range(64)],
        "H": [0.0 for _ in range(64)],
    }
    for arm, returns in values.items():
        for episode, value in enumerate(returns):
            rows.append(
                {"arm": arm, "phase": "eval", "episode": episode, "J": value}
            )
    arms = {}
    for index, arm in enumerate(("R", "F", "G")):
        arms[arm] = {
            "counts": {
                "constructors": 1,
                "train_episodes": 2048 if index < 2 or status == "COMPLETE" else 0,
                "train_team_steps": 524288 if index < 2 or status == "COMPLETE" else 0,
                "optimizer_steps": 4096 if index < 2 or status == "COMPLETE" else 0,
                "eval_episodes": 64 if index < 2 or status == "COMPLETE" else 0,
                "eval_team_steps": 16384 if index < 2 or status == "COMPLETE" else 0,
            },
            "train_complete": index < 2 or status == "COMPLETE",
            "eval_complete": index < 2 or status == "COMPLETE",
            "exposure": {"total": {"displacement": float(index + 1)}},
            "evaluation_parameter_exposure": {"total": {"displacement": 0.0}},
        }
    arms["H"] = {"counts": {}, "trained": False, "eval_complete": True}
    return {
        "object": b01.OBJECT,
        "card": b01.CARD,
        "configuration": {
            "seed": seed,
            "horizon": 256,
            "train_episodes": 2048,
            "eval_episodes": 64,
            "chunk": 32,
            "watchdog_seconds": 6000,
            "fixture": False,
        },
        "seed": seed,
        "launch_sha": launch_sha,
        "status": status,
        "arms": arms,
        "new_fits": 3,
        "counts": {},
        "limits": [],
        "elapsed_wall_seconds": 12.0,
        "aggregate_process_cpu_seconds": 5.0,
        "resource_note": "inherited resource scope",
        "panel": b01.final_panel(rows, 64, status == "COMPLETE"),
    }


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


def create_artifacts(out, arms=("R", "F", "G")):
    out.mkdir()
    (out / "episodes.jsonl").write_text("{}\n")
    (out / "updates.jsonl").write_text("{}\n")
    for arm in arms:
        (out / f"{arm}_final.pt").write_bytes(b"checkpoint")


def test_complete_summary_relabels_primary_and_preserves_vectors_and_exposure(tmp_path):
    out = tmp_path / "complete"
    create_artifacts(out)
    original = inherited_summary()
    expected_returns = dict(original["panel"]["returns"])
    expected_r_g = list(original["panel"]["R_minus_G"]["differences"])
    result = study.adapt_summary(original, out, admission())

    assert result["object"] == "UCOPE_REACTIVE_RENEWAL_B02"
    assert result["source_object"] == b01.OBJECT
    assert result["notebook"] == "docs/research/candidates/ucope/NOTES.md"
    assert result["launch_sha"] == result["admission"]["sha"] == "admitted-sha"
    assert result["declared_execution_node"] == "local_linux"
    assert "launch manifest" in result["node_evidence_scope"]
    assert result["admission"] == admission()
    assert "node" not in result["admission"]
    assert result["selected_masters"] == [8911, 8912]
    assert "new_fits" not in result

    panel = result["panel"]
    assert panel["selected_contrast"] == "R_minus_G"
    assert panel["primary"] == panel["R_minus_G"]
    assert panel["primary"]["differences"] == expected_r_g
    assert panel["secondary"]["R_minus_F"] == panel["R_minus_F"]
    assert panel["secondary"]["F_minus_G"] == panel["F_minus_G"]
    assert panel["returns"] == expected_returns
    assert "reading" not in panel and "categorical_mei_reading" not in panel
    assert panel["complete"] and panel["primary"]["complete"]

    accounting = result["fit_accounting"]
    assert accounting["allocated_fits_this_invocation"] == 3
    assert accounting["allocated_fits_complete_batch"] == 6
    assert accounting["exact_started_fits"] == 3
    assert accounting["completed_training_fits"] == 3
    assert result["evaluation_optimizer_steps"] == 0
    assert result["telemetry"]["wall_seconds"] == 12.0
    assert result["telemetry"]["process_cpu_seconds"] == 5.0
    assert result["telemetry"]["peak_rss_kib"] > 0
    assert result["telemetry"]["complete_process_exit_wall"] is None
    assert "does not invalidate" in result["resource_note"]
    assert result["arms"]["R"]["exposure"]["total"]["displacement"] == 1.0
    assert all(item["present"] for item in result["artifacts"]["checkpoints"].values())


def test_incomplete_invocation_never_publishes_complete_comparison(tmp_path):
    out = tmp_path / "incomplete"
    create_artifacts(out, arms=("R", "F"))
    # Deliberately retain all final-panel rows while the invocation is incomplete.
    result = study.adapt_summary(inherited_summary("INCOMPLETE"), out, admission())
    panel = result["panel"]
    assert panel["all_panels_complete"]
    assert not panel["complete"]
    for name in (
        "R_minus_F",
        "R_minus_G",
        "R_minus_H",
        "F_minus_H",
        "G_minus_H",
        "F_minus_G",
    ):
        assert panel[name]["panel_complete"]
        assert not panel[name]["complete"]
        assert panel[name]["differences"]
    accounting = result["fit_accounting"]
    assert accounting["exact_started_fits"] is None
    assert accounting["observed_training_activity_arms"] == ["R", "F"]
    assert accounting["observed_training_activity_fit_lower_bound"] == 2
    assert accounting["scientific_constructor_arms"] == ["R", "F", "G"]
    assert accounting["per_arm"]["G"]["activity"]["optimizer_steps"] == 0
    assert not result["artifacts"]["checkpoints"]["G"]["present"]


def test_run_delegates_one_exact_fixed_config_and_rewrites_summary(tmp_path, monkeypatch):
    captured = []

    def fake_run(config, out, start=None):
        captured.append((config, out, start))
        create_artifacts(out)
        return inherited_summary(launch_sha="admitted-sha", seed=config.seed)

    monkeypatch.setattr(study.b01, "run", fake_run)
    out = tmp_path / "delegated"
    result = study.run(8912, out, admission(), start=12.5)
    config, observed_out, observed_start = captured.pop()
    assert observed_out == out and observed_start == 12.5
    assert (
        config.seed,
        config.horizon,
        config.train_episodes,
        config.eval_episodes,
        config.chunk,
        config.fixture,
    ) == (8912, 256, 2048, 64, 32, False)
    assert result["object"] == study.OBJECT
    written = json.loads((out / "summary.json").read_text())
    assert written["object"] == study.OBJECT
    assert written["panel"]["selected_contrast"] == "R_minus_G"


def test_scope_and_source_identity_refuse_foreign_inputs(tmp_path):
    for master in (8910, 8913):
        try:
            study.config_for(master)
        except ValueError as error:
            assert "prospectively selected" in str(error)
        else:
            raise AssertionError("foreign master accepted")
    summary = inherited_summary()
    summary["object"] = "foreign"
    try:
        study.adapt_summary(summary, tmp_path, admission())
    except ValueError as error:
        assert "foreign source study" in str(error)
    else:
        raise AssertionError("foreign source study accepted")
