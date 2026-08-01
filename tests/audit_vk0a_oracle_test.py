"""V-K0A source-urgency oracle -- calibration of the exhaustive instrument.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D1,
VK-D10, A-VK-D2) and the two frozen rulings named there.

This machine's default pytest basetemp
(`C:\\Users\\fires\\AppData\\Local\\Temp\\pytest-of-fires`) is broken, so this
file never relies on the `tmp_path` fixture. Every scratch directory lives
under the repository's own `logs/_tmp_vk0a_oracle_test/` tree and is removed
after each test. Invoke with an explicit `--basetemp` anyway so pytest's own
collection-time temp directory (unrelated to these scratch dirs) does not
touch the broken default, e.g.:

    python -m pytest tests/audit_vk0a_oracle_test.py -q --basetemp logs/_pytest_basetemp
"""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "vk0a_oracle", PROJECT_ROOT / "scripts" / "audit_vk0a_source_urgency_oracle.py"
)
oracle = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = oracle
_SPEC.loader.exec_module(oracle)

import config_d7_2b_toy_learned_keep  # noqa: E402  (needs oracle's sys.path insert first)

SCRATCH_ROOT = PROJECT_ROOT / "logs" / "_tmp_vk0a_oracle_test"


def _fresh_scratch_dir(name: str) -> Path:
    d = SCRATCH_ROOT / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


@pytest.fixture(autouse=True)
def _clean_scratch():
    yield
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)


def _config():
    return config_d7_2b_toy_learned_keep.Config()


def test_end_to_end_panel_is_valid_and_deterministic():
    config = _config()

    artifact1 = oracle.build_panel(config)
    out1 = _fresh_scratch_dir("run1")
    panel1, sidecar1 = oracle.write_artifact(artifact1, out1)

    assert artifact1["row_count"] == 112
    assert len(artifact1["rows"]) == 112
    assert artifact1["verdict"] in (
        oracle.VALID_VERDICT,
        oracle.NOT_IDENTIFIED_VERDICT,
        oracle.INVALID_VERDICT,
    )
    assert artifact1["validity"]["all_passed"] is True
    for name in oracle.ValidityTracker.NAMES:
        assert artifact1["validity"][name] is True, name

    recomputed = hashlib.sha256(panel1.read_bytes()).hexdigest()
    assert sidecar1.read_text(encoding="utf-8").strip() == recomputed

    # Determinism: an independent second run must produce byte-identical
    # artifact bytes (no timestamps, no run-to-run float drift).
    artifact2 = oracle.build_panel(config)
    out2 = _fresh_scratch_dir("run2")
    panel2, _ = oracle.write_artifact(artifact2, out2)
    assert panel1.read_bytes() == panel2.read_bytes()


def test_permutation_relabel_matches_unordered_urgency_values():
    """A-VK-D2: at one sampled check, the two permutation tracks must expose
    the same *unordered* {U_src} value pair -- track choice only relabels
    which physical agent holds which duty, it must not change what the
    source contains."""
    config = _config()
    artifact = oracle.build_panel(config)
    rows = artifact["rows"]

    target_combo = rows[0]["sign_combo"]
    target_check = rows[0]["check_index"]
    by_track = {0: [], 1: []}
    for row in rows:
        if row["sign_combo"] == target_combo and row["check_index"] == target_check:
            by_track[row["assignment_permutation"]].append(row["U_src"])

    assert len(by_track[0]) == 2 and len(by_track[1]) == 2
    assert sorted(by_track[0]) == pytest.approx(sorted(by_track[1]), abs=1e-9)


def test_same_label_set_admission_flips_validity_to_invalid():
    """Paired negative for `same_label_set_excluded` (validity condition 4).

    Watched-fail ritual: corrupt the legality enumerator to admit a
    same-label SET, confirm the run goes red (validity fails, verdict is
    INVALID), restore, confirm green. A companion ad hoc check (reported
    alongside this test, not embedded here) additionally verified that with
    the guard predicates themselves stubbed out, the identical corruption is
    NOT caught -- proving this assertion exercises the guard rather than an
    incidental side effect.
    """
    config = _config()
    real_legal_options = oracle.legal_options

    def corrupted_legal_options(incumbent, n_skills=oracle.N_SKILLS):
        opts = real_legal_options(incumbent, n_skills)
        opts.append(("SET", int(incumbent)))  # illegal: same-label SET
        return opts

    oracle.legal_options = corrupted_legal_options
    try:
        artifact_red = oracle.build_panel(config)
    finally:
        oracle.legal_options = real_legal_options

    assert artifact_red["validity"]["same_label_set_excluded"] is False
    assert artifact_red["validity"]["legal_edit_enumeration_exact"] is False
    assert artifact_red["validity"]["all_passed"] is False
    assert artifact_red["verdict"] == oracle.INVALID_VERDICT

    # Revert and confirm green.
    artifact_green = oracle.build_panel(config)
    assert artifact_green["validity"]["all_passed"] is True
    assert artifact_green["verdict"] != oracle.INVALID_VERDICT


def test_teammate_marginal_spans_full_support_and_crosses_duty_axis():
    """A-VK-D2 / full_action_support_maximization_exhausted: the u_src
    computation must explore the teammate's (non-focal slot's) skill across
    the WHOLE 4-skill support, never narrowed to that slot's own duty axis --
    duty-axis restriction only applies to the later incumbent-advancement
    step, never to the u_src maximization itself.

    176 is a known-good literal from a real run of the shipped config (the
    count of argmax_K + argmax_S entries, across all 112 rows, whose
    teammate skill lies outside that teammate slot's own duty axis for that
    row's track) -- an independent source of truth this test pins against,
    not a value the test itself derives from the code under test.

    Watched-fail ritual (reported alongside this test, not embedded here,
    mirroring `test_same_label_set_admission_flips_validity_to_invalid`'s
    precedent): under a track-aware narrowing of `legal_options` down to the
    incumbent's own duty group (a plausible bug -- collapsing the *SET*
    support the same way the *duty-axis-restricted incumbent advancement*
    already is), the same count collapses to 0 (and the run goes INVALID
    because the enumeration no longer has 4 legal options); restoring the
    real `legal_options` brings the count back to 176."""
    config = _config()
    artifact = oracle.build_panel(config)
    rows = artifact["rows"]

    teammate_skills_seen: set[int] = set()
    combined_outside_axis = 0
    argmax_s_outside_axis = 0
    for row in rows:
        focal = row["focal_slot"]
        teammate_slot = 1 - focal
        track = row["assignment_permutation"]
        teammate_axis = oracle.duty_allowed_skills(teammate_slot, track)
        for entry in row["argmax_K"] + row["argmax_S"]:
            teammate_skill = entry["agent_1"] if focal == 0 else entry["agent_0"]
            teammate_skills_seen.add(teammate_skill)
            if teammate_skill not in teammate_axis:
                combined_outside_axis += 1
        for entry in row["argmax_S"]:
            teammate_skill = entry["agent_1"] if focal == 0 else entry["agent_0"]
            if teammate_skill not in teammate_axis:
                argmax_s_outside_axis += 1

    assert teammate_skills_seen == {0, 1, 2, 3}
    assert argmax_s_outside_axis > 0
    assert combined_outside_axis == 176


def test_transient_branch_poisoning_flips_identical_initial_state_red():
    """Paired negative for B1. A real `evaluate_window` wrapper transiently
    poisons `source_env._initial_fast_sign` for exactly one branch call
    (restoring it before returning), simulating in-flight corruption that
    heals itself before the next branch runs.

    The OLD same-call recomputation (`ref_fp = fingerprint(source_env)`
    taken inside the very call it validates, immediately before the
    deepcopy) could never catch this: at the moment that call reads
    `source_env`, it is already poisoned, so ref and deepcopy always agree
    trivially. B1's single reference -- captured once before the branch
    loop starts -- is what makes this fire."""
    config = _config()
    real_evaluate_window = oracle.evaluate_window
    call_count = {"n": 0}

    def poisoning_evaluate_window(
        source_env, skill0, skill1, action_table, expected_table_hash, tracker, ref_fp
    ):
        call_count["n"] += 1
        poison_here = call_count["n"] == 3
        original = None
        if poison_here:
            original = source_env._initial_fast_sign
            source_env._initial_fast_sign = -1.0 * original
        try:
            return real_evaluate_window(
                source_env, skill0, skill1, action_table, expected_table_hash, tracker, ref_fp
            )
        finally:
            if poison_here:
                source_env._initial_fast_sign = original

    oracle.evaluate_window = poisoning_evaluate_window
    try:
        artifact_red = oracle.build_panel(config)
    finally:
        oracle.evaluate_window = real_evaluate_window

    assert artifact_red["validity"]["identical_initial_state_across_branches"] is False
    assert artifact_red["validity"]["all_passed"] is False

    artifact_green = oracle.build_panel(config)
    assert artifact_green["validity"]["identical_initial_state_across_branches"] is True
    assert artifact_green["validity"]["all_passed"] is True


def test_duty_axis_collapse_flips_permutation_relabels_only_red():
    """Paired negative for B3. Monkeypatch `duty_allowed_skills` so track 1
    is handed track 0's own duty axes (collapsing the mirror): track 1 no
    longer explores the swapped assignment, so its incumbent pair stops
    being the exact slot-swap of track 0's, and
    `permutation_relabels_only` must go False. The state-only cross-track
    fingerprint check (kept as an auxiliary signal) does NOT catch this --
    the environment's own dynamics never depend on which skill either agent
    holds, only the incumbent/urgency mirror check does."""
    config = _config()
    real_duty_allowed_skills = oracle.duty_allowed_skills

    def collapsed_duty_allowed_skills(slot, track):
        return real_duty_allowed_skills(slot, 0)

    oracle.duty_allowed_skills = collapsed_duty_allowed_skills
    try:
        artifact_red = oracle.build_panel(config)
    finally:
        oracle.duty_allowed_skills = real_duty_allowed_skills

    assert artifact_red["validity"]["permutation_relabels_only"] is False
    assert artifact_red["validity"]["all_passed"] is False

    artifact_green = oracle.build_panel(config)
    assert artifact_green["validity"]["permutation_relabels_only"] is True
    assert artifact_green["validity"]["all_passed"] is True


def test_shipped_config_ground_truth_pinned():
    """Independent pinned literal, not recomputed the way the code under
    test computes it: the shipped config's real 112-row panel must be
    exactly this verdict, this U_src support, and this URGENT/STABLE
    split."""
    config = _config()
    artifact = oracle.build_panel(config)

    assert artifact["verdict"] == oracle.VALID_VERDICT
    u_src_values = {row["U_src"] for row in artifact["rows"]}
    assert u_src_values == {0.0, 2.5}
    urgent = sum(1 for row in artifact["rows"] if row["urgency_class"] == "URGENT")
    stable = sum(1 for row in artifact["rows"] if row["urgency_class"] == "STABLE")
    assert urgent == 64
    assert stable == 48
    assert urgent + stable == 112


def test_compute_u_src_env_non_mutation_and_fail_closed_without_tracker():
    """`compute_u_src` (A-VK-D10's external, V-K0B-facing surface) must
    never mutate its `env` argument, and a corrupted legal-edit enumeration
    must still raise `SourceAuditInvalid` even with no `ValidityTracker` at
    all -- fail-closed is not a V-K0A-only bookkeeping property."""
    config = _config()
    env = oracle.TwoTimescaleRoleFreeActionsEnv(config=config)
    env.reset(seed=0)

    policy = oracle.FixedSkillPrimitivePolicy(4, 2, "continuous")
    action_table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    table_hash = hashlib.sha256(np.ascontiguousarray(action_table).tobytes()).hexdigest()

    fp_before = oracle.fingerprint(env)
    result = oracle.compute_u_src(env, (0, 2), action_table, table_hash)
    fp_after = oracle.fingerprint(env)

    assert fp_after == fp_before
    assert set(result.keys()) == {0, 1}

    real_legal_options = oracle.legal_options

    def corrupted_legal_options(incumbent, n_skills=oracle.N_SKILLS):
        opts = real_legal_options(incumbent, n_skills)
        opts.append(("SET", int(incumbent)))
        return opts

    oracle.legal_options = corrupted_legal_options
    try:
        with pytest.raises(oracle.SourceAuditInvalid):
            oracle.compute_u_src(env, (0, 2), action_table, table_hash)
    finally:
        oracle.legal_options = real_legal_options


def test_b2_predicate_flags_k0_drift_below_the_premise_gate():
    """Test-gap-3, realized one layer below build_panel's B4 premise gate
    (PM ruling 2026-08-01): a k0-mismatched config never reaches window
    evaluation end-to-end (B4 aborts build_panel first, correctly, with no
    artifact) -- so this proves B2's in-flight predicate at the unit level
    instead, calling `compute_incumbent_edit_results` directly on an env
    built with r39_toy_k0=4, bypassing build_panel /
    resolve_and_assert_env_premises entirely.

    Outer gate (B4, in build_panel) = config-wiring refusal, no artifact.
    Inner predicate (B2, in evaluate_window) = in-flight arithmetic drift
    detection, unit-proven here because the outer gate correctly makes it
    unreachable end-to-end."""

    class _K0DriftConfig(config_d7_2b_toy_learned_keep.Config):
        r39_toy_k0 = 4

    env = oracle.TwoTimescaleRoleFreeActionsEnv(config=_K0DriftConfig())
    env.reset(seed=0)
    assert int(env.k0) == 4  # confirms the drift is real, not a fixture no-op

    policy = oracle.FixedSkillPrimitivePolicy(4, 2, "continuous")
    action_table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    table_hash = hashlib.sha256(np.ascontiguousarray(action_table).tobytes()).hexdigest()

    tracker = oracle.ValidityTracker()
    oracle.compute_incumbent_edit_results(
        env, (0, 2), action_table, table_hash, tracker, check_index=1
    )

    assert tracker.results["no_check_crossed_within_window"] is False
    assert tracker.all_passed() is False


def test_b4_premise_gate_aborts_end_to_end_with_no_artifact():
    """R1/R2: the B4 hard abort must actually fire end-to-end for both
    drifted clocks, before any window evaluation and before any artifact is
    written. slow_period_blocks is the clock that determines where
    JOINT_CHECK_INDEX=6 (step 30) really falls -- with slow_period_blocks=3
    the true joint fast+slow transitions land at checks 3 AND 6, so a
    drifted slow_period_blocks that slipped past this gate would silently
    produce a scientifically wrong NOT_IDENTIFIED verdict instead of
    aborting."""

    class _K0DriftConfig(config_d7_2b_toy_learned_keep.Config):
        r39_toy_k0 = 4

    class _SlowPeriodDriftConfig(config_d7_2b_toy_learned_keep.Config):
        r39_toy_slow_period_blocks = 3

    for drifted_config_cls in (_K0DriftConfig, _SlowPeriodDriftConfig):
        out_dir = _fresh_scratch_dir(f"b4_abort_{drifted_config_cls.__name__}")
        with pytest.raises(oracle.SourceAuditInvalid):
            artifact = oracle.build_panel(drifted_config_cls())
            oracle.write_artifact(artifact, out_dir)
        assert list(out_dir.iterdir()) == []
