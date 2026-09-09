# ACVC P76: native link-loss mapping for the original Convergence node

Source-supported proposal: a private, correctly bound observation of lost link eligibility may make a learned motion correction useful against competent fixed controls on the existing five-UAV service host.
Binding MARL structure: other-agent non-stationarity and partial observability; simultaneous teammate motion changes interference and service assignment while each actor sees only its own filtered observations.

## 1. Assignment, authority and acceptance

P76 commissions one source-backed mapping and a bounded proposed B question, or a concrete
no-ready fact. It permits exact GitHub TASK/HANDOFF preparation for Root, not a card, model
import/instantiation, evaluator, episode, diagnostic, probe, implementation, master, run or Send.
This intake selects **READY_QUESTION / DIRECTION_DECISION_PENDING**, not family re-entry.

Checkout: `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`. Starting SHA was
`7380cf5762796aa4206220c7c4c2969dff744fa6`, clean. Required main inputs were merged at
`c5debab878e17382535e8dc34d4f6a209306191c` from main
`477331c62ab03e0f9beca4369d0761e81a803569` and pushed. The sole append conflict was the
identical existing P68 audit row; its equality was checked and all later rows retained once.
Root owns main/integration; this assignment changes only ACVC preparation and owner/audit records.

The current Portfolio row is ACTIVE/MEDIUM. Recasts remain **2**, with the existing lowest
sequencing instruction; no lifecycle, priority, investment or third recast is selected here.
R03's `0.2139371014275... < 1/4` certificate closes only the unchanged uncertain/delayed
learner-investment host. R02's positive legal-history gain `0.022197511111...` and action
witness remain. No rescue, retry, threshold retuning or causal explanation is inferred.

Controlling inherited rule, verbatim, from the archived Convergence 02 response, HC-C:

> **Re-entry condition:** a new, independently motivated host must prospectively specify a competent same-information history policy expected to change a legal action and clear `1/4` native-return headroom over its strongest competent fixed null. The current thresholds or envelope may not be tuned to this result.

Evidence-spec §§11.4, 11.8.1–3, 11.8.6–7 and 11.9 control the next question. Missing an exact
upper, tuned headroom or unique mechanism explanation does not require a diagnostic before B.
The action mapping below is a source inference and proposed learning experiment, not an exact
history witness or evidence that the inherited expected-gain condition has already been met.
The return-unit issue in §4 is explicitly returned to the same node.

## 2. Native event, information and action path

Direct source was read without importing it. The environment, adapter, UCOPE environment/policy/
learner and MGTAP geometry surfaces have no diff between accepted P75 source
`4f65eefb1b15e44b42d694376630fba0c230cc6c` and this checkout. Relevant facts:

| Source | Direct fact and consequence |
| --- | --- |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:9` (`make_real`) | Five UAVs, 50 static uniform users, 1000 m square, heights 50–150 m, speed scale 30 m/s, 256 one-second steps, free-space vectorized channel, no shadowing, no FDMA, native reward. This independently existing service task is not a new counterevidence simulator. |
| `envs/pettingzoo/uav_env.py:382` (`_get_observation_vectorized`) and `:575` (`_local_user_entries`) | The 20 user rows are relative XY and normalized SINR, sorted among SINR-eligible users; unused rows are zero. Despite a stale dimension comment, the third value is SINR, not distance. The inclusion threshold is 3 dB. |
| `environment.py:28` (`actor_features`), `:42` (`own_positions`), `learner.py:51` | Each private actor receives its own 104-value observation plus own previous command and remaining timer. Primitive feedback has remaining zero. Own coordinates are recoverable. Global user IDs, service assignment, full SINR, another actor's history and current command are absent. |
| `uav_env.py:229`, `:279`, `:888`, `:947` | Users remain at their reset positions. Joint UAV movement updates interference; eligibility is followed by greedy global assignment, one UAV per user and at most ten users per UAV. Losing an own eligible link does not establish global loss of service. |
| `uav_env.py:1463`, `environment.py:49`, `learner.py:126` | Native team reward is `0.7 * served/50 + 0.3 * mean clipped connected-link quality`; the five per-agent rewards sum to it. Team reward is the learning target, not an input secretly fed into the actor. |

**One bounded negative fact.** At time t−1 retain just the lowest-SINR nonpadding user row
observed by that UAV. Bind it to the static coordinate reconstructed from own XY plus relative
XY, the observing UAV, t−1 and the actually applied own motion. At t, if fewer than 20 user rows
are nonpadding and that coordinate is absent, its own link has fallen below the inclusion
threshold. The absence cannot then be caused merely by top-20 truncation. Current rows contain
every currently eligible user when the list is unsaturated. Compare the anchor with at most
20 current rows; skip an ambiguous coordinate match under a modest FP32/geometry tolerance.
Do not identify an entity by its changing sorted row slot. No global identity lookup is legal.

Only the prior anchor is remembered for this cue, for one transition. A full retained-user
census is unnecessary. At a saturated current list, absent/ambiguous history, t=0, or an episode
reset, no negative cue is asserted. The cue says **own-link eligibility loss**, not false
teammate testimony, failed global service, or proven harm caused by the preceding motion.
Teammates can create interference or take over service. Those are reasons to learn whether
correction is useful rather than to equate local prediction with native value.

**Different legal action.** Each UAV's existing frozen DENSE controller proposes a legal
normalized velocity b_t. A corrective velocity c_t retraces its own realized previous
displacement: `(p_(t−1) − p_t) / (30 m/s * 1 s)`, with the ordinary legal clipping for FP32
rounding. Both positions are its own permitted observations. Since the previous displacement
was produced by a legal one-second action, this is a legal one-step action. It approximately
restores the prior own position, including when the preceding proposal hit a boundary; it
does not reverse other UAVs or guarantee recovery of the link.

The proposed switch is available only on the unambiguous loss cue and when b_t's horizontal
component points away from the remembered user. Otherwise every arm applies b_t. The fixed
cue handler always chooses c_t when available. Learned handlers choose b_t or c_t there.
No added duration, sensing cost, reward, message, new sensor or counterfactual environment call
is required. An implementation must store the actually applied command for future base inputs.

A concrete information distinction is a currently invisible user previously seen west of the
UAV versus one previously seen east. The current filtered list need not reveal either user;
for the same eastward proposal, the bound west history opens correction while the east history
does not. This is an information/action example supported by the observation law, not an
enumerated positive-probability trace or measured reward witness. Which choice improves team
service depends on partner interference, handoff and competing users, and is exactly what the
real comparison would measure. A fixed rule may already contain all useful handling.

**Trace to learning and native consequence.** Simultaneous motion → owner-local channel row
loss → one static-coordinate anchor plus private history → apply/retrace selection → actual
joint motion and reassignment → unchanged team reward and gamma=1 return-to-go. All five
learned gates share parameters with separate private recurrent states and co-adapt through
their trajectories. Membership is fixed: no join, leave, replacement or slot reuse, and all
history resets per episode. Primitive time and decision opportunity coincide; there is no
semi-Markov or horizon-censored duration claim. The centralized predecision critic remains
learning-only. Only the gate's sampled Bernoulli factor has trainable policy likelihood;
the common frozen base proposal's likelihood cancels. Gate-opportunity and actual parameter
movement counts are necessary to interpret gate learning, not a separate launch probe.

## 3. Competent controls and the proposed minimal B

Use P75's first listed completed **DENSE/8201 final checkpoint** as the common, fully frozen
motion proposer. Both P75 outcomes were already visible when this choice was made, so the
proposal is outcome-informed and conditional on one fixed base. No checkpoint search or
new baseline training is requested. The accepted collection reports real actor movement
`0.2409414873` relative to initialization and 512 training episodes/1024 Adam updates. Its
own original 32-episode panel gave mean J `0.1922357063`, versus hover `0.1478473820`.
The other DENSE/8202 panel gave `0.1687618179`, versus hover `0.1413671718`. These support
a trained reachable control; they do not establish tuned competence on future ACVC trajectories.

The checkpoint's existing local bytes were read for identity only: `final_DENSE.pt`, SHA256
`f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`, matching the accepted
collection. No tensor/model load occurred. `SOURCE_AND_WORK_FACTS.json` records the retained
local/remote evidence source. Pro need not download or execute the checkpoint to decide the question.

The four proposed evaluation policies are:

- **C:** always apply the frozen DENSE proposal. This is the competent fixed base control.
- **F:** same frozen DENSE recurrence, always retrace on the named cue. This is the strongest
  directly specified deterministic counterevidence null, not an optimal-policy certificate.
- **T:** learn a private recurrent apply/retrace gate using the bound anchor and the same
  raw current/prior observations, own actions and base proposal. The small structured path
  explicitly presents the anchor coordinate, prior SINR, age and ownership to its gate.
- **G:** a containing generic learned gate: retain T's entire trainable path and add an
  unconstrained dense residual from the same raw private history to the gate logit. Setting
  the residual to zero contains T by construction. It receives every derived anchor feature
  T receives, so there is no information advantage for T. The common part starts identically;
  the residual output starts at zero. Its extra capacity/work is declared, not equalized by
  reducing its learner budget. The exact small head sizes are a later card detail.

C and F are explicit constant gate choices available to both learned controllers. This is
functional containment, not a claim that finite SGD must find the constants or G must win.
All arms have independent private base recurrence following their own actual trajectory;
none reuses another arm's hidden state. T and G start fresh gate/critic training on one
matched new instance, with paired exogenous reset panels and separate action streams.
No master is chosen. Train only gate and critic; do not fine-tune the selected base.

**Question:** does learning when to use this counterevidence create useful native return over
the two competent fixed responses, and is constraining the handler to the structured path
worth anything relative to the containing generic learner? Primary report: every T−C and
T−F paired native-return difference; summarize T minus the better of the two panel means
without hiding either contrast. T−G is the mandatory structure comparison, and G−C/G−F
identify a generic learned-package result. All four native values remain visible.

If T clears the declared margin over C/F but loses to G, the result supports at most a learned
correction package; recommend the generic route, not ACVC structure superiority. A positive
T−G with a native loss to C or F does not rescue performance. Within-margin differences are
not equivalence. Adverse native differences or little gate exposure may end this bounded
comparison or motivate a specific new question through the existing ladder; they never
reopen the closed uncertain/delayed host. One training instance gives no training-population
uncertainty. Conditional paired episode SEs describe only its fixed evaluation panel.

P75 MGTAP's REL−DENSE results remain separately adverse (`−0.0446825`, `−0.00324368`).
P74 VSPC1's two 768-episode comparisons remain separately negative; latest B09 T−MLP is
`−0.01353496`. Neither loss becomes ACVC evidence, and neither is suppressed. Their shared
host/code is useful; their geometry/duration/value objectives are different. This proposal
reuses a baseline asset, not a fused direction or new Portfolio recommendation.

The P68 question-driven local-library retrieval is reused only as adjacent grounding:
communication confidence and counterevidence require an owned action path. No retrieved paper
establishes UAV gain or makes a channel measurement a teammate message. The new evidence is
the actual native observation/assignment/action source. No broad retrieval or novelty verdict
was repeated. CM, if later assigned, needs the source entries above, not that citation tree.

## 4. Gain expectation, return units and headroom

The existing native evaluator emits both `reward_sum = S` and `J = S / 256`
(`learner.py:165`). Keep both unchanged and visible. A proposed new-host MEI is **0.01 in J**
(2.56 raw episode reward), because a one-percentage-point persistent service-quality gain
would justify a small next investment; this is not a repository-wide threshold.

For the archived re-entry wording, the prospective interpretation proposed to Convergence
is `1/4` in the unnormalized native episode return S. Its reporting conversion is
`0.25 / 256 = 0.0009765625` in J. This is **not locally adopted**. If the archived node
intended `1/4` in the host's reported J, that is a materially different requirement, and
the inspected evidence does not support predicting an extra 0.25 average reward. The node
must resolve that meaning explicitly before selecting the affected new-host object; do not
silently lower the threshold, claim it passed, or tune any old-host threshold/envelope.

The low-confidence positive mechanism expectation in raw S is concrete: avoiding the net
loss of one served user for 18 primitive steps contributes `18 * 0.7/50 = 0.252` through
the coverage term. This is scale arithmetic, not a reward guarantee: changing the connected
set's mean quality, useful handoffs, travel and partner motion can erase or reverse it.
The learned handler may avoid the blind fixed handler's unnecessary retraces while correcting
genuine loss. C/F or G may already contain all that value. No numeric fitted-gain forecast,
headroom measurement or empirical prediction is scored by this preparation.

There is no tuned same-information upper-minus-generic headroom record for this host. The
P75 panel and checkpoint are a reusable competence reference, not that record. A complete
exact maximum, policy/trajectory search, tuning sweep or pre-learning positive measurement
would not answer this bounded performance question more economically. Under §11.8/11.9
none is proposed as an A or B prerequisite.

## 5. Known work, unknowns and exposure

All arithmetic below is machine-generated in
`pro_packets/20260909_native_link_loss_convergence/SOURCE_AND_WORK_FACTS.json`.
One proposed matched instance uses two trained gates, each 512 complete 256-step episodes,
256 two-episode rollouts and four Adam calls per rollout; final checkpoints only, with
32 fresh paired episodes for each of T/G/C/F. That is **294,912 native team steps,
2,048 optimizer updates, 512 rollouts, 1,152 explicit resets and 128 final evaluations**.
This is 1.02857 times P75's pair step count, not a wall-time forecast.

The frozen base contributes 1,474,560 agent forwards. A gate at every primitive observation
would add at most 1,392,640 agent forwards over T/G train and evaluation. Actual switch
opportunities, gate movement and their value are unknown; a critic update alone is not gate
exposure. The generic residual's extra operations remain part of G's full invocation.

Cost review changed the question before any engineering: matching all 20 past users would
require up to 573,440,000 coordinate pairs. One prospectively selected anchor suffices,
reducing the bound to **28,672,000** pair comparisons across T/G/F. This is observation
bookkeeping intrinsic to the proposed algorithm, not policy search or a support census.
C requires no matching. There are no nested candidate rollouts, joint-action cross-products,
future-trajectory searches, solver calls, extra evaluation checkpoints or validation episodes.

P75's existing complete pairs took 353.71 and 368.12 seconds on the declared remote CPU;
those are reference measurements, not timings of the new gates/matching. Proposed stop bounds
are 1,800 seconds per complete learned arm and 3,600 seconds for the complete logical study,
including initialization, C/F evaluation, checks and publication. New wall/RSS and trigger
frequency remain unknown. This preparation allocates none of those invocations. If the direct
comparison becomes too expensive, reconsider the question, not a hidden pilot, higher cap,
parallel justification or added orchestration. Later portable execution uses the current
`remote_first` node, exact committed source and fresh node-local memory admission.

Engineering-scope §4: this preparation needs **none** of its listed machinery. The proposed B
needs no new distributed execution, checkpoint/recovery orchestration, guards, registries,
validation service or extra telemetry. Reusing one final base checkpoint is input loading,
not a resume mechanism. Existing final learner publication, one proportionate changed-path
check and native primary checks would be sufficient within the 2,000/600-line budgets.
No implementation diff or section-5 budget breach exists here.

Machine exposure line: **P76 consultation: new scientific invocations=0; model
instantiations/imports=0; native steps=0; optimizer updates=0; evaluation episodes=0;
counterfactual probes=0. Proposed gate exposure remains unmeasured; no model was instantiated.**
Prior P75 learner displacement is retained as historical exposure only. There is no new
scientific root, RNG state, checkpoint or live process. Owner prediction: **not taken**.

## 6. Decisions this intake produces and delivery boundary

**Object tier, preparation only.** Options: (a) finish this concrete ready question and publish
its exact TASK/HANDOFF for Root; (b) return no-ready solely because value is not measured;
(c) locally open the family or run a diagnostic/learner. Recommend **(a)**. The missing
source/action/comparator mapping from P68 is now explicit; option (b) would impose a
performance prerequisite, and (c) exceeds P76. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** This selects preparation, not its proposed scientific arms.

**Direction tier, unformed.** Ask the original `em:acvc:convergence` node to choose between
(a) this bounded native B, with an explicit inherited return-unit interpretation, and
(b) retain the current boundary with no successor because the cue or expected native value
does not justify this family. Recommend (a) narrowly; this is a close call because local
eligibility is not global service and a competent fixed/generic control may contain all
useful behavior. A refusal on either concrete scientific ground is substantive; refusal only
for lacking exact upper/tuning/confirmation would be a class mismatch. No local override,
new disposition, recast count or Portfolio action follows from this recommendation.

At the clean boundary, both worktree and main `item.py reviews --json` returned `[]`.
The already-applied owner review `owner/reviews/2026-09-05.md:19–23` continues to control
lowest sequencing. P2 item `owner/inbox/2026-09-09/20260909-acvc-001.json` records only this recommendation/preparation; it
does not fabricate a formed Pro decision or owner approval. Audit anchor:
`acvc-native-link-loss-p76-ready-question-20260909` in the September 9 audit ledger.

Publish with the Prompt Author default GitHub mode on this same direction branch. Root is
receipt parent and the configured independent Transport is executor; **this DM does not
dispatch or Send**. The current registry contains only ACVC's retired pre-cutover provider
conversation. Preserve the decision binding and old archive; leave the requested provider ID
unset so Transport applies the recorded owner cutover to a verified 6 Pro context. No retired
ID is prebound and no accepted request is regenerated.

Strongest support: an actual native observation distinction now leads to a legal corrective
action, with a trained base and explicit containing generic control. Strongest contradiction:
the cue does not establish loss of global service, structured predecessors lost, and fixed
handling may suffice. Claim ceiling: source/readiness and a proposed single-instance B only,
not positive performance, mechanism isolation, stable superiority or family reopening.
Next discriminator is the proposed real learned-versus-fixed/generic native comparison if
selected by Convergence and concretely assigned by Root. Until then everything is committed,
no scientific process is live, and Root can advance an independent direction.

Chinese brief: `docs/research/portfolio/owner/briefs/acvc/2026-09-09_native_link_loss_p76.md`.
