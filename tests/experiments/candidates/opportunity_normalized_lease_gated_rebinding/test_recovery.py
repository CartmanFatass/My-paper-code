from __future__ import annotations

import contextlib
import io
import inspect
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

import numpy as np

from experiments.candidates.opportunity_normalized_lease_gated_rebinding import recovery
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.models import MarkedLearner


class FrozenLearnerTests(unittest.TestCase):
    def test_joint_log_probability_is_exact_inference_only_facade(self) -> None:
        reference = MarkedLearner(17, "ONLGR")
        frozen = recovery.FrozenLearner(
            reference.seed, reference.arm, reference.actor, reference.critic,
        )
        features = np.arange(28, dtype=np.float32).reshape(2, 14) / 31.0
        exposure = np.asarray([3.0, 11.0], dtype=np.float32)
        actions = np.asarray([2, 1], dtype=np.int64)
        mask = np.asarray([True, False], dtype=np.bool_)

        self.assertEqual(
            frozen.joint_log_probability(features, exposure, actions, mask),
            reference.joint_log_probability(features, exposure, actions, mask),
        )
        self.assertFalse(hasattr(frozen, "optimizer"))
        self.assertFalse(hasattr(frozen, "update"))
        self.assertTrue(all(not parameter.requires_grad for parameter in frozen.actor.parameters()))
        self.assertTrue(all(not parameter.requires_grad for parameter in frozen.critic.parameters()))


class AtomicFrontierTests(unittest.TestCase):
    def test_existing_exact_cell_is_reused_without_recomputation(self) -> None:
        calls = 0

        def work(ledger: recovery.RecoveryLedger) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {"complete": True}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common = {
                "frontier_root": root,
                "cell_id": "native:17",
                "marker_sha256": "a" * 64,
                "checkpoint_sha256": {"17:ONLGR": "b" * 64},
                "source_identity": {"composite_sha256": "s1"},
                "slice_started": time.perf_counter(),
                "slice_seconds": 60.0,
            }
            first = recovery._run_or_load_cell(**common, work=work)
            second = recovery._run_or_load_cell(**common, work=work)

            self.assertEqual(calls, 1)
            self.assertEqual(first, second)
            self.assertEqual(second["data"], {"complete": True})

    def test_frontier_identity_tamper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common = {
                "frontier_root": root,
                "cell_id": "iid:31",
                "marker_sha256": "c" * 64,
                "checkpoint_sha256": {"31:ONLGR": "d" * 64},
                "source_identity": {"composite_sha256": "s1"},
                "slice_started": time.perf_counter(),
                "slice_seconds": 60.0,
            }
            recovery._run_or_load_cell(
                **common, work=lambda ledger: {"complete": True},
            )
            with self.assertRaises(recovery.RecoveryRefused):
                recovery._run_or_load_cell(
                    **{**common, "marker_sha256": "e" * 64},
                    work=lambda ledger: {"complete": False},
                )

    def test_frontier_source_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common = {
                "frontier_root": root,
                "cell_id": "safety:47",
                "marker_sha256": "f" * 64,
                "checkpoint_sha256": {"47:ONLGR": "0" * 64},
                "source_identity": {"composite_sha256": "source-v1"},
                "slice_started": time.perf_counter(),
                "slice_seconds": 60.0,
            }
            recovery._run_or_load_cell(
                **common, work=lambda ledger: {"complete": True},
            )
            with self.assertRaises(recovery.RecoveryRefused):
                recovery._run_or_load_cell(
                    **{**common, "source_identity": {"composite_sha256": "source-v2"}},
                    work=lambda ledger: {"complete": False},
                )

    def test_expired_slice_cannot_reuse_existing_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common = {
                "frontier_root": root,
                "cell_id": "probes:61",
                "marker_sha256": "1" * 64,
                "checkpoint_sha256": {"61:ONLGR": "2" * 64},
                "source_identity": {"composite_sha256": "source-v1"},
                "slice_started": time.perf_counter(),
                "slice_seconds": 60.0,
            }
            recovery._run_or_load_cell(
                **common, work=lambda ledger: {"complete": True},
            )
            with self.assertRaises(recovery.RecoverySliceIncomplete):
                recovery._run_or_load_cell(
                    **{
                        **common,
                        "slice_started": time.perf_counter() - 2.0,
                        "slice_seconds": 1.0,
                    },
                    work=lambda ledger: self.fail("existing cell must not be evaluated after deadline"),
                )

    def test_atomic_write_checks_deadline_after_serialization_before_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "cell.json"
            with self.assertRaises(recovery.RecoverySliceIncomplete):
                recovery._atomic_json(
                    target, {"data": {"complete": True}},
                    before_replace=lambda: recovery._enforce_atomic_replace_window(
                        time.perf_counter() - 2.0, 1.0,
                    ),
                )
            self.assertFalse(target.exists())
            self.assertEqual(list(target.parent.glob("*.tmp")), [])

    def test_cell_commit_is_checked_again_after_atomic_replace(self) -> None:
        boundaries: list[str] = []
        real_check = recovery._enforce_slice_deadline

        def record(started: float, seconds: float, boundary: str) -> None:
            boundaries.append(boundary)
            real_check(started, seconds, boundary)

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            recovery, "_enforce_slice_deadline", side_effect=record,
        ):
            recovery._run_or_load_cell(
                frontier_root=Path(directory), cell_id="native:79",
                marker_sha256="3" * 64,
                checkpoint_sha256={"79:ONLGR": "4" * 64},
                source_identity={"composite_sha256": "source-v1"},
                slice_started=time.perf_counter(), slice_seconds=60.0,
                work=lambda ledger: {"complete": True},
            )
        self.assertIn("a completed atomic cell commit", boundaries)

    def test_historical_marker_is_reused_only_on_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker.json"
            expected = {"artifact_kind": "marker", "path": "exact", "hashes": {"a": "b"}}
            recovery._validate_or_create_marker(marker, expected)
            before = marker.read_bytes()
            recovery._validate_or_create_marker(marker, expected)
            self.assertEqual(marker.read_bytes(), before)
            with self.assertRaises(recovery.RecoveryRefused):
                recovery._validate_or_create_marker(marker, {**expected, "path": "changed"})
            self.assertEqual(marker.read_bytes(), before)


class FrontierVersioningTests(unittest.TestCase):
    def test_sealed_v2_is_preserved_and_ignored_while_v3_is_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recovery_root = Path(directory)
            v2 = recovery_root / "checkpoint_only_core_frontier_v2"
            v2.mkdir()
            sealed = v2 / "sealed-cell.json"
            sealed.write_bytes(b"sealed-v2-evidence")
            before = sealed.read_bytes()

            active = recovery._prepare_frontier_root(recovery_root)

            self.assertEqual(active.name, "checkpoint_only_core_frontier_v3")
            self.assertEqual(list(active.iterdir()), [])
            self.assertEqual(sealed.read_bytes(), before)

    def test_fresh_v3_cells_are_bound_to_corrected_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            active = recovery._prepare_frontier_root(Path(directory))
            identity = {"composite_sha256": "corrected-source"}
            cell = recovery._run_or_load_cell(
                frontier_root=active, cell_id="native:97",
                marker_sha256="5" * 64,
                checkpoint_sha256={"97:ONLGR": "6" * 64},
                source_identity=identity,
                slice_started=time.perf_counter(), slice_seconds=60.0,
                work=lambda ledger: {"complete": True},
            )

            self.assertEqual(cell["frontier_revision"], recovery.FRONTIER_REVISION)
            self.assertEqual(cell["source_identity"], identity)
            cell_names = [path.name for path in active.iterdir()]
            self.assertEqual(cell_names, ["native__97.json"])
            self.assertNotIn("checkpoint_only_core_frontier_v2", cell_names)

    def test_unexpected_recovery_root_entry_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recovery_root = Path(directory)
            (recovery_root / "checkpoint_only_core_frontier_v2").mkdir()
            (recovery_root / "unexpected-evidence.txt").write_text("preserve", encoding="utf-8")

            with self.assertRaises(recovery.RecoveryRefused):
                recovery._prepare_frontier_root(recovery_root)

            self.assertFalse((recovery_root / recovery.FRONTIER_DIRECTORY).exists())
            self.assertTrue((recovery_root / "unexpected-evidence.txt").exists())


class ProcessEnvelopeTests(unittest.TestCase):
    def test_slice_limit_is_strictly_below_four_hours(self) -> None:
        self.assertLess(recovery.MAX_SLICE_SECONDS, 4 * 60 * 60)
        self.assertEqual(recovery.MAX_RSS_BYTES, 1024**3)

    def test_legacy_caps_are_not_executor_stop_conditions(self) -> None:
        source = inspect.getsource(recovery.RecoveryLedger.check)
        self.assertNotIn("total_tick_cap", source)
        self.assertNotIn("wall_seconds", source)
        self.assertNotIn("CUMULATIVE_HARD_MAX_TICKS", source)
        self.assertIn("MAX_RSS_BYTES", source)
        self.assertIn("slice_seconds", source)

    def test_incomplete_slice_emits_no_partial_stdout(self) -> None:
        output = io.StringIO()
        argv = [
            "checkpoint-only-core-reevaluate",
            "--original-output-root", "original",
            "--original-result", "original-result.json",
            "--original-terminal", "terminal.json",
            "--recovery-output-root", "recovery",
            "--result", "result.json",
        ]
        with mock.patch.object(
            recovery, "recover", side_effect=recovery.RecoverySliceIncomplete("slice"),
        ), contextlib.redirect_stdout(output):
            code = recovery.main(argv)
        self.assertEqual(code, 75)
        self.assertEqual(output.getvalue(), "")

    def test_requested_slice_deadline_applies_to_finalization(self) -> None:
        with self.assertRaises(recovery.RecoverySliceIncomplete) as raised:
            recovery._enforce_slice_deadline(
                time.perf_counter() - 2.0, 1.0, "atomic result finalization",
            )
        self.assertIn("atomic result finalization", str(raised.exception))

    def test_source_identity_binds_frozen_contract_and_all_semantic_modules(self) -> None:
        identity = recovery._source_identity()
        self.assertEqual(set(identity["files"]), set(recovery.SOURCE_IDENTITY_FILES))
        contract = identity["frozen_contract"]
        self.assertEqual(contract["iid_reward_decomposition"]["definition"], "R_IID := S_IID - C_IID")
        self.assertEqual(contract["native_episodes"], 32)
        self.assertEqual(contract["iid_episodes"], 32)


class CompletionSemanticsTests(unittest.TestCase):
    def _facts(self) -> dict[str, bool]:
        return {
            "exact_composite_revision": True,
            "mandatory_core_tick_accounting_exact": True,
            **{name: True for name in recovery.PRESENT_SAFETY_RESOURCE_CLAIM_GATES},
        }

    def test_present_failed_latency_gate_does_not_withhold_complete_artifact(self) -> None:
        facts = self._facts()
        facts["ONLGR_latency_at_most_1_10_RAW"] = False

        complete, technical, claim_gates = recovery._completion_partition([], facts)

        self.assertTrue(complete)
        self.assertTrue(all(technical.values()))
        self.assertFalse(claim_gates["ONLGR_latency_at_most_1_10_RAW"])

    def test_actual_all_expected_conformance_dictionary_completes(self) -> None:
        facts = {
            "exact_composite_revision": True,
            "all_24_sole_final_checkpoints_valid_and_immutable": True,
            "no_optimizer_constructed_or_loaded_for_recovery": True,
            "gradient_calculation_disabled": True,
            "training_or_parameter_update_performed": False,
            "analytic_probability_and_full_jacobian": True,
            "partition_probability_and_full_jacobian": True,
            "KEEP_grid_equality": True,
            "switch_twin": True,
            "IID_filtration_and_pairing": True,
            "IID_reward_decomposition": True,
            "exposure_closed_form": True,
            "action_before_service": True,
            "reward_service_cost_per_tick": True,
            "segment_ownership": True,
            "terminal_boundary_absence": True,
            "safety": True,
            "matched_actor_critic_parameters": True,
            "matched_native_actor_calls": True,
            "matched_native_resource_work": True,
            "ONLGR_latency_at_most_1_10_RAW": True,
            "mandatory_core_tick_accounting_exact": True,
            "frontier_evaluator_analyzer_source_identity_exact": True,
            "all_atomic_cell_commits_within_process_slice_limit": True,
            "recovery_RSS_strictly_below_1GiB": True,
            "recovery_exactly_one_CPU_worker": True,
            "recovery_no_GPU_use": True,
        }

        complete, technical, claim_gates = recovery._completion_partition([], facts)

        self.assertTrue(complete)
        self.assertFalse(technical["training_or_parameter_update_performed"])
        self.assertTrue(all(claim_gates.values()))

    def test_performed_training_violates_expected_recovery_polarity(self) -> None:
        facts = self._facts()
        facts["training_or_parameter_update_performed"] = True
        complete, _technical, _claims = recovery._completion_partition([], facts)
        self.assertFalse(complete)

    def test_each_present_safety_resource_failure_is_claim_only(self) -> None:
        for failed_name in recovery.PRESENT_SAFETY_RESOURCE_CLAIM_GATES:
            with self.subTest(failed_name=failed_name):
                facts = self._facts()
                facts[failed_name] = False
                complete, _technical, claim_gates = recovery._completion_partition([], facts)
                self.assertTrue(complete)
                self.assertFalse(claim_gates[failed_name])

    def test_missing_data_or_technical_incoherence_still_prevents_completion(self) -> None:
        facts = self._facts()
        complete_missing, _technical, _claims = recovery._completion_partition(
            ["native:17:ONLGR:CONST-4"], facts,
        )
        facts["mandatory_core_tick_accounting_exact"] = False
        complete_incoherent, _technical, _claims = recovery._completion_partition([], facts)

        self.assertFalse(complete_missing)
        self.assertFalse(complete_incoherent)

    def test_complete_over_45_minute_aggregate_is_retained_with_fence_reported(self) -> None:
        historical = recovery._historical_non_gating_process_facts(
            {"wall_seconds": 45 * 60 + 1.0},
        )
        complete, _technical, _claims = recovery._completion_partition([], self._facts())

        self.assertTrue(complete)
        self.assertFalse(historical["historical_2700s_wall_fence_pass_for_checkpoint_only_core"])
        self.assertFalse(
            historical["historical_2700s_wall_fence_execution_or_completeness_authority"]
        )
        self.assertFalse(
            historical[
                "historical_exact_once_no_rescue_marker_execution_or_completeness_authority"
            ]
        )


if __name__ == "__main__":
    unittest.main()
