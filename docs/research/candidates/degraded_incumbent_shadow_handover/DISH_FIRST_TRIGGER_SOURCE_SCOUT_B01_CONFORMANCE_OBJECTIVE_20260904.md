# DISH B01 production conformance attempt C01 — CM objective

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Engineering attempt: `DISH-B01-PRODUCTION-CONFORMANCE-C01`
- Evidence class and claim ceiling: unchanged **B — EXPLORE** card; this attempt itself has no
  scientific claim
- Frozen card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- Preceding technical intake:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_TECHNICAL_INTAKE_20260904.md`
- Objective baseline: `99f249d9b99162c404e6882fe0632605962c7dff`
- Outcome status at freeze: no scientific seed, result, checkpoint, or branch has been observed

This is one outcome-blind, meaning-complete engineering objective. It widens implementation
ownership only to the production surfaces proved necessary by the technical intake. It does not
change the B01 question, treatment, comparators, first-trigger panel, causal cut, result rule,
seeds, budget, claim ceiling, or prediction.

## 1. Objective and technical acceptance

Produce the smallest inspectable implementation that makes one coherent production algorithm span
live collection, PPO replay, evaluation, and the native RETAIN/COPY/SHADOW fork. Technical
acceptance requires all of the following before any result-bearing launch can be considered:

1. live collection and replay use exactly the same normalized per-tick policy input, recurrent
   start state, physical-entity/role indexing, snapshot order, reset mask, promotion order, action
   heads, action outcomes, and old-policy likelihood;
2. the production evaluator reaches a native-owned post-arrival/post-assimilation/pre-application-
   GRU cut in normal production mode and creates the three frozen branches there without consuming
   an application-tick action first;
3. the native trigger is bound to the stored origin certificate/action facts, not the application
   `StepInput.raw_action`;
4. one under-60-second TEST-only smoke and focused conformance tests pass on the final bytes;
5. an independent reviewer finds no material scientific, numerical, RNG, checkpoint, ABI,
   side-effect, or scope divergence; and
6. the runner's non-result `project-cost` mode emits one fully charged cost row for each of
   RETAIN, COPY, and SHADOW and each row is at or below the frozen 1,800-second cap.

Test success, a cost row, or a process exit proves engineering conformance only. It cannot select
an `FTS-*` branch or establish COPY/SHADOW value.

## 2. Exact owned surfaces

The CM owns changes only in these existing production files:

- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_evaluator.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp`

It may add the B01-local implementation only under:

- `experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/**`
- `scripts/run_dish_first_trigger_source_scout_b01.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/**`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_b01_production_conformance.py`

The accepted TEST sidecar
`production_source_factored_backend.py`, its
`native/dish_promotion_source_fork_r01.cpp`, and existing source-factored tests are read-only
references. They must not become a production substitute or be relabelled as production evidence.
No `hmasd/`, `ha_ctse_process/`, `envs/`, core configuration, direction document, science card,
historical evidence, or unrelated R06 surface is owned.

If meaning-complete implementation requires another path, the CM stops and returns a path-specific
technical refusal. It does not expand ownership itself.

## 3. Frozen live/replay law

The recurrent copy order is exactly `[U0-I,U0-S,U1-I,U1-S]`. For owner `o` and standby
`s=1-o`, both behavior collection and PPO replay select:

```text
physical U0 motion <- U0-I when o=0, otherwise U0-S
physical U1 motion <- U1-I when o=1, otherwise U1-S
prepare            <- owner-I
commit              <- standby-S
prediction owner    <- owner-I
prediction/service source <- standby-S where the inherited head contract assigns it
```

The implementation must retain the per-tick owner needed to apply this law. It may not hard-code
copies `0/1`, `0/2`, or one physical prepare/commit column.

For every 64-tick PPO fragment, collection retains the detached four-copy hidden state at the
fragment entrance and the exact current observation that generated each action. It must not pair an
action with the subsequent native observation or reconstruct an entrance state as zero. Episode
reset is applied before the first policy forward of the new episode and is recorded identically for
replay.

Within each replay tick the order is:

1. apply the recorded episode-reset mask;
2. apply any accepted snapshot bridge to the physical standby-shadow state;
3. consume the exact normalized actor tensor used by behavior and advance the four GRU copies;
4. select the role-indexed heads and compute the old action likelihood for that tick; and
5. after that tick's native CAS fact, apply entity-aware COPY/FLEX promotion to form the next
   tick's hidden state.

The actor Welford state frozen at the start of an update is the state used for both behavior and
old-policy replay of that update. Raw present rollout values update the retained Welford state only
after collection in the existing deterministic order; the resulting state becomes the next
rollout's start state and must be synchronized into the live policy after every optimizer update.
Snapshot and critic paths remain exactly as declared by the B01 card/current flow unless a direct
live/replay equality check shows that they participate in the recorded divergence; no historical
C-time normalizer expansion is authorized by this objective.

The pre-mutation behavior-policy likelihood ratio must be exactly one within the existing numeric
precision on a two-owner sentinel trace. Logits, selected means, action outcomes, masks, and old log
probabilities must agree between live collection and replay before any optimizer mutation.

## 4. Frozen native/evaluator cut

The B01 application opportunity originates at tick `n`; its application is `t*=n+1`. The
production path must expose this order without using a TEST reset:

1. process `t*` pending arrivals and native buffer replacement from the common parent;
2. expose any causally accepted snapshot delivery, apply the Python snapshot bridge to the
   standby-shadow recurrent copy, and evaluate the native first-application predicate from stored
   origin facts;
3. if and only if the predicate is valid, freeze the common parent after assimilation and before
   CAS and before any `t*` actor-observation GRU update;
4. clone the immutable parent into RETAIN, TRANSFER_COPY, and TRANSFER_SHADOW, apply the equal-cost
   transaction shell and the card's source-specific recurrent promotion;
5. materialize each branch's post-transaction/pre-action `t*` actor and critic observation;
6. execute exactly one branch-specific policy forward and common action projection; and
7. advance ticks `t*,...,t*+99` with the checkpoint, Welford state, and future physical tape held
   common and with zero optimizer updates.

`test_mode=0` is mandatory. Native state retains authority for ownership, actuator, transaction,
held origin certificate, buffers, physical tape/counter frontier, costs, and hard events. The
caller may hand off recurrent tensors only through a typed, validated API; it may not edit native
owner/state fields. The parent and recurrent handoff are immutable across cloning.

The application predicate must have no dependency on the application-tick raw action. A conformance
test must show that perturbing only the unused application action leaves the predicate and fork
unchanged, while invalidating the native-owned origin certificate/facts refuses the fork. No
observation may be consumed twice and no application GRU forward may occur before cloning.

The branch transaction remains exactly:

```text
RETAIN:          owner/actuator and all recurrent copies retained.
TRANSFER_COPY:   owner/actuator o->s; I_s <- clip(I_o); S_o <- I_o.
TRANSFER_SHADOW: owner/actuator o->s; I_s <- clip(S_s); S_o <- I_o.
```

All other recurrent copies retain their common pre-CAS values. Every source must be finite and
already in `[-1,1]`; malformed values are rejected rather than repaired. Existing native ABI
layouts and existing REAL/SHAM/TEST behavior remain unchanged; any B01 entry point is additive and
private to this research surface.

## 5. Runner and output obligations

The new runner has exactly two modes:

- `project-cost`: non-result-bearing; prints machine-readable per-seed and per-arm rows from the
  runner's own cost law without creating a scientific root, RNG master, model, optimizer,
  checkpoint, or result; and
- `run --seed {11,29,47}`: implements one frozen seed invocation, but CM and reviewers must not
  invoke this mode.

The generated cost law retains the card's explicit components and may replace the historical
per-update constant only with a result-blind direct measurement whose command and output are
returned. The full seed invocation is conservatively charged independently to RETAIN, COPY, and
SHADOW. Any arm above 1,800 seconds makes the implementation technically inadmissible.

The eventual run mode must expose the frozen learner counts, panel rows, trigger/no-trigger facts,
three branch receipts, 100-tick endpoints, hard events, energy, actual exposure line, wall time,
peak RSS or `resources_unmeasured`, checkpoint evidence, and the unchanged ordered `FTS-*` inputs.
It accepts an explicit fresh admission receipt and refuses a missing or failed receipt. This is not
authorization to generate that receipt or invoke the runner.

## 6. Focused verification and independent review

The final focused suite contains only:

- a two-owner sentinel-hidden live/replay equality test covering normalized inputs,
  fragment-initial hidden, reset, snapshot, owner-indexed motion/prepare/commit, promotion, masks,
  logits, and pre-mutation likelihood ratio one;
- a production-mode phased native test covering arrival-before-bridge, origin-bound predicate,
  immutable three-way clone, exact branch source mapping, one forward per branch, and rejection of
  malformed recurrent sources;
- a trigger/no-trigger and ordered synthetic result-rule test; and
- one under-60-second toy end-to-end smoke that uses an explicit TEST fixture but traverses the new
  production APIs and publication path without training a scientific seed.

The CM runs the smallest relevant existing regression tests for every modified R06 surface and one
final focused suite on final bytes. It records exact commands, counts, duration, and warnings.
Repeated smoke suites are not authorized.

After implementation, one independent `hmasd-reviewer` performs a static, card-aware review. The
reviewer is not given test success as evidence of correctness and must inspect the causal order,
role indexing, live/replay identity, native authority, RNG/numerical/checkpoint preservation,
runner counts/cost rows, and scope. Any material finding is repaired and re-reviewed before
technical acceptance.

## 7. Protected semantics and engineering scope

Preserve FP32 policy/optimizer behavior, float64 native physics, one Torch thread, exact model
architecture, AdamW parameters and PPO update order, addressed policy RNG fields and draw counts,
public seed derivation, native physical RNG/address frontier, checkpoint schema and load behavior,
external side effects, panel/seeds/horizons, and card result rule. Do not inspect outcomes, tune a
seed/row, or add a comparator.

**Engineering-scope section 4 declaration: this attempt needs none of the default-prohibited
machinery.** It adds no process pool, queue, scheduler, resume orchestration, retry loop, lease,
lock, heartbeat, liveness probe, tamper evidence, byte manifest, provenance/currentness guard,
incident tree, schema validator, registry, telemetry beyond wall time and peak RSS, compatibility
shim, or repeated smoke suite.

The complete attempt remains below 2,000 added research-code lines, the runner below 600 lines,
and orchestration below 30 percent of the implementation diff. Existing lines may be simplified
where needed, but unrequested machinery and unrelated cleanup are rejected. `scope: none` is the
expected commit scope.

## 8. Resource, stop, and return rules

CM tests and `project-cost` are non-result-bearing and do not require scientific admission. The CM
must not run `admit-memory`, create a seed run root/master, train a seed, or execute evaluation
outcomes. After a technically accepted commit is integrated and pushed, the DM must still run a
fresh 4 GiB physical/effective memory admission immediately before each detached seed invocation.

Stop and return a technical refusal with no approximation if:

- an owned surface is insufficient;
- existing production ABI behavior, scientific meaning, RNG, precision, checkpoint schema, or
  side effects cannot be preserved;
- the implementation requires any undeclared section-4 machinery or exceeds a scope budget;
- the final tests or independent review retain a material finding; or
- any generated per-arm cost exceeds 1,800 seconds.

Return the exact changed files, line counts, section-4 additions, test and cost commands/results,
review findings, commit/push state, and remaining technical risk. Technical acceptance does not
authorize science and cannot establish any COPY/SHADOW branch.

## 9. Object-tier implementation decision

Options:

- **(a)** preserve B01 unchanged and open this single, narrowly scope-expanded production
  conformance attempt over the five recorded production surfaces;
- **(b)** fit the existing TEST sidecar or pre-arrival observer by weakening the causal cut and
  role/replay law; or
- **(c)** treat the technical refusal as direction evidence and park/close the family.

Recommendation: **(a)**. It is outcome-blind, reversible, and directly tests whether the accepted
B question can be instantiated without changing its meaning. Option (b) changes the object;
option (c) confuses engineering state with mechanism evidence.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This selects an implementation attempt inside the accepted B mechanism; it does
not change direction or Portfolio state and does not authorize a result-bearing launch.
