"""Which world array diverges first between two runs of the same episode keys?

STEP 1 of the provenance correction ordered by the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`):

    compare existing component digests and identify the first differing world
    array

Why this exists rather than a one-off snippet. Runs `30403322062` and
`30479940700` produced DIFFERENT initial worlds for 3 of 8 topologies at
identical `contract_id`, topology-coordinate hash, block, episode index and
`user_world_seed`, with numpy and scipy hard-pinned. Both recorded only the
COMBINED `episode_world_fingerprint`, so answering "which array moved" required
a cross-machine investigation instead of reading a field. `component_digests`
closed that gap; this reads it.

The ruling's Challenge 6 is explicit: **do not** freeze "machine-dependent
construction state" as the causal conclusion until this comparison names the
first differing surface. This script produces that name and nothing more -- it
asserts no cause, and it is an apparatus diagnostic, never a result.

The array ORDER matters and is not alphabetical. `episode_world_fingerprint`
hashes its components in a fixed sequence, and a divergence in an earlier array
can propagate into later ones through the shared RNG stream. "First differing"
means first in that generation order, which is the only ordering that can
distinguish a root cause from its consequences.

Usage -- two artifacts written by `audit_d7_s_event_aligned.py`:

    python scripts/d7_s_world_component_digest_diff.py \
        --left  local/d7_s_event_aligned.json \
        --right cloud/d7_s_event_aligned.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The generation order `episode_world_fingerprint` hashes in. Kept as a literal
# rather than read from a digest dict, because a dict's key order would silently
# become the contract and this ordering is the thing doing the scientific work.
COMPONENT_ORDER = (
    "user_positions",
    "user_velocities",
    "user_waypoints",
    "user_pause_times",
    "user_cluster_assignments",
    "cluster_centers_history",
    "cluster_velocities",
    "cluster_waypoints",
    "cluster_pause_times",
)

IDENTITY_FIELDS = ("block", "episode_index", "episode_seed", "user_world_seed",
                   "pinned_coordinate_hash", "n_users")


def load_worlds(path: str) -> dict:
    """Index one artifact's episode worlds by (block, episode_index)."""
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    provenance = payload.get("episode_world_provenance") or {}
    worlds = provenance.get("episode_worlds") or []
    indexed = {}
    for world in worlds:
        indexed[(world.get("block"), world.get("episode_index"))] = world
    return indexed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--left-label", default="left")
    parser.add_argument("--right-label", default="right")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    left = load_worlds(args.left)
    right = load_worlds(args.right)

    shared = sorted(set(left) & set(right), key=lambda k: (str(k[0]), k[1]))
    only_left = sorted(set(left) - set(right), key=lambda k: (str(k[0]), k[1]))
    only_right = sorted(set(right) - set(left), key=lambda k: (str(k[0]), k[1]))

    print(f"{args.left_label}: {len(left)} episode worlds   "
          f"{args.right_label}: {len(right)} episode worlds   shared: {len(shared)}")
    if only_left or only_right:
        print(f"  NOT COMPARABLE -- keys present on one side only: "
              f"{len(only_left)} {args.left_label}-only, {len(only_right)} {args.right_label}-only")

    if not shared:
        print("\nNO_SHARED_EPISODE_KEYS: nothing to compare. Both artifacts must "
              "cover the same (block, episode_index) keys.")
        return 1

    # A comparison is only meaningful when the registered identity matches. If
    # the seeds differ, the worlds SHOULD differ and a divergence proves nothing
    # -- that is precisely the wrong-namespace error this line already made once.
    identity_mismatches = []
    missing_digests = []
    fingerprint_diff = []
    first_differing: dict[str, int] = {}
    rows = []

    for key in shared:
        a, b = left[key], right[key]
        bad = [f for f in IDENTITY_FIELDS if a.get(f) != b.get(f)]
        if bad:
            identity_mismatches.append((key, bad))
            continue
        da, db = a.get("component_digests"), b.get("component_digests")
        if not da or not db:
            missing_digests.append(key)
            continue
        same_fp = a.get("fingerprint") == b.get("fingerprint")
        differing = [name for name in COMPONENT_ORDER
                     if name in da and name in db and da[name] != db[name]]
        # a component present on one side only is itself a divergence
        differing += [name for name in COMPONENT_ORDER
                      if (name in da) != (name in db)]
        if not same_fp:
            fingerprint_diff.append(key)
        if differing:
            first = differing[0]
            first_differing[first] = first_differing.get(first, 0) + 1
        rows.append({"block": key[0], "episode_index": key[1],
                     "fingerprint_same": same_fp,
                     "first_differing_component": differing[0] if differing else None,
                     "all_differing_components": differing})

    if identity_mismatches:
        print(f"\nREFUSED for {len(identity_mismatches)} episode(s): registered identity "
              f"differs, so a world difference would prove nothing.")
        for key, bad in identity_mismatches[:5]:
            print(f"  {key}: {bad}")
        return 1

    if missing_digests:
        print(f"\n{len(missing_digests)} episode(s) carry no component_digests. Artifacts "
              f"written before that field was added cannot be localized -- this is the "
              f"state H and run 30479940700 are in.")

    print(f"\nfingerprints differing: {len(fingerprint_diff)} of {len(rows)} comparable")
    if rows:
        print(f"\n{'block':13s} {'ep':>3s} {'fp_same':>8s}  first_differing_component")
        for row in rows:
            print(f"{str(row['block']):13s} {row['episode_index']:3d} "
                  f"{str(row['fingerprint_same']):>8s}  "
                  f"{row['first_differing_component'] or '-'}")

    print("\n=== first differing component, tallied in generation order ===")
    if not first_differing:
        verdict = "WORLD_COMPONENTS_IDENTICAL"
        print("  none -- every comparable episode agrees on all nine arrays")
    else:
        for name in COMPONENT_ORDER:
            if name in first_differing:
                print(f"  {name:28s} {first_differing[name]}")
        earliest = next(n for n in COMPONENT_ORDER if n in first_differing)
        verdict = f"FIRST_DIVERGENCE:{earliest}"
        print(f"\n  earliest in generation order: {earliest}")
        print("  Step 2 is to identify every writer and random source for THAT array.")

    if not fingerprint_diff and not first_differing:
        print("\nA clean result here does NOT clear the generator. It says these two "
              "runs agreed on these episode keys. The divergence is known to affect "
              "only some topologies, so absence on one key set is not absence.")

    print(f"\n{verdict}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"verdict": verdict, "rows": rows,
                       "first_differing_tally": first_differing,
                       "fingerprints_differing": len(fingerprint_diff),
                       "comparable": len(rows),
                       "missing_digests": len(missing_digests),
                       "left": args.left, "right": args.right}, handle, indent=2)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
