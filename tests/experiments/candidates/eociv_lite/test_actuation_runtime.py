"""Focused tests for the executable actuation edge (receipt, policy, runner)."""

import hashlib
from dataclasses import replace

import numpy as np
import pytest

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import sibling_env as sib

PROFILE = roster_env.TRAIN_PROFILES[0]


def _runner(arm: str, episode_id: int = 0, **kwargs) -> art.ArmEpisodeRunner:
    env = gate_mod._make_sibling(PROFILE, episode_id)
    return art.ArmEpisodeRunner(
        env, arm, tape_seed=gate_mod.TAPE_SEED,
        d_learned_fn=gate_mod.registered_learned_decision, **kwargs
    )


def _boundary_materials(runner: art.ArmEpisodeRunner):
    gate_mod._drive_to(runner.env, sib.EVENT_TIMES[0])
    slot, receipt, opportunity, actuation, _ = runner._boundary(0)
    view = runner.env.observe()
    kwargs = dict(
        opportunity=opportunity,
        actuation=actuation,
        observations=view.observations,
        active_mask=view.active_mask,
        slot_block=slot,
        noise=runner.noise[runner.env.time],
    )
    return receipt, kwargs


class TestSlotAndPolicy:
    def test_slot_features_are_lossless_and_width_checked(self):
        slot = bytes(range(32))
        features = art.slot_features(slot)
        assert features.dtype == np.float32 and features.shape == (32,)
        assert np.array_equal(features * np.float32(255.0), np.arange(32, dtype=np.float32))
        with pytest.raises(ValueError):
            art.slot_features(b"short")

    def test_policy_is_deterministic_and_registered(self):
        p1 = art.CommonPolicy(8)
        p2 = art.CommonPolicy(8)
        assert np.array_equal(p1.w_obs, p2.w_obs)
        assert np.array_equal(p1.w_slot, p2.w_slot)
        obs = np.zeros((8, roster_env.OBSERVATION_DIM), dtype=np.float32)
        mask = np.ones(8, dtype=np.bool_)
        slot = np.zeros((8, art.SLOT_DIM), dtype=np.float32)
        noise = np.zeros((8, roster_env.ACTION_DIM), dtype=np.float32)
        a1, k1, h1 = p1.forward(obs, mask, slot, p1.initial_state(), noise)
        a2, k2, h2 = p2.forward(obs, mask, slot, p2.initial_state(), noise)
        assert np.array_equal(a1, a2) and np.array_equal(k1, k2) and np.array_equal(h1, h2)
        assert np.all(np.abs(a1) < 1.0)

    def test_slot_reaches_only_the_fed_row(self):
        policy = art.CommonPolicy(8)
        obs = np.zeros((8, roster_env.OBSERVATION_DIM), dtype=np.float32)
        mask = np.ones(8, dtype=np.bool_)
        noise = np.zeros((8, roster_env.ACTION_DIM), dtype=np.float32)
        slot_a = np.zeros((8, art.SLOT_DIM), dtype=np.float32)
        slot_b = slot_a.copy()
        slot_b[3, :] = art.slot_features(sib._pad_slot(b"EOCIV-SIGNAL:B"))
        a_a, _, h_a = policy.forward(obs, mask, slot_a, policy.initial_state(), noise)
        a_b, _, h_b = policy.forward(obs, mask, slot_b, policy.initial_state(), noise)
        differs = ~np.all(np.isclose(a_a, a_b), axis=1)
        assert differs[3] and not differs[[0, 1, 2, 4, 5, 6, 7]].any()
        assert not np.array_equal(h_a[3], h_b[3])


class TestRunner:
    def test_full_episode_boundary_records(self):
        runner = _runner("LR")
        total = runner.run_episode()
        assert runner.env.time == roster_env.HORIZON
        assert len(runner.step_traces) == roster_env.HORIZON
        assert len(runner.boundary_records) == 3
        for record, tick in zip(runner.boundary_records, sib.EVENT_TIMES):
            assert record.receipt.physical_tick == tick
            assert record.receipt.route == "REAL"
            assert record.receipt.slot_digest == hashlib.sha256(record.slot).hexdigest()
            trace = runner.step_traces[tick]
            assert record.action_receipt.policy_input_digest == trace.input_digest
            assert record.action_receipt.kernel_digest == trace.kernel_digest
            assert record.action_receipt.sampled_action_digest == trace.action_digest
            assert record.action_receipt.recurrent_write_digest == trace.hidden_digest
        assert total == sum(runner.env.reward_trace)

    def test_receipt_fail_closed_modes(self):
        runner = _runner("LR", episode_id=1)
        receipt, kwargs = _boundary_materials(runner)
        with pytest.raises(art.ReceiptError):
            runner.bound_step(receipt=None, **kwargs)
        other = _runner("LR", episode_id=2)
        other_receipt, _ = _boundary_materials(other)
        with pytest.raises(art.ReceiptError):
            runner.bound_step(receipt=other_receipt, **kwargs)
        focal = kwargs["opportunity"].identity.receiver_member_key
        wrong_identity = replace(
            receipt.opportunity_identity,
            receiver_member_key=(focal + 1) % runner.env.ledger.member_capacity,
        )
        with pytest.raises(art.ReceiptError):
            runner.bound_step(
                receipt=replace(receipt, opportunity_identity=wrong_identity),
                **kwargs,
            )
        altered_focal = kwargs["slot_block"].copy()
        altered_focal[focal, 0] += np.float32(1.0 / 255.0)
        with pytest.raises(art.ReceiptError):
            runner.bound_step(
                receipt=receipt, **{**kwargs, "slot_block": altered_focal}
            )
        nonfocal = kwargs["slot_block"].copy()
        nonfocal[(focal + 1) % nonfocal.shape[0], 0] = np.float32(1.0)
        with pytest.raises(art.ReceiptError):
            runner.bound_step(receipt=receipt, **{**kwargs, "slot_block": nonfocal})
        for altered in (
            replace(receipt, route="NEUTRAL"),
            replace(receipt, decision_source="D_L"),
            replace(receipt, ingestion_cost=receipt.ingestion_cost + 1),
        ):
            with pytest.raises(art.ReceiptError):
                runner.bound_step(receipt=altered, **kwargs)
        runner.bound_step(receipt=receipt, **kwargs)
        with pytest.raises(art.ReceiptError):
            runner.bound_step(receipt=receipt, **kwargs)

    def test_action_receipt_rejects_altered_digest_material(self):
        runner = _runner("LR", episode_id=3)
        receipt, kwargs = _boundary_materials(runner)
        actions, kernel, new_hidden, action_receipt = runner.bound_step(
            receipt=receipt, **kwargs
        )
        with pytest.raises(art.ReceiptError):
            runner.verify_action_receipt(
                replace(action_receipt, sampled_action_digest="0" * 64),
                opportunity=kwargs["opportunity"],
                actuation=kwargs["actuation"],
                observations=kwargs["observations"],
                active_mask=kwargs["active_mask"],
                slot_block=kwargs["slot_block"],
                hidden=runner.hidden,
                kernel=kernel,
                actions=actions,
                new_hidden=new_hidden,
            )

    def test_stale_post_action_receipt_fails_closed(self):
        runner = _runner("LR", episode_id=4)
        receipt, kwargs = _boundary_materials(runner)
        runner.env.step(roster_env.constructive_actions(runner.env.observe()))
        with pytest.raises(art.ReceiptError):
            runner.bound_step(receipt=receipt, **kwargs)

    def test_lr_cr_byte_identity_and_ls_divergence(self):
        lr = _runner("LR", episode_id=2)
        cr = _runner("CR", episode_id=2)
        lr.run_episode()
        cr.run_episode()
        assert lr.step_traces == cr.step_traces
        # A selective arm forced to neutralize every boundary must diverge.
        env = gate_mod._make_sibling(PROFILE, 2)
        ls_forced = art.ArmEpisodeRunner(
            env, "LS", tape_seed=gate_mod.TAPE_SEED, d_learned_fn=lambda w: False
        )
        ls_forced.run_episode()
        assert all(
            record.actuation_route == "NEUTRAL" for record in ls_forced.boundary_records
        )
        assert ls_forced.step_traces != lr.step_traces

    def test_body_mutation_reaches_first_post_event_input_only(self):
        states_a = (sib.SHOCK_A, sib.SHOCK_NONE, sib.SHOCK_A)
        states_b = (sib.SHOCK_B, sib.SHOCK_NONE, sib.SHOCK_A)
        env_a = gate_mod._make_sibling(PROFILE, 3, shock_states=states_a)
        env_b = gate_mod._make_sibling(PROFILE, 3, shock_states=states_b)
        runner_a = art.ArmEpisodeRunner(
            env_a, "LR", tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        runner_b = art.ArmEpisodeRunner(
            env_b, "LR", tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        runner_a.run_episode()
        runner_b.run_episode()
        boundary = sib.EVENT_TIMES[0]
        assert runner_a.step_traces[:boundary] == runner_b.step_traces[:boundary]
        assert (
            runner_a.step_traces[boundary].input_digest
            != runner_b.step_traces[boundary].input_digest
        )
        assert runner_a.boundary_records[0].w_minus == runner_b.boundary_records[0].w_minus
