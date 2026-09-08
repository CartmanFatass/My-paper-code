Claim under assessment: an ordinary motion proposal can use its own already-observed applied acceleration without reading a native legality certificate; whether this improves native service remains untested.
Binding MARL structure: systems / information flow. The proposed local actuator-memory path operates alongside partial observations, moving partners and role-owned recurrent state; it is a control parameterization hypothesis, not a specifically multi-agent advantage claim.

# DISH P53 source intake — 2026-09-08

One candidate survives the source assessment: a fixed previous-command input to the
motion mean, compared with the existing direct mean. Recommend posing that single
B/EXPLORE comparison to the existing Convergence node. **No successor, implementation,
model construction or scientific invocation is selected by this intake.** The completed
post-B06 narrow stop and the open ordinary-source-application agenda remain intact.

## 1. Assignment, class and checks

Authority is the published P53 handoff
`docs/research/portfolio/handoffs/2026-09-08-p53-dish-native-proposal-question.md`
at main `7e16fcc34c7b33c13f51b6968249340c731c27a0`, and Root's matching bounded
assignment. Its source assessment is **A/RECON**: implementation/information facts and
a question recommendation, with no observed algorithm effect. Its reading rule is:

> Identify at most one fair native-return B comparison, or a precise source-based yield.

I read the current Portfolio P53 command, DIRECTION's final accepted post-B06 section,
post-B06 intake §§4,7, B06 card §2, and only the connected actor/learner/native consumers
needed below. The older prepared-only statements and lagging Portfolio table row are
historical; the final accepted decision is the complete response at immutable
`f7b58f1b88d7282f98ca6be531e9b4c27f85b690`, already intaken by
`DISH_POST_B06_CONVERGENCE_INTAKE_20260907.md`. I reuse that accepted intake rather
than redoing its empirical reduction or provider archival.

Checkout: `C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907`, branch
`codex/pro-dish-post-b06-20260907`. It started clean at
`57f7a97df67a418a5edb9c9312fab619ac70307a`. Committed current instructions/handoff were
imported from main at `bd740558676929a4aba20027b573e63d5fbe27c8` by `894d26d69`, then
the accepted authoring/Transport inputs and dated audit base from
`de23d1774277294f29e4495582d862f686f02a7c` by `77c4e471f`. Those are input syncs,
not new governance. Native and learner source is unchanged from the starting checkout;
the inspected B02/B03/B04/B06, first-trigger and r06 source trees also match accepted B06
launch `373d187200a91942385e9380770dcf9f8098aada` in the Git surface comparison.
Completed delivery packets, response and unique archive contents are preserved.

Applicable evidence rules checked: §§3–5.2, 11.4, 11.7, 11.8.1–3, 11.8.6–7 and 11.9.
No model/simulator import, native call, training, evaluation, replay, profiling or test
was performed. The only computed quantities are integer configuration arithmetic and
read-only metadata/source checks. This source result has no independent training unit;
the proposed later independent unit is one matched pair of newly trained controllers.

## 2. What the accepted source actually supplies

Paths beginning `r06/` below abbreviate
`experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`.
Line numbers refer to the source at the intake's committed inputs.

| Boundary | Direct source observation | Implication for this question |
| --- | --- | --- |
| Host/learner | `sampled_execution_b06/study.py:179–212` uses B04's LOW_LR learner and B02 evaluator; `control_low_lr_b04/study.py:16–22,74–89` supplies the corrected B03 recurrent path; `first_trigger_source_scout_b01/native_a03.py:13–21` selects the A03 endpoint variant. | Reuse the corrected A03 host and existing learner. No old source fork or label-clone controller is the ordinary evaluator. |
| Own causal inputs | Native `actor_row`, `r06/native/rbhr_r06_production_backend.cpp:304–317`, includes physical vehicle position, velocity, **current applied acceleration at indices 8:10**, battery, masked local camera values, own filter, local radio values, own source presence/age and the existing role/renewal fields. | Each motion controller already has the proposed acceleration input. It needs no future label, partner hidden state, native certificate query or new sensor. |
| Received information and limitations | Partner fields 29:38 are exposed under `partner_present`; source presence/age is local. Snapshot delivery updates only the standby shadow recurrent state (`production_training_engine.py:92–108`; trainer `prepare_recurrent:272–285`). However native actor fields 45:54 mostly repeat `prepare_latched`, warmup and handover state; they are **not** readiness/version/origin-certificate bits. Field 44 is computed using current owner degradation, and partner fields read current native partner values under a retained presence flag. | Preserve the accepted interface literally. Do not claim that every supplied feature is a freshly received decentralized measurement or infer a receipt/certificate from its feature name. The new skip path uses only the unambiguous own acceleration fields, not these native summaries. Auditing or repairing the wider historical observation interface is not this assignment. |
| Entity/role ownership | `_role_policy_heads`, `production_training_engine.py:345–383`, selects vehicle 0/1 motion from that vehicle's incumbent or shadow copy according to current owner. **Prepare comes from the incumbent; commit comes from the standby shadow**, then trainer `step_rows:330–335` serializes both in the owner slot. | A field serialized for the owner is not proof that its neural decision used the owner's information. Motion's prior input must follow each physical vehicle's selected role; never swap physical identities with role slots. |
| Current proposals | Trainer `step_rows:287–335` advances recurrent state every primitive tick; on ordinary renewal, motion mean is `3*tanh(motion)` with learned diagonal Gaussian training noise and two existing Bernoulli intents. Between renewals it holds physical commands and emits zero intents. | The direct mean has no explicit own-command skip. A mean parameterization can change ordinary action proposals while leaving support, intent law and renewal opportunity intact. |
| Native actuation and application | C++ `project:261–264` clips raw acceleration to norm 3 and change to norm 1.5. `complete_prepared_tick:433–456,469–481` handles pending application, filter/prepare, projection, packet reservation, snapshots/readiness and new intent in the existing order. | Keep projection and application untouched. At origin, the certificate is called **after projection has updated `s.a`**; it checks clipped raw action against that state. A smooth-looking proposal does not guarantee origin or later application legality. |
| Native/global certification | `native_origin_certificate:356–358` combines warmup, both source identities, two predicted means/covariances, standby service-Q, separation, raw/applied slew and terminal facts. `version_ready:480–481` and application checks `438–449` additionally use readiness/snapshot ticks, epochs, packet sequence, both batteries and geometry. | These predicates are not available to one actor merely because they appear in StepOutput or `_State`. No `first_application_valid`, native/global legality mask, privileged rejection/resampling or certificate-as-actor-input is proposed. Causal learned predictions are distinct from the joint native predicate that consumes them. |
| Learning and private futures | `passive_labels_one:731–746` advances a private future and an eligible forced-promotion label clone. Collection computes these labels separately before ordinary stepping (`production_recurrent_trainer.py:428–445`); fragments retain `actor_raw` separately from target/link/missing/Q labels (`482–523`). | Private future labels remain existing auxiliary supervision only. They do not enter the proposed mean; private promotion is not an observed ordinary transfer. No label collection is executed here. |
| Reward and source application | Native service at C++ `488` requires delivered data age/error/link conditions; `491–496` updates energy, motion, separation, time and terminal. Fragments use ordinary `service` as reward (`trainer:515–516`). Native `cas_applied` alone triggers recurrent promotion (`trainer:377–384`). | Motion can affect service and later information without any source transfer. Source-application value still requires its own ordinary origin and matched source comparison. |

The proposed path is therefore: ordinary renewal under existing partial observations →
each physical vehicle's current incumbent/shadow copy → its own observed applied
acceleration plus its causal recurrent motion output → an ordinary raw motion proposal →
unchanged native projection, packet service and any legal application → real PPO exposure
and full native service/events/energy. Roster schedules, membership, survivor state,
role promotion, primitive-time discounting, partner co-adaptation and censoring semantics
are inherited, not intervened upon.

## 3. The single surviving intervention and fair comparator

**Proposed candidate: OWN_COMMAND_MEAN.** For the two components of each vehicle's
selected motion role, let `m` be its existing motion head and `a_prev` the same physical
vehicle's pre-decision `actor_raw[...,8:10]`. At ordinary renewal use:

```text
candidate mean  = 3 * tanh(m + a_prev / 3)
comparator mean = 3 * tanh(m)
```

The coefficient is fixed at one, and divisor 3 is the existing acceleration scale;
neither is a sweep. This is a soft previous-command input **inside the mean's tanh**,
not a legality mask, hard delta bound, forced hold or an additional native projection.
At `m=0` it retains a damped prior command, not exactly `a_prev`. It does not guarantee
smaller action changes at every state. Both means use the same componentwise range;
both raw Gaussian training distributions retain full support. Native radial clipping
and slew projection still act on both in exactly the existing way.

Both arms use the same graph, parameter count, observation/action opportunity,
causal histories, private supervision, raw service-Q, PPO/AdamW **3e-5**, normalization,
gradient clipping, 32-lane training distribution and ordinary Bernoulli intent law.
There is no change to learned noise, exploration temperature, prepare/commit support,
credit assignment, reward, ABI, certificates, event law or timing. Learning and future
trajectories may diverge as the consequence of the mean change. The generic comparator
is the accepted LOW_LR direct-mean learner trained alongside it, not a reused seed113
checkpoint, an untrained controller, a new weakened comparator or a privileged oracle.

The existing `actor_raw` fragment supplies the exact own input for both online behavior
likelihood and recurrent PPO likelihood. Source consumers requiring a later coherent
change are `step_rows:308–325,370–374`, `_policy_log_prob:428–458` and training's duplicated
mean calculation `579–580`; all must use their arm's same formula and physical ordering.
The tanh transforms the **Gaussian mean**, not a sampled latent, so this proposal does
not introduce a tanh-squashed action density. A mismatched live/replay mean would damage
the learning comparison and must be checked if engineering is later commissioned.
No such implementation or check is authorized or executed in P53.

## 4. Decision value, contrary evidence and honest ceiling

Expected useful consequence (inference): a cheap direct own-command input may make it
easier for a recurrent learner to maintain useful actuation under intermittent local
observations and changing partner trajectories, improving complete native service at
fixed learning exposure. A lower raw/applied command gap could also avoid some rejected
origin requests. The latter is a possibility, not a diagnosis of B06 or the primary
success criterion. Invalid-commit reduction or a legal transfer alone cannot rescue a
negative service contrast.

**Strongest contrary case:** the existing network already sees this input and native
projection already enforces applied slew; the skip may be redundant or persist a bad
acceleration during a turn or loss of partner coverage. Certification may remain blocked
by prediction, source, version or geometry conditions that it does not change. Thus the
candidate may yield fewer invalid commits yet lose service, or improve ordinary service
while leaving all source quantities unestimated. These are separate reportable outcomes.

The completed B06 fact remains sampled-minus-modal **-77.5** native service ticks, with
four adverse condition means, modal/sample invalid-commit means **3.5/31.875**, sampled
energy **+4642.6427**, and zero legal transfers in every reference/final row. Training's
1030 invalid commits, 3 separation breaches and 35 terminal events are retained separately.
Two sampled episodes win (+14/+3), final modal improves 292.5 over initialization, and
final sampled improves 215 overall while retaining TERRAIN/K8 -57. B04/B05's useful LR
means and adverse conditions remain intact. None of these observations identifies a
command-discontinuity cause or predicts the sign of this new parameterization reliably.

If selected by Convergence, the minimal useful observation is **one fresh matched
training-seed pair**, proposed seed127, selecting only update16, with the same four
exogenous evaluation conditions and complete native service. Each arm gets its own four
raw initial modal rows and four final modal rows; the primary is the mean of the four
final candidate-minus-comparator service contrasts. No best-seed/checkpoint/condition
selection and no sampled-versus-modal arm are added. The initial rows describe each arm's
own learning change, not an upper or a qualification threshold. Shared initial weights
and master-addressed exogenous streams are pairing, not a promise of shared trajectories.

Proposed MEI: **+24 mean service ticks**, 2% of the 1200-tick horizon. This retains a
comparable development scale for a modest no-extra-parameter intervention; it is neither
a repository-wide threshold nor a claim about source value. Above +24 with useful native
tradeoffs I would recommend a bounded independent-seed follow-up; within (-24,+24) I would
report weak/heterogeneous value and favor no automatic expansion; at or below -24 or with
a material native loss I would retain direct mean and stop this narrow candidate. All
conditions, energy, events, terminal exposure and transfer counts remain visible; any
legal transfer is only a path fact. These are a proposed reading narrative, not a frozen
B card or permission to rewrite B06.

Prospective prediction, if the comparison is selected: **low-confidence positive sign
for the final service contrast; crossing +24 is uncertain**. The strongest contrary
outcome is at most -24, including the case of fewer invalid commits but worse service.
There was no pre-read source prediction to score. Owner prediction: **not taken**.

Headroom remains absent: no tuned same-information generic baseline/stated upper pair
on this host. Reuse the accepted baseline configuration because information, actions and
budget match. Missing exact headroom or complete cause does not hold this proposed B.
An exact support/certificate census would answer a stronger question and can have nested
work; it is unnecessary to decide whether this single learned proposal is useful.

Claim ceiling for a later positive result: an outcome-informed, finite B/EXPLORE native
service signal for one training pair on this host. It establishes neither stable
superiority, uniquely multi-agent benefit, safety, transfer impossibility nor
COPY−RETAIN/SHADOW−COPY value. No source arm/fork, forecast-package reopening, old LR/noise
sweep, private witness, forced promotion, event-law change or legal mask follows.

## 5. Exposure, source-derived work and engineering scope

`pro_packets/20260908_p53_own_command_mean/EXPOSURE_AND_COST.json` contains Python integer
arithmetic over the retained configuration and existing measured wall. New P53 exposure
is **0 initializers, 0 learners, 0 native steps, 0 optimizer steps, 0 evaluation episodes**.

Proposed later work, not admitted: two arms × one seed ×16×32×128 = **131072 ordinary
transitions**; two ×16×4×8 = **1024 optimizer steps**; two arms ×(4 initial +4 final)
= **16 episodes**, at most **19200 native evaluation ticks**. Per arm N=65536, with the
unchanged auxiliary law `2N+2E+H`, `0<=E<=N`, `0<=H<=20E`: **131072–1572864 native
training calls** per arm. Actual E/H and cost vary with trajectories and remain unknown.
One ordinary batched controller forward occurs per primitive training tick; no new
candidate/trajectory search, multiple controller calls per candidate, or scientific
source fork is added. Historical private label clones remain charged algorithm work.

Same-scale anchors are B05's complete pair **432.82 s** and B06's complete single
controller/comparison **226.02 s**, with relative L2 movement **0.04474046045735298** in
B06. These show a real learner can move at the retained exposure; they do not measure
new runtime or effects. Proposed bound is **1800 s per complete arm, 3600 s for the pair**,
including required checks, initialization, labels, training, evaluation and publication;
shared work is counted once and allocated equally. It is a new proposed cap, not an
unused historical balance. New mean/check cost is unknown; no timing experiment is added.

Added validation would be a focused own-vehicle/role mapping and live/replay likelihood
check plus the changed primary output, reusing existing evidence. No historical replay,
full arrays, support census, new telemetry, search or repeated smoke campaign is needed.
Portable execution would retain remote-first `wsl_4070`, native float64/policy FP32 CPU,
one Torch/BLAS thread, and fresh per-invocation resource admission. No resource admission
is attempted during this zero-execution preparation.

Engineering scope §4: **none newly required** for this source assessment or the proposed
mean change; reuse existing learner checkpoints, private labels and execution route.
No new implementation or §5 breach exists. P53 is pure source/document/question work,
so it enrolls no CM comparison batch. If a later Pro-selected card requires a new CM
assignment, Root must receive the same complete code spec, task, committed source and
original acceptance checks before any coding dispatch under the current comparison rule.

## 6. Question-driven literature and owner boundary

Retrieval question: is there verified local evidence for a previous-command mean
parameterization, or a caution against equating persistence with useful control?
The checked My-lib tracked registry still contains two synthetic example papers only;
both are excluded. The accessible real Inst-sci catalog has **190** records. A bounded
index query for residual/continuous-action/parameterization/action-space/smoothing/
projection/safety terms returned 36 metadata candidates. Their titles/abstracts did not
establish this exact mean mechanism; this is a searched-snapshot limit, not a novelty verdict.

The closest caution was checked in **Learning Uncertainty-Aware Temporally-Extended
Actions**, Joongkyu Lee et al., AAAI 2024, local ID `VS-0005`, source
`C:/Projects/Inst-sci/papers/MyLib/json/VS-0005.json`, page1 elements62–63 and page2
element73; corresponding local PDF is `pdf/VS-0005.pdf`. The source warns that persisting
a suboptimal action can harm performance. Its studied mechanism selects action repetition
length in Gridworld/Atari; it does **not** validate this DISH mean or its multi-agent effect.
Metadata records local PDF identity as verified, extraction ready, grade B, with missing
DOI/official URL warnings. The passage changes the proposed intake interpretation by
keeping persistence-induced service loss as the strongest contrary outcome and retaining
all adverse conditions. It does not justify a duration/ensemble intervention or a safety
claim. CM would need only the direct source pointers in §3, not this paper collection.

At this clean boundary, `item.py reviews --json` returned `[]` in main and this checkout;
the dated audit owner column contained no applicable override. No handled review or
prediction reply is invented. The Chinese source brief is
`docs/research/portfolio/owner/briefs/degraded_incumbent_shadow_handover/2026-09-08_P53-source.md`.
P2 item `docs/research/portfolio/owner/inbox/2026-09-08/20260908-dish-001.json`
shows the recommendation and pending decision without marking a B as auto-applied.
Its CLI trace corrects an initial ledger-pointer entry error: this checkout's question
row is line69 and source row is line68, not the originally entered line30. The trace
preserves that correction without inventing an owner reply. No owner wait or per-stage
approval is introduced.

## 7. Decisions this intake produces

1. **Object-tier source acceptance.** Options: (a) accept the mapped information/action
   facts at A/RECON ceiling and retain limitations; (b) infer a diagnosed cause or legal
   transfer guarantee from B06; (c) demand a runtime census. Recommend/select **(a)**.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **P53 preparation choice.** Options: (a) author one OWN_COMMAND_MEAN versus direct-mean
   Convergence question with the source map and bounded B cost; (b) source-based yield;
   (c) implement or run now. Recommend/select **(a)** under P53's conditional consultation
   route. The source provides an existing own input, a complete ordinary path and a fair
   null without a private legality dependency. **Owner-delegated decision (unattended,
   2026-09-03 instruction): (a).** This selects only the question, not the experiment.
3. **Direction-tier decision, pending Pro.** Options: (a) select the single proposed B
   under a concrete card/budget; (b) retain no successor for a precise scientific reason.
   DM recommends **(a)**. Convergence may reject the intervention's value or amend its
   bounded specification; no local substitute decision is made. A different family,
   extra arm or diagnostic campaign is not silently commissioned here.

The two automatic object rows are appended to `docs/research/portfolio/audit/2026-09-08.md`.
Owner flags: none; no critic dissent, close-call override or recast is applied. This is
a direction-local recommendation, with no Portfolio priority, capacity or lifecycle action.

## 8. Clean return and exact next route

Author one distinct request `2026-09-08-dish-p53-own-command-mean-convergence-01`,
packet `pro_packets/20260908_p53_own_command_mean/`, for
`em:degraded_incumbent_shadow_handover:convergence`. The existing verified conversation
is `6a9bec54-df00-83e8-9840-46440458f316`; its prior correction request is archived.
Historical retired conversations are not reused. Issue4 is open and reused as the same
direction discussion surface; its older title is not the current question.

Root receives the new full HANDOFF commit/path and fixed TASK URL, then dispatches that
exact handoff through configured independent Transport. Transport returns the matching
complete response receipt to Root, which wakes this original native DM for full immutable
response intake. No provider Send occurs in this authoring task. Completed bindings are
unchanged; normal branch advances do not replace the fixed input SHA.

Park this local assignment at the committed/pushed question boundary. Complete conforming
decision → same-DM intake → any selected prospective card/full CM specification → Root's
concrete implementation/budget route. A blocker forms no direction decision. A no-successor
answer yields without an abstract replacement assessment. The next scientific discriminator,
if selected, is the new pair's native final-modal service contrast, with native costs and
source-transfer facts reported separately.

## 9. Completed Convergence intake — 2026-09-08

**Accepted, conforming PRO_FINAL direction decision: select only
DISH-OWN-COMMAND-MEAN-B07, B/EXPLORE, one matched seed127 pair of OWN_COMMAND_MEAN
versus newly trained DIRECT_MEAN.** This supersedes the pending-decision statements
above, which remain the prospective source/question record. This intake implements
the scientific selection only; it constructs no model or RNG master, dispatches no CM,
and starts no experiment. Root's present return assignment requests intake and commit,
not implementation or another Send.

### Full evidence and delivery read

I read all 173 response lines directly from immutable commit
`ddb4c9ff20167837c99d146b2177c3e784066411`, in complete ranges1–90 and91–173.
`pro_packets/20260908_p53_own_command_mean/archive/RESPONSE.md` is 33313 bytes,
SHA256 `9797d7961500ddacfa1f61d6af03c29991190ef57d42beda747a8811adf7445d`.
Those are immutable Git-blob bytes; the local checkout has only Git's CRLF conversion
(33486 bytes), whose LF-normalized content matches that blob exactly.
The received SHA `c9f88329d4c558a280110e0b9c041786c38bec03bb0f9bcea6aa1b098c186b2c`
identifies the separate short chat receipt containing two delivery links, **not** the
complete scientific response. The exact chat receipt and Transport facts are retained
beside the response. A fresh API read of Issue4 comment5589714012 confirms the response,
fixed TASK `ba699af4e79be7a1c9dd6ef7811dc04c02c9ff14` and scientific input
`d19bded986f364600cf7769497d1daf3c8fc3ca6`; creation/update is18:11:43Z. That comment
snapshot is archived separately. Python could not open the long receipt path, but
PowerShell copied/read it and its hash matches the factual receipt; no access gap remains.

Git confirms one added response file,173 lines and0 deletions, on parent
`f1bb245c7045f48e0ab31dbd350fb0fec213789e`. The initially clean DISH checkout was
fast-forwarded to this delivery before editing. Fixed input, TASK, response and handoff
SHA roles are distinct; no completed packet or binding is rewritten.

Transport records one Send in the verified6 Pro/Latest conversation
`6a9bec54-df00-83e8-9840-46440458f316`, exact current TASK link pairing, and natural
completion after14m19s with no active generation control. DOM IDs were unavailable;
the retained pairing is link-based. These are attributed Transport observations, not
a DM browser inspection. The full immutable answer, not the receipt or comment summary,
forms the scientific decision.

### Rule applied verbatim and selected meaning

The response's opening decision, applied verbatim:

> **选择一个新的 DISH-OWN-COMMAND-MEAN-B07（B/EXPLORE）：新配对种子127，OWN_COMMAND_MEAN 对 DIRECT_MEAN，两臂各十六更新，只比较各自 update16 的完整模态原生服务，并保留各臂自己的初始化模态参考。**

The formed response chooses the first option in §7.3 and gives the concrete specification
in its §§二–七. The own-input formula remains `3*tanh(m+a_prev/3)` versus `3*tanh(m)`.
For physical vehicle i and decision-input owner o, select copy `2*i + 1[i!=o]` and
its **pre-decision raw actor** acceleration8:10. Preserve vehicle0x/y,vehicle1x/y order;
never use post-projection state, normalized features, old snapshot commands or successor
owner to rearrange an already recorded action. Prepare and commit keep their different
incumbent/standby-shadow decision origins and existing owner-slot serialization.

Keep every original learning/noise/private-label/native semantic in §§2–3. The selected
mean must agree in live generation, behavior likelihood, replay likelihood and the
duplicated training mean, using the recorded own input. Gradients still reach motion;
no environment gradient, detached entire mean, projected-action density or tanh-squash
Jacobian is introduced. Pro's §四 checks directly protect this changed training path
and primary reduction; they are not another scientific object or launch gate.

The selected master law is the literal SHA256 ASCII family in the response §三 for
seed127; it is recorded, not generated or invoked here. Both arms retain STRUCTURED
initialization and common exogenous streams, then separate optimizer/recurrent/Welford
and native evolution. Each arm has16 updates/65536 ordinary transitions/512 optimizer
steps, four own initial modal rows and four final modal rows, update16 only. Thus one
training pair has131072 transitions,1024 steps and16 episodes, at most19200 evaluation
ticks. Two arms and four conditions are not independent training replicates.

Primary: mean over four conditions of final OWN minus final DIRECT native service.
MEI is+24 ticks; opposite scale−24 and open band(−24,+24). Per-arm initial/final changes
are companion facts, not a change-of-baseline primary or proof of faster learning.
Response §五 retains useful-signal, within-band, adverse, own-initial-loss, no-transfer,
observed-transfer and damaged-primary branches. Preserve actual and zero-filled terminal
remainder ticks, energy with duration, seven hard-event categories, first CAS time/null
and ordinary service before/after transfer. Counts without opportunity denominators do
not become rejection probabilities; post-transfer service is not causal source value.

Selected complete cap:1800s/arm,3600s/pair including checks, common initialization/build,
labels, training, all evaluations and publication. Shared work counts once, splitS/2.
Per-arm native training remains2N+2E+H in131072–1572864 calls, plus evaluation and all
non-native compute; no extra search/fork is selected. Existing B05 pair432.82s/B06 single
226.02s and B06 relative movement0.04474046045735298 are planning evidence only. New
time/E/H/effect remains unknown. The committed exposure arithmetic is reused; this
consultation/intake adds0 learners/transitions/optimizer steps/evaluations/native calls.

### Scientific interpretation and conformance

Strongest support is the inspected own-input path in both live and replay and a real
same-information/direct-mean learner comparison. Pro selects this as a limited question
worth one pair, not a proved mechanism. Strongest contradiction remains redundancy with
the existing input/network/projection or persistent bad acceleration; other certificate
conditions can remain limiting. B06's−77.5, all adverse condition means, higher invalid
commits/energy, training events, two positive sample exceptions and zero transfers stay
separate empirical evidence. B04/B05 LR means and adverse conditions are unchanged.

The claim ceiling is a future finite B native-service signal on the accepted A03
information/ownership host. No performance result exists yet. Its native summary and
partner-feature limitations are disclosed; no strict-fresh-message decentralized or
uniquely MARL benefit is claimed. No source origin or COPY−RETAIN/SHADOW−COPY value is
estimated. Headroom is still absent. The P53/Pro positive-sign prediction is **pending**,
low confidence, with MEI crossing uncertain; owner prediction remains **not taken**.

I checked the whole decision against P53, current owner scope and evidence-spec §§4,
5.2,11.4,11.7–11.9. It selects the exact single proposed B and preserves the native
and information boundaries. No exact headroom/support/cause prerequisite, forced origin,
old LR/noise/forecast replay, extra arm, stronger C burden or specification exception
appears. No conflict requires returning to the node. Source/cost/likelihood checks and
ordinary independent engineering review serve the changed implementation; no code is
accepted by this scientific response. Engineering-scope §4 needs none newly; no §5
budget breach occurred in this documentation-only intake.

Main's current instruction delta at `8d58e5454502a8940b0126ed1dc81ba5a72168fb` was read:
Root continues the original DM route under existing authority, and current engineering
instructions govern later work. Pro's temporary-comparison wording is conditional on
what remains applicable; it imposes no new batch or scientific invocation. No coding
assignment is dispatched here. The source intake's verified literature record is reused;
no new mechanism, comparator or unexplained result needs further retrieval.

### Decisions this intake produces

1. Object-tier conformance: (a) accept this complete class-correct answer; (b) return a
   concrete scope/spec conflict; (c) substitute the short receipt. Recommend/select(a).
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. Direction-tier selection: (a) the one specified B07 pair; (b) no successor. Pro selects
   (a), and DM accepts its finite rationale. **PRO_FINAL**; **Owner-delegated decision
   (unattended, 2026-09-03 instruction): apply option(a).** This is not PARK/CLOSE/RECAST,
   C promotion, UAV-validation entry, or Portfolio disposition. Recast count is unchanged.
3. Current execution boundary: record selection and return to Root for the original DM's
   prospective card/full CM specification; no additional seed, implementation or run in
   this intake. No new Portfolio science selection or second Send is required.

The audit records the two applied decisions. The existing P2 item20260908-dish-001 gains
an actual PRO_FINAL execution trace selecting(a); this is scientific selection only, not
an owner reply or launched B. Owner flags:none. At this clean boundary owner reviews in
main and the direction checkout returned[], with no applicable non-empty audit override.
The existing Chinese brief is updated to the accepted decision. The next discriminator
is the selected pair's native final service contrast after the later card/implementation
route; this intake creates no evidence for that contrast.

## 10. B07 card and complete engineering handoff — 2026-09-08

Root reports integration of §9's `5b9390ba2da7c2002a512505c2a13f3045a57ab1` as
`221b4ff7b`, preserving concurrent audit rows, then assigns the original DM the selected
B07 card and full CM specification. This return is **preparation only**: no implementation,
model, training, native/UAV episode, experimental master, extra seed or Pro Send.

The existing checkout began clean at `5b9390ba2da7c2002a512505c2a13f3045a57ab1`, on
`codex/pro-dish-post-b06-20260907`. The B02/B03/B04/B06/first-trigger/r06 code surfaces
still have no content difference from accepted B06 launch `373d187200a91942385e9380770dcf9f8098aada`.
I read the current assignment, Portfolio's still-lagging B06 row, accepted DIRECTION/P53
§9 and only the code consumers needed to freeze the implementation. The Portfolio row
does not supersede the archived decision or Root's named continuation, and is not edited.

The controlling selection is the verbatim rule in §9. The new
`DISH_OWN_COMMAND_MEAN_B07_SCIENCE_CARD_20260908.md` records that exact single pair:
raw own applied acceleration and physical-copy mapping, full live/replay Gaussian law,
new seed127 master consumers, both real LOW_LR learners, 16 total own-initial/final rows,
the final OWN-minus-DIRECT primary, MEI+24 and complete 1800s/arm/3600s/pair charges.
Its seven result rows are copied verbatim from immutable response §五. No rule or past
result was rewritten. Card §1 preserves P52/P53/B06 support, contrary outcomes and the
same finite B/source-information ceilings; §§4–5 preserve incomplete-result dependency,
initial-relative limits, native tradeoffs and unestimated source value.

`DISH_OWN_COMMAND_MEAN_B07_CM_SPEC_20260908.md` is the complete five-item handoff with
starting source, owned entries, preserved semantics, original focused acceptance and
budget/stop. Source reading identifies **PersistentTrainer.run_update** as a necessary
third propagation boundary in addition to live policy and update engine. After each
update, policy reconstruction must retain mode. The current B04 shared helper's four
DIRECT references cannot substitute for OWN's four or be charged as common episodes.
The spec makes these concrete gaps explicit without adding a new framework or real test run.

Integer counts were recomputed through Python AST/configuration reads without importing
the learner/native modules: 65536 transitions,512 optimizer steps,2048 batched policy
forwards and8 episodes per arm; pair131072/1024/4096 and16 episodes<=19200 ticks. Native
training is2N+2E+H, per arm131072–1572864 and pair262144–3145728. These match the earlier
committed proposal arithmetic. Historical B06 relative L2 movement0.04474046045735298
supplies the existing exposure evidence; new effects, time and E/H remain unmeasured.
No master hash was generated. Added validation is the single focused synthetic changed-
behavior/primary check and existing independent engineering review, not another A or B.

Conformance checked against evidence-spec §§4,5.2,11.4,11.7–11.9 and engineering-scope
§§3–5. Section4 needs none newly and no implementation budget breach exists. Current
main instruction deltas at `27c0a4ed3efe4f4a3118af922d2260b07273ab0f` retain the original
DM/CM continuation and invocation-owned test-scratch cleanup. The comparison document
is absent from this authoring checkout, so its **committed main** copy was read; it records
all three CM comparison batches completed. Concrete exclusion recorded once: this is
science/card/spec authoring with no coding dispatch, and it enrolls no new comparison.
Root nevertheless receives the complete identical task/source/spec/acceptance before CM.
No current instruction file or unrelated Portfolio record is changed by this delivery.

### Decisions this intake produces

1. **Object-tier card wording/preparation.** Options: (a) freeze the accepted single B07
   card and complete implementation handoff; (b) return a concrete scientific/spec conflict;
   (c) add a diagnostic, new arm or stronger-class prerequisite. Recommend/select(a), since
   the full response conforms and existing source exposes all required paths.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Execution boundary.** Return the committed card/spec to Root for the already selected
   CM implementation route. The current DM assignment performs no coding or invocation;
   engineering acceptance and the later named launch remain separate from this card freeze.

The object row is appended to `docs/research/portfolio/audit/2026-09-08.md`; owner flags:none.
The required new-card P2 item `docs/research/portfolio/owner/inbox/2026-09-08/20260908-dish-002.json`
records the actual frozen choice under the standing delegation,
not an invented owner response. Owner reviews in main and this checkout returned[] at this
boundary; the existing prediction remains not taken. The existing source/decision brief
records that the card/spec are ready. No new valid performance result is claimed and no
extra result brief or new direction decision is manufactured.

Remaining uncertainties are exactly the future implementation and pair: correct mode/raw
input/likelihood propagation, completion of the fixed learning exposure, and its native
service/cost consequences. The next discriminator is still the paired final service contrast;
there is no need for a replacement Portfolio selection or another abstract Pro assessment.

## 11. B07 implementation acceptance and exact Root route — 2026-09-08

Root accepted the card/spec commit `fc52d630de39429383cb12ad7ec8e7b2877f67b6` and assigned
the existing DM the selected CM implementation/review route, then explicitly requested this
acceptance and exact submission command. CM used this same designated checkout/branch;
no other DISH CM was available to reuse at the new assignment, and the same CM and reviewer
handled all corrections. The prior three comparison batches were already completed as
recorded in §10; the timing repair is an existing-delivery correction, not a new assignment.

CM delivered and immediately pushed `0f6fa80fe76a2227792ce824abbcd95eb38b3a7e`, followed
by timing-source correction **`a4612a020921d24269a19a3471cc03fa62c082c8`**, then the literal
payload/record binding **`ae5cdea0f292d632c59eb79e655f6d4861a81224`**. At intake, local HEAD
and upstream both equal the last commit and the checkout is clean. These commits are already
present in the shared direction checkout; no source copying or merge is needed here. The
scientific execution binding is a4612a0; ae5cdea changes only the CM record. Root integrates
the named accepted changes while preserving concurrent work and checks what is already present.

### Checked artifacts, rule and bounded acceptance

The CM spec §4 rule applied is:

> Accept implementation by the actual changed paths, synthetic outputs and existing
> independent review, under card §§2–6 and evidence-spec §§4,5.2,11.4,11.8.6–11.8.7.

I read the actual shared-path diff, B07 study/runner, affected focused checks, retained final
test logs and complete CM record. The raw actor and normalized encoder input remain separate;
owner0/1 select physical copies `[owner,3-owner]`, preserving vehicle0 xy then vehicle1 xy.
The same differentiable `3*tanh(m+a_prev/3)` reaches live generation, behavior/replay density
and the engine's repeated motion term. DIRECT defaults, all mode propagation including
post-update policy reconstruction, raw Gaussian density and motion gradients are preserved.
Common initialization executes no shared modal episodes; each arm owns its four initial
and four final rows. The final four-condition contrast is retained separately from incomplete
initial-reference claims. The same LOW_LR STRUCTURED learners, master family/seed127,
65536 transitions and512 optimizer steps per arm, native boundaries and seven card branches
remain fixed. No change to B06 evidence or source-value interpretation follows.

The independent CM reviewer found and CM repaired missing native-work bounds and an ambiguous
publication charge. DM then returned a concrete timing defect: the original time-only wrapper
and disabled publication alarm could not enforce the complete cap. The same CM/reviewer repaired
it without another scientific invocation. Final publication retains the tighter pair/arm alarm;
the exact wrapper bounds admission, startup, execution and accounting externally. Timeout or
failed readback takes precedence over an earlier COMPLETE summary. Final independent disposition
is **no material finding remains**, recorded in
`DISH_OWN_COMMAND_MEAN_B07_CM_RECORD_20260908.md` (ae5cdea). No OS timeout experiment was added.

The original focused module ended **12 passed**,1 existing disabled-cache configuration warning,
in1.98s pytest time. Four process-wall charges, including the first absent-parent setup failure,
are3.3619347+2.8518697+2.6727375+2.8946026 = **11.7811445s**. I checked the retained cm03/cm04
logs and test coverage instead of rerunning the suite. Logs and precise commands are in the CM
record; these are small synthetic/intercepted engineering checks, not scientific learners or
native episodes. Source additions across the two source commits are301 gross non-test lines,
23 deletions; including the43-line staged payload gives344. The final runner is102 lines,
145 including that payload. Engineering-scope §4 needs **none newly**; no §5 source/test
budget breach occurred. Synthetic check success establishes the changed boundary,
not native-service value, training success or complete runtime conformance.

One technical limitation remains: automatic approval review rejected invocation-owned scratch
cleanup before execution, stating only **“blocked by policy.”** The ignored cm02/cm03/cm04
directories under `temp/directions/degraded_incumbent_shadow_handover/test/` remain, with needed
logs outside them and exact paths in the CM record. No alternate shell/agent bypass was used.
This is an explicit cleanup limitation; it neither changes the scientific comparison nor creates
an empirical failure. Required cleanup is not reported as completed.

### Decisions this intake produces

1. **Object-tier technical acceptance.** Options: (a) accept the corrected implementation
   and return its exact bounded launch route; (b) return a remaining correctness/scope conflict;
   (c) add a native smoke, historical replay or stronger-class prerequisite. Recommend/select(a):
   actual artifacts, focused evidence and repaired independent review support the frozen B07
   contract. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Existing execution route.** Root stages and submits the single previously selected pair
   with the binding below, adopts its accepted handle, and returns terminal evidence to this
   same CM and DM. This is continuation of PRO_FINAL B07, not a new direction/Portfolio choice,
   a second Send, a scientific retry, a new seed or formal UAV-validation entry. This DM intake
   performs no staging, admission, experiment or supervisor submission.

Owner reviews in main and this checkout returned[] at2026-09-08T20:08:21Z; the relevant recent
audit owner columns contain no override. No prediction reply exists; the prediction remains
unscored/not taken. The technical row is appended to the existing audit. No new P1/P2 item is
created for this ordinary engineering acceptance; the existing card/decision items remain.
The existing Chinese source/decision brief is updated only with implementation status. DIRECTION
is unchanged because this delivery supplies no new accepted mechanism-level science.

### Exact Root staging and one submission

Use the configured `wsl_4070` node via SSH `hmasd-wsl-node`, CPU native float64/policyFP32,
one Torch/BLAS thread. Staging facts are:

| Field | Exact binding |
| --- | --- |
| Scientific source SHA | `a4612a020921d24269a19a3471cc03fa62c082c8` |
| Payload document SHA | `ae5cdea0f292d632c59eb79e655f6d4861a81224` |
| Detached cwd | `/home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01` |
| Supervisor handle | `dish_b07_seed127_20260908_run01` |
| Relative envelope | `temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01` |
| Staged wrapper | envelope `/launch.sh` under that exact cwd |
| Scientific output | envelope `/run/` under that exact cwd |
| Admission | envelope `/admission.json`, produced inside the wrapper immediately before the runner |
| Logs/accounting | envelope `/runner.log`, `/supervised.time`, `/whole_chain.json` |

Extract only the bash fence between `B07_BOUNDED_PAYLOAD_BEGIN` and `B07_BOUNDED_PAYLOAD_END`
from the immutable ae5cdea CM record. Write UTF-8 LF with one terminal newline to the staged
wrapper; do not retype it, use the superseded 0f6fa80 time-only command, or substitute the
old8.8865419 check charge. Read-only extraction here produced **2432 bytes,43 lines**,
SHA256 **`2fb1d2bd447b0bb84594869cd50610de94518ac85a10c69ed400eaac382ceedd`**, no CR bytes.
The fixed source SHA is already literal in the payload. The run child is created only after
fresh same-node physical/effective memory admission>=4GiB; the envelope exists for staging/logs.

Root compares actual staged cwd/source with these existing bindings and syntax-checks the
actual staged LF wrapper without executing it, as current ROOT_OPERATIONS requires. The exact
PowerShell-to-configured-node syntax command is:

```powershell
ssh hmasd-wsl-node '/usr/bin/time -f "syntax_check_wall_seconds=%e\nsyntax_check_exit=%x" -o /home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01/temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/wrapper_syntax.time bash -n /home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01/temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/launch.sh'
```

After a successful exact staging check and reconciled not-yet-accepted handle, the **one exact
Root submission command** is:

```powershell
ssh hmasd-wsl-node 'PATH="/home/wu/.local/bin:/usr/lib/wsl/lib:$PATH" /usr/local/bin/agent-task run dish_b07_seed127_20260908_run01 "bash /home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01/temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/launch.sh"'
```

The outer PowerShell single quotes preserve the literal remote PATH expansion and the job's
single command argument. The job executes the CM's exact checked wrapper; this command does not
reconstruct its nested payload. No admission or accepted handle exists at this intake. If the
handle unexpectedly exists or acceptance is uncertain, reconcile its actual supervisor state;
do not submit a duplicate. A pre-admission transport defect returns to this same CM's repair
route. It is not scientific polarity or permission for another result-bearing attempt.

### Cost, collection and next discriminator

Decimal arithmetic over the retained charges gives S_check/2=5.89057225s, remaining
**1794.10942775s/arm and3588.2188555s/pair** before startup/closure. The fixed outer3587.21s
timeout leaves1.0088555s within the pair cap for outside-wrapper timing/closure; subsequent
required syntax-check attempts are retained as additional shared charge, never new allowance.
Measured startup is rounded upward at0.01s with a0.02s handoff allowance and enters the runner's
prior charge once. Its10s shared planning reserve and2s final closure margin are bounds, not
claimed measured cost. Later collection counts **checks + whole-chain elapsed + separately
measured required tail** once; it does not add the startup argv charge a second time. Shared S
is that total minus exclusive arm wall, allocated S/2. Preserve timer resolution, actual exit,
kernel termination latency and the final accounting-write boundary; neither timers nor a
COMPLETE marker prove complete-cost conformance. An observed cap crossing remains recorded.

The card's dominant work is unchanged: two arms×one paired seed×16×32×128 =131072 transitions,
1024 optimizer steps,16 initial/final modal episodes<=19200 ticks, native training
262144–3145728 calls plus evaluation. The updated same-scale B06 anchor plus checks is
231.91057225s/arm (463.8211445s pair), an estimate with unknown B07 trajectories/E/H, not a
new timing observation or launch guarantee. No cost pilot is added.

Root uses current EXPERIMENT_MONITOR/ROOT_OPERATIONS goal-driven observation: record the exact
accepted handle, node/source/cwd, admission/log/result paths and this native DM/CM identity,
then own routine observation. No scheduler or new automation is requested. At terminal state,
resume `cm_am_dish_b07` under `/root/dm_dish_p53_native_proposal_question` for collection and
technical acceptance, then this same DM for science. CM preserves all partial/full rows,
counts, per-condition service/native costs, own-initial deltas, first-transfer/null evidence,
terminal zero remainder, exit/timeout and whole-chain receipts in the card's result evidence.
Missing/truncated output limits its dependent claim; trustworthy facts remain reportable.
There is no extra invocation or seed on failure and no effect-based replacement.

The claim ceiling remains **unmeasured finite B/EXPLORE**: correct implementation is not a
native gain. Strongest support is the available own input plus coherent tested live/replay
path; strongest contradiction remains input already available to the network, native projection
possibly making the new path redundant, or persistence worsening acceleration. B06's service
loss and zero evaluation transfers remain contrary evidence, and source-copy value remains
unestimated. The next discriminator is exactly seed127's final modal OWN-minus-DIRECT service
contrast with all native companions, interpreted by the unchanged seven card §5 branches.
