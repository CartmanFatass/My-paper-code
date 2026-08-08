"""Focused tests for the corrected EOCIV pre-PPO capability gate (measured pins)."""

from fractions import Fraction

from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import sibling_env as sib


class TestFullSupportOracle:
    def test_measured_primary_cell_values(self):
        env, _ = gate_mod._forced_pair(gate_mod.GATE_PROFILES[0], 0, 0)
        opportunity = env.opportunity(0)
        oracle = gate_mod.full_support_oracle(
            env.ledger, 0, opportunity.identity.receiver_member_key
        )
        assert oracle.informed_value == Fraction(
            677256339518951415894437545171107478024986982,
            70480833548440535835364716493084811650197801,
        )
        assert oracle.blind_value == Fraction(5471379764104612, 812022094677233)
        assert oracle.reveal_value == Fraction(
            202358662519849191960407727636172717122062818,
            70480833548440535835364716493084811650197801,
        )
        assert oracle.optimal_sets_disjoint_every_step

    def test_primary_cell_interior_b_optimum_matches_pro_reconstruction(self):
        # Pro's loop-6 ruling reconstructed the full-support B-state optimum
        # at segment step 0 as an interior exact-target action
        # x ~= 0.49425157, y ~= 0.42509554 attaining reward 1.  The oracle
        # must find exactly that point; A stays at the zero-effort corner.
        env, _ = gate_mod._forced_pair(gate_mod.GATE_PROFILES[0], 0, 0)
        opportunity = env.opportunity(0)
        oracle = gate_mod.full_support_oracle(
            env.ledger, 0, opportunity.identity.receiver_member_key
        )
        b_point = oracle.per_step_optima[sib.SHOCK_B][0]
        assert b_point == (
            Fraction(1448904029668987874631, 2931511216945674321920),
            Fraction(1087808204784110951817, 2558973455769586892800),
        )
        assert float(b_point[0]) == 0.49425157280434806
        assert float(b_point[1]) == 0.4250955406870225
        assert oracle.per_step_optima[sib.SHOCK_A][0] == (Fraction(0), Fraction(0))
        # The interior optimum attains reward exactly 1 under B.
        keys = gate_mod._active_keys_in_segment(env.ledger, 0)
        geometry = gate_mod.StepGeometry(
            load=gate_mod._frac(env.ledger.load[12]),
            mix=gate_mod._frac(env.ledger.target_mix[12]),
            receiver_caps=(
                gate_mod._frac(env.ledger.capabilities[opportunity.identity.receiver_member_key, 0]),
                gate_mod._frac(env.ledger.capabilities[opportunity.identity.receiver_member_key, 1]),
            ),
            aggregate=(
                sum((gate_mod._frac(env.ledger.capabilities[k, 0]) for k in keys), Fraction(0)),
                sum((gate_mod._frac(env.ledger.capabilities[k, 1]) for k in keys), Fraction(0)),
            ),
        )
        assert geometry.reward(sib.SHOCK_B, *b_point) == 1

    def test_neutral_cell_reveal_is_exactly_zero(self):
        env = gate_mod._make_sibling(gate_mod.GATE_PROFILES[0], 0)
        gate_mod._drive_to(env, sib.EVENT_TIMES[1])
        opportunity = env.opportunity(1)
        oracle = gate_mod.full_support_oracle(
            env.ledger, 1, opportunity.identity.receiver_member_key
        )
        assert oracle.reveal_value == 0

    def test_blind_optimizer_reproduces_segment_total_on_same_scale(self):
        env, _ = gate_mod._forced_pair(gate_mod.GATE_PROFILES[0], 0, 0)
        opportunity = env.opportunity(0)
        oracle = gate_mod.full_support_oracle(
            env.ledger, 0, opportunity.identity.receiver_member_key
        )
        realized, envelope = gate_mod.blind_optimizer_conformance(
            env.ledger, 0, oracle
        )
        assert len(oracle.per_step_blind_optima) == sib.SEGMENT_LENGTH
        assert realized <= oracle.blind_value
        assert envelope == oracle.blind_value - realized
        assert 0 <= float(envelope) < 1e-7
        # A one-step maximum cannot masquerade as the registered segment total.
        assert oracle.blind_value > 1


class TestGate:
    def test_full_gate_terminal_and_counts(self):
        report = gate_mod.gate()
        assert report["terminal"] == "EOCIV_SIBLING_CAPABILITY_PRESENT"
        checks = report["checks"]
        assert all(bool(result["passed"]) for result in checks.values())
        assert len(checks) == 10
        one = checks["1_disabled_projection_reproduces_base_completely"]
        assert one["episodes_compared"] == 24
        assert one["illegal_action_rejection_parity"] is True
        two = checks["2_owner_and_spell_receipts_complete_and_distinct"]
        assert two["opportunities"] == two["eligible"] == 72
        assert two["distinct_identities"] == 72
        assert two["distinct_cluster_ids"] == 72
        assert two["distinct_tape_keys"] == 72
        four = checks["4_receipt_discipline_and_ordering"]
        assert four["fail_closed"] == {
            "missing": True,
            "cross_runner_identity": True,
            "wrong_focal_owner": True,
            "altered_focal_row": True,
            "nonzero_nonfocal_row": True,
            "altered_route": True,
            "altered_decision_source": True,
            "altered_ingestion_cost": True,
            "duplicate": True,
            "altered_action_digest": True,
            "stale_post_action": True,
        }
        five = checks["5_identical_w_minus_disjoint_full_support_optima"]
        assert five["critical_cells"] == five["cells_with_disjoint_optimal_sets"] == 48
        six = checks["6_full_support_strict_value_with_envelopes"]
        assert six["critical_cells"] == 48
        assert six["min_reveal_value"] == (
            "4006373723506941012813514474530777786529678359834693971904620747694484/"
            "2942466151782517510224626170689821337592819255507855782176966403586809"
        )
        # The envelopes are wiring quantities: deterministic on one box but
        # sensitive to numpy/BLAS reduction order across platforms, so the
        # test pins the bounds the science needs, not the 16th digit.  The
        # measured values on the registration box are recorded in the loop-7
        # portfolio document (7.636763256388432e-09 and 8.921690147767336e-08).
        assert 0 < six["max_action_quantization_gap"] < 1e-6
        assert 0 < six["max_blind_action_quantization_gap"] < 1e-6
        assert six["blind_optimizer_conformance"] is True
        assert (
            0
            < six["max_kernel_conformance_error"]
            <= gate_mod.SEGMENT_CONFORMANCE_TOL
        )
        assert six["dominance_ok"] is True
        assert checks["7_neutral_cells_zero_reveal_value"]["neutral_cells"] == 24
        nine = checks["9_controls_execute_and_lr_cr_byte_identity"]
        assert nine["lr_cr_byte_identical"] is True
        ten = checks["10_arm_support_and_frozen_registration"]
        assert ten["support"] == {
            "CRITICAL/CR": 12,
            "CRITICAL/CS": 12,
            "CRITICAL/LR": 12,
            "CRITICAL/LS": 12,
            "NEUTRAL/CR": 6,
            "NEUTRAL/CS": 6,
            "NEUTRAL/LR": 6,
            "NEUTRAL/LS": 6,
        }
        assert ten["registration_declares_gate_probes_not_outcome_design"] is True

    def test_reveal_extremes_and_dominance(self):
        report = gate_mod.gate()
        six = report["checks"]["6_full_support_strict_value_with_envelopes"]
        values = sorted(Fraction(row["reveal_value"]) for row in six["rows"])
        assert float(values[0]) == 1.3615700289636021
        assert float(values[-1]) == 3.3693454610424074
        assert values[0] >= gate_mod.REVEAL_FLOOR
        assert float(values[0]) >= gate_mod.DOMINANCE_FACTOR * six["envelope_sum"]

    def test_w_minus_identical_across_hidden_pair(self):
        env_a, env_b = gate_mod._forced_pair(gate_mod.GATE_PROFILES[1], 3, 2)
        opp_a = env_a.opportunity(2)
        opp_b = env_b.opportunity(2)
        assert opp_a.identity == opp_b.identity
        assert sib.w_minus(env_a.observe(), opp_a) == sib.w_minus(env_b.observe(), opp_b)
        assert env_a.focal_payload(2) != env_b.focal_payload(2)

    def test_registered_outcome_experiment_is_frozen_and_unlicensed(self):
        reg = gate_mod.REGISTERED_OUTCOME_EXPERIMENT
        assert reg["identity"] == "EOCIV-G32-SIBLING-4ARM-COMPLETE-BLOCK-D0"
        assert reg["licensed"] is False
        assert reg["valve"]["threshold_kappa"] == "1/4"
        assert reg["budget"] == {
            "parallel_envs": 16, "actor_seeds": 3,
            "d_fit_episodes_per_profile": 7282,
            "d_policy_episodes_per_profile": 2048,
            "d_cal_episodes_per_profile": 512,
            "d_focal_roots_per_profile": 256,
            "pattern_knockout_audit_roots_per_profile": 64,
            "d_focal_total_episodes": 9216,
        }
        assert reg["fit_support_schedule"] == {
            "REAL": "1/2", "NATIVE_NEUTRAL": "1/4",
            "PATTERN_ONLY": "1/8", "PAYLOAD_KNOCKOUT": "1/8",
        }

    def test_registered_arm_is_profile_qualified_and_covers_all_arms(self):
        per_profile = {
            profile.name: tuple(
                gate_mod.registered_arm(profile.name, episode, event)
                for episode in gate_mod.GATE_EPISODES
                for event in range(3)
            )
            for profile in gate_mod.GATE_PROFILES
        }
        for arms in per_profile.values():
            assert set(arms) == set(sib.ARMS)
        assert len(set(per_profile.values())) >= 2
