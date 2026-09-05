# B01 implementation and focused-check contract

CM implementation base: `7c4f2c6bc`; frozen science card and CM handoff at that commit.
This task implements the new N7 direct-return B, not R03/E01 or historical verification systems.
Source acceptance and the non-target engineering check do not establish a scientific B result.

## Ownership and protected behavior

Write ownership is `scripts/run_vnfc_n7_direct_b01.py`,
`experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`, corresponding tests,
and this object's direction-local engineering records. Existing R01/R02/R09/headroom and
shared core remain read-only. Semantic implementer works in its own branch; CM integrates
and an independent reviewer inspects the complete source. Scope-spec section 4 additions: none.
Ordinary source limit 2,000 lines, runner limit 600 lines; orchestration ratio is a review signal.

Preserve N7 survivors from eight pre-loss entities, six post-loss joint decisions, 240 total
native ticks including prehistory, original native service/demand endpoints, and unshaped
`0.5 R_fail_60 + 0.5 U_total`. Preserve R02 canonical opaque-rank policy sorting, forced-command
replay and inverse physical action mapping. Both actual learners receive the same public
observation fields; world tapes and administrative identities do not enter actors. BCRH is
fixed, executes its complete intrinsic controller/checker, and supplies no training labels.

Use CPU binary64, one scientific process, single-thread Torch/BLAS and serial native stepping.
Batch independent same-N7 episodes/tensors only; autoregressive token and episode time order
remain sequential. Task-local trajectories own mutable state. Keep actual existing GAE/PPO and
AdamW values: gamma 1, lambda .95, population advantage normalization, four epochs, minibatch24,
ratio clip [.8,1.2], value coefficient .5, entropy coefficient .01, learning rate .0003,
betas (.9,.999), epsilon 1e-8, matrix decay .0001/plain decay zero, gradient clip .5.

Formal inputs remain namespace `VNFC-N7-DIRECT-RETURN-B01-20260905`, train seed2026090501,
eval seed2026090502, 64 rounds of 32 episodes per arm (16/zone), 192 transitions/round,
32 optimizer steps/round, 2,048 steps/arm. Initial/32/64 evaluation uses the same 64 fresh
episodes (32/zone); BCRH evaluates these once. Preserve readable initial/mid/final checkpoints,
per-episode primary/context outcomes, actual exposure and DIRECT residual observations.
Final checkpoint remains primary; no selection on observed performance.

## One necessary non-target focused check

Prospectively fixed non-target inputs: namespace `B01-ENGINEERING-CHECK`, training seed2026090591,
evaluation seed2026090592; two rounds of 32 complete episodes per learner, balanced16/zone;
eight fresh evaluation episodes (four/zone), reused at initial/round1/round2; BCRH once on eight.
PPO remains four epochs with minibatch24, hence64 actual steps per arm. This exercises the same
collection, update, evaluation and publication path with non-target seeds. Required observations
include action/entity/mask mapping for both failed zones and both models, forced-command replay,
native complete terminal and endpoint-derived primary/context metrics, actual optimizer work,
checkpoint/summary/episode readback. It does not compare every intermediate bit or all histories.

Execute on configured `wsl_4070`, CPU path only, exact committed and pushed source in a detached
remote worktree. One detached `agent-task` command joins destination `admit-memory` (both 4GiB
floors) and the check by `&&`. Freeze the implemented exact argv, output root and launch SHA
in this record before invoking it. No uncommitted source copy or formal target pre-run.
Focused-check wall bound: 300 seconds including import, single-job build, both learner paths,
BCRH and readable publication. Stop on a concrete failure or bound; preserve partial facts,
do not automatically relaunch or change inputs. Existing directory test budget remains five
minutes excluding runner smoke; no second smoke solely at formal launch.

## Cost and collection boundary

Measure actual shared build/import/setup, collection, PPO update, evaluation, BCRH and publication
wall in this necessary check. For each arm project the full card's 2,048 collection episodes,
64 update rounds and192 evaluation episodes using observed corresponding complete units;
add64 complete BCRH episodes, shared preparation once and required publication. Uncovered costs
remain unknown, not zero. Projection is an estimate conditional on this node and source, not
the formal run's measured wall. Old Windows R02 outer walls626.079/691.121/584.934 seconds are
historical two-arm N3/N5 evidence, not new per-arm projections; E01 timing is not learner cost.

The formal complete invocation is capped at2,700 wall seconds across both arms plus BCRH,
imports/build/setup and publication. No extra cost A, configurations, thread teams or budget
are selected. CM returns implementation, independent review, focused-check facts, complete
cost projection with uncertainty and the exact formal command to Root/DM before formal execution.
An unowned dependency, missing primary correctness or over-cap plan returns as that concrete
engineering gap without dropping an arm or reinterpreting scientific feasibility.
