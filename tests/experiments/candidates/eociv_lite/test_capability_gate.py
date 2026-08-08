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


class TestGate:
    def test_full_gate_terminal_and_counts(self):
        report = gate_mod.gate()
        assert report["terminal"] == "EOCIV_SIBLING_CAPABILITY_PRESENT"
        checks = report["checks"]
        assert all(bool(result["passed"]) for result in checks.values())
        assert len(checks) == 11
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
            "wrong_owner": True,
            "identity_mismatch": True,
            "route_mismatch": True,
            "decision_source_mismatch": True,
            "ingestion_cost_mismatch": True,
            "slot_mismatch": True,
            "policy_tensor_mismatch": True,
            "nonfocal_nonzero": True,
            "cross_runner": True,
            "duplicate": True,
            "stale_post_action": True,
            "action_altered_after_forward": True,
        }
        five = checks["5_identical_w_minus_disjoint_full_support_optima"]
        assert five["critical_cells"] == five["cells_with_disjoint_optimal_sets"] == 48
        six = checks["6_full_support_strict_value_with_envelopes"]
        assert six["critical_cells"] == 48
        assert six["min_reveal_value"] == (
            "33029367329065267099970516619425633618760375227/"
            "24289297430485184514310814667806889932013611700"
        )
        # The envelopes are wiring quantities: deterministic on one box but
        # sensitive to numpy/BLAS reduction order across platforms, so the
        # test pins the bounds the science needs, not the 16th digit.  The
        # accumulated envelopes are on the SEGMENT-TOTAL scale (Pro's C2):
        # they include the informed AND blind trajectories over all 12 steps,
        # so their conservative ceiling is 24x the per-step maxima.
        assert 0 < six["max_step_action_quantization_gap"] < 1e-7
        assert 0 < six["max_step_kernel_conformance_error"] <= gate_mod.CONFORMANCE_TOL
        assert 0 < six["max_accumulated_quant_envelope"] < 24 * 1e-7
        assert 0 < six["max_accumulated_kernel_envelope"] < 24 * gate_mod.CONFORMANCE_TOL
        assert six["quantized_never_exceeds_exact"] is True
        assert six["min_dominance_ratio"] >= gate_mod.DOMINANCE_FACTOR
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
        eleven = checks["11_profile_qualified_outcome_world_noise_manifest"]
        assert eleven["cross_profile_world_noise_distinct"] is True
        # The stream-level certificates (not the whole-ledger digests, which
        # differ across profiles for structural membership reasons anyway):
        # qualification separates the shared base streams, and the
        # unqualified registered seed reproduces the shared-stream defect.
        assert eleven["world_streams_profile_qualified"] is True
        assert eleven["unqualified_seed_defect_reproduced"] is True
        assert eleven["four_arm_clones_identical"] is True
        assert eleven["clone_comparison_discriminates"] is True
        assert eleven["namespace_sizes_match_budgets"] is True
        assert eleven["namespaces_disjoint"] is True
        assert eleven["profile_hash_collision_free_registry_size"] == 7
        assert eleven["derived_seeds_distinct"] is True
        assert len(set(eleven["world_seeds"].values())) == 3
        assert len(set(eleven["noise_seeds"].values())) == 3

    def test_reveal_extremes_and_dominance(self):
        report = gate_mod.gate()
        six = report["checks"]["6_full_support_strict_value_with_envelopes"]
        values = sorted(Fraction(row["reveal_value"]) for row in six["rows"])
        assert float(values[0]) == 1.3598321410322283
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
        identity = reg["world_noise_identity"]
        assert identity["ledger_master_seed_label"] == "EOCIV-LEDGER-WORLD-V1"
        assert identity["action_noise_seed_label"] == "EOCIV-ACTION-NOISE-V1"
        assert identity["registered_master_seed"] == gate_mod.MASTER_SEED
        assert identity["registered_action_seed"] == 730202
        assert identity["applies_to_pools"] == [
            "d_fit", "d_policy", "d_cal", "d_focal", "pattern_knockout_audit",
        ]
        namespaces = reg["episode_namespaces"]
        assert namespaces["d_fit"] == [0, 7281]
        assert namespaces["d_policy"] == [100000, 102047]
        assert namespaces["d_cal"] == [200000, 200511]
        assert namespaces["d_focal"] == [300000, 300255]
        assert namespaces["pattern_knockout_audit"] == [400000, 400063]

    def test_profile_qualified_seed_derivation_is_stable_and_distinct(self):
        seed = gate_mod.profile_qualified_seed(
            "EOCIV-LEDGER-WORLD-V1", gate_mod.MASTER_SEED, "train_4_3_6_5"
        )
        assert seed == gate_mod.outcome_world_seed("train_4_3_6_5")
        assert 0 <= seed < 2 ** 64
        world = {p.name: gate_mod.outcome_world_seed(p.name) for p in gate_mod.GATE_PROFILES}
        noise = {p.name: gate_mod.outcome_noise_seed(p.name) for p in gate_mod.GATE_PROFILES}
        assert len(set(world.values()) | set(noise.values())) == 6

    def test_oracle_retains_blind_optimizer_trajectory(self):
        env, _ = gate_mod._forced_pair(gate_mod.GATE_PROFILES[0], 0, 0)
        opportunity = env.opportunity(0)
        oracle = gate_mod.full_support_oracle(
            env.ledger, 0, opportunity.identity.receiver_member_key
        )
        assert len(oracle.per_step_blind_optima) == 12
        # Each stored blind point attains the step's blind maximum: summing
        # the exact per-step mixture values reproduces the blind total.
        keys = gate_mod._active_keys_in_segment(env.ledger, 0)
        receiver = opportunity.identity.receiver_member_key
        caps = (
            gate_mod._frac(env.ledger.capabilities[receiver, 0]),
            gate_mod._frac(env.ledger.capabilities[receiver, 1]),
        )
        aggregate = (
            sum((gate_mod._frac(env.ledger.capabilities[k, 0]) for k in keys), Fraction(0)),
            sum((gate_mod._frac(env.ledger.capabilities[k, 1]) for k in keys), Fraction(0)),
        )
        total = Fraction(0)
        for step, point in enumerate(oracle.per_step_blind_optima):
            time = sib.EVENT_TIMES[0] + step
            geometry = gate_mod.StepGeometry(
                load=gate_mod._frac(env.ledger.load[time]),
                mix=gate_mod._frac(env.ledger.target_mix[time]),
                receiver_caps=caps, aggregate=aggregate,
            )
            total += sum(
                (sib.CRITICAL_PRIOR[state] * geometry.reward(state, *point)
                 for state in sib.CRITICAL_PRIOR),
                Fraction(0),
            )
        assert total == oracle.blind_value

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
