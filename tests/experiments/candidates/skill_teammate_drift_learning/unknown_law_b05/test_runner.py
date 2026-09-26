"""Legal-feedback selection, fixed stage identity and publication checks; no pilot fits."""

from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_skill_drift_unknown_law_b05 as runner
from tools.research_support.interpreters import control_plane_interpreter


@dataclass(frozen=True)
class FixtureSpec:
    family: str
    representation: str = "fixture"
    prior_strength: float = 2.0
    recent_window: int | None = None

    @property
    def id(self):
        return f"{self.family}_{self.prior_strength}"


def fixture_scores(specs, seeds):
    return [{"seed": seed, "setting_id": spec.id, "primary_dr_reward": .5,
             "whole_target_reward_brier": .25}
            for seed in seeds for spec in specs]


@pytest.mark.parametrize("q,truth", [([.4, .7], [.6, .8]), ([.9, .1], [.6, .3]), ([.5, .5], [.6, .9])])
def test_dr_score_expectation_is_chosen_true_value(q, truth):
    greedy = int(q[1] > q[0])
    expected = 0.0
    for action in (0, 1):
        for reward in (0, 1):
            weight = .5 * (truth[action] if reward else 1 - truth[action])
            score = runner.score_feedback([q], [greedy], [action], [reward], [1])
            expected += weight * score["primary_dr_reward"]
    assert expected == pytest.approx(truth[greedy], abs=1e-14)


def test_selection_interface_has_no_truth_and_uses_declared_windows():
    assert set(inspect.signature(runner.score_feedback).parameters) == {
        "predictions", "greedy", "collection_action", "reward", "phase"}
    prediction = np.full((80, 2), .5)
    reward = np.r_[np.zeros(8), np.ones(64), np.zeros(8)]
    score = runner.score_feedback(prediction, np.zeros(80, int), np.zeros(80, int),
                                  reward, np.r_[np.zeros(8, int), np.ones(72, int)])
    assert score["primary_rows"] == 64
    assert score["target_rows"] == 72
    assert score["primary_dr_reward"] == 1.5
    assert score["whole_target_reward_brier"] == .25


def test_selection_rejects_noncausal_choice_inconsistency():
    with pytest.raises(ValueError, match="greedy"):
        runner.score_feedback([[.5, .5]], [1], [1], [1], [1])


def test_mechanical_selection_tie_and_exact_bank_coverage():
    specs = [FixtureSpec(family, prior_strength=alpha)
             for family in runner.FAMILIES for alpha in (2, 16)]
    rows = fixture_scores(specs, (1, 2, 3))
    for row in rows:
        if row["setting_id"].endswith("_16"):
            row["primary_dr_reward"] += 5e-13
            row["whole_target_reward_brier"] = .3
    chosen, _ = runner.choose_settings(rows, specs, (1, 2, 3))
    assert all(row["spec"]["prior_strength"] == 2 for row in chosen.values())
    with pytest.raises(ValueError, match="exactly"):
        runner.choose_settings(rows[:-1], specs, (1, 2, 3))
    with pytest.raises(ValueError, match="exactly"):
        runner.choose_settings(rows + [rows[0]], specs, (1, 2, 3))


def test_main_refuses_wrong_batch_before_admission(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: called.append(True))
    with pytest.raises(SystemExit):
        runner.main(["--stage", "development", "--seeds", "123", "--launch-sha", "a" * 40,
                     "--out", str(tmp_path / "out")])
    assert not called


def test_admission_and_source_are_required_before_scientific_stage(monkeypatch, tmp_path):
    stage_calls = []
    monkeypatch.setattr(runner, "run_stage", lambda *a: stage_calls.append(True))
    arguments = ["--stage", "development", "--seeds", *map(str, runner.DEVELOPMENT_SEEDS),
                 "--launch-sha", "a" * 40, "--out", str(tmp_path / "out")]

    def refuse(*args, **kwargs):
        raise PermissionError("no admission")

    monkeypatch.setattr(runner, "require_admission", refuse)
    with pytest.raises(PermissionError, match="no admission"):
        runner.main(arguments)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "b" * 40})
    with pytest.raises(SystemExit):
        runner.main(arguments)
    assert not stage_calls
    assert not (tmp_path / "out").exists()


def test_literal_guard_passes_real_launcher_inspection_and_constant_does_not(tmp_path):
    source = Path(runner.__file__)
    program = ("from pathlib import Path; import sys; "
               "from scripts.hmasd_launch import _validate_guard_contract; "
               "_validate_guard_contract(Path(sys.argv[1]), 'skill_teammate_drift_learning')")
    prefix = [control_plane_interpreter(), "-B", "-c", program]
    accepted = subprocess.run(prefix + [str(source)], cwd=runner.ROOT,
                              capture_output=True, text=True, timeout=20)
    assert accepted.returncode == 0, accepted.stderr
    broken = tmp_path / "constant_guard.py"
    text = source.read_text()
    replaced = text.replace('direction="skill_teammate_drift_learning")', 'direction=DIRECTION)')
    assert replaced != text
    broken.write_text(replaced)
    refused = subprocess.run(prefix + [str(broken)], cwd=runner.ROOT,
                             capture_output=True, text=True, timeout=20)
    assert refused.returncode != 0
    assert "must contain exactly one" in refused.stderr


def test_selection_tampering_and_digest_fail_before_any_fit(monkeypatch, tmp_path):
    from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05 import study

    bank = study.development_specs()
    config = study.Config()
    rows = fixture_scores(bank, runner.DEVELOPMENT_SEEDS)
    chosen, ranking = runner.choose_settings(rows, bank, runner.DEVELOPMENT_SEEDS)
    selection = {"schema": runner.SELECTION_SCHEMA, "object": runner.OBJECT,
                 "config": runner.asdict(config), "development_seeds": list(runner.DEVELOPMENT_SEEDS),
                 "score_rows": rows, "ranking": ranking, "selected": chosen}
    assert len(runner.validate_selection(selection, config, bank)) == 3
    selection["selected"]["response_all"]["spec"]["prior_strength"] = 99
    with pytest.raises(ValueError, match="mechanical"):
        runner.validate_selection(selection, config, bank)
    source = tmp_path / "selection.json"
    source.write_bytes(runner.json_bytes(selection))
    fits = []
    monkeypatch.setattr(study, "run_block", lambda *a, **k: fits.append(True))
    args = SimpleNamespace(stage="heldout", selection=source, selection_sha256="0" * 64,
                           out=tmp_path / "out", launch_sha="a" * 40, seeds=list(runner.HELDOUT_SEEDS))
    with pytest.raises(ValueError, match="digest mismatch"):
        runner.run_stage(args, {"sha": "a" * 40})
    assert not fits
    assert not args.out.exists()


def test_block_artifacts_retain_arrays_identity_and_digest(tmp_path):
    result = {"summary": {"counts": {"decision_fits": 1}},
              "common": {"reward": np.array([0, 1], np.int8)},
              "fits": {"fixture": {"summary": {"movement": .2},
                                   "curves": {"greedy_action": np.array([0, 1])},
                                   "state": {"estimate": np.array([.4, .7])}}}}
    runner.save_block(tmp_path, result, 17, "fixture", "a" * 40)
    block = tmp_path / "seed_17"
    assert json.loads((block / "summary.json").read_text())["launch_sha"] == "a" * 40
    with np.load(block / "common.npz", allow_pickle=False) as data:
        np.testing.assert_array_equal(data["reward"], [0, 1])
    for relative, digest in json.loads((block / "artifacts.json").read_text()).items():
        assert hashlib.sha256((block / relative).read_bytes()).hexdigest() == digest
