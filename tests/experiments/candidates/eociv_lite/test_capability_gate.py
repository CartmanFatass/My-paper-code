"""Focused tests for the EOCIV pre-PPO capability gate (measured pins)."""

from fractions import Fraction

from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import sibling_env as sib


class TestSegmentOracle:
    def test_measured_primary_cell_values(self):
        env, _ = gate_mod._forced_pair(gate_mod.GATE_PROFILES[0], 0, 0)
        opportunity = env.opportunity(0)
        oracle = gate_mod.segment_oracle(
            env.ledger, 0, opportunity.identity.receiver_member_key
        )
        assert oracle.switch_step == 0
        assert oracle.informed_value == Fraction(
            147657052349330479463426183791785520,
            15563800326580818681313331162464689,
        )
        assert oracle.blind_value == Fraction(5471379764104612, 812022094677233)
        assert oracle.reveal_value == Fraction(
            42788647021927284227014365728509324,
            15563800326580818681313331162464689,
        )
        # The switch is the boundary mechanism: overshoot under A -> effort 0,
        # undershoot under B -> effort 1, at every step of the held segment.
        assert set(oracle.optimal_actions[sib.SHOCK_A]) == {Fraction(0)}
        assert set(oracle.optimal_actions[sib.SHOCK_B]) == {Fraction(1)}

    def test_neutral_cell_reveal_is_exactly_zero(self):
        env = gate_mod._make_sibling(gate_mod.GATE_PROFILES[0], 0)
        gate_mod._drive_to(env, sib.EVENT_TIMES[1])
        opportunity = env.opportunity(1)
        oracle = gate_mod.segment_oracle(
            env.ledger, 1, opportunity.identity.receiver_member_key
        )
        assert oracle.reveal_value == 0
        assert not oracle.candidate_switch_exists


class TestGate:
    def test_full_gate_terminal_and_counts(self):
        report = gate_mod.gate()
        assert report["terminal"] == "EOCIV_SIBLING_CAPABILITY_PRESENT"
        checks = report["checks"]
        assert all(bool(result["passed"]) for result in checks.values())
        assert len(checks) == 10
        assert checks["1_disabled_projection_reproduces_base"]["episodes_compared"] == 24
        assert checks["2_owner_and_spell_receipts_complete"]["opportunities"] == 72
        assert checks["2_owner_and_spell_receipts_complete"]["eligible"] == 72
        five = checks["5_identical_w_minus_different_optimal_actions"]
        assert five["critical_cells"] == 48
        assert five["cells_with_action_switch"] == 48
        six = checks["6_real_payload_strictly_better_in_critical_cells"]
        assert six["critical_cells"] == 48
        assert six["max_execution_conformance_error"] <= gate_mod.CONFORMANCE_TOL
        assert checks["7_neutral_cells_zero_reveal_value"]["neutral_cells"] == 24
        support = checks["10_four_arms_positive_support_per_stratum"]["support"]
        assert support == {
            "CRITICAL/CR": 12,
            "CRITICAL/CS": 12,
            "CRITICAL/LR": 12,
            "CRITICAL/LS": 12,
            "NEUTRAL/CR": 6,
            "NEUTRAL/CS": 6,
            "NEUTRAL/LR": 6,
            "NEUTRAL/LS": 6,
        }

    def test_reveal_values_dominate_wiring_noise(self):
        report = gate_mod.gate()
        rows = report["checks"]["6_real_payload_strictly_better_in_critical_cells"]["rows"]
        values = [Fraction(row["reveal_value"]) for row in rows]
        assert min(values) >= gate_mod.REVEAL_FLOOR
        # Measured extremes of the exact reveal distribution.
        assert float(min(values)) == 1.098753756605706
        assert float(max(values)) == 2.9871686834596036

    def test_w_minus_identical_across_hidden_pair(self):
        env_a, env_b = gate_mod._forced_pair(gate_mod.GATE_PROFILES[1], 3, 2)
        opp_a = env_a.opportunity(2)
        opp_b = env_b.opportunity(2)
        assert opp_a.identity == opp_b.identity
        assert sib.w_minus(env_a.observe(), opp_a) == sib.w_minus(env_b.observe(), opp_b)
        # ...while the focal payload bodies differ (the mutation is real).
        assert env_a.focal_payload(2) != env_b.focal_payload(2)

    def test_registered_learned_decision_reads_w_minus_only(self):
        import inspect

        parameters = inspect.signature(gate_mod.registered_learned_decision).parameters
        assert set(parameters) == {"w_minus_bytes"}

    def test_registered_arm_assignment_covers_all_arms(self):
        arms = {
            gate_mod.registered_arm(episode_id, event_index)
            for episode_id in gate_mod.GATE_EPISODES
            for event_index in range(3)
        }
        assert arms == set(sib.ARMS)
