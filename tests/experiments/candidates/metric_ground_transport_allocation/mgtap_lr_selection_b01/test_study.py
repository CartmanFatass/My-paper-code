"""Synthetic wiring/publication tests; no native environment or science run."""

import json
from pathlib import Path
import unittest
from unittest import mock

import pytest
import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import protocol
from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import study


class FakeModel:
    def __init__(self, identity):
        self.identity = identity

    def state_dict(self):
        return {"identity": torch.tensor(self.identity)}


def expected_counts():
    result = {key: 0 for key in study.new_counts(False)}
    result.update(study.EXPECTED_COUNTS)
    result["completed_episode_steps"] = result["team_steps"]
    return result


class Harness:
    def __init__(self, root, fail_at=None):
        self.root, self.fail_at = Path(root), fail_at
        self.factory_calls, self.invocations, self.model_ids = [], [], []
        self.live_models = []  # Retain fixtures so Python cannot recycle id() across fits.

    def factory(self, master):
        if master == protocol.HOLDOUT_MASTER:
            selection = self.root / "selection.json"
            assert selection.exists()
            body = selection.read_bytes()
            digest = (self.root / "selection.sha256").read_text(encoding="ascii").split()[0]
            assert study.hashlib.sha256(body).hexdigest() == digest
        serial = len(self.factory_calls)
        self.factory_calls.append(master)
        pair = {arm: (FakeModel(serial * 10 + i), FakeModel(serial * 10 + i + 2))
                for i, arm in enumerate(protocol.ARMS)}
        self.live_models.extend(model for models in pair.values() for model in models)
        return pair

    def fit(self, *, stage, master, lr_key, arm, models, output, emit_episode,
            emit_rollout, study_start, clock):
        index = len(self.invocations)
        self.invocations.append((stage, lr_key, arm))
        self.model_ids.append(tuple(id(model) for model in models))
        if self.fail_at == index:
            emit_episode({"stage": stage, "phase": "train", "pair_master": master,
                          "arm": arm, "lr_key": lr_key, "episode": 0, "J": 0.0})
            raise RuntimeError("synthetic stop")
        rate = protocol.LEARNING_RATES[lr_key]
        # Full raw training rows and rollout rows are retained without doing learning.
        for episode in range(protocol.TRAIN_EPISODES):
            address = protocol.randomization(master, "train", episode)
            emit_episode({"stage": stage, "phase": "train", "pair_master": master,
                          "arm": arm, "lr_key": lr_key, "learning_rate": rate,
                          "episode": episode, "steps": protocol.HORIZON, "J": 0.0,
                          **address})
        for rollout in range(protocol.TRAIN_EPISODES // 2):
            emit_rollout({"stage": stage, "pair_master": master, "arm": arm,
                          "lr_key": lr_key, "learning_rate": rate,
                          "rollout": rollout, "episodes": 2, "optimizer_steps": 4})
        scores = {
            "COND": {"base": .02, "slow": .07, "fast": .03},
            "DENSE": {"base": .04, "slow": .01, "fast": .08},
        }
        score = ({"COND": .11, "DENSE": .08}[arm] if stage == "holdout"
                 else scores[arm][lr_key])
        for episode in range(protocol.EVAL_EPISODES):
            address = protocol.randomization(master, "eval", episode)
            emit_episode({"stage": stage, "phase": "eval", "pair_master": master,
                          "arm": arm, "lr_key": lr_key, "learning_rate": rate,
                          "episode": episode, "steps": protocol.HORIZON, "J": score,
                          **address})
        checkpoint = Path(output) / f"{stage}_{lr_key}_{arm}.pt"
        checkpoint.write_bytes(b"synthetic checkpoint")
        return {"stage": stage, "pair_master": master, "arm": arm,
                "lr_key": lr_key, "learning_rate": rate, "fit_complete": True,
                "panel_complete": True, "counts": expected_counts(),
                "checkpoint": checkpoint.name, "limits": []}


class StudyTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _invocation_scratch(self, tmp_path):
        self.scratch = tmp_path

    def test_complete_eight_fit_order_stage_fence_and_primary_publication(self):
        directory = self.scratch / "complete"
        harness = Harness(directory)
        summary = study.run_study(directory, "a" * 40, pair_factory=harness.factory,
                                  fit_runner=harness.fit)
        expected = [("selection", key, arm) for key in protocol.LEARNING_RATES
                    for arm in protocol.ARMS]
        expected += [("holdout", "slow", "COND"), ("holdout", "fast", "DENSE")]
        self.assertEqual(harness.invocations, expected)
        self.assertEqual(harness.factory_calls,
                         [protocol.SELECTION_MASTER] * 3 + [protocol.HOLDOUT_MASTER])
        self.assertEqual(len({item for pair in harness.model_ids for item in pair}), 16)
        self.assertEqual(summary["status"], "COMPLETE")
        self.assertEqual(summary["completed_fit_count"], 8)
        self.assertEqual(summary["raw_episode_rows"], 8 * (256 + 32))
        self.assertEqual(summary["raw_rollout_rows"], 8 * 128)
        self.assertEqual(summary["selection"]["selected_lr_key"],
                         {"COND": "slow", "DENSE": "fast"})
        self.assertAlmostEqual(summary["primary"]["delta_J"], .03)
        self.assertEqual(summary["primary"]["reading"], "COND_ABOVE_MEI")
        self.assertIn("excludes module imports", summary["timing_scope"])
        self.assertIn("model-pair factory", summary["timing_scope"])
        self.assertEqual(len(list(directory.glob("*.pt"))), 8)
        published = json.loads((directory / "summary.json").read_text())
        self.assertEqual(published["primary"], summary["primary"])
        self.assertEqual(published["planned_exposure"]["total"]["adam_calls"], 4096)

    def test_failure_retains_partial_rows_and_publishes_incomplete_without_replacement(self):
        directory = self.scratch / "failure"
        harness = Harness(directory, fail_at=2)
        summary = study.run_study(directory, "b" * 40, pair_factory=harness.factory,
                                  fit_runner=harness.fit)
        self.assertEqual(summary["status"], "INCOMPLETE")
        self.assertEqual(summary["completed_fit_count"], 2)
        self.assertEqual(len(harness.invocations), 3)
        self.assertEqual(harness.factory_calls, [protocol.SELECTION_MASTER] * 2)
        self.assertIsNone(summary["selection_file"])
        self.assertTrue((directory / "episodes.jsonl").stat().st_size)
        self.assertIn("synthetic stop", " ".join(summary["limits"]))
        self.assertEqual(json.loads((directory / "summary.json").read_text())["status"],
                         "INCOMPLETE")

    def test_native_fit_owns_optimizer_and_private_rng_objects_at_selected_rate(self):
        optimizers, rngs = [], []

        class FakeOptimizer:
            def __init__(self):
                self.param_groups = [{"lr": 3e-4}]

            def state_dict(self):
                return {"lr": self.param_groups[0]["lr"]}

        def fake_optimizer(_actor, _critic):
            value = FakeOptimizer()
            optimizers.append(value)
            return value

        def fake_generator(seed):
            value = object()
            rngs.append((seed, value))
            return value

        def fake_collect(_env, _actor, _critic, _horizon, reset_seed, _vrng, _drng,
                         metadata, _check, counts, emit_episode, _emit_diag, _limits, **_options):
            phase = metadata["phase"]
            counts[f"{phase}_episodes"] += 1
            counts[f"{phase}_team_steps"] += 256
            counts["team_steps"] += 256
            counts["completed_episode_steps"] += 256
            emit_episode(dict(metadata, reset_seed=reset_seed, steps=256, J=0.0))
            return {"reward": torch.zeros(256)}

        def fake_update(_actor, _critic, _optimizer, _episodes, _chunk, _check, counts, **_options):
            counts["optimizer_steps"] += 4
            return [{"epoch": i} for i in range(4)]

        directory = self.scratch / "native_fit"
        directory.mkdir()
        with mock.patch.multiple(
                study, make_real=lambda _seed: object(), optimizer_for=fake_optimizer,
                generator=fake_generator, collect_episode=fake_collect, update=fake_update,
                geometry_snapshot=lambda *_args: {}, geometry_exposure=lambda *_args: {}):
            for lr_key in ("slow", "fast"):
                study._native_fit(
                    stage="holdout", master=protocol.HOLDOUT_MASTER, lr_key=lr_key,
                    arm="COND", models=(FakeModel(1), FakeModel(2)), output=directory,
                    emit_episode=lambda _row: None, emit_rollout=lambda _row: None,
                    study_start=0.0, clock=lambda: 1.0)
        self.assertEqual([item.param_groups[0]["lr"] for item in optimizers], [1e-4, 1e-3])
        self.assertEqual(len({id(item) for item in optimizers}), 2)
        # Same numeric matched address across fits, but never the same live generator object.
        by_seed = {}
        for seed, value in rngs:
            by_seed.setdefault(seed, []).append(value)
        self.assertTrue(all(len({id(value) for value in values}) == len(values)
                            for values in by_seed.values()))


if __name__ == "__main__":
    unittest.main()
