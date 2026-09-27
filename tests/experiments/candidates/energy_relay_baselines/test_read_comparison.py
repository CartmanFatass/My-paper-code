import copy
import hashlib
import json

import pytest

from experiments.candidates.energy_relay_baselines import read_comparison as reader


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def rows(qos):
    return [dict(seed=world, failed=False, actual_length=3000, terminal_type="truncated",
                 qos_per_step_pre_entry=qos, qos_per_step_entry_to_input=None,
                 qos_per_step_post_input=None, steps_pre_entry=3000,
                 steps_entry_to_input=0, steps_post_input=0,
                 qos_satisfaction_ratio_per_step=qos,
                 raw_native_J=3000 * qos, return_constraint_cost_sum=1.0,
                 cutoff_event_count_sum=0, depletion_event_count_sum=0,
                 min_decoded_battery=0.1, zero_service=False)
            for world in reader.WORLDS]


@pytest.fixture
def comparison(tmp_path):
    train_dirs, eval_dirs = [], []
    for offset, seed in enumerate(reader.SEEDS):
        train, evaluation = tmp_path / f"train-{seed}", tmp_path / f"eval-{seed}"
        train_dirs.append(train)
        eval_dirs.append(evaluation)
        checkpoints = {name: dict(rollout=r, transitions=t,
                                 policy_fingerprint=f"fp-{seed}-{name}", agent_pt_sha256=f"sha-{seed}-{name}")
                       for name, (r, t) in reader.CHECKPOINTS.items()}
        write_json(train / "summary.json", dict(
            object_id=reader.OBJECT_ID, seed=seed, status="COMPLETE", failure=None,
            counts=dict(transitions=1_200_000, rollouts=200), checkpoints=checkpoints,
            optimizer_steps=dict(low_actor=450_000, low_critic=450_000)))
        for name, record in checkpoints.items():
            artifacts = {}
            for mode in reader.MODES:
                name_full = f"L_{name}_{mode}_e0.00_x0.05"
                panel_rows = rows(0.2 if name == "c00" else 0.3 + 0.1 * offset)
                if name == "c06":
                    panel_rows[0][reader.Q] = 0.1  # retain the adverse world
                    panel_rows[0][reader.J] = 300.0
                    panel_rows[1]["return_constraint_cost_sum"] = 5.0
                panel_path = evaluation / "checkpoint-eval/panels" / f"{name_full}.json"
                write_json(panel_path, dict(
                    name=name_full, policy_seed=seed, checkpoint=name, final=False,
                    action_mode=mode, rollout=record["rollout"], transitions=record["transitions"],
                    draw=0 if mode == "stochastic" else None,
                    policy_identity=[dict(checkpoint_sha256=record["agent_pt_sha256"],
                                          policy_fingerprint=record["policy_fingerprint"])], worlds=panel_rows))
                artifacts[f"panels/{name_full}.json"] = hashlib.sha256(panel_path.read_bytes()).hexdigest()
            write_json(evaluation / "checkpoint-eval" / f"{name}_deterministic-stochastic/summary.json",
                       dict(object_id=reader.OBJECT_ID, status="COMPLETE", failure=None,
                            policy_seed=seed, checkpoint=name, final=False, worlds=list(reader.WORLDS),
                            modes=list(reader.MODES), artifacts=artifacts,
                            counts=dict(episodes_completed=64, steps=192_000, panels_completed=2,
                                        failed_worlds=0, new_optimizer_updates=0)))
        # The reader must not discover any extra checkpoint or final subdirectory.
        write_json(evaluation / "checkpoint-eval/panels/L_c03_deterministic_e0.00_x0.05.json", {})
        write_json(evaluation / "checkpoint-eval/final/panels/forbidden.json", {})
    b01, refs = tmp_path / "b01", tmp_path / "refs"
    for label, (base, relative) in reader.REFERENCE_PATHS.items():
        root = b01 if base == "b01" else refs
        path = root / relative
        write_json(path, dict(name=path.stem, worlds=rows(0.5)))
    return dict(train_dirs=train_dirs, eval_dirs=eval_dirs, b01=b01, refs=refs)


def test_complete_reading_keeps_training_units_and_losses(comparison):
    value = reader.make_reading(**comparison)
    assert value["independent_fresh_training_n"] == 2
    assert len(value["sources_sha256"]) == 19
    for seed in reader.SEEDS:
        mode = value["seeds"][str(seed)]["modes"]["deterministic"]
        assert mode["endpoint_minus_initial"][reader.Q]["n"] == 32
        assert mode["endpoint_minus_initial"][reader.Q]["positive"] == 31
        assert mode["endpoint_minus_initial"]["conflict"] is not None
        assert mode["per_world_endpoint_minus_initial"]["955001"][reader.Q] == pytest.approx(-0.1)
    spread = value["descriptive_seed_spread"]["deterministic"][reader.Q]
    assert spread["n"] == 2
    assert spread["sd"] > 0


def test_duplicate_panel_is_not_overwritten(comparison):
    comparison["eval_dirs"].append(comparison["eval_dirs"][0])
    with pytest.raises(ValueError, match="duplicate checkpoint"):
        reader.make_reading(**comparison)


def test_missing_endpoint_refuses_complete_reading(comparison):
    path = comparison["eval_dirs"][0] / "checkpoint-eval/panels/L_c06_stochastic_e0.00_x0.05.json"
    path.unlink()
    with pytest.raises(ValueError, match="incomplete comparison"):
        reader.make_reading(**comparison)


@pytest.mark.parametrize("change", ["world", "fingerprint", "seed", "failure", "nan"])
def test_wrong_panel_refuses_before_output(comparison, tmp_path, change):
    path = comparison["eval_dirs"][0] / "checkpoint-eval/panels/L_c06_stochastic_e0.00_x0.05.json"
    panel = json.loads(path.read_text())
    if change == "world":
        panel["worlds"][0]["seed"] = 957001
    elif change == "fingerprint":
        panel["policy_identity"][0]["policy_fingerprint"] = "wrong"
    elif change == "seed":
        panel["policy_seed"] = 925031
    elif change == "failure":
        panel["worlds"][0]["failed"] = True
    else:
        panel["worlds"][0][reader.Q] = float("nan")
    write_json(path, panel)
    output = tmp_path / "output/reading.json"
    with pytest.raises(ValueError):
        reader.main(["--train", *map(str, comparison["train_dirs"]),
                     "--evals", *map(str, comparison["eval_dirs"]),
                     "--b01", str(comparison["b01"]), "--refs", str(comparison["refs"]),
                     "--out", str(output)])
    assert not output.parent.exists()


def test_recovered_or_incomplete_fit_not_counted_fresh(comparison):
    path = comparison["train_dirs"][0] / "summary.json"
    original = json.loads(path.read_text())
    for patch in ({"resume": {"rollout": 100}}, {"status": "INCOMPLETE"},
                  {"counts": {"transitions": 200, "rollouts": 1_200_000}}):
        summary = copy.deepcopy(original)
        summary.update(patch)
        write_json(path, summary)
        with pytest.raises(ValueError):
            reader.make_reading(**comparison)


def test_complete_panels_do_not_hide_failed_evaluation(comparison):
    path = comparison["eval_dirs"][0] / "checkpoint-eval/c06_deterministic-stochastic/summary.json"
    status = json.loads(path.read_text())
    status["status"] = "INCOMPLETE"
    write_json(path, status)
    with pytest.raises(ValueError, match="status/identity"):
        reader.make_reading(**comparison)


def change_panel(comparison, mutate):
    root = comparison["eval_dirs"][0] / "checkpoint-eval"
    panel_path = root / "panels/L_c06_stochastic_e0.00_x0.05.json"
    status_path = root / "c06_deterministic-stochastic/summary.json"
    panel, status = json.loads(panel_path.read_text()), json.loads(status_path.read_text())
    mutate(panel, status)
    write_json(panel_path, panel)
    status["artifacts"][f"panels/{panel_path.name}"] = hashlib.sha256(panel_path.read_bytes()).hexdigest()
    write_json(status_path, status)


def test_native_early_termination_preserves_adverse_complete_panel(comparison):
    def shorten(panel, status):
        panel["worlds"][0].update(actual_length=1000, terminal_type="terminated", steps_pre_entry=1000,
                                  depletion_event_count_sum=8)
        status["counts"]["steps"] -= 2000
    change_panel(comparison, shorten)
    value = reader.make_reading(**comparison)
    endpoint = value["seeds"][str(reader.SEEDS[0])]["modes"]["stochastic"]["endpoint"]
    assert endpoint["n"] == 32
    assert endpoint["actual_transitions"] == 94_000
    assert endpoint["terminal_types"] == {"terminated": 1, "truncated": 31}
    assert endpoint["depletion_event_count_sum"] == 0.25


def test_summary_step_count_must_match_native_rows(comparison):
    change_panel(comparison, lambda panel, status: status["counts"].update(steps=191_999))
    with pytest.raises(ValueError, match="summed native episode lengths"):
        reader.make_reading(**comparison)


def test_phase_summary_preserves_observed_denominators(comparison):
    def add_one_phase(panel, status):
        panel["worlds"][0].update(steps_pre_entry=1000, steps_entry_to_input=500, steps_post_input=1500,
                                  qos_per_step_entry_to_input=0.1, qos_per_step_post_input=0.5)
    change_panel(comparison, add_one_phase)
    value = reader.make_reading(**comparison)
    endpoint = value["seeds"][str(reader.SEEDS[0])]["modes"]["stochastic"]["endpoint"]
    assert endpoint["qos_per_step_post_input"] == 0.5
    assert endpoint["observed_qos_per_step_post_input"] == 1
    assert endpoint["total_steps_post_input"] == 1500
    assert endpoint["observed_qos_per_step_pre_entry"] == 32


def test_missing_phase_is_not_legitimate_null(comparison):
    change_panel(comparison, lambda panel, status: panel["worlds"][0].pop("qos_per_step_post_input"))
    with pytest.raises(ValueError, match="missing required phase"):
        reader.make_reading(**comparison)


def test_holdout_path_rejected_without_read(tmp_path):
    with pytest.raises(ValueError, match="does not read hold-out"):
        reader.read_json(tmp_path / "b02_holdout_refs_a01/missing.json", {})
