# DISH first-trigger source scout B01 — technical intake

- Direction: `degraded_incumbent_shadow_handover`
- Object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Evidence class and claim ceiling: **B — EXPLORE**, limited to a preliminary source-selection
  signal or counterexample on the frozen sixteen-row, three-seed, 64-update panel
- Frozen card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- Bytes inspected: `f0a398f51716b764e66754feb76739b616a075a6`
- Intake status: **technical refusal; implementation attempt quarantined before edit or launch**

This intake contains no scientific result. It distinguishes a directly inspected implementation
boundary from any inference about the DISH mechanism.

## 1. What was checked

The Direction Manager checked the CM return against the frozen card's treatment, comparator,
causal cut, learner semantics, launch conditions, result rule, owned paths, and engineering-scope
declaration. The CM and its single semantic implementer independently returned the same refusal.
The Direction Manager then reproduced the static observations below directly over the recorded
Git bytes.

The result rule in card section 7 was applied verbatim: it accepts only three complete seed
summaries after the common integrity checks. There are zero summaries, so none of `FTS-B0`,
`FTS-BH`, `FTS-BS`, `FTS-BR`, `FTS-BC`, `FTS-BN`, or `FTS-BU` applies.

Counts and receipts checked:

- changed implementation files: `0`;
- new code, runner, and orchestration lines: `0`;
- focused tests and scientific invocations: `0`;
- memory-admission receipts, learner transitions, optimizer steps, evaluated rows, checkpoints,
  and result summaries: `0`;
- conforming implementation commit or push: none; and
- CM worktree: clean at the same card commit.

No runner existed, so no runner-generated `project-cost` receipt exists. The card's prospective
`1,474.544745605439 s/seed` value remains a card assumption, not measured or generated cost
evidence.

## 2. Direct observations over the recorded bytes

1. **Live and replayed actor inputs differ.** Live action selection applies actor Welford
   normalization before the encoder
   (`production_recurrent_trainer.py:279-283`). The training batch stores the raw actor tensor
   (`production_recurrent_trainer.py:413-424`), and PPO replay encodes that tensor directly
   (`production_training_engine.py:124`, `386-392`, `429-434`).
2. **Replay does not start from the recurrent state that generated each fragment.** Every
   64-tick fragment is replayed from a newly allocated zero hidden state
   (`production_training_engine.py:386`); the rollout payload has no fragment-initial hidden.
3. **Replay cannot preserve physical-entity and active/shadow role identity.** Snapshot and
   promotion replay are fixed to copies `0/1`
   (`production_training_engine.py:108-123`). PPO motion, prepare, and commit heads are also fixed
   to copies `0/1` (`production_training_engine.py:403-408`) and have no per-tick owner history.
4. **The live head selection differs from both replay and the frozen role law.** Live motion uses
   fixed physical copies `0/2`, while both prepare and commit use `2 * owner`
   (`production_recurrent_trainer.py:287-306`). That cannot implement the frozen owner-I motion
   and prepare with standby-S motion and commit while keeping
   `[U0-I,U0-S,U1-I,U1-S]` distinct.
5. **The accepted three-way native clone is unavailable on the production evaluator path.** The
   evaluator constructs every production row with `test_mode=0`
   (`production_evaluator.py:88-115`). The native source-factored predicate accepts only modes
   `1/2` and explicitly rejects mode `0`
   (`native/rbhr_r06_production_backend.cpp:472-490`).
6. **The frozen causal cut is absent.** The evaluator calls the complete policy `step_rows` before
   its observer (`production_evaluator.py:175-181`), while application arrivals and the native
   transition occur only in the subsequent `native.step` (`:182-186`). Consequently there is no
   production seam after application arrivals and snapshot assimilation but before the
   application-tick GRU forward. The matching split seam exists only in an isolated TEST sidecar.
7. **The native trigger remains tied to the application input.** `first_application_valid`
   constrains `StepInput.raw_action` at the application step
   (`native/rbhr_r06_production_backend.cpp:458-468`), rather than a retained origin action at the
   frozen post-arrival cut.

These observations are engineering facts. They are not COPY, SHADOW, RETAIN, trigger-prevalence,
or return observations.

## 3. Bounded interpretation

Within the assigned object-local paths and the explicit prohibition on copying the learner loop
or editing the old R06 implementation, no implementation can bind the frozen algorithm to the
production host. A conforming implementation requires either a deliberately owned repair of the
existing learner/training/evaluator/native surfaces or a separately reviewed production bridge
and learner path. Silently using the TEST sidecar, the pre-arrival observer, fixed copy indices, or
the current raw-observation replay would implement a different algorithm.

This is a technical refusal, not evidence that SHADOW lacks value and not evidence that triggers
are scarce. It leaves the card's B claim ceiling unchanged but supports **no scientific claim**.
The B object has no consumption state, and no valid result exists to close even the smallest
scientific unit.

Strongest support for the refusal is the conjunction of the missing production cut, the explicit
native mode rejection, and the live/replay role and recurrent-state disagreements. The strongest
contradiction is that the TEST-only sidecar already demonstrates a three-branch transaction
substrate; that shows the intervention is implementable in a fixture, but it does not connect the
fixture to the real trained production path. This intake does not prove that a scope-expanded,
outcome-blind repair is impossible.

## 4. Flags for the owner and Root

- A future engineering attempt must explicitly own every production surface it changes and
  preserve or prospectively specify observation normalization, fragment-initial hidden state,
  entity/role indexing, RNG, numerical precision, checkpoint bytes, and the exact fork order.
- Treating the current learner divergence as an implementation defect may alter numerical and RNG
  behavior; it must be reviewed as a meaning-preserving conformance repair before any launch, not
  smuggled into an object-local wrapper.
- The runner cost law must be generated anew by the eventual conforming runner before resource
  admission. The card's historical timing constant is not a substitute.
- No `DIRECTION.md` conclusion is changed: this intake adds engineering state, not accepted
  mechanism-level science.

## 5. Decisions this intake produces

### Decision 1 — disposition of this implementation attempt (object tier)

Options:

- **(a)** accept the reproduced technical refusal, quarantine this zero-effect implementation
  attempt, preserve the frozen B01 question and causal cut, and permit no scientific launch from
  these bytes;
- **(b)** weaken the causal cut, role mapping, or learner semantics to fit the existing production
  path; or
- **(c)** treat the refusal or TEST fixture as a scientific result and close the B object.

Recommendation: **(a)**. It is the only reversible option that preserves the prospective card and
the boundary between engineering conformance and scientific evidence.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. The implementation attempt is quarantined; the scientific object remains
unconsumed and no result branch is selected.

### Decision 2 — next boundary

No direction-tier recast, park, family closure, or Portfolio action follows from a zero-effect
technical refusal. The next discriminator is an outcome-blind, meaning-complete engineering
feasibility attempt whose owned surface includes the required production learner, evaluator,
Python binding, and native cut. That work must first demonstrate one coherent live/replay role and
normalization law plus a real post-arrival/pre-GRU three-way seam. Only after its own tests,
runner-generated cost admission, commit, push, and per-invocation resource admission may B01 be
launched. This intake neither authorizes that broader implementation nor changes the frozen card.
