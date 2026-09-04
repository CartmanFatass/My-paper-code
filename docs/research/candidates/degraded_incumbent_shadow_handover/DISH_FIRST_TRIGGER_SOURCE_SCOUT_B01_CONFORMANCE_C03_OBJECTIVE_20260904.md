# DISH B01 production conformance C03 — fresh CM objective

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Evidence class and claim ceiling: unchanged **B — EXPLORE**; this engineering attempt has no
  scientific claim
- Frozen science card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- Prior engineering authority:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_OBJECTIVE_20260904.md`
- Terminal prior intake:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_C02_INTAKE_20260904.md`
- Clean source baseline inspected by the DM: `8025a9f955447c7e3539a678e6cae2e62e8fda72`
- Frozen: `2026-09-04T09:47:02-07:00`, before a new implementation, test, cost command,
  resource admission, checkpoint, or scientific invocation

## 1. Actual boundary and objective

The C01/C02 implementation remains quarantined and uncommitted. Its production changes passed an
independent static review with no material finding, four existing regressions, and three focused
categories; the mandatory smoke then stopped before its branch loop and cost subprocess because
the test-only C02 edit removed `import numpy as np` while retaining an `np.float32` use. The
prospective C02 terminal rule correctly stopped that chain. No scientific root, seed master,
learner, checkpoint, panel endpoint, result summary, admission receipt, or accepted cost row exists.

At the clean baseline above, the five tracked production surfaces are byte-identical to the C01
objective baseline `38429fb7e18781b874a079ddc023bfde7995f3cc`. The quarantined implementer
worktree at
`C:/Projects/HMASD-worktrees/impl-dish-b01-conformance-20260904` is therefore a read-only reuse
candidate, not current authority and not a patch to accept wholesale.

**C03 objective:** on a fresh branch and worktree from this committed objective, inspect and reuse
only the meaning-complete C01/C02 semantic changes that still satisfy this objective, retain the
required NumPy import in the final smoke, and produce one technically accepted B01 implementation.
Every carried line is reviewed as C03 code. C03 does not reinterpret the prior failed suite or
rewrite its rule.

## 2. Scientific comparison held fixed

All scientific meaning remains verbatim from the B01 card:

- treatment: `TRANSFER_SHADOW`, promoting the pre-warmed standby hidden state after the common
  atomic transfer;
- strongest same-information comparator: `TRANSFER_COPY`, the identical owner/actuator remap,
  cost, checkpoint, prefix, observations, and future tape with incumbent-state copy promoted;
- shell-matched control: `RETAIN`, consuming the same intent and transaction shell/cost while
  retaining owner and hidden placement;
- population: seeds `11`, `29`, `47`; one 64-update STRUCTURED checkpoint per seed; the exact
  sixteen rows from packages `{TARGET_VISUAL_MASK,TERRAIN_RELAY_MASK}`, schedules
  `{K8,K4_TO_K12}`, speeds `{4,8}`, and within-speed slots `{0,3}` at block `0` with degradation
  on; and
- estimands, endpoints, trigger-support/nonharm definitions, and ordered result branches
  `FTS-B0`, `FTS-BH`, `FTS-BS`, `FTS-BR`, `FTS-BC`, `FTS-BN`, `FTS-BU` are unchanged.

The causal cut remains after application arrivals and accepted snapshot assimilation, before CAS
and before the application-tick GRU forward. C03 may not move it, force a natural trigger, add a
replay arm, change a seed/row/budget, or revive any R02 root, certificate, production stack, or
result vocabulary.

## 3. Production and learner semantics held fixed

The complete C01 objective remains incorporated. In particular:

1. recurrent copies are `[U0-I,U0-S,U1-I,U1-S]`, with owner/standby role-indexed motion,
   prepare, commit, prediction, snapshot, and promotion for both live collection and PPO replay;
2. collection retains the exact normalized actor input, per-tick owner, reset mask, action facts,
   and detached four-copy hidden state at every 64-tick fragment entrance; replay does not start
   from zero or use a subsequent observation;
3. behavior and old-policy replay use the same update-start actor Welford state and agree before
   mutation on inputs, recurrent states, logits, outcomes, masks, old log probabilities, and
   likelihood ratio one within inherited precision;
4. production `test_mode=0` exposes the native-owned post-arrival/pre-action cut, holds the origin
   certificate rather than the application raw action, freezes one immutable parent, and creates
   exact RETAIN/COPY/SHADOW clones before one branch-specific policy forward;
5. native state remains authoritative for owner, actuator, transaction, buffers, physical tape,
   counters, costs, and hard events; Python passes recurrent tensors only through the private typed
   B01 API; and
6. existing REAL/SHAM/TEST behavior, ABI layouts, checkpoint schema, public-seed RNG derivation,
   addressed draw counts, FP32 learner/optimizer behavior, float64 native physics, AdamW/PPO order,
   one Torch thread, external side effects, and legacy observables remain unchanged.

The branch mapping stays exactly:

```text
RETAIN:          owner/actuator and all recurrent copies retained.
TRANSFER_COPY:   owner/actuator o->s; I_s <- clip(I_o); S_o <- I_o.
TRANSFER_SHADOW: owner/actuator o->s; I_s <- clip(S_s); S_o <- I_o.
```

All sources must already be finite and within `[-1,1]`; malformed inputs are rejected, not
repaired. The origin predicate mirrors accepted legacy reasons 2--12, excludes raw-action reason
13, and adds no current-readiness or current-lineage equality that legitimate arrivals invalidate.

## 4. Owned paths and reuse boundary

C03 owns only the same five existing production files:

- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_evaluator.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp`

and the B01-local paths:

- `experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/**`
- `scripts/run_dish_first_trigger_source_scout_b01.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/**`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_b01_production_conformance.py`

The accepted TEST sidecar and its existing source-factored tests are read-only references. No
`hmasd/`, `ha_ctse_process/`, `envs/`, core configuration, science card, `DIRECTION.md`, historical
evidence, A01 headroom object, or unrelated R06 path is owned. If another path is necessary, CM
returns a path-specific refusal; it does not expand scope.

The dirty reuse candidate is never edited, staged, committed, cleaned, or treated as evidence.
An implementer ports selected changes into its own clean worktree and records which paths were
reused, changed, or rejected.

## 5. Runner, exposure, projection, and resource boundary

The runner retains only:

- `project-cost`, which is non-result-bearing and creates no run root, RNG master, model,
  optimizer, checkpoint, endpoint, or summary; and
- `run --seed {11,29,47}`, which CM, implementer, and reviewer must not invoke.

`project-cost` must emit machine-readable per-seed rows and one fully charged row for each RETAIN,
COPY, and SHADOW arm from the runner's own law. The card projects
`1,474.544745605439 s` per arm from 64 updates and its fixed/margin terms; every generated arm must
be at or below the frozen `1,800 s` cap. The complete seed invocation is charged independently to
every arm. C03 changes no cost cap or scientific budget.

The prospective exposure line remains 2,048 AdamW minibatch steps, nominal learning-rate path
`0.6144`, and `8.51x` the smallest inherited Xavier RMS. A future result must emit actual float64
parameter displacement, initialization/final norms, maximum per-tensor ratio, and optimizer-step
count; zero or missing displacement is incomplete. C03 verifies that the runner publishes these
fields but observes no learner values.

The B01 object is prospectively portable between configured nodes because host identity and
device are not part of its estimand, provided exact committed source bytes run with `device=cpu`,
one Torch thread, the frozen precision/RNG law, and no semantic change. Any eventual result is
therefore **remote-first** on `wsl_4070`. A remote launch requires one `agent-task` command joining
the node-local fresh 4 GiB physical/effective admission and exact runner with `&&` at the launch
SHA. Local fallback is allowed only under the repository's predeclared rule. C03 performs no
admission and no result-bearing command.

## 6. Technical verification and acceptance

The C03 implementer first performs static self-review against sections 2--5. One independent
`hmasd-reviewer`, not primed with test success, then inspects the complete final diff for scientific,
causal, role, live/replay, numerical, RNG, checkpoint, ABI, side-effect, output, cost, and scope
conformance. A material finding is repaired before the sole final verification; if that changes
meaning or ownership, CM stops instead.

On final bytes, CM runs exactly one focused verification group:

1. the smallest existing R06 regressions for the five changed production surfaces;
2. the focused B01 production-conformance tests;
3. the B01-local rule/intervention tests and the single under-60-second smoke using
   `b01_production_test_fixture(width=1, origin_valid=True)` with `test_mode=0`, retaining
   `import numpy as np`, traversing prepare, immutable clones, one forward/completion per branch,
   JSON publication, and the real `project-cost` subprocess; and
4. one direct non-result `project-cost` command on those same final bytes.

CM records commands, pass/fail counts, durations, warnings, emitted cost rows, changed-line counts,
and reviewer findings. Test success or cost-row production establishes only engineering
conformance. It cannot establish an `FTS-*` branch, trigger support, source value, or direction
status.

## 7. Stop rule, engineering scope, and return

Stop with a technical refusal and no approximation if an owned path is insufficient; a protected
semantic would change; any final test fails; reviewer material findings remain; an emitted arm
exceeds 1,800 seconds; an unrequested section-4 item appears; or a scope budget is exceeded. Do not
repair after the sole final verification, do not run a scientific seed, and do not assign polarity.

**Engineering-scope §4 declaration: C03 needs none of the default-prohibited machinery.** It adds
no distributed/multi-process execution, worker pool, queue, scheduler, resume/recovery
orchestration, retry loop, lease, lock, heartbeat, liveness probe, supervisor, tamper evidence,
byte manifest, provenance/currentness guard, incident tree, schema validator, registry, plugin or
factory layer, logging framework, compatibility shim, defensive impossible-host handling,
telemetry beyond wall time and peak RSS, or repeated smoke suite. New non-test research code stays
below 2,000 lines, the runner below 600, orchestration below 30 percent, and focused non-smoke tests
below five minutes. Any breach is returned and recorded, not accepted as the price of a result.

CM returns exact changed files, reused/rejected paths, line counts, §4 additions (`none` expected),
tests and cost output, review findings, commit/push state, and residual technical risks. A clean
technical return permits the DM to inspect launch readiness; it does not itself authorize science.

## 8. Object-tier decision

Options:

- **(a)** open this fresh C03 attempt from clean current bytes, reuse only independently reviewed
  meaning-complete C01/C02 work, retain the missing NumPy import, and require one clean final suite
  plus all three cost rows;
- **(b)** discard the inspected conformance work and rebuild the entire implementation from the
  unchanged production baseline; or
- **(c)** stop or park the B01 mechanism because the preceding test-only assembly failed.

Recommendation: **(a)**. The prior dynamic failure is isolated to a missing test import, while the
substantive production diff had no material static finding and passed the executed production
categories. Reuse is the smallest outcome-blind path; option (b) repeats inspected work, and option
(c) would convert technical invalidity into scientific or direction polarity.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This reversible technical decision opens one fresh CM chain and no scientific
launch.
