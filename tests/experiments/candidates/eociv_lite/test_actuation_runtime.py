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
        assert total == sum(runner.env.reward_trace)

    def test_receipt_fail_closed_modes(self):
        env = gate_mod._make_sibling(PROFILE, 1)
        runner = art.ArmEpisodeRunner(
            env, "LR", tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        gate_mod._drive_to(env, sib.EVENT_TIMES[0])
        opportunity = env.opportunity(0)
        actuation = sib.actuate(
            "LR", opportunity, env.focal_payload(0), d_learned=True, d_control=True
        )
        receipt = art.make_receipt(
            opportunity, actuation, runner_binding=runner.runner_binding
        )
        focal = opportunity.identity.receiver_member_key
        capacity = env.ledger.member_capacity

        def block():
            b = np.zeros((capacity, art.SLOT_DIM), dtype=np.float32)
            b[focal, :] = art.slot_features(actuation.slot)
            return b

        with pytest.raises(art.ReceiptError, match="missing"):
            runner._verify_and_consume(None, opportunity, actuation, block(), focal)
        with pytest.raises(art.ReceiptError, match="focal receiver"):
            runner._verify_and_consume(receipt, opportunity, actuation, block(), focal + 1)
        with pytest.raises(art.ReceiptError, match="slot digest"):
            runner._verify_and_consume(
                receipt, opportunity,
                replace(actuation, slot=sib._pad_slot(b"EOCIV-ALTERED")),
                block(), focal,
            )
        runner._verify_and_consume(receipt, opportunity, actuation, block(), focal)
        with pytest.raises(art.ReceiptError, match="duplicate"):
            runner._verify_and_consume(receipt, opportunity, actuation, block(), focal)

    def test_pro_c1_negative_matrix(self):
        """Pro's seven required negative tests for the corrected binding."""
        env = gate_mod._make_sibling(PROFILE, 1)
        runner = art.ArmEpisodeRunner(
            env, "LR", tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        gate_mod._drive_to(env, sib.EVENT_TIMES[0])
        opportunity = env.opportunity(0)
        actuation = sib.actuate(
            "LR", opportunity, env.focal_payload(0), d_learned=True, d_control=True
        )
        receipt = art.make_receipt(
            opportunity, actuation, runner_binding=runner.runner_binding
        )
        focal = opportunity.identity.receiver_member_key
        capacity = env.ledger.member_capacity

        def block():
            b = np.zeros((capacity, art.SLOT_DIM), dtype=np.float32)
            b[focal, :] = art.slot_features(actuation.slot)
            return b

        # 1. Correct receipt but altered focal slot tensor.
        altered = block()
        altered[focal, 0] += np.float32(1.0 / 255.0)
        with pytest.raises(art.ReceiptError, match="focal policy slot tensor"):
            runner._verify_and_consume(receipt, opportunity, actuation, altered, focal)
        # 2. Correct focal slot plus a nonzero non-focal slot.
        leaky = block()
        leaky[(focal + 1) % capacity, 5] = np.float32(0.25)
        with pytest.raises(art.ReceiptError, match="non-focal"):
            runner._verify_and_consume(receipt, opportunity, actuation, leaky, focal)
        # 3. Correct slot but wrong source identity.
        wrong_source = replace(
            receipt,
            opportunity_identity=replace(
                receipt.opportunity_identity,
                source_member_key=receipt.opportunity_identity.source_member_key + 1,
            ),
        )
        with pytest.raises(art.ReceiptError, match="identity"):
            runner._verify_and_consume(wrong_source, opportunity, actuation, block(), focal)
        # 4. Wrong profile / episode / event / spell epoch.
        for field, value in (
            ("profile_registration_id", "train_5_3_7_6"),
            ("episode_id", 2),
            ("lifecycle_event_index", 1),
            ("receiver_active_spell_epoch",
             receipt.opportunity_identity.receiver_active_spell_epoch + 1),
        ):
            bad = replace(
                receipt,
                opportunity_identity=replace(
                    receipt.opportunity_identity, **{field: value}
                ),
            )
            with pytest.raises(art.ReceiptError, match="identity"):
                runner._verify_and_consume(bad, opportunity, actuation, block(), focal)
        # 5. Altered route, decision source, or ingestion cost.
        with pytest.raises(art.ReceiptError, match="route"):
            runner._verify_and_consume(
                receipt, opportunity, replace(actuation, route="NEUTRAL"), block(), focal
            )
        with pytest.raises(art.ReceiptError, match="decision source"):
            runner._verify_and_consume(
                receipt, opportunity, replace(actuation, decision_source="D_C"),
                block(), focal,
            )
        with pytest.raises(art.ReceiptError, match="ingestion cost"):
            runner._verify_and_consume(
                receipt, opportunity, replace(actuation, ingestion_cost=0),
                block(), focal,
            )
        # 6. Correct policy input but altered action after the forward pass.
        slot_block = block()
        view = env.observe()
        actions, kernel, hidden = runner.policy.forward(
            view.observations, view.active_mask, slot_block,
            runner.hidden, runner.noise[env.time],
        )
        runner._verify_and_consume(receipt, opportunity, actuation, slot_block, focal)
        action_receipt = art.ActionReceipt(
            actuation_receipt_digest=art.receipt_digest(receipt),
            policy_input_digest=art._digest(
                view.observations, view.active_mask, slot_block, runner.hidden
            ),
            kernel_digest=art._digest(kernel),
            sampled_action_digest=art._digest(actions),
            recurrent_write_digest=art._digest(hidden),
            physical_tick=env.time,
        )
        tampered = actions.copy()
        tampered[focal, 0] = np.float32(0.0) if tampered[focal, 0] else np.float32(0.5)
        with pytest.raises(art.ReceiptError, match="altered after"):
            art.bound_step(env, tampered, action_receipt)
        with pytest.raises(art.ReceiptError, match="missing action receipt"):
            art.bound_step(env, actions, None)
        # The untampered action with its receipt is accepted.
        reward, terminated, _ = art.bound_step(env, actions, action_receipt)
        assert not terminated and 0.0 <= reward <= 1.0
        # 7. A receipt from another runner at the same tick is rejected by
        # full block identity.
        env2 = gate_mod._make_sibling(PROFILE, 1)
        other = art.ArmEpisodeRunner(
            env2, "CR", tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        cross = art.make_receipt(
            opportunity, actuation, runner_binding=other.runner_binding
        )
        fresh = art.ArmEpisodeRunner(
            gate_mod._make_sibling(PROFILE, 1), "LR",
            tape_seed=gate_mod.TAPE_SEED,
            d_learned_fn=gate_mod.registered_learned_decision,
        )
        gate_mod._drive_to(fresh.env, sib.EVENT_TIMES[0])
        with pytest.raises(art.ReceiptError, match="cross-runner"):
            fresh._verify_and_consume(cross, opportunity, actuation, block(), focal)

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
