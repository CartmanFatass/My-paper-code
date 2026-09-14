"""Synthetic changed-contract checks: no native environment or scientific fitting."""

import copy
import json

import pytest
import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_fixed_lr_b01 import protocol, study


def final_rows(delta):
    return [dict(object=protocol.OBJECT, stage="fixed", phase="eval", pair_master=8253,
                 arm=arm, lr_key="slow", learning_rate=1e-4, episode=e, steps=256,
                 J=delta if arm == "COND" else 0.0,
                 **protocol.randomization(8253, "eval", e))
            for arm in protocol.ARMS for e in range(32)]


@pytest.mark.parametrize("delta,reading", [(.02, "COND_ABOVE_MEI"),
    (-.02, "COND_ADVERSE"), (.01, "INSIDE_MEI"), (-.01, "INSIDE_MEI"), (0., "INSIDE_MEI")])
def test_complete_primary_and_inclusive_boundaries(delta, reading):
    answer = protocol.primary(final_rows(delta))
    assert answer["delta_J"] == pytest.approx(delta)
    assert answer["reading"] == reading
    assert answer["ordered_COND_minus_DENSE"] == [delta] * 32
    assert answer["conditional_panel_se"] == 0
    assert answer["independent_new_training_pairs"] == 1
    assert answer["new_selection_procedure_replications"] == 0


@pytest.mark.parametrize("damage", ["missing", "duplicate", "nonfinite", "master",
    "rate", "rng", "stage", "endpoint", "arm"])
def test_invalid_final_has_no_primary(damage):
    rows = final_rows(.02)
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    else:
        key, value = {"nonfinite": ("J", float("nan")), "master": ("pair_master", 8252),
                      "rate": ("learning_rate", 3e-4), "rng": ("velocity_seed", 1),
                      "stage": ("stage", "selection"), "endpoint": ("steps", 255),
                      "arm": ("arm", "UNKNOWN")}[damage]
        rows[0][key] = value
    with pytest.raises(ValueError):
        protocol.primary(rows)


def test_fixed_addresses_and_computed_exposure():
    assert protocol.randomization(8253, "train", 255) == {
        "reset_seed": 825301255, "velocity_seed": 825300021, "duration_seed": 825304255}
    assert protocol.randomization(8253, "eval", 31) == {
        "reset_seed": 825302031, "velocity_seed": 825303031, "duration_seed": 825305031}
    for master in (8251, 8252, 8254):
        with pytest.raises(ValueError):
            protocol.randomization(master, "train", 0)
    work = protocol.planned_exposure()
    assert work["total"] == {
        "fits": 2, "train_episodes": 512, "evaluation_episodes": 64,
        "train_team_ticks": 131072, "evaluation_team_ticks": 16384,
        "rollouts": 256, "adam_calls": 1024, "total_team_ticks": 147456,
        "actor_row_uses_collection_evaluation_replay": 3358720}
    assert work["new_selection_fits"] == 0


@pytest.mark.parametrize("fail_after_update", [False, True])
def test_native_fit_contract_reaches_rng_optimizer_rows_checkpoints_and_summary(tmp_path, monkeypatch, fail_after_update):
    native = study.inherited
    models, optimizers, environments, generators, training_rngs, calls = [], [], [], [], [], []

    class Model:
        def state_dict(self):
            return {"synthetic": torch.tensor(0.)}

    class Optimizer:
        def __init__(self):
            self.param_groups = [{"lr": 3e-4}]

        def state_dict(self):
            return {"lr": self.param_groups[0]["lr"]}

    def factory(master):
        calls.append(master)
        pair = {arm: (Model(), Model()) for arm in protocol.ARMS}
        models.extend(model for pair_models in pair.values() for model in pair_models)
        return pair

    def optimizer(*_args):
        value = Optimizer()
        optimizers.append(value)
        return value

    def environment(seed):
        value = object()
        environments.append((seed, value))
        return value

    def generator(seed):
        value = object()
        generators.append((seed, value))
        return value

    def collect(_env, _actor, _critic, horizon, reset, velocity, _duration,
                metadata, _check, counts, emit, _diag, _limits, **options):
        phase, arm = metadata["phase"], metadata["arm"]
        assert horizon == 256 and options["ratio_grouping"] == "agent_compound"
        assert options["real"] and not options["diagnostics"]
        counts[f"{phase}_episodes"] += 1
        counts[f"{phase}_team_steps"] += 256
        counts["team_steps"] += 256
        counts["completed_episode_steps"] += 256
        if phase == "train":
            training_rngs.append((arm, velocity))
        emit(dict(metadata, reset_seed=reset, steps=256, J=.02 if arm == "COND" else 0.))
        return {"synthetic": True}

    def update(_actor, _critic, opt, episodes, chunk, _check, counts, **options):
        assert opt.param_groups[0]["lr"] == 1e-4
        assert len(episodes) == 2 and chunk == 32
        assert options == {"ratio_grouping": "agent_compound", "entropy_coef": .01}
        counts["optimizer_steps"] += 4
        if fail_after_update:
            raise RuntimeError("synthetic failure after Adam counter increment")
        return [{"epoch": e} for e in range(4)]

    for name, value in {"optimizer_for": optimizer, "make_real": environment,
                        "generator": generator, "collect_episode": collect, "update": update,
                        "geometry_snapshot": lambda *_args: {},
                        "geometry_exposure": lambda *_args: {"synthetic": True}}.items():
        monkeypatch.setattr(native, name, value)
    summary = study.run_study(tmp_path, "a" * 40, pair_factory=factory,
                              clock=lambda: 1.)
    if fail_after_update:
        assert summary["status"] == "INCOMPLETE"
        assert summary["completed_fit_count"] == 0 and summary["fits"] == []
        assert summary["primary"] is None and len(summary["partial_fits"]) == 1
        partial = summary["partial_fits"][0]
        assert partial["arm"] == "COND" and partial["phase"] == "training"
        assert partial["counts"]["optimizer_steps"] == 4
        assert partial["counts"]["train_team_steps"] == 512
        assert partial["counts"]["train_episodes"] == 2
        assert partial["exposure"] == {"synthetic": True}
        assert partial["fit_complete"] is False
        assert "synthetic failure after Adam" in partial["limits"][0]
        assert summary["raw_episode_rows"] == 2 and summary["raw_rollout_rows"] == 0
        assert json.loads((tmp_path / "summary.json").read_text())["partial_fits"] == [partial]
        assert len(optimizers) == 1  # No next arm or replacement started.
        return
    assert calls == [8253]
    assert len({id(model) for model in models}) == 4
    assert len({id(opt) for opt in optimizers}) == 2
    assert environments[0][0] == environments[1][0] == 825301000
    assert environments[0][1] is not environments[1][1]
    assert len({id(rng) for _, rng in generators}) == len(generators)
    for arm in protocol.ARMS:
        assert len({id(rng) for label, rng in training_rngs if label == arm}) == 1
    assert training_rngs[0][1] is not training_rngs[-1][1]
    assert summary["status"] == "COMPLETE" and summary["limits"] == []
    assert summary["raw_episode_rows"] == 576 and summary["raw_rollout_rows"] == 256
    assert summary["completed_fit_count"] == 2
    assert summary["primary"]["delta_J"] == pytest.approx(.02)
    assert not (tmp_path / "selection.json").exists()
    for arm in protocol.ARMS:
        checkpoint = torch.load(tmp_path / f"fixed_slow_{arm}.pt", weights_only=True)
        assert checkpoint["object"] == protocol.OBJECT
        assert checkpoint["pair_master"] == 8253 and checkpoint["learning_rate"] == 1e-4
        assert checkpoint["optimizer"]["lr"] == 1e-4
    rows = [json.loads(line) for line in (tmp_path / "episodes.jsonl").read_text().splitlines()]
    assert all(row["object"] == protocol.OBJECT and row["pair_master"] == 8253 for row in rows)
    assert [(fit["arm"], fit["lr_key"]) for fit in summary["fits"]] == [("COND", "slow"), ("DENSE", "slow")]
    assert json.loads((tmp_path / "summary.json").read_text()) == summary
    assert native.protocol.OBJECT == "MGTAP-LR-SELECTION-B01"
    assert native.protocol.HOLDOUT_MASTER == 8252


def test_failure_publishes_partial_once_without_replacement(tmp_path):
    calls = []

    def failing_fit(**kwargs):
        calls.append(kwargs["arm"])
        kwargs["emit_episode"]({"phase": "train", "partial": True})
        raise RuntimeError("synthetic interrupted fit")

    result = study.run_study(tmp_path, "b" * 40,
                            pair_factory=lambda _s: {arm: (None, None) for arm in protocol.ARMS},
                            fit_runner=failing_fit)
    assert calls == ["COND"] and result["status"] == "INCOMPLETE"
    assert result["primary"] is None and result["raw_episode_rows"] == 1
    assert "synthetic interrupted fit" in result["limits"][0]
    assert json.loads((tmp_path / "summary.json").read_text())["status"] == "INCOMPLETE"
