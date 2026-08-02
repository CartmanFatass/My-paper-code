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


def default_target_vector_pair(check_index=0):
    """A well-formed {'slow','fast'} target-vector pair (A-W6-4 / W6-D4) --
    shape mirrors the env's own `_targets()`: two 2-element (sign/zero)
    vectors. Values are dummy but well-typed; the current V-K0B statistics
    ignore these fields beyond validation."""
    return {"slow": [1.0, 0.0], "fast": [0.0, 1.0 if check_index % 2 == 0 else -1.0]}


def make_check_row(*, training_seed, episode_id, agent_order, check_index, focal_agent,
                    check_unit_id, u_src, natural_token_kind, keep_prob,
                    slow_match=1, fast_match=1, checkpoint_hash=DEFAULT_CHECKPOINT_HASH,
                    resolved_config_hash=DEFAULT_CONFIG_HASH, oracle_urgency_class=None,
                    incumbent_end_authority_at_check=None, post_window_end_authority=None,
                    current_targets=None, previous_targets=None):
    row = _identity(training_seed, episode_id, agent_order, check_index, focal_agent,
                     check_unit_id, checkpoint_hash, resolved_config_hash)
    if oracle_urgency_class is None:
        oracle_urgency_class = "URGENT" if u_src > 0.5 else ("STABLE" if u_src < 0.5 else "BOUNDARY")
    if incumbent_end_authority_at_check is None:
        # A-W6-4: a voluntary SET ends the incumbent segment at the check
        # boundary; a KEEP row ordinarily carries none_open.
        incumbent_end_authority_at_check = "voluntary_set" if natural_token_kind == "SET" else "none_open"
    if post_window_end_authority is None:
        post_window_end_authority = "none_open"
    row.update(
        {
            "oracle_u_src": u_src,
            "oracle_urgency_class": oracle_urgency_class,
            "natural_token_kind": natural_token_kind,
            "natural_set_skill": "z1" if natural_token_kind == "SET" else None,
            "keep_prob": keep_prob,
            "incumbent_end_authority_at_check": incumbent_end_authority_at_check,
            "post_window_end_authority": post_window_end_authority,
            "current_targets": current_targets or default_target_vector_pair(check_index),
            "previous_targets": previous_targets or default_target_vector_pair(check_index - 1),
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


def valid_actual_exposure_block():
    """A-W6-1/A-W6-2/A-W6-5: a fully conforming per-seed `actual_exposure`
    block at the exact identical-contract identities -- 640,000 interactions,
    1,000 outer updates, 3,000/3,000/0/0 high-pass attempted/stepped/skipped/
    aborted, exact shared/actor/value optimizer steps, complete parameter
    coverage, and the N_KEEP+N_SET=2*N_sequences token identity
    (1400+1600=2*1500). Fresh dict per call -- callers mutate their own copy
    via `_patched_exposure_block`, never a shared one."""

    def w(value, source="runtime_counter"):
        return {"value": value, "source": source}

    return {
        "actual_exposure_schema": M.ACTUAL_EXPOSURE_SCHEMA,
        "high_optimizer_semantics": M.HIGH_OPTIMIZER_SEMANTICS_SHARED,
        "environment_interactions": w(640_000),
        "completed_outer_updates": w(1_000),
        "high_optimizer_steps_shared": w(3_000, "optimizer_state"),
        "high_actor_optimizer_steps": w(3_000, "optimizer_state"),
        "high_value_optimizer_steps": w(3_000, "optimizer_state"),
        "high_actor_parameter_count_expected": w(42, "training_accumulator"),
        "high_actor_parameter_count_with_step_state": w(42, "optimizer_state"),
        "high_value_parameter_count_expected": w(17, "training_accumulator"),
        "high_value_parameter_count_with_step_state": w(17, "optimizer_state"),
        "high_optimizer_step_min": w(3_000, "optimizer_state"),
        "high_optimizer_step_max": w(3_000, "optimizer_state"),
        "high_optimizer_parameter_coverage_ok": w(True, "optimizer_state"),
        "high_check_sequences_completed": w(1_500, "training_accumulator"),
        "high_check_sequences_failed_or_skipped": w(0, "training_accumulator"),
        "agent_tokens_keep": w(1_400, "training_accumulator"),
        "agent_tokens_set": w(1_600, "training_accumulator"),
        "high_epoch_passes_attempted": w(3_000, "runtime_counter"),
        "high_epoch_passes_stepped": w(3_000, "runtime_counter"),
        "high_epoch_passes_skipped": w(0, "runtime_counter"),
        "high_epoch_passes_aborted": w(0, "runtime_counter"),
        "high_epoch_pass_skip_reasons": w([], "runtime_counter"),
        "high_epoch_pass_abort_reasons": w([], "runtime_counter"),
        "low_level_optimizer_steps": w(0, "checkpoint_optimizer_absence"),
    }


def _patched_exposure_block(overrides):
    """Applies a shallow {field_name: replacement_entry} patch onto a fresh
    valid block -- e.g. {"high_epoch_passes_skipped": {"value": 1, "source":
    "runtime_counter"}} for a negative-witness fixture."""
    block = valid_actual_exposure_block()
    if overrides:
        block.update(overrides)
    return block


def manifest_for(seeds, checkpoint_hash=DEFAULT_CHECKPOINT_HASH,
                  resolved_config_hash=DEFAULT_CONFIG_HASH, low_optimizer_steps=0,
                  authorization=None, exposure_overrides=None,
                  source_run_manifest_sha256="e" * 64):
    exposure_overrides = exposure_overrides or {}
    manifest = {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": SCHEMA_VERSION,
        "seeds": {
            str(seed): {
                "checkpoint_hash": checkpoint_hash,
                "resolved_config_hash": resolved_config_hash,
                "low_optimizer_steps": low_optimizer_steps,
                "actual_exposure": _patched_exposure_block(exposure_overrides.get(seed)),
                "source_run_manifest_sha256": source_run_manifest_sha256,
            }
            for seed in seeds
        },
    }
    if authorization is not None:
        manifest["authorization"] = authorization
    return manifest


# The exact key set observed on the real V-K0A panel emitted by
# scripts/audit_vk0a_source_urgency_oracle.py (inspected directly from
# logs/vk0a_formal/source_oracle_panel.json during this fix): `acceptance`,
# `action_table_hash`, `contract_id`, `env_premises`, `environment_blob_sha`,
# `initial_check_metadata`, `oracle_script_hash`, `panel_schema_version`,
# `row_count`, `rows`, `seed_to_sign_map`, `stage_commit`, `validity`,
# `verdict`. Notably it carries NO `validity_predicates` and NO
# `artifact_sha256` -- those are the driver's (audit_vk0b_r30_access.py)
# authorization-view derivation, recorded only in the run manifest. Fixtures
# below reproduce this literal key set (not a runtime dependency on the log
# file itself, which is generated evidence, not implementation source) so a
# schema of the fixture drifting from the real artifact is caught locally.
REAL_PANEL_KEY_SET = frozenset(
    {
        "acceptance", "action_table_hash", "contract_id", "env_premises",
        "environment_blob_sha", "initial_check_metadata", "oracle_script_hash",
        "panel_schema_version", "row_count", "rows", "seed_to_sign_map",
        "stage_commit", "validity", "verdict",
    }
)


def oracle_panel_for(verdict=M.VK0A_VERDICT_IDENTIFIED, row_count=M.VK0A_PANEL_ROW_COUNT):
    """The RAW V-K0A panel schema exactly as
    scripts/audit_vk0a_source_urgency_oracle.py emits it: a `validity` dict
    of named booleans (plus `all_passed`/`violations`), never a pre-derived
    `validity_predicates` or `artifact_sha256` -- see `authorization_for`
    for the driver's separate authorization-view derivation of those."""
    validity = {name: True for name in M.VK0A_VALIDITY_PREDICATE_NAMES}
    validity["all_passed"] = True
    validity["violations"] = []
    panel = {
        "contract_id": CONTRACT_ID,
        "stage_commit": "c4b64841798d65af8474ded00bf623a109c7c792",
        "environment_blob_sha": "envsha",
        "action_table_hash": "actiontablehash",
        "oracle_script_hash": "oraclehash",
        "panel_schema_version": "panel-v1",
        "row_count": row_count,
        "validity": validity,
        "verdict": verdict,
        # Present but unvalidated by the analyzer, kept so this fixture's
        # key set matches REAL_PANEL_KEY_SET exactly.
        "rows": [{"seed": 0, "check_index": 0}],
        "acceptance": {"each_slot_in_both_classes": True},
        "seed_to_sign_map": {"0": [1, 1]},
        "initial_check_metadata": {},
        "env_premises": {},
    }
    assert set(panel.keys()) == REAL_PANEL_KEY_SET
    return panel


def authorization_for(panel, *, tamper_hash=False):
    """Exactly the driver's derivation (scripts/audit_vk0b_r30_access.py,
    `resolve_oracle_panel`): validity_predicates from panel["validity"] over
    the eight named predicates, then artifact_sha256 = SHA-256 over the
    canonical nine-field tuple. Computed here via the analyzer's own
    (mirrored) formula, not duplicated by hand, so a fixture's "correct"
    authorization is defined identically to what the analyzer will
    recompute -- the tamper path is the only place this test file
    deliberately diverges from that formula."""
    authorization = M._panel_tuple_payload(panel)
    authorization["artifact_sha256"] = M._panel_expected_sha256(panel)
    if tamper_hash:
        authorization["artifact_sha256"] = "0" * 64
    return authorization


def standard_manifest_and_panel(
    seeds,
    *,
    checkpoint_hash=DEFAULT_CHECKPOINT_HASH,
    resolved_config_hash=DEFAULT_CONFIG_HASH,
    low_optimizer_steps=0,
    verdict=M.VK0A_VERDICT_IDENTIFIED,
    row_count=M.VK0A_PANEL_ROW_COUNT,
    omit_authorization=False,
    tamper_hash=False,
    exposure_overrides=None,
):
    """The common case: a manifest/panel pair whose authorization is
    correctly matched (unless deliberately broken via omit_authorization or
    tamper_hash), and whose per-seed actual_exposure block is fully valid
    (unless overridden per-seed via exposure_overrides) -- returned as
    (manifest, panel) for
    `write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel(...))`."""
    panel = oracle_panel_for(verdict=verdict, row_count=row_count)
    authorization = None if omit_authorization else authorization_for(panel, tamper_hash=tamper_hash)
    manifest = manifest_for(
        seeds, checkpoint_hash=checkpoint_hash, resolved_config_hash=resolved_config_hash,
        low_optimizer_steps=low_optimizer_steps, authorization=authorization,
        exposure_overrides=exposure_overrides,
    )
    return manifest, panel


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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_analyzer_refuses_on_bad_enum_field(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    check_rows[0]["agent_order_code"] = "north"
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_analyzer_refuses_on_window_return_inconsistent_with_reward_vector(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    unit_rows[0]["window_return"] = unit_rows[0]["window_return"] + 1000.0
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    seed_counts = result["support_floor"]["per_seed"][str(SEED)]
    assert seed_counts["urgent_total"] == urgent_before


# =============================================================================
# Result rows 1-8: full first-match scenarios
# =============================================================================


def test_row1_invalid_on_replay_conformance_false(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    unit_rows[3]["replay_conformance"] = {"boundary_fingerprint": False}
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert result["result"]["code"] == "INVALID_VARIABLE_K_URGENCY_AUDIT"


def test_row1_invalid_on_manifest_checkpoint_mismatch(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], checkpoint_hash="a-different-checkpoint"),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row1_invalid_on_prohibited_optimizer_exposure(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], low_optimizer_steps=3),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row1_invalid_on_oracle_panel_authorization_hash_tamper(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED], tamper_hash=True),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1


def test_row1_invalid_on_manifest_missing_authorization(tmp_path):
    # A manifest recorded without ever verifying the V-K0A artifact tuple
    # (VK-D10) is itself the row-1 finding -- not a schema refusal, and not
    # silently treated as "authorization not required".
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED], omit_authorization=True),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert any("no oracle-panel authorization record" in reason for reason in result["result"]["reasons"])


def test_oracle_panel_fixture_matches_the_real_raw_panel_key_set():
    panel = oracle_panel_for()
    assert set(panel.keys()) == REAL_PANEL_KEY_SET
    assert M.validate_oracle_panel(panel) == []
    # The driver's derivation must round-trip cleanly against the real
    # `validity` shape (8 named booleans plus all_passed/violations).
    predicates = M.derive_validity_predicates(panel)
    assert set(predicates) == set(M.VK0A_VALIDITY_PREDICATE_NAMES)
    assert all(predicates.values())


def test_row2_source_not_identified(tmp_path):
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], verdict=M.VK0A_VERDICT_NOT_IDENTIFIED),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 2
    assert result["result"]["code"] == "TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED"


def test_row3_support_floor_insufficient(tmp_path):
    # Far below the 192-per-class / 64-per-class-per-order floor.
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 3
    assert result["result"]["code"] == "R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT"
    assert result["support_floor"]["per_seed"][str(SEED)]["pass"] is False


def test_row4_competence_not_established(tmp_path):
    check_rows, unit_rows = build_dataset(
        SEED, urgent_slow_match=0, urgent_fast_match=0, stable_slow_match=0, stable_fast_match=0,
    )
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 8
    assert result["result"]["code"] == "HETEROGENEOUS_URGENCY_AND_R30_NATURAL_ACCESS_IDENTIFIED"


# =============================================================================
# Actual-exposure block (W6-D3 / A-W6-1 / A-W6-2 / A-W6-5, round
# 20260801_vk0b_rerun_exposure_conformance) -- the missing frozen row-1
# predicate: exact per-seed training-optimizer exposure.
# =============================================================================

SIX_SEEDS = [2026080101, 2026080102, 2026080103, 2026080104, 2026080105, 2026080106]


def test_row1_not_triggered_by_valid_exposure_block_at_all_six_seeds(tmp_path):
    # (a) A valid actual_exposure block at exact identical-contract
    # identities, at all six frozen scientific seeds, must not itself
    # trigger row 1 -- this reuses the cheap row-3 (support-insufficient)
    # scenario purely to prove the exposure gate is clean; the point under
    # test is "proceeds past row 1", not the row-3 code itself.
    check_rows, unit_rows = [], []
    for seed in SIX_SEEDS:
        c, u = build_dataset(seed, rows_per_class_order=8)
        check_rows.extend(c)
        unit_rows.extend(u)
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel(SIX_SEEDS))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] != 1
    assert result["result"]["row"] == 3
    assert result["result"]["code"] == "R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT"


def test_row1_invalid_on_honestly_recorded_skip(tmp_path):
    # (b) A-W6-2: 2,999 stepped + 1 honestly recorded skip (attempted still
    # = stepped+skipped+aborted = 3000, so the partition identity itself
    # holds) is nonetheless a violation -- "recording a deviation does not
    # make that deviation admissible". Without the corruption this exact
    # full-scale dataset resolves to row 8 (test_row8_...); the corruption
    # alone must flip it to row 1, proving the predicate is load-bearing.
    check_rows, unit_rows = build_dataset(SEED)
    overrides = {
        SEED: {
            "high_epoch_passes_stepped": {"value": 2_999, "source": "runtime_counter"},
            "high_epoch_passes_skipped": {"value": 1, "source": "runtime_counter"},
            "high_optimizer_steps_shared": {"value": 2_999, "source": "optimizer_state"},
            "high_actor_optimizer_steps": {"value": 2_999, "source": "optimizer_state"},
            "high_value_optimizer_steps": {"value": 2_999, "source": "optimizer_state"},
            "high_optimizer_step_min": {"value": 2_999, "source": "optimizer_state"},
            "high_optimizer_step_max": {"value": 2_999, "source": "optimizer_state"},
        }
    }
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], exposure_overrides=overrides),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert result["result"]["code"] == "INVALID_VARIABLE_K_URGENCY_AUDIT"
    assert any("TRAINING_OPTIMIZER_EXPOSURE_MISMATCH" in r for r in result["result"]["reasons"])


def test_row1_invalid_on_inadmissible_exposure_source_label(tmp_path):
    # (c) "config" is explicitly named inadmissible (A-W6-5) -- even though
    # the recorded value itself is the frozen-correct 640,000.
    check_rows, unit_rows = build_dataset(SEED)
    overrides = {SEED: {"environment_interactions": {"value": 640_000, "source": "config"}}}
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], exposure_overrides=overrides),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert any("TRAINING_OPTIMIZER_EXPOSURE_MISMATCH" in r for r in result["result"]["reasons"])


def test_row1_invalid_on_token_identity_violation(tmp_path):
    # (d) A-W6-3: N_KEEP + N_SET must equal 2 * N_high_sequences exactly.
    # 1400 + 1601 != 2*1500.
    check_rows, unit_rows = build_dataset(SEED)
    overrides = {SEED: {"agent_tokens_set": {"value": 1_601, "source": "training_accumulator"}}}
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], exposure_overrides=overrides),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert any("TRAINING_OPTIMIZER_EXPOSURE_MISMATCH" in r for r in result["result"]["reasons"])


def test_row1_invalid_on_coverage_not_ok(tmp_path):
    # (e) A-W6-1: uniformity over existing optimizer-state entries is not a
    # coverage certificate -- an explicit coverage_ok=false must invalidate
    # even though every other field in the block is at its frozen value.
    check_rows, unit_rows = build_dataset(SEED)
    overrides = {SEED: {"high_optimizer_parameter_coverage_ok": {"value": False, "source": "optimizer_state"}}}
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], exposure_overrides=overrides),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert any("TRAINING_OPTIMIZER_EXPOSURE_MISMATCH" in r for r in result["result"]["reasons"])


def test_row1_invalid_on_parameter_coverage_short_of_expected(tmp_path):
    # (e), second half: a trainable parameter that never received a
    # gradient has no optimizer-state entry and is invisible to a naive
    # uniformity check -- with_step_state < expected must be caught even
    # though coverage_ok itself was (incorrectly) left true.
    check_rows, unit_rows = build_dataset(SEED)
    overrides = {
        SEED: {"high_actor_parameter_count_with_step_state": {"value": 41, "source": "optimizer_state"}}
    }
    paths = write_dataset(
        tmp_path, check_rows, unit_rows,
        *standard_manifest_and_panel([SEED], exposure_overrides=overrides),
    )
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["result"]["row"] == 1
    assert any("TRAINING_OPTIMIZER_EXPOSURE_MISMATCH" in r for r in result["result"]["reasons"])


# =============================================================================
# vk0-trace-2 segment-ending fields (A-W6-4)
# =============================================================================


def test_row_schema_refuses_trace2_row_carrying_retired_segment_ending_authority(tmp_path):
    # (f) The vk0-trace-1 scalar is retired under vk0-trace-2: a row that
    # still carries it must be refused, not silently accepted or ignored.
    # Every other test in this suite proves the negative (a row WITHOUT this
    # key validates fine), so adding the key back is what flips this fixture.
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    check_rows[0]["segment_ending_authority"] = "voluntary_set"
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])


def test_final_check_dual_ending_row_validates_under_trace2(tmp_path):
    # (g) A final-check voluntary SET whose newly started segment is then
    # ended by episode termination must carry BOTH non-none_open values --
    # the exact case the single old scalar could not represent.
    check_rows, unit_rows = build_dataset(SEED, rows_per_class_order=8)
    check_rows[0]["incumbent_end_authority_at_check"] = "voluntary_set"
    check_rows[0]["post_window_end_authority"] = "episode_termination"
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    # Reaches the ordinary pipeline (schema accepted it, row 1 did not fire
    # on it) -- at this cheap rows_per_class_order=8 scale that means row 3.
    assert result["result"]["row"] == 3


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
        paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
        result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    assert result["support_floor"]["pass"] is False
    assert result["result"]["row"] == 3
    assert "opportunity" not in result


# =============================================================================
# Determinism
# =============================================================================


def test_determinism_two_runs_are_byte_identical(tmp_path):
    check_rows, unit_rows = build_dataset(SEED)
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
    result = M.run_analysis(paths["trace"], paths["units"], paths["panel"], paths["manifest"])
    pooled = result["opportunity"]["pooled"]
    assert pooled["urgent"]["lower_95"] > 0.5
    assert pooled["stable"]["upper_95"] < 0.5


def test_bootstrap_straddling_effect_yields_unresolved_not_decisive(tmp_path):
    def urgent_opp_fn(local_ep, n_episodes):
        return 1.5 if local_ep < n_episodes // 2 else -0.5

    check_rows, unit_rows = build_dataset(SEED, urgent_opp_fn=urgent_opp_fn)
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))

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
    del check_rows[0]["current_targets"]
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
    paths = write_dataset(tmp_path, check_rows, unit_rows, *standard_manifest_and_panel([SEED]))
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
