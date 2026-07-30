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

import audit_d7_s_event_aligned as audit  # noqa: E402

# A sentinel distinct from `None`: a required field that is PRESENT and holds
# `None` is a defect (§5.4); a required field that is ABSENT is a different
# defect. `dict.get(field, _ABSENT)` tells the two apart.
_ABSENT = object()

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

# Ruling 2026-07-30 §5.4: a required horizon field missing on either side, or
# `None` on either side, is UNTESTED -- never silently skipped (the old
# `if field not in ha and field not in hb: continue` let a whole surface go
# uncompared) and never treated as a witness merely because it agrees.
# `snapshot_state_hash` is deliberately NOT here: `EventSnapshot` exposes no
# public `state_hash` attribute today, so the probe now drops the key entirely
# rather than recording `None` on both sides (§8 action 4) -- forcing it into
# REQUIRED would make this gate permanently UNTESTED for a reason that has
# nothing to do with replay.
REQUIRED_HORIZON_FIELDS = (
    "event_found",
    "post_roll_world_digests",
    "event_conformance_digest",
    "duty_map_at_te_digest",
    "unit_stable_digest",
    "unit_flex_digest",
    # §2 Gap 2 -- per-step lossless exogenous trajectory digests through BOTH
    # continuation forks, not merely the prefix roll `post_roll_world_digests`
    # already covers.
    "continuation_stable_digest",
    "continuation_flex_digest",
)

# Compared for equality when both sides carry it. Absence on either or both
# sides is not itself evidence of anything (§5.4) -- unlike a REQUIRED field.
OPTIONAL_HORIZON_FIELDS = ("snapshot_state_hash",)

HORIZON_EQUALITY_FIELDS = REQUIRED_HORIZON_FIELDS + OPTIONAL_HORIZON_FIELDS

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
    liveness_witnessed = False
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
                detail = f"{str(a.get(field))[:16]} != {str(b.get(field))[:16]}"
                if field == "pre_step_state_fingerprint":
                    named = _differing_attributes(a.get("pre_step_state_attribute_digests"),
                                                  b.get("pre_step_state_attribute_digests"))
                    if named is not None:
                        detail = (f"{len(named)} of {len(a.get('pre_step_state_attribute_digests') or {})} "
                                  f"attribute(s): {', '.join(named[:8])}")
                failures.append({"episode": list(key), "surface": field,
                                 "detail": detail,
                                 "differing_attributes": (
                                     _differing_attributes(
                                         a.get("pre_step_state_attribute_digests"),
                                         b.get("pre_step_state_attribute_digests"))
                                     if field == "pre_step_state_fingerprint" else None)})
        if horizon:
            ha, hb = a.get("horizon") or {}, b.get("horizon") or {}

            # §5.4 -- fail closed on missing/None BEFORE comparing anything, and
            # never let a required field fall through to the equality loop below
            # once it has already been reported absent.
            missing_required = set()
            for field in REQUIRED_HORIZON_FIELDS:
                va, vb = ha.get(field, _ABSENT), hb.get(field, _ABSENT)
                if va is _ABSENT or vb is _ABSENT or va is None or vb is None:
                    missing_required.add(field)

                    def _state(v):
                        return "missing" if v is _ABSENT else ("None" if v is None else "present")

                    untested.append(
                        f"episode {key}: required horizon field {field!r} is "
                        f"{_state(va)} on left and {_state(vb)} on right -- "
                        f"absence is UNTESTED, not equality")

            for field in HORIZON_EQUALITY_FIELDS:
                if field in missing_required:
                    continue
                if field not in ha and field not in hb:
                    continue  # optional field neither side carries (§5.4)
                if ha.get(field) != hb.get(field):
                    detail = f"{str(ha.get(field))[:16]} != {str(hb.get(field))[:16]}"
                    if field == "post_roll_world_digests":
                        first = _first_differing_component(ha.get(field), hb.get(field))
                        detail = f"first differing component after the roll: {first}"
                    failures.append({"episode": list(key), "surface": field,
                                     "detail": detail})

            # §8 action 6 -- event_found must actually be True on both sides, not
            # merely equal (two probes that both found nothing would otherwise
            # "agree").
            if ha.get("event_found") is not True or hb.get("event_found") is not True:
                untested.append(
                    f"episode {key}: event_found is not True on both sides "
                    f"(left={ha.get('event_found')!r} right={hb.get('event_found')!r})")

            # Both recorded audit units must be valid.
            for side_name, h in (("left", ha), ("right", hb)):
                if h.get("unit_stable_invalid") or h.get("unit_flex_invalid"):
                    untested.append(
                        f"episode {key}: {side_name} probe recorded an invalid audit "
                        f"unit (unit_stable_invalid={h.get('unit_stable_invalid')!r} "
                        f"unit_flex_invalid={h.get('unit_flex_invalid')!r})")

            # Stable and flex horizons -- both the certified-event units and the
            # continuation-trajectory exercise -- must equal the registered
            # lengths, not merely agree with each other at the wrong length.
            for side_name, h in (("left", ha), ("right", hb)):
                executed = h.get("horizons_executed") or {}
                if executed.get("stable") != audit.H_STABLE or executed.get("flex") != audit.H_FLEX:
                    untested.append(
                        f"episode {key}: {side_name} probe's horizons_executed "
                        f"{executed!r} does not equal the registered lengths "
                        f"(stable={audit.H_STABLE}, flex={audit.H_FLEX})")
                if h.get("continuation_stable_steps") != audit.H_STABLE:
                    untested.append(
                        f"episode {key}: {side_name} probe's continuation_stable_steps "
                        f"{h.get('continuation_stable_steps')!r} != registered "
                        f"H_STABLE={audit.H_STABLE}")
                if h.get("continuation_flex_steps") != audit.H_FLEX:
                    untested.append(
                        f"episode {key}: {side_name} probe's continuation_flex_steps "
                        f"{h.get('continuation_flex_steps')!r} != registered "
                        f"H_FLEX={audit.H_FLEX}")

            # §2 Gap 3 -- a positive liveness witness on AT LEAST ONE compared
            # episode, either side. Absence must not read as caution.
            if max(
                int(ha.get("post_manifest_user_waypoint_regenerations") or 0),
                int(hb.get("post_manifest_user_waypoint_regenerations") or 0),
                int(ha.get("post_manifest_cluster_target_regenerations") or 0),
                int(hb.get("post_manifest_cluster_target_regenerations") or 0),
            ) > 0:
                liveness_witnessed = True

    if horizon and compared and not liveness_witnessed:
        untested.append(
            "no compared episode recorded a positive post-manifest liveness counter "
            "(post_manifest_user_waypoint_regenerations or "
            "post_manifest_cluster_target_regenerations on either side): if every "
            "relevant generator remained dormant, equality leaves the exact "
            "A1-versus-A2 risk untested")

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


def _differing_attributes(a, b):
    """Name the attributes behind a combined-fingerprint mismatch.

    Returns None when a probe carries no per-attribute record -- an older artifact
    is not a reason to guess, and a guessed surface is worse than an opaque hash.
    """
    if not a or not b:
        return None
    return sorted(name for name in set(a) | set(b) if a.get(name) != b.get(name))


def _first_differing_component(a, b) -> str:
    """Generation order, because an earlier divergence propagates into later ones."""
    a = a or {}
    b = b or {}
    for name in audit.WORLD_COMPONENT_ORDER:
        if a.get(name) != b.get(name):
            return name
    return "<none in WORLD_COMPONENT_ORDER>"


if __name__ == "__main__":
    raise SystemExit(main())
