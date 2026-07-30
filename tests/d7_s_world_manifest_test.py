"""A replayed world must be the registered world, checked and not intended.

`scripts/d7_s_world_manifest.py` is the selected repair family (Route A). The
property it must have is narrow and absolute: after `apply_world_manifest`, the
environment holds exactly the bytes the manifest recorded AND the state derived
from them, or the episode fails closed.

THE FAILURE MODE THESE TESTS ARE TUNED TO. The two cloud runs differed from each
other in the LAST BITS of `user_positions` -- not by a visible amount. A digest
gate that catches gross corruption but not a one-ULP change would pass the actual
defect while looking like coverage, which is why the paired negatives below
perturb by `np.nextafter` rather than by something obvious.

SCHEMA 2 ADDS FIVE MORE PAIRED NEGATIVES, one per blocker the round-2 ruling
found. Each of them describes a manifest that verifies perfectly against ITSELF
and is still not the registered world -- which is the whole family of defect this
module exists to exclude, and which schema 1 admitted five ways.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import d7_s_world_manifest as wm  # noqa: E402
import audit_d7_s_event_aligned as audit  # noqa: E402


class _Env:
    """The caller-visible surface the manifest reads and writes.

    Carries all nine components, because schema 2 refuses a partial world. It is
    a double for the mechanics only -- the closure and rebuild-list tests below
    run against the REAL env class, since a double cannot tell you what the real
    generator calls.
    """

    n_users = 3
    n_clusters = 2
    cluster_std = 110.0
    user_distribution = "forced_relay_cluster"
    user_movement_model = "rpgm"
    area_size = 8000.0

    def __init__(self, *, pinned="topo-hash"):
        self.pinned_coordinate_hash = pinned
        self.np_random = np.random.RandomState(7)
        self.user_positions = np.arange(9, dtype=np.float64).reshape(3, 3)
        self.user_velocities = np.full((3, 3), 0.25, dtype=np.float64)
        self.user_waypoints = np.full((3, 2), 11.5, dtype=np.float64)
        self.user_pause_times = np.zeros(3, dtype=np.float64)
        self.user_cluster_assignments = np.array([0, 1, 1], dtype=np.int64)
        self.cluster_centers_history = np.array([[1.0, 2.0], [3.0, 4.0]])
        self.cluster_velocities = np.full((2, 2), 0.5, dtype=np.float64)
        self.cluster_waypoints = np.array([[5.0, 6.0], [7.0, 8.0]])
        self.cluster_pause_times = np.zeros(2, dtype=np.float64)
        self.rebuilt = []

    # A generator surface with the same SHAPE as the real one -- entry points that
    # reach a helper and read configuration off self. Without it the closure is
    # empty, `generator_version` covers nothing, and every test below would be
    # exercising a version hash that cannot move.
    def _generate_user_positions(self):
        return np.zeros((self.n_users, 3), dtype=np.float64)

    def _init_user_velocities(self):
        self.user_velocities = np.zeros((self.n_users, 3), dtype=np.float64)

    def _initialize_user_waypoints_rpgm(self):
        self._generate_intra_cluster_waypoint()

    def _generate_intra_cluster_waypoint(self):
        return self.cluster_std * self.area_size / max(self.n_clusters, 1)

    def regenerate_user_world(self, *, user_world_seed):
        self._generate_user_positions()
        self._init_user_velocities()
        self._initialize_user_waypoints_rpgm()
        self._reset_connection_baseline()
        self._update_channel_state()
        self._update_uav_connections()
        self._compute_routing_paths()

    # the four calls `regenerate_user_world` makes after replacing the world
    def _reset_connection_baseline(self):
        self.rebuilt.append("_reset_connection_baseline")

    def _update_channel_state(self):
        self.rebuilt.append("_update_channel_state")

    def _update_uav_connections(self):
        self.rebuilt.append("_update_uav_connections")

    def _compute_routing_paths(self):
        self.rebuilt.append("_compute_routing_paths")


def _capture(env, **over):
    kwargs = dict(contract_id="NS", topology_seed=20260734, block="audit",
                  episode_index=0, user_world_seed=12345)
    kwargs.update(over)
    return wm.world_manifest_from_env(env, **kwargs)


def _expected(env, manifest=None, **over):
    """The identity a caller asserts INDEPENDENTLY of the stored sidecar."""
    kwargs = dict(contract_id="NS", topology_seed=20260734, block="audit",
                  episode_index=0, pinned_coordinate_hash=env.pinned_coordinate_hash,
                  user_world_seed=12345,
                  generator_version_hash=(manifest["identity"]["generator_version"]
                                          if manifest else wm.generator_version(env)),
                  n_users=env.n_users, n_clusters=env.n_clusters)
    kwargs.update(over)
    return wm.expected_identity(**kwargs)


# ------------------------------------------------------------- capture -------

def test_capture_records_every_component_its_digest_shape_and_dtype() -> None:
    manifest = _capture(_Env())
    assert set(manifest["arrays"]) == set(audit.WORLD_COMPONENT_ORDER)
    assert set(manifest["component_digests"]) == set(audit.WORLD_COMPONENT_ORDER)
    assert manifest["component_shapes"]["user_positions"] == [3, 3]
    assert manifest["component_dtypes"]["user_cluster_assignments"] == np.dtype(np.int64).str
    assert manifest["identity"]["user_world_seed"] == 12345
    assert len(manifest["identity"]["generator_version"]) == 64
    assert len(manifest["payload_hash"]) == 64


def test_capture_refuses_an_unpinned_topology() -> None:
    """The world is a function of the BS layout as well as the seed, so a manifest
    from an unpinned env would record a world its key cannot describe."""

    with pytest.raises(wm.WorldManifestError) as excinfo:
        _capture(_Env(pinned=None))
    assert excinfo.value.reason == "TOPOLOGY_NOT_PINNED"


def test_capture_refuses_a_partial_world() -> None:
    """B2's PAIRED NEGATIVE. Schema 1 skipped an absent component, and the digest
    check then compared the short array set against the short digest set and found
    them consistent. A manifest missing one of the nine passed every check."""

    env = _Env()
    env.cluster_waypoints = None
    with pytest.raises(wm.WorldManifestError) as excinfo:
        _capture(env)
    assert excinfo.value.reason == "COMPONENT_ABSENT"
    assert "cluster_waypoints" in str(excinfo.value)


def test_a_self_consistent_partial_manifest_is_still_refused() -> None:
    """The sharper half of B2: consistency between the two sets proves nothing."""

    manifest = _capture(_Env())
    del manifest["arrays"]["cluster_pause_times"]
    del manifest["component_digests"]["cluster_pause_times"]
    # internally consistent -- and not the world
    assert set(manifest["arrays"]) == set(manifest["component_digests"])
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_digests(manifest)
    assert excinfo.value.reason == "COMPONENT_SET_INCOMPLETE"


def test_digests_match_the_fingerprint_encoding_exactly() -> None:
    """The manifest's per-component digests must be comparable against an
    artifact's `component_digests`. Any encoding difference would make them
    silently incomparable."""

    env = _Env()
    manifest = _capture(env)
    from_artifact = audit.episode_world_fingerprint(env, seed_value=12345)
    for name, digest in manifest["component_digests"].items():
        assert digest == from_artifact["component_digests"][name], name


# ------------------------------------------------------- store and reload ----

def test_round_trip_is_bit_exact(tmp_path) -> None:
    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    loaded = wm.load_world_manifest(str(tmp_path), expected=_expected(env, manifest))
    for name, arr in manifest["arrays"].items():
        assert loaded["arrays"][name].tobytes() == arr.tobytes(), name
    assert loaded["component_digests"] == manifest["component_digests"]
    assert loaded["payload_hash"] == manifest["payload_hash"]


def test_a_one_ulp_corruption_is_refused(tmp_path) -> None:
    """THE PAIRED NEGATIVE THAT MATTERS. One ULP, because that is the real defect.

    A gate that only catches visible corruption would have passed the very
    divergence that blocked the R4 claim.
    """

    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)

    target = tmp_path / "NS" / "20260734" / "audit" / "0"
    with np.load(target / "world.npz", allow_pickle=False) as handle:
        arrays = {k: handle[k].copy() for k in handle.files}
    arrays["user_positions"][0, 0] = np.nextafter(arrays["user_positions"][0, 0], np.inf)
    np.savez(target / "world.npz", **arrays)

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=_expected(env, manifest))
    assert excinfo.value.reason == "COMPONENT_DIGEST_MISMATCH"
    assert "user_positions" in str(excinfo.value)


def test_a_missing_manifest_is_refused_not_regenerated(tmp_path) -> None:
    """Silently generating a world when replay is in force is the defect wearing a
    different hat."""

    env = _Env()
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=_expected(env, topology_seed=1))
    assert excinfo.value.reason == "MANIFEST_ABSENT"


def test_a_schema_bump_invalidates_old_bytes(tmp_path) -> None:
    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    sidecar = tmp_path / "NS" / "20260734" / "audit" / "0" / "identity.json"
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    meta["identity"]["schema_version"] = wm.SCHEMA_VERSION + 1
    sidecar.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=_expected(env, manifest))
    assert excinfo.value.reason == "SCHEMA_MISMATCH"


# --------------------------------------------------------------- B1 ----------

def test_a_manifest_moved_into_a_plausible_directory_is_refused(tmp_path) -> None:
    """B1's PAIRED NEGATIVE, and the one that reads most like a real accident.

    A manifest for episode 0 is copied into episode 1's directory. Its arrays,
    digests and payload hash all verify against its own sidecar -- schema 1 checked
    nothing else, so it was accepted as episode 1's registered world.
    """

    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)

    source = tmp_path / "NS" / "20260734" / "audit" / "0"
    destination = tmp_path / "NS" / "20260734" / "audit" / "1"
    destination.mkdir(parents=True)
    for name in ("world.npz", "identity.json"):
        (destination / name).write_bytes((source / name).read_bytes())

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=_expected(env, manifest,
                                                                episode_index=1))
    assert excinfo.value.reason == "IDENTITY_MISMATCH"
    assert "MOVED or COPIED" in str(excinfo.value)


@pytest.mark.parametrize("field,value", [
    ("pinned_coordinate_hash", "a-different-topology"),
    ("user_world_seed", 999),
    ("generator_version_hash", "0" * 64),
    ("n_users", 4),
    ("n_clusters", 3),
])
def test_every_non_path_identity_field_is_compared(tmp_path, field, value) -> None:
    """The four path fields are caught by the test above; these five are the ones
    schema 1 read into a dict and never looked at again."""

    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path),
                               expected=_expected(env, manifest, **{field: value}))
    assert excinfo.value.reason == "IDENTITY_MISMATCH"


def test_an_incomplete_expected_identity_is_refused(tmp_path) -> None:
    """A field the caller may omit is a field nobody checks."""

    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    partial = _expected(env, manifest)
    del partial["pinned_coordinate_hash"]
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=partial)
    assert excinfo.value.reason == "EXPECTED_IDENTITY_INCOMPLETE"


def test_a_dtype_change_is_refused(tmp_path) -> None:
    """Same digits, different world. The digest already catches this because the
    bytes differ, but the dtype check names WHAT changed instead of reporting an
    opaque digest mismatch."""

    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    target = tmp_path / "NS" / "20260734" / "audit" / "0"
    with np.load(target / "world.npz", allow_pickle=False) as handle:
        arrays = {k: handle[k].copy() for k in handle.files}
    arrays["user_pause_times"] = arrays["user_pause_times"].astype(np.float32)
    np.savez(target / "world.npz", **arrays)

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), expected=_expected(env, manifest))
    assert excinfo.value.reason in ("COMPONENT_DIGEST_MISMATCH", "DTYPE_MISMATCH")


# --------------------------------------------------------------- B3 ----------

def test_generator_version_moves_when_a_generator_changes() -> None:
    """A version that cannot change is a version nobody has to maintain and
    everybody can trust wrongly."""

    env = _Env()
    baseline = wm.generator_version(env)
    assert wm.generator_version(_Env()) == baseline, "must be stable for equal envs"

    env.n_users = 4
    assert wm.generator_version(env) != baseline, "shape parameters must be covered"


def test_generator_version_covers_a_parameter_read_only_by_a_helper() -> None:
    """`cluster_std` is read by `_generate_intra_cluster_waypoint`, two calls deep
    and named by no constructor of the double. A hand-listed parameter subset is
    exactly what the ruling called out."""

    env = _Env()
    baseline = wm.generator_version(env)
    env.cluster_std = env.cluster_std + 1.0
    assert wm.generator_version(env) != baseline


def test_an_env_with_no_generators_is_refused_not_versioned() -> None:
    """A version hash over an empty closure is stable across every possible
    generator -- a guard that cannot fail, which is the defect this whole module
    keeps running into."""

    class _Bare:
        n_users = 1

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.generator_version(_Bare())
    assert excinfo.value.reason == "GENERATOR_CLOSURE_EMPTY"


def test_the_generator_closure_reaches_the_trig_helpers_on_the_real_env() -> None:
    """B3's PAIRED NEGATIVE, and it must run against the REAL class.

    Schema 1 hand-listed five functions. The transitive closure is eight, and the
    three it missed are exactly the trigonometric helpers that overwrite
    `user_velocities` -- the array measured to diverge. A double cannot show this;
    only the real generator's call graph can.
    """

    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    closure = set(wm.generator_function_closure(UAVEnergyAwareRelayEnv))

    for name in wm.GENERATOR_SEED_FUNCTIONS:
        assert name in closure, f"{name} is a seed and must be in its own closure"
    for name in ("_initialize_cluster_migration_rpgm",
                 "_generate_intra_cluster_waypoint",
                 "_generate_inter_cluster_waypoint"):
        assert name in closure, (
            f"{name} writes world arrays through np.cos/np.sin and is reachable "
            f"from _initialize_user_waypoints_rpgm. Schema 1 omitted it, which is "
            f"how two different generators could share a version.")
    assert closure - set(wm.GENERATOR_SEED_FUNCTIONS), (
        "the closure equals the hand-listed seeds, so the walk found nothing -- "
        "that is the schema-1 defect reintroduced")


# --------------------------------------------------------------- B4 ----------

def test_apply_installs_the_world_and_reads_it_back() -> None:
    source = _Env()
    manifest = _capture(source)

    target = _Env()
    target.user_positions = np.zeros((3, 3), dtype=np.float64)   # a different world
    assert target.user_positions.tobytes() != manifest["arrays"]["user_positions"].tobytes()

    report = wm.apply_world_manifest(target, manifest)
    assert report["user_world_seed"] == 12345
    assert target.user_world_seed_applied == 12345
    for name, arr in manifest["arrays"].items():
        assert np.asarray(getattr(target, name)).tobytes() == arr.tobytes(), name


def test_apply_rebuilds_the_derived_state_in_order() -> None:
    """B4's POSITIVE. The world was REPLACED, not advanced; without the rebuild the
    next diff compares new serving sets against the DISCARDED world's and books the
    difference as pre-episode handovers the fingerprint then captures."""

    target = _Env()
    report = wm.apply_world_manifest(target, _capture(_Env()))
    assert tuple(target.rebuilt) == wm.DERIVED_STATE_REBUILD
    assert report["derived_state_rebuilt"] == list(wm.DERIVED_STATE_REBUILD)
    assert report["rng_state_unchanged"] is True


def test_apply_refuses_an_env_that_cannot_rebuild_derived_state() -> None:
    """B4's PAIRED NEGATIVE. Applying the arrays alone is the failure that happens
    on the HAPPY path -- correct manifest, correct digests, hybrid environment."""

    class _NoRebuild(_Env):
        _compute_routing_paths = None

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.apply_world_manifest(_NoRebuild(), _capture(_Env()))
    assert excinfo.value.reason == "DERIVED_STATE_METHOD_MISSING"
    assert "_compute_routing_paths" in str(excinfo.value)


def test_apply_refuses_a_rebuild_that_consumes_continuation_randomness() -> None:
    """Replay must not perturb the arm streams, or the manifest changes the
    measurement it exists to fix. Measured: 35 functions are reachable from the
    four rebuild calls on the real class and none touches np_random, so this
    assertion is satisfiable and a future edit that breaks it is a real finding."""

    class _Drawing(_Env):
        def _update_channel_state(self):
            super()._update_channel_state()
            self.np_random.random()

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.apply_world_manifest(_Drawing(), _capture(_Env()))
    assert excinfo.value.reason == "DERIVED_REBUILD_CONSUMED_RANDOMNESS"


def test_the_rebuild_list_matches_what_regenerate_user_world_calls() -> None:
    """The list is a constant, so it can drift from the method it mirrors. This is
    the only check that would notice a FIFTH rebuild step being added."""

    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    assert (wm.derived_state_rebuild_from_source(UAVEnergyAwareRelayEnv)
            == wm.DERIVED_STATE_REBUILD)


def test_apply_refuses_when_assignment_does_not_stick() -> None:
    """The read-back is the point: an env that intercepts assignment would leave
    the episode in a world the manifest does not describe, while the manifest
    itself still verifies."""

    class _Swallowing(_Env):
        @property
        def user_positions(self):
            return getattr(self, "_up", np.zeros((3, 3)))

        @user_positions.setter
        def user_positions(self, value):      # drops the write on the floor
            self._up = np.zeros((3, 3), dtype=np.float64)

    manifest = _capture(_Env())
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.apply_world_manifest(_Swallowing(), manifest)
    assert excinfo.value.reason == "COMPONENT_DIGEST_MISMATCH"


# --------------------------------------------------------------- B5 ----------

def test_save_refuses_to_overwrite_a_different_world(tmp_path) -> None:
    """B5's PAIRED NEGATIVE. Schema 1 used makedirs(exist_ok=True) and np.savez,
    both of which overwrite in silence, leaving no trace that a frozen population
    had been edited."""

    env = _Env()
    wm.save_world_manifest(str(tmp_path), _capture(env))

    other = _Env()
    other.user_positions = other.user_positions + 1.0
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.save_world_manifest(str(tmp_path), _capture(other))
    assert excinfo.value.reason == "MANIFEST_EXISTS"


def test_save_is_idempotent_for_identical_bytes(tmp_path) -> None:
    """Re-writing the same world is idempotence, not mutation, and refusing it
    would make a resumed generation impossible."""

    manifest = _capture(_Env())
    wm.save_world_manifest(str(tmp_path), manifest)
    wm.save_world_manifest(str(tmp_path), manifest)      # must not raise


def _population(tmp_path, keys=((20260734, "audit", 0), (20260734, "audit", 1))):
    manifests = []
    for seed, block, index in keys:
        env = _Env()
        env.user_positions = env.user_positions + float(index) + float(seed % 7)
        manifest = _capture(env, topology_seed=seed, block=block, episode_index=index)
        wm.save_world_manifest(str(tmp_path), manifest)
        manifests.append(manifest)
    return manifests


def test_inventory_freezes_the_set_and_verifies(tmp_path) -> None:
    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)
    report = wm.verify_manifest_inventory(str(tmp_path))
    assert report["episode_count"] == 2
    assert len(report["set_hash"]) == 64


def test_a_deleted_episode_is_caught_by_the_inventory_and_by_nothing_else(tmp_path) -> None:
    """B5's second PAIRED NEGATIVE. Every REMAINING manifest still verifies
    perfectly; only the set hash notices the population shrank."""

    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)

    victim = tmp_path / "NS" / "20260734" / "audit" / "1"
    for name in ("world.npz", "identity.json"):
        (victim / name).unlink()

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "MANIFEST_ABSENT"


def test_an_added_episode_is_caught_by_the_set_hash(tmp_path) -> None:
    """The direction the per-manifest checks structurally cannot see: everything
    the inventory names is present and correct, and the population is still wrong.

    A rebuilt-vs-frozen hash COMPARISON proves nothing about `verify_manifest_
    inventory` itself unless the function is actually called and its refusal
    observed -- comparing two `build_manifest_inventory` outputs never touches the
    disk-walk path at all. This calls the real entry point.
    """

    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)
    assert wm.verify_manifest_inventory(str(tmp_path))["episode_count"] == 2

    _population(tmp_path, keys=((20260734, "audit", 2),))

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "INVENTORY_UNLISTED_MANIFEST"
    assert "2" in str(excinfo.value)


def test_an_unlisted_manifest_on_disk_is_refused(tmp_path) -> None:
    """B5's PAIRED NEGATIVE for the disk walk, kept separate from the test above so
    the walk is exercised at a DIFFERENT topology_seed subtree -- the earlier test
    only adds a sibling episode_index under the same topology directory, which
    would not catch a walk that only looks one directory level too shallow or too
    deep. Per-manifest checks cannot see this at all: nothing here names episode
    99 or asks whether it verifies, so a check that only reloads inventory-named
    entries has no way to notice it exists.
    """

    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)
    _population(tmp_path, keys=((99999, "audit", 0),))

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "INVENTORY_UNLISTED_MANIFEST"
    message = str(excinfo.value)
    # Forward-slash, exactly the extra directory -- and MEASURED to matter: a
    # walk that emits raw os.path.relpath (backslash on Windows) would compare
    # unequal to every forward-slash `relative_dir` the inventory names, so it
    # would report the two ALREADY-LISTED directories as unlisted too. A bare
    # `"99999" in message` substring check does not notice that failure mode --
    # it stays true either way -- so this asserts the legitimate entries are
    # named nowhere in the refusal.
    assert "99999/audit/0" in message
    assert "20260734/audit/0" not in message
    assert "20260734/audit/1" not in message


def test_a_consistent_metadata_tamper_is_caught_by_the_full_entry_set_hash(tmp_path) -> None:
    """B5's PAIRED NEGATIVE for entry completeness, and the one that actually
    isolates it. Editing the disk sidecar's identity ALONE is already caught by
    `_compare_identity` regardless of the set-hash formula, so that would not
    distinguish the fix. This edits `n_clusters` in BOTH the disk sidecar and the
    inventory's own recorded entry, consistently -- so the per-manifest identity
    check (which compares disk against the entry's OWN identity) cannot see
    anything wrong, and `payload_hash` is untouched since no array byte changed.
    The old formula hashed only `relative_dir=payload_hash`, so this tamper would
    not move it. Only a set hash that also covers the entry's identity notices
    the recorded population moved, because the stored `set_hash` was computed
    BEFORE the tamper and nothing here recomputes it to match.
    """

    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)

    sidecar_path = tmp_path / "NS" / "20260734" / "audit" / "0" / "identity.json"
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    sidecar["identity"]["n_clusters"] = 999
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

    inventory_path = tmp_path / wm.INVENTORY_FILE
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["entries"][0]["identity"]["n_clusters"] = 999
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "INVENTORY_SET_HASH_MISMATCH"


def test_a_replaced_world_is_caught_even_though_it_verifies(tmp_path) -> None:
    """The sharpest of the inventory negatives: the manifest on disk is internally
    perfect and is a DIFFERENT world."""

    manifests = _population(tmp_path)
    wm.write_manifest_inventory(str(tmp_path), manifests)

    env = _Env()
    env.user_positions = env.user_positions + 100.0
    replacement = _capture(env, topology_seed=20260734, block="audit", episode_index=1)
    wm.save_world_manifest(str(tmp_path), replacement, allow_overwrite=True)

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "INVENTORY_PAYLOAD_MISMATCH"


def test_a_duplicated_episode_key_is_refused() -> None:
    manifest = _capture(_Env())
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.build_manifest_inventory([manifest, manifest])
    assert excinfo.value.reason == "DUPLICATE_EPISODE_KEY"


def test_a_missing_inventory_is_not_a_pass(tmp_path) -> None:
    _population(tmp_path)
    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.verify_manifest_inventory(str(tmp_path))
    assert excinfo.value.reason == "INVENTORY_ABSENT"


# --------------------------------------------------------------- wiring ------

def test_it_is_not_wired_into_the_audit_path_yet() -> None:
    """Integration must not precede the manifest-REPLAY gate. The round-2 ruling
    holds it explicitly. This test is the reminder, and it should be DELETED in the
    same change that wires it in."""

    source = (ROOT / "scripts" / "audit_d7_s_event_aligned.py").read_text(encoding="utf-8")
    assert "d7_s_world_manifest" not in source, (
        "the manifest is now referenced by the audit; if that is intentional, the "
        "manifest-replay conformance gate must have passed and this test must be "
        "removed deliberately rather than edited into passing")
