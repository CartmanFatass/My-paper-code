Claim to test: A fresh count-conditioned return learner can acquire paid information and improve sampled native net return over a count-blind learner fitted to the same episodes and IMMEDIATE-4 on this finite host.
Binding structure: **systems / information flow**. This host does not instantiate multi-agent partial observability or non-stationarity; no MARL population claim is made.

# UCOPE shared-data return model B02 — science card

Object: `UCOPE-SHARED-DATA-RETURN-MODEL-B02`. Class: **B/EXPLORE**.
Status: **scientific selection and card frozen; implementation handoff prepared, not dispatched**.
Root-relayed Portfolio command **P07-UCOPE-CARD-01 (OWNER_DIRECT)** authorizes selection,
this card and its five-item CM handoff only. There is no implementation, experiment or provider
Send in this preparation. The new learner has no accepted executable launch SHA yet.

## 1. Question, source and retained evidence

The next observation decides whether an ordinary sampled-return learner can turn the paid
display into useful native performance, without first explaining B01's failure. Fit two models
on one fresh deliberately exploratory dataset; evaluate their final purchase/duration policies
against each other and IMMEDIATE-4. This is a changed learner/comparator inside the accepted
paid-information mechanism, an **object-tier** choice under the 2026-09-03 unattended delegation.
No direction recast, family reopening, C promotion or Portfolio disposition is selected.

Native source anchor: `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`, with these unchanged modules:

- `experiments/candidates/ucope/conditioning_discriminator_r01/contract.py`: only `CONTEXTS`,
  `context_id`, `K_EVAL`, `MARKS` supply this object's host constants.
- `.../conditioning_discriminator_r01/host.py`: `execute_episode` and its `Execution` result.
- `.../conditioning_discriminator_r01/rng.py`: unchanged environment counter RNG.
- `.../conditioning_discriminator_r01/oracle.py`: `tail_q` remains internal to the environment.

These four files match preparation base `fb7a319da6793ddfd3752f1da4c643ed7ffa8f56` by
`git diff`. This binds the reused native path; the future implementation commit must bind the
new learner and runner before a separately assigned invocation. No new currentness guard is needed.
The old `WorkloadConfig`, learner, odd training support, fold machinery, posterior labels,
retained policies and offset-2,000,000 numerical-locus family are not B02 inputs.

Accepted evidence is [B01 intake §§2–6](UCOPE_NATIVE_RETURN_ACQUISITION_B01_INTAKE_20260907.md)
and [proposal §§1–5](UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md).
B01 is still NR-B: zero final native gain in both seeds despite 126,242 training probes and
2,048 joint updates. Historical PA-B (5/6 versus 6/6) and TW-B tail coverage (6/6 versus 4/6)
keep acquisition plausible; unchanged full competence (3/6 in both arms) and two false probes
losing 0.028562899 each keep native losses central. This experiment does not locate B01's cause.
The proposal's verified DACOM/VIL2C retrieval is reused: downstream action change motivates a
native-return check, not a proxy endpoint, a novelty claim or a new communication implementation.

**Headroom and MEI.** No tuned generic current-host headroom record exists. The historical
oracle/reference gap 0.00267963765625 is only a diagnostic reference. Both comparisons in §4
use **0.001 absolute native return** as their minimum effect of interest: 37.318% of that small
historical gap, a scale worth a bounded follow-up rather than merely a numerical difference.
Reuse IMMEDIATE-4 because public observation, legal action/information, host and evaluation
budget match B01. The new blind learner is trained here; it is not an existing tuned baseline.
B01's actor has different training allocation and numerical semantics, so no architecture,
matched-dose or precision superiority claim against historical B01 follows.

## 2. Real data, information and RNG

Use the eight `CONTEXTS` in their source order: LINKED then SEVERED, reliability 13/20 then
17/20, and cost 9/100 then 7/50. Train and evaluate on even periods `K_EVAL=(2,4,6,8)`.
For every real episode call `execute_episode`; retain its complete `external_return` as the
training target. Its sampled service and native time/energy/probe charges are unchanged.
IMMEDIATE uses period 4. A PROBE pays the native charge and chooses a period through the
count-only `tail_selector` callback. No current display, actual marks, latent regime, service,
reward component or unchosen return reaches the root or tail before its legal observation.
In SEVERED the displayed count is independent of the actual-mark regime; actual probe reward
arrives only after duration choice. Outcome components may be logged after the episode, never
used separately as learner inputs or privileged labels.

Select exactly **one fresh shared-data seed, 6401**. Both models start fresh and share that
single dataset intentionally; they are not two independent training runs.

- Execute 1,024 batches `u=0..1023`, then context in `CONTEXTS` order, then `j=0..31`.
  Each context contributes `j<16` IMMEDIATE-4 and `j>=16` PROBE episodes per batch.
  The context-local training index is `32*u+j`.
- Use one private Python `random.Random(6401+2000000)` behavior stream. Before every training
  row draw exactly one `random()` binary64 uniform; choose `K_EVAL[int(4*uniform)]` for PROBE
  and discard this draw for IMMEDIATE. No other draws use this stream. The probe callback
  ignores its displayed count during this fixed exploratory collection.
- Environment ancestry is `("UCOPE-SHARED-DATA-RETURN-MODEL-B02", "seed-6401", context_id(c))`.
  Training uses `evaluation=False`. Evaluation uses `evaluation=True` and indices `0..4095`;
  its existing `eval-*` namespaces separate it from training. All three evaluated policies
  share the same context/index/ancestry addresses. No process-global RNG or historical data
  are used. Zero initialization and deterministic evaluation consume no policy RNG.

The event/action/learning path is: hidden host event → public-context purchase → paid display
→ duration choice → full realized native reward → observed-action value update → final learned
purchase/action consequence. Collection is deliberately balanced and exploratory, not a policy
search. Episodes reset independently; no bootstrap, discount update, entity replacement,
censoring, roster change, survivor state or partner co-adaptation is part of this host.

## 3. Incremental learner and final policies

Use Python scalar **IEEE-754 binary64** values and integer counts on CPU, one process/compute
thread. No Torch optimizer, mixed precision or parallel reduction is selected. The unchanged
host converts its existing rational constants as before. Update in the row order of §2.
All value entries and counts initialize to zero; the only label is the completed episode's
full native return `R`.

| Learned quantity | Shape | Update on the actual observation |
| --- | --- | --- |
| Shared immediate value `q_I(c)` and count `N_I(c)` | 8 | Each IMMEDIATE-4 episode, once for both policies |
| Conditioned value `q_F(c,n,k)` and count `N_F(c,n,k)` | 8×7×4 | Each PROBE episode with displayed count `n` and chosen `k` |
| Blind value `q_B(c,k)` and count `N_B(c,k)` | 8×4 | The same PROBE episode and return, discarding `n` |
| Display histogram `H(c,n)` | 8×7 | The same PROBE episode, increment the observed count bin |

For each applicable value entry, increment `N`, then perform exactly the ordinary scalar
update `q <- q + (R-q)/N`. On a probe update full, then blind, then histogram; on an immediate
episode update only shared immediate. These are **incremental parameter updates**, not
`optimizer.step` calls. There is one pass, no fitted-target replay, gradient training,
hyperparameter search or model selection. Keeping the data as a stream is sufficient.

After all batches, define `p_hat(n|c)=H(c,n)/sum_m H(c,m)` and
`Q_F(c,n,k)=q_F(c,n,k)` when `N_F>0`, otherwise the corresponding learned `q_B(c,k)`.
An unobserved blind or immediate entry retains zero. Missing full-model cells use this fallback;
they do not require additional sampling, full support or a census. If no probe has yet been
observed in a context, the full policy chooses IMMEDIATE (relevant to partial/synthetic checks).

- **FULL:** compare `sum_n p_hat(n|c)*max_k Q_F(c,n,k)` with `q_I(c)`. Probe only when the
  former is strictly greater; after the current paid display choose `argmax_k Q_F(c,n,k)`.
- **BLIND:** compare `max_k q_B(c,k)` with that same `q_I(c)`. Probe only when greater;
  if probing use `argmax_k q_B(c,k)` regardless of the current displayed count.
- **IMMEDIATE-4:** always commit immediately to period 4, with no learning or paid display.

Ties select IMMEDIATE at the root and the lowest legal period at the tail. Use counts `0..6`
and periods in `K_EVAL` order, with `math.fsum` for the full root expectation. These small sums
and four-action maxima are the deployed policy's calculation over learned values; they are not
enumeration or bounded search over policies/trajectories. Final evaluation uses only the models
after batch 1,024. The possible upward bias from maximizing noisy fitted means is part of the
learner under test and is judged by fresh native return, not corrected with unseen oracle labels.

## 4. Final primary comparison, reading rule and prediction

For each context, evaluate FULL, BLIND and IMMEDIATE-4 on the same 4,096 fresh addresses in §2.
There is no intermediate evaluation or selection of the best checkpoint, context or metric.
The population is the uniform mean of all eight declared contexts. Compute:

`Delta_native = mean_c mean_i (R_FULL(c,i) - R_IMMEDIATE-4(c,i))` — **primary**.

`Delta_information = mean_c mean_i (R_FULL(c,i) - R_BLIND(c,i))` — information discriminator.

Also report BLIND-minus-IMMEDIATE-4, all per-context returns/differences, final root/tail actions,
actual probe counts and paid components by policy. Every local gain and native loss stays visible.
For each paired difference use binary64 `math.fsum` means and sample variance (`ddof=1`) of its
4,096 episode differences in each context. The conditional Monte Carlo SE of its overall mean is
`sqrt(sum_c(var_c/4096))/8`. It describes evaluation noise conditional on this fitted pair.
The independent learning unit is **one shared dataset/seed**; it cannot estimate training-seed
population uncertainty. Episodes, contexts, value cells and the two models do not increase that n.

Apply the following rule to complete, trustworthy primary comparisons, without significance
or all-context-positive requirements:

| Branch | Reading rule | Bounded next recommendation |
| --- | --- | --- |
| **RM-A** | `Delta_native > 0.001` and `Delta_information > 0.001`, with actual FULL evaluation acquisition | A useful acquisition signal; recommend one or two separately bounded fresh independent data seeds with the same comparison, retaining every outcome |
| **RM-D** | `Delta_native > 0.001` and `Delta_information <= 0.001` | Native gain, but the declared information increment is unsupported; retain both gains/losses before selecting any more specific follow-up |
| **RM-B** | `-0.001 <= Delta_native <= 0.001` | No material native gain at this endpoint; a gain against a weaker blind policy alone does not show useful acquisition |
| **RM-C** | `Delta_native < -0.001` | Native loss for this learner/data budget; do not recommend an unchanged extension solely from a local or information-relative gain |

Missing primary output or an incomplete dataset/evaluation is **INCOMPLETE** for the dependent
comparison, with actual counts and independently trustworthy facts retained. A gain over
IMMEDIATE-4 reported without any FULL acquisition contradicts the declared paths and is an
integrity gap to resolve, not evidence for RM-A. Optional resource telemetry gaps are marked
`resources_unmeasured` and do not invalidate this non-resource claim.

**How the result will be interpreted.** Above both MEIs, sampled learned information has local
native value worth a small independent-seed follow-up. Inside the native MEI, this learner has
not established useful acquisition even if conditioning beats blind. Opposite sign bounds the
particular fitted policy adversely. These readings neither identify B01's cause nor refute paid
information generally. A single positive B does not establish stable superiority, exact optimality,
transfer, generic headroom or MARL effectiveness. No branch itself launches the next invocation.

**DM prediction, before B02 output:** RM-A; FULL will acquire in at least one LINKED low-cost
context, while BLIND will remain immediate in all eight. Confidence is low: direct value fitting
and deliberate probe exposure may reveal the small conditional benefit, while fitted-max bias
and action-estimation noise can erase it. Those causal expectations are predictions, not findings.
Score the branch and both action predictions at intake, separately from the unverified mechanism.
Owner prediction: **not taken (unattended)**; no separate prediction item is required.

## 5. Exposure, complete budget and implementation boundary

Python arithmetic from the selected configuration gives this one-dataset allocation:

| Quantity | Work |
| --- | ---: |
| Independent datasets / learned policies / fixed references | 1 / 2 / 1 |
| Real training episodes | 1,024×8×32 = 262,144 |
| Paid / immediate training episodes | 131,072 / 131,072 |
| Full / blind / shared-immediate scalar value updates | 131,072 / 131,072 / 131,072 |
| Value updates / histogram increments | 393,216 / 131,072 |
| Learned value entries / histogram entries | 264 / 56 |
| Behavior uniforms / used probe draws | 262,144 / 131,072 |
| Training host-event transitions | 1,310,720 |
| Final evaluation episodes | 3×8×4,096 = 98,304 |
| Total episodes / possible host-event transitions | 360,448 / 1,507,328–1,900,544 |

**Machine-generated prospective exposure:** `datasets=1; seed=6401; train_episodes=262144;
scalar_value_updates=393216; histogram_updates=131072; value_entries=264; initial_value_l2=0;
first_observation_step_size=1.0; eval_episodes=98304; new_preparation_exposure=0`.
The first observed reward moves its zero-initialized value with step size 1, followed by `1/N`;
there is no suppressed zero-learning regime. Publish actual updates, occupied-entry counts and
L2/max-absolute value movement separately for full, blind and shared immediate. A ratio to zero
initial scale is undefined and must not be reported as a finite optimizer-displacement ratio.
These small learner summaries are exposure evidence, not extra resource telemetry.

The dominant work is one collection, two fits sharing its labels and three sampled evaluations.
There are no nested candidate rollouts or search factors; at most seven counts×four values per
context enter the full root calculation. Added validation is one focused synthetic changed-path
check and rule cases, using existing host evidence, with zero scientific host episodes.

**Cap: 600 seconds for the complete single-dataset invocation**, including process/import
initialization, all data, both fits, all three evaluations and final publication. It is not
600 seconds per model. No auxiliary real-seed smoke, preliminary A, cost pilot or retry allocation
is selected. Runtime of this learner is unmeasured; B01's 8.80/9.67 s are context, not a B02 estimate.
Unknown unit time does not create a new gate; return a concrete inability to honor the cap.
Record whole-process wall and peak RSS with existing tools; any cap breach stays explicit.

Future portable execution follows `.codex/hmasd-compute.toml`: `remote_first`, `wsl_4070`,
`/home/wu/.venvs/hmasd/bin/python`, CPU binary64, one scientific process/compute thread, no GPU.
Processor identity is not the estimand. The existing prospective local-fallback rule may apply
only without an accepted remote process and with exact semantic portability and fresh destination
admission. Every actual invocation needs its adjacent destination `admit-memory` receipt (physical
and effective available memory each at least 4 GiB), detached exact-commit execution through the
existing supervisor, and the existing Root adoption/CM collection path. No process is created here.

**ENGINEERING_SCOPE_SPEC §4: needs none.** Reuse infrastructure; add no worker pool, registry,
guard, retry/resume system, schema layer or telemetry framework. Ordinary §5 limits apply:
2,000 new non-test research lines, 600 runner lines, 30% orchestration as review signal only.

## 6. Five-item CM implementation handoff — prepared only

1. **Deliverable/goal:** implement the B02 real-host streamed return learner, deterministic final
   FULL/BLIND/IMMEDIATE-4 evaluation and compact `summary.json`; return a source commit and focused
   technical acceptance. This initial handoff is implementation plus synthetic checks, with no
   scientific or real-host technical invocation. Root dispatches it separately.
2. **Owned paths/entry points:** new `experiments/candidates/ucope/shared_data_return_model_b02/`,
   `scripts/run_ucope_shared_data_return_model_b02.py`, and corresponding
   `tests/experiments/candidates/ucope/shared_data_return_model_b02/`; technical return belongs in
   this direction's dated intake. Reuse only the native entry points in §1; preserve the old host
   modules and unrelated work. Runtime outputs later belong under
   `temp/directions/ucope/exp/shared-data-return-b02-seed6401/`.
3. **Preserved semantics:** §§2–4 bind data order, fresh RNG, paid/current-count boundary,
   observed-action full-return labels, shared data/immediate fit, binary64 updates, ties,
   final-only evaluation and the two comparisons. Ordinary in-scope code organization is CM's;
   report a concrete semantic ambiguity rather than silently changing those definitions.
4. **Acceptance:** one focused synthetic check covers observed-action update/one-time shared
   immediate accounting, blind/count timing, unseen-cell fallback, final action calculation and
   primary publication; cover the §4 branch boundaries. Reuse the accepted unchanged host path;
   retain CM's independent affected-path review for changes affecting reward/information/comparison.
   Return actual source/line scope and check evidence under evidence-spec §§4, 5.2, 11.4,
   11.8.5–11.8.8 and ENGINEERING_SCOPE_SPEC §§3–5. No historical replay, support census, oracle
   maximum, exact bit-equality test or extra contract is required.
5. **Budget/stop:** §5 fixes one future dataset and complete 600 s cap; current implementation
   has **zero result-bearing invocations**. Use the ordinary five-minute focused test allowance;
   long portable checks use committed source on the configured remote route. Stop the dependent
   work and return a concrete reward/information/RNG/budget/source gap if present. Routine in-scope
   repairs continue to acceptance; tests passing do not constitute scientific value or launch.

The selection intake records authority, options and the actual owner-item receipt. This card's
freeze does not modify B01's evidence or the stopped retained-policy family.
