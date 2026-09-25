"""B20 fixed bindings and one reduced real-path pair; no production exposure."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20 import runner
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.bindings import (
    BLOCKS, EVALUATION_ORDER, PRODUCTION_SPEC_VALUES, SCHEDULES, WORLD_SEED_BASES,
)
from scripts import run_agent_count_ordered_roster_confirmation_b20 as entry
from scripts.hmasd_admission import ENVIRONMENT_KEY


TECH_SEED = 9_201_019
TECH_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=EVALUATION_ORDER,
    horizon=20, train_lanes=2, eval_lanes=2, rollouts=4, panels=(0, 4),
    hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
    sequence_batch_size=4, coordinator_batch_size=2, torch_threads=4,
)
TECH_SCHEDULES = {"F": (6, 6, 6, 6), "M": (4, 6, 8, 4)}
TECH_TAG = f"technical_{BLOCKS[1].tag}_s{TECH_SEED}"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def completed_pair(tmp_path_factory):
    out = tmp_path_factory.mktemp("b20-real-path") / TECH_TAG
    initial_agents = []

    def capture(agent):
        initial_agents.append((agent, agent.discoverer_actor_optimizer,
                               agent.discoverer_critic_optimizer))

    code = runner.run_batch(
        out, "technical-b20", {"sha": "technical-b20"}, 1, TECH_SPEC,
        technical_seed=TECH_SEED, schedules=TECH_SCHEDULES, agent_setup_hook=capture,
    )
    assert code == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), initial_agents


def test_fixed_block_seed_world_tag_and_contract():
    assert [(block.number, block.seed, block.training_world_base, block.tag)
            for block in BLOCKS.values()] == [
        (1, 1_016_101, 3_246_100, "s1_ordered_roster_confirmation_b20_b1_s1016101"),
        (2, 1_017_101, 3_346_100, "s1_ordered_roster_confirmation_b20_b2_s1017101"),
        (3, 1_018_101, 3_446_100, "s1_ordered_roster_confirmation_b20_b3_s1018101"),
    ]
    assert WORLD_SEED_BASES == {5: 2_446_500, 7: 2_446_700, 6: 2_446_600}
    assert SCHEDULES == {"F": (6,) * 45, "M": (4, 6, 8) * 15}
    assert runner.jsonable(vars(runner.PRODUCTION_SPEC)) == PRODUCTION_SPEC_VALUES
    assert runner._expected_arm_counts(SCHEDULES["F"], runner.PRODUCTION_SPEC)[
        "training_team_steps"] == 360_000
    assert runner._expected_arm_counts(SCHEDULES["M"], runner.PRODUCTION_SPEC,
                                       common_stage0=True)["evaluation_team_steps"] == 48_000


def test_one_real_reduced_pair_uses_fixed_path_and_persistent_arm_state(completed_pair):
    out, batch, agents = completed_pair
    assert batch["status"] == "complete" and batch["block"] == 1
    assert not batch["production_contract"] and batch["seed"] == TECH_SEED
    assert batch["counts"]["fits"] == 2 and batch["counts"]["panels"] == 9
    assert batch["counts"]["updates"] == 8
    assert batch["counts"]["evaluation_team_steps"] == 9 * 2 * 20
    assert len(agents) == 2 and all(f is not m for f, m in zip(*agents))
    assert all(value for key, value in batch["initial_identity"].items() if key.endswith("_equal"))
    assert batch["initial_identity"]["common_stage0_reused_without_new_steps"]
    assert batch["common_n6_training_world_identity"]["all_equal"]
    for arm, schedule in TECH_SCHEDULES.items():
        summary = _read(out / arm / "summary.json")
        assert summary["spec"]["torch_threads"] == 4
        assert [row["n"] for row in summary["rollouts"]] == list(schedule)
        assert summary["counts"]["training_team_steps"] == 4 * 2 * 20
        assert summary["counts"]["stored_team_steps"] == 4 * 2 * 20
        assert summary["counts"]["training_episodes"] == 8
        assert all(boundary["parameter_values_preserved"] and
                   boundary["optimizer_objects_preserved"] and
                   boundary["optimizer_state_preserved"] and
                   boundary["normalizers_preserved"] and
                   boundary["global_rng_preserved"] and
                   boundary["sampler_rng_preserved"] for boundary in summary["boundaries"])
        stream = summary["training_stream"]
        raw = (out / arm / stream["path"]).read_bytes()
        assert len(raw) == stream["bytes"]
        assert hashlib.sha256(raw).hexdigest() == stream["sha256"]
        assert stream["completed_rows"] == 4
        for rollout, n in enumerate(schedule, start=1):
            identity = summary["training_reset_scenes"][rollout - 1]
            with np.load(out / arm / identity["path"], allow_pickle=False) as scene:
                assert scene["lane_world_seeds"].tolist() == [
                    BLOCKS[1].training_world_base + 10_000_000 + 100 * rollout + lane
                    for lane in range(2)
                ]
                assert int(scene["n"]) == n
        assert summary["source_hashes_unchanged"]
    f = _read(out / "F/summary.json")
    m = _read(out / "M/summary.json")
    assert [row["policy_stage"] for row in f["panels"]] == [0] * 3 + [4] * 3
    assert [row["policy_stage"] for row in m["panels"]] == [4] * 3
    assert not list((out / "M/raw").glob("trace_stage00_n*.npz"))
    for n in EVALUATION_ORDER:
        same_n = [row for row in f["panels"] + m["panels"] if row["test_n"] == n]
        assert len(same_n) == 3
        assert all(row["world_seeds"] == [WORLD_SEED_BASES[n] + 10_000_000 + lane
                                          for lane in range(2)] for row in same_n)
        assert same_n[0]["initial_world_identity"] == same_n[1]["initial_world_identity"] == \
               same_n[2]["initial_world_identity"]
        assert all(not any(row["optimizer_calls"].values()) and
                   row["training_storage_calls"] == 0 for row in same_n)


def test_production_rejects_technical_seed_schedule_or_wrong_tag_before_effects(tmp_path):
    proper = tmp_path / BLOCKS[1].tag
    with pytest.raises(ValueError, match="production seed is fixed"):
        runner.run_batch(proper, "x", {"sha": "x"}, 1,
                         technical_seed=TECH_SEED)
    with pytest.raises(ValueError, match="production schedules are fixed"):
        runner.run_batch(proper, "x", {"sha": "x"}, 1,
                         schedules=TECH_SCHEDULES)
    with pytest.raises(ValueError, match="reduced technical spec needs"):
        runner.run_batch(proper, "x", {"sha": "x"}, 1, TECH_SPEC)
    with pytest.raises(ValueError, match="output basename"):
        runner.run_batch(tmp_path / BLOCKS[2].tag, "x", {"sha": "x"}, 1)
    assert not proper.exists()


def test_cli_checks_block_seed_output_and_admits_before_runner_import(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(entry, "require_admission",
                        lambda *_a, **_k: calls.append("admit") or {"sha": "x"})
    out = tmp_path / BLOCKS[2].tag
    result = entry.main([
        "--block", "2", "--seed", str(BLOCKS[2].seed), "--launch-sha", "x",
        "--out", str(out),
    ], run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 7)
    assert result == 7 and calls[0] == "admit"
    assert calls[1][0][3] == 2
    assert calls[1][1]["command_start"] == entry.COMMAND_START
    calls.clear()
    with pytest.raises(SystemExit):
        entry.main(["--block", "2", "--seed", str(BLOCKS[1].seed),
                    "--launch-sha", "x", "--out", str(out)])
    assert not calls
    environment = dict(os.environ)
    environment.pop(ENVIRONMENT_KEY, None)
    direct = subprocess.run(
        [sys.executable, str(Path(entry.__file__).resolve()), "--block", "2",
         "--seed", str(BLOCKS[2].seed), "--launch-sha", "0" * 40,
         "--out", str(out)], cwd=entry.ROOT, env=environment,
        capture_output=True, text=True, timeout=30,
    )
    assert direct.returncode != 0 and "missing HMASD admission" in direct.stderr
    assert not out.exists()


def test_fresh_cli_process_blocks_scientific_import_until_admission(tmp_path):
    script = """
import importlib.abc
import sys
class RejectScientific(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'numpy' or fullname.startswith('numpy.') or \\
                fullname == 'torch' or fullname.startswith('torch.') or \\
                fullname == 'envs' or fullname.startswith('envs.') or \\
                fullname.startswith('experiments.candidates.agent_count_generalization'):
            raise RuntimeError('scientific import before admission: ' + fullname)
        return None
sys.meta_path.insert(0, RejectScientific())
from scripts import run_agent_count_ordered_roster_confirmation_b20 as entry
assert 'torch' not in sys.modules and 'numpy' not in sys.modules
try:
    entry.main(['--block', '1', '--seed', '1017101', '--launch-sha', 'x',
                '--out', sys.argv[1]])
except SystemExit:
    pass
else:
    raise AssertionError('wrong seed was admitted')
def refuse(*args, **kwargs):
    raise RuntimeError('native admission reached')
entry.require_admission = refuse
try:
    entry.main(['--block', '1', '--seed', '1016101', '--launch-sha', 'x',
                '--out', sys.argv[1]])
except RuntimeError as error:
    assert str(error) == 'native admission reached', error
else:
    raise AssertionError('native admission was skipped')
assert 'torch' not in sys.modules and 'numpy' not in sys.modules
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path / BLOCKS[1].tag)],
        cwd=entry.ROOT, capture_output=True, text=True, timeout=30,
    )
    assert process.returncode == 0, process.stderr


def test_failed_f_stops_pair_and_records_m_unstarted(tmp_path):
    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    out = tmp_path / TECH_TAG

    def fail(agent):
        def first_step(*_args, **_kwargs):
            raise RuntimeError("technical B20 first-step failure")
        agent.step = first_step

    assert runner.run_batch(out, "technical-fail", {"sha": "technical-fail"}, 1,
                            one, technical_seed=TECH_SEED,
                            schedules={"F": (6,), "M": (4,)},
                            agent_setup_hook=fail) == 1
    f = _read(out / "F/summary.json")
    m = _read(out / "M/summary.json")
    assert f["status"] == "failed" and f["counts"]["training_team_steps"] == 0
    assert f["incomplete_rollout"]["_telemetry"]["executed_min"] is None
    assert m["status"] == "unstarted" and not m["fit_started"]
