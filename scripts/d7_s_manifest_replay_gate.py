"""The Route A acceptance gate: does ONE manifest replay to ONE episode, twice?

Ordered by the Pro ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_provenance_correction_result/`, §6).

WHAT MAKES THIS A DIFFERENT GATE FROM `d7_s_world_conformance_gate.py`. That one
asks whether two machines GENERATE the same world, and answers `UNTESTED` when it
cannot prove the machines differed -- correctly, because generator portability is
a claim about hardware. This one asks whether two machines REPLAY the same bytes
into the same episode, and that question does not need distinct hardware:

    For manifest replay, two independently provisioned runners using the same
    immutable bytes provide meaningful evidence even if their CPU model strings
    match. Record distinct workflow job/runner identities. [...] an inability to
    obtain two CPU models from the hosted fleet must not create a permanent
    `UNTESTED` state for a byte-replay mechanism.

That amendment reverses a rule this project wrote itself. Carrying
`RUNTIME_DISCRIMINATORS` across to replay would have produced a gate that a
homogeneous fleet makes UNFALSIFIABLE -- permanently untested, and reading like
caution.

THERE IS NO `--allow-same-runtime` HERE, AND THERE MUST NEVER BE. The ruling:
"The existing `--allow-same-runtime` escape must never exist on the
conclusion-bearing route." A gate with an escape hatch is a gate that will be
escaped at 3am by whoever needs it green.

THREE OUTCOMES, for the reason the generator gate has three:

    MANIFEST_REPLAY_PASS        all eight assertions, both sides, equal digests,
                                independent executions
    MANIFEST_REPLAY_FAIL        a divergence -- decisive, and it names the surface
    MANIFEST_REPLAY_UNTESTED    coverage or independence could not be established

`UNTESTED` exits non-zero. It is not a pass.

    python scripts/d7_s_manifest_replay_gate.py --samples a.json b.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fields whose difference proves two probes were INDEPENDENT EXECUTIONS. Not
# hardware -- see the module docstring. Any one differing is enough.
INDEPENDENCE_FIELDS = ("github_run_id", "github_run_attempt", "github_job",
                       "runner_name", "hostname", "pid")

# Everything the two sides must agree on before a comparison means anything.
SHARED_CONTEXT_FIELDS = ("contract_id", "topology_seed", "coordinate_hash", "block",
                         "manifest_set_hash", "manifest_episode_count")

# The per-episode digests that must be equal. Ordered so the FIRST difference
# reported is the earliest in episode time -- a divergence at t=0 explains one at
# t=550, and never the other way round.
EQUALITY_FIELDS = (
    "manifest_payload_hash",
    "episode_world_fingerprint",
    "pre_step_state_fingerprint",
)

HORIZON_EQUALITY_FIELDS = (
    "event_found",
    "post_roll_world_digests",
    "event_conformance_digest",
    "duty_map_at_te_digest",
    "snapshot_state_hash",
    "unit_stable_digest",
    "unit_flex_digest",
)

LOCAL_ASSERTIONS = (
    "a1_sidecar_identity_equals_expected",
    "a2_complete_set_shapes_and_dtypes",
    "a3_digests_match_before_application",
    "a4_post_application_readback",
    "a5_derived_state_postcondition",
    "a6_complete_pre_step_environment_identity",
    "a7_no_registered_randomness_consumed",
)


def load_probe(path: str) -> dict:
    payload = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if payload.get("kind") != "d7_s_manifest_replay_probe":
        raise SystemExit(
            f"{path} is not a manifest-replay probe artifact (kind="
            f"{payload.get('kind')!r}). The generator-conformance artifacts are a "
            f"different measurement and comparing them here would answer a "
            f"different question.")
    payload["_path"] = path
    return payload


def _index(payload: dict) -> dict:
    return {(e["topology_seed"], e["block"], e["episode_index"]): e
            for e in payload.get("episodes", [])}


def executions_are_independent(left: dict, right: dict) -> tuple:
    a = left.get("job_identity") or {}
    b = right.get("job_identity") or {}
    if not a or not b:
        return False, "at least one probe records no job_identity"
    for field in INDEPENDENCE_FIELDS:
        x, y = a.get(field), b.get(field)
        if x is not None and y is not None and x != y:
            return True, f"{field} differs"
    return False, ("no recorded job field differs, so these may be the same "
                   "execution reported twice")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", nargs=2, required=True,
                        help="two probe artifacts from independent executions")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    left, right = (load_probe(p) for p in args.samples)
    print(f"left  {left['_path']}   {len(left.get('episodes', []))} episode(s)")
    print(f"right {right['_path']}   {len(right.get('episodes', []))} episode(s)")

    untested = []
    failures = []

    for field in SHARED_CONTEXT_FIELDS:
        if left.get(field) != right.get(field):
            untested.append(f"{field} differs ({left.get(field)!r} vs {right.get(field)!r}); "
                            f"the two probes did not replay the same manifest set")

    independent, reason = executions_are_independent(left, right)
    print(f"independent executions: {independent} -- {reason}")
    if not independent:
        untested.append(f"independence not established: {reason}")

    horizon = bool(left.get("horizon_executed")) and bool(right.get("horizon_executed"))
    if not horizon:
        untested.append(
            "assertion a8_full_horizon_equality is UNCOVERED: at least one probe "
            "ran with --no-horizon. Initial replay can pass while later RPGM "
            "trigonometric updates diverge, so this is not a replay result")

    li, ri = _index(left), _index(right)
    shared = sorted(set(li) & set(ri), key=lambda k: (k[0], str(k[1]), k[2]))
    print(f"shared episode keys: {len(shared)}")
    if not shared:
        untested.append("no shared episode keys")
    for missing in sorted(set(li) ^ set(ri)):
        untested.append(f"episode {missing} appears on only one side")

    compared = 0
    for key in shared:
        a, b = li[key], ri[key]
        for side, entry in (("left", a), ("right", b)):
            for name in LOCAL_ASSERTIONS:
                if not entry.get("assertions", {}).get(name):
                    failures.append({"episode": list(key), "surface": name,
                                     "detail": f"{side} probe did not satisfy it"})
        if not a.get("replaced_a_different_world") or not b.get("replaced_a_different_world"):
            # If applying the manifest changed nothing, the env already held that
            # world and the readback proves nothing about replay.
            untested.append(
                f"episode {key}: applying the manifest changed no component, so the "
                f"readback tested agreement with a world that was already there")
        compared += 1
        for field in EQUALITY_FIELDS:
            if a.get(field) != b.get(field):
                failures.append({"episode": list(key), "surface": field,
                                 "detail": f"{str(a.get(field))[:16]} != {str(b.get(field))[:16]}"})
        if horizon:
            ha, hb = a.get("horizon") or {}, b.get("horizon") or {}
            for field in HORIZON_EQUALITY_FIELDS:
                if field not in ha and field not in hb:
                    continue
                if ha.get(field) != hb.get(field):
                    detail = f"{str(ha.get(field))[:16]} != {str(hb.get(field))[:16]}"
                    if field == "post_roll_world_digests":
                        first = _first_differing_component(ha.get(field), hb.get(field))
                        detail = f"first differing component after the roll: {first}"
                    failures.append({"episode": list(key), "surface": field,
                                     "detail": detail})

    print(f"compared {compared} episode key(s)")

    if failures:
        print(f"\n{len(failures)} DIVERGENCE(S)")
        for entry in failures[:20]:
            print(f"  {entry['episode']}  {entry['surface']:32s} {entry['detail']}")
        earliest = failures[0]["surface"]
        verdict = f"MANIFEST_REPLAY_FAIL:{earliest}"
        exit_code = 1
    elif untested:
        print(f"\n{len(untested)} reason(s) this tested less than it appears to:")
        for entry in untested[:20]:
            print(f"  {entry}")
        verdict = "MANIFEST_REPLAY_UNTESTED"
        exit_code = 1
    else:
        print(f"\nall {compared} episode(s) replayed identically across independent "
              f"executions, over the registered stable and flex horizons")
        verdict = "MANIFEST_REPLAY_PASS"
        exit_code = 0

    print(f"\n{verdict}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"verdict": verdict, "compared": compared,
                       "failures": failures, "untested": untested,
                       "independent_executions": independent,
                       "independence_reason": reason,
                       "horizon_executed": horizon,
                       "left": left["_path"], "right": right["_path"],
                       "left_job": left.get("job_identity"),
                       "right_job": right.get("job_identity"),
                       "left_runtime": left.get("runtime_identity"),
                       "right_runtime": right.get("runtime_identity")},
                      handle, indent=2, sort_keys=True, default=repr)
        print(f"wrote {args.out}")
    return exit_code


def _first_differing_component(a, b) -> str:
    """Generation order, because an earlier divergence propagates into later ones."""
    import audit_d7_s_event_aligned as audit
    a = a or {}
    b = b or {}
    for name in audit.WORLD_COMPONENT_ORDER:
        if a.get(name) != b.get(name):
            return name
    return "<none in WORLD_COMPONENT_ORDER>"


if __name__ == "__main__":
    raise SystemExit(main())
