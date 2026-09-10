# UCOPE B04 — complete P61 code specification and CM task

## 1. Deliverable, checkout and ownership

Implement and technically accept the selected action-conditioned opening-duration
B04 on the existing UAV opening-prefix runner. Return the accepted source and
focused test/review evidence for exactly one master7201 pair. The
[P61 Convergence intake](UCOPE_POST_B03_CONVERGENCE_INTAKE_20260908.md#1-decision-and-immutable-source)
and [card](UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md) supply the selected
scientific authority and complete real exposure; implementation runs no science.

Reuse `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch
`codex/ucope`, same CM `/root/dm_ucope_p47_resume/cm_am_ucope_b02_p47`. Accepted
starting research source is `70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`; the
authoring checkout at `475f4452177a98e20fb4c0aedf31a89aee4d8912` has identical
source and the complete accepted Pro answer. Card/spec publication adds docs
only; use its supplied full commit as the actual dispatch start. You are not
alone in the repository; preserve others' changes. CM owns the named code,
checks and index through its explicit-path commit/push; DM pauses overlapping
edits. Do not create an authoring branch or replace this checkout from main.

Owned production paths/entry points:

- `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`: T head creation
  in `arm_copy`, `sample`, `joint_terms`, existing exposure groups/summary.
- `experiments/candidates/ucope/uav_motion_prefix_b01/study.py`: `Config`,
  `declared_masters`, `run_pair`, new single-pair identity/aggregate refusal.
- `scripts/run_ucope_uav_motion_prefix_b01.py`: named `b04` route and early refusal.
- `learner.py` only if minimal argument plumbing is actually necessary; its
  reward, RTG, loss, optimization and held-row semantics are unchanged.

Owned checks: the existing
`tests/experiments/candidates/ucope/uav_motion_prefix_b01/` directory, with one
focused conditional-duration test file if useful. CM owns its new B04 technical
acceptance/review record. DM owns card, science intake, facts, DIRECTION,
owner/audit records and subsequent Root handoff. Environment/adapter/native
source, observation construction, reward, critic architecture/targets and
other directions are not owned. Implementation-relevant literature pointers
are only the verified UTE selected-action dependency and ACAC decision-credit
note in preparation §3; no paper retrieval or framework adoption is assigned.

## 2. Exact T head and private initialization

[Card §3](UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md#3-selected-architecture-and-true-likelihood-credit)
fixes the only architectural change: T's duration input is the same64-component
recurrent feature concatenated with its own actual sampled `tanh(u)`3. Use
**Linear(67,32), Tanh, Linear(32,2)**. With b=100000×seed, construct this head
under a private CPU RNG context seeded **b+12**, ordinary Linear initialization,
then zero only final weights/biases. This must leave common initialization b+11,
global caller RNG and action generators untouched. Common T/G actor/critic
parameters are copied from the same template, then optimizers/trajectories remain
separate. Historical treatment heads remain Linear(64,2), zero initialized,
and historical routes retain their existing default behavior.

New-head counts:2242 parameters, +2112 relative to old T; T total68553, G66311.
G has no duration head. A scientific mode derived from pair`b04` is sufficient;
do not add a tunable head/width/init-seed CLI or generic architecture registry.
Ordinary helper signatures are CM's choice so long as existing callers retain
their original scientific route and B04 receives the declared mode/master.

Sample velocity first, then conditional duration from the same owner's command.
The head is called only for actual opening decisions. Never condition on mean,
fresh/resampled velocity, other-agent action, later displacement, global state
or a searched candidate. No new environment or GRU forward is required.

## 3. Behavior/recomputed density and masking

At T openings use the compound log density
`tanh_log_prob(stored_u, current_mean, log_std) + log pi_d(stored_d | recurrent, tanh(stored_u))`.
The condition is **`tanh(stored_u.detach())`**, detached from any action path;
head parameters and recomputed recurrent features retain gradients. The velocity
density retains its existing Jacobian. Collection and update must agree on the
same stored behavior action, including after policy parameters change.

The new head's density/entropy evaluation uses only the true `duration_mask`
rows. Select those rows before the head forward; if none, call no duration head
and return zero duration contributions. Restore the original logp shape for
agent-compound clipping. Do not run it over all primitive rows and mask after
the expensive forward. No density is assigned to an unsampled held action.
Existing historical density behavior stays intact on p21/p24/b02/b03.

Reuse current `learner.collect_episode` and `update` path: velocity/duration
ownership is per agent, held rows have no fresh action/credit, duration is chosen
once at t0, feedback resumes by t4. Both T/G use `agent_compound`, entropy0.0,
native full RTG, the existing scalar advantage normalization and summed-agent
surrogates averaged over all primitive rows. No denominator, critic/value-target,
optimizer, entropy, recurrent, reward or information change is selected.

## 4. Named B04 route and truthful output

Add pair`b04` with only real master **7201**, derived `agent_compound`, entropy0.0,
and the T sampled-command conditional head. P21/P24 remain joint/entropy.01;
B02 agent-compound/.01 and B03 agent-compound/0 with independent duration.
Wrong real master and `--pair b04 --aggregate ...` are refused before scientific
work or aggregate-input access. Direct `aggregate(..., pair='b04')` also refuses:
B04 has one independent trained pair and no two-pair aggregate.

Real summary binds object`UCOPE-UAV-MOTION-PREFIX-B04`, pair`b04`, masters`[7201]`,
card`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md`,
card section5, grouping`agent_compound`, entropy0.0, and the selected conditional
duration mode/head-init seed. Save the same effective Config in both existing
checkpoints. Each arm's actual lr/objective/exposure remain readable; G must not
be described as owning the T-only head. Do not add another manifest/version layer.

Reuse existing `primary.T_minus_G.mean`, all T/G/H J arrays, episode rows, counts,
opening diagnostics, clock/failure handling, publication/readback and exit route.
DM can calculate T−H from the preserved paired J arrays, as before; no new generic
aggregation or primary writer is needed. Preserve all outcomes, including an
incomplete primary, complete narrower contrasts and actual cap breach.

Extend existing parameter-group exposure narrowly so B04 reports hidden and
zero-initialized final duration layers separately, alongside common_actor,
critic, duration and total. Record parameter counts, initial/final norms and
absolute displacement; an initial-zero subgroup's relative displacement is
undefined/null, not an epsilon-divided effect. Do not alter published historical
exposure bytes or require every group to move. These are the requested actual
learner measurements, not new runtime hooks or standing telemetry.

Existing synthetic/tensor tests may use the new mode through established fake
boundaries. Preserve synthetic mode/identity; no fixture output qualifies as
real B04. No standalone fixture is requested or allocated by this task.

## 5. Original focused acceptance checks

Read card§§2–6 for scientific invariants; evidence-spec§§4,11.4,11.8.6–7 for
actual integrity/failure questions; scope-spec§§4–5 for ordinary implementation
limits. Preserve the actual native-primary and information tests already present.

1. On fixed tensor actions/features, exercise the actual new duration path:
   correct67→32→2 dimensions/counts, exactly uniform initial probabilities,
   separate b+12 initialization without consuming common/action/global RNG.
   An explicitly nonzero test head must make duration probabilities depend on
   the actual command while the same stored action gives matching behavior and
   recomputed joint terms. Test the meaningful likelihood boundary: duration
   credit reaches head/recurrent features but not the detached conditioning
   action. Avoid requiring all parameters to move or a policy-performance test.
2. Through actual masks and collector/update interfaces, check no new-head call
   on non-opening/held rows, the selected opening-row count, correct original
   logp shape/agent-compound grouping, and ordinary t1/t4 ownership. Reuse existing
   hold/RTG/primary checks rather than recreating the environment or trainer.
3. Extend the existing fake-workload Config/CLI/run_pair tests to check b04/7201,
   both arms' entropy/grouping, T-only conditioning, private init seed, same
   final reset/stream law, checkpoints/summary identities and counts. Verify
   wrong-master and direct/CLI single-pair aggregate refusals without a real
   UAV call. Historical routing tests remain. Check the zero-initial layer's
   exposure summary truthfully retains absolute movement/undefined ratio.
4. One independent review covers actual-command conditional density, detached
   stored-action gradients, opening/held credit, RNG isolation, native reward/
   actor-information/primary boundaries, truthful mode and scope. Reuse the
   existing available reviewer context where useful. It supplies engineering
   findings, not an empirical result or new scientific selection.

One affected-directory suite, **≤300s total**, after implementation:

```text
python -m pytest -q -p no:cacheprovider --basetemp temp/directions/ucope/test/uav-motion-prefix-b04-p61 tests/experiments/candidates/ucope/uav_motion_prefix_b01
```

Use the declared interpreter: local
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` for short checks; after exact
source is committed/pushed, a portable longer suite uses configured remote
`/home/wu/.venvs/hmasd/bin/python` in its detached exact-SHA checkout. Record
actual placement and wall time, without upgrading either environment. Repeat
only for a concrete correction and record cumulative directory time. No separate
smoke/warm-up/profile/benchmark/pilot/replay or scientific invocation is selected.
An initial source commit used for remote checking is not technical acceptance.

## 6. Engineering budget and later collection boundary

Engineering scope§4: none; source≤2000 new lines and runner≤600 lines. The30%
orchestration share is a review signal, not an automatic refusal or census task.
Return unrequested machinery as a diff concern rather than accepting it as a
price of the result. The bounded head and existing metadata need no new execution,
recovery, schema, fingerprint, scheduler, profiler or benchmark service.

CM implementation/review has **zero scientific invocations**. Complete the
useful bounded deliverable, required independent review and focused acceptance,
then explicit-path commit/push and return exact source plus evidence, or a
concrete unresolved gap. Preserve historical smoke/command failures at their
original meaning. The three CM comparison batches are complete; no fourth
enrollment or historical replay is authorized.

After DM accepted-source binding, Root's existing P61 route permits one detached
remote7201 T/G/H invocation at accepted committed/pushed bytes:286720 team steps,
2048 Adam calls,96 final episodes,1800s/arm and3600s complete publication/exit.
Fresh actual-node admission precedes scientific roots/models. Root stages,
launches and observes; the same CM collects/technically accepts; DM interprets
all outcomes. No retry, replacement master, second pair, extra H completion or
evaluation, tuning or cap growth is allocated. CM never independently relaunches
an accepted handle. Each final outcome exhausts this allocation.

## 7. Complete five-item dispatch

- **Deliverable:** implement and technically accept the selected B04 conditional
  opening-duration comparison, returning exact source for one7201 pair.
- **Owned paths/entry points:** §1's policy/study/runner, learner only if necessary,
  existing focused checks and B04 technical/review record in the same checkout.
- **Preserved semantics:** card§§2–6 and specification§§2–4; true stored-action
  conditional likelihood, real native learning/primary and historical routes.
- **Acceptance:** §5's original dependency/mask/RNG/identity/output checks, one
  ≤300s directory suite and independent high-impact action/credit review.
- **Budget/stop:** §6 and card§6; no scientific run during implementation; return
  accepted explicit-path source commit/push and evidence or the exact blocker.

Root receives this complete committed task/spec/card/source and original checks
before the reused CM starts. Record the completed-three-batches exclusion once;
do not hold ordinary work on a fourth comparison or a new Portfolio vote.
