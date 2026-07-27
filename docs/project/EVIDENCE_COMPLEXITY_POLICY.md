# HMASD evidence and scaling complexity policy

```text
policy_kind=user_authorized_hard_workflow_boundary
purpose=stop_unbounded_verification_apparatus_not_unbounded_science
nonformal_wall_clock_cap_minutes=20
formal_iteration_wall_clock_cap=none_user_ruling_20260726
audit_stage_proliferation=forbidden
audit_driven_verification_experiment=forbidden
prelaunch_cost_projection=required_informational_never_a_launch_gate
replicate_volume_cost_expression=O(episodes * events_per_episode * forks_per_event * steps_per_fork)
violation=NON_EXECUTABLE_EVIDENCE_DESIGN
violation_iteration_cost=0
override_authority=user_only_for_one_named_boundary
```

Ported 2026-07-26 from the HMASD-new reference policy by user direction, then
**re-scoped the same day by user ruling** after the first version bound the
wrong thing.

## What this policy is actually for

The original wording capped the conclusion-bearing experiment at eight hours.
That was a misreading of the intent, and the user corrected it: **the scientific
run is not what needs a ceiling.** A real audit that answers the registered
question is worth its wall clock, however long it takes.

What needs a ceiling is the **apparatus around it** — review stages that spawn
more review stages, and the code-verification experiments those stages demand.
That machinery grows without limit if nothing stops it, consumes the compute the
science needs, and produces no scientific claim of its own.

So the boundary moved:

| | Capped? |
|---|---|
| The formal conclusion-bearing experiment (loop step 7) | **No.** No wall-clock cap. |
| Smokes, probes, pilots, rehearsals | Yes — 20 minutes, and sized to the minimum that proves a genuinely untested path |
| Adding another audit/review stage | Forbidden without the workflow value test |
| An experiment run to verify code on behalf of an audit stage | Forbidden |

Every loop step except step 7 is experiment-free by construction. If a stage
that is supposed to be experiment-free starts asking for compute, that is the
defect this policy exists to catch — not a long step 7.

## The nonformal cap stands

The complete nonformal exercise (smoke, probe, pilot) must finish within
**20 minutes** on the registered local CPU, sized to the minimum that proves the
untested path — normally one episode per untested limb. Rehearsal beyond that is
the defect, not diligence.

## Prelaunch cost projection — required, but informational

Before a conclusion-bearing run, the Project Manager still records a cost
projection: episode count, expected qualifying events, forks per event (all arms
x limbs x select/eval replicates), steps per fork (prefix replay + continuation
horizon + guard), and the projected wall clock at the intended sharding width.
`scripts/d7_s_prelaunch_cost_bound.py` is the D7.S instance of this.

It exists so the run's cost is **known and scheduled**, not so it can be
refused. It is no longer a launch gate. When constants are unknown, one
microbenchmark of at most 20 minutes may establish them.

## Audit-stage proliferation

A review or verification stage runs only if it passes the workflow value test in
`AGENTS.md`: name the false scientific assertion it prevents, and confirm its
total packaging, waiting, repair and compute cost is smaller than the waste it
avoids. A stage that cannot name one does not run. `review_stack=false` and
`routine_preimplementation_code_science_review=forbidden` are the standing
expressions of this.

An audit stage may read code, run focused tests, and reason on paper. It may not
commission a training or evaluation run to satisfy itself.

## On violation

A violation is `NON_EXECUTABLE_EVIDENCE_DESIGN`, not a scientific result and not
a failed iteration; it consumes zero conclusion-bearing iterations. It now names
an unbounded *apparatus*, not an expensive experiment. The Project Manager stops
the offending stage at the smallest reproducer and removes it, rather than
shrinking the science to pay for it.

Neither an active grant nor formal-compute authority overrides this policy; only
the user may grant one named exception with a replacement bound.

## Precedent

**2026-07-26, the eight-hour cap and its removal.** The D7.S event-aligned joint
audit as originally frozen (8 topologies x 16 episodes, `n_select=4` /
`n_eval=8`, ~48 forks per event at ~1,100-1,500 steps per fork) projected to 2-4
days wall at 8-way sharding, and the user closed the run. External Pro then
ruled the replicate volume down to the `2/2` scientific floor and accepted
shared-prefix forking, conditioning launch on an eight-hour bound.

The user removed that condition the same day: the projection had become a wall
in front of the only step that produces evidence. Pro's ruling anticipated
exactly this — its over-cap branch waits for "a user-named exception, different
compute, or a newly demonstrated bounded realization", and this is that named
exception. The refuted unit Pro recorded was explicitly scoped "under the user's
eight-hour policy", so removing the policy does not overturn the ruling; it
removes the ruling's premise.

What survives from the episode is the part that was always right: the `2/2`
floor is a scientific finding about the bootstrap, not a cost compromise, and it
stands regardless of available compute. The confirmatory `4/8` route stays where
Pro put it — retained, not reactivated by this exception alone.
