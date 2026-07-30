"""Emit per-component world digests for a frozen episode key set. Construction only.

WHY THIS EXISTS. Step 1 of the provenance correction needs the same episode keys'
component digests from two machines. The only way to get them today is to run the
full audit -- `--smoke --dev` took over half an hour per arm and the cloud job runs
two arms, so localizing a divergence cost hours of wall clock for data that takes
seconds to produce. This constructs the worlds and hashes them. It never steps an
environment, never forks a continuation, and computes no estimand.

That makes it cheap enough to run on any machine, in any job, as often as needed --
which is the point, because the ruling requires a **cross-process and
cross-machine** check and one machine is exactly where the current generator looks
stable.

It is a DIAGNOSTIC. It asserts nothing about any estimand and writes nothing into
the audit path.

    python scripts/d7_s_world_digest_probe.py --out local_digests.json
    python scripts/d7_s_world_digest_probe.py --topologies 20260725 --episodes 2

Compare two of its outputs with
`scripts/d7_s_world_component_digest_diff.py --left A --right B`, which reports the
first differing array in generation order and refuses when the registered identity
does not match.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit_d7_s_event_aligned as audit  # noqa: E402


def runtime_identity() -> dict:
    """Delegates to the audit module, which is the single definition.

    It was duplicated here first, and a duplicate of an identity function is a
    slow-motion drift: two artifacts could record "the same" runtime under two
    different definitions of same. The audit script now writes this into every
    artifact it produces, so the probe and the formal path must agree by
    construction rather than by review.
    """
    return audit.runtime_identity()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topologies", type=int, nargs="+",
                        default=list(audit.TOPOLOGY_SEEDS_R4))
    parser.add_argument("--blocks", nargs="+", default=["calibration", "audit"])
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--contract-id", default=audit.R4_POPULATION_NAMESPACE,
                        help="seed namespace; must be R4's when probing the R4 population")
    parser.add_argument("--energy-stage", default="S3")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    # Same refusal as the rejoin probe, for the same measured reason: rolling the
    # R4 topologies under the module's default namespace produces a DIFFERENT
    # population, and every derived seed differs.
    if (set(args.topologies) == set(audit.TOPOLOGY_SEEDS_R4)
            and args.contract_id != audit.R4_POPULATION_NAMESPACE):
        raise SystemExit(
            f"REFUSED: probing the frozen R4 population under contract_id "
            f"{args.contract_id!r}, not {audit.R4_POPULATION_NAMESPACE!r}. Those are "
            f"different episodes -- every derived seed differs.")

    runtime = runtime_identity()
    print("=== runtime identity ===")
    for key, value in runtime.items():
        print(f"  {key}: {value}")
    print(f"\ncontract_id / seed namespace: {args.contract_id}")
    print(f"construction only -- no stepping, no continuations, no estimand\n")

    config = audit.build_config()
    worlds = []
    for seed in args.topologies:
        coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
        for block in args.blocks:
            for index in range(args.episodes):
                episode_seed = audit._derived_seed(
                    topology_seed=seed, block=block, idx=index, tag="episode_seed",
                    contract_id=args.contract_id)
                user_seed = audit.user_world_seed(
                    topology_seed=seed, block=block, episode_index=index,
                    contract_id=args.contract_id)
                env = audit.build_pinned_env(
                    config, episode_seed=episode_seed, coords=coords,
                    coord_hash=coord_hash, energy_stage=args.energy_stage,
                    user_world_seed=user_seed)
                record = audit.episode_world_fingerprint(env, seed_value=user_seed)
                entry = {
                    "topology_seed": seed, "block": block, "episode_index": index,
                    "episode_seed": episode_seed,
                    "user_world_seed": record["user_world_seed"],
                    "pinned_coordinate_hash": record["pinned_coordinate_hash"],
                    "n_users": record["n_users"],
                    "fingerprint": record["fingerprint"],
                    "component_digests": record["component_digests"],
                    "seed_controls_generation": record["seed_controls_generation"],
                }
                worlds.append(entry)
                print(f"  {seed} {block:11s} ep{index}  fp={record['fingerprint'][:16]}  "
                      f"components={len(record['component_digests'])}")

    print(f"\n{len(worlds)} episode worlds constructed")
    if args.out:
        # Written in the same shape the audit artifact uses, so
        # d7_s_world_component_digest_diff.py reads either without a special case.
        payload = {"episode_world_provenance": {"episode_worlds": worlds},
                    "runtime_identity": runtime,
                    "contract_id": args.contract_id,
                    "probe": "d7_s_world_digest_probe"}
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        print(f"wrote {args.out}")
    print("\nWORLD_DIGEST_PROBE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
