"""Persist and replay a complete episode world, so a key identifies one world.

STEP 3 of the provenance correction ordered by the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`, §6.2), and the
selected repair family. Design: `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`.

THE DEFECT THIS REMOVES. A registered episode key -- contract namespace,
topology-coordinate hash, block, episode index, `user_world_seed` -- does not
identify one world. Runs `30403322062` and `30479940700` produced different
initial worlds on 3 of 8 topologies at identical keys with numpy and scipy
hard-pinned, and both reported `seed_controls_generation = True` for all 128
episodes. The ruling: a registered key must identify either one reproducible world
or one validated probability law, and it currently identifies neither.

Replay achieves the first WITHOUT requiring world generation to be bit-portable
across machines, which is why it is the reversible repair: it holds whatever the
root cause turns out to be, so it does not wait on the root-cause localization
(steps 1-2) to be correct.

**NOT WIRED IN.** Nothing in the audit path calls this yet. Integration changes a
claim-bearing path and must not land before the step 4 cross-machine conformance
gate exists -- a manifest mechanism that has never been checked across two
machines would reintroduce the same unverified assumption one level up.

The ordering rule that matters when reading a mismatch: components are compared in
GENERATION order, because a divergence in an earlier array propagates into later
ones through the shared RNG stream.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_VERSION = 1

# The functions that produce the nine world arrays. `generator_version` hashes
# their source, so editing any of them invalidates existing manifests.
GENERATOR_FUNCTIONS = (
    "_generate_user_positions",
    "_generate_forced_relay_cluster_positions",
    "_generate_coverage_hole_positions",
    "_init_user_velocities",
    "_initialize_user_waypoints_rpgm",
)

IDENTITY_FIELDS = (
    "schema_version", "contract_id", "topology_seed", "pinned_coordinate_hash",
    "block", "episode_index", "user_world_seed", "generator_version",
    "n_users", "n_clusters",
)


class WorldManifestError(RuntimeError):
    """A manifest could not be produced, loaded, or verified.

    Carries `reason` so callers distinguish a missing manifest from a corrupted
    one. A digest mismatch is FAIL-CLOSED and must never be downgraded to a
    warning: the whole point is that the world the episode runs in is the world
    that was registered.
    """

    def __init__(self, message: str, *, reason: str):
        super().__init__(message)
        self.reason = reason


def _component_order() -> tuple:
    """Imported lazily so this module can be imported BY the audit module without
    an import cycle once integration lands."""
    import audit_d7_s_event_aligned as audit
    return tuple(audit.WORLD_COMPONENT_ORDER)


def _digest_component(name: str, arr: np.ndarray) -> str:
    """Exactly the bytes `episode_world_fingerprint` feeds its hash, per component.

    Kept byte-identical to that function on purpose: a manifest digest that used a
    different encoding could not be compared against an artifact's
    `component_digests`, and comparing them is how the gate works.
    """
    return hashlib.sha256(b"".join((
        name.encode("utf-8"),
        str(arr.shape).encode("utf-8"),
        np.ascontiguousarray(arr).tobytes(),
    ))).hexdigest()


def generator_version(env) -> str:
    """A content hash over the world generators and their shape parameters.

    [PM BINDING, disclosed in the design note.] The ruling requires the identity
    tuple to carry a world-generator version but does not say how to derive one. A
    hand-maintained integer fails the way every hand-maintained version fails --
    someone edits a generator and forgets to bump it, and then two different worlds
    share a version string. A source hash cannot be forgotten.

    The cost is that a whitespace-only edit to those functions invalidates existing
    manifests. That is the correct direction to err: a wrongly invalidated manifest
    is regenerated, while a wrongly accepted one is a false result.
    """
    parts: list[bytes] = []
    for name in GENERATOR_FUNCTIONS:
        function = getattr(type(env), name, None)
        parts.append(name.encode("utf-8"))
        if function is None:
            parts.append(b"<absent>")
            continue
        try:
            parts.append(inspect.getsource(function).encode("utf-8"))
        except (OSError, TypeError):  # pragma: no cover - source always available here
            raise WorldManifestError(
                f"cannot read source of {name}; generator_version would be a lie",
                reason="GENERATOR_SOURCE_UNAVAILABLE")
    for attribute in ("n_users", "n_clusters", "cluster_std", "user_distribution",
                      "user_movement_model", "area_size"):
        parts.append(f"{attribute}={getattr(env, attribute, None)!r}".encode("utf-8"))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def world_manifest_from_env(env, *, contract_id: str, topology_seed: int, block: str,
                            episode_index: int, user_world_seed: int) -> dict:
    """Capture the complete world, its identity and its per-component digests.

    Must be called at the same point `episode_world_fingerprint` is -- immediately
    after construction and world regeneration, BEFORE any stepping. A manifest
    taken after a step records a stepped world and would replay the wrong state.
    """
    pinned = getattr(env, "pinned_coordinate_hash", None)
    if pinned is None:
        raise WorldManifestError(
            "refusing to capture a manifest from an env with no pinned topology; "
            "the world is a function of the BS layout as well as the seed",
            reason="TOPOLOGY_NOT_PINNED")

    arrays: dict[str, np.ndarray] = {}
    digests: dict[str, str] = {}
    for name in _component_order():
        value = getattr(env, name, None)
        if value is None:
            continue
        arr = np.ascontiguousarray(np.asarray(value))
        arrays[name] = arr
        digests[name] = _digest_component(name, arr)

    if not arrays:
        raise WorldManifestError("env exposed none of the world components",
                                 reason="NO_COMPONENTS")

    identity = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": str(contract_id),
        "topology_seed": int(topology_seed),
        "pinned_coordinate_hash": str(pinned),
        "block": str(block),
        "episode_index": int(episode_index),
        "user_world_seed": int(user_world_seed),
        "generator_version": generator_version(env),
        "n_users": int(getattr(env, "n_users", 0)),
        "n_clusters": int(getattr(env, "n_clusters", 0)),
    }
    return {"identity": identity, "arrays": arrays, "component_digests": digests}


def manifest_relative_dir(identity: dict) -> str:
    return os.path.join(str(identity["contract_id"]), str(identity["topology_seed"]),
                        str(identity["block"]), str(identity["episode_index"]))


def save_world_manifest(root: str, manifest: dict) -> str:
    """Write `world.npz` plus a numpy-free `identity.json` sidecar.

    Arrays go to npz because they are float64 and must round-trip bit-exactly;
    identity goes to JSON so provenance is readable without numpy.
    """
    identity = manifest["identity"]
    target = os.path.join(root, manifest_relative_dir(identity))
    os.makedirs(target, exist_ok=True)
    np.savez(os.path.join(target, "world.npz"), **manifest["arrays"])
    with open(os.path.join(target, "identity.json"), "w", encoding="utf-8") as handle:
        json.dump({"identity": identity,
                   "component_digests": manifest["component_digests"]},
                  handle, indent=2, sort_keys=True)
    return target


def load_world_manifest(root: str, *, contract_id: str, topology_seed: int, block: str,
                         episode_index: int) -> dict:
    """Load and VERIFY. A digest mismatch raises rather than returning.

    `allow_pickle=False` is deliberate: a manifest is data, and a pickle in this
    path would be both an execution risk and a way for the bytes to stop being
    the bytes.
    """
    identity_stub = {"contract_id": contract_id, "topology_seed": topology_seed,
                     "block": block, "episode_index": episode_index}
    target = os.path.join(root, manifest_relative_dir(identity_stub))
    sidecar = os.path.join(target, "identity.json")
    payload_path = os.path.join(target, "world.npz")
    if not os.path.isfile(sidecar) or not os.path.isfile(payload_path):
        raise WorldManifestError(
            f"no manifest at {target}; a formal episode must not generate its own "
            f"world when replay is in force",
            reason="MANIFEST_ABSENT")

    with open(sidecar, encoding="utf-8") as handle:
        meta = json.load(handle)
    identity = meta.get("identity") or {}
    recorded = meta.get("component_digests") or {}

    if int(identity.get("schema_version", -1)) != SCHEMA_VERSION:
        raise WorldManifestError(
            f"manifest schema {identity.get('schema_version')} != {SCHEMA_VERSION}; "
            f"the layout changed and these bytes cannot be trusted to mean the same "
            f"thing", reason="SCHEMA_MISMATCH")

    arrays: dict[str, np.ndarray] = {}
    with np.load(payload_path, allow_pickle=False) as handle:
        for name in _component_order():
            if name in handle.files:
                arrays[name] = np.ascontiguousarray(handle[name])

    verify_manifest_digests({"identity": identity, "arrays": arrays,
                             "component_digests": recorded})
    return {"identity": identity, "arrays": arrays, "component_digests": recorded}


def verify_manifest_digests(manifest: dict) -> None:
    """Recompute every component digest and refuse on the first mismatch.

    THE TRAP THIS EXISTS FOR. The real failure mode is `user_positions` differing
    in the LAST BIT -- that is what the two cloud runs did to each other. A check
    tuned to catch gross corruption would pass the actual defect, so the paired
    negative for this function perturbs by one ULP, not by a visible amount.
    """
    recorded = manifest.get("component_digests") or {}
    arrays = manifest.get("arrays") or {}

    missing = [n for n in recorded if n not in arrays]
    extra = [n for n in arrays if n not in recorded]
    if missing or extra:
        raise WorldManifestError(
            f"manifest component set does not match its digest set; "
            f"missing arrays {missing}, undigested arrays {extra}",
            reason="COMPONENT_SET_MISMATCH")

    for name in _component_order():
        if name not in arrays:
            continue
        actual = _digest_component(name, arrays[name])
        if actual != recorded[name]:
            raise WorldManifestError(
                f"component {name!r} does not match its recorded digest "
                f"({actual[:12]} != {recorded[name][:12]}). This is the first "
                f"differing component in GENERATION order, so it is the one to "
                f"investigate; later components may differ only as a consequence.",
                reason="COMPONENT_DIGEST_MISMATCH")


def apply_world_manifest(env, manifest: dict) -> dict:
    """Install a verified world onto an env, and verify again after installing.

    Verifying before AND after is not paranoia about the arrays -- it is about the
    assignment. `env.user_positions = arr` can be intercepted by a property, a
    subclass, or a dtype coercion, any of which would leave the env holding
    something other than the manifest while the manifest still verifies. The
    post-assignment read-back is what makes "this episode ran in the registered
    world" a checked statement rather than an intended one.
    """
    verify_manifest_digests(manifest)
    for name, arr in manifest["arrays"].items():
        setattr(env, name, np.ascontiguousarray(arr).copy())

    readback = {}
    for name in manifest["arrays"]:
        value = getattr(env, name, None)
        if value is None:
            raise WorldManifestError(
                f"env dropped component {name!r} on assignment",
                reason="ASSIGNMENT_DROPPED_COMPONENT")
        readback[name] = np.ascontiguousarray(np.asarray(value))
    verify_manifest_digests({"identity": manifest["identity"], "arrays": readback,
                             "component_digests": manifest["component_digests"]})

    applied = int(manifest["identity"]["user_world_seed"])
    env.user_world_seed_applied = applied
    return {"applied_components": sorted(manifest["arrays"]),
            "user_world_seed": applied,
            "generator_version": manifest["identity"]["generator_version"]}
