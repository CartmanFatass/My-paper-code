Claim under assessment: retaining half of the standby's pre-arrival recurrent state when incorporating an ordinary snapshot may improve finite-budget native service over full bridge replacement; no such effect has been measured.
Binding MARL structure: systems / information flow. A physical vehicle combines its own causal history with its partner's received forecast/control packet while both vehicles act under the retained partially observed information interface; no membership change is introduced.

# DISH arrival-bridge retention reentry — 2026-09-10

**Recommend one specific B/EXPLORE comparison to Convergence, without selecting or launching it locally.**
The proposed new comparison is HALF_RETAIN versus REPLACE at ordinary snapshot arrival, with
fresh matched DIRECT/LOW_LR learners. This is a question about the finite-budget service value
of prewarming's information-processing rule. The post-CAS RETAIN/COPY/SHADOW source estimands
remain unresolved. P62's B06/B07 narrow stops and DIRECT remain binding.

## 1. Assignment, current authority and source versions

Root's 2026-09-10 native assignment to `/root/dm_dish_rolling_reentry` resumes DISH as an
independent rolling chain: resolve the ordinary-source question after P62/P67, classify the
choice, and use the proper node for a family-opening decision. It allocates **zero new scientific
exposure** before a separately selected, carded, costed, published and admitted invocation.
The owner-directed rolling-chain rule removes sibling/batch waits; it does not itself select
this mechanism or restore an old allowance. ACTIVE/MEDIUM and all historical budgets stay.

The designated authoring checkout is
`C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907`, branch
`codex/pro-dish-post-b06-20260907`. It began tracked-clean at
`f9d3aa52d398ddbb32ccad21e8033c662c07b283`, matching upstream. Commit `0864cba6f` copies only the
already accepted Transport endpoint from main `9b0c700b33d307745a5d7fbf88b1fb490a65d2ab`.
Accepted requests retain their old bindings. Current method references are pinned separately
to that main SHA; the direction's scientific source/evidence remain on this branch. Main's
older DISH engine lacks the branch's accepted B07 mean-mode additions, so it is not silently
substituted for the declared scientific source. No code, frozen card or historical archive changes.

I read the current Portfolio row, P62 intake §8, P67 intake §§2–6, the relevant DIRECTION sections,
evidence-spec §§11.4,11.7–11.10, and current authority/ownership instructions. The old workflow
descriptions in P67 are historical; current Root coordinates and integrates, DM authors and
checks this direction question, and the independent Transport sends/observes it. This intake is
an A/source-and-existing-evidence assessment; the proposed empirical observation is ordinary B.

## 2. Concrete observation and new hypothesis

P67 correctly distinguishes the **18-field forecast/control snapshot** from a serialized
128-dimensional incumbent GRU state. It already noted that the standby shadow controls motion
and commit-related predictions before any ordinary CAS. That observation was not a measured
benefit and P67 nominated no bridge variant. This reentry uses that same accepted path; it does
not claim a newly discovered defect or reinterpret P67 as selecting a run.

At `production_training_engine.py:88–104`, after episode reset, an active received-snapshot mask
selects the standby shadow and computes

`b = tanh(snapshot_bridge(concat(h, tanh(snapshot_encoder(packet)))))`.

The current REPLACE rule assigns `h_pre = b`; the ordinary actor GRU then advances with the
current normalized observation. Both the live caller and recurrent PPO replay use this method.
`production_recurrent_trainer.py:273–386` then uses that standby shadow for physical standby
motion, commit and prediction heads. Native CAS, if one occurs, has its separate unchanged
promotion rule. The intervention can therefore affect ordinary actions **before** any CAS.

B07's accepted E0 §2 reports final masked snapshot Welford counts **12,321 DIRECT / 12,309 OWN**,
alongside 65,536 training transitions per arm and zero ordinary TRAIN/EVAL transfers. The engine
updates that count from stored `snapshot_mask`, which the collector obtains from native
`snapshot_delivery_mask`. These are recorded masked training samples, not independent messages,
training runs, evidence of harmful overwriting, or a guarantee of future exposure. They do show
that a bridge-specific question is not limited to the already observed zero-CAS path.

**Proposed HALF_RETAIN rule:** on exactly the same active arrival, set
`h_pre = 0.5*h + 0.5*b`; otherwise preserve the current reset/advance path. Both old history and
the complete existing learned bridge remain in use. The factor 0.5 is a fixed first exploratory
choice, not a tuned optimum or a reliability estimate. No new weights, observation, message,
hidden size, loss, packet frequency, gate, owner transition or source promotion is proposed.
Both learners use the same complete allowed inputs; the new inductive bias changes how one
received input enters memory, not the declared information set or communication charge.

The source-based rationale is limited: the current learned replacement can substantially
re-encode a physical vehicle's own action-relevant history at receipt. An explicit retained
component may make that history easier to use during finite training while still incorporating
the partner packet. At fixed input/state, the proposed displacement from h is half the old
bridge displacement; this algebra does **not** imply a trajectory, action, stability or return
bound after policies and histories diverge. Real learning and native evaluation decide value.

Strongest alternative: the full bridge and following GRU can already learn to preserve useful
history, while immediate replacement may correctly discard stale local state. HALF_RETAIN can
delay useful adaptation or reinforce bad history, and a successful result may reflect optimizer
conditioning/co-adaptation rather than uniquely useful information. The current rule remains a
competent matched comparator, retrained here if selected, not an inferior archived endpoint.

## 3. Knowledge and literature: what they change and what they do not

Scientific-reading mode used `FOUNDATIONS.md` §§2–4 and `topic-notes/02_MARL.md`'s first two
sections at the current method SHA. The concrete assumption is that different recurrent update
rules can change actions at fixed weights; that is distinct from parameter learning. Consequently
the proposal trains both complete policies and reads native service, rather than treating a
hidden-state difference as an empirical advantage. The allowed actor interface, including A03's
partner/current-summary ceiling, remains literal; no strict fresh-message decentralization claim
follows. Expressiveness of the full bridge does not settle finite-budget learning performance.

The formal Inst-sci catalog was rechecked: 190 records, unchanged SHA256
`2e682c6d1131d503ad48920794dd8005ccf8f535dc9ff75679b0c8502533efc0`.
Six explicit memory/message-weighting terms yielded 14 metadata candidates. My-lib's checked
registry still contains only two declared synthetic fixtures, excluded. This states the searched
surfaces, not complete local coverage, novelty or absence of other methods.

Verified source passages: Yu et al., *Robust Communicative Multi-Agent Reinforcement Learning
with Active Defense*, AAAI 2024, DOI 10.1609/aaai.v38i16.29708, local `MARL-0050.json`, page1
ids50/53 and page2 id84. The paper weights message-derived action preferences using learned
reliability and local history under attacked communication. It supports treating message influence
and local history as distinct design quantities; it does not test this bridge, justify coefficient
0.5 or show that DISH packets are malicious/unreliable. No defense classifier is imported.

Reverified the relevant P67 CoDe source: Song et al., AAAI 2025, DOI 10.1609/aaai.v39i22.34497,
`MARL-0066.json`, page1 id25, page3 ids155/156 and page4 id158. Its historical GRU encoding,
future-action intent prediction and message alignment constitute a different learned package.
They do not establish the proposed fixed interpolation's value. The source read informs the
limited information-processing hypothesis and comparator, not an authority or prerequisite.
Metadata for both is official-title-matched, grade A, with no warnings; substantive claims above
come from the passages. Exact access/counts are in `evidence/2026-09-10-arrival-bridge-reentry.json`.

## 4. Proposed smallest empirical discriminator, not an allocated card

Option (a) opens only the arrival-bridge comparison for **one fresh matched training pair**:
REPLACE versus HALF_RETAIN. Preserve GROUND-TERMINAL-LINEAR-CLEARANCE-A03, the corrected ordinary
renewal boundary, underlying STRUCTURED, DIRECT_MEAN, raw service-Q logits, original auxiliaries
and private-label work, recurrent PPO/AdamW with both groups at 3e-5, native float64/policy FP32,
CPU and one Torch/BLAS thread. The complete B07 direct path is the source reference. The stopped
OWN_COMMAND_MEAN and joint sampled-execution arms do not return.

Each arm would receive 16 updates ×32 lanes ×128 primitive ticks; final **update16 only** on the
same four condition/reset coordinates drawn from a new declared master. The executed modal
deployment rule stays unchanged; exogenous worlds are sampled by the existing addressed law.
No new action-sampling comparison is introduced. One paired training seed is the independent
learning unit; four conditions are not four training replicates. Initial-policy evaluation is
unnecessary for this final-only primary and is omitted, not silently borrowed from B07.

Primary: equal-condition mean of HALF_RETAIN minus REPLACE complete native service ticks.
Retain every condition and energy, invalid-commit, separation, slew/continuity and ordinary
transfer observations; TRAIN and EVAL stay separate. No new opportunity denominator or whole
cause census is requested. Ordinary transfers are descriptive companions, never an eligibility
filter or a requirement to estimate this all-trajectory service contrast. Zero transfers leave
post-CAS source value unestimated even if ordinary service improves.

Proposed MEI is **24 service ticks**, 2% of the 1,200-tick episode horizon, because this modest
same-parameter intervention needs a practical scale for a bounded follow-up judgment. This is a
new proposed card's scale choice, not a inherited result rule or repository threshold. Above +24
would favor a separately considered replication; a small inside-band gain could still justify a
follow-up with its uncertainty and costs visible; an opposite sign would favor retaining REPLACE
and ending this candidate. None implies stable superiority, proves no value, or allocates a seed.
Tuned same-information baseline/upper headroom is absent, not zero and not a stop reason.

This is a whole-policy finite-budget performance comparison, not isolation of delayed-message
harm, post-promotion source value, memory necessity, unique MARL benefit or a formal UAV entry.
No replay absorption certificate, saved-origin search, exact upper, diagnostic campaign,
positive-first gate or extra source measurement precedes B. A post-CAS-only COPY/SHADOW run is
the alternative question that can remain unestimated with no events; it does not answer this
pre-arrival-history intervention and is not silently bundled into the proposed purchase.

## 5. Cost, exposure and prospective engineering boundary

`pro_packets/20260910_arrival_bridge_retention/EXPOSURE_AND_COST.json` computes from the retained
configuration, without importing learner/native modules:

| Dominant work | Per arm | Proposed pair |
| --- | ---: | ---: |
| Ordinary training transitions, 16×32×128 | 65,536 | 131,072 |
| AdamW/backward minibatches, 16×4×8 | 512 | 1,024 |
| Batched ordinary policy-forward ticks, 16×128 | 2,048 | 4,096 |
| Recurrent replay steps per minibatch | 64 | 64 |
| Final native episodes | 4 | 8 |
| Final evaluation ticks / width1 forwards, at most | 4,800 | 9,600 |
| Native training calls, 2N+2E+H | 131,072–1,572,864 | 262,144–3,145,728 |

Here N=65,536, 0≤E≤N and 0≤H≤20E per arm. Private labels are existing algorithm work; actual E/H
and runtime can differ after trajectories diverge. HALF_RETAIN adds a width128 elementwise blend
at active bridge uses in live/replay, with no candidate tree, new network or diagnostic search.
The actual number of future active samples and any uninstrumented H remain unknown. Ordinary
checks do not become additional learner runs or a mandatory profiling experiment.

**Machine-generated consultation exposure:** 0 initializers, 0 models/learners, 0 training
transitions, 0 backward/optimizer calls, 0 episodes, 0 native calls and 0 scientific invocations.
**Proposed B exposure:** 2 real learners, 131,072 transitions, 1,024 optimizer steps and 8 final
episodes≤9,600 ticks. Historical B07 DIRECT at this learning rate/exposure moved by relative
parameter L2 0.04690254949701972; this is evidence that the retained learner can move in this
budget, not a prediction, new fit or guaranteed displacement.

Proposed new cap, **unallocated**: 900 seconds of arm-exclusive initialization/learning/
evaluation/publication per arm plus at most 300 seconds of shared necessary support, for a
2,100-second complete pair. Shared support is charged once and split equally for complete
per-arm reporting, so each arm's projected charged cap is 1,050 seconds. It includes all needed
checks, build/load, source/input staging computation, common initialization, observation tool
work, collection, intake/publication and preservation/closeout computation. Administrative human/
provider latency is recorded separately; no actual machine work is silently exempted. The later
card must reserve publication within these totals and state the exact arm/pair stop command.
No failed check, slice, new process or incomplete arm replenishes the allowance.

B07's known subtotal 463.83358418601877 seconds plus unmeasured syntax-check cost and B05's
432.82-second complete pair are historical scale anchors, not guarantees or balances. The
proposal removes eight initial evaluation episodes; changed trajectories/bridge arithmetic,
current machine load and full observation/closeout costs remain uncertain. No cost probe is
purchased to make the proposal. Pro may decline its decision value without interpreting that as
a source-effect negative or demanding a cost experiment first.

No implementation is commissioned at this boundary. If selected, DM freezes the exact B card,
new seed/master, source and command before execution, then implements directly. The prospective
L0 is the two-arm bridge rule and final-only primary in §4; owned code is the recurrent engine,
its live/trainer parameter plumbing, one direction-local B08 runner and focused direction tests.
Preserve live/replay agreement, reset-before-bridge, owner/physical-copy mapping, promotion,
checkpoint loading, actual behavior likelihood, optimizer and publication semantics. Reuse the
existing paths and run a focused changed-bridge/replay/primary check with independent high-risk
review under current ENGINEERING_SCOPE_SPEC §7.3. No full historical suite is requested.
Engineering scope §4 needs **none** for this preparation; no new prohibited machinery is proposed
for the comparison. Ordinary 2,000-new-line/600-runner and directory-test limits apply if built.
Nothing here accepts code, changes an old scope exception, or authorizes a scientific invocation.

## 6. Decisions this intake produces

1. **Object-tier source/proposal acceptance.** Options: (a) accept the bounded source/count
   reading and nominate the concrete HALF_RETAIN comparison; (b) repeat the P67 no-candidate
   conclusion; (c) launch or infer a bridge defect from old counts. Recommend/select (a).
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This selects preparation
   only. The changed recommendation is explicit and outcome-informed by existing evidence;
   it does not rewrite P67 or treat another direction's result as permission.
2. **Direction-tier choice, pending Convergence.** (a), recommended: open the narrowly described
   arrival-bridge ordinary-service comparison for one B as proposed; (b) select no successor,
   retain DIRECT and the existing narrow stops with the source agenda unresolved. The full
   node response decides this family-opening choice. No direction option is auto-applied now.
   A wider family/lifecycle stop or recast is not requested. Any concrete conflicting requirement
   returns to the same node; a connector blocker forms no scientific decision.

DM建议：请 Convergence 选择一次 HALF_RETAIN 对 REPLACE 的新 B 比较，只改变普通快照到达时的记忆混合；当前仅提交问题，不启动训练，也不恢复已停止的执行规则。

The recommendation is a close call: training bridge exposure and a concrete active control path
favor one modest real comparison; the strong full-bridge null, arbitrary first coefficient and
absence of measured arrival-related harm favor no successor. The proposal does not require such
a harm diagnosis before B. P62's negative B07 service difference −135.25, B06's separate −77.5,
all B07 energy increases, the +74 B07 condition, fewer invalid commits, earlier LOW_LR gains and
adverse conditions, and B05 CONTROL's three ordinary training transfers all remain intact.
Different treatments are not pooled as replications of the proposed bridge effect.

An object selection audit row records only consultation preparation and flags `close-call`.
The P2 direction/close-call item `20260910-dish-001` carries both options, this packet and no
auto-applied direction choice. Main and direction all-age review queries returned []; applicable current DISH owner
columns were empty. There is no new empirical prediction to score and no owner prediction.
No owner reply is awaited. The separate Chinese A/source brief records the bounded reading.

## 7. Clean return

Author one new fixed GitHub question on `em:degraded_incumbent_shadow_handover:convergence`,
reuse verified provider `6a9bec54-df00-83e8-9840-46440458f316`, the designated branch and Issue4.
Return the published request, full TASK/HANDOFF commits and exact handoff path to Root for the
single configured Transport dispatch. Source is this DM, parent is Root; the independent
Transport endpoint is `01a087a3-4f12-7021-9a4d-6da9da2bafcc`.

The next discriminator at this boundary is the complete formed direction decision, intaken by
this DM against the fixed question/current specifications. No model, native process, scientific
root, test scratch, monitor registration or Pro provider Send has been created by preparation.
The shared checkout remains for its scoped response and subsequent intake; Root owns later
integration/reclamation. No historical scratch-cleanup rejection is retried or bypassed.

## 8. Complete Convergence intake and application — 2026-09-10

**Direction decision: execute option (a), one narrow HALF_RETAIN versus newly trained REPLACE
B/EXPLORE comparison.** Provenance is `PRO_FINAL / OWNER_DELEGATED`, under AGENTS §§2,4;
this opens only the arrival-bridge ordinary-service question. It is neither a recast nor a
Portfolio, C, UAV, source-fork or historical treatment decision. P62/P67's actual no-successor
boundaries and B06/B07's negative readings remain historical facts, not replenished budgets.

I read the complete 180-line response directly from immutable commit
`9e99e48dca9fe34b25c11cb7814ba4d54e83a2b5` (36,690 bytes,
SHA256 `9c546ba09f072f0cbb04c0c595ff95b2c631f01f8ed4198a357031587726a991`).
Its only changed path is the authorized `archive/RESPONSE.md`, descending directly from the
published handoff. The fixed TASK is `8d5ca0162f0325fe45e5bb13da1ce48ce2ec1fdc`;
Issue4 delivery comment5625186169 names that TASK and response. All thirteen input path/SHA/byte
mappings matched the publication record. Current primary methods at
`1f63c0168f7535ef1af8fc03c3db764ff2eb9455` are unchanged on the relevant AGENTS, evidence,
engineering, Root-operations and compute surfaces relative to the fixed method revision.
[Response readback](pro_packets/20260910_arrival_bridge_retention/RESPONSE_READBACK.json)
retains these checks; `archive/transport/` retains the original four Transport files.
Transport's 362-byte chat response is a delivery receipt, not the scientific answer.
One Send and natural completion were reported; no author Send or resend occurred.

The rule applied verbatim from AGENTS §2 is: “A complete archived Pro response that decides the
posed question at its declared evidence class and within current owner instructions and applicable
specifications is final for its node.” The response selects the posed finite learning question,
keeps same-information REPLACE, gives a nonzero learner exposure and primary, and uses the exact
submitted new cap. Its reset/mask/promotion/gradient and checkpoint clarifications protect the
selected recurrent comparison; they require no stronger evidence class, source-prevalence A,
exact upper, policy search or specification exception. No concrete conflict remains.

The accepted source chain is packet receipt → standby shadow → ordinary action and prediction →
native consequence → recorded rollout and existing private labels → PPO/AdamW → final service.
Historical masks prove this path was used, not that replacement is harmful. The strongest support
for purchasing B is a concrete active control and learning path. The strongest contradiction is
that the full bridge/GRU can already retain useful information and the blend may retain staleness.
The earlier scientific-reading assumptions remain current: recurrent state need not be sufficient,
fixed-state displacement is not learned return, and model expressiveness does not establish
finite-training equivalence. The pinned local literature supplies no evidence for factor0.5.

### Decisions this intake produces

1. **Direction:** (a) open the specified one-pair arrival-bridge B; (b) retain no successor.
   Pro recommends and selects (a); execute (a), with the close call and strong null retained.
   Trace existing owner item `20260910-dish-001` as applied, without inventing an owner reply.
2. **Object:** (a) freeze B08 with fresh seed137 and the new B08 master family, unchanged selected
   exposure and fixed0.5; (b) change exposure, coefficient, comparator or conditions; (c) wait for
   a proxy diagnosis. Recommend/select (a). **Owner-delegated decision (unattended,
   2026-09-03 instruction): (a).** The [B08 card](DISH_ARRIVAL_BRIDGE_RETENTION_B08_SCIENCE_CARD_20260910.md)
   records exact inputs, predictions, cost, branches and L0 before implementation and any output.
3. **Technical acceptance:** still pending the actual source diff, focused checks and independent
   high-risk review. No scientific launch or empirical effect is inferred from this Pro intake.

Main/direction all-age owner reviews were checked at receipt and card freeze; no relevant pending
reply was returned. Owner prediction: not taken (unattended). Record the new card P2 item and both
decisions in the existing audit. The next discriminator is B08's complete final service contrast
and native costs under its one-pair allowance; no automatic replication follows any result.
