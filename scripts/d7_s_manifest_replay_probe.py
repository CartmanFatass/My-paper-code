"""Produce one runner's evidence that manifest replay reproduces an episode.

Ordered by the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_provenance_correction_result/`, §6),
which held that the existing conformance gate tests the wrong mechanism:

    `d7_s_world_conformance_gate.py` compares independently generated
    `episode_world_provenance` records. It does not load the same manifest on two
    runners, apply it to two environments, compare post-application readback,
    compare rebuilt derived state, or exercise a complete episode or
    continuation. It remains a useful generator diagnostic [...] It is not the
    Route A acceptance gate.

This script is the PRODUCER. It emits one artifact per runner;
`d7_s_manifest_replay_gate.py` compares two of them. Splitting producer from
comparator is not tidiness: the comparison must be able to run anywhere, on
artifacts from machines that never met.

WHY THE HORIZON EXERCISE IS NOT OPTIONAL. An initial-state manifest fixes `t = 0`.
`_update_user_positions_rpgm` and `_update_cluster_centers_rpgm` re-enter
`np.cos`/`np.sin` whenever a user or cluster centre reaches its waypoint, so a
replay can agree perfectly at step 0 and diverge by step 40. The ruling's words:

    The last assertion is required because initial replay can pass while later
    RPGM trigonometric updates diverge.

DEVELOPMENT ONLY. This refuses to touch a topology in the frozen R4 population.
No confirmatory population may be selected, generated or inspected until the gate
passes, and a probe that ran over R4 seeds would have inspected one.

    python scripts/d7_s_manifest_replay_probe.py --mode capture --manifest-root dev_manifests
    python scripts/d7_s_manifest_replay_probe.py --mode replay  --manifest-root dev_manifests \\
        --out replay_a.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit_d7_s_event_aligned as audit  # noqa: E402
import d7_s_world_manifest as wm  # noqa: E402

DEVELOPMENT_CONTRACT_ID = "D7_S_MANIFEST_REPLAY_DEVELOPMENT"

# The eight assertions the ruling requires of a formal manifest gate, named so an
# artifact can say which ones it actually carries. A gate that reports PASS
# without naming its coverage is the two-outcome failure in another costume.
ASSERTIONS = (
    "a1_sidecar_identity_equals_expected",
    "a2_complete_set_shapes_and_dtypes",
    "a3_digests_match_before_application",
    "a4_post_application_readback",
    "a5_derived_state_postcondition",
    "a6_complete_pre_step_environment_identity",
    "a7_no_registered_randomness_consumed",
    "a8_full_horizon_equality",
)

# a8 is the only assertion this probe cannot complete alone: it is a CROSS-RUNNER
# equality, so the probe records the digests and the gate does the comparing.
LOCAL_ASSERTIONS = ASSERTIONS[:7]


class ReplayProbeError(RuntimeError):
    pass


def _canonical_digest(value) -> str:
    """A digest over an arbitrary JSON-able structure, stable across processes.

    `sort_keys` and `default=repr` between them make this total: a numpy scalar
    that would otherwise raise gets its repr, which is deterministic, rather than
    silently dropping the field the way a lenient encoder would.
    """
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=repr,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _world_component_digests(env) -> dict:
    out = {}
    for name in audit.WORLD_COMPONENT_ORDER:
        value = getattr(env, name, None)
        if value is None:
            out[name] = "<absent>"
            continue
        arr = np.ascontiguousarray(np.asarray(value))
        out[name] = wm._digest_component(name, arr)
    return out


def refuse_confirmatory_topology(topology_seed: int) -> None:
    """The ruling holds the confirmatory population unselected AND uninspected.

    Running this probe over an R4 seed would generate and read its worlds, which
    is exactly what §4 forbids -- and it would do it while looking like apparatus
    work rather than population consumption.
    """
    if int(topology_seed) in set(audit.TOPOLOGY_SEEDS_R4):
        raise ReplayProbeError(
            f"topology {topology_seed} is in the frozen R4 population. The ruling "
            f"forbids constructing, generating or inspecting confirmatory worlds "
            f"until the manifest gate passes. Use TOPOLOGY_SEED_DEV "
            f"({audit.TOPOLOGY_SEED_DEV}).")


def episode_identity(*, topology_seed: int, block: str, idx: int, contract_id: str) -> dict:
    """The registered per-episode seeds, derived exactly as the audit derives them.

    Re-derived rather than passed in, because the whole defect class here is a key
    that names one thing and identifies another.
    """
    return {
        "episode_seed": audit._derived_seed(topology_seed=topology_seed, block=block,
                                            idx=idx, tag="episode_seed",
                                            contract_id=contract_id),
        "energy_seed": audit._derived_seed(topology_seed=topology_seed, block=block,
                                           idx=idx, tag="energy_seed",
                                           contract_id=contract_id),
        "user_world_seed": audit.user_world_seed(topology_seed=topology_seed, block=block,
                                                 episode_index=idx,
                                                 contract_id=contract_id),
    }


# ------------------------------------------------------------------ capture --

def capture_development_manifests(*, manifest_root: str, topology_seed: int,
                                   episodes: int, block: str, energy_stage: str,
                                   contract_id: str) -> dict:
    """Generate the development world ONCE and freeze it, inventory included.

    This is the only place a world is generated. Everything downstream loads.
    """
    refuse_confirmatory_topology(topology_seed)
    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=topology_seed,
                                                       energy_stage=energy_stage)
    manifests = []
    for idx in range(int(episodes)):
        seeds = episode_identity(topology_seed=topology_seed, block=block, idx=idx,
                                 contract_id=contract_id)
        env = audit.build_pinned_env(config, episode_seed=seeds["episode_seed"],
                                     coords=coords, coord_hash=coord_hash,
                                     energy_stage=energy_stage,
                                     user_world_seed=seeds["user_world_seed"])
        manifest = wm.world_manifest_from_env(
            env, contract_id=contract_id, topology_seed=topology_seed, block=block,
            episode_index=idx, user_world_seed=seeds["user_world_seed"])
        wm.save_world_manifest(manifest_root, manifest)
        manifests.append(manifest)
    inventory_path = wm.write_manifest_inventory(manifest_root, manifests)
    report = wm.verify_manifest_inventory(manifest_root)
    return {"inventory_path": inventory_path, "set_hash": report["set_hash"],
            "episode_count": report["episode_count"],
            "coordinate_hash": coord_hash, "topology_seed": int(topology_seed)}


# ------------------------------------------------------------------- replay --

def replay_one_episode(config, *, manifest_root: str, topology_seed: int, block: str,
                       idx: int, coords: dict, coord_hash: str, energy_stage: str,
                       n_select: int, n_eval: int, contract_id: str,
                       run_horizon: bool) -> dict:
    """One episode, replayed from the manifest, with assertions 1-7 checked here.

    The env is built with `user_world_seed=None` ON PURPOSE. That path leaves the
    world at whatever construction produced -- which is precisely the
    non-identifying state the manifest exists to replace -- so the readback proves
    the manifest OVERWROTE a different world rather than agreeing with one that
    happened to match.
    """
    refuse_confirmatory_topology(topology_seed)
    seeds = episode_identity(topology_seed=topology_seed, block=block, idx=idx,
                             contract_id=contract_id)

    env = audit.build_pinned_env(config, episode_seed=seeds["episode_seed"],
                                 coords=coords, coord_hash=coord_hash,
                                 energy_stage=energy_stage, user_world_seed=None)
    before = _world_component_digests(env)

    expected = wm.expected_identity(
        contract_id=contract_id, topology_seed=topology_seed, block=block,
        episode_index=idx, pinned_coordinate_hash=coord_hash,
        user_world_seed=seeds["user_world_seed"],
        generator_version_hash=wm.generator_version(env),
        n_users=int(env.n_users), n_clusters=int(env.n_clusters))

    outcome = {"topology_seed": int(topology_seed), "block": block,
               "episode_index": int(idx),
               "episode_seed": int(seeds["episode_seed"]),
               "user_world_seed": int(seeds["user_world_seed"]),
               "assertions": {name: False for name in ASSERTIONS},
               "failure": None}

    # a1 + a2 + a3 -- load compares identity, layout and digests, and refuses.
    manifest = wm.load_world_manifest(manifest_root, expected=expected)
    outcome["assertions"]["a1_sidecar_identity_equals_expected"] = True
    outcome["assertions"]["a2_complete_set_shapes_and_dtypes"] = True
    outcome["assertions"]["a3_digests_match_before_application"] = True
    outcome["manifest_payload_hash"] = manifest["payload_hash"]

    # a4 + a5 + a7 -- apply reads back, rebuilds derived state, and proves the
    # rebuild drew nothing from the continuation stream.
    report = wm.apply_world_manifest(env, manifest)
    outcome["assertions"]["a4_post_application_readback"] = True
    outcome["assertions"]["a5_derived_state_postcondition"] = (
        list(report["derived_state_rebuilt"]) == list(wm.DERIVED_STATE_REBUILD))
    outcome["assertions"]["a7_no_registered_randomness_consumed"] = bool(
        report["rng_state_unchanged"])
    outcome["derived_state_rebuilt"] = report["derived_state_rebuilt"]

    after = _world_component_digests(env)
    outcome["replaced_a_different_world"] = any(
        before[name] != after[name] for name in audit.WORLD_COMPONENT_ORDER)

    # a6 -- the COMPLETE pre-step environment identity, not only the nine arrays.
    # `full_state_fingerprint` covers the continuation-sensitive surfaces the nine
    # arrays do not: battery, charging, station queues, duty map, lifecycle mask.
    outcome["episode_world_fingerprint"] = audit.episode_world_fingerprint(
        env, seed_value=seeds["user_world_seed"])["fingerprint"]
    outcome["pre_step_state_fingerprint"] = audit.full_state_fingerprint(env)
    outcome["assertions"]["a6_complete_pre_step_environment_identity"] = True

    if not run_horizon:
        outcome["horizon"] = None
        return outcome

    # a8's INPUTS. The equality itself is cross-runner and belongs to the gate;
    # what this side can do is execute the registered horizon and digest the four
    # surfaces the ruling names.
    energies = audit.draw_energy_permutation(energy_seed=seeds["energy_seed"])
    audit.apply_energy_profile(env, energies)
    prefix = audit.roll_prefix_and_find_event(env)

    horizon = {
        "event_found": prefix["event"] is not None,
        "roll_power": prefix.get("roll_power", {}),
        "rejected_counts": prefix.get("rejected_counts", {}),
        # bullet 1: exogenous user/cluster trajectory, read off the arrays AFTER
        # the roll -- every RPGM waypoint regeneration in between is folded in,
        # which is exactly the trig re-execution an initial manifest cannot fix
        "post_roll_world_digests": _world_component_digests(env),
    }

    if prefix["event"] is not None:
        event = prefix["event"]
        snapshot = audit.capture_event_snapshot(env, coord_hash=coord_hash, event=event)
        # bullet 2: event and candidate identity
        horizon["event_conformance_digest"] = _canonical_digest(event["conformance_record"])
        horizon["duty_map_at_te_digest"] = _canonical_digest(event["duty_map_at_te"])
        horizon["snapshot_state_hash"] = snapshot.state_hash if hasattr(
            snapshot, "state_hash") else None
        # bullets 3 and 4: primary-G component series and branch-relevant
        # quantities both live inside the per-limb units, over the registered
        # stable (139) and flex (550) horizons
        unit_stable = audit.run_audit_event(
            snapshot=snapshot, topology_seed=topology_seed,
            episode_seed=seeds["episode_seed"], event=event, limb="stable",
            n_select=n_select, n_eval=n_eval, event_index=idx, contract_id=contract_id)
        unit_flex = audit.run_audit_event(
            snapshot=snapshot, topology_seed=topology_seed,
            episode_seed=seeds["episode_seed"], event=event, limb="flex",
            n_select=n_select, n_eval=n_eval, event_index=idx, contract_id=contract_id)
        horizon["unit_stable_digest"] = _canonical_digest(unit_stable)
        horizon["unit_flex_digest"] = _canonical_digest(unit_flex)
        horizon["unit_stable_invalid"] = bool(unit_stable.get("event_invalid"))
        horizon["unit_flex_invalid"] = bool(unit_flex.get("event_invalid"))
        horizon["horizons_executed"] = {"stable": audit.H_STABLE, "flex": audit.H_FLEX}

    outcome["horizon"] = horizon
    return outcome


def run_probe(*, manifest_root: str, topology_seed: int, block: str, episodes: int,
              energy_stage: str, n_select: int, n_eval: int, contract_id: str,
              run_horizon: bool) -> dict:
    refuse_confirmatory_topology(topology_seed)
    inventory = wm.verify_manifest_inventory(manifest_root)

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=topology_seed,
                                                       energy_stage=energy_stage)
    episodes_out = []
    for idx in range(int(episodes)):
        episodes_out.append(replay_one_episode(
            config, manifest_root=manifest_root, topology_seed=topology_seed, block=block,
            idx=idx, coords=coords, coord_hash=coord_hash, energy_stage=energy_stage,
            n_select=n_select, n_eval=n_eval, contract_id=contract_id,
            run_horizon=run_horizon))

    return {
        "kind": "d7_s_manifest_replay_probe",
        "schema_version": wm.SCHEMA_VERSION,
        "contract_id": contract_id,
        "topology_seed": int(topology_seed),
        "coordinate_hash": coord_hash,
        "block": block,
        "manifest_set_hash": inventory["set_hash"],
        "manifest_episode_count": inventory["episode_count"],
        "horizon_executed": bool(run_horizon),
        "assertion_names": list(ASSERTIONS),
        "episodes": episodes_out,
        "runtime_identity": audit.runtime_identity(),
        "job_identity": job_identity(),
    }


def job_identity() -> dict:
    """Who ran this, independently of what CPU it landed on.

    The ruling's amendment to my own gate design: for manifest REPLAY, two
    independently provisioned runners using the same immutable bytes are
    meaningful evidence even when their CPU model strings match. An inability to
    obtain two CPU models from a homogeneous hosted fleet must not create a
    permanent UNTESTED for a byte-replay mechanism -- so identity here is the JOB,
    which is always distinct, not the hardware, which may not be.
    """
    keys = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_JOB", "GITHUB_ACTION",
            "RUNNER_NAME", "GITHUB_SHA", "GITHUB_REF_NAME")
    out = {key.lower(): os.environ.get(key) for key in keys}
    out["hostname"] = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME")
    out["pid"] = os.getpid()
    out["wall_clock_start"] = time.time()
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("capture", "replay"), required=True)
    parser.add_argument("--manifest-root", required=True)
    parser.add_argument("--topology-seed", type=int, default=audit.TOPOLOGY_SEED_DEV)
    parser.add_argument("--block", default="audit")
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--energy-stage", default="S3")
    parser.add_argument("--n-select", type=int, default=audit.N_SELECT)
    parser.add_argument("--n-eval", type=int, default=audit.N_EVAL)
    parser.add_argument("--contract-id", default=DEVELOPMENT_CONTRACT_ID)
    parser.add_argument("--no-horizon", action="store_true",
                        help="skip the full-horizon exercise. Assertion 8 is then "
                             "UNCOVERED and the gate will say so.")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if args.mode == "capture":
        report = capture_development_manifests(
            manifest_root=args.manifest_root, topology_seed=args.topology_seed,
            episodes=args.episodes, block=args.block, energy_stage=args.energy_stage,
            contract_id=args.contract_id)
        print(json.dumps(report, indent=2))
        return 0

    report = run_probe(
        manifest_root=args.manifest_root, topology_seed=args.topology_seed,
        block=args.block, episodes=args.episodes, energy_stage=args.energy_stage,
        n_select=args.n_select, n_eval=args.n_eval, contract_id=args.contract_id,
        run_horizon=not args.no_horizon)

    failed = [
        (e["topology_seed"], e["episode_index"], name)
        for e in report["episodes"] for name in LOCAL_ASSERTIONS
        if not e["assertions"][name]
    ]
    for key in failed:
        print(f"LOCAL ASSERTION FAILED  {key}")
    print(f"episodes={len(report['episodes'])} local_assertion_failures={len(failed)}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, default=repr)
        print(f"wrote {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
