from __future__ import annotations

from collections import Counter
import hashlib
import json
import math

import pytest

from experiments.candidates.expressibility_gated_renewal_credit_relay import prerequisite_config as C
from experiments.candidates.expressibility_gated_renewal_credit_relay import prerequisite_experiment as E
from experiments.candidates.expressibility_gated_renewal_credit_relay import prerequisite_run as R


def test_frozen_constants_and_exact_counter_key() -> None:
    assert C.TREATMENT == "EGRCR-T3-DIRECTED-CYCLE-SUPPORT-ORACLE-HEADROOM-v1"
    assert C.STARTING_COMMIT == "650e8029a0ea2c28d7b73056378dd3556101057d"
    assert C.AGENTS == (0, 1, 2)
    assert C.BLOCK_TICKS == 10
    assert (C.WAITER_REQUEST_TICK, C.JOINER_SOURCE_TICK, C.JOINER_FALLBACK_TICK) == (2, 3, 4)
    assert (C.WAITER_EXPIRY_TICK, C.OUTCOME_BOUNDARY_TICK, C.TERMINAL_PADDING_TICK) == (6, 8, 9)
    assert C.SERVICE_TICKS == (4, 5, 6, 7, 8)
    assert C.SERVICE_PROBABILITY == 0.8
    assert C.DEPLOYMENT_COST == 0.01
    assert C.CALIBRATION_ROOTS == (223, 227, 229, 233, 239, 241)
    assert C.CONFIRMATION_ROOTS == (251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313)
    assert C.GAE_LAMBDAS == (0.0, 0.5, 0.95, 1.0)
    assert C.NAMESPACES == {
        "training_service": "training-service-v1",
        "evaluation_service": "evaluation-service-v1",
        "evaluation_token_choice": "evaluation-token-choice-v1",
        "calibration": "calibration-panel-v1",
    }
    key = E.counter_key(251, C.TRAINING_SERVICE_NAMESPACE, 4, 1, 15, 8, 1)
    assert key == (
        "EGRCR-T3-DIRECTED-CYCLE-SUPPORT-ORACLE-HEADROOM-v1|251|"
        "training-service-v1|4|1|15|8|1"
    )
    independent = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") / 2**64
    assert E.counter_uniform(251, C.TRAINING_SERVICE_NAMESPACE, 4, 1, 15, 8, 1) == independent
    assert 0.0 <= independent < 1.0


def test_compatibility_is_derived_from_ports_and_occupancy() -> None:
    favorable = E.route_capacity(2, 0, True, True)
    unfavorable = E.route_capacity(1, 0, True, True)
    fallback = E.route_capacity(2, 0, False, False)
    severed = E.route_capacity(2, 0, True, True, sever_waiter=True)

    assert favorable["waiter_output_port"] == favorable["joiner_input_port"] == 0
    assert favorable["route_connected"] is True
    assert favorable["capacity"] == 2
    assert unfavorable["waiter_output_port"] == 2
    assert unfavorable["joiner_input_port"] == 0
    assert unfavorable["route_connected"] is False
    assert unfavorable["capacity"] == 0
    assert fallback["atomic"] is False and fallback["capacity"] == 1
    assert severed["waiter_output_occupancy"] == []
    assert severed["capacity"] == 1
    assert "compatibility" not in favorable


def test_expected_quartets_balance_and_path_sever() -> None:
    support = E.compute_support()
    assert support["all_passed"] is True
    assert len(support["pair_world_table"]) == 6
    by_pair = {
        (row["waiter_id"], row["joiner_id"]): row
        for row in support["pair_world_table"]
    }
    for pair in C.FAVORABLE_PAIRS:
        row = by_pair[pair]
        assert row["Y00"] == pytest.approx(0.38)
        assert row["Y10"] == pytest.approx(0.38)
        assert row["Y01"] == pytest.approx(0.38)
        assert row["Y11"] == pytest.approx(0.78)
        assert row["Delta"] == pytest.approx(0.40)
        assert row["kappa"] == pytest.approx(0.40)
        assert row["true_waiter_first_stage"] is True
    for pair in C.UNFAVORABLE_PAIRS:
        row = by_pair[pair]
        assert row["Y11"] == pytest.approx(-0.02)
        assert row["Delta"] == pytest.approx(-0.40)
        assert row["kappa"] == pytest.approx(-0.40)
    assert all(row["C"] == pytest.approx(0.8) for row in support["joiner_contrasts"].values())
    assert all(row["K"] == pytest.approx(0.8) for row in support["joiner_contrasts"].values())
    assert max(abs(value) for value in support["marginal_sums"]["waiter"].values()) <= 1e-12
    assert max(abs(value) for value in support["marginal_sums"]["joiner"].values()) <= 1e-12
    for row in support["path_sever"]["pair_world_table"]:
        assert row["worlds"]["Y11"]["waiter_action_tick"] == C.JOINER_SOURCE_TICK
        assert row["worlds"]["Y11"]["waiter_transition_severed"] is True
    assert all(abs(row["C"]) <= 1e-12 for row in support["path_sever"]["joiner_contrasts"].values())
    assert all(abs(row["K"]) <= 1e-12 for row in support["path_sever"]["joiner_contrasts"].values())


def test_service_always_consumes_two_slot_tape_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []

    def uniform(*args: object) -> float:
        calls.append((int(args[-2]), int(args[-1])))
        return 0.0

    monkeypatch.setattr(E, "counter_uniform", uniform)
    rewards = E._sampled_rewards(251, C.TRAINING_SERVICE_NAMESPACE, 1, 0, 1, 0)
    assert sum(rewards) == pytest.approx(-0.02)  # incompatible atomic capacity is zero
    assert calls == [(tick, slot) for tick in C.SERVICE_TICKS for slot in (0, 1)]


def test_balanced_batch_retains_complete_three_agent_traces() -> None:
    records = E.build_training_batch(251, C.TRAINING_SERVICE_NAMESPACE)
    counts = Counter((row.waiter_id, row.joiner_id, row.action) for row in records)
    assert len(records) == 192
    assert set(counts.values()) == {16}
    assert set(counts) == {
        (waiter, joiner, action)
        for waiter, joiner in C.ORDERED_PAIRS
        for action in (0, 1)
    }
    assert all(row.stored_probability == 0.5 for row in records)
    assert all(row.generic_vector == E.generic_pre_action_vector() for row in records)
    for row in records:
        assert len(row.physical_trace) == 30
        assert Counter((trace["agent_id"], trace["tick"]) for trace in row.physical_trace) == {
            (agent, tick): 1 for agent in C.AGENTS for tick in range(C.BLOCK_TICKS)
        }
        eligible = [trace for trace in row.physical_trace if trace["source_eligible"]]
        assert len(eligible) == 1
        assert eligible[0]["agent_id"] == row.joiner_id
        assert eligible[0]["tick"] == C.JOINER_SOURCE_TICK
        assert eligible[0]["action"] == row.action


def test_pair_head_masks_diagonals_and_hidden_pair_status() -> None:
    features = {pair: E.actor_features(*pair) for pair in C.ORDERED_PAIRS}
    assert all(len(vector) == 7 and sum(vector) == 2.0 for vector in features.values())
    assert len(set(features.values())) == 6
    assert E.actor_features(2, 0, pair_masked=True) == (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="diagonal"):
        E.actor_features(1, 1)
    representation = E.representation_checks(E.freeze_trust_scale()["parameter_displacement"])
    assert representation["passed"] is True
    assert representation["pair_masked_remains_chance"] is True
    assert representation["pair_masked_probability"] == 0.5
    assert "compatibility" in representation["forbidden_information_absent"]


def test_oracle_replaces_only_source_and_preserves_geometry_and_work() -> None:
    records = E.build_training_batch(251, C.TRAINING_SERVICE_NAMESPACE)
    trust = E.freeze_trust_scale()
    gae_theta, gae = E._fit_arm(
        records,
        0.95,
        trust["parameter_displacement"],
        arm="GAE-DP",
        source_local=False,
    )
    oracle_theta, oracle = E._fit_arm(
        records,
        0.95,
        trust["parameter_displacement"],
        arm="PAIR-Q-ORACLE",
        source_local=False,
    )
    assert gae["work"]["oracle_source_replacements"] == 0
    assert oracle["work"]["oracle_source_replacements"] == 192
    assert oracle["replacement_not_addition"] is True
    assert gae["work"]["changed_non_source_records"] == 0
    assert oracle["work"]["changed_non_source_records"] == 0
    equal_work_keys = set(gae["work"]) - {"oracle_source_replacements"}
    assert all(gae["work"][key] == oracle["work"][key] for key in equal_work_keys)
    assert math.dist(gae_theta, [0.0] * len(gae_theta)) == pytest.approx(
        math.dist(oracle_theta, [0.0] * len(oracle_theta)), abs=1e-12
    )
    assert gae["mean_bernoulli_kl"] <= 0.02
    assert oracle["mean_bernoulli_kl"] <= 0.02


def test_noiseless_pair_aware_gae_is_mandatorily_competent() -> None:
    trust = E.freeze_trust_scale()
    competence = E.noiseless_competence(0.95, trust)
    assert competence["all_passed"] is True
    assert competence["gradient_sign_matches"] == [True] * 6
    assert competence["gradient_cosine"] >= 0.999
    assert competence["max_favorable_allocation_probability_difference"] <= 1e-6
    assert competence["max_bellman_residual"] <= 1e-12
    assert competence["checks"]["work_equal"] is True
    assert competence["checks"]["no_critic_learning"] is True


def test_source_local_control_reuses_total_service_but_severs_waiter_path() -> None:
    native = E.build_training_batch(251, C.TRAINING_SERVICE_NAMESPACE, source_local=False)
    local = E.build_training_batch(251, C.TRAINING_SERVICE_NAMESPACE, source_local=True)
    assert len(native) == len(local) == 192
    for native_row, local_row in zip(native, local):
        assert (native_row.waiter_id, native_row.joiner_id, native_row.action, native_row.repetition) == (
            local_row.waiter_id,
            local_row.joiner_id,
            local_row.action,
            local_row.repetition,
        )
        assert sum(native_row.rewards) == pytest.approx(sum(local_row.rewards))
        assert local_row.rewards[C.JOINER_SOURCE_TICK] == pytest.approx(sum(native_row.rewards))
        assert sum(abs(value) for tick, value in enumerate(local_row.rewards) if tick != C.JOINER_SOURCE_TICK) == 0.0
        local_waiter_at_source = [
            row
            for row in local_row.physical_trace
            if row["agent_id"] == local_row.waiter_id and row["tick"] == C.JOINER_SOURCE_TICK
        ][0]
        assert local_waiter_at_source["waiter_output_occupancy"] is None


@pytest.mark.parametrize(
    ("criteria", "expected"),
    [
        (
            {
                "native_headroom_passed": True,
                "source_path_relevance_passed": True,
                "probability_only_evaluator_movement": False,
            },
            "valid_source_path_headroom",
        ),
        (
            {
                "native_headroom_passed": False,
                "source_path_relevance_passed": False,
                "probability_only_evaluator_movement": False,
            },
            "gae_sufficiency",
        ),
        (
            {
                "native_headroom_passed": True,
                "source_path_relevance_passed": False,
                "probability_only_evaluator_movement": False,
            },
            "static_identity_or_denoising",
        ),
        (
            {
                "native_headroom_passed": False,
                "source_path_relevance_passed": False,
                "probability_only_evaluator_movement": True,
            },
            "evaluator_null",
        ),
    ],
)
def test_headroom_branch_classification(criteria: dict[str, bool], expected: str) -> None:
    assert E.classify_headroom_branch(criteria) == expected


def test_support_failure_is_terminal_bounded_null_and_skips_headroom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(E, "compute_support", lambda: {"all_passed": False, "witness": "frozen failure"})

    def forbidden() -> object:
        raise AssertionError("headroom setup must not run")

    monkeypatch.setattr(E, "freeze_trust_scale", forbidden)
    result = E.run_prerequisite()
    assert result["stage"] == "support_stopped_before_headroom"
    assert result["branch"] == "bounded_support_null"
    assert result["interpretation_valid"] is True
    assert result["scientific_null"] is True
    assert result["per_root"] == []
    assert result["complete_terminal_artifact"] is True


def test_comparator_failure_is_invalid_and_skips_sampled_headroom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(E, "compute_support", lambda: {"all_passed": True})
    monkeypatch.setattr(
        E,
        "freeze_trust_scale",
        lambda: {"parameter_displacement": 0.1, "mean_bernoulli_kl": 0.01, "kl_limit": 0.02},
    )
    monkeypatch.setattr(E, "representation_checks", lambda _: {"passed": True})
    monkeypatch.setattr(E, "select_lambda", lambda _: {"selected_lambda": 0.95})
    monkeypatch.setattr(E, "noiseless_competence", lambda *_: {"all_passed": False})

    result = E.run_prerequisite()
    assert result["stage"] == "comparator_invalid_stopped_before_sampled_headroom"
    assert result["branch"] == "representation_or_comparator_invalid"
    assert result["interpretation_valid"] is False
    assert result["scientific_null"] is False
    assert result["per_root"] == []
    assert result["complete_terminal_artifact"] is True


def test_full_terminal_artifact_has_registered_surface_and_caps() -> None:
    result = E.run_prerequisite()
    assert result["artifact_kind"] == C.ARTIFACT_KIND
    assert result["treatment"] == C.TREATMENT
    assert result["starting_commit"] == C.STARTING_COMMIT
    assert result["stage"] == "headroom_evaluation_complete"
    assert result["branch"] in {
        "valid_source_path_headroom",
        "gae_sufficiency",
        "static_identity_or_denoising",
        "evaluator_null",
    }
    assert result["support"]["all_passed"] is True
    assert result["representation"]["passed"] is True
    assert result["lambda_selection"]["selected_lambda"] in C.GAE_LAMBDAS
    assert result["frozen"]["trust_scale"]["mean_bernoulli_kl"] <= C.KL_MAX
    assert result["noiseless_competence"]["all_passed"] is True
    assert [root["root"] for root in result["per_root"]] == list(C.CONFIRMATION_ROOTS)
    assert result["intervals"]["native_oracle_minus_gae_allocation"]["n"] == 12
    assert result["intervals"]["native_oracle_minus_gae_normalized_utility"]["n"] == 12
    assert result["intervals"]["native_minus_local_oracle_gae_normalized_utility_gap"]["n"] == 12
    assert result["accounting"]["three_agent_physical_ticks"] <= C.MAX_THREE_AGENT_PHYSICAL_TICKS
    assert result["accounting"]["cpu_workers"] == 1
    assert result["accounting"]["restarts"] == result["accounting"]["sweeps"] == 0
    assert result["accounting"]["seed_replacement"] is False
    assert result["accounting"]["threshold_repair"] is False
    assert result["accounting"]["post_result_enlargement"] is False
    assert result["anomalies"] == []
    assert all(
        result["cap_status"][name]
        for name in ("wall_respected", "rss_respected", "physical_ticks_respected", "one_cpu_worker")
    )
    assert result["complete_terminal_artifact"] is True


def test_cli_contract_and_atomic_sorted_json(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    parser = R.build_parser()
    parsed = parser.parse_args(["--stage", "all", "--result-output", "x.json"])
    assert parsed.stage == "all"
    assert parsed.result_output == "x.json"
    with pytest.raises(SystemExit):
        parser.parse_args(["--stage", "confirmation", "--result-output", "x.json"])

    payload = {
        "artifact_kind": C.ARTIFACT_KIND,
        "artifact_identity": {"treatment": C.TREATMENT},
        "branch": "gae_sufficiency",
        "stage": "headroom_evaluation_complete",
        "complete_terminal_artifact": True,
    }
    monkeypatch.setattr(R, "run_prerequisite", lambda: payload)
    output = tmp_path / "result.json"
    assert R.main(["--stage", "all", "--result-output", str(output)]) == 0
    assert not (tmp_path / "result.json.tmp").exists()
    assert json.loads(output.read_text(encoding="utf-8")) == {
        **payload,
        "artifact_identity": {"treatment": C.TREATMENT, "result_path": str(output)},
    }
    text = output.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index('"artifact_identity"') < text.index('"artifact_kind"') < text.index('"branch"')


def test_cli_writes_explicit_technical_stop_and_nonzero_exit(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> object:
        raise RuntimeError("frozen technical failure")

    monkeypatch.setattr(R, "run_prerequisite", fail)
    output = tmp_path / "technical.json"
    assert R.main(["--stage", "all", "--result-output", str(output)]) == 4
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["stage"] == "technical_stop"
    assert result["branch"] == "representation_or_comparator_invalid"
    assert result["interpretation_valid"] is False
    assert result["scientific_null"] is False
    assert result["error"]["type"] == "RuntimeError"
    assert result["complete_terminal_artifact"] is True
