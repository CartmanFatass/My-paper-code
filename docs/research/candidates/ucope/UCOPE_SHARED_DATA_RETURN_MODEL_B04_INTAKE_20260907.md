# UCOPE shared-data return model B04 — joint scientific intake

Object: `UCOPE-SHARED-DATA-RETURN-MODEL-B04`. Class: **B/EXPLORE**.
Result: **COMPLETE, joint RM-A**, from the prospective half-data datasets 6601 and 6602.
The mean clears the frozen 0.001 usefulness threshold by only 0.00003788248697916916.
One dataset is adverse inside the MEI; the other is positive above it. This is a preliminary
finite-host result with substantial variation, not stable superiority or a C promotion.

## 1. Assignment, evidence checked and engineering boundary

P09-UCOPE-HALF-DATA-01 authorized the prospective card, minimal implementation/checks,
exactly two sequential remote invocations, collection and this joint intake/Chinese brief.
The [card](UCOPE_SHARED_DATA_RETURN_MODEL_B04_SCIENCE_CARD_20260907.md) and
[selection intake](UCOPE_SHARED_DATA_RETURN_MODEL_B04_SELECTION_INTAKE_20260907.md) were frozen
at `414cd77e50061f1dee102645b980886057942183` before either output. Both summaries bind
source `71433bfabb70481def4329e622a838fa0cd9eeec`. Exact commands were committed before
execution at `28d25e709`; CM collection is `9cda381ac8d2090ab366082e74497a0d231c7f5f`
in the [E0 result record](UCOPE_SHARED_DATA_RETURN_MODEL_B04_RESULT_EVIDENCE_20260907.md).

I checked that E0 record against card §§2–5, the affected source diff and both collected
`summary.json` files, adjacent admissions, authoritative `status.json`, supervisor logs
and external `whole_time.txt`. The selected seeds/source, 512 batches, real updates, full
eight-context/three-policy final evaluation, paired primary measurements, acquisition/costs
and plans agree with the card. Runtime declarations are Python 3.10.21, CPU, one scientific
compute thread and 53-bit binary64 mantissas. No required dataset primary is missing.

The affected caller resolves the optional batch argument locally, passes it into collection
and reports that selected count/cost law; historical callers still default to 1,024.
The B04 entry selects 512 and seeds 6601/6602. Model, native host, evaluator, reward/information,
B02 RNG-family literal, scalar update order, ties and fallback are unchanged. CM's three
focused synthetic cases passed in 7.87 s, covering the 512-batch path, historical defaults
and publication; the reused independent affected-path reviewer found no material issue.
I did not repeat those tests, replay an old seed or execute an environment/learner.
Engineering conformance supports readability of the result; it is not performance evidence.

The non-test source diff is 28 additions/4 deletions, including a 23-line B04 entry;
the new focused test has 62 lines. **ENGINEERING_SCOPE_SPEC §4: none added.** No §5
budget breach or unrequested machinery was reported or found in the affected diff.
Evidence-spec §§4, 5.2, 11.4 and 11.8.3, 11.8.5–11.8.8 control this ordinary B intake.

**Integration is separate and complete for the inputs.** Root integrated/pushed accepted
source at `98ee9ec0f`, then prospective binding and collection at `2506a50f8` and
`cd7192bb64050f56a4416d663a04e49aa87cdac5`. Card, E0 and affected source/test surfaces
match that main collection. B03's historical main-index incident is resolved and is not
a B04 dependency. Root next integrates this DM intake/brief commit.

## 2. Frozen reading rule and primary result

Card §3 supplies the following joint rules, applied verbatim:

| Branch | Joint reading rule |
| --- | --- |
| **RM-A** | `Delta_native_bar > 0.001` and `Delta_information_bar > 0.001`, with actual FULL evaluation acquisition in at least one selected dataset |
| **RM-D** | `Delta_native_bar > 0.001` and `Delta_information_bar <= 0.001` |
| **RM-B** | `-0.001 <= Delta_native_bar <= 0.001` |
| **RM-C** | `Delta_native_bar < -0.001` |

Both required datasets are complete. FULL actually acquires in both, with 8,192 and
4,096 final evaluation probes. The separate recorded dataset rules and joint rule yield:

| Independent dataset | Native gain | Information gain | Conditional MC SE, either gain | Dataset branch |
| --- | ---: | ---: | ---: | --- |
| 6601 | -0.0008735351562499955 | -0.0008735351562499955 | 0.0007446457182142347 | RM-B |
| 6602 | 0.002949300130208334 | 0.002949300130208334 | 0.0005641773928187774 | RM-A |
| **Prospective mean, n=2** | **0.0010378824869791692** | **0.0010378824869791692** | **0.0004671170560530268** | **joint RM-A** |

BLIND-minus-IMMEDIATE-4 is zero with conditional paired MC SE zero for each seed and
its mean. Every BLIND root is immediate with period 4, so the reference policies share
the same realized paths. The equal native/information contrast columns are not independent
replications. Zero reference difference does not establish zero training uncertainty.

The independent unit is the prospectively selected training dataset/seed, **n=2**.
Sample SD (`ddof=1`) of either gain is **0.0027031527544139028**. Conditional MC SE of
the mean is `sqrt(SE_6601^2+SE_6602^2)/2 = 0.0004671170560530268`; it describes final
evaluation noise conditional on these fitted policies. The sample SD includes such noise
and cannot precisely identify the underlying seed-population variance from two samples.

The mean's excess over MEI, **0.00003788248697916916**, is much smaller than that conditional
MC SE and the dataset dispersion. The frozen point-estimate rule nevertheless gives RM-A;
I do not add a significance gate, change the MEI or discard seed 6601 after output.
Seed 6601 is adverse inside the native MEI, **RM-B**, not RM-C. No confidence interval,
stable population claim or all-positive-seed requirement is inferred from these two scores.

Offline Python parsed the saved summaries and counts and applied the accepted reading function;
it made zero new environment calls or learner updates. The scientific-tools
`summarize_runs.py` used one selected endpoint per seed/contrast in `scores.csv` and
returned the means/SD above. The input scores are already paired within seed; no second
arm pairing was requested. B02 seed 6401 and B03 seeds 6501/6502 are excluded from this
primary and from its uncertainty calculation.

## 3. Acquisition, native consequences and prediction check

The complete E0 retains all sixteen seed-context entries. The three acquired entries are:

| Dataset / context | FULL evaluation probes | Native = information gain | FULL mean paid component | FULL tails, displayed count 0–6 |
| --- | ---: | ---: | ---: | --- |
| 6601 / LINKED-p13_20-c9_100 | 4096 | **-0.021816406250000003** | -0.049736328124999993 | [6, 6, 6, 4, 2, 2, 2] |
| 6601 / LINKED-p17_20-c9_100 | 4096 | 0.014828125000000039 | -0.049335937499999996 | [6, 8, 6, 2, 2, 2, 2] |
| 6602 / LINKED-p17_20-c9_100 | 4096 | 0.023594401041666671 | -0.050901692708333328 | [6, 6, 6, 2, 2, 2, 2] |

The remaining thirteen seed-context entries have zero native/information difference.
FULL's overall probe frequencies are 0.25 and 0.125; overall mean paid components are
-0.012384033203125 and -0.006362711588541666. BLIND/IMMEDIATE-4 never acquire.
The loss in the first row is a native return loss after paying, not a proxy-only deficit.
Its FULL mean return is 0.7761875 versus 0.79800390625 for the reference. It outweighs
seed 6601's useful p17 acquisition in the uniform eight-context average.

The strongest support is positive paid-acquisition value in LINKED-p17_20-c9_100 in both
new datasets, together with the above-MEI joint point estimate. The strongest current
contradiction to robust usefulness is seed 6601's additional harmful acquisition and adverse
overall score. Averaging across the two seeds gives -0.010908203125000002 at p13/c9 and
0.019211263020833355 at p17/c9; the other six context averages are zero. These are retained
descriptive outcomes, not newly selected confirmatory subgroups.

The observed chain remains public context → purchase → paid displayed count → count-dependent
duration → sampled native return. Shared training labels update FULL and BLIND; only FULL
can use the current display after paying. This establishes consequences of the observed
probe-and-duration paths. It does not isolate why a fitted root purchased, separate fitting
variation from evaluation noise, or causally attribute the new loss to reduced data.
No new literature claim is needed: the accepted B02 comparator/information route is reused,
and existing false-probe evidence remains relevant without a new prerequisite diagnosis.

The prospective card forecast was joint RM-A, FULL only at LINKED-p17_20-c9_100 in
each dataset, and BLIND immediate throughout both. Scoring its five components:

| Prediction component | Observed | Score |
| --- | --- | --- |
| Joint RM-A | RM-A | match |
| FULL location, seed 6601 | p17/c9 plus harmful p13/c9 | miss |
| FULL location, seed 6602 | p17/c9 only | match |
| BLIND immediate, seed 6601 | all eight contexts | match |
| BLIND immediate, seed 6602 | all eight contexts | match |

**Four of five components match.** The missed action-location prediction is material to
the mixed result, even though the joint branch forecast matches. Owner prediction:
**not taken (unattended)**; no prediction reply was present at intake.

## 4. Exposure, receipts and complete-invocation cost

| Actual quantity | Seed 6601 | Seed 6602 | Both |
| --- | ---: | ---: | ---: |
| Training batches | 512 | 512 | 1024 |
| Training episodes | 131072 | 131072 | 262144 |
| Training paid-probe / immediate episodes | 65536 / 65536 | 65536 / 65536 | 131072 / 131072 |
| Scalar value updates | 196608 | 196608 | 393216 |
| Histogram increments | 65536 | 65536 | 131072 |
| Final evaluation episodes | 98304 | 98304 | 196608 |
| Complete episodes | **229376** | **229376** | **458752** |
| Actual host-event transitions | 901120 | 876544 | 1777664 |
| Complete probe episodes | 73728 | 69632 | 143360 |
| Committed period units | 984902 | 983034 | 1967936 |
| Probe time units | 147456 | 139264 | 286720 |

Each fresh dataset initializes 264 values at zero, occupies all of them, and makes 65,536
updates each to FULL, BLIND and shared IMMEDIATE. The 56-bin histogram is fully occupied.
The first observed-value step size is 1; a relative displacement to zero initialization
is undefined. FULL displacement L2 is 9.927680447628749 / 9.936797331506643; E0 and
saved summaries retain all component L2/max movements. These are scalar incremental-mean
updates, not optimizer steps. Shared labels do not multiply environment episode counts.

Machine-generated actual exposure:
`datasets=2; seeds=[6601,6602]; batches_per_dataset=512; train_episodes=262144;
scalar_value_updates=393216; histogram_updates=131072; eval_episodes=196608;
total_episodes=458752; actual_host_events=1777664; new_intake_learner_exposure=0`.

Both commands ran on remote `wsl_4070` / `hmasd-wsl-node`, CPU binary64 and one scientific
thread, with separate fresh state/output roots at the bound source. External whole-command
timeout was 600 seconds with no extra allowance, enclosing adjacent admission and the complete
runner, including imports/setup, collection/fits, full evaluation, both publications and exit.

| Receipt | Seed 6601 | Seed 6602 |
| --- | --- | --- |
| Adjacent admission UTC | 2026-09-07T19:07:43.844963Z | 2026-09-07T19:08:49.160077Z |
| Physical / effective available bytes | 15653625856 / 15653625856 | 15668584448 / 15668584448 |
| Complete external wall | 4.71 s | 4.71 s |
| External peak RSS | 21088 KiB | 20856 KiB |
| Runner wall | 4.655675072979648 s | 4.62867763498798 s |
| Supervisor terminal state | finished, exit 0, no tmux | finished, exit 0, no tmux |

Both destination admissions exceeded 4 GiB. Complete invocation walls sum to **9.42 s**,
within 600 s each and 1,200 s summed. The supervisor's second-resolution first-start to
second-finish interval is about 70 s, including intervening control time; it is not the
sum of invocation wall or aggregate CPU work. CPU work and scratch are unmeasured.
Raw `resources_unmeasured` is preserved despite the separately recorded external wall/RSS;
this optional-resource gap does not invalidate the non-resource primary.

Scoped usage is **9.42 s for one valid complete B04 two-dataset comparison**; source
preparation, focused checks, control intervals and the direction's full historical cost
are not included. There was no real-data pilot, old-seed replay, third dataset or extra
evaluation. Seed 6602 followed the terminal first result irrespective of its adverse sign.

## 5. Bounded scientific reading and retained evidence

**Accepted claim:** at 512 batches this shared-data controller shows an above-MEI joint
point estimate of useful paid acquisition on two fresh finite-host datasets, with one
within-MEI adverse dataset and one above-MEI positive dataset. The tiny joint margin,
material dispersion and observed false purchase limit repeatability. This is enough to
consider a bounded follow-up, not enough for stable superiority or promotion.

B03 is separate prior evidence: its mean 0.0024423014322916717 and dataset SD
0.0012263883236204184 came from different seeds at 1,024 batches. B02's sole positive
6401 outcome remains separate. B04 has no paired 1,024-batch arm, so the numerical change
from B03 cannot estimate a causal budget effect, equivalence, percentage of benefit
retained, minimum sufficient data or an optimum learning curve. No five-seed pooled mean
is substituted for the prospective B04 primary.

B01's two native-return nulls, historical false-probe losses, full-competence limits and
small host headroom remain contrary evidence. B02 changed learner/exploration/precision
together, so none of these follow-ups locates B01's cause or establishes architecture/
precision superiority. Fitted-value and evaluation variation remain surviving alternatives
for the observed mixed signs; they have not been causally separated.

The binding structure remains **systems / information flow**. This finite host does not
instantiate multi-agent partial observability or other-agent non-stationarity; no generic
MARL, variable-population, lifetime or transfer conclusion follows. There is no new tuned
generic current-host headroom record; the old oracle/reference diagnostic is not an exact
upper for sampled scores. The retained-policy/root-residual numerical-locus family remains
stopped. No historical quarantine, recast count or family/Portfolio disposition changes.

## 6. Decisions this intake produces

**Decision 1 — object-tier result intake.** Options: (a) accept both complete datasets and
apply joint RM-A; (b) limit a concretely damaged required primary; (c) retain technical
facts only if no complete comparison exists. Recommend/select **(a)**: the committed-source
summaries, real counts, paired measurements, acquisition and receipts agree with the frozen
card. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
The close margin changes the bounded interpretation, not the frozen reading rule.

**Decision 2 — object-tier next-question recommendation; close call.** Options: (a) recommend
preparing two more independent 512-batch datasets with unchanged comparison and final
evaluation, preserving every outcome; (b) recommend no additional 512-batch follow-up now
and retain this evidence. Recommend/select **(a), as a returned preparation recommendation
only**. There is a real positive native signal in the same context in both datasets,
while the extra harmful purchase shows that variation now matters to the question. Another
same-budget pair would provide new independent learning outcomes before another budget cut.
Option (b) is credible because the present mean barely clears MEI and neither stable
usefulness nor the likely information value of another pair is established. This is a
**close call**, not an automatic continuation triggered by the RM-A label.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

Owner-facing recommendation, quoted verbatim in the close-call packet:
建议向 Root 返回“准备两个新的 512 批次独立数据集”的方案，比较器和最终评估不变，保留所有结果；这次只执行建议记录，不分配新运行。均值刚过门槛且一组有额外购买亏损，因此这是接近取舍，也可选择暂不继续。

For next-command planning only, two proposed fresh 512 × 256 datasets would require
229,376 complete episodes and 196,608 scalar updates each, **458,752 / 393,216 summed**,
with unchanged FULL/BLIND/IMMEDIATE-4 and 4,096 final episodes/context/policy.
The dominant work is two collections, shared-label fits and three final policies ×
eight contexts × 4,096 evaluations each. The per-dataset cost law stays
`T_init + 512*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
The present observed 4.71 s each / 9.42 s summed is a same-host planning point, not a
bound or future guarantee; phase coefficients are unmeasured. Candidate caps remain
600 s each / 1,200 s summed, **unallocated here**. No diagnostic, policy search, cost pilot
or positivity prerequisite is proposed, and no further training-budget cut is selected.

This selects the recommendation only. No new seed IDs, card, prediction, source binding,
budget allocation, CM task, invocation or Pro request is frozen or dispatched. P09 ends
with delivery of this intake/brief. Root returns this direction-local recommendation to
Portfolio for next-command planning; this is no priority, capacity, lifecycle or object-family
action. The current two accepted handles are terminal and no execution gap remains.

## 7. Owner boundary and durable records

At the clean intake boundary, `item.py reviews --json` returned `[]` on main and no
UCOPE ledger owner override was present. The owner prediction is not taken; no absent
reply is fabricated. Existing card item `20260907-ucope-005` remains asynchronous.

Owner flag: **close-call** for Decision 2. Its P2 item is created through the owner
console with both options, recommendation, actual recommendation-only choice, positive
and adverse evidence, cost and the audit selection row. Ordinary result facts and the
brief remain in these records under the current P1/P2-only rule. No critic dissent is
overruled, and no second recast or C consumption occurs.
Item: [20260907-ucope-006](../../portfolio/owner/inbox/2026-09-07/20260907-ucope-006.json),
linked to audit row 51. Its auto-applied choice is the preparation recommendation only;
publishing it does not wait for an owner reply or authorize an invocation.

The Chinese [owner brief](../../portfolio/owner/briefs/ucope/2026-09-07_shared-data-return-b04.md)
accompanies this valid result. DIRECTION is updated only with accepted bounded science,
strongest support/contradiction, surviving uncertainty and the unlaunched next discriminator.
The [audit ledger](../../portfolio/audit/2026-09-07.md) records both delegated decisions.

## 8. Evidence paths and return boundary

The [CM E0 record](UCOPE_SHARED_DATA_RETURN_MODEL_B04_RESULT_EVIDENCE_20260907.md) retains both
exact commands, prospective source, focused acceptance, every context/plan, exposure and receipts.
Original roots are
`/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907/temp/directions/ucope/exp/shared-data-return-b04-seed<seed>/`.
Collected copies are under the same relative `temp/directions/ucope/exp/` roots in
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, for seeds 6601 and 6602.
Each contains `summary.json`, `resource_admission.json`, `status.json`, `supervisor.log`
and `whole_time.txt`. Offline calculations are in `shared-data-return-b04-intake/`
(`analysis.json`, `scores.csv`, `run_summary.json`) beneath that experiment directory.

Returned decision: **object-tier COMPLETE / joint RM-A**, with the mixed-outcome ceiling above.
**Next discriminator:** another prospectively selected independent pair at the same 512-batch
budget, if a subsequent command selects it, to observe useful acquisition and harmful-purchase
variation with every sign retained. **Next owner:** Root integrates this intake/brief and returns
the close-call preparation recommendation to Portfolio. No further experiment or provider action
was taken by this intake.
