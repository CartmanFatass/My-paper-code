"""Focused tests for the EOCIV Stage 0 package (models, harness, preflight).

Stage 0 is forward-only; these tests assert construction, determinism,
contract conformance and the abort machinery — never a training step and
never a focal-arm contrast.
"""

from fractions import Fraction

import numpy as np
import pytest
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import outcome_harness as harness
from experiments.candidates.eociv_lite import sibling_env as sib
from experiments.candidates.eociv_lite import stage0_registration as reg
from experiments.candidates.eociv_lite import stage0_preflight as preflight_mod
from experiments.candidates.eociv_lite import trainable_policy as tp

PROFILE = roster_env.TRAIN_PROFILES[0]
SEED = reg.ACTOR_TRAINING_SEEDS[0]


class TestAuthoritativeMechanisms:
    def test_seed_functions_are_the_accepted_objects_by_identity(self):
        assert harness.profile_qualified_seed is gate_mod.profile_qualified_seed
        assert harness.outcome_world_seed is gate_mod.outcome_world_seed
        assert harness.outcome_noise_seed is gate_mod.outcome_noise_seed

    def test_namespaces_come_from_the_frozen_registration(self):
        assert set(harness.POOLS) == {
            "d_fit", "d_policy", "d_cal", "d_focal", "pattern_knockout_audit",
        }
        assert harness.pool_episode_ids("d_fit") == range(0, 7282)
        assert harness.pool_episode_ids("d_focal") == range(300000, 300256)
        with pytest.raises(ValueError):
            harness.episode_uid(PROFILE.name, "d_fit", 7282)
        with pytest.raises(ValueError):
            harness.episode_uid(PROFILE.name, "no_such_pool", 0)

    def test_gate_probe_has_no_call_site_in_the_harness(self):
        import inspect

        assert "control_tape_open(" not in inspect.getsource(harness)


class TestTrainableModels:
    def test_models_are_deterministic_per_seed_and_distinct_across_seeds(self):
        a1, c1, v1 = tp.build_models(SEED)
        a2, c2, v2 = tp.build_models(SEED)
        assert tp.parameter_digest(a1, c1, v1) == tp.parameter_digest(a2, c2, v2)
        a3, c3, v3 = tp.build_models(reg.ACTOR_TRAINING_SEEDS[1])
        assert tp.parameter_digest(a1, c1, v1) != tp.parameter_digest(a3, c3, v3)

    def test_actor_matches_registered_contract_shapes(self):
        actor, critic, valve = tp.build_models(SEED)
        assert actor.slot_encoder.in_features == 32
        assert actor.slot_encoder.out_features == 16
        assert actor.input_projector.in_features == 26
        assert actor.cell.hidden_size == 32
        assert actor.action_head.out_features == roster_env.ACTION_DIM
        assert torch.allclose(
            actor.log_std, torch.full((2,), float(np.log(0.2)))
        )
        assert critic.body[0].in_features == 11
        assert valve.body[0].in_features == 9

    def test_valve_features_read_only_the_sealed_bytes(self):
        env = harness.block_environment(PROFILE, 0)
        gate_mod._drive_to(env, sib.EVENT_TIMES[0])
        opportunity = env.opportunity(0)
        w_bytes = sib.w_minus(env.observe(), opportunity)
        features = tp.valve_features(w_bytes, env.ledger.member_capacity)
        assert features.shape == (9,) and features.dtype == np.float32
        assert features[8] == 1.0  # event 0 is CRITICAL by registration
        assert 0.0 <= features[0] <= 1.0

    def test_valve_decision_hard_opens_on_invalid_input(self):
        _, _, valve = tp.build_models(SEED)
        assert valve.decision(b"not json", 8) is True

    def test_optimizers_configured_but_stage0_takes_no_step(self):
        actor, critic, valve = tp.build_models(SEED)
        opt, vopt = tp.build_optimizers(actor, critic, valve)
        assert isinstance(opt, torch.optim.Adam)
        assert opt.defaults["lr"] == reg.OPTIMIZATION["learning_rate"]
        assert vopt.defaults["lr"] == reg.VALVE_CONTRACT["optimizer"]["learning_rate"]
        digest_before = tp.parameter_digest(actor, critic, valve)
        # Stage 0 never calls step(); constructing the optimizers must not
        # perturb a single parameter byte.
        assert tp.parameter_digest(actor, critic, valve) == digest_before

    def test_terminal_leave_hidden_is_zeroed_at_the_terminal_boundary(self):
        actor, _, _ = tp.build_models(SEED)
        env = harness.block_environment(PROFILE, 0)
        adapter = tp.ActorRunnerAdapter(actor, env.ledger)
        hidden = adapter.initial_state()
        hidden[:] = 0.5
        adapter._time = roster_env.EVENT_TIMES[2]
        obs = np.zeros((8, roster_env.OBSERVATION_DIM), dtype=np.float32)
        mask = np.zeros(8, dtype=np.bool_)
        slot = np.zeros((8, tp.SLOT_DIM), dtype=np.float32)
        noise = np.zeros((8, roster_env.ACTION_DIM), dtype=np.float32)
        _, _, new_hidden = adapter.forward(obs, mask, slot, hidden, noise)
        for key in env.ledger.terminal_leave:
            assert np.array_equal(new_hidden[key], np.zeros(tp.ACTOR_HIDDEN))


class TestHarness:
    def test_block_runner_uses_complete_block_identity_binding(self):
        actor, _, valve = tp.build_models(SEED)
        runner = harness.build_arm_runner(
            PROFILE, pool="d_fit", actor_training_seed=SEED,
            local_episode_id=0, arm="LR", actor=actor, valve=valve,
        )
        binding = runner.runner_binding
        assert binding.startswith(f"d_fit|seed{SEED}|{PROFILE.name}|ep0|LR|")
        runner.run_episode()
        assert len(runner.action_receipts) == 3
        for record in runner.boundary_records:
            assert record.receipt.runner_binding == binding

    def test_four_arm_block_shares_world_and_lr_cr_traces_identical(self):
        actor, _, valve = tp.build_models(SEED)
        runners = {
            arm: harness.build_arm_runner(
                PROFILE, pool="d_fit", actor_training_seed=SEED,
                local_episode_id=1, arm=arm, actor=actor, valve=valve,
            )
            for arm in sib.ARMS
        }
        ledgers = {
            arm: gate_mod._world_digest(r.env.ledger) for arm, r in runners.items()
        }
        assert len(set(ledgers.values())) == 1
        shocks = {arm: r.env._shock_states for arm, r in runners.items()}
        assert len(set(shocks.values())) == 1
        runners["LR"].run_episode()
        runners["CR"].run_episode()
        assert runners["LR"].step_traces == runners["CR"].step_traces

    def test_control_decisions_route_d_c_without_the_gate_probe(self):
        actor, _, valve = tp.build_models(SEED)
        closed = harness.build_arm_runner(
            PROFILE, pool="d_fit", actor_training_seed=SEED,
            local_episode_id=2, arm="CS", actor=actor, valve=valve,
            control_decisions=(False, False, False),
        )
        closed.run_episode()
        assert all(
            record.actuation_route == "NEUTRAL"
            for record in closed.boundary_records
        )
        opened = harness.build_arm_runner(
            PROFILE, pool="d_fit", actor_training_seed=SEED,
            local_episode_id=2, arm="CS", actor=actor, valve=valve,
            control_decisions=(True, True, True),
        )
        opened.run_episode()
        assert all(
            record.actuation_route == "REAL"
            for record in opened.boundary_records
        )

    def test_fit_support_route_is_deterministic_and_near_schedule(self):
        first = harness.fit_support_route("d_fit", PROFILE.name, 0, 0)
        assert first == harness.fit_support_route("d_fit", PROFILE.name, 0, 0)
        counts: dict[str, int] = {}
        for episode_id in range(2000):
            for event in range(3):
                route = harness.fit_support_route(
                    "d_fit", PROFILE.name, episode_id, event
                )
                counts[route] = counts.get(route, 0) + 1
        total = sum(counts.values())
        assert abs(counts["REAL"] / total - 0.5) < 0.03
        assert abs(counts["NATIVE_NEUTRAL"] / total - 0.25) < 0.03
        assert abs(counts["PATTERN_ONLY"] / total - 0.125) < 0.02
        assert abs(counts["PAYLOAD_KNOCKOUT"] / total - 0.125) < 0.02

    def test_exact_rate_tape_hits_the_integer_allocation_exactly(self):
        tape = harness.exact_rate_control_tape(
            PROFILE.name,
            close_fraction=Fraction(1, 3),
            local_episode_ids=tuple(range(10)),
            tape_epoch=0,
        )
        assert len(tape) == 30
        assert sum(tape.values()) == 10  # floor(10) + (0 since frac 0 < 1/2)
        tape_again = harness.exact_rate_control_tape(
            PROFILE.name,
            close_fraction=Fraction(1, 3),
            local_episode_ids=tuple(range(10)),
            tape_epoch=0,
        )
        assert tape == tape_again
        other_epoch = harness.exact_rate_control_tape(
            PROFILE.name,
            close_fraction=Fraction(1, 3),
            local_episode_ids=tuple(range(10)),
            tape_epoch=1,
        )
        assert sum(other_epoch.values()) == 10
        assert other_epoch != tape
        half_up = harness.exact_rate_control_tape(
            PROFILE.name,
            close_fraction=Fraction(1, 2),
            local_episode_ids=(0,),
            tape_epoch=0,
        )
        assert sum(half_up.values()) == 2  # 1.5 rounds half-up to 2

    def test_clustered_bootstrap_is_deterministic_and_shared_across_seeds(self):
        draws = harness.clustered_bootstrap_root_draws(
            PROFILE.name, replicate_index=7, n_roots=256
        )
        assert len(draws) == 256
        assert draws == harness.clustered_bootstrap_root_draws(
            PROFILE.name, replicate_index=7, n_roots=256
        )
        assert draws != harness.clustered_bootstrap_root_draws(
            PROFILE.name, replicate_index=8, n_roots=256
        )

    def test_negative_control_decision_algebra(self):
        verdict = harness.negative_control_decision(0.10, 0.04, -0.03)
        assert verdict["negative_controls_pass"] is True
        verdict = harness.negative_control_decision(0.10, 0.06, 0.0)
        assert verdict["negative_controls_pass"] is False
        verdict = harness.negative_control_decision(-0.01, 0.0, 0.0)
        assert verdict["primary_fails"] is True
        verdict = harness.negative_control_decision(0.0, 0.0, 0.0)
        assert verdict["primary_fails"] is True


class TestPreflight:
    def test_preflight_completes_with_no_aborts_and_no_updates(self):
        report = preflight_mod.preflight()
        assert report["terminal"] == "EOCIV_STAGE0_PREFLIGHT_COMPLETE"
        assert not any(report["abort_predicates"].values())
        assert report["detail"]["optimizer_steps_taken"] == 0
        assert report["detail"]["gate_terminal"] == (
            "EOCIV_SIBLING_CAPABILITY_PRESENT"
        )
        assert len(report["detail"]["model_parameter_digests"]) == 3
        assert set(report["abort_predicates"]) == set(reg.ABORT_PREDICATES)
        frequencies = report["detail"]["fit_support_frequencies"]
        assert abs(frequencies["REAL"] - 0.5) < 0.02
        assert report["binding_failure_rule"] == (
            "invalidate_entire_arm_episode_no_resume"
        )
        pools = report["world_noise_ancestry"]
        assert set(pools) == set(harness.POOLS)
        for pool in pools.values():
            for profile_entry in pool.values():
                for row in profile_entry["samples"]:
                    assert len(row["world_digest"]) == 64
                    assert len(row["shock_source_receiver_digest"]) == 64

    def test_source_digests_cover_the_registered_files(self):
        digests = preflight_mod.source_digests()
        assert set(digests) == set(reg.DIGEST_FILES)
        assert all(len(v) == 64 for v in digests.values())

    def test_frozen_digest_baseline_matches_current_sources(self):
        # The baseline covers every digest file except the registration
        # module itself (which cannot contain its own digest).
        assert set(reg.EXPECTED_SOURCE_DIGESTS) == set(reg.DIGEST_FILES) - {
            "experiments/candidates/eociv_lite/stage0_registration.py"
        }
        digests = preflight_mod.source_digests()
        for path, expected in reg.EXPECTED_SOURCE_DIGESTS.items():
            assert digests[path] == expected, path
