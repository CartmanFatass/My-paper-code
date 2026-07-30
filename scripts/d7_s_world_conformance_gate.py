"""Cross-machine world conformance gate. Fails closed, and refuses to be fooled.

STEP 4 of the provenance correction ordered by the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`, §6.3):

    define a cross-machine fail-closed conformance gate

and the ruling's reason it must be cross-machine:

    A test performed on one machine or one process is insufficient because that
    is precisely where the current generator appears stable.

THE TRAP THIS GATE IS BUILT AROUND. An agreement between two digest samples means
nothing unless the samples came from *different* runtimes. The `workers` job prints
`nproc` and no CPU model, so two samples that agree are indistinguishable from two
samples that ran on the same hardware. A gate that passed on agreement alone would
therefore report PASS most loudly exactly when it had tested nothing.

So this gate has three outcomes, not two:

    WORLD_CONFORMANCE_PASS          samples agree AND came from distinct runtimes
    WORLD_CONFORMANCE_FAIL          samples disagree -- localized, decisive
    WORLD_CONFORMANCE_UNTESTED      samples agree but the runtimes are not
                                    distinguishable, or identity is missing

`UNTESTED` exits non-zero. It is not a pass, and it must never be recorded as one.

Inputs are artifacts from `d7_s_world_digest_probe.py` (preferred -- it records
runtime identity) or from `audit_d7_s_event_aligned.py`.

    python scripts/d7_s_world_conformance_gate.py --samples a.json b.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMPONENT_ORDER = (
    "user_positions", "user_velocities", "user_waypoints",
    "user_pause_times", "user_cluster_assignments",
    "cluster_centers_history", "cluster_velocities",
    "cluster_waypoints", "cluster_pause_times",
)

# Fields that must MATCH for a comparison to be meaningful at all.
IDENTITY_FIELDS = ("episode_seed", "user_world_seed", "pinned_coordinate_hash", "n_users")

# Fields whose difference makes two samples genuinely distinct runtimes. Any one
# of these differing is enough.
RUNTIME_DISCRIMINATORS = ("processor", "machine", "platform", "numpy_blas", "cpu_features")


BLOCK_BEGIN = "=== D7_S_WORLD_DIGEST_BLOCK_BEGIN ==="
BLOCK_END = "=== D7_S_WORLD_DIGEST_BLOCK_END ==="


def _read_payload(path: str) -> dict:
    """Accept a JSON artifact, or a log containing the embedded digest block.

    The `benchmark` workflow job pipes `d7_s_clone_conformance_check.py` into
    `conformance.txt` and uploads that file, which is how R4 component digests
    with runtime identity are obtainable at all without a workflow change. So the
    gate reads either shape rather than requiring a separate extraction step that
    someone would have to remember.
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if BLOCK_BEGIN not in text or BLOCK_END not in text:
        raise SystemExit(
            f"{path} is neither a JSON artifact nor a log containing "
            f"{BLOCK_BEGIN!r}. Nothing to compare.")
    body = text.split(BLOCK_BEGIN, 1)[1].split(BLOCK_END, 1)[0].strip()
    payload = json.loads(body)
    if "world_digest_block_error" in payload:
        raise SystemExit(
            f"{path} carries a digest block that FAILED to build: "
            f"{payload['world_digest_block_error']}. That is not an agreement.")
    return payload


def load_sample(path: str) -> dict:
    payload = _read_payload(path)
    provenance = payload.get("episode_world_provenance") or {}
    worlds = provenance.get("episode_worlds") or []
    indexed = {}
    for world in worlds:
        key = (world.get("topology_seed"), world.get("block"), world.get("episode_index"))
        indexed[key] = world
    return {"path": path, "worlds": indexed,
            "runtime": payload.get("runtime_identity") or {}}


def runtimes_are_distinguishable(left: dict, right: dict) -> tuple[bool, str]:
    """True only when some recorded field proves the two runtimes differ."""
    if not left or not right:
        return False, ("at least one sample records no runtime_identity, so 'different "
                       "machine' cannot be established -- use d7_s_world_digest_probe.py, "
                       "which records it")
    for field in RUNTIME_DISCRIMINATORS:
        a, b = left.get(field), right.get(field)
        if a is not None and b is not None and a != b:
            return True, f"{field} differs"
    return False, ("every recorded runtime discriminator is identical, so these two "
                   "samples may have run on the same hardware")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", nargs=2, required=True,
                        help="two digest artifacts, from DIFFERENT machines")
    parser.add_argument("--out", default=None)
    parser.add_argument("--allow-same-runtime", action="store_true",
                        help="development only: report PASS on agreement even when the "
                             "runtimes cannot be distinguished. Never use for a gate.")
    args = parser.parse_args()

    left, right = (load_sample(p) for p in args.samples)
    shared = sorted(set(left["worlds"]) & set(right["worlds"]),
                    key=lambda k: (k[0] or 0, str(k[1]), k[2] or 0))

    print(f"left  {left['path']}  ({len(left['worlds'])} worlds)")
    print(f"right {right['path']}  ({len(right['worlds'])} worlds)")
    print(f"shared episode keys: {len(shared)}")

    distinct, reason = runtimes_are_distinguishable(left["runtime"], right["runtime"])
    print(f"\nruntimes distinguishable: {distinct} -- {reason}")
    for field in RUNTIME_DISCRIMINATORS:
        a = left["runtime"].get(field)
        b = right["runtime"].get(field)
        if a != b:
            print(f"  {field}:\n    left  {str(a)[:110]}\n    right {str(b)[:110]}")

    if not shared:
        print("\nWORLD_CONFORMANCE_UNTESTED: no shared episode keys to compare.")
        return 1

    identity_mismatch = []
    divergences = []
    compared = 0

    for key in shared:
        a, b = left["worlds"][key], right["worlds"][key]
        bad = [f for f in IDENTITY_FIELDS if a.get(f) != b.get(f)]
        if bad:
            identity_mismatch.append((key, bad))
            continue
        da = a.get("component_digests") or {}
        db = b.get("component_digests") or {}
        if not da or not db:
            continue
        compared += 1
        differing = [n for n in COMPONENT_ORDER
                     if (n in da) != (n in db) or (n in da and n in db and da[n] != db[n])]
        if differing:
            divergences.append({"topology_seed": key[0], "block": key[1],
                                 "episode_index": key[2],
                                 "first_differing_component": differing[0],
                                 "all_differing_components": differing})

    if identity_mismatch:
        print(f"\nWORLD_CONFORMANCE_UNTESTED: {len(identity_mismatch)} episode(s) have "
              f"differing registered identity, so a world difference would prove nothing.")
        for key, bad in identity_mismatch[:5]:
            print(f"  {key}: {bad}")
        return 1

    if compared == 0:
        print("\nWORLD_CONFORMANCE_UNTESTED: no episode carried component_digests on both "
              "sides. Artifacts predating that field cannot be gated.")
        return 1

    print(f"\ncompared {compared} episode key(s) with component digests")

    if divergences:
        tally: dict[str, int] = {}
        for entry in divergences:
            name = entry["first_differing_component"]
            tally[name] = tally.get(name, 0) + 1
        print(f"\n{len(divergences)} of {compared} episode worlds DIVERGE")
        for name in COMPONENT_ORDER:
            if name in tally:
                print(f"  first differing: {name:28s} {tally[name]}")
        earliest = next(n for n in COMPONENT_ORDER if n in tally)
        print(f"\n  earliest in generation order: {earliest}")
        verdict = f"WORLD_CONFORMANCE_FAIL:{earliest}"
        exit_code = 1
    elif distinct or args.allow_same_runtime:
        verdict = "WORLD_CONFORMANCE_PASS"
        if not distinct:
            verdict = "WORLD_CONFORMANCE_PASS_SAME_RUNTIME_ALLOWED"
            print("\n  WARNING: --allow-same-runtime was passed. This is not a "
                  "cross-machine result and must not be cited as one.")
        print(f"\nall {compared} compared worlds agree, across distinguishable runtimes")
        exit_code = 0
    else:
        print(f"\nall {compared} compared worlds agree -- but the two runtimes cannot be "
              f"distinguished, so this tested nothing. One machine is exactly where the "
              f"current generator appears stable.")
        verdict = "WORLD_CONFORMANCE_UNTESTED"
        exit_code = 1

    print(f"\n{verdict}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"verdict": verdict, "compared": compared,
                       "divergences": divergences,
                       "runtimes_distinguishable": distinct,
                       "runtime_reason": reason,
                       "left": left["path"], "right": right["path"],
                       "left_runtime": left["runtime"],
                       "right_runtime": right["runtime"]}, handle, indent=2)
        print(f"wrote {args.out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
