# DISH A03 — paired ground-endpoint native path evidence

Date: 2026-09-05. Object `DISH-GROUND-ENDPOINT-PATH-A03`, **A / RECON**.
Card: `DISH_GROUND_ENDPOINT_PATH_A03_SCIENCE_CARD_20260905.md`, including the
prospective promoted-owner relay wording at `c0ecf6e9f` before any A03 output.

## 1. Identity, exact input and evidence

One accepted task `dish_ground_endpoint_a03_seed11_pair_a1`, PID 1664694, node
`wsl_4070`, source `818b2566d1bac7cafcc71ed0bbb90b8abd1c6b65`, detached cwd
`/home/wu/hmasd-worktrees/dish-endpoint-a03-818b2566`. The exact command is in
`DISH_GROUND_ENDPOINT_PATH_A03_CM_RETURN_20260905.md`: destination admission and
`python -m scripts.run_dish_ground_endpoint_path_a03 run --seed 11` joined by `&&`.
The shared tracker observed the unique accepted process and its terminal exit 0;
CM collected the original artifacts, and DM acknowledged terminal handoff once.

Original `seed_master(11)` / `panel()[0]`, block 0, CLAIM/TARGET_VISUAL_MASK/K8/slot 0,
speed 4, normal mode 0, original masks/reflection/owner. Both hosts use the same
2,070,711-byte retained B01 checkpoint with SHA256
`0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa`.
Literal and new ground-terminal hosts use the same deterministic retained controller,
independent fresh recurrent state, original normalization, FP32 Torch/float64 native,
one Torch thread and no learning. No source fork, forced signal or fixture substitution.

Original runtime root relative to that cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/`.
Files are `a1/summary.json`, `a1/trace.jsonl`, `a1/task.log`, and `a1_admission.json`.
Local originals are in the same relative root in CM's
`C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904` worktree.

| Original artifact | Bytes | SHA256 checked by DM |
| --- | ---: | --- |
| summary.json | 16,719 | `09a69cc54de2a064d018916bedbb2b20a6c5c267cdca5d3456030fdf5fd537cf` |
| trace.jsonl | 39,140,340 | `f2c612928529f30b0566c8895cb40644071dd87c2db03b14cededd98e0dbf45d` |
| a1_admission.json | 504 | `9738a4fc2ef70985ea3e3c8f60d041021ba63770ce9442cd102e54f0ad3769c0` |

CM accepted collection commit: `e58b9f1f82e2bbfa9e6e2655244cd88e324f4bcf`, reference
`DISH_GROUND_ENDPOINT_PATH_A03_COLLECTION_20260905.md`.
The compact tracked summary is `DISH_GROUND_ENDPOINT_PATH_A03_SUMMARY_20260905.json`.
DM also compared the committed summary Git blob with the collected original; the bytes
are identical. Hashes here record collection provenance; they add no runtime gate.

## 2. Rule applied verbatim

> 1. If either camera has no observed available tick, either receiver has no completed
> SOURCE adoption, or no common SOURCE is observed: **A03-ACCESS-NOT-RESTORED**.
> 2. Otherwise, if there is no delivered snapshot, no delivered readiness, no ordinary
> application-valid boundary or no applied legal owner/actuator transfer:
> **A03-DOWNSTREAM-STAGE-GAP**, naming every absent stage and the earliest absent stage.
> 3. Otherwise, if no valid native service occurs from an actually adopted relay emitted
> by the promoted owner at or after the legal application:
> **A03-CONSEQUENCE-NOT-REACHED**.
> 4. Otherwise: **A03-BOUNDED-PATH-QUALIFIED**, only for this fixture/controller and host.

The new host reaches camera, both actual receiver adoptions, common SOURCE, snapshot
and readiness delivery. It reaches no application-valid boundary or legal transfer.
Apply branch 2: **A03-DOWNSTREAM-STAGE-GAP**, absent stages `origin_valid` and
`legal_transfer`, earliest absent stage `origin_valid`. The literal host separately
reads A03-ACCESS-NOT-RESTORED. Service remains reported even though an earlier branch
controls. The complete pair is not full host-path qualification or source-value evidence.

## 3. Direct observations and DM recount

DM read all 2,400 raw trace records without native/model calls. Each host has exactly
1,200 live prepared/complete ticks, action ticks 0–1199 and final native tick 1200.
Every next `before_prepare` matches the previous completed state; both raw and normalized
actor inputs have the required four-by-54 shape. Native terminal occurs only at final
completion, with positive batteries and no terminal padding. Data-only recomputation of
receiver adoption, delivered masks, protocol/proposal events, service and application
histogram agrees with the summary. The literal overlapping counts also match A01 panel 0.

| Quantity | Literal | Ground-terminal A03 |
| --- | ---: | ---: |
| Live/completed ticks | 1,200 / 1,200 | 1,200 / 1,200 |
| Camera-present ticks U0 / U1 | 0 / 0 | 283 / 237 |
| Actual SOURCE adoptions U0 / U1 | 0 / 0 | 287 / 287 |
| Common-SOURCE ticks | 0 | 1,199 |
| Snapshot deliveries / accepted ticks | 0 / 0 | 331 / 915 |
| Readiness deliveries / accepted ticks | 0 / 0 | 634 / 914 |
| Version-ready ticks | 0 | 634 |
| Renewal / prepare / commit proposals | 150 / 103 / 138 | 150 / 119 / 14 |
| Completion-latch ticks | 1,196 | 916 |
| Emitted intents / with certificate | 0 / 0 | 4 / 0 |
| Application-valid / legal-transfer events | 0 / 0 | 0 / 0 |
| Actual relay emissions / base adoptions | 0 / 0 | 1,199 / 1,174 |
| Native service / promoted-owner service ticks | 0 / 0 | 299 / 0 |
| Invalid-commit count | 0 | 4 |

New-host first action ticks: cameras 0, both SOURCE adoptions and common SOURCE 1,
base adoption/service 2, latch 284, snapshot delivery 285, readiness/version-ready 286,
first emitted intent 340, first rejection 341. Service starts long before any proposed
transfer and all 299 service ticks belong to the original owner. The host service
contrast is +299/1200 = +0.2491666667 of bounded ticks; it is not SHADOW-COPY benefit.

The four emitted-intent origins are 340, 364, 388 and 596. Actual send margins are
26.30299553383493, 26.163229162847568, 23.441132736808548 and 14.487308916885556 dB;
each recorded intent certificate is 0. Native applications at the following ticks
return reason 2; the full histogram is 1,196 reason-0 and four reason-2 ticks. These
are observed ordinary protocol rejections, not a failed process or a demonstrated
implementation defect. The underlying predicate cause has not yet been decomposed.

Both hosts retain owner/actuator U0 and service epoch 0. Separation, command-slew,
token-gap, dual-owner, dual-payload and buffer-clear breach counts are zero. Minimum
separation is 288.19950003710176 m literal and 172.22221119029322 m new host. Total
energy is 287,544.6125112445 J versus 292,276.03269612946 J. These are descriptive
host contrasts; four invalid commits and the absent legal transition remain adverse
evidence against claiming a qualified handover chain.

## 4. Exposure, resources and engineering boundary

Two checkpoint-loaded model/policy initializations, zero optimizer initializations,
training transitions, learner updates and optimizer steps; 2,400 prepared and completed
evaluation ticks. Each host's parameter norm is 41.78517869974931 before/after, with
L2 and relative displacement exactly 0. The inherited B01 training exposure stays
262,144 transitions, 64 updates and 2,048 optimizer steps; none is new A03 work.

Fresh actual-node memory receipt: `2026-09-05T11:13:50.543010Z`, physical and effective
available memory each 13,224,554,496 bytes, all pass flags true, floor 4,294,967,296.
The recorded adjacent `&&` command places this before master/model/result construction.

| Cost quantity | Measured seconds |
| --- | ---: |
| Literal host wall, including trace write/flush | 1.9898064709996106 |
| New host wall, including trace write/flush | 1.9763470540056005 |
| Pair runner wall | 3.969379171001492 |
| Supervisor wall | 5 |
| Trace serialization/write/flush, literal / new | 0.34065982316678856 / 0.3447093938157195 |

Peak RSS 365,654,016 bytes, `resources_unmeasured=false`. Pair timing includes retained
input, both builds/model loads/evaluations and trace close, but excludes the final
summary serialization; the supervisor covers the full process. Per-host projections
88.47988453649668 seconds and pair 176.95976907299337 were below 300/600 caps;
actual timings also fit. Runner and supervisor metrics are alternatives, not additive.
Supervisor start/end are 2026-09-05T11:13:50Z and 11:13:55Z. The named A03 window has
one accepted verification task (8 supervisor seconds) and one accepted scientific pair
(5 seconds): 13 supervisor seconds across these two tasks per one valid paired A result.
This is not the full direction-history denominator; that remains unaggregated.

CM's independent scope review: 435 new non-test lines, runner 68, tests 207 excluded;
127/435 = 29.20% orchestration, scope section 4 adds none. The opt-in native seam adds
22 lines and preserves the literal default/ABI. Five focused tests passed in 6.12 seconds,
including the 5.15-second non-card-coordinate paired publication smoke. No repeated B01
or A01 suite and no original A03 fixture during tests. The publication path is covered;
no open end-to-end publication item or accepted-attempt budget breach remains.

## 5. Prediction, MEI and bounded reading

DM predicted restored camera/SOURCE support with a downstream gap rather than complete
qualification, and literal absence of common SOURCE/service. Both subpredictions match.
Owner prediction: `not taken (unattended)`; no new reply exists at intake. The one-event
diagnostic resolution is reached through readiness but not through legal application
and promoted-owner service. The +299-tick descriptive host effect exceeds the card's
one-tick descriptive MEI; it does not bypass the branch-2 reading. B01's five-tick
source-effect MEI and tuned same-information headroom remain unestimated.

Strongest support: actual information and ordinary service recover under the declared
ground-terminal law without forced margins/readiness or parameter updates. Strongest
contradiction to full qualification: zero legal transfer and four false-certificate
intents despite delivered snapshot/readiness. This locates a remaining stage; it proves
neither general policy incapacity nor an inherently impossible handover protocol.

The surviving alternatives are the fixed retained policy's certificate inputs and the
ordinary timing/action predicates. SHADOW-training co-adaptation and deadline-bound
replay/replan remain live for any later source study, which this pair did not perform.
The smallest next discriminator is an explicitly bounded read-only reconstruction of
the four recorded origin-certificate predicates. No new rollout, learner, threshold
override, physics sweep, family recast or Portfolio action follows from A03 alone.
