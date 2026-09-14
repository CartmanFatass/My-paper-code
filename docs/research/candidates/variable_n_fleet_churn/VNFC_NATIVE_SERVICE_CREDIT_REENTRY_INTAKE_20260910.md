# VNFC native-service temporal-credit re-entry intake — 2026-09-10

## 1. Current assignment and accepted boundary

Root resumed this direction for independent rolling readiness and authorized continuation.
This is a direction-local question; no sibling result, cleanup, batch or Portfolio bundle is
a dependency. The current Portfolio row is `ACTIVE/HIGH`; the existing two recasts retain
their lowest contention sequencing. Neither fact selects an experiment.

The latest formed decision remains the [2026-09-06 post-deployment-mode Convergence
pause](pro_packets/20260906_post_depmode_convergence/archive/RESPONSE.md), applied in
[its intake](VNFC_POST_DEPMODE_CONVERGENCE_INTAKE_20260906.md). It pauses the unchanged B01
MAPR-versus-DIRECT N7 direct-return comparison and repetitions merely seeking to rescue
its small separation. The deployment-mode question is closed. No runnable successor,
existing-record analysis or third recast was selected. Re-entry may present one concrete
information, representation, credit or optimization change with a real-training comparator.

All E01 semantics and the completed technical cost stop remain unchanged. R03 census,
wider K, old exact-law/DEBUG obligations, historical quarantines, old cross-N comparisons
and their evidence are not reopened. No unused B01 or E01 balance transfers here. B01's
2,700 seconds was its cumulative formal total, with both recorded boundaries retained:
827.76 seconds runner-mixed accounting and 828.98 seconds consistent outer accounting.

The original direction checkout was absent. This author created the designated
`codex/vnfc` / `C:/Projects/HMASD-worktrees/codex-vnfc` from published main commit
`2482db44052705b130b3970456415d2309c99e2b`, initially clean. Main's unrelated work was
untouched. This checkout is retained for this author's request and scoped Pro delivery;
Root owns integration and later reclamation. Owner reviews returned `[]` on this boundary;
no owner prediction was taken. There is no new result to score or brief.

## 2. Evidence supporting and opposing re-entry

The two accepted B01 training draws support real same-distribution N7 recovery learning:
MAPR final-minus-initial `R_fail_60` was +0.204127604 / +0.199453125; DIRECT improved
+0.188658854 / +0.195520833. Both architectures actually moved. MAPR's final advantages
over DIRECT were only +0.015468750 / +0.003932292; the zone-1 contrast changed sign.
Both learners lost to fixed BCRH on all four native metrics in both zones. MAPR's observed
BCRH gaps were -0.041822917 / -0.060911458. These observations motivate improving shared
recovery learning without presuming a MAPR-specific advantage or BCRH optimality.

Deployment SAMPLE-minus-GREEDY recovery was -0.006536 / -0.003646 / -0.005599 /
+0.016901 across the four saved policies; all four overall `J_ext` differences were
negative. This closes that selected execution-mode observation, not every possible
execution explanation. No old policies, outcomes or training units are pooled into a new B.

**The new, concrete change in decision readiness** is a defined credit estimator on an
already exposed native path, resolving the prior response's unspecified credit alternative.
`learning.update` passes one terminal `J_ext` per episode to `gae_terminal`; the latter
uses six decisions, **gamma=1 and lambda=.95**, not a discounted per-tick objective.
`bpcr_general.hpp::ginteractive_snapshot` already returns cumulative delivered/demand
integers after each physical interval. `ginteractive_step` executes 20 post-loss native
ticks per command; reset's prehistory contributes no post-loss endpoint counters.
`gtick` stops accumulating failed-zone primary counters at 60 seconds, while total and
intact service continue to the complete 120-second endpoint. The Python interface exposes
these counters at reset and after each step. The proposal needs their six differences,
not counterfactual trajectories, a new controller, an extra rollout or a native ABI change.

The strongest alternative is to retain the pause. There are only six decisions, so the
original lambda weighting at the earliest decision is .95^5 = .7737809375, not a very
long delayed-reward chain. Both original learners already learned. Moving labels earlier
does not identify which earlier coordinated command caused subsequent service; travel,
acquisition, retained occupants, and partner effects persist across intervals. A learned
critic may already absorb much of this timing issue. New within-episode labels can help,
do little, or worsen the finite GAE/PPO update. No historical cause has been established.

## 3. One fully specified proposed B, unselected

Proposed object: `VNFC-N7-NATIVE-SERVICE-CREDIT-B02`, `B/EXPLORE`.
Claim: At fixed real-training exposure after one N7 membership loss, assigning native service
to its six collection intervals can change the learned MAPR policy's complete recovery
performance relative to placing the same objective at the terminal interval.
Binding MARL structure: (a) roster change; temporal team credit influences how surviving
entities reassign the failed role while retaining other occupants and service responsibilities.

This is a comparison of **two newly trained MAPR-4 instances**, `INTERVAL` and `TERMINAL`.
The comparator is the actual existing terminal-credit algorithm in the same architecture,
not an old checkpoint, an untrained null, or a restarted MAPR-versus-DIRECT comparison.
DIRECT's accepted positive learning and contrary comparison remain evidence, but are not a
third arm. BCRH-PERSIST is a fixed native reference, evaluated once on the shared panel;
its field-by-field information equivalence remains unestablished.

For each completed own-trajectory episode, let `F_j` and `T_j` be the existing cumulative
failed-zone delivered units and total delivered units after j post-loss intervals,
j=0,...,6. The native initial values are zero. Let `D_F` and `D_T` be the corresponding
positive **terminal** demand denominators. With j=0,...,5, define:

```text
J = 0.5 * F_6 / D_F + 0.5 * T_6 / D_T
r_TERMINAL[j] = J if j == 5 else 0
r_INTERVAL[j] = 0.5 * (F_(j+1) - F_j) / D_F
              + 0.5 * (T_(j+1) - T_j) / D_T
delta[j] = r[j] + V_old[j+1] - V_old[j], with V_old[6] = 0
A[j] = delta[j] + 0.95 * A[j+1], with A[6] = 0
lambda_return[j] = A[j] + V_old[j]
```

The six interval rewards sum to the same full-episode native `J`; failed-zone increments
after interval 3 are zero under the existing 60-second primary definition. Do not divide
by each interval's or current cumulative demand, omit later total service, add a bonus,
change metric weights, shorten termination, or equate these rewards with causal contributions.

Terminal denominators are used **retrospectively, after complete collection**, in both
arms' training target construction. They are exogenous demand accounting, never future
actor/critic inputs or action selection hints. Both arms retain the same counter snapshots
for matched collection work; TERMINAL uses only the final scalar in its update. The change
therefore supplies temporally resolved training labels, while actor observations and raw
available trajectory data stay matched. Equal total objective is not identical learning
information or identical finite gradients. No arbitrary potential shift is applied to the
critic to cancel the intended difference; both instances start with identical fresh tensors.
With an approximate observation critic, lambda<1, PPO clipping, normalization and shared
actor/value features, no unbiased-gradient, universal variance reduction, Markov reward or
finite-training equivalence claim follows from the telescoping identity.

Preserve the current canonical MAPR policy/action path, public observations, masks,
physical entity mapping, four-token grammar, fixed occupants, one loss, post-loss N7,
120-second terminal, AdamW settings, advantage normalization, PPO epochs/minibatches,
entropy/value coefficients, gradient clipping, CPU float64 and one compute thread.
No join/rejoin/replacement, recurrent-state intervention, controller features, imitation,
oracle action, search, checkpoint selection or deployment-mode exploration is added.

Use one fresh paired training draw, identical initial MAPR tensors and independent
optimizers; share exogenous training/evaluation worlds, use separate arm-specific action
and minibatch streams, and a separate evaluation master. Select exact new identities only
after a conforming decision. Each arm gets 64 rounds x 32 complete training episodes;
4 PPO epochs x 8 minibatches per round = 2,048 backward/AdamW updates per arm.
Evaluate fixed checkpoints 0, 32 and 64 on the same 64 fresh worlds, balanced 32 per zone.
Use the existing token-greedy evaluator in both arms. Final round 64 is the sole primary
checkpoint; the common initial checkpoint is an initial-state observation, not another
independent training draw. Preserve all outcomes, curves, failures and native components.

Primary: final `INTERVAL - TERMINAL` in `R_fail_60`, paired by evaluation world. Report
each arm's final-minus-initial and difference to BCRH, plus `J_ext`, `U_total`, `U_intact`,
both failed-zone strata and existing finite-episode violation/context facts. This is one
training pair; world-level paired SE is conditional on these two fitted policies and does
not estimate training-population uncertainty. No headroom claim: a tuned same-information
upper-reference pair is still absent, not zero. BCRH is not a proven upper bound.

Proposed MEI is .02 absolute recovery, a noticeable fraction of the existing .04-.06 MAPR
reference gap. It describes this new question; it does not change B01's .10 scale or make
positivity/significance an admission rule. An improvement beyond .02 with preserved complete
native objective would support recommending a separate independent pair; recovery gains
with `J_ext` or intact-service losses remain mixed. Inside .02, report the actual effect
and tradeoffs without an equivalence or automatic-stop claim. Opposite sign would argue
against this specific credit recipe at the observed budget, not against N7 learning.
No follow-up is automatically allocated by any branch. The next discriminator, if later
selected, would be an independent fresh pair with this same fixed comparison.

## 4. Scientific reading and concrete inferential limits

Read current evidence-spec section 11, FOUNDATIONS sections 1-4 and 6, and RL topic sections
on data/updates, baselines/critic and reward transformations. They distinguish unchanged
task return from changed finite training and distinguish 64 evaluation worlds from an
independent training population. This changed the proposal from a vague service-difference
reward to terminal-normalized increments with explicit gamma=1 and a complete 120-second
objective. It does not demonstrate that service timing is the source of the old shortfall.

Local retrieval on 2026-09-10 searched Inst-sci's 190-row formal `catalog.v2.jsonl` for
`reward redistribution`, `RUDDER`, `potential-based`, `return-decomposition`, `delayed reward`
and `generalized advantage`. Only MARL-0449 (ACAC) matched the broader GAE term; its
asynchronous method is not evidence for this synchronous credit recipe. My-lib's exposed
registry contains P-SYN-001/P-SYN-002 and the collection README identifies synthetic-core;
neither was used as science. No verified real-collection interface was located in that
inspection; this is a coverage limit, not a claim that no relevant papers exist there.

For this specific gap, the author read primary sources directly:

- Schulman et al., *High-Dimensional Continuous Control Using Generalized Advantage
  Estimation*, ICLR 2016, arXiv:1506.02438v6, sections 2-3, equation (16), pp. 2-5
  ([paper](https://arxiv.org/pdf/1506.02438v6)). GAE is a weighted sum of TD residuals;
  changing the reward timing at fixed gamma/lambda can change its finite estimates. The
  paper's value/bias/variance reasoning motivates a comparison, not a predicted improvement
  for this six-step partial-observation MARL host.
- Arjona-Medina et al., *RUDDER: Return Decomposition for Delayed Rewards*, NeurIPS 2019,
  section 2 definitions and Theorem 1, p. 3 ([paper](https://papers.nips.cc/paper/2019/file/16105fb9cc614fc29e1bda00dab60d41-Paper.pdf)).
  Return-preserving redistribution separates episode objective from reward timing and may
  produce rewards that are not Markov. This proposal uses measured native counter increments,
  not RUDDER's learned predictor/contribution analysis, and claims neither optimal
  redistribution nor removal of every delayed causal effect. The pathwise sum is supported
  directly by the native accounting definitions, not borrowed from a theorem's different
  assumptions.

These are methodological sources, not novelty evidence. The fixed intake carries the
specific source/version/access and author interpretation; Pro need not follow an unlisted
literature tree or invoke local tools. Explanatory source limitations create no extra B gate.

## 5. Work, complete cost and implementation boundary

[The machine-generated count and cost record](pro_packets/20260910_native_service_credit_reentry/EXPOSURE_AND_COST.json)
reads the two existing B01 summaries and computes only documentary arithmetic. Consultation
exposure is zero models, worlds, native steps, updates, evaluations, tests and profiling.
Proposed full work is two learners x 64 rounds x 32 episodes x 6 joint decisions, with
2,048 actual updates each, plus two learners x three checkpoints x 64 evaluation episodes
and 64 BCRH episodes. Total: 4,096 training + 448 evaluation/reference = 4,544 complete
episodes, 1,090,560 native ticks including prehistory, 4,096 backward/optimizer calls.
No outer action/trajectory/counterfactual search or new controller calls are added.
The existing 384 complete BCRH calls retain their intrinsic candidate/checker work.

From the largest observed B01 MAPR unit times, each same-size MAPR arm has a historical
planning component of 170.35347127632122 seconds. Replacing both old arms by MAPR gives
400.28840911334555 seconds including the recorded shared terms and reference. This is
an executable derivation, not a new measurement or a bound on a changed runner. Increment
collection/target/publication overhead and current-machine variability remain unknown;
per-arm formulae retain those unknown terms. The historical actual two-arm invocation
walls, 306.68 and 388.75 seconds, are another planning input, not guaranteed new costs.

Proposed allocation: **one new paired B invocation, 900 seconds cumulative complete
machine work**, partitioned as a 600-second complete native invocation (both arms plus
build/init, all evaluation/reference and runner publication) and at most 300 seconds of
required preparation, focused checks, source staging, Monitor observation commands,
collection/readback and closeout. These are components of one total, not replenished caps.
Agent deliberation and queue/network idle latency are administrative elapsed time, reported
separately when relevant; actual invoked support work is charged. If actual support timing
cannot be established, record complete-cost conformance as unestablished rather than zero.
No calibration experiment, second accepted invocation, retry, replacement seed, extra
checkpoint/panel or follow-up is selected by the proposal. A forecast exceeding its
allocated component returns the concrete cost fact without shortening the science.

The 300-second support allowance includes the affected focused test(s); it is not an
extra test budget. A non-environment unit check can falsify zero initial counters, terminal
normalization, telescoping, 60-second failed-zone freeze and the two different GAE targets;
the real accepted chain must expose nonzero learner movement and readable primary output.
No separate preliminary result-bearing run is proposed. Ordinary changed reward/learner
semantics get independent high-risk review under Engineering Scope section 7.3. Source
implementation, focused tests and exact launch bytes follow only after selection, with
the normal L0 task specification. Scope section 4 needs no new machinery; reuse existing
native execution, finite counters, outputs and the configured detached supervisor. No E01
parallel team/batch exception transfers. Ordinary proportionality limits remain applicable.

Launch, if selected, remains remote-first at `wsl_4070`, CPU float64/thread1, detached exact
committed/pushed source under `agent-task`; fresh admission on that node is adjacent to
the actual command. The DM retains technical acceptance, direct Monitor handover, terminal
collection, scientific intake and scoped preservation/closeout. Root integrates; Transport
only handles the Pro request. No remote invocation or scientific RNG root exists now.

## 6. Decisions this intake produces

| Option for direction Convergence | Consequence | DM recommendation |
| --- | --- | --- |
| (a) Open only the specified native-service temporal-credit B comparison | One new paired training comparison within N7 shared recovery, after exact card/implementation; old MAPR-DIRECT and deployment-mode pauses remain | Recommended: the previously vague credit alternative now has a target-preserving definition, real trained null and bounded reusable path |
| (b) Retain the current pause with no new numerical work | Preserve the evidence and revisit on a better supported learning question or concrete integrity fact | Strong alternative: six decisions, existing learning and non-Markov credit limits make benefit uncertain |

Reopening a paused comparison family is **direction tier**; the DM does not apply (a)
locally. This request asks `em:variable_n_fleet_churn:convergence` to decide these options
and the specified one-pair scope, not to decide Portfolio priority, lifecycle, capacity,
fusion, registration or a third recast. If a disposition would require changing those
boundaries, state the conflict instead of silently executing it. A/B has no consumption
state and Pro is not a general B launch gate; this consultation follows this family's
specific prior pause. No scientific option is `auto_applied` before the formed decision.

Object-tier procedural choice: submit this precise re-entry question instead of running
an undefined intervention or repeating the paused configuration. **Owner-delegated decision
(unattended, 2026-09-03 instruction): submit the direction question.** This zero-exposure
choice is recorded in the 2026-09-10 ledger; the associated P2 direction item states the
unexecuted recommendation and contrary evidence:
[`20260910-vnfc-001`](../../portfolio/owner/inbox/2026-09-10/20260910-vnfc-001.json).
Its `auto_applied` is null. Publishing it does not wait for an owner
reply. This intake and the packet are the existing recovery record, not a second approval
system. At the published handoff boundary the direction awaits its own Pro answer and
Root may advance independent work.

## 7. Published request and return boundary

Preparation/evidence commit: `b610a07986d839e4a44159d8c7c5a85ca300606c`.
The final [fixed TASK](https://github.com/CartmanFatass/My-paper-code/blob/b03b1471ff8808d5cf3c9256889b724d501ae92f/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260910_native_service_credit_reentry/delivery/TASK.md)
and REQUEST are published at `b03b1471ff8808d5cf3c9256889b724d501ae92f` on `codex/vnfc`.
All 19 effective path/SHA mappings existed at their Git objects, were reachable from the
observed published direction ref, and matched the embedded path/SHA/purpose/provenance
manifest. Issue 1 was OPEN with four previous comments at the saved observation. This
establishes local publication, not current provider access. No tests or native invocation
were needed for this documentary packet.

Request `2026-09-10-vnfc-native-service-credit-reentry-01` is READY_TO_DISPATCH in
`pro_packets/20260910_native_service_credit_reentry/delivery/HANDOFF.json` after binding
the exact committed TASK. Source is this native DM, parent is Root, operator is the
configured independent Transport. The current registry has the preceding request at
`DIRECTION_VERIFIED` on `em:variable_n_fleet_churn:convergence` /
`6a9c674e-6eb8-83e8-b19f-06cb6f3ebe08`; this preserves that post-cutover binding and does
not reuse retired `6a9aa8d1-3338-83e8-aeae-18863837a4ea`. Transport rechecks provider model
and Send state. The author has not dispatched Transport or sent a provider message.

One initial uncommitted, unpublished TASK/HANDOFF draft remains in
`temp/directions/variable_n_fleet_churn/pro_authoring/20260910_native_service_credit_draft01/`.
The renderer required a fresh output directory for wording revision, so the final generated
pair uses the `delivery/` directory above; the old draft retains TASK_NOT_PUBLISHED and
has no acceptance/Send. This is authoring provenance, not a second scientific request.
The DM retains its preservation/cleanup through the request's intake boundary; Root owns
eventual direction-checkout reclamation after integration. No live run or scientific
evidence depends on the draft.

Root's next action is to load this committed HANDOFF and dispatch it exactly once through
the existing Transport. On the immutable full response, resume this DM for conformance,
direction intake and any exact authorized continuation. Until then, the proposed scientific
option and its 900-second allocation remain unexecuted; all prior pauses and limits stand.

## 8. Transport blocker and same-request reconciliation wait

Root subsequently dispatched the bound request and forwarded a terminal Transport blocker.
The [exact forwarded receipt and selected registry corroboration](pro_packets/20260910_native_service_credit_reentry/TRANSPORT_BLOCKER_20260910.json)
record `SEND_UNCERTAIN`, `WAITING_UNKNOWN`, and **one Send click** on the bound conversation
`6a9c674e-6eb8-83e8-b19f-06cb6f3ebe08`. The forwarded observation is: "Exact bound URL
reloaded; no current-round user node or assistant response; acceptance unresolved". Its
blocker is: "Pro Send acceptance unresolved after one click; no retry permitted". There
is no current-round archive or formed scientific decision. The read-only registry check
at 2026-09-10T20:32:12Z corroborated this state; Transport's last provider observation was
2026-09-10T20:28:57Z. The registry's accepted delivery describes its blocker receipt to
Root, not acceptance of the Pro prompt. The DM did not inspect the browser or retry Send.

This supersedes section 7's ready-to-dispatch status, while its TASK, REQUEST, HANDOFF,
fixed SHA `b03b1471ff8808d5cf3c9256889b724d501ae92f`, prompt bytes and request identity remain
unchanged. Current authoring HEAD before this receipt update was
`607aa7ec6c5095fa2444eb28bd536e415cc56d47`; its checkout and upstream were clean and aligned.

**Rule applied verbatim — AGENTS section 3:** "**Direction and Portfolio tiers**: the
direction parks at a clean boundary (everything committed, runs detached, state recoverable
from the repository) and Root advances independent authorized work. Nothing is decided
provisionally at these tiers."

The direction therefore waits at a clean execution boundary for its own Transport
reconciliation. This is an operational wait, not a Portfolio `PARK` disposition or option
(b) selected in section 6. Neither section 6 scientific option is selected; the proposed
900-second B allocation is not granted or spent. New scientific invocations, learner
updates, native episodes and scientific exposure remain **zero**. There is no result,
scientific polarity, prediction score or valid-result brief to add. The prior accepted
pause, E01 limits, `ACTIVE/HIGH`, two recasts and lowest contention sequencing still apply.

**Decisions this receipt produces.** The procedural options are (a) preserve the receipt
and same request for Transport reconciliation, (b) blindly resend, or (c) substitute a
local direction disposition. Recommendation and executed choice: **(a)**.
**Owner-delegated decision (unattended, 2026-09-03 instruction): preserve the same-request
reconciliation wait.** This is a technical preservation decision under the blocker rule,
not `PRO_BLOCKED / LOCAL_PROVISIONAL` scientific selection. The audit records it separately
from the earlier zero-exposure question submission.

The outstanding queue entry is maintained here: request
`2026-09-10-vnfc-native-service-credit-reentry-01`, binding
`em:variable_n_fleet_churn:convergence`, existing conversation and exact fixed inputs above;
Root owns routing and the dedicated Transport owns acceptance reconciliation, any permitted
same-request recovery and observation. This return requests that Root retain that entry.
No resend is authorized while acceptance remains uncertain. An authoritative acceptance
fact returns to the existing Transport route; a complete response must be archived at its
immutable commit and forwarded to this DM for full conformance/intake before any affected
direction action. An authoritative failed-effect fact is handled by Transport under the
existing request and recovery rules, never by a new DM request or duplicate Send. Root
continues independent authorized directions meanwhile.

Owner reviews again returned `[]` at this boundary. The existing P2 item
`20260910-vnfc-001` receives a blocked-state trace through `item.py`, sourced to the explicit
AGENTS section 3 rule and this receipt record; its recommendation is preserved and
`auto_applied` remains null. This is no owner reply or formed Pro verdict. Only this intake,
the receipt, its technical audit row and that trace change. No scientific/source test is
needed for a documentary receipt update. The direction checkout remains retained for the
unresolved delivery and subsequent DM intake, with this DM owning draft preservation and
Root owning integration and eventual reclamation as recorded in section 7.

## 9. Reconciled full response and direction decision — 2026-09-11

Root returned the original request's reconciled delivery with `no_new_send=true`.
The DM directly read all 235 lines / 31,994 bytes from response commit
`10bb08476ff58afd25b90b21cd2d1a739b25ca4b`, SHA256
`11076fff024affb030dd692e1a8637fa2b36043274495b1419ad93a13bccd117`.
The [complete response](pro_packets/20260910_native_service_credit_reentry/archive/RESPONSE.md)
is the decision; the short chat receipt and section 8 blocker remain historical facts.
The response commit adds only that authorized file on the prior branch descendant.
This checkout fast-forwarded cleanly from `2e1ab2ffb4a3b1b55f1d355d278e03f6bee5d341`.

The current Issue 1 body and [delivery comment 5637667527](https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5637667527)
were read through `gh api` on 2026-09-11 (DM boundary began 18:04 UTC): the Issue is open,
has five comments, and the new comment points to that response and fixed TASK
`b03b1471ff8808d5cf3c9256889b724d501ae92f`. The old Issue body is historical, as Pro states.
Executable Git/regex checks found all 19 response source path/SHA pairs, exactly matching
REQUEST and fixed TASK; every Git object exists. Four historical versions and the other
15 sources at `b610a07986d839e4a44159d8c7c5a85ca300606c` are preserved. Pro reports its actual
source scope, including partial native-code reading, and does not claim new execution or
direct paper access. The requested sections, counts, comparison, costs, limitations and
both choices are answered. No missing source or out-of-scope delivery change was found.

**Rule applied verbatim — AGENTS section 2:** "A complete archived Pro response that
decides the posed question at its declared evidence class and within current owner
instructions and applicable specifications is final for its node."

**Scientific/specification acceptance:** conforming. Response opening and sections III–VI
select precisely one ordinary B pair, INTERVAL versus TERMINAL, with the unchanged full
native objective, retrospective labels, gamma=1/lambda=.95 PPO, 64x32 training per arm,
0/32/64 fixed evaluations and the one BCRH panel. It accepts native<=600 s,
support<=300 s, total<=900 s without transfers, pilots, retries or successors. It imposes
no exact-headroom, causal-diagnosis, positive-result or stronger-class prerequisite.
The current evidence-spec sections 4, 5.2, 11.4 and 11.7–11.10, Engineering Scope sections
4–5 and 7, rolling execution and current Transport ownership are consistent with the
selected requirements. No correction round is needed. Technical source acceptance and
actual execution have not yet occurred at this decision boundary.

Scientific-reading application: FOUNDATIONS sections 1–4 and 6 and the RL topic's
data/critic/reward passages support the distinction between a preserved full trajectory
return and changed finite GAE/PPO targets. Complete labels may use terminal demand after
collection; behavior and observation-only critic inputs may not. A bootstrapping critic
does not establish Markov closure, variance reduction or identical finite gradients.
Reuse the specific literature retrieval in section 4; no new literature search changes
the question. One paired training draw is the independent unit; 64 shared evaluation
worlds only supply conditional evaluation uncertainty.

**Decisions this intake produces.** Direction options remain section 6 (a) the exact
credit comparison and (b) retain the narrow pause. Pro selects **(a)**; DM recommends
and applies that conforming selection as **PRO_FINAL / OWNER_DELEGATED**. Only the named
credit comparison reopens. Old B01/deployment/E01/R03 stops, every prior result and
quarantine, ACTIVE/HIGH, recasts=2 and lowest contention sequencing remain unchanged.
No Portfolio decision or third recast follows. Object choice: bind this accepted scope
to the [B02 science card](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_SCIENCE_CARD_20260911.md),
fresh seed 2026091101, evaluation seed 2026091102 and namespace
`VNFC-N7-NATIVE-SERVICE-CREDIT-B02-20260911`.
**Owner-delegated decision (unattended, 2026-09-03 instruction): bind this one fresh B02
pair and implement its selected comparison.** No historical seed or checkpoint is reused.

Strongest support remains the now-defined native-label intervention and already
observed learning; strongest contradiction remains the six-decision horizon, common
old gains, native BCRH losses and absence of a diagnosed credit bottleneck. There is
still no new effect measurement. Claim ceiling: one local B signal or counterexample,
not stable superiority, equivalence, pure causal attribution, tuned headroom or transfer.
Next discriminator is the card's final INTERVAL-minus-TERMINAL native recovery, with
full J and intact/zone costs retained. No automatic next invocation follows its intake.

The existing P2 decision item receives an applied Pro trace with option (a), preserving
its earlier blocked trace. A new-card item links the same selected scope. Owner reviews
returned `[]`; prediction not taken (unattended). The [Chinese decision brief](../../portfolio/owner/briefs/variable_n_fleet_churn/2026-09-11_B02_CONVERGENCE.md)
explicitly says no new run has occurred. Root integration support is included in the
card's cost record: 5.3663749 s internally timed plus approximately 1.0, 2.6 and 0.1 s
displayed tool walls; approximation is retained. Support work without a reliable timer
will not be replaced with zero.

DM application summary used in the new-card packet (a summary, not a verbatim Pro quote):
选择（a）：仅开放 VNFC-N7-NATIVE-SERVICE-CREDIT-B02 的一次新训练对，比较 INTERVAL 与 TERMINAL；完整机器工作最多900秒。
