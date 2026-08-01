"""Focused calibration tests for the B3-L touchpoint-2 realization additions
to scripts/audit_d7_s_event_aligned.py.

Frozen contract: docs/research/designs/D7_S_B3L_DECISION_LEDGER.md (D1, D3,
D5, D8, and the frozen amendments A-D1/A-D3/A-D5/A-D7 from the conformance
ruling `docs/external-review/rounds/20260801_d7_s_b3l_design_conformance/
21_PRO_OPEN_RAW.md`).

Every real environment here is built through the audit script's own
`build_topology_template`/`build_pinned_env` on `TOPOLOGY_SEED_DEV`, the same
construction `tests/scenario7_canonical_initialization_test.py` uses -- no
doubles, since several of these functions (`finalize_preaction_state`,
`component_dtypes`, the trajectory collector) exist specifically to describe
real environment state.
"""
import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
pytest.importorskip("gymnasium")

import audit_d7_s_event_aligned as audit  # noqa: E402

# Development topology only -- an R4 seed must never be constructed at
# design/test time (R1 discipline; see the B3-L ledger's "Deliberately not
# done" section).
TOPOLOGY_SEED = audit.TOPOLOGY_SEED_DEV
EPISODE_SEED = 1001
ENERGY_SEED = 2002
USER_WORLD_SEED = 3003
ENERGY_STAGE = "S3"

CLASS_TEST_PATH_SET = (
    "scripts/audit_d7_s_event_aligned.py",
    "envs/pettingzoo/__init__.py",
)


@pytest.fixture(scope="module")
def topology():
    """The recorded topology template. Read-only, so one build serves the file."""
    assert TOPOLOGY_SEED not in set(audit.TOPOLOGY_SEEDS_R4)
    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(
        config, topology_seed=TOPOLOGY_SEED, energy_stage=ENERGY_STAGE)
    return config, coords, coord_hash


@pytest.fixture
def dev_env(topology):
    """One freshly pinned dev env per test -- several tests mutate it."""
    config, coords, coord_hash = topology
    return audit.build_pinned_env(
        config, episode_seed=EPISODE_SEED, coords=coords, coord_hash=coord_hash,
        energy_stage=ENERGY_STAGE, user_world_seed=USER_WORLD_SEED)


def _set_registered_launch_env(monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", str(audit.REGISTERED_PYTHONHASHSEED))
    for key, value in audit.REGISTERED_THREAD_VARS.items():
        monkeypatch.setenv(key, value)


# =============================================================================
# source_code_id
# =============================================================================

def test_source_code_id_is_deterministic_across_two_calls(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("alpha\n", encoding="utf-8")
    f2.write_text("beta\n", encoding="utf-8")
    path_set = (str(f1), str(f2))

    sid_a = audit.source_code_id(tmp_path, path_set=path_set)
    sid_b = audit.source_code_id(tmp_path, path_set=path_set)

    assert sid_a == sid_b
    assert len(sid_a) == 64  # hex SHA-256


def test_source_code_id_changes_when_frozen_content_changes(tmp_path):
    """Paired negative for determinism: `git hash-object` (verified to work on
    an arbitrary path outside any repository -- see the implementer's report)
    lets this run entirely inside `tmp_path`, so no repository file is ever
    mutated. Mutating one file's content must move the id; if it didn't, the
    id would be a function of the path set alone, not of content, and could
    never invalidate a certificate after a real code edit."""
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("alpha\n", encoding="utf-8")
    f2.write_text("beta\n", encoding="utf-8")
    path_set = (str(f1), str(f2))

    before = audit.source_code_id(tmp_path, path_set=path_set)
    f1.write_text("alpha-mutated\n", encoding="utf-8")
    after = audit.source_code_id(tmp_path, path_set=path_set)

    assert before != after

    # And reverting reproduces the original id -- content-addressed, not a
    # one-way ratchet.
    f1.write_text("alpha\n", encoding="utf-8")
    restored = audit.source_code_id(tmp_path, path_set=path_set)
    assert restored == before


def test_source_code_id_missing_path_is_a_named_hard_error(tmp_path):
    f1 = tmp_path / "a.py"
    f1.write_text("alpha\n", encoding="utf-8")
    missing = tmp_path / "does_not_exist.py"

    with pytest.raises(FileNotFoundError, match="does_not_exist.py"):
        audit.source_code_id(tmp_path, path_set=(str(f1), str(missing)))


def test_source_code_id_default_path_set_reports_the_not_yet_created_scripts():
    """At this HEAD, two of the frozen paths (`d7_s_local_replay_gate.py`,
    `d7_s_successor_input_inventory.py`) are future work and do not exist --
    the ledger names this as the expected error branch, not a defect."""
    with pytest.raises(FileNotFoundError, match="d7_s_local_replay_gate.py"):
        audit.source_code_id(audit.PROJECT_ROOT)


# =============================================================================
# verify_registered_launch_env
# =============================================================================

def test_verify_registered_launch_env_returns_verified_values(monkeypatch):
    _set_registered_launch_env(monkeypatch)

    result = audit.verify_registered_launch_env()

    assert result["PYTHONHASHSEED"] == str(audit.REGISTERED_PYTHONHASHSEED)
    for key, value in audit.REGISTERED_THREAD_VARS.items():
        assert result[key] == value


def test_verify_registered_launch_env_raises_naming_the_wrong_variable(monkeypatch):
    """Paired negative: one variable set wrong must raise, and the message
    must name that exact variable rather than a generic failure."""
    _set_registered_launch_env(monkeypatch)
    monkeypatch.setenv("MKL_NUM_THREADS", "4")

    with pytest.raises(RuntimeError, match="MKL_NUM_THREADS"):
        audit.verify_registered_launch_env()


def test_verify_registered_launch_env_raises_naming_a_missing_variable(monkeypatch):
    _set_registered_launch_env(monkeypatch)
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)

    with pytest.raises(RuntimeError, match="PYTHONHASHSEED"):
        audit.verify_registered_launch_env()


# =============================================================================
# certified_local_execution_class
# =============================================================================

def test_certified_local_execution_class_returns_all_named_fields(monkeypatch):
    _set_registered_launch_env(monkeypatch)

    record = audit.certified_local_execution_class(
        worker_count=4, start_method="spawn", role="parent",
        config={"preset": "S7-S3"}, path_set=CLASS_TEST_PATH_SET)

    required = (
        "node", "os_platform", "machine", "python_version", "numpy_version",
        "scipy_version", "numpy_blas", "cpu_features", "worker_count",
        "process_start_method", "pythonhashseed", "thread_vars", "role",
        "source_code_id", "configuration_digest",
        "fingerprint_algorithm_version", "provenance_contract_version",
        "class_id",
    )
    for key in required:
        assert key in record, f"missing field {key}"
    assert set(record["thread_vars"]) == set(audit.REGISTERED_THREAD_VARS)
    assert record["fingerprint_algorithm_version"] == audit.FINGERPRINT_ALGORITHM_VERSION
    assert record["provenance_contract_version"] == audit.PROVENANCE_CONTRACT_VERSION
    assert record["worker_count"] == 4
    assert record["process_start_method"] == "spawn"
    assert record["role"] == "parent"


def test_certified_local_execution_class_id_stable_across_two_calls(monkeypatch):
    _set_registered_launch_env(monkeypatch)
    kwargs = dict(worker_count=4, start_method="spawn", role="parent",
                  config={"preset": "S7-S3"}, path_set=CLASS_TEST_PATH_SET)

    first = audit.certified_local_execution_class(**kwargs)
    second = audit.certified_local_execution_class(**kwargs)

    assert first["class_id"] == second["class_id"]


def test_certified_local_execution_class_id_differs_with_worker_count(monkeypatch):
    """Paired negative for stability: only `worker_count` changes."""
    _set_registered_launch_env(monkeypatch)
    common = dict(start_method="spawn", role="parent",
                  config={"preset": "S7-S3"}, path_set=CLASS_TEST_PATH_SET)

    four = audit.certified_local_execution_class(worker_count=4, **common)
    two = audit.certified_local_execution_class(worker_count=2, **common)

    assert four["class_id"] != two["class_id"]


def test_certified_local_execution_class_raises_without_registered_env(monkeypatch):
    """STRICT per D3: a lookup failure (here, the launch-env verification)
    must raise rather than degrade to a partial record, unlike `runtime_identity`."""
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)
    for key in audit.REGISTERED_THREAD_VARS:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError):
        audit.certified_local_execution_class(
            worker_count=4, start_method="spawn", role="parent",
            config={}, path_set=CLASS_TEST_PATH_SET)


# =============================================================================
# finalize_preaction_state
# =============================================================================

def test_finalize_preaction_state_returns_fingerprint_and_rng_token(dev_env):
    energies = audit.draw_energy_permutation(energy_seed=ENERGY_SEED)
    audit.apply_energy_profile(dev_env, energies)

    result = audit.finalize_preaction_state(dev_env)

    assert result["observations_materialized"] is True
    assert isinstance(result["preaction_fingerprint"], str) and result["preaction_fingerprint"]
    assert isinstance(result["rng_token"], str) and result["rng_token"]
    # Matches what a direct call to the (unmodified) barrier plus the audit's
    # own fingerprint/RNG readers would independently compute -- proving this
    # wraps the real barrier rather than a private recomputation.
    assert result["preaction_fingerprint"] == audit.full_state_fingerprint(dev_env)
    assert result["rng_token"] == audit._rng_state_token(dev_env)


def test_finalize_preaction_state_is_idempotent(dev_env):
    """A-D1 postcondition carried through: calling it twice must reproduce
    the identical fingerprint, since the barrier itself is idempotent and
    randomness-free (established directly against the real barrier by
    tests/scenario7_canonical_initialization_test.py)."""
    energies = audit.draw_energy_permutation(energy_seed=ENERGY_SEED)
    audit.apply_energy_profile(dev_env, energies)

    first = audit.finalize_preaction_state(dev_env)
    second = audit.finalize_preaction_state(dev_env)

    assert first["preaction_fingerprint"] == second["preaction_fingerprint"]
    assert first["rng_token"] == second["rng_token"]


# =============================================================================
# component_dtypes (D7/A-D7)
# =============================================================================

def test_episode_world_fingerprint_carries_the_complete_dtype_map(dev_env):
    world = audit.episode_world_fingerprint(dev_env, seed_value=USER_WORLD_SEED)

    dtypes = world["component_dtypes"]
    assert set(dtypes.keys()) == set(audit.WORLD_COMPONENT_ORDER)
    assert "user_cluster_assignments" in dtypes
    # The sibling task owns the dtype PIN itself (D7's np.int32 binding);
    # this only asserts the map matches whatever the live env actually
    # carries, never a literal '<i4'.
    assert dtypes["user_cluster_assignments"] == dev_env.user_cluster_assignments.dtype.str

    # The digest itself must stay unaffected by adding this field -- it was
    # computed from exactly the same bytes before and after this change.
    assert world["component_digests"]["user_cluster_assignments"] == audit.hashlib.sha256(
        b"user_cluster_assignments" +
        str(dev_env.user_cluster_assignments.shape).encode("utf-8") +
        np.ascontiguousarray(dev_env.user_cluster_assignments).tobytes()
    ).hexdigest()


# =============================================================================
# TrajectoryDigestCollector (D5/A-D5)
# =============================================================================

def test_trajectory_digest_collector_replay_equal_and_mutation_negative(dev_env):
    """Two identical replays: recording on the SAME unstepped env twice must
    produce identical digests (driving real env steps for this is not
    proof-sized -- the encoding correctness this collector exists to prove is
    orthogonal to whether the env was stepped).

    The watched-red paired negative: mutate one world array in place and
    require the digest to move, then restore and require it to return."""
    collector = audit.TrajectoryDigestCollector()

    first = collector.record(dev_env, 0)
    second = collector.record(dev_env, 0)
    assert first == second

    name = "user_positions"
    original = np.array(getattr(dev_env, name), copy=True)
    mutated = original.copy()
    mutated[0, 0] = mutated[0, 0] + 1000.0
    setattr(dev_env, name, mutated)
    try:
        mutated_digest = collector.record(dev_env, 0)
        assert mutated_digest != first, (
            "mutating a WORLD_COMPONENT_ORDER array in place did not move the "
            "trajectory digest -- the collector is not actually reading live "
            "component bytes")
    finally:
        setattr(dev_env, name, original)

    restored_digest = collector.record(dev_env, 0)
    assert restored_digest == first


def test_trajectory_digest_collector_step_index_is_load_bearing(dev_env):
    """A different step index over the identical env state must produce a
    different digest -- the step index is hashed, not merely accepted and
    discarded."""
    collector = audit.TrajectoryDigestCollector()
    d_step_0 = collector.record(dev_env, 0)
    d_step_1 = collector.record(dev_env, 1)
    assert d_step_0 != d_step_1


def test_trajectory_digest_collector_appends_every_record(dev_env):
    collector = audit.TrajectoryDigestCollector()
    collector.record(dev_env, 0)
    collector.record(dev_env, 1)
    assert collector.digests == [collector.digests[0], collector.digests[1]]
    assert len(collector.digests) == 2


# =============================================================================
# Spawn context (D3.2/A-D3(2), D8's mp_context binding)
# =============================================================================

def test_run_indexed_in_pool_source_passes_spawn_mp_context():
    """Structural assertion: the pool creation call must pass an explicit
    spawn context rather than recording "spawn" while relying on the
    platform default."""
    source = inspect.getsource(audit._run_indexed_in_pool)
    assert 'mp_context=multiprocessing.get_context("spawn")' in source
    assert "ProcessPoolExecutor(" in source


def _cheap_picklable_worker(*, idx: int, offset: int) -> int:
    """Module-level (not a closure/lambda) so a real spawned child process
    can import and locate it by reference -- the same constraint a real pool
    worker is under."""
    return idx + offset


def test_run_indexed_in_pool_two_workers_returns_index_ordered_results():
    """A real, small `ProcessPoolExecutor(workers=2)` run through the actual
    `_run_indexed_in_pool` seam -- not a fake -- proving a genuine spawn pool
    both starts and folds results back keyed by index regardless of
    completion order."""
    indices = [0, 1, 2, 3]
    results = audit._run_indexed_in_pool(
        _cheap_picklable_worker, indices, workers=2, offset=100)

    assert results == {0: 100, 1: 101, 2: 102, 3: 103}
