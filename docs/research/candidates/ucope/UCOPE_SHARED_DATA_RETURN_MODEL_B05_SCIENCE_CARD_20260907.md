Claim to test: The shared-data count-conditioned return learner produces a useful mean native acquisition gain over BLIND and IMMEDIATE-4 at 512 training batches on another two fresh independent datasets.
Binding structure: **systems / information flow**. The finite coordinator host does not instantiate multi-agent partial observability or non-stationarity; no MARL population claim is made.

# UCOPE shared-data return model B05 — independent same-budget pair

Object: `UCOPE-SHARED-DATA-RETURN-MODEL-B05`. Class: **B/EXPLORE**.
Status: **prospective card and predictions prepared; execution unallocated**.
Authority: **P10-UCOPE-PAIR-PREP-01**, [Portfolio command](../../portfolio/handoffs/2026-09-07-p10-goal-five-directions.md#p10-ucope-pair-prep-01).
This command selects preparation only. The executable handoff is a candidate for a subsequent
Portfolio command; no CM execution assignment, implementation, learner/environment call, pilot,
extra diagnostic, old-seed replay or Pro request is issued here.

## 1. Question, prior evidence and interpretation ceiling

The next observation asks whether useful paid acquisition and harmful-purchase variation recur
on **two new independent datasets at the same 512-batch budget**. This follows the close-call
recommendation in [B04 intake §6](UCOPE_SHARED_DATA_RETURN_MODEL_B04_INTAKE_20260907.md#6-decisions-this-intake-produces),
not an automatic continuation from its joint RM-A label. The selected question needs sampled
learning outcomes; an exact diagnostic or another training-budget cut would answer a different
question and is not selected under evidence-spec §§11.8.2–11.8.3 and 11.9.

B04 remains **mixed**: seed 6601 native/information gain -0.0008735351562499955 (RM-B), seed
6602 gain 0.002949300130208334 (RM-A), mean 0.0010378824869791692. Its excess over MEI was only
0.00003788248697916916, with dataset SD 0.0027031527544139028 and conditional mean MC SE
0.0004671170560530268. The strongest support is positive native paid-acquisition value in
LINKED-p17_20-c9_100 in both datasets. The strongest contradiction is seed 6601's extra purchase
in LINKED-p13_20-c9_100, losing 0.021816406250000003 and making its overall score adverse.

This is outcome-informed B exploration with prospectively fixed new datasets. B02, B03 and B04
remain separate prior evidence and never enter B05's primary or uncertainty calculation.
B01's two nulls and the older false-probe losses remain visible. The retained-policy/root-residual
numerical-locus family stays stopped. No branch establishes stable superiority, explains B01,
isolates the cause of a false purchase, changes a family/Portfolio disposition, or promotes to C.
There is no paired 1,024-batch arm, causal budget effect, budget equivalence or minimum-data claim.

**MEI: 0.001 absolute native return for each contrast.** The same host, costs and reward scale
make the prior usefulness threshold appropriate. There is no tuned generic current-host
headroom record. The historical 0.00267963765625 oracle/reference diagnostic is not a fresh
upper or prerequisite. The existing FULL/BLIND/IMMEDIATE-4 baseline set matches this host's
observation/action/information opportunities and training/evaluation budget and is reused.
The accepted B04/B02 comparator and information route are unchanged; no new literature question
or comparator search is needed for independent datasets alone.

## 2. Fixed datasets, learning and information

Select **6701, then 6702**, before either output. Each starts a fresh process, a newly
zero-initialized 264-value model and integer counts; no prior model, histogram, checkpoint,
episode or result initializes or tunes either fit. Current UCOPE cards, runner records and
local experiment-root names contained no prior use of these seeds at preparation.
Both IDs stay fixed regardless of the first valid sign; failed/adverse seeds are never replaced.

Reuse [B04 card §2](UCOPE_SHARED_DATA_RETURN_MODEL_B04_SCIENCE_CARD_20260907.md#2-prospective-datasets-and-preserved-learninginformation-semantics)
and accepted source `71433bfabb70481def4329e622a838fa0cd9eeec`. The **only changes from B04**
are the two seeds, B05 card/result identity, and separate future output/handle names.
The existing shared runner's `run(out, seed, object_id, batches)` is called with `batches=512`;
its historical CLI defaults and the B04-specific entry point are not edited or repurposed.

Each dataset collects 512 batches × 256 rows, in existing `CONTEXTS` order then `j=0..31`:
16 IMMEDIATE-4 rows followed by 16 PROBE rows per context/batch, support `(2,4,6,8)`.
The actual completed action's sampled full native return updates the incremental observed-action
mean, `q <- q + (R-q)/N`. A probe supplies the same observed label to FULL, then BLIND and the
histogram; the immediate table updates once. Preserve binary64 scalar order, `math.fsum`, ties,
unseen-cell fallback, fixed exploration, reward and probe costs. There is no optimizer or bootstrap.

Private behavior RNG is `random.Random(2006701)` or `random.Random(2006702)`, with one draw per
row including unused immediate draws. Preserve the B02 ancestry literal:
`("UCOPE-SHARED-DATA-RETURN-MODEL-B02", f"seed-{seed}", context_id(c))`.
Training addresses remain `32*u+j`, `u=0..511`, `evaluation=False`; final evaluation uses
`0..4095`, `evaluation=True` and the existing `eval-*` namespaces. The seed separates datasets;
all three policies share exogenous evaluation addresses inside one dataset. No global RNG or
global seed/batch mutation is introduced. Deterministic initialization/selection draws no policy RNG.

Public context → purchase → paid displayed count → chosen duration → sampled native return
→ observed-action learning remains the action/credit path. Only FULL uses the current count
after paying; BLIND ignores it. SEVERED actual marks arrive after duration selection. Neither
latent regime, actual marks, analytic value nor an unchosen-action label enters the fit.
There is no membership, lifetime, partner co-adaptation or temporal-transfer change.

## 3. Primary, completeness and all-outcome reading

Evaluate only the final batch-512 fit: eight contexts × three policies × 4,096 paired fresh
episode indices. Keep every policy/context mean, paired difference, conditional MC SE, root/tail
plan, actual acquisition and paid cost, including losses. Record each dataset's existing RM rule.

The primary is `Delta_native_bar = (Delta_native_6701 + Delta_native_6702)/2`;
the information discriminator is the corresponding FULL-minus-BLIND mean. Within each dataset,
each contrast is the uniform mean over all eight contexts. Also report both BLIND-minus-
IMMEDIATE-4 endpoints and their mean. No prior seed, selected context, better checkpoint or
extra evaluation replaces this complete prospective pair.

The independent unit is the newly collected training dataset/seed, **n=2**, not an evaluation
episode, arm or repeated fit. Report both endpoint scores and sample SD (`ddof=1`). Conditional
MC SE of the mean is `sqrt(SE_6701^2+SE_6702^2)/2`; it describes evaluation noise conditional
on fitted policies and does not substitute for dataset dispersion or identify population variance.
Keep the signs separately, even when native and information contrasts coincide. Do not require
significance or all-positive seeds; two datasets cannot support a stable population conclusion.

| Branch | Joint reading rule |
| --- | --- |
| **RM-A** | `Delta_native_bar > 0.001` and `Delta_information_bar > 0.001`, with actual FULL evaluation acquisition in at least one selected dataset |
| **RM-D** | `Delta_native_bar > 0.001` and `Delta_information_bar <= 0.001` |
| **RM-B** | `-0.001 <= Delta_native_bar <= 0.001` |
| **RM-C** | `Delta_native_bar < -0.001` |

Missing/damaged required primaries make the joint comparison **INCOMPLETE**; retain any
independently trustworthy dataset and its bounded reading. Preserve the existing per-dataset
integrity check for positive native gain without actual FULL acquisition. A telemetry gap
retains `resources_unmeasured` without annulling this non-resource claim.

**How the result will be interpreted.** Above both MEIs, another same-budget pair would support
preliminary useful acquisition and a specifically bounded next question; any harmful purchases
still constrain repeatability. Native gain without the information increment narrows attribution.
Inside the native MEI, practical usefulness remains unresolved/limited at this budget; an opposite
sign weighs against this learner/comparison at 512 batches. I would recommend reporting that limit
before another performance investment. None of these readings pools old outcomes, changes B04,
automatically adds seeds/diagnostics, closes paid-information research or allocates another run.

## 4. Predictions recorded before any B05 output

**DM prediction: joint RM-B**, with low confidence because B04's joint margin is tiny and its
dataset variation is substantial. FULL will acquire at LINKED-p17_20-c9_100 in each new dataset;
at least one of the pair will acquire in an additional context. BLIND will remain immediate in
all eight contexts in each dataset. These are six scored components: one joint branch, two
p17/c9 acquisition predictions, one additional-context prediction and two BLIND predictions.
They are forecasts, not completeness/continuation conditions. Owner prediction: **not taken
(unattended)**. No B05 outcome exists to score during this preparation.

## 5. Machine-generated exposure, cost and candidate execution boundary

[Preparation counts](UCOPE_SHARED_DATA_RETURN_MODEL_B05_PREPARATION_COUNTS_20260907.json)
come from Python standard-library AST reads of the accepted constants/loop bounds and arithmetic,
without importing an experiment module, constructing a model or calling a learner/environment.

| Work | Per dataset | Both datasets |
| --- | ---: | ---: |
| Real training episodes / paid episodes | 131072 / 65536 | 262144 / 131072 |
| Scalar value updates / histogram increments | 196608 / 65536 | 393216 / 131072 |
| Full final evaluation episodes | 98304 | 196608 |
| Complete episodes | **229376** | **458752** |
| Candidate complete wall cap, unallocated | **600 s** | **1200 s summed** |

Prospective machine-generated exposure:
`datasets=2; seeds=[6701, 6702]; batches_per_dataset=512; train_episodes=262144; scalar_value_updates=393216; histogram_updates=131072; eval_episodes=196608; total_episodes=458752; value_entries_per_dataset=264; initial_l2=0; first_observation_step_size=1; new_preparation_learner_exposure=0`.

The first observation can move a value with step size 1; a finite relative displacement ratio
to zero initialization is undefined. Each actual summary must retain component scalar updates,
absolute L2/max displacement, real host transitions and evaluation counts. Shared labels do not
multiply environment episodes; scalar mean updates are not optimizer steps.

Dominant algorithm work is **two independent collections** with the shared FULL/BLIND fit,
followed by **2 datasets × 3 final policies × 8 contexts × 4096 episodes**. IMMEDIATE-4 is a
fixed reference, not a third trained model. There is one selected final checkpoint per dataset,
no policy/trajectory/controller search and no separate training allocation per comparison arm.
The per-dataset runner cost law is
`T_init + 512*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
Parsing both B04 external wall records gives **4.71 s each**: a same-host planning point of
**4.71 s per complete three-policy dataset comparison / 9.42 s summed**. Phase coefficients and
aggregate CPU are unmeasured; probe choices may change cost, so this is no bound or guarantee.
The 600-second complete-dataset cap contains the work of every arm; it is not 600 seconds per
policy. Added result-bearing validation: **zero calls**. Existing affected-path checks are reused;
the preparation checks only counts, source/API facts and command syntax. No timing pilot follows.

If a subsequent command allocates this pair, use remote `wsl_4070` / `hmasd-wsl-node`, Python
`/home/wu/.venvs/hmasd/bin/python`, CPU binary64, one scientific process/compute thread, under
`.codex/hmasd-compute.toml`. The processor is not the estimand; this candidate selects the
recorded remote route only, with no local fallback. Each separate invocation needs destination
admission with physical and effective available memory >=4 GiB immediately adjacent to its runner.
The external 600-second whole-command timeout covers admission, interpreter/import/setup,
collection/fits, full evaluation, both publications and exit. Source staging/control intervals
are separate; no learning or initialization is moved outside the cap.

The [prepared handoff](UCOPE_SHARED_DATA_RETURN_MODEL_B05_EXECUTION_HANDOFF_20260907.md)
binds source, exact commands, fresh roots and existing routes. Future order is 6701 then 6702
after terminal reconciliation irrespective of the first valid sign. A concrete shared integrity
defect or failed fresh admission returns its dependent gap and all complete/partial evidence;
no automatic retry, replacement or third invocation follows. Preparation creates no scientific
run root or accepted handle. Portfolio owns any subsequent allocation; the unresolved existing-CM
identity is a routing fact, not scientific polarity.

**ENGINEERING_SCOPE_SPEC §4: needs none.** No implementation is selected; the existing API and
supervisor suffice. Ordinary source/runner/test budgets remain in force for any separately
authorized repair; this preparation adds zero non-test runtime-source or test lines.
