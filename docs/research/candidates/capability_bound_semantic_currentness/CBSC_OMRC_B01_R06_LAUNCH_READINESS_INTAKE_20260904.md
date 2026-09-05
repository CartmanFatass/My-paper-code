# CBSC-OMRC-B01 r06 launch-readiness intake — 2026-09-04

Claim: on `CBSC-DYNAMIC-CACHE-2R-1C-v1`, current capability-bound content may change the learned
native `SERVE / REFRESH / SAFE_FALLBACK` decision and held-out team return relative to competent
same-information RAW, predictive-index, and deranged-content controls.
Binding structure: **systems / information flow**. The question arises from one controller's
partial observation of receiver-addressed capability state and its non-stationary currentness; this
object has no changing learner roster, partner co-adaptation, or multi-agent credit assignment.

- Direction: `capability_bound_semantic_currentness`
- Object and rung: `CBSC-OMRC-B01`, `CBSC-OMRC-B1-THREE-SEED-SCOUT`
- Evidence class: **B/EXPLORE**
- Fresh attempt selected here: `b1_scout_r06`
- Integrated portability-repair commit: `602ee7467b93aa3993aab5e5a9c87814fee54f7d`
- Launch binding: the pushed commit containing this intake, passed literally as
  `--implementation-commit` and recorded by the result; a post-launch receipt records that SHA.
- Scientific-result status at this intake: **none**

This intake closes launch readiness only. Attempts `r01` through `r05` remain technical failures;
none has scientific polarity or consumes this B object. The host, treatment, comparators, FP32
learner, RNG addressing, seeds, budgets, held-out panels, result rule and claim ceiling are not
refrozen or changed here.

## 1. Evidence checked

I checked the frozen direction and literal/metrics specifications, evidence-spec section 11, the
defect-8 decision and technical-closure intakes, the fixed B0 receipt, the A01 headroom census,
the current source surface, direct Linux failure reproduction, the bounded repair, independent
reviews, exact-SHA remote profiles, r05 engineering telemetry, and current owner reviews.

Defect 8 is technically closed. Task `cbsc-d8-profile-4f8fe0f6e-04` ran the formal publication
profile in a clean detached Linux worktree at exact commit
`4f8fe0f6eaca799a79e05fe75ec408acb05f979f`: `17 passed` in `23.67` seconds. The canonical
scientific/code surface stayed unchanged through the later control-plane integration before the
telemetry repair. This is engineering conformance, not mechanism evidence.

The remaining Linux failure was then reproduced directly at exact commit
`2aaf43a8a8824eabe10c2cfb8d55cb025cadf1d9`. Task
`cbsc-b1-readiness-2aaf43a8a-02` ran the six supervisor tests and returned `4 passed, 2 failed`:
short-lived external Python children can legitimately have CPU time quantized to `0.0` at the
node's 100 Hz clock. The bounded repair preserves full-lifetime external-child CPU/IO accounting,
allows only finite nonnegative CPU endpoints/stages, and continues to reject negative, Boolean,
NaN and infinity values. Positive wall time, nonzero RSS, sample counts, process topology, real
scientific work, throughput identities, 120-minute stopping, admission and all learner semantics
remain strict. Its independent reviewer returned PASS. Exact repair task
`cbsc-b1-zero-cpu-55e405a2-01` then ran the original six-test Linux profile: `6 passed` in `2.03`
seconds. The repair adds no new engineering-scope section-4 category and is `scope: none`.

The restored B0 evidence is fixed by manifest SHA-256
`c7c6f73be17e785cbe6ffaba6cfd30c4c8483ecf23e43bbd48df535c676bc298` and inventory SHA-256
`184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5`: 33 files and
12,807,274 bytes. Current local and remote readiness both read the locator-only evidence and return
`B1_FORMAL_READY`, `start_authorized=true`, with no blocker after the tracked authority documents
are included. Final exact-launch-SHA readiness is repeated before launch.

Owner-console reviews returned an empty list. There is no owner instruction that changes this rung.

## 2. Section-11.4 launch conditions

The four controlling conditions are satisfied or bound to the atomic launch command:

1. **Section-4 integrity.** Treatment is `STRUCT-CURRENTNESS-GRU`; the strongest competent
   same-information null is unrestricted `RAW-GRU`, with `PI-GRU` and equal-work
   `DERANGED-CURRENTNESS-GRU` as live explanations/controls. B0 fixes host causality, action masks,
   primitive-history parity, RNG independence, held-out separation, adapter/equal-update parity,
   checkpoint roundtrip, ledger arithmetic and update/evaluation counts. Defect-8 publication and
   the reachable Linux supervision path have exact-SHA profiles and independent PASS reviews.
2. **Real nonzero work.** Each of three seeds (`21101`, `21121`, `21143`) and four arms trains for
   384 episodes, 58,368 primitive transitions, 9,216 decisions, 48 rollout updates and 768 Adam
   steps. Checkpoints are `0/12/24/48`; each has 64 held-out episodes, for 38,912 evaluation
   transitions and 6,144 opportunities per arm-seed. These are real recurrent-PPO and evaluator
   paths, not synthetic placeholders.
3. **Resource admission.** The sole remote result task contains fresh node-local
   `admit-memory && exact runner`; no scientific root, RNG master, model or optimizer may be
   created unless physical and effective available memory are both at least 4 GiB. The runner also
   admits every training slice and policy replay invocation. A prior diagnostic check is not reused.
4. **Exposure.** A machine calculation from the fixed B0 `update-0` and `update-1` checkpoints
   gives the identical initialization scale `L2=29.89684618357759`,
   `RMS=0.08582370837903153` over 121,349 parameters. After only 16 Adam steps, the four arms move
   `L2=0.4576527919924285..0.47487743607923133`, or
   `1.5307728085506834%..1.5883863908698257%` of initialization L2, with at least 115,876
   parameter entries changed. Thus the optimizer can move the learner at this initialization.
   B1 has 768 Adam steps per arm-seed and publishes its realized step count, parameter digests and
   post-clip gradient-norm range in the machine-generated exposure line.

Headroom is not a launch condition. The accepted A/RECON branch is
`HC-M / CANDIDATE_ASSETS_MISMATCHED`: neither a same-host same-information upper result nor a valid
tuned generic result exists, so both terms and their gap are null, not zero. No MEI threshold is
applied. This diagnostic neither supports nor contradicts the B mechanism and does not rewrite the
already-open ladder's result branches.

Engineering-scope accounting is unchanged: defect 8 has the one already carded incident-root
static path budget; the telemetry correction adds no section-4 machinery. The accepted defect diff
was below the 2,000-line, 600-line runner and 30% orchestration budgets. The telemetry repair changes
five existing files, leaves the runner untouched, and is likewise below those budgets.

## 3. Per-arm cost projection and stop rule

The runner's unit is one arm-seed: three training slices followed by one same-slot policy replay.
Using only r05's outcome-blind process telemetry, the projection law is

`P_arm,seed = sum(wall of slices 0:12, 12:24, 24:48) + wall of matching replay`.

Across all 12 completed engineering slots, `P_arm,seed` ranges from `197.446350000042` to
`323.7225416000001` seconds. A stricter componentwise envelope combines the largest three-slice
training observation (`296.92813109999406`) with the largest replay observation
(`36.342732699995395`): `333.27086379998945` seconds per arm-seed, or `4.628762%` of the frozen
`7,200`-second cap. Every arm-seed is therefore admitted by projection. The 120-minute wall cap is
still enforced per invocation; no observed scientific value was read to form this projection.

The runner stops and quarantines on an integrity, learner-instrumentation, admission, or wall-cap
failure. Missing resource telemetry alone remains `resources_unmeasured`. No failed attempt is
resumed or interpreted; an outcome-blind repair at a new SHA would be a fresh attempt.

## 4. Prediction and interpretation boundary

DM prediction on record: STRUCT will reach usable competence earlier, around updates 12–24, and
retain a preliminary held-out advantage by update 48; the strongest alternative is that competent
RAW contains the information and removes the effect at this budget. Owner prediction:
`not taken (unattended)`.

The result is read only through the frozen branches
`PRELIMINARY_SEMANTIC_CURRENTNESS_SIGNAL`, `GENERIC_FACTORIZATION_OR_CONDITIONING`,
`PREDICTIVE_INDEX_SUFFICIENT_ON_HOST`, `NULL_AT_THIS_BUDGET`, `INSTABILITY`,
`ADVERSE_COUNTEREXAMPLE`, or `INVALID_OR_NONIDENTIFYING`, after the mechanical RAW-competence and
integrity checks. Above a future object-local MEI would be described as practically material;
inside it as a bounded null/too-small signal; opposite sign as an adverse counterexample. This
open ladder predates the current MEI field, so no new threshold is injected into its frozen rule.

The claim ceiling is one preliminary host- and budget-bounded recurrent-PPO signal, competent null,
instability diagnosis, generic-conditioning explanation, predictive-index sufficiency observation,
or adverse counterexample. It cannot establish stable or general superiority, representation
necessity, natural frequency, communication/credit value, variable-population value, transfer,
safety or deployment value.

## 5. Decisions this intake produces

### Launch the fresh minimal B rung (Object tier, selection)

Options:

- **(a)** accept the bounded Linux repair and complete final exact-SHA readiness, then launch the
  sole fresh `b1_scout_r06` task remote-first with atomic admission and the unchanged card;
- **(b)** leave the runnable rung unlaunched because current-host headroom or a new MEI is absent;
  or
- **(c)** expand engineering scope, alter the cap/exposure/comparators, or use a local fallback
  despite an admitted portable remote route.

Recommendation: **(a)**. The only directly reproduced portability blocker is closed and the
section-11.4 conditions are satisfied; option (b) promotes non-gating diagnostics into a launch
condition, while option (c) changes scope or scientific meaning without evidence.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. The selection is reversible until the single result task is accepted. Once
accepted, its frozen attempt runs to a valid result or a directly reproduced technical blocker; no
duplicate launch or local fallback is authorized.
