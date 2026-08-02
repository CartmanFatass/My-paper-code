"""V-K0B evaluation driver -- proof-sized executable skeleton.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D3,
VK-D5, VK-D6, VK-D7, VK-D8, VK-D10, every A-VK-D amendment) and the two frozen
rulings named there. This is Pro's permitted "executable skeleton" (convergence
round `20260801_vk0_design_conformance`): NO training, NO scientific run. Every
agent here is freshly, randomly initialized (never loaded from a checkpoint),
and every replicate count is shrunk via an internal test-only hook -- the
frozen CLI contract (2 select + 2 eval draws, 64 episodes) is never touched.

This machine's default pytest basetemp
(`C:\\Users\\fires\\AppData\\Local\\Temp\\pytest-of-fires`) is broken, so this
file never relies on the `tmp_path` fixture. Invoke with an explicit
`--basetemp` anyway:

    python -m pytest tests/audit_vk0b_driver_test.py -q --basetemp logs/_pytest_basetemp
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


oracle = _load("vk0a_oracle_for_vk0b_test", "audit_vk0a_source_urgency_oracle.py")
driver = _load("vk0b_driver_under_test", "audit_vk0b_r30_access.py")

import config_d7_2b_toy_learned_keep  # noqa: E402  (needs the loader's sys.path insert first)

SCRATCH_ROOT = PROJECT_ROOT / "logs" / "_tmp_vk0b_driver_test"


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


def _fake_entry(training_seed: int = 999) -> dict:
    return {
        "training_seed": training_seed,
        "checkpoint_path": "unused-because-load_checkpoint-is-False.pt",
        "checkpoint_sha256": "f" * 64,
        "resolved_config_hash": "c" * 64,
    }


# =============================================================================
# (1) Two-episode skeleton run: identity keys, joins, paired KEEP, fingerprint
#     replay, and a clean replay_mismatch=False completion.
# =============================================================================


def test_two_episode_skeleton_run_is_internally_consistent():
    config = _config()
    result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=2, n_select=1, n_eval=1, load_checkpoint=False,
    )

    # V-K0B's frozen shared per-episode bank alternates canonical/reversed by
    # parity (driver.agent_order_for_evaluation_index), so episodes=2 covers
    # exactly one of each order.
    assert {row["agent_order_code"] for row in result.check_rows} == {
        driver.AGENT_ORDER_CANONICAL, driver.AGENT_ORDER_REVERSED,
    }
    # 2 episodes x 7 noninitial checks x 2 focal agents.
    assert len(result.check_rows) == 2 * 7 * 2

    identity_keys = (
        "contract_id", "trace_schema_version", "training_seed", "evaluation_seed",
        "episode_id", "agent_order_code", "check_index", "focal_agent", "check_unit_id",
        "checkpoint_hash", "resolved_config_hash",
    )
    for row in result.check_rows:
        for key in identity_keys:
            assert row[key] is not None, f"check row missing {key}: {row}"
        assert row["check_index"] != 0, "the initial check has no incumbent and must be excluded (VK-D1)"

    check_ids = {row["check_unit_id"] for row in result.check_rows}
    assert len(result.unit_rows) > 0
    for row in result.unit_rows:
        for key in identity_keys:
            assert row[key] is not None, f"unit row missing {key}: {row}"
        # Counterfactual rows join to their parent check rows.
        assert row["parent_check_unit_id"] in check_ids
        assert row["check_unit_id"] in check_ids
        # Fingerprints equal within each family: every emitted row's own
        # replay conformance is True (a mismatch would have aborted the
        # family and this run instead -- see test 3 for the negative case).
        assert row["replay_conformance"]["fingerprint_match"] is True

    # Each non-KEEP_REFERENCE family has its paired KEEP unit.
    branch_ids = {row["branch_unit_id"] for row in result.unit_rows}
    for row in result.unit_rows:
        if row["estimand_family"] == driver.ESTIMAND_KEEP_REFERENCE:
            assert row["paired_keep_unit_id"] is None
            continue
        assert row["paired_keep_unit_id"] is not None, row
        assert row["paired_keep_unit_id"] in branch_ids

    assert result.replay_mismatch is False


# =============================================================================
# (2) Authorization paired negative, watched red.
# =============================================================================


def test_authorization_refuses_a_tampered_panel_and_passes_when_restored():
    config = _config()
    scratch = _fresh_scratch_dir("authorization")
    artifact = oracle.build_panel(config)
    panel_path, digest_path = oracle.write_artifact(artifact, scratch)

    original_bytes = panel_path.read_bytes()
    tampered = bytearray(original_bytes)
    # Flip one byte inside the JSON body (well past the opening brace) so the
    # file stays syntactically plausible-looking but its hash changes.
    flip_at = len(tampered) // 2
    tampered[flip_at] ^= 0xFF
    panel_path.write_bytes(bytes(tampered))

    with pytest.raises(driver.Vk0bRefusalError, match="PANEL_DIGEST_MISMATCH"):
        driver.load_and_authorize_panel(panel_path, digest_path)

    # Restore and confirm green.
    panel_path.write_bytes(original_bytes)
    result = driver.load_and_authorize_panel(panel_path, digest_path)
    assert result["authorization"]["verdict"] == oracle.VALID_VERDICT


# =============================================================================
# (3) Fingerprint paired negative, watched red.
# =============================================================================


def _bump_steps_to_check(fp: dict) -> dict:
    perturbed = dict(fp)
    perturbed["steps_to_check"] = int(perturbed["steps_to_check"]) + 1
    return perturbed


def test_fingerprint_perturbation_aborts_the_family_and_invalidates_the_run():
    config = _config()

    perturbed_result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=1, n_select=1, n_eval=1,
        load_checkpoint=False, fingerprint_perturber=_bump_steps_to_check,
    )
    assert perturbed_result.replay_mismatch is True
    assert perturbed_result.mismatched_families, "expected at least one recorded mismatch"
    mismatched_rows = [
        row for row in perturbed_result.unit_rows if row["replay_conformance"]["fingerprint_match"] is False
    ]
    assert mismatched_rows, "a perturbed fingerprint must be visible as a False replay_conformance row"
    for row in mismatched_rows:
        # Fail-closed placeholder shape (A-VK-D3): the row still carries every
        # identity key so the analyzer's replay-conformance scan can find it,
        # but no real reward content.
        assert row["window_return"] == 0.0
        assert row["external_reward_vector"] == [0.0] * driver.WINDOW

    # Remove the perturbation and confirm green on the identical inputs.
    clean_result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=1, n_select=1, n_eval=1, load_checkpoint=False,
    )
    assert clean_result.replay_mismatch is False
    assert all(row["replay_conformance"]["fingerprint_match"] is True for row in clean_result.unit_rows)


# =============================================================================
# (4) U_src oracle-consistency: recompute independently via the exposed
#     oracle function and the row's own durable identity, not the driver's
#     internals.
# =============================================================================


def test_oracle_u_src_matches_independent_recomputation_from_row_identity():
    config = _config()
    result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=1, n_select=1, n_eval=1, load_checkpoint=False,
    )
    focal0_rows = {
        (row["check_index"], row["episode_id"], row["agent_order_code"]): row
        for row in result.check_rows if row["focal_agent"] == 0
    }
    focal1_rows = {
        (row["check_index"], row["episode_id"], row["agent_order_code"]): row
        for row in result.check_rows if row["focal_agent"] == 1
    }
    key = next(iter(focal0_rows))
    row0 = focal0_rows[key]
    row1 = focal1_rows[key]
    check_index, episode_id, agent_order_code = key

    # Reconstruct the joint incumbent pair from the two sibling check rows'
    # own `current_skill` fields -- durable row data, not driver internals.
    incumbent = (int(row0["current_skill"]), int(row1["current_skill"]))

    # Reconstruct the raw env at this check's boundary independently: the
    # environment is deterministic given `reset(seed)` and `steps` alone
    # (VK-D1), so re-deriving the episode seed from the row's own identity
    # and stepping forward with any legal action reproduces the identical
    # state -- exactly the technique the driver itself uses (never trusted
    # from the driver's live objects).
    ep_seed = driver.episode_seed(int(next(i for i in range(64) if driver.episode_seed(i) == episode_id)))
    assert ep_seed == episode_id
    raw_env_wrapper = driver.make_env(config, int(ep_seed))
    raw_env_wrapper.reset(seed=int(ep_seed))
    raw_env = raw_env_wrapper.env
    zero_action = {k: np.zeros(2, dtype="float32") for k in ("agent_0", "agent_1")}
    for _ in range(check_index * driver.K0):
        raw_env.step(zero_action)

    # The action table and its hash, rebuilt independently here rather than
    # reused from the driver's own precomputed module constants -- otherwise
    # a wrong table hash baked into the driver could never be caught by this
    # test.
    from ha_ctse_process.standalone_agent import FixedSkillPrimitivePolicy

    policy = FixedSkillPrimitivePolicy(4, 2, "continuous")
    action_table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    table_hash = driver.hash_bytes(np.ascontiguousarray(action_table).tobytes())

    recomputed = oracle.compute_u_src(raw_env, incumbent, action_table, table_hash)
    raw_env_wrapper.close()

    assert recomputed[0]["U_src"] == pytest.approx(row0["oracle_u_src"], abs=1e-9)
    assert recomputed[1]["U_src"] == pytest.approx(row1["oracle_u_src"], abs=1e-9)
    assert recomputed[0]["urgency_class"] == row0["oracle_urgency_class"]
    assert recomputed[1]["urgency_class"] == row1["oracle_urgency_class"]


# =============================================================================
# (5) W6-D4 target vectors: independent recomputation from a FRESH env replay
#     (never the driver's own live capture), spot-asserting one fast flip and
#     the joint check; plus both A-W6-4 ending fields present with legal
#     values on every row, and the vk0-trace-2 schema bump.
# =============================================================================


def _independent_targets(config, episode_id: int, check_index: int) -> dict:
    """Fresh env, independent of the driver's own bookkeeping (same technique
    as test 4's oracle recomputation): step a NEW raw env forward to this
    check's own primitive step and read `_targets()` directly off it."""
    wrapper = driver.make_env(config, int(episode_id))
    wrapper.reset(seed=int(episode_id))
    raw_env = wrapper.env
    zero_action = {"agent_0": np.zeros(2, dtype=np.float32), "agent_1": np.zeros(2, dtype=np.float32)}
    for _ in range(check_index * driver.K0):
        raw_env.step(zero_action)
    slow, fast = raw_env._targets()
    wrapper.close()
    return {"slow": [float(x) for x in slow], "fast": [float(x) for x in fast]}


def test_target_vectors_match_independent_recomputation_and_ending_fields_are_legal():
    config = _config()
    result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=1, n_select=1, n_eval=1, load_checkpoint=False,
    )
    assert driver.TRACE_SCHEMA_VERSION == "vk0-trace-2"

    for row in result.check_rows:
        assert row["trace_schema_version"] == "vk0-trace-2"
        assert set(row["current_targets"]) == {"slow", "fast"}
        assert row["incumbent_end_authority_at_check"] in driver.INCUMBENT_END_AUTHORITIES
        assert row["post_window_end_authority"] in driver.POST_WINDOW_END_AUTHORITIES
        assert row["segment_origin"] in driver.SEGMENT_ORIGINS

    rows_by_check = {row["check_index"]: row for row in result.check_rows if row["focal_agent"] == 0}

    # (i) one fast flip: fast_block = step // k0 = check_index on this clock,
    # so fast flips between EVERY consecutive pair of checks -- check 1 vs
    # its previous (check 0, whose own row is excluded from output but whose
    # targets still exist and are what `previous_targets` must carry).
    row1 = rows_by_check[1]
    expected_current_1 = _independent_targets(config, row1["episode_id"], 1)
    expected_previous_1 = _independent_targets(config, row1["episode_id"], 0)
    assert row1["current_targets"] == expected_current_1
    assert row1["previous_targets"] == expected_previous_1
    assert expected_current_1["fast"][1] == pytest.approx(-expected_previous_1["fast"][1])
    assert expected_current_1["slow"][0] == pytest.approx(expected_previous_1["slow"][0])

    # (ii) the joint check (oracle.JOINT_CHECK_INDEX=6, step 30): slow AND
    # fast both flip -- the only point in this 8-check clock where the slow
    # block itself increments.
    joint_index = oracle.JOINT_CHECK_INDEX
    row_joint = rows_by_check[joint_index]
    expected_current_joint = _independent_targets(config, row_joint["episode_id"], joint_index)
    expected_previous_joint = _independent_targets(config, row_joint["episode_id"], joint_index - 1)
    assert row_joint["current_targets"] == expected_current_joint
    assert row_joint["previous_targets"] == expected_previous_joint
    assert expected_current_joint["slow"][0] == pytest.approx(-expected_previous_joint["slow"][0])
    assert expected_current_joint["fast"][1] == pytest.approx(-expected_previous_joint["fast"][1])


# =============================================================================
# (6) Pro-named witness (`21_PRO_OPEN_RAW.md` section 5): a final-check
#     voluntary SET row carries BOTH `incumbent_end_authority_at_check=
#     voluntary_set` and `post_window_end_authority=episode_termination` --
#     the exact case one scalar field could not represent. Driven via the
#     natural-pass forced-token test hook rather than left to an untrained
#     policy's stochastic output.
# =============================================================================


def test_final_check_voluntary_set_carries_both_ending_authorities():
    config = _config()
    forced = {driver.NONINITIAL_CHECKS: {0: (driver.SET_TOKEN, driver.INVALID_SKILL)}}
    result = driver.evaluate_checkpoint(
        entry=_fake_entry(), config=config, episodes=1, n_select=1, n_eval=1,
        load_checkpoint=False, forced_tokens_by_check=forced,
    )
    final_rows = [
        row for row in result.check_rows
        if row["check_index"] == driver.NONINITIAL_CHECKS and row["focal_agent"] == 0
    ]
    assert len(final_rows) == 1, final_rows
    row = final_rows[0]
    assert row["natural_token_kind"] == driver.NATURAL_TOKEN_SET
    assert row["incumbent_end_authority_at_check"] == "voluntary_set"
    assert row["post_window_end_authority"] == "episode_termination"


# =============================================================================
# (7) A-W6-5 exposure-block propagation: verbatim copy plus the driver's own
#     recomputed source-manifest hash; tampered hash or missing block refuses
#     the seed before evaluation. Paired negative/positive, watched red.
# =============================================================================


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_exposure_block_propagation_refuses_tampered_or_missing_and_passes_when_valid():
    scratch = _fresh_scratch_dir("exposure")

    checkpoint_path = scratch / "checkpoint.pt"
    checkpoint_path.write_bytes(b"fake-checkpoint-bytes-for-this-test-only")
    checkpoint_sha256 = driver.hash_bytes(checkpoint_path.read_bytes())

    run_manifest_path = scratch / "run_manifest.json"
    actual_exposure = {
        "actual_exposure_schema": driver.ACTUAL_EXPOSURE_SCHEMA,
        "environment_interactions": {"value": 640000, "source": "runtime_counter"},
        "completed_outer_updates": {"value": 1000, "source": "runtime_counter"},
        "high_optimizer_steps_shared": {"value": 3000, "source": "optimizer_state"},
    }
    _write_json(run_manifest_path, {"actual_exposure": actual_exposure})
    run_manifest_sha256 = driver.hash_bytes(run_manifest_path.read_bytes())

    preflight_manifest_path = scratch / "vk0b_preflight_manifest.json"

    def _write_preflight(*, run_manifest_sha256_value: str) -> None:
        _write_json(
            preflight_manifest_path,
            {
                "nonscientific": False,
                "resolved": {
                    "training_seed": 2026080101,
                    "low_optimizer_absence": {
                        "use_recurrent_low_level": False,
                        "r39_toy_fixed_skill_primitives": True,
                    },
                },
                "resolved_config_hash": "c" * 64,
                "training": {
                    "final_checkpoint_path": str(checkpoint_path),
                    "checkpoint_sha256": checkpoint_sha256,
                    "run_manifest_path": str(run_manifest_path),
                    "run_manifest_sha256": run_manifest_sha256_value,
                },
            },
        )

    # (i) tampered/mismatched source_run_manifest_sha256 -> refused.
    _write_preflight(run_manifest_sha256_value="0" * 64)
    with pytest.raises(driver.Vk0bRefusalError, match="RUN_MANIFEST_HASH_MISMATCH"):
        driver.resolve_checkpoint_entry(str(preflight_manifest_path))

    # Restore the correct hash -> green, and the block/hash are propagated
    # into the resolved entry verbatim.
    _write_preflight(run_manifest_sha256_value=run_manifest_sha256)
    entry = driver.resolve_checkpoint_entry(str(preflight_manifest_path))
    assert entry["source_run_manifest_sha256"] == run_manifest_sha256
    assert entry["actual_exposure"] == actual_exposure

    # (ii) missing actual_exposure block -> refused, even with a correctly
    # matching hash (the hash check alone cannot catch a well-formed but
    # incomplete run_manifest.json).
    _write_json(run_manifest_path, {})
    _write_preflight(run_manifest_sha256_value=driver.hash_bytes(run_manifest_path.read_bytes()))
    with pytest.raises(driver.Vk0bRefusalError, match="ACTUAL_EXPOSURE_BLOCK_MISSING_OR_WRONG_SCHEMA"):
        driver.resolve_checkpoint_entry(str(preflight_manifest_path))

    # Restore the real run_manifest.json -> green again.
    _write_json(run_manifest_path, {"actual_exposure": actual_exposure})
    _write_preflight(run_manifest_sha256_value=driver.hash_bytes(run_manifest_path.read_bytes()))
    entry2 = driver.resolve_checkpoint_entry(str(preflight_manifest_path))
    assert entry2["actual_exposure"]["actual_exposure_schema"] == driver.ACTUAL_EXPOSURE_SCHEMA
