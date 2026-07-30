"""Persist and replay a complete episode world, so a key identifies one world.

The selected repair family (Route A), per the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_provenance_correction_result/`).
Design: `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`.

THE DEFECT THIS REMOVES. A registered episode key -- contract namespace,
topology-coordinate hash, block, episode index, `user_world_seed` -- does not
identify one world. Runs `30403322062` and `30479940700` produced different
initial worlds on 3 of 8 topologies at identical keys with numpy and scipy
hard-pinned, and both reported `seed_controls_generation = True` for all 128
episodes.

SCHEMA 2 -- WHAT THE ROUND-2 RULING FOUND WRONG WITH SCHEMA 1. Five defects, all
of them a manifest that verifies against itself while not being the registered
world:

    B1  load compared only `schema_version`. Every other identity field was read
        and never checked, and the path-derived four came FROM the path, so a
        mis-copied directory verified against its own sidecar and was accepted.
        Fixed: `load_world_manifest` requires an INDEPENDENTLY supplied expected
        identity and compares every field, plus shapes and dtypes.
    B2  a `None` component was skipped on capture, and the digest check only
        compared the array set against the digest set -- so a manifest missing
        one of the nine passed both. Fixed: capture refuses an absent component
        and verification requires the set to equal `WORLD_COMPONENT_ORDER`.
    B3  `generator_version` hashed five hand-listed functions. Measured: the
        transitive closure is EIGHT -- `_initialize_cluster_migration_rpgm`,
        `_generate_intra_cluster_waypoint` and `_generate_inter_cluster_waypoint`
        were missing, which are exactly the trigonometric helpers that write the
        array that diverged. Two semantically different generators could share a
        version. Fixed: the closure is DERIVED, never listed.
    B4  apply installed the nine arrays and stopped. `regenerate_user_world` also
        rebuilds the connection baseline, channel state, UAV connections and
        routing paths -- so applying a CORRECT manifest still left an environment
        whose connections and routing belonged to the world just replaced. This
        was the only blocker that fails on the happy path. Fixed below, with the
        rebuild list derived from `regenerate_user_world` itself.
    B5  save overwrote silently and no inventory bound the population together.
        Fixed: create-once, plus a set-hashed inventory.

The ordering rule that matters when reading a mismatch: components are compared in
GENERATION order, because a divergence in an earlier array propagates into later
ones through the shared RNG stream.

**NOT WIRED IN.** Nothing in the audit path calls this. The ruling holds
integration until a manifest-REPLAY gate passes -- the generator-conformance gate
(`d7_s_world_conformance_gate.py`) compares independently generated worlds and
cannot certify replay.

WHAT THIS MODULE STILL DOES NOT DO, and must not be read as doing. It fixes the
INITIAL world. `_update_user_positions_rpgm` and `_update_cluster_centers_rpgm`
re-enter `np.cos`/`np.sin` during the episode, so a manifest covers `t = 0` only.
Closing that is the A1-versus-A2 choice and it is not made here.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import sys
import textwrap

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_VERSION = 2

INVENTORY_FILE = "inventory.json"

# The entry points into world generation. `generator_version` walks OUT from
# these; it does not treat them as the answer. Schema 1 listed the closure by
# hand and was wrong by three functions -- see B3 above.
GENERATOR_SEED_FUNCTIONS = (
    "_generate_user_positions",
    "_generate_forced_relay_cluster_positions",
    "_generate_coverage_hole_positions",
    "_init_user_velocities",
    "_initialize_user_waypoints_rpgm",
)

# The method `apply_world_manifest` must reproduce, because a manifest replaces
# the world rather than advancing it. Kept as a constant so a test can compare it
# against what `regenerate_user_world` actually calls -- see
# `derived_state_rebuild_from_source`.
DERIVED_STATE_REBUILD = (
    "_reset_connection_baseline",
    "_update_channel_state",
    "_update_uav_connections",
    "_compute_routing_paths",
)

IDENTITY_FIELDS = (
    "schema_version", "contract_id", "topology_seed", "pinned_coordinate_hash",
    "block", "episode_index", "user_world_seed", "generator_version",
    "n_users", "n_clusters",
)

# The four that also name the storage path. Listed separately because a mismatch
# on one of these means the manifest was MOVED, which reads differently from a
# manifest that was regenerated under a different configuration.
PATH_IDENTITY_FIELDS = ("contract_id", "topology_seed", "block", "episode_index")


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


def payload_hash(component_digests: dict) -> str:
    """One hash over the whole world, derived from the per-component digests.

    Deliberately NOT a hash of `world.npz`. A zip carries timestamps and member
    ordering, so hashing the file would report two byte-identical worlds as
    different and make the inventory useless for exactly the comparison it exists
    for.
    """
    parts = []
    for name in _component_order():
        if name in component_digests:
            parts.append(f"{name}={component_digests[name]}".encode("utf-8"))
    return hashlib.sha256(b"\n".join(parts)).hexdigest()


# ------------------------------------------------------------------ B3 -------

def _as_class(env_or_cls):
    """Accept an instance or the class itself.

    The closure and the rebuild list are properties of the CLASS, and the real env
    cannot be instantiated cheaply in a unit test -- so a test that wants to check
    the real generator's call graph must be able to hand over the class.
    """
    return env_or_cls if isinstance(env_or_cls, type) else type(env_or_cls)


def _method_source(cls, name: str):
    function = getattr(cls, name, None)
    if function is None:
        return None
    try:
        return textwrap.dedent(inspect.getsource(function))
    except (OSError, TypeError):  # pragma: no cover - source available in-repo
        raise WorldManifestError(
            f"cannot read source of {name}; generator_version would be a lie",
            reason="GENERATOR_SOURCE_UNAVAILABLE")


def _self_calls(source: str) -> list:
    """Every `self.<name>(...)` in a method body, from the AST rather than a regex.

    A regex over `self\\.` also matches attribute reads, which would drag
    unrelated state into the closure and make the version churn for no reason.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - dedent handles the real cases
        return []
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"):
            out.append(node.func.attr)
    return out


def _self_attribute_reads(source: str) -> list:
    """Every `self.<attr>` that is READ rather than called, from the AST.

    These are the generator's configuration inputs. Deriving them is B3's second
    half: the ruling's complaint was not only the missing functions but the
    "multiple distribution and movement parameters" a hand-picked subset omitted.
    A parameter the generator reads is a parameter that changes the world.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover
        return []
    called = set()
    seen = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"):
            called.add(node.func.attr)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "self" and node.attr not in called):
            seen.append(node.attr)
    return seen


def generator_function_closure(env) -> tuple:
    """Every method reachable from the world-generation entry points.

    THIS IS B3's FIX AND THE REASON IT IS DERIVED. Measured on the real env class:
    the closure is eight functions, and the three the hand-written list missed --
    `_initialize_cluster_migration_rpgm`, `_generate_intra_cluster_waypoint`,
    `_generate_inter_cluster_waypoint` -- are precisely the trigonometric helpers
    that overwrite `user_velocities`. A hand list is that error frozen into code.

    Accepts an instance or the class.
    """
    cls = _as_class(env)
    seen: set = set()
    visited: set = set()
    stack = [n for n in GENERATOR_SEED_FUNCTIONS]
    while stack:
        name = stack.pop()
        if name in visited:
            continue
        visited.add(name)
        source = _method_source(cls, name)
        if source is None:
            # A seed the class does not define contributes nothing. Counting it
            # anyway is how an env with NO generators got a stable version hash.
            continue
        seen.add(name)
        for called in _self_calls(source):
            if called in visited:
                continue
            if callable(getattr(cls, called, None)):
                stack.append(called)
    return tuple(sorted(seen))


def _configuration_parameters(env) -> tuple:
    """Every constructor parameter across the MRO, UNION every attribute the
    generator closure reads, so configuration cannot be forgotten the way the
    function list was.

    A hand-listed subset is the same defect as a hand-listed function list: it
    looks complete and silently is not. Two derivations rather than one because
    neither alone is complete -- a constructor parameter may be unused, and an
    attribute set outside `__init__` (a class attribute, a later assignment) has
    no signature to be read off. The world components themselves are excluded:
    they are the generator's OUTPUT, and hashing them into the version would make
    every world its own generator.
    """
    cls = _as_class(env)
    names: set = set()
    for name in generator_function_closure(cls):
        source = _method_source(cls, name)
        if source is None:
            continue
        names.update(_self_attribute_reads(source))
    for excluded in _component_order():
        names.discard(excluded)
    names.discard("np_random")
    for ancestor in cls.__mro__:
        if ancestor is object:
            continue
        init = ancestor.__dict__.get("__init__")
        if init is None:
            continue
        try:
            signature = inspect.signature(init)
        except (TypeError, ValueError):  # pragma: no cover
            continue
        for parameter in signature.parameters.values():
            if parameter.name == "self":
                continue
            if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
                continue
            names.add(parameter.name)
    return tuple(sorted(names))


def generator_version(env) -> str:
    """A content hash over the COMPLETE world-generation implementation and its
    complete configuration.

    [PM BINDING, disclosed in the design note.] The ruling requires a
    world-generator version and requires it to cover every reachable writer and
    every source parameter; it does not say how to derive one. Binding: the
    transitive call closure's source, plus every constructor parameter's value.

    A hand-maintained integer fails the way every hand-maintained version fails.
    A source hash cannot be forgotten. Its cost is that a whitespace-only edit
    invalidates existing manifests -- the correct direction to err, because a
    wrongly invalidated manifest is regenerated while a wrongly accepted one is a
    false result.
    """
    cls = _as_class(env)
    closure = generator_function_closure(cls)
    if not closure:
        raise WorldManifestError(
            f"{cls.__name__} exposes none of {GENERATOR_SEED_FUNCTIONS}, so the "
            f"closure is empty and generator_version would hash nothing but the "
            f"schema number. A version that covers no code is worse than none: it "
            f"is stable across every possible generator.",
            reason="GENERATOR_CLOSURE_EMPTY")
    parts: list = [f"schema={SCHEMA_VERSION}".encode("utf-8")]
    for name in closure:
        parts.append(name.encode("utf-8"))
        source = _method_source(cls, name)
        parts.append(b"<absent>" if source is None else source.encode("utf-8"))
    parts.append(b"--config--")
    for name in _configuration_parameters(cls):
        value = getattr(env, name, "<absent>")
        if callable(value):
            continue
        if isinstance(value, np.ndarray):
            # a configuration array (an MCS table, a bandwidth ladder) is content,
            # not identity -- hash its bytes rather than numpy's truncated repr,
            # which elides the middle of a long array and would collide
            value = ("ndarray", value.shape, value.dtype.str,
                     hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest())
        parts.append(f"{name}={value!r}".encode("utf-8"))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def derived_state_rebuild_from_source(env) -> tuple:
    """What `regenerate_user_world` actually calls after replacing the world.

    Exists so a test can compare `DERIVED_STATE_REBUILD` against the real thing.
    If someone adds a fifth rebuild step to `regenerate_user_world`, manifest
    replay silently stops reproducing it -- and that is invisible unless something
    reads the source.
    """
    cls = _as_class(env)
    source = _method_source(cls, "regenerate_user_world")
    if source is None:
        raise WorldManifestError("env has no regenerate_user_world to compare against",
                                 reason="NO_REGENERATE_USER_WORLD")
    generation = set(generator_function_closure(cls))
    out = []
    for name in _self_calls(source):
        if name in generation or name in out:
            continue
        out.append(name)
    return tuple(out)


# ------------------------------------------------------- capture and store ---

def world_manifest_from_env(env, *, contract_id: str, topology_seed: int, block: str,
                            episode_index: int, user_world_seed: int) -> dict:
    """Capture the complete world, its identity, shapes, dtypes and digests.

    Must be called at the same point `episode_world_fingerprint` is -- immediately
    after construction and world regeneration, BEFORE any stepping. A manifest
    taken after a step records a stepped world and would replay the wrong state.

    B2: an absent component is a REFUSAL, not a skip. Schema 1 skipped it, and
    `verify_manifest_digests` then compared the short array set against the short
    digest set and found them consistent -- a manifest missing one of the nine
    passed every check it had.
    """
    pinned = getattr(env, "pinned_coordinate_hash", None)
    if pinned is None:
        raise WorldManifestError(
            "refusing to capture a manifest from an env with no pinned topology; "
            "the world is a function of the BS layout as well as the seed",
            reason="TOPOLOGY_NOT_PINNED")

    arrays: dict = {}
    digests: dict = {}
    shapes: dict = {}
    dtypes: dict = {}
    absent = []
    for name in _component_order():
        value = getattr(env, name, None)
        if value is None:
            absent.append(name)
            continue
        arr = np.ascontiguousarray(np.asarray(value))
        arrays[name] = arr
        digests[name] = _digest_component(name, arr)
        shapes[name] = list(arr.shape)
        dtypes[name] = arr.dtype.str

    if absent:
        raise WorldManifestError(
            f"env exposed no value for world component(s) {absent}. A manifest is "
            f"the COMPLETE world; a partial one verifies against itself and still "
            f"fails to identify the episode.",
            reason="COMPONENT_ABSENT")

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
    return {"identity": identity, "arrays": arrays, "component_digests": digests,
            "component_shapes": shapes, "component_dtypes": dtypes,
            "payload_hash": payload_hash(digests)}


def manifest_relative_dir(identity: dict) -> str:
    return os.path.join(str(identity["contract_id"]), str(identity["topology_seed"]),
                        str(identity["block"]), str(identity["episode_index"]))


def save_world_manifest(root: str, manifest: dict, *, allow_overwrite: bool = False) -> str:
    """Write `world.npz` plus a numpy-free `identity.json` sidecar, ONCE.

    B5: schema 1 used `makedirs(exist_ok=True)` and `np.savez`, both of which
    overwrite in silence. A formal population whose manifests can be replaced
    in place is not a frozen population, and the replacement leaves no trace.

    `allow_overwrite` exists for development regeneration and must never be set
    on a conclusion-bearing path. Re-writing IDENTICAL bytes is always permitted;
    that is idempotence, not mutation.
    """
    identity = manifest["identity"]
    target = os.path.join(root, manifest_relative_dir(identity))
    payload_path = os.path.join(target, "world.npz")
    sidecar_path = os.path.join(target, "identity.json")

    if os.path.exists(sidecar_path) and not allow_overwrite:
        try:
            with open(sidecar_path, encoding="utf-8") as handle:
                existing = json.load(handle)
        except (OSError, json.JSONDecodeError):
            existing = {}
        if existing.get("payload_hash") != manifest["payload_hash"]:
            raise WorldManifestError(
                f"a DIFFERENT manifest already exists at {target} "
                f"(existing payload {str(existing.get('payload_hash'))[:12]}, new "
                f"{manifest['payload_hash'][:12]}). Manifests are create-once; pass "
                f"allow_overwrite only on a development set.",
                reason="MANIFEST_EXISTS")

    os.makedirs(target, exist_ok=True)
    np.savez(payload_path, **manifest["arrays"])
    with open(sidecar_path, "w", encoding="utf-8") as handle:
        json.dump({"identity": identity,
                   "component_digests": manifest["component_digests"],
                   "component_shapes": manifest["component_shapes"],
                   "component_dtypes": manifest["component_dtypes"],
                   "payload_hash": manifest["payload_hash"]},
                  handle, indent=2, sort_keys=True)
    return target


# -------------------------------------------------------------- load, B1 ----

def expected_identity(*, contract_id: str, topology_seed: int, block: str,
                      episode_index: int, pinned_coordinate_hash: str,
                      user_world_seed: int, generator_version_hash: str,
                      n_users: int, n_clusters: int) -> dict:
    """Build the identity a caller asserts INDEPENDENTLY of the stored sidecar.

    Every field is keyword-only and none defaults. A field that could be omitted
    would be a field nobody checks, which is exactly how B1 happened.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_id": str(contract_id),
        "topology_seed": int(topology_seed),
        "pinned_coordinate_hash": str(pinned_coordinate_hash),
        "block": str(block),
        "episode_index": int(episode_index),
        "user_world_seed": int(user_world_seed),
        "generator_version": str(generator_version_hash),
        "n_users": int(n_users),
        "n_clusters": int(n_clusters),
    }


def _compare_identity(recorded: dict, expected: dict) -> None:
    if int(recorded.get("schema_version", -1)) != SCHEMA_VERSION:
        raise WorldManifestError(
            f"manifest schema {recorded.get('schema_version')} != {SCHEMA_VERSION}; "
            f"the layout changed and these bytes cannot be trusted to mean the same "
            f"thing", reason="SCHEMA_MISMATCH")

    differing = []
    for field in IDENTITY_FIELDS:
        want = expected.get(field)
        got = recorded.get(field)
        if isinstance(want, int) and not isinstance(want, bool):
            try:
                got_cmp = int(got)
            except (TypeError, ValueError):
                got_cmp = got
        else:
            got_cmp = got if got is None else str(got)
            want = want if want is None else str(want)
        if got_cmp != want:
            differing.append((field, got, expected.get(field)))

    if differing:
        moved = [f for f, _, _ in differing if f in PATH_IDENTITY_FIELDS]
        detail = "; ".join(f"{f}: manifest {g!r} != expected {w!r}" for f, g, w in differing)
        hint = (" The differing fields name the storage path, so this manifest was "
                "MOVED or COPIED into a directory that does not describe it."
                if moved else
                " The manifest describes a different configuration than the caller "
                "expects, so its arrays are a different world.")
        raise WorldManifestError(
            f"manifest identity does not match the independently expected identity. "
            f"{detail}.{hint}",
            reason="IDENTITY_MISMATCH")


def _compare_layout(arrays: dict, shapes: dict, dtypes: dict) -> None:
    for name in _component_order():
        if name not in arrays:
            continue
        arr = arrays[name]
        want_shape = shapes.get(name)
        want_dtype = dtypes.get(name)
        if want_shape is None or want_dtype is None:
            raise WorldManifestError(
                f"component {name!r} carries no recorded shape/dtype; a schema-{SCHEMA_VERSION} "
                f"manifest records both and one without them cannot be checked",
                reason="LAYOUT_UNRECORDED")
        if list(arr.shape) != list(want_shape):
            raise WorldManifestError(
                f"component {name!r} has shape {list(arr.shape)}, recorded {list(want_shape)}",
                reason="SHAPE_MISMATCH")
        if arr.dtype.str != want_dtype:
            raise WorldManifestError(
                f"component {name!r} has dtype {arr.dtype.str}, recorded {want_dtype}. A "
                f"dtype change is a different world even when the digits look the same.",
                reason="DTYPE_MISMATCH")


def load_world_manifest(root: str, *, expected: dict) -> dict:
    """Load and VERIFY against an INDEPENDENTLY supplied identity.

    B1: schema 1 derived the path from the requested key, then checked only
    `schema_version`. Everything else in the sidecar was read and never compared,
    so a manifest copied into a plausible directory verified against its own
    digests and was accepted as the registered world.

    `allow_pickle=False` is deliberate: a manifest is data, and a pickle in this
    path would be both an execution risk and a way for the bytes to stop being
    the bytes.
    """
    missing = [f for f in IDENTITY_FIELDS if f not in expected]
    if missing:
        raise WorldManifestError(
            f"expected identity is incomplete: {missing}. A field the caller does "
            f"not supply is a field nobody checks.",
            reason="EXPECTED_IDENTITY_INCOMPLETE")

    target = os.path.join(root, manifest_relative_dir(expected))
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
    shapes = meta.get("component_shapes") or {}
    dtypes = meta.get("component_dtypes") or {}

    _compare_identity(identity, expected)

    arrays: dict = {}
    with np.load(payload_path, allow_pickle=False) as handle:
        for name in _component_order():
            if name in handle.files:
                arrays[name] = np.ascontiguousarray(handle[name])

    manifest = {"identity": identity, "arrays": arrays, "component_digests": recorded,
                "component_shapes": shapes, "component_dtypes": dtypes,
                "payload_hash": meta.get("payload_hash")}
    verify_manifest_digests(manifest)
    _compare_layout(arrays, shapes, dtypes)

    recomputed = payload_hash(recorded)
    if manifest["payload_hash"] != recomputed:
        raise WorldManifestError(
            f"recorded payload_hash {str(manifest['payload_hash'])[:12]} != "
            f"{recomputed[:12]} recomputed from the component digests",
            reason="PAYLOAD_HASH_MISMATCH")
    return manifest


def verify_manifest_digests(manifest: dict, *, require_complete: bool = True) -> None:
    """Recompute every component digest and refuse on the first mismatch.

    THE TRAP THIS EXISTS FOR. The real failure mode is `user_positions` differing
    in the LAST BIT -- that is what the two cloud runs did to each other. A check
    tuned to catch gross corruption would pass the actual defect, so the paired
    negative for this function perturbs by one ULP, not by a visible amount.

    B2: `require_complete` is the second trap. Comparing the array set against the
    digest set proves only that the manifest is internally consistent. A manifest
    missing the same component from BOTH sets is internally consistent and is not
    the world. `require_complete=False` exists only for the intermediate
    read-back inside `apply_world_manifest`, never for a stored manifest.
    """
    recorded = manifest.get("component_digests") or {}
    arrays = manifest.get("arrays") or {}
    order = _component_order()

    missing = [n for n in recorded if n not in arrays]
    extra = [n for n in arrays if n not in recorded]
    if missing or extra:
        raise WorldManifestError(
            f"manifest component set does not match its digest set; "
            f"missing arrays {missing}, undigested arrays {extra}",
            reason="COMPONENT_SET_MISMATCH")

    if require_complete:
        absent = [n for n in order if n not in arrays]
        unknown = [n for n in arrays if n not in order]
        if absent or unknown:
            raise WorldManifestError(
                f"manifest does not carry the complete world: missing {absent}, "
                f"unrecognised {unknown}. The required set is exactly "
                f"WORLD_COMPONENT_ORDER; a self-consistent partial manifest is the "
                f"failure this check exists for.",
                reason="COMPONENT_SET_INCOMPLETE")

    for name in order:
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


# ------------------------------------------------------------- apply, B4 ----

def _rng_state_digest(env) -> str:
    """A digest of the continuation stream's state, or `<none>`.

    Used to PROVE the derived-state rebuild consumes no registered randomness.
    Measured on the real class: 35 functions are reachable from the four rebuild
    calls and none of them touches `np_random`, so this assertion is satisfiable
    and any future edit that breaks it is a real finding rather than a nuisance.
    """
    rng = getattr(env, "np_random", None)
    if rng is None:
        return "<none>"
    try:
        state = rng.get_state()
    except AttributeError:
        try:
            state = rng.bit_generator.state
        except AttributeError:  # pragma: no cover
            return "<unreadable>"
    return hashlib.sha256(repr(state).encode("utf-8")).hexdigest()


def apply_world_manifest(env, manifest: dict, *, rebuild_derived_state: bool = True) -> dict:
    """Install a verified world onto an env, rebuild what depends on it, verify.

    Verifying before AND after the assignment is not paranoia about the arrays --
    it is about the assignment. `env.user_positions = arr` can be intercepted by a
    property, a subclass, or a dtype coercion, any of which would leave the env
    holding something other than the manifest while the manifest still verifies.

    B4, AND THE ONLY BLOCKER THAT FAILED ON THE HAPPY PATH. Schema 1 stopped after
    the read-back. `regenerate_user_world` additionally runs the four calls in
    `DERIVED_STATE_REBUILD`, and its own comment says why: the world was REPLACED,
    not advanced, so without the rebuild the next diff compares new serving sets
    against serving sets belonging to the DISCARDED world and books the difference
    as pre-episode handovers, joins and leaves -- state the D7.S event fingerprint
    then captures as if the episode had produced it. Applying a perfectly correct
    manifest still produced a non-identifying hybrid environment.

    `rebuild_derived_state=False` exists for unit tests over a bare component
    holder. A conclusion-bearing path must never pass it.
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
                             "component_digests": manifest["component_digests"]},
                            require_complete=False)

    rebuilt: tuple = ()
    rng_before = rng_after = None
    if rebuild_derived_state:
        missing = [n for n in DERIVED_STATE_REBUILD
                   if not callable(getattr(env, n, None))]
        if missing:
            raise WorldManifestError(
                f"env cannot rebuild derived state; missing {missing}. Applying the "
                f"arrays alone leaves connections, channel state and routing from "
                f"the world that was just replaced.",
                reason="DERIVED_STATE_METHOD_MISSING")
        rng_before = _rng_state_digest(env)
        for name in DERIVED_STATE_REBUILD:
            getattr(env, name)()
        rng_after = _rng_state_digest(env)
        if rng_after != rng_before:
            raise WorldManifestError(
                "the derived-state rebuild consumed registered continuation "
                "randomness. Replay must not perturb the arm streams, or the "
                "manifest changes the measurement it exists to fix.",
                reason="DERIVED_REBUILD_CONSUMED_RANDOMNESS")
        rebuilt = DERIVED_STATE_REBUILD

    applied = int(manifest["identity"]["user_world_seed"])
    env.user_world_seed_applied = applied
    return {"applied_components": sorted(manifest["arrays"]),
            "user_world_seed": applied,
            "generator_version": manifest["identity"]["generator_version"],
            "payload_hash": manifest.get("payload_hash"),
            "derived_state_rebuilt": list(rebuilt),
            "rng_state_digest": rng_after,
            "rng_state_unchanged": (rng_before == rng_after) if rebuilt else None}


# ---------------------------------------------------------- inventory, B5 ---

def build_manifest_inventory(manifests) -> dict:
    """Bind a whole population together, so the SET is frozen and not just its parts.

    B5: without this there is nothing that says which episode keys the population
    contains. A manifest can be deleted, and every remaining manifest still
    verifies perfectly.
    """
    entries = []
    for manifest in manifests:
        identity = manifest["identity"]
        entries.append({
            "relative_dir": manifest_relative_dir(identity).replace(os.sep, "/"),
            "identity": {field: identity[field] for field in IDENTITY_FIELDS},
            "component_digests": dict(manifest["component_digests"]),
            "payload_hash": manifest["payload_hash"],
        })
    entries.sort(key=lambda e: e["relative_dir"])

    duplicates = [e["relative_dir"] for e in entries]
    if len(set(duplicates)) != len(duplicates):
        raise WorldManifestError(
            "two manifests share an episode key; a population with a duplicated key "
            "weights one world twice", reason="DUPLICATE_EPISODE_KEY")

    set_hash = hashlib.sha256("\n".join(
        f"{e['relative_dir']}={e['payload_hash']}" for e in entries).encode("utf-8")).hexdigest()
    return {"schema_version": SCHEMA_VERSION, "entries": entries,
            "episode_count": len(entries), "set_hash": set_hash}


def write_manifest_inventory(root: str, manifests, *, allow_overwrite: bool = False) -> str:
    inventory = build_manifest_inventory(manifests)
    path = os.path.join(root, INVENTORY_FILE)
    if os.path.exists(path) and not allow_overwrite:
        with open(path, encoding="utf-8") as handle:
            existing = json.load(handle)
        if existing.get("set_hash") != inventory["set_hash"]:
            raise WorldManifestError(
                f"an inventory with a DIFFERENT set_hash already exists at {path}; "
                f"a frozen population is not re-frozen",
                reason="INVENTORY_EXISTS")
    os.makedirs(root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(inventory, handle, indent=2, sort_keys=True)
    return path


def verify_manifest_inventory(root: str) -> dict:
    """Reload every manifest the inventory names and check the set is intact.

    Catches the three failures a per-manifest check cannot see: an episode key
    deleted, an episode key added, and a manifest replaced by a different world
    that verifies perfectly against its own sidecar.
    """
    path = os.path.join(root, INVENTORY_FILE)
    if not os.path.isfile(path):
        raise WorldManifestError(f"no inventory at {path}; the population set is "
                                 f"not frozen", reason="INVENTORY_ABSENT")
    with open(path, encoding="utf-8") as handle:
        inventory = json.load(handle)

    checked = []
    for entry in inventory.get("entries", []):
        expected = dict(entry["identity"])
        manifest = load_world_manifest(root, expected=expected)
        if manifest["payload_hash"] != entry["payload_hash"]:
            raise WorldManifestError(
                f"{entry['relative_dir']} holds a different world than the inventory "
                f"records ({str(manifest['payload_hash'])[:12]} != "
                f"{str(entry['payload_hash'])[:12]})",
                reason="INVENTORY_PAYLOAD_MISMATCH")
        checked.append(manifest)

    rebuilt = build_manifest_inventory(checked)
    if rebuilt["set_hash"] != inventory.get("set_hash"):
        raise WorldManifestError(
            f"inventory set_hash {str(inventory.get('set_hash'))[:12]} != "
            f"{rebuilt['set_hash'][:12]} rebuilt from what is on disk; the SET "
            f"changed even though every manifest verifies",
            reason="INVENTORY_SET_HASH_MISMATCH")
    return {"set_hash": rebuilt["set_hash"], "episode_count": rebuilt["episode_count"],
            "manifests": checked}
