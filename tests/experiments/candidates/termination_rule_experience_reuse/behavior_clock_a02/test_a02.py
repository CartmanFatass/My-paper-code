"""Correctness fixtures only: no A02 learning result or seed selection."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

import numpy as np
import pytest

from experiments.candidates.termination_rule_experience_reuse.behavior_clock_a02 import study
from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.host import (
    STATE_COUNT,
    behavior_episode,
)
from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.learning import (
    forward_targets,
)
from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.study import (
    LIMITS as A01_LIMITS,
    OBJECT as A01_OBJECT,
    Config,
    run_study as produce_study,
)


@pytest.mark.parametrize(
    ("arm", "zeta", "same_probability", "changed_probability"),
    [
        ("long_behavior", .125, .9375, .0625),
        ("matched_termination", .5, .75, .25),
    ],
)
def test_fixed_laws_and_actual_conditional_support(
        arm, zeta, same_probability, changed_probability):
    config = study.make_config(arm, 91031)
    assert config == Config(arm="retrace", seed=91031, zeta=zeta)
    assert (
        config.train_episodes, config.horizon, config.eval_episodes,
        config.checkpoints, config.chunk, config.gamma, config.alpha, config.beta,
    ) == (512, 96, 64, (0, 32, 128, 512), 8, .95, 1., .5)
    assert config.train_episodes * config.horizon == 49_152
    assert config.train_episodes * (config.horizon // config.chunk) == 6_144
    assert len(config.checkpoints) * config.eval_episodes * config.horizon == 24_576
    episode = behavior_episode(91031, 0, 256, zeta)
    expected = np.where(
        episode.options[1:] == episode.options[:-1],
        same_probability,
        changed_probability,
    )
    np.testing.assert_array_equal(episode.next_option_probability, expected)
    assert set(np.unique(episode.next_option_probability)) == {
        same_probability, changed_probability,
    }
    # A same-label redraw is an actual renewal whose recorded denominator remains marginal.
    same_label_redraw = episode.renewed & (episode.options[1:] == episode.options[:-1])
    assert same_label_redraw.any()
    np.testing.assert_array_equal(
        episode.next_option_probability[same_label_redraw], same_probability,
    )
    values = forward_targets(
        np.zeros((STATE_COUNT, 2)), episode, 0, len(episode.rewards),
        "retrace", config.gamma, config.beta,
    )
    target_probability = np.where(
        episode.options[1:-1] == episode.options[:-2], .75, .25,
    )
    np.testing.assert_array_equal(
        values["raw_ratios"], target_probability / episode.next_option_probability[:-1],
    )
    np.testing.assert_array_equal(
        values["coefficients"][1:], np.minimum(1., values["raw_ratios"]),
    )


def test_a02_rejects_undeclared_arm_and_seed():
    with pytest.raises(ValueError, match="invalid A02 arm/seed"):
        study.make_config("retrace", 91031)
    with pytest.raises(ValueError, match="invalid A02 arm/seed"):
        study.make_config("long_behavior", 91021)


@pytest.mark.parametrize(
    ("arm", "zeta"),
    [("long_behavior", .125), ("matched_termination", .5)],
)
def test_a02_artifact_identity_counts_and_distinct_trajectory_limit(
        tmp_path, monkeypatch, arm, zeta):
    fixture_config = Config(
        arm="retrace", seed=42, zeta=zeta, train_episodes=2, horizon=4,
        chunk=2, eval_episodes=2, checkpoints=(0, 1, 2),
    )
    monkeypatch.setattr(study, "make_config", lambda actual_arm, seed: fixture_config)
    admission = {"direction": "termination_rule_experience_reuse", "sha": "a" * 40}
    out = tmp_path / arm
    result = study.run_study(arm, 91031, out, admission, time.monotonic())

    expected_identity = {
        "object": study.OBJECT, "arm": arm, "learner": "retrace", "seed": 42,
    }
    config_json = json.loads((out / "config.json").read_text())
    status_json = json.loads((out / "status.json").read_text())
    for artifact in (config_json, status_json, result):
        assert {key: artifact[key] for key in expected_identity} == expected_identity
    assert config_json["config"]["arm"] == "retrace"
    assert config_json["config"]["zeta"] == zeta
    assert result["limits"] == list(study.LIMITS)
    assert "observed behavior trajectories differ" in " ".join(result["limits"])
    assert result["counts"] == {
        "started_fits": 1, "train_episodes": 2, "train_team_steps": 8,
        "evaluation_episodes": 6, "evaluation_team_steps": 24,
        "tabular_update_calls": 4, "target_rows": 8,
        "table_entries_written": result["counts"]["table_entries_written"],
        "evaluation_new_updates": 0, "gradient_optimizer_steps": 0,
    }
    for item in result["artifacts"]:
        path = out / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_a01_default_artifact_identity_and_limits_are_unchanged(tmp_path):
    config = Config(
        arm="retrace", seed=42, train_episodes=1, horizon=2,
        chunk=2, eval_episodes=1, checkpoints=(0, 1),
    )
    admission = {"direction": "termination_rule_experience_reuse", "sha": "b" * 40}
    out = tmp_path / "a01-default"
    result = produce_study(config, out, admission)
    config_json = json.loads((out / "config.json").read_text())
    status_json = json.loads((out / "status.json").read_text())
    expected_identity = {
        "object": A01_OBJECT, "arm": "retrace", "learner": "retrace", "seed": 42,
    }
    for artifact in (config_json, status_json, result):
        assert {key: artifact[key] for key in expected_identity} == expected_identity
    assert result["limits"] == list(A01_LIMITS)


def test_runner_guard_contract_and_missing_admission_refuse_before_output(tmp_path):
    from scripts import hmasd_launch

    repo = Path(__file__).resolve().parents[5]
    runner = repo / "scripts/run_termination_reuse_a02.py"
    hmasd_launch._validate_guard_contract(runner, "termination_rule_experience_reuse")
    source = runner.read_text()
    assert source.index("admission = require_admission") < source.index(
        "from experiments.candidates.termination_rule_experience_reuse.behavior_clock_a02"
    )

    out = tmp_path / "never-created"
    env = dict(os.environ)
    env.pop("HMASD_ADMISSION_V1", None)
    process = subprocess.run(
        [sys.executable, str(runner), "--arm", "long_behavior", "--seed", "91031",
         "--out", str(out), "--launch-sha", "c" * 40],
        capture_output=True, text=True, env=env, cwd=repo, timeout=20,
    )
    assert process.returncode != 0
    assert "missing HMASD admission" in process.stderr
    assert not out.exists()


def test_runner_rejects_source_mismatch_before_scientific_import(tmp_path, monkeypatch):
    from scripts import run_termination_reuse_a02 as runner

    monkeypatch.setattr(
        runner, "require_admission",
        lambda *_args, **_kwargs: {
            "direction": "termination_rule_experience_reuse", "sha": "d" * 40,
        },
    )
    scientific_module = (
        "experiments.candidates.termination_rule_experience_reuse.behavior_clock_a02.study"
    )
    sys.modules.pop(scientific_module, None)
    out = tmp_path / "never-created"
    with pytest.raises(SystemExit) as exc:
        runner.main([
            "--arm", "matched_termination", "--seed", "91032",
            "--out", str(out), "--launch-sha", "e" * 40,
        ])
    assert exc.value.code == 2
    assert scientific_module not in sys.modules
    assert not out.exists()


def test_runner_admitted_command_and_final_witness_use_artifact_identity(
        tmp_path, monkeypatch, capsys):
    from scripts import run_termination_reuse_a02 as runner

    admission = {
        "direction": "termination_rule_experience_reuse", "sha": "f" * 40,
    }
    monkeypatch.setattr(runner, "require_admission", lambda *_args, **_kwargs: admission)
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        monkeypatch.setenv(key, "fixture-before")
    captured = {}
    scientific_module = (
        "experiments.candidates.termination_rule_experience_reuse.behavior_clock_a02.study"
    )
    fake_study = types.ModuleType(scientific_module)

    def fake_run_study(arm, seed, out, actual_admission, start):
        captured.update(
            arm=arm, seed=seed, out=out, admission=actual_admission, start=start,
        )
        return {"status": "COMPLETE", "arm": arm, "learner": "retrace"}

    fake_study.run_study = fake_run_study
    monkeypatch.setitem(sys.modules, scientific_module, fake_study)
    out = tmp_path / "not-produced-by-stub"
    assert runner.main([
        "--arm", "matched_termination", "--seed", "91033",
        "--out", str(out), "--launch-sha", "f" * 40,
    ]) == 0
    assert captured == {
        "arm": "matched_termination", "seed": 91033, "out": out,
        "admission": admission, "start": captured["start"],
    }
    assert isinstance(captured["start"], float)
    assert capsys.readouterr().out.strip() == (
        "status=COMPLETE arm=matched_termination learner=retrace seed=91033"
    )
