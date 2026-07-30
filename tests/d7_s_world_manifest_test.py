"""A replayed world must be the registered world, checked and not intended.

`scripts/d7_s_world_manifest.py` is step 3 of the provenance correction ruled on
2026-07-30 and the selected repair family. The property it must have is narrow and
absolute: after `apply_world_manifest`, the environment holds exactly the bytes the
manifest recorded, or the episode fails closed.

THE FAILURE MODE THESE TESTS ARE TUNED TO. The two cloud runs differed from each
other in the LAST BITS of `user_positions` -- not by a visible amount. A digest
gate that catches gross corruption but not a one-ULP change would pass the actual
defect while looking like coverage, which is why the paired negatives below perturb
by `np.nextafter` rather than by something obvious.
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
    """The caller-visible surface the manifest reads and writes."""

    n_users = 3
    n_clusters = 2
    cluster_std = 110.0
    user_distribution = "forced_relay_cluster"
    user_movement_model = "rpgm"
    area_size = 8000.0

    def __init__(self, *, pinned="topo-hash"):
        self.pinned_coordinate_hash = pinned
        self.user_positions = np.arange(9, dtype=np.float64).reshape(3, 3)
        self.user_velocities = np.full((3, 3), 0.25, dtype=np.float64)
        self.cluster_centers_history = np.array([[1.0, 2.0], [3.0, 4.0]])
        self.user_pause_times = np.zeros(3, dtype=np.float64)


def _capture(env, **over):
    kwargs = dict(contract_id="NS", topology_seed=20260734, block="audit",
                  episode_index=0, user_world_seed=12345)
    kwargs.update(over)
    return wm.world_manifest_from_env(env, **kwargs)


def test_capture_records_every_exposed_component_and_its_digest() -> None:
    manifest = _capture(_Env())
    assert set(manifest["arrays"]) == set(manifest["component_digests"])
    assert "user_positions" in manifest["arrays"]
    # absent components are skipped, not zero-filled -- a zero-filled absent
    # component would be indistinguishable from a real all-zero array
    assert "cluster_waypoints" not in manifest["arrays"]
    assert manifest["identity"]["user_world_seed"] == 12345
    assert len(manifest["identity"]["generator_version"]) == 64


def test_capture_refuses_an_unpinned_topology() -> None:
    """The world is a function of the BS layout as well as the seed, so a manifest
    from an unpinned env would record a world its key cannot describe."""

    with pytest.raises(wm.WorldManifestError) as excinfo:
        _capture(_Env(pinned=None))
    assert excinfo.value.reason == "TOPOLOGY_NOT_PINNED"


def test_digests_match_the_fingerprint_encoding_exactly() -> None:
    """The manifest's per-component digests must be comparable against an
    artifact's `component_digests`, which is how the step 4 gate will work. Any
    encoding difference would make them silently incomparable."""

    env = _Env()
    manifest = _capture(env)
    from_artifact = audit.episode_world_fingerprint(env, seed_value=12345)
    for name, digest in manifest["component_digests"].items():
        assert digest == from_artifact["component_digests"][name], name


def test_round_trip_is_bit_exact(tmp_path) -> None:
    env = _Env()
    manifest = _capture(env)
    wm.save_world_manifest(str(tmp_path), manifest)
    loaded = wm.load_world_manifest(str(tmp_path), contract_id="NS",
                                    topology_seed=20260734, block="audit",
                                    episode_index=0)
    for name, arr in manifest["arrays"].items():
        assert loaded["arrays"][name].tobytes() == arr.tobytes(), name
    assert loaded["component_digests"] == manifest["component_digests"]


def test_a_one_ulp_corruption_is_refused(tmp_path) -> None:
    """THE PAIRED NEGATIVE THAT MATTERS. One ULP, because that is the real defect.

    A gate that only catches visible corruption would have passed the very
    divergence that blocked the R4 claim.
    """

    manifest = _capture(_Env())
    wm.save_world_manifest(str(tmp_path), manifest)

    target = tmp_path / "NS" / "20260734" / "audit" / "0"
    with np.load(target / "world.npz", allow_pickle=False) as handle:
        arrays = {k: handle[k].copy() for k in handle.files}
    arrays["user_positions"][0, 0] = np.nextafter(arrays["user_positions"][0, 0], np.inf)
    np.savez(target / "world.npz", **arrays)

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), contract_id="NS", topology_seed=20260734,
                                block="audit", episode_index=0)
    assert excinfo.value.reason == "COMPONENT_DIGEST_MISMATCH"
    assert "user_positions" in str(excinfo.value)


def test_a_missing_manifest_is_refused_not_regenerated(tmp_path) -> None:
    """Silently generating a world when replay is in force is the defect wearing a
    different hat."""

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), contract_id="NS", topology_seed=1,
                                block="audit", episode_index=0)
    assert excinfo.value.reason == "MANIFEST_ABSENT"


def test_a_schema_bump_invalidates_old_bytes(tmp_path) -> None:
    manifest = _capture(_Env())
    wm.save_world_manifest(str(tmp_path), manifest)
    sidecar = tmp_path / "NS" / "20260734" / "audit" / "0" / "identity.json"
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    meta["identity"]["schema_version"] = wm.SCHEMA_VERSION + 1
    sidecar.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(wm.WorldManifestError) as excinfo:
        wm.load_world_manifest(str(tmp_path), contract_id="NS", topology_seed=20260734,
                                block="audit", episode_index=0)
    assert excinfo.value.reason == "SCHEMA_MISMATCH"


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


def test_generator_version_moves_when_a_generator_changes() -> None:
    """A version that cannot change is a version nobody has to maintain and
    everybody can trust wrongly."""

    env = _Env()
    baseline = wm.generator_version(env)
    assert wm.generator_version(_Env()) == baseline, "must be stable for equal envs"

    env.n_users = 4
    assert wm.generator_version(env) != baseline, "shape parameters must be covered"


def test_generator_version_covers_the_declared_function_list() -> None:
    assert "_generate_forced_relay_cluster_positions" in wm.GENERATOR_FUNCTIONS
    assert "_initialize_user_waypoints_rpgm" in wm.GENERATOR_FUNCTIONS
    # and it must hash real source, not just names -- proven against the real class
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv
    for name in wm.GENERATOR_FUNCTIONS:
        assert getattr(UAVEnergyAwareRelayEnv, name, None) is not None, (
            f"{name} is not on the real env class; generator_version would hash "
            f"'<absent>' and silently cover nothing")


def test_it_is_not_wired_into_the_audit_path_yet() -> None:
    """Integration must not precede the step 4 cross-machine gate. This test is the
    reminder, and it should be DELETED in the same change that wires it in."""

    source = (ROOT / "scripts" / "audit_d7_s_event_aligned.py").read_text(encoding="utf-8")
    assert "d7_s_world_manifest" not in source, (
        "the manifest is now referenced by the audit; if that is intentional, the "
        "cross-machine conformance gate must exist and this test must be removed "
        "deliberately rather than edited into passing")
