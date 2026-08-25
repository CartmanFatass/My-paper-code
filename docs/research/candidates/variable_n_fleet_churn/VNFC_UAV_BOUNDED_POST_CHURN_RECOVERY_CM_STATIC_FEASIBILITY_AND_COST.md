# VNFC UAV bounded post-churn recovery CM static feasibility and cost

Direction: `variable_n_fleet_churn_b4`

Stage: `VNFC-UAV-BOUNDED-POST-CHURN-RECOVERY-DEFINITION`

CM: `/root/cm_vnfc_uav_post_churn`

Accepted science revision: `VNFC-BPCR-SCIENCE-20260820-09`

Card SHA-256:
`39b20b0655cef10ff4d3bc3c0550cd286ade922074f73dfd9cba1b62f8f977bf`

Pro response SHA-256:
`85a2d063b1e5a362f9ac827bd8493d5c1ee2c6aad635c92b314e9bcba6b12e57`

## Technical disposition

The exact revision-09 object is **statically feasible and finitely costed**.
The public-law dependency, prehistory, observation, command grammar, MAPR,
strictly containing DIRECT comparator, association cut, bounded fixed
comparator, corrected exact inference, outcome map, and atomic evidence surface
can be bound without the old full graph, quotient, `FIXED-FH`, `GLOBAL-EXACT`,
old coordinates, checkpoints, results, or a hidden exponential solver tail.

This is definition/static evidence only. No source, host, model, coordinate,
test, probe, build, training, evaluation, lease, or compute was inspected,
created, or run. No question-relevant output exists.

## Static binding and observability

- **Immutable dependency.** The currently available source object hashes to
  `be15c98e59e2e8b95bccc51e00c755d943627cc59e482c136892809ab717fe64`,
  exactly matching the immutable public-physical-law binding. A future manifest
  can vendor those bytes or a content-addressed copy and fail closed on mismatch.
- **Unique prehistory and token state.** Legal-command enumeration followed by
  the six ordered criteria and opaque-rank serialization yields one command.
  Fixed en-route commitments are explicit. `VACANT`,
  `COMMITTED_OR_ACQUIRING`, and `ACQUIRED`, plus acquisition elapsed and the
  separate clearance field, cover every token lifecycle without an overloaded
  or hidden state.
- **Observation and command grammar.** Agent width 38, zone width 15, four
  globals, four failure-relative tokens, fixed-commitment skipping, candidate
  removal, null support, base fallback, legality masks, and tie serialization
  are directly materializable and auditable at every decision.
- **Order-independent pooling and initialization.** The mean can use a fixed
  exact binary superaccumulator followed by one correctly rounded division;
  maximum is an exact binary64 comparison. Counter-addressed normal matrices
  followed by canonical sign-fixed Householder/QR orientation bind the stated
  row/column Haar-Stiefel initialization and gains. A future activity identity
  must freeze the concrete counter transform, QR convention, compiler/ABI, and
  generated-matrix conformance record before coordinate binding.
- **MAPR and DIRECT containment.** DIRECT copies every MAPR base parameter and
  its residual output can be identically zero, reproducing every conditional
  and joint command distribution. A nonzero prefix-dependent residual supplies
  a strictness witness unavailable to MAPR. Full-versus-zero-residual
  distributions and physical decodes expose both `I_res_active` and
  `I_res_change` over every required denominator.
- **Association surfaces.** Row-cut partitions, derangements, row-multiset
  preservation, inverse mapping, common tapes, opportunity/action-change
  indicators, and raw-record consistent-relabel recomputation are all finite
  and directly observable.
- **BCRH-PERSIST.** Current-command enumeration is bounded by 1,961 commands.
  Forward/backward reciprocal weights are action-independent exact rationals;
  persistent candidate schedules are finite event-jump records; post-60
  ranking removes only a completed candidate-common term. Scorer, independent
  checker, maximin early-recovery floor, canonical ties, 64 exact fixtures, and
  competence rows can be recorded without a future-action tree or full-state
  graph.
- **Corrected exact inference.** Revision 09 replaces the prior multivariate
  projection. Each coordinate uses `2^15` canonical complementary partitions,
  exact dyadic-rational input values, exact subset means, inclusive tails, and
  a fixed `q_m` order statistic. Streaming extreme heaps bound memory; there is
  no continuous search, profiling assumption, or semialgebraic projection.
- **Atomic evidence.** Immutable dependencies, coordinate manifest, initial and
  final learned states, common worlds, endpoint traces, containment/cut/
  invariance records, every BCRH candidate and checker comparison, fixtures,
  exact inference matrices, and result-map reduction have distinct writers and
  can be sealed under one create-only manifest.

## Independent count verification

| Object | Independent derivation | Exact count |
| --- | --- | ---: |
| Training episodes | `16 reps * 2 arms * 256 updates * 16 episodes` | 131,072 |
| Learned joint decisions | `131,072 * 6` | 786,432 |
| Optimizer minibatch steps | `16 reps * 2 arms * 256 updates * 4 epochs * 4 minibatches` | 131,072 |
| Learned validation rollouts | `16 reps * 2 arms * 2 checkpoints * 4 cells * 32 worlds` | 8,192 |
| Conclusion rollouts | `16 reps * 64 worlds * 4 arms/controls` | 4,096 |
| BCRH conclusion rollouts | `16 reps * 64 worlds` | 1,024 |

The BCRH arithmetic also agrees:

- scorer plus checker: `1,024 * 6 * 4,415,000 = 27,125,760,000`;
- action sensitivity: `1,024 * 300,000 = 307,200,000`;
- fixtures: `64 * 4,415,000 = 282,560,000`;
- total bounded-controller ceiling: `27,715,520,000` logical operations before
  serialization constants.

For inference, the family sizes are `12,24,8,28,18`, totaling 90 coordinates.
With `H=32,768`, the exact table is
`q_m={28,14,41,12,19}`. The family noncoverage numerators are
`{324,312,320,308,324}`, summing to 1,588 and giving joint coverage lower bound
`1-1588/32768=0.9515380859375`. Work is exactly 2,949,120 partition visits and
5,898,060 finite complementary subset-mean constructions, with ceiling
`90*((H-1)+26H)=79,626,150` exact-rational comparisons.

## Required C++ batched production binding

Any later construction must satisfy the shared production policy before the
activity boundary:

1. call `require_cpp_batched_production` and fail closed if the native batched
   path is unavailable;
2. place physical ticks, legality/safe-return checks, prehistory, token-state
   transitions, event-jump schedules, batched endpoint accumulation, and BCRH
   candidate evaluation in C++ batch kernels;
3. keep Python limited to orchestration, PyTorch model/optimizer calls, immutable
   artifact publication, and final reduction—never scalar environment/action
   loops;
4. use a separately implemented C++ checker for BCRH command enumeration and
   exact score/tie reproduction; and
5. compare the native batch against deterministic reference fixtures before any
   coordinate binding. Exact semantic equality, not speed alone, is the gate.

## Prospective engineering cost

This is a standalone conservative cost; it does not assume that unfinished
shared backend work will be accepted. An already accepted reusable native
substrate could reduce the incremental range by roughly 8–14 focused days.

| Work package | Focused engineer-days |
| --- | ---: |
| Immutable dependency, schemas, counters, atomic artifact skeleton | 4–6 |
| C++ batched physics, prehistory, tensor, grammar and safe-return kernel | 12–18 |
| MAPR/DIRECT, PPO, exact pooling/Haar binding and containment audits | 10–15 |
| Row cut, consistent relabel and mechanism observability | 4–6 |
| BCRH scorer, independent checker, exact rational layer and 64 fixtures | 15–24 |
| Panels, corrected inference, branch map and serialization | 8–12 |
| End-to-end conformance, failure injection, reproducibility and CM acceptance | 8–12 |
| **Total standalone envelope** | **61–93 days (about 12–19 weeks)** |

The dominant engineering uncertainty is the independent exact-rational BCRH
scorer/checker plus compact evidence serialization, not the UAV physics loop or
learned model size.

## Prospective runtime and storage cost

The registered learned/panel workload comprises about 34.4 million physical
one-second ticks when 120-second prehistory and 120-second post-event execution
are counted. The exact fixed comparator adds the registered 27.716 billion
logical operations; inference adds at most 79.627 million exact comparisons.

Without an activity-bearing benchmark, the honest planning envelope is:

| Resource | Prospective envelope |
| --- | --- |
| CPU purchase | 200–1,500 core-hours; point planning value about 600 core-hours |
| Elapsed wall | about 2–8 days on a 16-core CPU host with memory-aware 2–4-way worker concurrency |
| Worker memory | 2–6 GiB per worker; 8–16 GiB typical aggregate, 32 GiB conservative ceiling |
| Retained artifacts | 8–30 GiB compressed |
| Scratch/build/checker workspace | 20–60 GiB; reserve 80 GiB to avoid lifecycle pressure |
| Native build and focused conformance | 1–4 core-hours per clean build; included in CPU and engineering totals |
| Exact inference | 2–20 core-hours inside the total; no unbounded tail |

The runtime range is driven by exact-rational bit complexity and the bytes per
BCRH candidate/checker record. Approximately 12.05 million maximum held-out
candidate-decision rows are possible before action-sensitivity and fixture
records. Streaming records, fixed-width canonical integers where proven safe,
and compressed columnar storage preserve exactness while preventing memory from
scaling with the complete candidate set. A later authorized, result-blind
native microbenchmark may tighten throughput and byte-size estimates; it cannot
change the frozen object or serve as a stopping rule.

## Comparison with the old VNFC route

| Dimension | Old full route | BPCR revision 09 | Conservative reduction |
| --- | ---: | ---: | ---: |
| Engineering | 50–98 weeks | 12–19 weeks | about 2.6x–8.2x smaller |
| CPU | `1.1e5–1.01e7` core-hours | 200–1,500 core-hours | at least about 73x smaller using new upper vs old lower |
| Solver tail | unresolved full graph / larger tail | finite fixed-token enumeration, fixed rational DP and bounded scalar inference | unbounded tail removed |

The new object therefore meets the required *bounded and materially smaller*
technical condition. Whether its remaining 12–19 engineering-week opportunity
cost merits construction is a Portfolio decision, not a CM scientific or
allocation judgment.

## Remaining technical unknowns and next owner

- Actual native exact-rational and serialization throughput remains unmeasured
  until a later construction/benchmark envelope.
- The concrete counter-to-normal transform, canonical QR ABI, exact integer
  widths, compressed record schema, and worker count must be frozen during a
  later authorized construction before coordinates.
- No empirical competence, headroom, association activity, efficacy, or
  inference power is known.

Next owner: the paired EM for intake of this technical packet, then Operational
Root and Dedicated Portfolio for a separate construction/no-current decision.
No source, activity, lease, or automatic successor follows from this assessment.
