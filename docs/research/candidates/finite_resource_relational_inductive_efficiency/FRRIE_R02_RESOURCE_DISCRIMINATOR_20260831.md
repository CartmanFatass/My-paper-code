# FRRIE R02 value-blind resource-discriminator audit — 2026-08-31

Status: `ENGINEERING_AUDIT / NO_RESULT / NO_EXECUTABLE_DISCRIMINATOR /
R02_PRODUCTION_REPAIR_REQUIRED`

## Engineering conclusion

The requested R02 resource discriminator cannot currently be implemented or run as an honest
complete-production observation. The repository contains the package-owned C++ environment ABI,
the exact actor/critic and RSCF/Adam primitives, deterministic work accounting, and checkpoint
codecs, but it contains no production trainer/orchestrator that connects those surfaces over one
complete block, much less 916 blocks. The production runner explicitly stops with
`ProductionTrainingUnavailable`, and prospective preflight explicitly retains
`RESOURCE_RUNTIME_CONFORMANCE_UNOBSERVED`.

Performance disposition for the R02 production path: **`REPAIR_REQUIRED`**. The complete
trainer/orchestrator, process-tree monitor, fixed worker scheduler, and end-to-end checkpoint/result
transaction are missing. A TEST-only micro-path cannot upgrade that disposition.

No `resource_probe.py`, probe CLI, or probe test is retained. An initially drafted classifier was
withdrawn after Portfolio fixed the decision boundary: with the current implementation it could
establish only the already-known raw checkpoint byte floor plus `UNKNOWN` for the material runtime
resources. That would be dead code and would not change the investment decision. No R01 or R02
root, ancillary word, RNG master, scientific model, production checkpoint, episode, panel, or
result was created.

This is an engineering conclusion, not `PHY_TRUST`/`EDGE_FLEX` polarity and not a Portfolio
lifecycle decision.

## Frozen engineering question and acceptance

The requested observable was a value-blind resource record for the exact successful-branch R02
work, under one plan frozen before observation, that could answer whether the purchase was already
obviously disproportionate or remained uncertain.

An accepted observation would have had to cover the same local production surfaces and the same
work meaning:

- package-owned `FRRIE_NATIVE_STEP_ABI_V2_FP32` reset/observe/step/snapshot/restore;
- the exact 35,513-parameter CPU FP32 actor/critic for both learned arms;
- the exact RSCF factual-audit and seven-nonfactual-continuation law;
- one full-batch backward call and the frozen projected Torch Adam update for every update;
- the update-512 direct optimizer-state and canonical checkpoint codec;
- the complete training, evaluation, checkpoint, and terminal publication chain;
- one fixed process/worker/thread/native-width schedule; and
- stage and end-to-end wall time, scientific-work throughput, process-tree peak RSS, process-tree
  CPU and worker occupancy, scratch/durable high-water marks, logical and operating-system I/O,
  and checkpoint serialization/read/restore time.

The observation and all artifacts would have had to be `TEST_ONLY/NON_RESULT`, create-once, and
disjoint from manifest output/checkpoint roots. It could not read, retain, compare, or publish arm
returns, contrasts, Bernoulli counts, support state, projection contact, action TV, endpoint
primitives, or any other question-relevant quantity. Execution, concurrency, stage counts, and
stop rules could not adapt to such quantities.

Non-goals were treatment inference, prevalence, a new block count, a new stopping rule, R01
activation, R02 registration, root generation, a resource-budget choice, or a Portfolio GO.

## Exact target work; not runtime evidence

For 916 complete blocks and both learned arms, the accepted ledger is:

| Work item | Exact count |
| --- | ---: |
| complete blocks | `916` |
| environment slots | `4,667,408,384` |
| conventional static FLOPs | `3,626,968,371,982,336` |
| backward calls | `937,984` |
| Adam steps | `937,984` |
| evaluation opportunities | `3,751,936` |
| learned policy decisions | `48,990,904,320` |
| suffix future actor steps | `3,301,703,680` |
| learned-arm update-512 states | `1,832` |

These counts preserve the update-512 four-condition mean-return object. They are not observations
of wall time, hardware FLOP rate, memory, filesystem behavior, completion probability, or safe
concurrency.

One direct lower bound is available without opening any scientific state. One learned-arm state
has `35,513 * 4 = 142,052` parameter bytes and two equally shaped Adam-moment arrays. Therefore the
916-block two-arm panel contains at least

```text
916 * 2 * 3 * 142,052 = 780,717,792 bytes
```

of raw parameters plus first and second moments. This excludes optimizer-step words, codec
headers, base64 expansion, the embedded manifest/packet/native/work records, filesystem metadata,
the root and ancillary packets, panel output, staging, and any retained monitor record. It is a
strict raw-byte floor, not a durable-storage estimate. Approximately 0.781 GB alone is not a
demonstration that the overall purchase is disproportionate.

## Direct repository observations

### The production chain stops before training

`runner.guard_v2_production_run` validates the manifest and immediately raises the frozen inference
blocker. The older `guard_production_run` also ends with
`ProductionTrainingUnavailable("... no production FRRIE trainer ...")`. There is no loop that
materializes one production block through all 512 updates, evaluation, checkpoint publication, and
terminalization.

The exposed V2 functions are composable primitives, not a production route:

```text
sealed packet -> [missing production block scheduler/trainer]
              -> native ABI + policy/RSCF/Adam primitives
              -> checkpoint/evaluation codecs
              -> [missing monitored atomic result transaction]
```

Consequently there is no exact invocation whose elapsed time can be scaled to 916 without
substituting a different implementation.

### Native batching and workers are nominal bindings, not an observed schedule

The C++ ABI accepts a bounded batch count up to `native_width`. The Python
`PackageExternalActionEnvironment` nevertheless allocates one state lane and calls every native
operation with `batch_count=1`. Its docstring permits a future bounded worker to group instances,
but no such grouping worker, deterministic parent reducer, 1/2/4-worker equivalence record, or
occupancy observation exists.

Thus `native_width`, `workers`, and `threads` in a valid manifest bind intended resources but do
not prove that production work is vectorized or parallelized. Static presence of the batch ABI is
not throughput evidence.

### The resource monitor is declarative

`preflight._resource_monitor_contract` names the correct future measurements and the abort-on-
ceiling rule. It also states `observed_by_preflight=false`, provides no host availability snapshot,
and is emitted alongside `RESOURCE_RUNTIME_CONFORMANCE_UNOBSERVED`. No code follows the result
process and its descendants through atomic terminal publication while sampling those fields.

### R01 V2 is not an R02 execution contract

The current V2 manifest and packet require the R01 experiment ID, 24 distinct record labels and
roots, the 28-member inactive analysis family, and the R01 support structure. R02 instead has a
fixed `L_star`, 916 iid roots with replacement, legal duplicate root bytes, four 1075-bit ancillary
words per row, no stochastic support gate, and a four-count result map. Exercising current V2 as if
it were R02 would change the scientific population and completion law.

## Bounded TEST-only observation and why it is inadmissible for extrapolation

A fresh non-result memory admission was run before a bounded engineering smoke. It observed both
physical and effective available memory of `18,225,672,192` bytes, above the 4 GiB safety floor.
This established only that the small smoke could start; the scratch receipt was removed when the
probe objective was withdrawn.

The bundled Python supplied NumPy and CPU Torch 2.7.0 but initially lacked Torch Adam's `sympy`
dependency. After supplying dependencies in an isolated ignored TEST namespace, the existing

```text
run_test_only_v2_chain(exercise_package_native=False)
```

completed in `4.543644999997923` seconds and reported that it published no scientific fields.
This observation is deliberately rejected as R02 performance evidence because that helper:

- uses `TestOnlyExternalEnvironment`, not the package C++ environment;
- captures only one synthetic episode graph at each training roster for each arm and reuses those
  tensors across the 64 batch positions;
- executes one optimizer update per arm rather than 512 updates per arm and block;
- does not execute production evaluation;
- uses an in-memory `torch.save` TEST checkpoint rather than the direct production checkpoint
  transaction; and
- did not collect process-tree RSS, scratch/durable high-water marks, process I/O, or worker
  occupancy.

Multiplying its elapsed time by updates or blocks would silently replace the production workload
and is not a conservative bound. The initial missing dependency is an engineering environment
fact, not evidence that the R02 workload is infeasible.

## Falsifiable disposition rule

Any future resource observation must seal five resource ceilings before execution:

```text
W = maximum wall seconds
C = maximum process-tree CPU core-hours
M = maximum process-tree peak RSS bytes
S = maximum scratch high-water bytes
D = maximum durable high-water bytes
```

Only two value-blind conclusions are permitted:

1. `REJECT_OBVIOUSLY_DISPROPORTIONATE` if a directly observed or exact conservative lower bound
   for the unchanged complete object is already greater than its sealed ceiling; or
2. `UNCERTAIN_NOT_FEASIBLE_EVIDENCE` otherwise.

There is no `FEASIBLE`, `GO`, or `PERFORMANCE_READY` branch from a bounded probe. Passing a probe
cannot upper-bound the 916-block path. A throughput projection may be reported only with its exact
scaling assumptions and is never decision-eligible unless those assumptions are independently
shown conservative for the same complete production chain.

For the current tree the lower-bound vector is:

```text
wall seconds       unknown; no positive conservative production lower bound measured
CPU core-hours     unknown; no positive conservative production lower bound measured
peak RSS           unknown; complete production state ownership/lifetime is absent
scratch bytes      unknown; complete staging/publication path is absent
durable bytes      >= 780,717,792 raw parameter-plus-moment bytes
```

Therefore a sealed `D < 780,717,792` would immediately reject the purchase. For any larger durable
ceiling, the present evidence remains `UNCERTAIN_NOT_FEASIBLE_EVIDENCE`. The exact static FLOP and
slot counts do not convert that uncertainty into time without an observed same-chain rate.

## Sequential and smaller-object recasts do not repair this resource gap

The capped-2048 Bernoulli SPRT proposal has single-component alternative ASN around `463--467`.
That is not the cost of the four-condition IUT. All four components share each expensive block,
and a successful object waits for `max_j T_j`.

- The dependence-robust bound for `E[max_j T_j]` is about `920.95`, already above fixed `916`.
- The `822.19` estimate assumes cross-component independence that the object does not authorize.
- Worst-case use is `2048` blocks, `2.236` times the fixed-916 work.

Thus single-component ASN cannot be used as a resource discount. The randomized 909-row variant
saves only seven rows and still lacks its finite exact decision-coin law; the approximate 720-row
roster-mixture object changes the claim by allowing one roster to mask another. None supplies a
validated, materially cheaper, architecture-selecting mean-return discriminator.

## Performance disposition and remaining technical risk

| Path | Disposition | Direct reason |
| --- | --- | --- |
| R02 916-block production path | `REPAIR_REQUIRED` | No complete production trainer/orchestrator or result-process resource monitor exists. |
| Current V2 primitives | `TEST_ONLY structural evidence` | Local ABI/model/optimizer/codec contracts exist, but no complete path connects and measures them. |
| Withdrawn bounded smoke | `NOT_APPLICABLE` | It used the TEST environment, abbreviated graphs, and no complete telemetry; it is not a retained execution route. |

The principal remaining risks are not statistical polarity. They are incomplete production state
ownership, unobserved native/model batching, unknown worker determinism, unknown checkpoint and
filesystem amplification, missing process-tree observation, missing abort-to-no-partial-output
semantics, and the incompatibility between the pinned R01 V2 schemas and R02's population/result
law.

## Decision impact and next discriminator

This audit supplies no Portfolio GO and cannot reverse a Root-owned decision to close the R02
purchase. Closing the purchase would preserve package uncertainty; it would not establish equality,
harm, wide-package superiority, noncontact, or absence of a mean-return package effect.

Under the current Portfolio boundary, only either of the following merits reentry:

1. a sound universal first-native-action noncontact proof that closes the architecture choice
   without purchasing sampled returns; or
2. a prospectively exact mean-return discriminator whose dependence-robust total cost is clearly
   below the registered 916-block purchase and whose result would genuinely choose between the
   architectures.

If Root later selects a resource observation as part of such an object, engineering must first
implement the complete result-blind trainer/orchestrator and monitor. Only then should CM freeze one
exact argv, cwd, TEST output root, resource ceiling, worker plan, and stop rule; verify native batch
and 1/2/4-worker equivalence where concurrency is admitted; and run one observed process to a
terminal technical witness. No long production is admissible while disposition remains
`REPAIR_REQUIRED`.

## Checks and evidence boundaries

Directly inspected surfaces:

- `experiments/candidates/finite_resource_relational_inductive_efficiency/runner.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/preflight.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/orchestration.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/native_adapter.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/native/native_abi.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/native/frrie_ridgegate2z_external.cpp`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/policy.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/training.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/state_codec.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/checkpoint.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/work.py`
- the complete focused FRRIE V2 test surface.

The bounded smoke established only that the existing TEST helper can execute one abbreviated
two-arm update after its optional dependencies are present. It did not establish production
throughput, resource conformance, completion probability, or scientific truth. No result-bearing
command was launched.

## Exact authority and evidence paths

- `AGENTS.md`
- `docs/research/portfolio/FIVE_DIRECTION_HANDOFF_20260831.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R01_INFERENCE_RESOLUTION_EVIDENCE_20260831.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R02_MEAN_PRESERVING_IUT_PRO_INTAKE_20260831.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R02_EXACT_LAW_AND_SMALLER_OBJECT_SYNTHESIS_20260831.md`
