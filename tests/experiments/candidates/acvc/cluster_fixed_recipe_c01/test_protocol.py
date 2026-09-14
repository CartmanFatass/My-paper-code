"""Synthetic C01 routing, record validation and inference checks; no learner run."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.acvc.cluster_fixed_recipe_c01 import protocol as p


def inference_units(fc=None, fd=None):
    fc = fc or [.03, .04, .05, .06, .07, .08]
    fd = fd or [.02, .03, .04, .05, .06, .07]
    return [
        {
            "unit_index": unit,
            "master": master,
            "evaluation_namespace": namespace,
            "complete": True,
            "issues": [],
            "contrasts": {
                "F-C": {"mean_J": fc[index]},
                "F-dwell": {"mean_J": fd[index]},
                "dwell-C": {"mean_J": fc[index] - fd[index]},
            },
        }
        for index, (unit, master, namespace) in enumerate(p.UNITS)
    ]


def test_df5_sqrt6_joint_boundaries_and_adverse_unit_retention():
    units = inference_units()
    units[0]["contrasts"]["F-C"]["mean_J"] = -0.25
    result = p.aggregate(units, "a" * 40)
    assert result["complete"]
    assert result["t_quantile"] == {
        "probability": .9875,
        "df": 5,
        "value": pytest.approx(p.CRITICAL, abs=1e-15),
        "frozen_reference": p.CRITICAL,
        "n_units": 6,
    }
    observed = result["primary"]["F-C"]
    assert observed["unit_means_J"][0] == -.25
    assert observed["fit_panel_SE_J"] == pytest.approx(
        __import__("statistics").stdev(observed["unit_means_J"]) / math.sqrt(6)
    )
    assert result["joint_reading"] == "JOINT_NOT_ESTABLISHED"
    favorable = p.aggregate(inference_units([.10, .11, .12, .13, .14, .15],
                                             [.08, .09, .10, .11, .12, .13]), "a" * 40)
    assert favorable["joint_reading"] == "JOINT_ABOVE_MEI"
    assert "iid-normal" in favorable["qualification"]
    assert "calibration is not established" in favorable["qualification"]


@pytest.mark.parametrize("lower,upper,reading", [
    (-.03, -.00001, "BELOW_ZERO"),
    (-.03, 0.0, "AT_OR_BELOW_MEI"),
    (-.01, .01, "AT_OR_BELOW_MEI"),
    (.01, .04, "UNRESOLVED"),
    (.01000001, .04, "ABOVE_MEI"),
    (-.01, .04, "UNRESOLVED"),
])
def test_exact_interval_boundaries(lower, upper, reading):
    assert p.interval_reading(lower, upper) == reading


def test_zero_variance_and_incomplete_have_no_inferential_substitute():
    zero = p.aggregate(inference_units([.02] * 6, [.03] * 6), "b" * 40)
    for item in zero["primary"].values():
        assert item["reading"] == "ZERO_VARIANCE_UNRESOLVED"
        assert item["lower_J"] is None and item["upper_J"] is None
    assert zero["joint_reading"] == "JOINT_NOT_ESTABLISHED"
    for candidate in (inference_units()[:5], list(reversed(inference_units()))):
        result = p.aggregate(candidate, "b" * 40)
        assert not result["complete"]
        assert result["primary"] is None and result["joint_reading"] == "INCOMPLETE"
    incomplete = inference_units()
    incomplete[2]["complete"] = False
    result = p.aggregate(incomplete, "b" * 40)
    assert not result["complete"] and result["units"][2] is incomplete[2]


def test_index_identity_allows_repeated_numeric_pairs(monkeypatch):
    repeated = tuple((index, 12000, 22000) for index in range(1, 7))
    monkeypatch.setattr(p, "UNITS", repeated)
    units = inference_units()
    result = p.aggregate(units, "c" * 40)
    assert result["complete"]
    assert [unit["unit_index"] for unit in result["units"]] == list(range(1, 7))


def write_synthetic_unit(root, *, unit_index=1, launch_sha="d" * 40):
    _, master, namespace = p.UNITS[unit_index - 1]
    path = root / f"unit_{unit_index:02d}"
    path.mkdir(parents=True)
    counts = {
        "train_episodes": 1024,
        "eval_episodes": 192,
        "train_team_steps": 262144,
        "eval_team_steps": 49152,
        "optimizer_steps": 2048,
        "backward_calls": 2048,
        "update_records": 2048,
        "rollouts": 512,
        "new_fits": 1,
        "final_checkpoints": 1,
        "selected_final_checkpoints": 1,
        "post_fit_loads": 3,
        "environment_constructors": 4,
    }
    configuration = {
        "horizon": 256,
        "training_episodes": 1024,
        "episodes_per_rollout": 2,
        "ppo_epochs_per_rollout": 4,
        "chunk": 32,
        "evaluation_episodes_per_arm": 64,
        "evaluation_order": list(p.ARMS),
        "ratio_grouping": "agent_compound",
        "value_moments": None,
        "renewal": False,
        "duration_support": [1, 4],
        "velocity_mode": "sampled",
        "entropy_coef": .01,
        "device": "cpu",
        "dtype": "float32",
        "intraop_threads": 1,
        "interop_threads": 1,
        "training_rule": "C",
        "user_distribution": "cluster",
        "fixed_recipe": "clustered_C_only_1024_final_only",
        "unit_index": unit_index,
    }
    summary = {
        "object": p.OBJECT,
        "unit_index": unit_index,
        "master": master,
        "evaluation_namespace": namespace,
        "indexed_identity": {
            "unit_index": unit_index,
            "master": master,
            "evaluation_namespace": namespace,
        },
        "launch_sha": launch_sha,
        "status": "complete",
        "fit_complete": True,
        "checkpoint_complete": True,
        "counts": counts,
        "configuration": configuration,
        "resources": "resources_unmeasured",
        "intervention_by_rule": {arm: {} for arm in p.ARMS},
        "complete_invocation_timeout": {
            "limit_s": 1800.0,
            "boundary": (
                "process start before imports through clustered publication, fixed-recipe "
                "publication and final summary readback"
            ),
            "pre_final_summary_write_elapsed_s": 100.0,
            "publication_payload_readback_elapsed_s": 100.1,
            "final_readback_within_limit": True,
            "final_readback_check": "requires zero process exit and native_time wall<1800s",
        },
    }
    (path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (path / "final_DENSE.pt").write_bytes(b"synthetic checkpoint sentinel")
    (path / "native_time.txt").write_text(
        "native_wall_s=100.20\nuser_cpu_s=90.10\nsystem_cpu_s=2.30\n"
        "peak_rss_kib=4194304\nexit_code=0\n",
        encoding="utf-8",
    )
    training = [
        {
            "phase": "train",
            "master": master,
            "base": master,
            "episode": episode,
            "reset_seed": 100000 * master + 1000 + episode,
            "steps": 256,
            "S": float(episode),
            "J": float(episode) / 256,
            "training_fact": f"retained-{episode}",
        }
        for episode in range(1024)
    ]
    evaluation = []
    for arm, offset in (("C", 0.0), ("F", .05), ("dwell", .02)):
        for episode in range(64):
            value = episode / 256 + offset
            if arm == "F" and episode == 0:
                value -= .1
            evaluation.append({
                "phase": "eval",
                "arm": arm,
                "episode": episode,
                "base": master,
                "evaluation_namespace": namespace,
                "reset_seed": 100000 * namespace + 2000 + episode,
                "steps": 256,
                "S": value * 256,
                "J": value,
                "absolute_fact": f"{arm}-{episode}",
            })
    updates = [
        {
            "master": master,
            "rollout": index // 4,
            "epoch": index % 4,
            "episodes": [2 * (index // 4), 2 * (index // 4) + 1],
            "loss": index / 2048,
        }
        for index in range(2048)
    ]
    (path / "episodes.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in training + evaluation), encoding="utf-8"
    )
    (path / "updates.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in updates), encoding="utf-8"
    )
    return path


def test_record_reader_requires_full_order_and_preserves_all_facts(tmp_path):
    path = write_synthetic_unit(tmp_path)
    unit, master, namespace = p.UNITS[0]
    result = p.read_unit(tmp_path, unit, master, namespace, "d" * 40)
    assert result["complete"]
    assert len(result["training_records"]) == 1024
    assert len(result["update_records"]) == 2048
    assert len(result["evaluation_records"]) == 192
    assert result["training_records"][-1]["training_fact"] == "retained-1023"
    assert result["evaluation_records"][-1]["absolute_fact"] == "dwell-63"
    assert result["contrasts"]["F-C"]["adverse_episode_ids"] == [0]
    assert len(result["contrasts"]["F-C"]["favorable_episode_ids"]) == 63
    assert result["summary"]["resources"] == "resources_unmeasured"
    assert result["native_resources"] == {
        "native_wall_s": 100.2,
        "user_cpu_s": 90.1,
        "system_cpu_s": 2.3,
        "peak_rss_kib": 4194304,
        "exit_code": 0,
    }

    lines = (path / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
    lines[-1], lines[-2] = lines[-2], lines[-1]
    (path / "episodes.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    broken = p.read_unit(tmp_path, unit, master, namespace, "d" * 40)
    assert not broken["complete"]
    assert any("out of order" in issue for issue in broken["issues"])
    wrong_sha = p.read_unit(tmp_path, unit, master, namespace, "e" * 40)
    assert any("launch SHA" in issue for issue in wrong_sha["issues"])
    (path / "native_time.txt").write_text(
        "native_wall_s=1800.00\nuser_cpu_s=90.10\nsystem_cpu_s=2.30\n"
        "peak_rss_kib=4194304\nexit_code=0\n", encoding="utf-8"
    )
    timed_out = p.read_unit(tmp_path, unit, master, namespace, "d" * 40)
    assert any("native time/CPU/RSS" in issue for issue in timed_out["issues"])


def test_all_indexed_runner_bindings_and_final_publication(tmp_path, monkeypatch):
    calls = []

    def fake_run(output, launch_sha, process_start, seconds, **kwargs):
        calls.append((output, launch_sha, process_start, seconds, kwargs))
        output.mkdir(parents=True)
        summary = {
            "object": kwargs["object_name"],
            "card": kwargs["card_path"],
            "master": kwargs["master"],
            "evaluation_namespace": kwargs["evaluation_namespace"],
            "launch_sha": launch_sha,
            "status": "complete",
            "fit_complete": True,
            "checkpoint_complete": True,
            "configuration": {"remaining_process_timeout_s": seconds},
        }
        (output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        rows = [
            {
                "phase": "eval", "arm": arm, "episode": episode,
                "base": kwargs["master"],
                "evaluation_namespace": kwargs["evaluation_namespace"],
                "reset_seed": 100000 * kwargs["evaluation_namespace"] + 2000 + episode,
                "steps": 256, "S": value * 256, "J": value,
            }
            for arm, value in (("C", .1), ("F", .2), ("dwell", .15))
            for episode in range(64)
        ]
        (output / "episodes.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
        return 0

    monkeypatch.setitem(
        sys.modules, "scripts.run_acvc_fresh_dense_reuse_b01", SimpleNamespace(run=fake_run)
    )
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_cluster_fixed_recipe_c01.py"
    spec = importlib.util.spec_from_file_location("fixed_recipe_runner", script)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    for unit, master, namespace in p.UNITS:
        output = tmp_path / f"run_{unit}" / f"unit_{unit:02d}"
        assert runner.main([
            "--unit", str(unit), "--output", str(output),
            "--launch-sha", "f" * 40, "--execution-seconds", "1800",
        ]) == 0
        _, _, _, seconds, kwargs = calls[-1]
        assert seconds == 1800
        assert kwargs == {
            "make_env": p.make_cluster,
            "train_episodes": 1024,
            "master": master,
            "evaluation_namespace": namespace,
            "object_name": p.OBJECT,
            "card_path": p.CARD,
            "mode": "PROVISIONAL_SINGLE_TASK_C_BENCH_UNIT",
            "allocation_seconds": p.PLANNING_SECONDS,
            "train_rule": "C",
            "eval_arms": p.ARMS,
        }
        published = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        assert published["unit_index"] == unit
        assert published["primary"]["complete"]
    assert len(calls) == 6
    with pytest.raises(SystemExit):
        runner.main(["--unit", "1", "--output", str(tmp_path / "unit_02"),
                     "--launch-sha", "f" * 40, "--execution-seconds", "1800"])
    prior = tmp_path / "prior" / "unit_01"
    prior.mkdir(parents=True)
    (prior / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        runner.main(["--unit", "1", "--output", str(prior),
                     "--launch-sha", "f" * 40, "--execution-seconds", "1800"])


def test_launch_has_adjacent_admission_refusal_and_both_timeouts():
    launch = Path(p.__file__).with_name("launch.sh").read_text(encoding="utf-8")
    assert 'if [[ -e "$output" ]]' in launch
    assert 'admit-memory --out "$output/admission.json" &&' in launch
    assert "user_cpu_s=%U\\nsystem_cpu_s=%S" in launch
    outer = "timeout --signal=TERM --kill-after=10s 1860s \\\n"
    inner = "timeout --signal=TERM --kill-after=10s 1800s \\\n"
    python = '"$HMASD_PYTHON" scripts/run_acvc_cluster_fixed_recipe_c01.py \\\n'
    assert launch.count("timeout --signal=TERM --kill-after=10s") == 2
    assert launch.index(outer) < launch.index(inner) < launch.index(python)
    assert "--execution-seconds 1800" in launch
    assert 'printf -v suffix \'unit_%02d\' "$unit"' in launch


def test_fixed_publication_marks_final_write_readback_boundary_incomplete(tmp_path, monkeypatch):
    output = tmp_path / "unit_01"
    output.mkdir()
    (output / "summary.json").write_text(json.dumps({
        "status": "complete",
        "configuration": {"remaining_process_timeout_s": 1800.0},
    }), encoding="utf-8")
    monkeypatch.setattr(p.shared, "publish", lambda *_args, **_kwargs: True)
    readings = iter((0.0, 100.0, 100.1, 1800.0))
    assert not p.publish(output, 0.0, 1, clock=lambda: next(readings))
    result = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert result["status"] == "incomplete"
    assert result["error"] == f"TimeoutError: {p.OBJECT} final evidence readback crossed 1800s"
    assert result["complete_invocation_timeout"]["final_readback_within_limit"] is False
    assert result["complete_invocation_timeout"]["failed_final_readback_elapsed_s"] == 1800.0
