# UCOPE shared-data return model B03 — joint scientific intake

Object: `UCOPE-SHARED-DATA-RETURN-MODEL-B03`. Class: **B/EXPLORE**.
Result: **COMPLETE, joint RM-A**, from exactly the prospective datasets 6501 and 6502.
This is a repeated preliminary useful-acquisition signal on the finite coordinator host.
It is not stable superiority, a MARL population result or a C promotion.

## 1. Assignment, evidence checked and engineering boundary

P08-UCOPE-TWO-DATASETS-01 authorized the prospective card, minimal implementation/checks,
two sequential remote invocations and this joint intake. The [card](UCOPE_SHARED_DATA_RETURN_MODEL_B03_SCIENCE_CARD_20260907.md)
and [selection intake](UCOPE_SHARED_DATA_RETURN_MODEL_B03_SELECTION_INTAKE_20260907.md) were
committed at `e185501a7e5b7302a63b835dee8c10851d9d1f84` before either result.
Both summaries bind implementation `af7c7d516bbd9466a2775d9cb1e29582be1aaa36`.
Exact commands were committed prospectively at `0c0514d83`; complete CM collection is
`9132895b3b2de1e81321e5ce5ae81f61a86bea95` in the [E0 result record](UCOPE_SHARED_DATA_RETURN_MODEL_B03_RESULT_EVIDENCE_20260907.md).

I checked that record against card §§2–5, the accepted seed-propagation diff and the two
collected `summary.json` files, adjacent admissions, authoritative `status.json`, supervisor
logs and external `whole_time.txt`. The direct outputs contain the selected seeds/source,
complete batches and updates, all eight final contexts and three policies, primary paired
differences, actual paid acquisition and final plans. Their runtime declarations are CPU,
one compute thread and 53-bit binary64 mantissas. No required primary is missing.

The changed caller passes seed explicitly into collection and final evaluation; private
behavior RNG and all training/evaluation ancestry receive it. The B02 RNG-family literal and
default seed 6401 remain unchanged. Each `run` constructs a new return model. Source review
confirms no changed native host, reward/information boundary, update order, fallback or tie rule.
CM's two synthetic seed/publication tests passed in 0.56 s; the reused independent reviewer
found no material issue and inspected five saved synthetic summaries. I did not repeat these
tests or execute another environment/learner. This accepts the affected implementation path;
test success alone supplies no performance conclusion.

Non-test source change is 37 additions/14 deletions, including a 23-line B03 runner; tests
are 79 additions/1 deletion. **ENGINEERING_SCOPE_SPEC §4: none added.** No §5 budget breach
or unrequested machinery was reported or found in the affected diff. Evidence-spec §§4, 5.2,
11.4 and 11.8.3, 11.8.5–11.8.8 control this ordinary B intake.

**Integration is separate.** Root reports that main cannot create `.git/index.lock`
(`Permission denied`); main remained `70b419a2ba29a1b912d438c1301f8a9543faf42b` at my read.
Root's subsequent 2026-09-07 instruction explicitly requests this final intake/brief commit
while that integration gap remains. Thus the scientific record is completed on `codex/ucope`
from the collected committed source; it does not assert main integration or diagnose the
permission cause. No integration failure is converted into scientific polarity or a relaunch.

## 2. Frozen reading rule and primary result

The joint reading rules below are verbatim from card §3:

| Branch | Joint reading rule |
| --- | --- |
| **RM-A** | `Delta_native_bar > 0.001` and `Delta_information_bar > 0.001`, with actual FULL evaluation acquisition in at least one selected dataset |
| **RM-D** | `Delta_native_bar > 0.001` and `Delta_information_bar <= 0.001` |
| **RM-B** | `-0.001 <= Delta_native_bar <= 0.001` |
| **RM-C** | `Delta_native_bar < -0.001` |

The card also says: “Any missing/damaged required dataset primary makes the **joint** comparison
INCOMPLETE”; both required primaries are complete. Actual FULL acquisition occurs in both.
The selected mean uses **6501 and 6502 only**, with equal dataset weight and the frozen uniform
mean of eight contexts inside each dataset. No endpoint, policy or seed was selected after output.

| Prospective dataset | FULL − IMMEDIATE-4 | FULL − BLIND | Conditional MC SE of either contrast | BLIND − IMMEDIATE-4 | Per-dataset branch |
| --- | ---: | ---: | ---: | ---: | --- |
| 6501 | 0.0033094889322916716 | 0.0033094889322916716 | 0.0005704859005940954 | 0 | RM-A |
| 6502 | 0.0015751139322916715 | 0.0015751139322916715 | 0.0005165530745357663 | 0 | RM-A |

| Joint endpoint, n=2 | Mean | Dataset sample SD, ddof=1 | Conditional MC SE of mean |
| --- | ---: | ---: | ---: |
| FULL − IMMEDIATE-4 | **0.0024423014322916717** | **0.0012263883236204184** | **0.0003847990519703138** |
| FULL − BLIND | **0.0024423014322916717** | **0.0012263883236204184** | **0.0003847990519703138** |
| BLIND − IMMEDIATE-4 | 0 | 0 | 0 |

Both primary means exceed their 0.001 absolute MEI by 0.0014423014322916716. Applying the
frozen rule gives **joint RM-A**. Both per-dataset signs happened to improve; their agreement
was neither an acceptance requirement nor a condition for executing the second dataset.

The independent unit is the training dataset/seed, **n=2**. I passed one already paired
endpoint score per dataset/contrast to scientific-tools `summarize_runs.py`, without `--paired`
because these inputs already are within-dataset paired differences. The tool's sample SD
matches the table. Conditional MC SE uses the frozen `sqrt(SE_6501^2+SE_6502^2)/2` formula.
The SD includes evaluation noise and is an imprecise two-dataset dispersion estimate; the
conditional MC SE is not a substitute for training-population uncertainty. No confidence
interval, significance claim, variance decomposition or stable superiority is inferred.

Prior evidence remains separate and is excluded from every B03 primary calculation:

| Prior object/dataset | Native and information gain | Conditional MC SE | Original reading |
| --- | ---: | ---: | --- |
| B02 / 6401 | 0.0030012207031250046 | 0.0005533139087041887 | RM-A, one dataset |

This prior outcome motivated B03's prospective follow-up. It is not a third prospective B03
replicate, and it was neither replayed nor silently pooled.

### Where the native consequence occurs

FULL purchases only in **LINKED-p17_20-c9_100** for both datasets: 4,096 actual evaluation
probes each, frequency 1/8 over the uniform host population. Its context native/information
gains are 0.026475911458333373 and 0.012600911458333372, after mean paid components
−0.049557291666666663 and −0.049957682291666659. The other fourteen seed-context entries
follow the immediate reference and have zero paired native difference. No context-mean
native loss was observed; this does not mean every sampled episode improves.

BLIND chooses IMMEDIATE-4 in all eight contexts in both datasets. Thus both references
actually deploy the same behavior, and the two equal contrast columns are not independent
replications. A zero paired SE for BLIND-minus-IMMEDIATE-4 describes these identical paths,
not zero environment or population uncertainty.

The purchased-context FULL tails differ: 6501 uses `[6,8,6,6,2,2,2]`, while 6502 uses
`[6,8,6,4,2,2,2]` for displayed counts 0–6. Their common root location is repeated evidence;
they are not the identical fitted controller. The smaller second gain could reflect fitted
policy and evaluation variation; these observations do not isolate their separate causes.

## 3. Actual exposure and retained counts

| Quantity | Each selected dataset | Both datasets |
| --- | ---: | ---: |
| Training batches | 1024 | 2048 |
| Real training episodes | 262144 | 524288 |
| Training paid / immediate episodes | 131072 / 131072 | 262144 / 262144 |
| Private behavior uniforms | 262144 | 524288 |
| Scalar value updates | 393216 | 786432 |
| Histogram increments | 131072 | 262144 |
| Final evaluation episodes | 98304 | 196608 |
| Complete episodes | 360448 | 720896 |
| Actual host-event transitions | 1531904 | 3063808 |
| Complete probe episodes | 135168 | 270336 |
| Complete probe-time units | 270336 | 540672 |

For each dataset, training transitions are 1,310,720. Final FULL/BLIND/IMMEDIATE-4 each
have 32,768 episodes, with transition counts 90,112/65,536/65,536. Complete committed-period
units are 1,575,264 for 6501 and 1,574,200 for 6502, sum 3,149,464. All final evaluations
are at batch 1,024; no earlier checkpoint comparison or additional fit was selected.

Each dataset has 224 FULL values, 32 BLIND values and 8 shared immediate values; each
component received 131,072 scalar updates. FULL L2 movement is 9.917759949585742 and
9.949343574772914; the CM record retains every component's absolute L2/max movement,
fitted values and integer counts. Initial L2 is zero, first observation step size is one,
and the relative movement ratio to zero is undefined. These are nonzero observed-return
updates, not Torch/Adam optimizer steps. Shared labels do not double environment exposure.

Machine-computed actual exposure: `datasets=2; seeds=[6501,6502]; train_episodes=524288;
scalar_value_updates=786432; histogram_updates=262144; eval_episodes=196608;
total_episodes=720896; host_event_transitions=3063808; value_entries_per_dataset=264;
initial_l2=0; first_observation_step_size=1`. This intake adds zero host or learner exposure.

## 4. Receipts, resource limits and technical validity

| Dataset | Adjacent admission UTC | Physical/effective available bytes | External whole wall | Peak RSS | Authoritative terminal |
| --- | --- | ---: | ---: | ---: | --- |
| 6501 | 2026-09-07T17:47:01.749948Z | 15666896896 / 15666896896 | 8.00 s | 20960 KiB | finished, exit 0, tmux inactive |
| 6502 | 2026-09-07T17:48:21.606275Z | 15664783360 / 15664783360 | 10.46 s | 21068 KiB | finished, exit 0, tmux inactive |

Both receipts pass 4 GiB on the actual `wsl_4070` destination. The accepted commands join
that fresh admission to the exact runner under one external 600-second timeout and whole
timer. Whole wall covers admission, startup/import, collection/fits, evaluation, publication
and exit. The runner's narrower walls are 7.907807689975016 and 8.441768046992365 s;
the external measurements govern cap compliance. Neither timeout fired.

**18.46 s summed invocation wall** is below the 1,200-second sum and both individual
600-second caps. The supervisor boundaries span about 91 seconds from first start to
second exit, including intervening control/collection; earlier staging is separate. This is
not aggregate CPU work. CPU and scratch peaks and total historical direction cost remain
unaggregated. Usage for this valid B03 comparison is 18.46 s across its two dataset invocations.

Raw summaries retain `resources_unmeasured`. External whole wall and RSS are directly
measured facts; they do not manufacture missing optional telemetry. Under §11.8.7 this
non-resource result remains valid. There is no missing learner-side primary dependency.
No third seed, pilot, retry, replay or extra endpoint was executed. B objects have no
C-class consumption state; completion does not grant another invocation.

## 5. Prediction check and bounded scientific interpretation

| Frozen prediction component | Observation | Score |
| --- | --- | --- |
| Joint RM-A | Both means above 0.001 with actual FULL acquisition | matched |
| 6501 FULL acquires only in LINKED-p17_20-c9_100 | Exactly that context | matched |
| 6502 FULL acquires only in LINKED-p17_20-c9_100 | Exactly that context | matched |
| 6501 BLIND stays immediate throughout | All eight contexts immediate | matched |
| 6502 BLIND stays immediate throughout | All eight contexts immediate | matched |

Five of five components match; no causal explanation is scored as established.
Owner prediction: **not taken (unattended)**.

**Strongest support:** two prospectively selected independent datasets reproduce a useful
mean native consequence after the real purchase cost against both legal references. The
mean remains above the MEI with all outputs retained. The event → public purchase → paid
display → count-conditioned duration → actual reward → observed-action update path changes
a deployed action with positive native value, not merely a predictive statistic or proxy.
The existing verified DACOM/VIL2C retrieval already motivates this native endpoint; this
expected repetition adds empirical evidence and requires no new literature claim or search.

**Strongest contradiction and limit:** the second gain is smaller and its margin above MEI
is only 0.0005751139322916715; two-dataset variation is material. Both fits benefit in just
one of eight fixed contexts. Small headroom, fitted-max bias and finite training/evaluation
variation remain alternatives to a broad stable effect. B01's two native nulls and historical
false-probe losses of 0.028562899/full competence 3/6 per arm remain unchanged contrary evidence.
B02/B03 changed learner, exploration allocation and precision relative to B01, so these results
do not locate B01's cause or prove architecture/precision superiority.

**Claim ceiling:** a preliminary repeated useful-acquisition signal for this shared-data
return learner, budget, finite host and final endpoint. The host is systems/information flow;
it does not instantiate multi-agent partial observability or non-stationarity. There is no
generic MARL, transfer, exact-optimum, stable-superiority or C-BENCH conclusion. No tuned-generic
current-host headroom record is added, and the historical 0.00267963765625 reference is not an
exact ceiling on these sampled estimates. The retained-policy/root-residual numerical-locus
family remains stopped; no quarantine or family disposition is changed.

## 6. Decisions this intake produces

**Decision 1 — object-tier result intake.** Options: (a) accept both complete datasets and
apply joint RM-A; (b) limit a concretely damaged required primary; (c) retain only technical
facts if no complete comparison exists. Recommend/select **(a)** because both committed-source
summaries, actual counts, paired primary measurements, acquisition and receipts agree with
the frozen card. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
This records bounded science while Root's separate integration gap remains open.

**Decision 2 — object-tier next-question recommendation.** Options: (a) recommend preparing
a two-dataset B at half the training-data budget with the same comparison and final evaluation;
(b) recommend two more unchanged-budget datasets; (c) recommend no follow-up now.
Recommend/select **(a), as a returned preparation recommendation only**. The useful signal has
now appeared in the separate prior dataset and both prospective follow-ups. A lower-data B
would ask whether useful native acquisition survives reduced learning exposure, rather than
spending the next allocation only refining the same-budget seed average. A failure there
would bound budget dependence, not erase B03 or close paid-information research.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

For next-command planning only, the proposed shape is two fresh datasets, **512 batches ×
256 rows each**, unchanged FULL/BLIND/IMMEDIATE-4 and 4,096 final episodes/context/policy.
Python arithmetic gives 131,072 training + 98,304 evaluation = **229,376 episodes/dataset**,
**458,752 summed**, and 196,608 scalar updates/dataset, **393,216 summed**. The dominant work
would be two collections with two shared-label fits each and three fixed final evaluations;
the fixed evaluation cost does not halve with training. The cost law is
`T_init + 512*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish` per dataset.
The present 8.00/10.46-second complete runs are planning evidence; phase coefficients and the
future runtime are unmeasured. A candidate cap remains 600 seconds each/1,200 summed,
**not allocated here**. No calibration, policy search or diagnostic prerequisite is proposed.

This selects the recommendation only. New seed IDs, prospective card, prediction, source
binding and execution are not frozen or dispatched. In particular this is no third B03 seed.
Root returns the recommendation for next-command planning; it is not a Portfolio priority,
capacity or lifecycle action, a new object-family decision or a Pro Send. The current assignment
ends with this intake/brief delivery; no further work is launched.

## 7. Owner boundary and durable records

At the clean intake boundary, `item.py reviews --json` returned `[]` and no UCOPE ledger
owner override was present. The owner prediction is not taken; no absent reply is fabricated.
Existing card item `20260907-ucope-004` remains the asynchronous review surface. Under the
current P1/P2-only rule these ordinary result/recommendation decisions and the brief belong
in the intake/card/audit; no routine P3/P4 item is created or upgraded.

Owner flags: **none**. No critic dissent or close call is overridden, no recast or C consumption
occurs, and no family or Portfolio disposition follows. The Chinese [owner brief](../../portfolio/owner/briefs/ucope/2026-09-07_shared-data-return-b03.md)
accompanies the result. DIRECTION is updated only with accepted bounded science, support,
contradiction, the surviving uncertainty and the unlaunched next discriminator.

## 8. Evidence paths and return boundary

The [CM result record](UCOPE_SHARED_DATA_RETURN_MODEL_B03_RESULT_EVIDENCE_20260907.md) retains
both exact commands, prospective source, focused acceptance and every context/plan/result.
Original output roots are `/home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907/temp/directions/ucope/exp/shared-data-return-b03-seed<seed>/`.
Collected copies are under the same relative `temp/directions/ucope/exp/` roots in
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, for seeds 6501 and 6502;
each contains `summary.json`, `resource_admission.json`, `status.json`, `supervisor.log`
and `whole_time.txt`. Offline DM calculations are in `shared-data-return-b03-intake/`
(`analysis.json`, `scores.csv`, `run_summary.json`) beneath that experiment directory.

The returned scientific decision is joint RM-A at object tier with the limited claim above.
**Next scientific discriminator:** the same native comparison with prospectively reduced
training data and all outcomes retained, if a subsequent command selects it. **Next engineering
owner:** Root resolves main integration of the pushed card/source/result/intake commits.
Both accepted experiment handles are terminal, the CM has returned writer ownership, and
no additional invocation or external provider action was taken by this intake.
