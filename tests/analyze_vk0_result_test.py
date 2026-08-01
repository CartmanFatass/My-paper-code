"""Calibration tests for the V-K0B result analyzer (scripts/analyze_vk0_result.py).

The V-K0B driver that emits real renewal_check_trace.jsonl /
renewal_counterfactual_units.jsonl rows does not exist yet (ledger status,
docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md). Every fixture here
is synthetic, hand-built against the frozen row schema (A-VK-D6) and the
frozen branch predicates (A-VK-D9, round 20260801_vk0_design_conformance).

Each test earns its place by being able to fail: the unit-level tests check
the estimand arithmetic against an independently hand-computed expected
value; the scenario tests drive real support-floor-scale data through the
real 10,000-iteration bootstrap and check the resulting first-match result
row; the precedence test plants a fixture that would independently trigger
two different rows and asserts only the higher-precedence one fires; the
mutation test perturbs a temporary copy of the analyzer's decisive-fail
predicate and shows the same fixture then yields a different result.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_SCRIPT_PATH = _ROOT / "scripts" / "analyze_vk0_result.py"
_SPEC = importlib.util.spec_from_file_location("analyze_vk0_result", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)


# =============================================================================
# Shared fixture-construction helpers (test-only; not part of the analyzer)
# =============================================================================

CONTRACT_ID = M.VK0_CONTRACT_ID
SCHEMA_VERSION = M.VK0_TRACE_SCHEMA_VERSION
DEFAULT_CHECKPOINT_HASH = "ckpt-a"
DEFAULT_CONFIG_HASH = "cfg-a"


def _identity(training_seed, episode_id, agent_order, check_index, focal_agent, check_unit_id,
              checkpoint_hash=DEFAULT_CHECKPOINT_HASH, resolved_config_hash=DEFAULT_CONFIG_HASH,
              evaluation_seed=1):
    return {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": SCHEMA_VERSION,
        "training_seed": training_seed,
        "evaluation_seed": evaluation_seed,
        "episode_id": episode_id,
        "agent_order_code": agent_order,
        "check_index": check_index,
        "focal_agent": focal_agent,
        "check_unit_id": check_unit_id,
        "checkpoint_hash": checkpoint_hash,
        "resolved_config_hash": resolved_config_hash,
    }


def make_check_row(*, training_seed, episode_id, agent_order, check_index, focal_agent,
                    check_unit_id, u_src, natural_token_kind, keep_prob,
                    slow_match=1, fast_match=1, checkpoint_hash=DEFAULT_CHECKPOINT_HASH,
                    resolved_config_hash=DEFAULT_CONFIG_HASH, oracle_urgency_class=None):
    row = _identity(training_seed, episode_id, agent_order, check_index, focal_agent,
                     check_unit_id, checkpoint_hash, resolved_config_hash)
    if oracle_urgency_class is None:
        oracle_urgency_class = "URGENT" if u_src > 0.5 else ("STABLE" if u_src < 0.5 else "BOUNDARY")
    row.update(
        {
            "oracle_u_src": u_src,
            "oracle_urgency_class": oracle_urgency_class,
            "natural_token_kind": natural_token_kind,
            "natural_set_skill": "z1" if natural_token_kind == "SET" else None,
            "keep_prob": keep_prob,
            "segment_ending_authority": "voluntary_set" if natural_token_kind == "SET" else "team_intent_boundary",
            "natural_external_reward_vector": [0.5, 0.5, 0.5, 0.5, 0.5],
            "slow_match_vector": [slow_match] * 5,
            "fast_match_vector": [fast_match] * 5,
        }
    )
    return row


def make_unit_row(*, training_seed, episode_id, agent_order, check_index, focal_agent,
                   check_unit_id, branch_unit_id, estimand_family, parent_check_unit_id,
                   candidate_skill, phase, replicate_index, window_return,
                   checkpoint_hash=DEFAULT_CHECKPOINT_HASH, resolved_config_hash=DEFAULT_CONFIG_HASH,
                   replay_conformance=None):
    row = _identity(training_seed, episode_id, agent_order, check_index, focal_agent,
                     check_unit_id, checkpoint_hash, resolved_config_hash)
    row.update(
        {
            "branch_unit_id": branch_unit_id,
            "estimand_family": estimand_family,
            "parent_check_unit_id": parent_check_unit_id,
            "candidate_skill": candidate_skill,
            "phase": phase,
            "replicate_index": replicate_index,
            "derived_seed": abs(hash(branch_unit_id)) % (2**31),
            "external_reward_vector": [window_return / 5.0] * 5,
            "window_return": window_return,
            "replay_conformance": replay_conformance or {"boundary_fingerprint": True},
        }
    )
    return row


def build_check_and_units(*, training_seed, episode_id, agent_order, check_index, focal_agent,
                           u_src, opp_effect, set_effect, nat_effect, natural_token_kind, keep_prob,
                           slow_match=1, fast_match=1):
    """One check-agent row plus its minimal joined unit rows: KEEP_REFERENCE
    (select+evaluate), one OPP_NAMED_SET candidate ("z1", select+evaluate),
    SET_SAMPLED (evaluate) and NATURAL (evaluate)."""
    check_unit_id = f"chk-{training_seed}-{episode_id}-{agent_order}-{check_index}-{focal_agent}"
    crow = make_check_row(
        training_seed=training_seed, episode_id=episode_id, agent_order=agent_order,
        check_index=check_index, focal_agent=focal_agent, check_unit_id=check_unit_id,
        u_src=u_src, natural_token_kind=natural_token_kind, keep_prob=keep_prob,
        slow_match=slow_match, fast_match=fast_match,
    )
    units = []

    def u(suffix, estimand_family, candidate_skill, phase, replicate_index, window_return):
        units.append(
            make_unit_row(
                training_seed=training_seed, episode_id=episode_id, agent_order=agent_order,
                check_index=check_index, focal_agent=focal_agent, check_unit_id=check_unit_id,
                branch_unit_id=f"{check_unit_id}-{suffix}", estimand_family=estimand_family,
                parent_check_unit_id=check_unit_id, candidate_skill=candidate_skill, phase=phase,
                replicate_index=replicate_index, window_return=window_return,
            )
        )

    for rep in (0, 1):
        u(f"keep-sel-{rep}", "KEEP_REFERENCE", None, "select", rep, 0.0)
        u(f"keep-eval-{rep}", "KEEP_REFERENCE", None, "evaluate", rep, 0.0)
        u(f"z1-sel-{rep}", "OPP_NAMED_SET", "z1", "select", rep, opp_effect)
        u(f"z1-eval-{rep}", "OPP_NAMED_SET", "z1", "evaluate", rep, opp_effect)
        u(f"setsamp-eval-{rep}", "SET_SAMPLED", "z1", "evaluate", rep, set_effect)
        u(f"nat-eval-{rep}", "NATURAL", None, "evaluate", rep, nat_effect)
    return crow, units


def build_dataset(
    training_seed,
    *,
    urgent_opp_fn=lambda local_ep, n_ep: 5.0,
    stable_opp_fn=lambda local_ep, n_ep: 0.0,
    urgent_set=5.0,
    stable_set=0.0,
    urgent_nat_fn=lambda local_ep, n_ep: 5.0,
    stable_nat_fn=lambda local_ep, n_ep: 0.0,
    urgent_keep_prob=0.1,
    stable_keep_prob=0.9,
    urgent_natural_token="SET",
    stable_natural_token="KEEP",
    urgent_natural_token_fn=None,
    stable_natural_token_fn=None,
    urgent_slow_match=1,
    urgent_fast_match=1,
    stable_slow_match=1,
    stable_fast_match=1,
    rows_per_class_order=96,
):
    """A full support-floor-scale (>=192 URGENT + >=192 STABLE, >=64 of each
    class under each agent order) one-seed dataset, per MEASUREMENT
    'Support floor'. Effects can be varied per local episode index via the
    *_fn callables to inject genuine bootstrap-relevant variance."""
    check_rows = []
    unit_rows = []
    n_episodes = rows_per_class_order // 8
    urgent_token_fn = urgent_natural_token_fn or (lambda local_ep, n_ep: urgent_natural_token)
    stable_token_fn = stable_natural_token_fn or (lambda local_ep, n_ep: stable_natural_token)
    blocks = [
        ("URGENT", "canonical", urgent_opp_fn, urgent_nat_fn, urgent_keep_prob, urgent_token_fn,
         urgent_slow_match, urgent_fast_match),
        ("URGENT", "reversed", urgent_opp_fn, urgent_nat_fn, urgent_keep_prob, urgent_token_fn,
         urgent_slow_match, urgent_fast_match),
        ("STABLE", "canonical", stable_opp_fn, stable_nat_fn, stable_keep_prob, stable_token_fn,
         stable_slow_match, stable_fast_match),
        ("STABLE", "reversed", stable_opp_fn, stable_nat_fn, stable_keep_prob, stable_token_fn,
         stable_slow_match, stable_fast_match),
    ]
    for cls, order, opp_fn, nat_fn, keep_prob, token_fn, slow_match, fast_match in blocks:
        u_src = 0.8 if cls == "URGENT" else 0.2
        set_effect = urgent_set if cls == "URGENT" else stable_set
        for k in range(rows_per_class_order):
            local_ep = k // 8
            episode_id = f"ep-{cls}-{order}-{local_ep}"
            opp_effect = opp_fn(local_ep, n_episodes)
            nat_effect = nat_fn(local_ep, n_episodes)
            natural_token = token_fn(local_ep, n_episodes)
            crow, units = build_check_and_units(
                training_seed=training_seed, episode_id=episode_id, agent_order=order,
                check_index=(k % 7) + 1, focal_agent=k % 2, u_src=u_src, opp_effect=opp_effect,
                set_effect=set_effect, nat_effect=nat_effect, natural_token_kind=natural_token,
                keep_prob=keep_prob, slow_match=slow_match, fast_match=fast_match,
            )
            check_rows.append(crow)
            unit_rows.extend(units)
    return check_rows, unit_rows


def manifest_for(seeds, checkpoint_hash=DEFAULT_CHECKPOINT_HASH,
                  resolved_config_hash=DEFAULT_CONFIG_HASH, low_optimizer_steps=0):
    return {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": SCHEMA_VERSION,
        "seeds": {
            str(seed): {
                "checkpoint_hash": checkpoint_hash,
                "resolved_config_hash": resolved_config_hash,
                "low_optimizer_steps": low_optimizer_steps,
            }
            for seed in seeds
        },
    }


def oracle_panel_for(verdict=M.VK0A_VERDICT_IDENTIFIED, row_count=M.VK0A_PANEL_ROW_COUNT,
                      tamper=False):
    payload = {
        "contract_id": CONTRACT_ID,
        "stage_commit": "c4b64841798d65af8474ded00bf623a109c7c792",
        "environment_blob_sha": "envsha",
        "action_table_hash": "actiontablehash",
        "oracle_script_hash": "oraclehash",
        "panel_schema_version": "panel-v1",
        "row_count": row_count,
        "validity_predicates": {"all_exhausted": True},
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["artifact_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if tamper:
        payload["artifact_sha256"] = "0" * 64
    return payload


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def write_dataset(tmp_path: Path, check_rows, unit_rows, manifest, panel, prefix="") -> dict[str, Path]:
    trace_path = tmp_path / f"{prefix}trace.jsonl"
    units_path = tmp_path / f"{prefix}units.jsonl"
    manifest_path = tmp_path / f"{prefix}manifest.json"
    panel_path = tmp_path / f"{prefix}panel.json"
    write_jsonl(trace_path, check_rows)
    write_jsonl(units_path, unit_rows)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    panel_path.write_text(json.dumps(panel), encoding="utf-8")
    return {"trace": trace_path, "units": units_path, "manifest": manifest_path, "panel": panel_path}


SEED = 2026080101


# =============================================================================
# Unit-level tests: the estimand arithmetic against a hand-computed value
# =============================================================================


def test_classify_urgency_boundary_is_exact():
    assert M.classify_urgency(0.5) == "BOUNDARY"
    assert M.classify_urgency(0.5000001) == "URGENT"
    assert M.classify_urgency(0.4999999) == "STABLE"


def test_compute_u_opp_selects_argmax_on_select_then_evaluates_disjoint_draws():
    # Three candidates. z2's select-phase mean (10.0) is the largest, so z2
    # must be chosen even though its evaluate-phase mean is worse than z3's
    # (which is never selected because it never won the select-phase race).
    # KEEP is 1.0 at both phases.
    units = [
        {"estimand_family": "KEEP_REFERENCE", "phase": "select", "window_return": 1.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "select", "window_return": 1.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 1.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 1.0, "candidate_skill": None},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 3.0, "candidate_skill": "z1"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 3.0, "candidate_skill": "z1"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 10.0, "candidate_skill": "z2"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 10.0, "candidate_skill": "z2"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 4.0, "candidate_skill": "z3"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 4.0, "candidate_skill": "z3"},
        # Evaluate-phase rows only for the winner z2 -- exactly what a real
        # driver would emit (n_eval=2 for the selected candidate only).
        {"estimand_family": "OPP_NAMED_SET", "phase": "evaluate", "window_return": 5.0, "candidate_skill": "z2"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "evaluate", "window_return": 5.0, "candidate_skill": "z2"},
        # A decoy evaluate row for z3, which must be ignored since z3 never
        # won the select-phase argmax.
        {"estimand_family": "OPP_NAMED_SET", "phase": "evaluate", "window_return": 100.0, "candidate_skill": "z3"},
    ]
    # Hand-computed: winner is z2 (select mean 10.0 > 3.0, 4.0). Effect =
    # mean(evaluate z2) - mean(evaluate KEEP) = 5.0 - 1.0 = 4.0.
    assert M.compute_u_opp(units) == pytest.approx(4.0)


def test_compute_u_opp_clips_negative_effect_to_zero():
    units = [
        {"estimand_family": "KEEP_REFERENCE", "phase": "select", "window_return": 5.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 5.0, "candidate_skill": None},
        {"estimand_family": "OPP_NAMED_SET", "phase": "select", "window_return": 1.0, "candidate_skill": "z1"},
        {"estimand_family": "OPP_NAMED_SET", "phase": "evaluate", "window_return": 1.0, "candidate_skill": "z1"},
    ]
    # Effect = 1.0 - 5.0 = -4.0 -> max(0, -4.0) = 0.0, per MEASUREMENT §4A.
    assert M.compute_u_opp(units) == pytest.approx(0.0)


def test_compute_u_opp_returns_none_without_a_legal_candidate():
    units = [
        {"estimand_family": "KEEP_REFERENCE", "phase": "select", "window_return": 0.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 0.0, "candidate_skill": None},
    ]
    assert M.compute_u_opp(units) is None


def test_compute_u_set_and_u_nat_are_paired_evaluate_differences():
    units = [
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 2.0, "candidate_skill": None},
        {"estimand_family": "KEEP_REFERENCE", "phase": "evaluate", "window_return": 4.0, "candidate_skill": None},
        {"estimand_family": "SET_SAMPLED", "phase": "evaluate", "window_return": 9.0, "candidate_skill": "z3"},
        {"estimand_family": "SET_SAMPLED", "phase": "evaluate", "window_return": 9.0, "candidate_skill": "z3"},
        {"estimand_family": "NATURAL", "phase": "evaluate", "window_return": 1.0, "candidate_skill": None},
        {"estimand_family": "NATURAL", "phase": "evaluate", "window_return": 1.0, "candidate_skill": None},
    ]
    # mean(KEEP eval) = 3.0. mean(SET_SAMPLED) = 9.0 -> U_SET = 6.0.
    # mean(NATURAL) = 1.0 -> U_nat = 1.0 - 3.0 = -2.0.
    assert M.compute_u_set(units) == pytest.approx(6.0)
    assert M.compute_u_nat(units) == pytest.approx(-2.0)


# =============================================================================
# Schema validation: refuse, never guess
# =============================================================================


def test_analyzer_refuses_on_missing_required_field(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    del check_rows[0]["oracle_u_src"]
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_analyzer_refuses_on_bad_enum_field(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    check_rows[0]["agent_order_code"] = "north"
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_analyzer_refuses_on_window_return_inconsistent_with_reward_vector(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    unit_rows[0]["window_return"] = unit_rows[0]["window_return"] + 1000.0
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_urgency_classification_is_recomputed_not_trusted_from_the_stored_label(tmp_path):
    # A row whose stored oracle_urgency_class is a stale/wrong "STABLE" label
    # but whose oracle_u_src (0.9) is unambiguously URGENT under the frozen
    # 0.5 threshold. If the analyzer trusted the label it would misclassify
    # this row; support_floor counts must reflect the recomputed class.
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    check_rows[0]["oracle_u_src"] = 0.9
    check_rows[0]["oracle_urgency_class"] = "STABLE"
    urgent_before = sum(1 for r in check_rows if M.classify_urgency(float(r["oracle_u_src"])) == "URGENT")
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    seed_counts = result["support_floor"]["per_seed"][str(SEED)]
    assert seed_counts["urgent_total"] == urgent_before


# =============================================================================
# Result rows 1-8: full first-match scenarios
# =============================================================================


def test_row1_invalid_on_replay_conformance_false(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    unit_rows[3]["replay_conformance"] = {"boundary_fingerprint": False}
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert result["result"]["code"] == "INVALID_VARIABLE_K_URGENCY_AUDIT"


def test_row1_invalid_on_manifest_checkpoint_mismatch(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        manifest_for([SEED], checkpoint_hash="a-different-checkpoint"), oracle_panel_for(),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row1_invalid_on_prohibited_optimizer_exposure(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        manifest_for([SEED], low_optimizer_steps=3), oracle_panel_for(),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row1_invalid_on_oracle_panel_tamper(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for(tamper=True),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row2_source_not_identified(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows, manifest_for([SEED]),
        oracle_panel_for(verdict=M.VK0A_VERDICT_NOT_IDENTIFIED),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 2
    assert result["result"]["code"] == "TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED"


def test_row3_support_floor_insufficient(tmp_path):
    # Far below the 192-per-class / 64-per-class-per-order floor.
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 3
    assert result["result"]["code"] == "R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT"
    assert result["support_floor"]["per_seed"][str(SEED)]["pass"] is False


def test_row4_competence_not_established(tmp_path):
    check_rows, unit_rows = build_dataset(
        SEED, urgent_slow_match=0, urgent_fast_match=0, stable_slow_match=0, stable_fast_match=0,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["support_floor"]["pass"] is True
    assert result["result"]["row"] == 4
    assert result["result"]["code"] == "R30_TOY_ACCESS_NOT_ESTABLISHED"


def test_row5_opportunity_decisively_not_accessed(tmp_path):
    # Urgent opportunity effect uniformly zero -> UCB(U_opp|URGENT) <= 0.5
    # decisively, in every required stratum.
    check_rows, unit_rows = build_dataset(
        SEED, urgent_opp_fn=lambda ep, n: 0.0, stable_opp_fn=lambda ep, n: 0.0,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["competence_floor"]["pass"] is True
    assert result["result"]["row"] == 5
    assert result["result"]["code"] == "SOURCE_IDENTIFIED_R30_OPPORTUNITY_NOT_ACCESSED"
    assert result["opportunity"]["pooled"]["decisive_fail"] is True


def test_row6_natural_alignment_wrong_direction(tmp_path):
    # Opportunity passes cleanly; natural STABLE effect is a large negative
    # constant, driving UCB(U_nat|STABLE) <= -0.5 decisively.
    check_rows, unit_rows = build_dataset(
        SEED, stable_nat_fn=lambda ep, n: -10.0,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["opportunity"]["all_pass"] is True
    assert result["result"]["row"] == 6
    assert result["result"]["code"] == "SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_WRONG_DIRECTION"
    assert result["natural"]["decisive_wrong"] is True


def test_row7_opportunity_unresolved_straddling_boundary(tmp_path):
    # Half the URGENT episodes get opp effect 1.5, half get -0.5: the
    # bootstrap LCB lands exactly at the 0.5 materiality boundary (fails the
    # strict > 0.5 pass gate) while the UCB (1.0) is nowhere near the <= 0.5
    # decisive-failure gate -- a genuine straddle, not a decisive result.
    def urgent_opp_fn(local_ep, n_episodes):
        return 1.5 if local_ep < n_episodes // 2 else -0.5

    check_rows, unit_rows = build_dataset(SEED, urgent_opp_fn=urgent_opp_fn)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    pooled = result["opportunity"]["pooled"]
    assert pooled["pass"] is False
    assert pooled["decisive_fail"] is False
    assert result["result"]["row"] == 7
    assert result["result"]["code"] == "SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_UNRESOLVED"


def test_row7_natural_unresolved_nonpositive_set_rate_point_estimate(tmp_path):
    # Opportunity passes. Natural URGENT/STABLE and hazard all pass cleanly
    # (constant effects, as in the row-8 fixture). The realized natural
    # SET-rate is varied per episode -- 30% of URGENT episodes naturally
    # SET, 40% of STABLE episodes naturally SET -- giving a nonpositive
    # point contrast (-0.083) whose bootstrap CI still straddles zero
    # (upper_95 ~= 0.15, nowhere near the <=0 decisive-failure gate). Per
    # A-VK-D9, "a nonpositive point estimate alone -> row 7".
    def urgent_token_fn(local_ep, n_episodes):
        return "SET" if local_ep < round(n_episodes * 0.3) else "KEEP"

    def stable_token_fn(local_ep, n_episodes):
        return "SET" if local_ep < round(n_episodes * 0.4) else "KEEP"

    check_rows, unit_rows = build_dataset(
        SEED, urgent_natural_token_fn=urgent_token_fn, stable_natural_token_fn=stable_token_fn,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["opportunity"]["all_pass"] is True
    natural = result["natural"]
    assert natural["decisive_wrong"] is False
    assert natural["set_rate_diff"]["point"] <= 0.0
    assert natural["set_rate_diff"]["upper_95"] > 0.0
    assert result["result"]["row"] == 7
    assert result["result"]["code"] == "SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_UNRESOLVED"


def test_row8_heterogeneous_urgency_and_natural_access_identified(tmp_path):
    check_rows, unit_rows = build_dataset(SEED)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 8
    assert result["result"]["code"] == "HETEROGENEOUS_URGENCY_AND_R30_NATURAL_ACCESS_IDENTIFIED"


# =============================================================================
# First-match precedence ordering
# =============================================================================


def test_first_match_precedence_row3_beats_row5():
    """A fixture that is simultaneously support-insufficient (row 3, only 8
    rows per class/order -- far under the 192/64 floor) AND would, were the
    floor ignored, show zero opportunity access (the row-5 condition) must
    resolve to row 3: precedence 1..8 is a *first*-match selector, and the
    opportunity stage must never even be evaluated once row 3 fires."""
    check_rows, unit_rows = build_dataset(
        SEED, rows_per_class_order=8, urgent_opp_fn=lambda ep, n: 0.0, stable_opp_fn=lambda ep, n: 0.0,
    )
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
        result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["support_floor"]["pass"] is False
    assert result["result"]["row"] == 3
    assert "opportunity" not in result


# =============================================================================
# Determinism
# =============================================================================


def test_determinism_two_runs_are_byte_identical(tmp_path):
    check_rows, unit_rows = build_dataset(SEED)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    out_a = tmp_path / "summary_a.json"
    out_b = tmp_path / "summary_b.json"
    result_a = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    result_b = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    M._write_json(out_a, result_a)
    M._write_json(out_b, result_b)
    assert out_a.read_bytes() == out_b.read_bytes()


# =============================================================================
# Bootstrap sanity
# =============================================================================


def test_bootstrap_huge_effect_bounds_exclude_materiality_boundary(tmp_path):
    check_rows, unit_rows = build_dataset(SEED)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    pooled = result["opportunity"]["pooled"]
    assert pooled["urgent"]["lower_95"] > 0.5
    assert pooled["stable"]["upper_95"] < 0.5


def test_bootstrap_straddling_effect_yields_unresolved_not_decisive(tmp_path):
    def urgent_opp_fn(local_ep, n_episodes):
        return 1.5 if local_ep < n_episodes // 2 else -0.5

    check_rows, unit_rows = build_dataset(SEED, urgent_opp_fn=urgent_opp_fn)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    pooled = result["opportunity"]["pooled"]
    assert not (pooled["urgent"]["lower_95"] > 0.5)
    assert not (pooled["urgent"]["upper_95"] <= 0.5)


# =============================================================================
# Paired negative: a flipped decisive-fail inequality must change the result
# =============================================================================


def test_paired_negative_flipping_decisive_fail_inequality_changes_the_result(tmp_path):
    """Mutate a TEMPORARY copy of the analyzer, replacing the natural
    decisive-wrong inequality `nat_stable["upper_95"] <= -MATERIALITY` with a
    strict `<`, and show that on a row-6 fixture -- constructed so the
    STABLE natural effect sits exactly on the -0.5 boundary
    (upper_95 == -0.5, which is decisive under the frozen `<=` but not under
    a mutated strict `<`), with every other decisive-wrong and pass clause
    clearly not at issue -- the mutant diverges from row 6. U_nat carries no
    max(0, .) clip (unlike U_opp), so this boundary can be isolated to
    exactly one clause; this proves the precedence assertions in this suite
    are real discriminators, not tautologies. The production module (never
    modified) still yields row 6."""
    check_rows, unit_rows = build_dataset(
        SEED, stable_nat_fn=lambda ep, n: -0.5,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())

    production_result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert production_result["opportunity"]["all_pass"] is True
    natural = production_result["natural"]
    assert natural["u_nat_stable"]["upper_95"] == pytest.approx(-0.5)
    # Isolation check: every other decisive-wrong clause is clearly inactive,
    # so only the mutated clause can be responsible for the row-6 verdict.
    assert not (natural["u_nat_urgent"]["upper_95"] <= 0.5)
    assert not (natural["u_nat_stable"]["lower_95"] >= 0.5)
    assert not (natural["lambda_diff"]["upper_95"] <= 0.0)
    assert not (natural["set_rate_diff"]["upper_95"] <= 0.0)
    assert production_result["result"]["row"] == 6, "fixture must trigger row 6 under the frozen <= predicate"

    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    target = 'nat_stable["upper_95"] <= -MATERIALITY'
    assert source.count(target) == 1, "expected exactly one decisive-wrong nat_stable<=-MATERIALITY site to mutate"
    mutated_source = source.replace(target, 'nat_stable["upper_95"] < -MATERIALITY')
    assert mutated_source != source

    mutant_path = tmp_path / "analyze_vk0_result_mutant.py"
    mutant_path.write_text(mutated_source, encoding="utf-8")
    mutant_spec = importlib.util.spec_from_file_location("analyze_vk0_result_mutant", mutant_path)
    assert mutant_spec is not None and mutant_spec.loader is not None
    mutant = importlib.util.module_from_spec(mutant_spec)
    mutant_spec.loader.exec_module(mutant)

    mutant_result = mutant.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    # Under the mutated strict `<`, upper_95 == -0.5 no longer counts as
    # decisive failure, and the equivalence pass gate (lower_95 > -0.5)
    # also fails since lower_95 == -0.5 -- so the mutant must land on
    # unresolved (row 7), diverging from the production row 6. The
    # mutation is caught (red).
    assert mutant_result["result"]["row"] != 6
    assert mutant_result["natural"]["decisive_wrong"] is False

    # Original file on disk is untouched -- nothing to "restore" -- and the
    # production module (already loaded, unmutated) still reports row 6.
    assert _SCRIPT_PATH.read_text(encoding="utf-8") == source
    rerun = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert rerun["result"]["row"] == 6


# =============================================================================
# CLI
# =============================================================================


def test_cli_refuses_and_writes_nothing_on_schema_violation(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    del check_rows[0]["segment_ending_authority"]
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    out_path = tmp_path / "summary.json"
    completed = subprocess.run(
        [
            sys.executable, str(_SCRIPT_PATH),
            "--trace", str(paths["trace"]), "--units", str(paths["units"]),
            "--oracle-panel", str(paths["panel"]), "--manifest", str(paths["manifest"]),
            "--out", str(out_path),
        ],
        capture_output=True, text=True,
    )
    assert completed.returncode != 0
    assert not out_path.exists()


def test_cli_writes_deterministic_summary_on_success(tmp_path):
    check_rows, unit_rows = build_dataset(SEED)
    paths = write_dataset(tmp_path, check_rows, unit_rows, manifest_for([SEED]), oracle_panel_for())
    out_a = tmp_path / "summary_a.json"
    out_b = tmp_path / "summary_b.json"
    for out_path in (out_a, out_b):
        completed = subprocess.run(
            [
                sys.executable, str(_SCRIPT_PATH),
                "--trace", str(paths["trace"]), "--units", str(paths["units"]),
                "--oracle-panel", str(paths["panel"]), "--manifest", str(paths["manifest"]),
                "--out", str(out_path),
            ],
            capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stderr
    assert out_a.read_bytes() == out_b.read_bytes()
    summary = json.loads(out_a.read_text(encoding="utf-8"))
    assert summary["result"]["code"] == "HETEROGENEOUS_URGENCY_AND_R30_NATURAL_ACCESS_IDENTIFIED"
    assert "analyzer_git_blob_sha1" in summary
