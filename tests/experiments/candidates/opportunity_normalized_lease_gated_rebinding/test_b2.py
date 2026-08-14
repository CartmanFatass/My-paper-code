from __future__ import annotations

import copy
from dataclasses import replace
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest import mock

import numpy as np
import torch

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.b2 import analysis, config, host, models, run


class ProbabilityAndInitializationTests(unittest.TestCase):
    def test_probability_and_full_jacobian_conform_at_float64_tolerance(self) -> None:
        facts = analysis.probability_jacobian_conformance()
        self.assertTrue(facts["passes"])
        self.assertLessEqual(facts["maximum_probability_error"], 1e-10)
        self.assertLessEqual(facts["maximum_jacobian_error"], 1e-10)
        self.assertEqual(float(models.analytic_probability(1.0, 0.0)), 0.0)

    def test_paired_initialization_zero_output_weights_and_analytic_bias(self) -> None:
        flex_actor, flex_critic = models.paired_modules(137, "RATE-FLEX")
        const_actor, const_critic = models.paired_modules(137, "RATE-CONST")
        for left, right in zip(flex_actor.state_dict().values(), const_actor.state_dict().values(), strict=True):
            self.assertTrue(torch.equal(left, right))
        for left, right in zip(flex_critic.state_dict().values(), const_critic.state_dict().values(), strict=True):
            self.assertTrue(torch.equal(left, right))
        self.assertEqual(int(torch.count_nonzero(flex_actor.output_layer.weight)), 0)
        self.assertEqual(float(flex_actor.output_layer.bias), models.initial_event_bias())
        report = models.initialization_report()
        self.assertAlmostEqual(report["RATE-FLEX"]["probabilities"][2], 0.20, places=14)
        self.assertEqual(
            report["RATE-FLEX"]["probabilities"], report["RATE-CONST"]["probabilities"],
        )

    def test_rate_const_input_weights_receive_exact_zero_data_gradient(self) -> None:
        actor, _ = models.paired_modules(149, "RATE-CONST")
        with torch.no_grad():
            actor.output_layer.weight.fill_(0.1)
        inputs = torch.tensor([[0.2] * 7, [0.9] * 7], dtype=torch.float64)
        outputs = actor(inputs)
        self.assertTrue(torch.equal(outputs[0], outputs[1]))
        outputs.sum().backward()
        self.assertEqual(int(torch.count_nonzero(actor.input_layer.weight.grad)), 0)


class HostContractTests(unittest.TestCase):
    def test_event_and_mark_use_separate_paired_counter_domains(self) -> None:
        episode = SimpleNamespace(namespace="B2_TEST", seed=137, episode_index=0)
        calls: list[str] = []

        def uniform(domain: str, *_coordinates: object) -> float:
            calls.append(domain)
            return 0.0

        with mock.patch.object(host, "counter_uniform", side_effect=uniform):
            self.assertEqual(host.sample_action(0.5, episode, 8, 0), 1)
        self.assertEqual(calls, ["ACTION_EVENT_UNIFORM", "ACTION_MARK_UNIFORM"])

    def test_iid_safety_ordinal_coincident_and_offgrid_rules(self) -> None:
        learner = models.B2Learner(137, "RATE-CONST")
        base = host.generate_episode(
            seed=137, episode_index=0, namespace="B2_DRY_SAFETY", schedule=config.IID_SCHEDULE,
            safety=True,
        )
        coincident = replace(base, safety_tick=0, safety_agent=0)
        result = host.run_episode(coincident, arm="RATE-CONST", learner=learner, force_keep=True)
        self.assertEqual(result.iid_draw_records[0][0:2], (0, 0))
        self.assertTrue(result.iid_draw_records[0][3])
        self.assertEqual(sum(record[1] == 0 for record in result.iid_draw_records), 1)
        self.assertEqual(result.safety_policy_score_factors, 0)
        self.assertFalse(result.safety_unaffected_clock_advanced)

        offgrid = replace(base, safety_tick=33, safety_agent=0)
        result = host.run_episode(offgrid, arm="RATE-CONST", learner=learner, force_keep=True)
        self.assertEqual(sum(record[1] == 33 for record in result.iid_draw_records), 0)
        self.assertEqual(tuple(record[0] for record in result.iid_draw_records), tuple(range(len(result.iid_draw_records))))

    def test_safety_coordinates_are_balanced_and_declared(self) -> None:
        episodes = [host.generate_episode(
            seed=163, episode_index=index, namespace="B2_DRY_SAFETY_BALANCE",
            schedule=config.IID_SCHEDULE, safety=True,
        ) for index in range(16)]
        self.assertEqual([episode.safety_agent for episode in episodes].count(0), 8)
        self.assertEqual([episode.safety_agent for episode in episodes].count(1), 8)
        self.assertTrue(all(32 <= int(episode.safety_tick) <= 223 for episode in episodes))
        self.assertEqual(len({episode.safety_tick for episode in episodes}), 16)

    def test_const_zeroes_every_real_masked_dummy_and_safety_forward(self) -> None:
        learner = models.B2Learner(181, "RATE-CONST")
        observed: list[torch.Tensor] = []
        handle = learner.actor.input_layer.register_forward_pre_hook(
            lambda _module, args: observed.append(args[0].detach().clone())
        )
        try:
            episode = host.generate_episode(
                seed=181, episode_index=1, namespace="B2_DRY_ZERO_INPUT",
                schedule=config.IID_SCHEDULE, safety=True,
            )
            result = host.run_episode(episode, arm="RATE-CONST", learner=learner, force_keep=True)
        finally:
            handle.remove()
        self.assertTrue(observed)
        self.assertTrue(all(int(torch.count_nonzero(value)) == 0 for value in observed))
        self.assertTrue(any(row["cause"] == "SAFETY_BYPASS" for row in result.rate_rows))
        self.assertTrue(all(set(row["effective_actor_input"]) == {0.0} for row in result.rate_rows))
        self.assertTrue(result.dummy_call_ledger)


class PPOCacheAndWorkTests(unittest.TestCase):
    def test_behavior_caches_and_matched_ppo_work_facts(self) -> None:
        learner = models.B2Learner(199, "RATE-FLEX")
        episodes = []
        for schedule_index, schedule in enumerate(config.TRAIN_SCHEDULES):
            for local_index in range(8):
                actor_features = np.full((2, 7), 0.1 * (schedule_index + 1), dtype=np.float64)
                exposure = np.asarray([8.0, 8.0], dtype=np.float64)
                actions = np.asarray([(local_index + schedule_index) % 3, (local_index + 1) % 3])
                mask = np.asarray([True, True])
                critic_features = np.linspace(0.0, 1.0, 39, dtype=np.float64)
                row = host.BoundaryTrainingRecord(
                    tick=0, actor_features=actor_features, critic_features=critic_features,
                    exposure=exposure, actions=actions, policy_mask=mask,
                    behavior_joint_log_prob=learner.joint_log_probability(
                        actor_features, exposure, actions, mask,
                    ),
                    behavior_value=learner.value(critic_features), duration=256,
                    segment_reward=float(local_index) / 10.0,
                )
                episodes.append(SimpleNamespace(schedule=schedule, training_records=[row]))
        facts = learner.update(episodes, 1)
        self.assertEqual(facts.optimizer_steps, 4)
        self.assertEqual(facts.complete_episodes, 32)
        self.assertEqual(facts.episodes_by_schedule, {schedule: 8 for schedule in config.TRAIN_SCHEDULES})
        self.assertTrue(facts.behavior_log_probabilities_cached_before_epochs)
        self.assertTrue(facts.behavior_critic_values_cached_before_epochs)
        self.assertTrue(facts.advantages_cached_before_epochs)
        self.assertTrue(facts.lambda_returns_cached_before_epochs)
        self.assertTrue(facts.caches_unchanged_all_epochs)
        self.assertEqual(facts.actor_global_scale, 1 / 256)
        self.assertFalse(facts.advantage_normalization)
        self.assertFalse(facts.value_clipping)
        self.assertEqual(facts.value_coefficient_applications, 1)


class FrontierTests(unittest.TestCase):
    def _identity(self) -> dict[str, object]:
        return {"revision": config.REVISION, "files": {"x": "a" * 64}, "composite_sha256": "b" * 64}

    def _valid_learned_checkpoint(
        self, *, completed_updates: int = 8, seed: int = 137, arm: str = "RATE-FLEX",
    ) -> dict[str, object]:
        learner = models.B2Learner(seed, arm)
        checkpoint = learner.checkpoint(completed_updates, [])
        checkpoint["update_facts"] = [{} for _ in range(completed_updates)]
        parameters = (*learner.actor.parameters(), *learner.critic.parameters())
        optimizer = learner.optimizer.state_dict()
        optimizer["state"] = {
            parameter_id: {
                "step": torch.tensor(float(completed_updates * 4), dtype=torch.float32),
                "exp_avg": torch.zeros_like(parameter),
                "exp_avg_sq": torch.zeros_like(parameter),
            }
            for parameter_id, parameter in enumerate(parameters)
        }
        checkpoint["optimizer"] = optimizer
        return checkpoint

    def _complete_result_fixture(
        self, identity: dict[str, object], checkpoint_file_digest: str,
    ) -> dict[str, object]:
        panels, checkpoints, training, keep_pairing = AnalyzerAndIsolationTests()._package()
        state_digest = "b" * 64
        for seed in config.SEEDS:
            for arm in config.ARMS:
                fact = checkpoints[str(seed)][arm]
                fact["source_identity"] = identity
                fact["sha256_before_evaluation"] = checkpoint_file_digest
                fact["sha256_after_evaluation"] = checkpoint_file_digest
                fact["learned_state_sha256"] = state_digest
        result = analysis.analyze_complete_package(
            panels=panels, checkpoints=checkpoints, training=training,
            keep_pairing=keep_pairing, source_identity_exact=True,
            atomic_frontier_exact=True, expected_source_identity=identity,
        )
        result["source_identity"] = identity
        result["activity_facts"] = {
            "scientific_activity_started": True,
            "trigger": "first retained task-trained actor/critic/optimizer update",
            "trigger_coordinate": "train:137:RATE-FLEX:update-1",
            "single_revision_only": True, "revision": config.REVISION,
        }
        result["fresh_counter_namespaces"] = {
            "training": "B2_TRAIN_PAIRED", "iid": "B2_IID_PAIRED",
            "safety": "B2_SAFETY_PAIRED", "keep_replay": "B2_KEEP_PAIRED",
            "global_domain_prefix": "ONLGR_B2_REV02", "r04_or_B1_namespace_reuse": False,
        }
        result["frontier"] = {
            "revision": config.FRONTIER_REVISION, "result_blind_until_complete": True,
            "persistent_training_cells": 128, "persistent_evaluation_cells": 0,
            "interrupted_evaluation_replayed_from_final_checkpoints": True,
            "slice_seconds_requested": 3600.0,
        }
        result["resources"] = {
            "training_cell_wall_seconds": 1.0,
            "final_evaluation_materialization_wall_seconds": 1.0,
            "peak_observed_rss_bytes": 1, "torch_intraop_threads": 1,
            "torch_interop_threads": 1,
            "resource_conditions_are_descriptive_not_scientific_gates": True,
        }
        digest_map = {
            str(seed): {arm: state_digest for arm in config.ARMS} for seed in config.SEEDS
        }
        panel_payload_sha256 = run._panel_payload_sha256({
            "iid": result["iid_seed_arm_metrics"],
            "safety": result["safety_seed_arm_metrics"],
            "keep": result["keep_seed_arm_metrics"],
            "grid": result["diagnostic_grids"],
        })
        result["result_materialization"] = {
            "complete_atomic_result": True,
            "claim_bearing_values_persisted_before_completion": False,
            "persistent_result_files": 1,
            "checkpoint_state_digest_map": digest_map,
            "panel_payload_sha256": panel_payload_sha256,
            "evaluation_binding_sha256": run._evaluation_binding_sha256(
                identity, digest_map, panel_payload_sha256,
            ),
        }
        self.assertEqual(set(result), run.COMPLETE_RESULT_TOP_LEVEL_FIELDS)
        return result

    def _validate_fixture(
        self, root: Path, result: dict[str, object], identity: dict[str, object], digest: str,
    ) -> dict[str, object]:
        path = root / "results.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        with mock.patch.object(run, "_validate_complete_training_frontier", return_value=[]), \
             mock.patch.object(
                 run, "_validate_checkpoint_envelope",
                 return_value={"learned_state_sha256": "b" * 64},
             ), \
             mock.patch.object(run, "_require_final_matches_durable_frontier"), \
             mock.patch.object(run, "_sha256", return_value=digest):
            return run._validate_existing_result(
                path, output_root=root, identity=identity,
                deadline=time.perf_counter() + 10.0,
            )

    def test_atomic_cell_resume_reuses_exact_coordinate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cell.pt"
            calls = 0

            def work() -> dict[str, int]:
                nonlocal calls
                calls += 1
                return {"value": 7}

            kwargs = dict(
                path=path, kind="analytic", coordinate="analytic:one",
                identity=self._identity(), deadline=time.perf_counter() + 5.0, work=work,
                reserve_seconds=0.1,
            )
            first = run._run_or_load_cell(**kwargs)
            second = run._run_or_load_cell(**kwargs)
            self.assertEqual(calls, 1)
            self.assertEqual(first["data"], second["data"])
            self.assertFalse(any(item.suffix == ".tmp" for item in path.parent.iterdir()))

    def test_existing_cell_reuse_still_obeys_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cell.pt"
            run._run_or_load_cell(
                path=path, kind="analytic", coordinate="analytic:one",
                identity=self._identity(), deadline=time.perf_counter() + 5.0,
                reserve_seconds=0.1, work=lambda: {"value": 1},
            )
            with self.assertRaises(run.SliceExpired):
                run._run_or_load_cell(
                    path=path, kind="analytic", coordinate="analytic:one",
                    identity=self._identity(), deadline=time.perf_counter(),
                    reserve_seconds=0.1, work=lambda: {"value": 2},
                )

    def test_frontier_identity_tamper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cell.pt"
            run._run_or_load_cell(
                path=path, kind="analytic", coordinate="analytic:one",
                identity=self._identity(), deadline=time.perf_counter() + 5.0,
                work=lambda: {"value": 7}, reserve_seconds=0.1,
            )
            with self.assertRaises(run.FrontierIdentityError):
                run._run_or_load_cell(
                    path=path, kind="analytic", coordinate="analytic:two",
                    identity=self._identity(), deadline=time.perf_counter() + 5.0,
                    work=lambda: {"value": 9}, reserve_seconds=0.1,
                )

    def test_forged_r04_checkpoint_envelope_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "RATE-FLEX.pt"
            run._atomic_torch(path, {
                "artifact_kind": "ONLGR_B1_FINAL_CHECKPOINT",
                "revision": config.REVISION, "source_identity": self._identity(),
                "seed": 137, "arm": "RATE-FLEX",
                "checkpoint": {
                    "seed": 137, "arm": "RATE-FLEX", "completed_updates": 8,
                    "update_facts": [{}] * 8, "actor": {}, "critic": {}, "optimizer": {},
                },
            })
            with self.assertRaises(run.FrontierIdentityError):
                run._validate_checkpoint_envelope(
                    path, seed=137, arm="RATE-FLEX", identity=self._identity(),
                )

    def test_learned_checkpoint_rejects_nan_shape_and_optimizer_counterexamples(self) -> None:
        valid = self._valid_learned_checkpoint()
        self.assertIs(
            run._validate_learned_checkpoint(
                valid, seed=137, arm="RATE-FLEX", completed_updates=8,
            ),
            valid,
        )
        mutations = []
        actor_nan = copy.deepcopy(valid)
        actor_nan["actor"]["input_layer.weight"][0, 0] = float("nan")
        mutations.append(actor_nan)
        equal_numel_wrong_shape = copy.deepcopy(valid)
        equal_numel_wrong_shape["actor"]["input_layer.weight"] = (
            equal_numel_wrong_shape["actor"]["input_layer.weight"].reshape(16, 14)
        )
        mutations.append(equal_numel_wrong_shape)
        empty_optimizer = copy.deepcopy(valid)
        empty_optimizer["optimizer"] = {}
        mutations.append(empty_optimizer)
        junk_optimizer = copy.deepcopy(valid)
        junk_optimizer["optimizer"]["state"] = {"junk": {}}
        mutations.append(junk_optimizer)
        nan_lr = copy.deepcopy(valid)
        nan_lr["optimizer"]["param_groups"][0]["lr"] = float("nan")
        mutations.append(nan_lr)
        wrong_step = copy.deepcopy(valid)
        wrong_step["optimizer"]["state"][0]["step"] = torch.tensor(31.0)
        mutations.append(wrong_step)
        for index, checkpoint in enumerate(mutations):
            with self.subTest(counterexample=index):
                with self.assertRaises(run.FrontierIdentityError):
                    run._validate_learned_checkpoint(
                        checkpoint, seed=137, arm="RATE-FLEX", completed_updates=8,
                    )

    def test_final_checkpoint_must_match_update_eight_frontier_learned_state(self) -> None:
        frontier_checkpoint = self._valid_learned_checkpoint()
        different_checkpoint = copy.deepcopy(frontier_checkpoint)
        different_checkpoint["actor"]["input_layer.weight"][0, 0] += 1e-12
        envelope = {
            "learned_state_sha256": run.learned_state_sha256(different_checkpoint),
            "checkpoint": different_checkpoint,
        }
        with self.assertRaises(run.FrontierIdentityError):
            run._require_final_matches_frontier(
                envelope, frontier_checkpoint, coordinate="137:RATE-FLEX",
            )

    def test_expired_slice_runs_no_cell_and_exposes_no_partial_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cell.pt"
            work = mock.Mock(return_value={"value": 7})
            with self.assertRaises(run.SliceExpired), mock.patch("sys.stdout", new=io.StringIO()) as output:
                run._run_or_load_cell(
                    path=path, kind="analytic", coordinate="analytic:one",
                    identity=self._identity(), deadline=time.perf_counter(), work=work,
                )
                self.assertEqual(output.getvalue(), "")
            work.assert_not_called()
            self.assertFalse(path.exists())

    def test_resume_discards_only_own_stale_atomic_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stale = root / f".results.json.{'a' * 32}.tmp"
            stale.write_bytes(b"partial")
            run._discard_stale_atomic_temps(root)
            self.assertFalse(stale.exists())
            unknown = root / ".foreign.tmp"
            unknown.write_bytes(b"preserve")
            with self.assertRaises(run.FrontierIdentityError):
                run._discard_stale_atomic_temps(root)
            self.assertTrue(unknown.exists())

    def test_scoped_lock_rejects_concurrent_same_root_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with run._ScopedRunLock(root):
                with self.assertRaises(run.FrontierIdentityError):
                    with run._ScopedRunLock(root):
                        pass
            self.assertTrue((root / ".run.lock").is_file())
            with run._ScopedRunLock(root):
                pass

    def test_unexpected_output_entry_and_evaluation_cell_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "foreign.bin").write_bytes(b"x")
            with self.assertRaises(run.FrontierIdentityError):
                run._validate_output_entries(root)
        self.assertIsNone(run._TRAIN_CELL_NAME.fullmatch("iid_seed_137_RATE-FLEX.pt"))

    def test_first_retained_training_cell_carries_outcome_free_activity_fact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.pt"
            activity = {
                "scientific_activity_started": True,
                "trigger": "first retained task-trained actor/critic/optimizer update",
                "trigger_coordinate": "train:137:RATE-FLEX:update-1",
                "earliest_registered_trigger": True,
                "claim_bearing_evaluation_persisted": False,
                "revision": config.REVISION,
            }
            run._run_or_load_cell(
                path=path, kind="training_update", coordinate="train:137:RATE-FLEX:update-1",
                identity=self._identity(), deadline=time.perf_counter() + 5.0,
                reserve_seconds=0.1, work=lambda: {"activity_fact": activity},
            )
            payload = run._load_torch(path)
            self.assertEqual(payload["data"]["activity_fact"], activity)
            self.assertFalse(any("iid" in item.name or "result" in item.name for item in path.parent.iterdir()))

    def test_interrupted_in_memory_evaluation_persists_nothing(self) -> None:
        learners = {(seed, arm): object() for seed in config.SEEDS for arm in config.ARMS}
        calls = 0

        def evaluator(**_kwargs: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise run.SliceExpired("injected interruption")
            return {"outcome": 1.0}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(run.SliceExpired):
                run._materialize_panels_in_memory(
                    learners, deadline=time.perf_counter() + 30.0,
                    panel_evaluator=evaluator, grid_evaluator=lambda _learner: {"grid": 1.0},
                )
            self.assertEqual(tuple(root.iterdir()), ())
        self.assertEqual(calls, 2)

    def test_sliced_cli_return_emits_no_partial_outcome(self) -> None:
        with mock.patch.object(run, "run_registered", return_value=None), \
             mock.patch("sys.stdout", new=io.StringIO()) as output:
            code = run.main([
                "run", "--output-root", "unused", "--slice-seconds", "120",
            ])
        self.assertEqual(code, 75)
        self.assertEqual(output.getvalue(), "")

    def test_post_training_final_reserve_expiration_is_resumable_not_error(self) -> None:
        identity = self._identity()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for seed in config.SEEDS:
                checkpoint_root = root / "checkpoints" / f"seed_{seed}"
                checkpoint_root.mkdir(parents=True, exist_ok=True)
                for arm in config.ARMS:
                    (checkpoint_root / f"{arm}.pt").write_bytes(b"discarded-contract-placeholder")
            with mock.patch.object(run, "_validate_complete_training_frontier", return_value=[]), \
                 mock.patch.object(run, "_validate_checkpoint_envelope", return_value={}), \
                 mock.patch.object(run, "_require_final_matches_durable_frontier"):
                with self.assertRaises(run.SliceExpired):
                    run._validate_post_training_state(
                        root, identity,
                        deadline=time.perf_counter() + run.FINAL_EVALUATION_RESERVE_SECONDS - 1.0,
                    )

            dummy = (object(), {}, {})
            with mock.patch.object(run, "_safe_output_root", return_value=root), \
                 mock.patch.object(run, "_discard_stale_atomic_temps"), \
                 mock.patch.object(run, "_validate_output_entries"), \
                 mock.patch.object(run, "_configure_torch_threads"), \
                 mock.patch.object(run, "source_identity", return_value=identity), \
                 mock.patch.object(run, "_prepare_manifest"), \
                 mock.patch.object(run, "_train_coordinate", return_value=dummy), \
                 mock.patch.object(
                     run, "_validate_post_training_state",
                     side_effect=run.SliceExpired("final evaluation reserve unavailable"),
                 ):
                self.assertIsNone(run.run_registered(root, slice_seconds=1000.0))

    def test_existing_result_validation_expiration_is_resumable(self) -> None:
        identity = self._identity()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(run, "_safe_output_root", return_value=root), \
                 mock.patch.object(run, "_discard_stale_atomic_temps"), \
                 mock.patch.object(run, "_validate_output_entries"), \
                 mock.patch.object(run, "_configure_torch_threads"), \
                 mock.patch.object(run, "source_identity", return_value=identity), \
                 mock.patch.object(run, "_prepare_manifest"), \
                 mock.patch.object(
                     run, "_validate_existing_result",
                     side_effect=run.SliceExpired("validation reserve unavailable"),
                 ):
                self.assertIsNone(run.run_registered(root, slice_seconds=30.0))

    def test_torch_thread_configuration_binds_intra_and_interop_to_one(self) -> None:
        with mock.patch.object(run.torch, "set_num_threads") as intra, \
             mock.patch.object(run.torch, "get_num_interop_threads", return_value=2), \
             mock.patch.object(run.torch, "set_num_interop_threads") as interop, \
             mock.patch.object(run.torch, "use_deterministic_algorithms") as deterministic:
            run._configure_torch_threads()
        intra.assert_called_once_with(1)
        interop.assert_called_once_with(1)
        deterministic.assert_called_once_with(True)

    def test_existing_complete_result_is_validated_and_returned_without_overwrite(self) -> None:
        identity = self._identity()
        digest = "d" * 64
        result = self._complete_result_fixture(identity, digest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "results.json"
            path.write_text(json.dumps(result), encoding="utf-8")
            before = path.read_bytes()
            loaded = self._validate_fixture(root, result, identity, digest)
            self.assertTrue(run._json_equivalent(loaded, result))
            self.assertEqual(path.read_bytes(), before)

    def test_existing_result_missing_field_and_altered_branch_are_rejected(self) -> None:
        identity = self._identity()
        digest = "d" * 64
        result = self._complete_result_fixture(identity, digest)
        missing = copy.deepcopy(result)
        del missing["resources"]
        altered = copy.deepcopy(result)
        altered["branches"]["RETAIN_RATE_FLEX"] = not altered["branches"]["RETAIN_RATE_FLEX"]
        for name, candidate in (("missing", missing), ("altered", altered)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(run.FrontierIdentityError):
                    self._validate_fixture(Path(directory), candidate, identity, digest)


class AnalyzerAndIsolationTests(unittest.TestCase):
    def _package(self, delta: float = 0.03, support: bool = True):
        panels = {name: {} for name in ("iid", "safety", "keep", "grid")}
        checkpoints: dict[str, dict[str, object]] = {}
        training: dict[str, dict[str, object]] = {}
        keep_pairing: dict[str, bool] = {}
        for seed in config.SEEDS:
            key = str(seed)
            checkpoints[key] = {}
            training[key] = {}
            keep_pairing[key] = True
            for panel in panels:
                panels[panel][key] = {}
            for arm in config.ARMS:
                mean = 0.50 + (delta if arm == "RATE-FLEX" else 0.0)
                actions = (4, 4, 4) if support else (100, 3, 3)
                rate_distributions = {
                    name: {"0": {
                        "n": 1, "lambda_mean": 0.1, "lambda_standard_deviation": 0.0,
                        "lambda_minimum": 0.1, "lambda_maximum": 0.1,
                        "event_probability_mean": 0.1,
                        "event_probability_standard_deviation": 0.0,
                        "marked_entropy_mean": 0.1,
                    }} for name in (
                        "by_exposure", "by_plan_age", "by_busy_state",
                        "by_preceding_interval", "by_role",
                    )
                }
                base = {
                    "episodes": 32, "physics_ticks": 32 * 256, "mean_return": mean,
                    "episode_return_interval": {
                        "n": 32, "mean": mean, "standard_error": 0.0,
                        "lower": mean, "upper": mean,
                    },
                    "mean_service": mean, "mean_action_cost": 0.0,
                    "poststartup_legal_rows_by_role": (32, 32),
                    "poststartup_legal_rows": 64, "poststartup_stochastic_actions": actions,
                    "poststartup_stochastic_actions_by_role": (actions, actions),
                    "masked_routine_rows": (0, 0), "eligible_exposure": (64, 64),
                    "iid_draw_count": 1, "iid_draw_counts": {"4": 1, "16": 0, "32": 0},
                    "iid_draw_ordinal_and_after_action_rule_exact": True,
                    "iid_draw_filtration": {
                        "draw_after_current_action": True,
                        "visible_history_action_state_reward_prior_intervals_excluded": True,
                    },
                    "reward_service_cost_exact": True, "segment_ownership_exact": True,
                    "terminal_boundary_absent": True, "identity_unique": True,
                    "identity_schema_valid": True, "identity_rows": 100,
                    "actor_calls": 100, "critic_calls": 50, "messages": 16384,
                    "transmitted_bits": 32768, "latency_ns": (),
                    "safety_forced_count": 0, "safety_violations": 0,
                    "safety_score_factors": 0, "safety_affected_clock_exact": True,
                    "safety_unaffected_clock_exact": True, "safety_response_rows": (),
                    "fixed_conditional_mark_probability": 0.5,
                    "rate_const_effective_actor_inputs_exact_zero": arm == "RATE-CONST" or None,
                    "rate_const_lambda_exactly_equal_across_actor_rows": arm == "RATE-CONST" or None,
                    "rate_distributions": rate_distributions,
                    "event_free_survival_rows": (), "voluntary_event_ticks": (),
                    "inter_event_dwells": (), "stale_binding_ticks": 0,
                    "plan_age_sum": 0, "downtime_ticks": 0,
                    "physics_ledger_sha256": "1" * 64,
                    "interval_ledger_sha256": "2" * 64,
                    "dummy_call_ledger_sha256": "3" * 64,
                    "checkpoint_learned_state_sha256": "b" * 64,
                }
                panels["iid"][key][arm] = base
                safety = dict(base)
                safety.update({
                    "episodes": 16, "physics_ticks": 16 * 256,
                    "episode_return_interval": {
                        "n": 16, "mean": mean, "standard_error": 0.0,
                        "lower": mean, "upper": mean,
                    },
                    "messages": 8192, "transmitted_bits": 16384,
                    "safety_forced_count": 16,
                    "safety_response_rows": tuple({
                        "episode": index, "tick": 33 + index,
                        "affected_agent": index % 2, "expected_action": 1,
                        "affected_action": 1, "unaffected_action": 0,
                        "draws_at_safety": 0, "coincident_routine": False,
                    } for index in range(16)),
                })
                panels["safety"][key][arm] = safety
                keep = dict(base)
                keep.update({
                    "episodes": 16, "physics_ticks": 16 * 256,
                    "episode_return_interval": {
                        "n": 16, "mean": mean, "standard_error": 0.0,
                        "lower": mean, "upper": mean,
                    },
                    "messages": 8192, "transmitted_bits": 16384,
                })
                panels["keep"][key][arm] = keep
                panels["grid"][key][arm] = {
                    "count": 20, "rows": tuple({
                        "plan_age": 0, "delta": 4, "exposure": 4,
                        "features": (0.0,) * 7, "lambda": 0.1,
                        "event_probability": 0.1, "logit": -1.0,
                    } for _ in range(20)),
                    "lambda_range": 0.0, "lambda_standard_deviation": 0.0,
                    "rate_const_exact_equality": arm == "RATE-CONST" or None,
                    "checkpoint_learned_state_sha256": "b" * 64,
                }
                checkpoints[key][arm] = {
                    "artifact_kind": "ONLGR_B2_SOLE_FINAL_CHECKPOINT",
                    "revision": config.REVISION, "seed": seed, "arm": arm,
                    "source_identity": {"revision": config.REVISION},
                    "learned_state_sha256": "b" * 64,
                    "path": f"checkpoints/seed_{seed}/{arm}.pt",
                    "sha256_before_evaluation": "a" * 64,
                    "sha256_after_evaluation": "a" * 64,
                    "immutable_before_after": True, "source_identity_exact": True,
                    "envelope_valid": True,
                    "completed_updates": 8, "actor_parameter_count": 1345,
                    "critic_parameter_count": 6785,
                }
                update_fact = {
                    "update_index": 1,
                    "optimizer_steps": 4, "complete_episodes": 32,
                    "boundary_rows": 696, "genuine_joint_policy_rows": 696,
                    "episodes_by_schedule": {schedule: 8 for schedule in config.TRAIN_SCHEDULES},
                    "actor_joint_rows_by_schedule": {schedule: 1 for schedule in config.TRAIN_SCHEDULES},
                    "behavior_log_probabilities_cached_before_epochs": True,
                    "behavior_critic_values_cached_before_epochs": True,
                    "advantages_cached_before_epochs": True,
                    "lambda_returns_cached_before_epochs": True,
                    "caches_unchanged_all_epochs": True, "advantage_normalization": False,
                    "value_clipping": False, "value_coefficient_applications": 1,
                    "terminal_behavior_value": 0.0, "actor_global_scale": 1 / 256,
                }
                per_update_work = {
                    "episodes": 32, "physics_ticks": 8192,
                    "actor_calls": 1392, "critic_calls": 696,
                    "messages": 16384, "transmitted_bits": 32768,
                    "identity_rows": 1392, "identity_unique_within_episodes": True,
                    "identity_schema_valid": True, "reward_service_cost_exact": True,
                    "segment_ownership_exact": True, "terminal_boundary_absent": True,
                    "latency_call_count": 696, "latency_sum_ns": 1,
                    "latency_max_ns": 1, "actor_parameter_count": 1345,
                    "critic_parameter_count": 6785,
                }
                training[key][arm] = {
                    "episodes": 256, "physics_ticks": 256 * 256,
                    "actor_calls": 11136, "critic_calls": 5568,
                    "messages": 131072, "transmitted_bits": 262144,
                    "identity_rows": 11136, "identity_unique_within_episodes": True,
                    "identity_schema_valid": True, "reward_service_cost_exact": True,
                    "segment_ownership_exact": True, "terminal_boundary_absent": True,
                    "latency_call_count": 5568, "latency_sum_ns": 1,
                    "latency_max_ns": 1, "actor_parameter_count": 1345,
                    "critic_parameter_count": 6785, "completed_updates": 8,
                    "optimizer_steps": 32, "update_facts": [update_fact] * 8,
                    "per_update_work_facts": [per_update_work] * 8,
                }
        return panels, checkpoints, training, keep_pairing

    def test_exact_counts_complete_and_retention_branch(self) -> None:
        package = self._package()
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertTrue(result["PACKAGE_VALID"])
        self.assertTrue(result["MARK_SUPPORT_OK"])
        self.assertTrue(result["branches"]["RETAIN_RATE_FLEX"])
        self.assertFalse(result["branches"]["ABSORB_TO_GLOBAL_RATE"])
        self.assertEqual(result["registered_work"]["total_team_ticks"], 1_310_720)

    def test_supported_nonpassage_absorbs_but_support_failure_is_inconclusive(self) -> None:
        package = self._package(delta=0.0)
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertTrue(result["branches"]["ABSORB_TO_GLOBAL_RATE"])
        package = self._package(delta=0.03, support=False)
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertTrue(result["branches"]["INCONCLUSIVE_INSUFFICIENT_VOLUNTARY_SUPPORT"])
        self.assertFalse(result["branches"]["RETAIN_RATE_FLEX"])
        self.assertFalse(result["branches"]["ABSORB_TO_GLOBAL_RATE"])

    def test_missing_mandatory_report_and_forged_r04_checkpoint_invalidate_package(self) -> None:
        package = self._package()
        del package[0]["iid"]["137"]["RATE-FLEX"]["rate_distributions"]
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertFalse(result["PACKAGE_VALID"])
        self.assertIn("iid:137:RATE-FLEX.rate_distributions", result["missing_facts"])

        package = self._package()
        package[1]["137"]["RATE-FLEX"]["artifact_kind"] = "ONLGR_B1_FINAL_CHECKPOINT"
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertFalse(result["PACKAGE_VALID"])
        self.assertIn("checkpoint_envelopes_and_hashes_exact", result["failed_conformance"])

        package = self._package()
        package[1]["137"]["RATE-FLEX"]["source_identity"] = {
            "revision": "opportunity_normalized_lease_gated_rebinding_r04",
        }
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertFalse(result["PACKAGE_VALID"])
        self.assertIn("checkpoint_envelopes_and_hashes_exact", result["failed_conformance"])

        package = self._package()
        del package[0]["safety"]
        result = analysis.analyze_complete_package(
            panels=package[0], checkpoints=package[1], training=package[2],
            keep_pairing=package[3], source_identity_exact=True, atomic_frontier_exact=True,
            expected_source_identity={"revision": config.REVISION},
        )
        self.assertFalse(result["PACKAGE_VALID"])

    def test_source_identity_and_runner_do_not_read_or_bind_r04_sources(self) -> None:
        identity = run.source_identity()
        paths = tuple(identity["files"])
        self.assertTrue(paths)
        self.assertTrue(all("/b2/" in path or "ONLGR_B2_" in path for path in paths))
        self.assertFalse(any(path.endswith(("/run.py", "/host.py", "/analysis.py")) and "/b2/" not in path for path in paths))
        runner_source = Path(run.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from ..", runner_source)
        self.assertNotIn("recovery", runner_source.lower())


if __name__ == "__main__":
    unittest.main()
