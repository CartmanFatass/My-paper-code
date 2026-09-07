Claim under test: On the finite renewal host, a fresh policy trained on sampled net return can learn when to buy information and earn more than the strongest immediate-commitment reference.
Binding MARL structure: **systems / information flow**. This host abstracts a coordinator buying otherwise unavailable information before a duration commitment; it does not instantiate multi-agent partial observability or non-stationarity, so no MARL population claim follows.

# UCOPE native-return acquisition B01 — science card

- Status: **FROZEN, B/EXPLORE**, 2026-09-07, before any new learner output.
- Object: `UCOPE-NATIVE-RETURN-ACQUISITION-B01`; no C-class consumption state.
- Selection: [object-tier selection intake](UCOPE_NATIVE_RETURN_ACQUISITION_B01_SELECTION_INTAKE_20260907.md), option (a), `OWNER_DELEGATED` under the 2026-09-03 standing instruction.
- Prepared question: [September 6 draft](UCOPE_NATIVE_RETURN_ACQUISITION_B01_QUESTION_PREP_20260906.md), integrated `79a80f630`.
- Source-binding base: `f095d53732705b4db00156f57d61976c979fd61a`. The new learner's actual launch SHA is recorded when launched; no run is represented by this card.

## 1. Question, population and native information path

Does direct learning from realized cost-inclusive return make useful paid acquisition learnable
on this finite host without oracle action labels, signed hinges or a fitted-root Bellman target?
This is outcome-informed exploration motivated by PA-B and TW-B, prospectively fixed for these
new runs. It cannot diagnose TW-B's retained root residual or establish a COUNT/RAW advantage,
complete competence, odd-to-even period transfer, stable superiority or deployment benefit.

Reuse these source entry points **unchanged**, at the source-binding base:

| Path under `experiments/candidates/ucope/conditioning_discriminator_r01/` | Bound use |
| --- | --- |
| `contract.py`: `CONTEXTS`, `context_id`, `K_EVAL`, `MARKS` | Eight contexts, their public order/identity, periods `{2,4,6,8}`, six marks |
| `host.py`: `execute_episode` | Real episode execution and count-only tail callback |
| `rng.py`: `bernoulli`, `uniform`, `_payload` | Existing counter-addressed environment RNG, with new ancestry below |
| `oracle.py`: `tail_q` | Environment's Bernoulli service probability, used internally by `execute_episode`; no oracle policy or posterior enters the learner |

The eight public contexts are the Cartesian product of `LINKED/SEVERED`, reliability
`13/20` or `17/20`, and total cost `9/100` or `7/50`, in the source `CONTEXTS` order.
At the root, the actor sees only this public context and chooses `IMMEDIATE(k=4)` or `PROBE`.
An actual regime is drawn with SHORT/LONG probability 1/2. Six actual marks are generated with
SHORT probability `p` in SHORT and `1-p` in LONG. A LINKED display uses those marks; a SEVERED
display has its own independent regime and marks. Only after selecting PROBE may the tail receive
the **displayed** SHORT count `n in {0,...,6}` and choose a period in `K_EVAL`.

The real episode return is the source `Execution.external_return`:
`Bernoulli(0.95-(k-center)^2/100) - k/100 - k^2/1000`, plus
`0.08*N_actual/6 - total_cost` only when probing; `center` is 2 or 8 for the actual regime.
The probe term retains its native service, time and energy contribution. In particular,
`N_actual` and this probe-service reward must **not** reach the tail before it chooses `k`:
otherwise SEVERED could leak information that the displayed count does not contain. The existing
callback executes before `execute_episode` returns these reward components. Hidden regimes,
actual marks, posterior probabilities, unchosen returns and oracle action labels remain outside
the actor inputs and optimizer targets. Return reaches the learner only after the complete episode.

This is a finite undiscounted episode (`gamma=1`); duration already incurs the native time/energy
terms. Count host-event transitions as the source does: `2 + 6*I(PROBE)`. This count is neither
primitive duration nor optimizer exposure. Also record committed period units and the two probe
time units when paid; no extra duration discount or reward rescaling is introduced.

## 2. Learner, comparator and objective

**RETURN-ACTOR** has 468 trainable FP32 parameters: an `8 x 2` root-logit table and a tail network
`9 -> 32 (tanh) -> 4`. Tail input is an eight-coordinate context one-hot followed by `n/6`;
output period order is `(2,4,6,8)`. Root order is `(IMMEDIATE,PROBE)`. Root logits start at zero.
Tail weights use Xavier-uniform initialization with gain 1, first input then output layer, with zero biases
and a dedicated CPU `torch.Generator` seeded by the training seed. No pretrained state is loaded.

One Adam optimizer jointly owns root and tail parameters: `lr=0.003`, `betas=(0.9,0.999)`,
`eps=1e-8`, `weight_decay=0`, `amsgrad=False`, `foreach=False`, no clipping or entropy bonus.
Run 1,024 updates, each on 256 newly sampled on-policy episodes: 32 per context in source context
order, then increasing within-context episode index. Cast realized returns to FP32 for learning.
For row `i` in a 32-row context group, use detached advantage
`A_i = R_i - (sum_{j in same context, j != i} R_j)/31`.
The batch loss is
`-mean_i A_i * [log pi_root(a_i|c_i) + I(a_i=PROBE)*log pi_tail(k_i|c_i,n_i)]`.
The denominator is all 256 episodes, including immediate episodes. There is one joint optimizer
step per batch, not a separate root and tail step. Only visited action terms supply gradients;
no regression, critic, oracle-signed target, forced-probe training arm or counterfactual return
is added. Ordinary in-process batching of policy calculations is allowed.

Training samples categorical actions from FP32 softmax probabilities with separate CPU Torch
uniform streams: root seed `seed+1,000,000`, tail seed `seed+2,000,000`. Draw one root and one
tail uniform per batch row in the declared order, including an unused tail uniform on immediate
rows. Select the first cumulative-probability bin strictly above the uniform, assigning any
floating-point terminal-bin remainder to the last action. These action streams never sample
environment events. Initialization has its own generator as specified above.

**IMMEDIATE-4** always commits to period 4, with no probe, count, optimizer or training data.
It is the strongest immediate-commitment action on this action set: the native expected values
at prior 1/2 are `{2:0.746, 4:0.794, 6:0.754, 8:0.626}` in every public context. The treatment
shares this immediate option. This comparison asks the incremental value of learning acquisition
and informed duration; it does not support representation superiority over a learned equal-information
baseline. Training and evaluation both use the even period set, explicitly narrowing the old
transfer question rather than rewriting it.

## 3. Fresh data, seeds, evaluation and primary estimand

Run exactly the two independent training seeds **6301 and 6302**, each from scratch. Environment
ancestry for the unchanged `execute_episode` is
`("UCOPE-NATIVE-RETURN-ACQUISITION-B01", "seed-<seed>", context_id(context))`.
For training update `u=0..1023`, local row `j=0..31`, use `episode_index=32*u+j`,
`support=K_EVAL`, `evaluation=False`. Evaluation uses indices `0..4095` per context with
`evaluation=True`; the existing `eval-` namespaces keep it disjoint from training. New ancestry
separates this object from all historical draws, including offset 2,000,000. Context ancestry
also separates exogenous draws between the eight contexts. No fold or retained-policy dataset is used.

Only the **final checkpoint**, after update 1,024, is evaluated. Deploy modal root and tail actions;
ties choose immediate at the root and the first (lowest) period at the tail. Use 4,096 sampled
episodes in each context. For each episode, evaluate RETURN-ACTOR and IMMEDIATE-4 on the same
environment ancestry/index with `evaluation=True`; the existing counter RNG gives common exogenous
randomness without using either policy's unchosen return in training. Evaluation has no gradients
or model selection, and no alternative stochastic endpoint is selected after seeing its outcome.

Primary per-seed measurement:
`Delta_s = (1/8) sum_c mean_e [R_RETURN-ACTOR(s,c,e)-R_IMMEDIATE-4(s,c,e)]`.
The batch primary is `Delta_bar=(Delta_6301+Delta_6302)/2`. Publish both seed values and every
context difference, both return means, probe frequencies and mean paid component. Accumulate
evaluation moments in float64 from the host's Python-float returns; learner tensors stay FP32.
Within each seed, report the conditional Monte Carlo standard error
`sqrt(sum_c sample_variance(paired_episode_differences_c)/4096)/8`.
It describes evaluation noise conditional on that trained policy, not training-population uncertainty.
Two independently trained policies remain two learning units; contexts and episodes do not add seeds.

Also retain each training batch's mean native return and probe count, actual cumulative episode/
transition counts, joint optimizer steps and tail-active batches. Save one final parameter state
per seed. The machine-generated exposure line reports initial L2, final displacement L2 and maximum
absolute parameter movement for root and tail, plus joint update count. Root initialization is zero,
so report its absolute displacement instead of an undefined ratio; tail displacement/initial L2
is defined. There is no positive-movement threshold or retrospective competence gate.

## 4. Effect size, reading rule and prediction

**MEI is 0.001 absolute uniform-context mean native return.** Existing PA-B01 arithmetic gives
oracle target gain `17149681/800000000`, hence at most **0.00267963765625** averaged over eight
contexts above IMMEDIATE-4. The MEI asks for about 37% of that small available reference gain,
with losses elsewhere fully charged. This is arithmetic over prior evidence, not a new exact
evaluation. There is no tuned generic current-host headroom record; this oracle/reference
diagnostic is not a substitute for one. The comparison reuses the host's known immediate null;
the old fitted learners do not match this training objective/data or its claim.

For a complete two-seed result, apply the first matching branch:

| Branch | Reading rule | Bounded interpretation |
| --- | --- | --- |
| `NR-A` | `Delta_bar > 0.001` | Mean improvement above the MEI; retain adverse seeds/contexts and recommend a separately bounded independent-seed follow-up of this comparison |
| `NR-B` | `-0.001 <= Delta_bar <= 0.001` | No material mean signal at this budget; any seed-specific gain remains local and selects no automatic extra invocation |
| `NR-C` | `Delta_bar < -0.001` | Native mean loss; recommend no unchanged extension of this learner |

If a primary dependency is incomplete, publish `INCOMPLETE` with actual counts and any trustworthy
completed-seed facts; no two-seed branch is assigned. Missing optional resource telemetry alone
means `resources_unmeasured`. Engineering failures have no scientific sign and select no retry.
All outcomes remain; a negative bounds this learner/budget, not paid information or the direction.

How the result will be interpreted: NR-A would support another small learning measurement,
not stable superiority or a causal account. NR-B would leave direct-return learning unpersuasive
at this budget even if one seed pays usefully. NR-C would prioritize a specifically justified
different learner question over repeating these settings. Local acquisition successes never erase
native losses. One trustworthy completed seed may support its own narrow B statement if the
other is incomplete; it cannot be called the complete two-seed comparison.

**DM prediction, before any new learner output: NR-B**, with at least one final policy choosing
immediate in all eight contexts. The available gain is small and initially costly probing may
stop before the tail learns to exploit it. A competent return learner is the surviving positive
alternative. Owner prediction: **not taken (unattended)**; the prediction item remains asynchronous.

## 5. Selected exposure, cost, topology and stop

The two invocations are selected as a bounded B batch. No outcome-dependent additional seed,
checkpoint, tuning arm, exact census, diagnostic run or search is included.

| Quantity | Per seed | Complete batch |
| --- | ---: | ---: |
| Training episodes | 1,024 x 256 = 262,144 | 524,288 |
| Joint optimizer steps | 1,024 | 2,048 |
| Evaluation episodes, learner plus reference | 2 x 8 x 4,096 = 65,536 | 131,072 |
| All sampled episodes | 327,680 | 655,360 |
| Native host-event transitions | actual `2*episodes+6*probe_episodes` | between 1,310,720 and 4,849,664, actual required |
| Complete invocation wall cap | **600 s** | **1,200 s summed maximum** |

Python computed these expressions and the 468-parameter count without creating a learner.
New scientific exposure at freeze is **0 episodes / 0 optimizer steps / 0 evaluations**.
The prospective nonzero exposure is the table; the actual movement line is produced by each run.

Each 600 s cap includes imports/initialization, all learning, both final evaluations and publication
of that seed's result. Do not move required work into another invocation to escape the cap. Retain
partial outputs on a failure or cap stop; no automatic restart/resume or extra allowance follows.
Dominant cost law is `T_init + 1024*T_batch256 + 32768*(T_eval_actor+T_eval_reference) + T_publish`.
The unit coefficients are not measured for this new actor. Historical TW-B 62.506/62.641 s charged
arm times are context only, not this runner's projection. CM may report timing from its already
required focused check; no separate cost experiment is required. A concrete known cap conflict
returns here for a scoped decision; unknown time is not another A prerequisite.

Execution is prospectively host portable: CPU FP32, one scientific process and one Torch intra-op/
inter-op compute thread, no GPU or native team. Use the configured `remote_first` node and existing
detached `agent-task` route at committed source. Preserve the same sampler, dtype, RNG and comparison
on any permitted local fallback; the AGENTS conditions for that fallback still apply. Wall time is
a budget constraint, not the estimand; exact cross-platform output identity is not claimed.

**ENGINEERING_SCOPE_SPEC §4: needs none.** Reuse existing resource admission and detached execution;
add no guard, registry, retry, supervisor, compatibility layer or new telemetry system. Wall time
and peak RSS are sufficient resource fields. Normal final parameter serialization is a learner
artifact, not resume orchestration. There is no new scope allowance or historical exception.

## 6. Engineering deliverable and focused acceptance

1. **Deliverable:** implement this card's fresh learner, real-host collector, evaluator and one
   `summary.json` per seed; complete focused checks and independent affected-path review. The initial
   CM handoff is implementation/checks only; formal seeds are not run in that handoff.
2. **Owned paths:** new `experiments/candidates/ucope/native_return_acquisition_b01/`,
   `tests/experiments/candidates/ucope/native_return_acquisition_b01/`, and
   `scripts/run_ucope_native_return_acquisition_b01.py`; one technical acceptance note under this
   direction. Reuse §1's four historical modules without editing them. No core, old-card or
   retained-policy source changes are authorized.
3. **Preserve:** §§1–3 bind the public information, reward/time law, fresh environment/action RNG,
   actual policy-gradient exposure, reference pairing and final modal endpoint. Retain every
   outcome; publication must not depend on competence or a solver diagnostic.
4. **Acceptance:** inspect information flow through the count-only callback (including SEVERED),
   paid versus immediate reward/counters, selected-action gradient terms and the 256-row loss
   denominator, fresh train/eval addresses and matched evaluation, primary means/SE/branch mapping,
   exposure and complete/partial summary publication. Use one focused real end-to-end check at a
   distinct technical seed `9006301`, at most 2 updates plus 16 evaluation episodes per context per
   policy; rule and information/reward unit cases may be included in the same focused suite.
   This technical profile is not a B seed or tuning opportunity; record its exposure separately.
   Independent review is required for this new information, RNG and gradient path. Relevant evidence
   spec sections are §4, §5.2, §11.4 and §11.8.5–7; no historical all-array replay is inherited.
5. **Budget/stop:** ordinary research limits of 2,000 new non-test source lines, 600 runner lines,
   one focused smoke below 60 s and the 5-minute directory-test budget excluding that smoke;
   orchestration share is a review signal. Commit and push explicit paths in CM's own worktree.
   Return accepted source, actual checks/review, counts and any concrete unresolved fact. No formal
   invocation or extra diagnostic is included in this initial engineering assignment.

Only the evidence-spec §11.4 integrity, real-learner/nonzero counts, destination resource admission
and machine-generated exposure requirements may hold a later B launch. This card introduces no
owner vote, Pro round, headroom, competence, cost pilot or numerical-locus prerequisite.

## 7. Retained evidence and risks

[PA-B01 card §§3–4](UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md) supplies the immediate reference
and historical gain. [TW-B result §§1, 6, 11](UCOPE_THREE_WITNESS_HINGE_R01_RESULT_EVIDENCE_20260904.md)
retains 6/6 versus 4/6 tail agreement, unchanged 3/6 full competence, and two false probes costing
0.028562899 each. Those facts motivate the full-return endpoint; this study neither repairs nor
reinterprets the retained-policy root-residual/numerical-locus family, which remains parked.

Question-driven local retrieval is reused from the [draft §5](UCOPE_NATIVE_RETURN_ACQUISITION_B01_QUESTION_PREP_20260906.md#5-evidence-check-risks-and-next-action):
verified DACOM (AAAI 2023, DOI 10.1609/aaai.v37i10.26389), source
`C:/Projects/Inst-sci/papers/MyLib/json/MARL-0006.json`, pp. 3–5, elements 123–124, 186, 188,
190–192, 213–215. It supports treating acquisition delay and the downstream action jointly in
native value. It does not establish this Monte Carlo objective's novelty or effectiveness.
The source binding above adds the decisive implementation fact: count-only selection precedes
return of the actual-mark service component.

Remaining scientific risks are small headroom, noisy score credit, premature loss of probe exposure,
and stochastic-training/modal-evaluation mismatch. Runtime within 600 s is unmeasured. No risk
is predeclared as the cause of an eventual result, and none changes the historical PA/TW ceiling.
