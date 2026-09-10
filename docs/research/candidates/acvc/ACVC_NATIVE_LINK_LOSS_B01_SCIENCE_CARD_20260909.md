Claim: On the existing five-UAV host and a fixed trained DENSE proposer, a private learned link-loss gate may improve native return over always-apply and cue-triggered retrace, with any structured-package advantage assessed against a containing generic gate.
Binding MARL structure: (d) other-agent non-stationarity or partial observability.

# ACVC-NATIVE-LINK-LOSS-B01 — P78

## 1. Question, authority and ceiling

B/EXPLORE; one matched new training instance, master **8901**. On this host and fixed base,
does learning when to retrace improve native return over both fixed rules, and does the
structured gate improve over its containing generic gate? This is a finite-budget performance
observation, not stable superiority, an optimal fixed-policy bound, a headroom certificate,
mechanism isolation, transfer, safety or formal UAV-validation entry.

Direction authority is the complete immutable Convergence response at
`2d914ab8b6238b2eb76bb07b90972945a23f7a68`,
`pro_packets/20260909_native_link_loss_convergence/archive/RESPONSE.md`, sections
“Controls, containment”, “Minimal question” and “Work proportional”. Accepted intake:
`ACVC_NATIVE_LINK_LOSS_P76_CONVERGENCE_INTAKE_20260909.md` §§2–7 at `3268864f`.
Root's P78 assignment now allocates this card, one CM implementation/independent semantic
review/focused acceptance, **one** exact-source remote comparison and full scientific intake.
There is no retry, resume, cost pilot, second instance, extra checkpoint panel, tuning or Pro Send.
R02/R03 old-host conclusions, recasts 2, ACTIVE/MEDIUM and lowest sequencing remain unchanged.

Starting checkout: `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`.
Current main inputs were merged at `6048ce191b550fb7dbdcda248f898344ac8433a4`, from clean
`3268864f`; the merge preserved every audit row and the accepted P76 brief. Root owns main.
Machine-generated configuration, master, stream ranges, parameter arithmetic, work factors
and exposure statement are in `ACVC_NATIVE_LINK_LOSS_B01_P78_PROSPECTIVE_FACTS_20260909.json`.

## 2. Native host, available information and action path

Reuse `ucope/uav_motion_prefix_b01/environment.py:make_real`: five fixed UAVs, 50 static
uniform users, 1000 m square, altitude 50–150 m, 256 one-second primitive steps, max speed
30 m/s, 20 user rows, existing vectorized free-space channel and unchanged native reward.
All arms receive their own 104-dimensional observation, own previous **sent** command (3),
and a zero remaining-commitment coordinate (1), giving raw private input x of width 108.
No global user ID, service assignment, full SINR, current teammate command, privileged
local-index accessor or new actor reward channel is available. Critic information is learning-only.

Each UAV stores exactly one explicit anchor for one transition: the lowest normalized-SINR
nonpadding user in its preceding observation, reconstructed as own normalized XY plus the
row's relative XY. Lowest-value ties use the first observed minimum; a row slot is never an
identity. Nonpadding is identified by positive encoded SINR (eligible SINR is at least 3 dB,
so the encoded value is at least 0.26), not by nonzero relative position.

Match coordinates in float64 arithmetic over the observed FP32 bytes. The fixed normalized
L-infinity match tolerance is **1e-6** (1 mm on this host). A preceding anchor is ambiguous
if another preceding visible coordinate is within 2e-6. At the current observation, a single
match within 1e-6 means present; a nearest coordinate in (1e-6, 2e-6], or multiple candidates
within 2e-6, is ambiguous and skipped. Absence requires no current coordinate within 2e-6.
These conservative ambiguity exclusions do not query identities or prove an exact census.

The loss cue requires a valid preceding anchor, an unambiguous absence, and current visible
count **1–19**. Empty, saturated, ambiguous and reset cases have no opportunity. A preceding
saturated list may supply its one observed anchor; the current list must be unsaturated.
At each step select the next anchor only from that current observation; never retain an older
lost anchor. Episode reset clears anchors, previous positions, sent commands and recurrent states.

Every arm samples the frozen base proposal b at every primitive step. An opportunity additionally
requires `dot(b_xy, p_current_xy - anchor_xy) > 0`. The alternative command is
`c = clip((p_previous - p_current) / 30, -1, 1)`, using the acting UAV's realized observed 3D
displacement, not its previous proposed command. FP32 reconstruction makes retrace approximate.
It restores neither teammates' positions nor their prior interference or assignment.

The causal chain is simultaneous motion → private loss of a correctly bound observed link →
own apply/retrace choice → new joint geometry and assignment → unchanged native team reward.
Loss of own-link eligibility is not proof of a global service loss; a teammate may have taken over.
Membership is fixed, with private state per UAV and shared parameters; no join/leave/rejoin,
replacement, censoring or semi-Markov effect is claimed. All credit uses primitive time, gamma 1.

## 3. Fixed base, treatment, containing control and learner

All four arms use the complete frozen DENSE/8201 final actor from
`C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/mgtap_b01_8201_4f65eefb1b15e44b42d694376630fba0c230cc6c/final_DENSE.pt`,
SHA256 `f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
Reuse the read-only `NativeGeometryActor` definition. Stage this input at its declared digest;
do not train, retune or reselect it. The selection was made with both old outcomes known, and
8201 had the better original DENSE mean (0.1922357063 J versus 0.1687618179 for 8202).
Its old above-hover result and displacement establish a trained asset, not competence on every
new trajectory or an independent baseline sample.

- **C:** always send b. No gate training or anchor matching is needed.
- **F:** send c on every opportunity, otherwise b. Its gate is deterministic; b remains sampled.
- **T:** train a private recurrent Bernoulli gate selecting c=1 or b=0 only on opportunities.
- **G:** retain T's entire trainable path and add the unconstrained dense recurrent residual
  defined below. It has all T information and more capacity, with the same training exposure.

All five UAVs share an arm's gate weights but keep private hidden states. Each arm evolves its
own frozen base recurrence on its own actual trajectory; next-step base input receives the
command actually sent. No hidden state or rollout is borrowed from another arm. Base parameters
are frozen and absent from the optimizer. Store each sampled b (and its pre-tanh sample) with
the rollout; optimizer likelihood evaluation never resamples it or substitutes another action.

The deterministic bound feature z has 13 entries, in order: preceding anchor-valid bit,
current count/20, loss-cue bit, current anchor-relative XY/1000 (2), preceding encoded SINR,
realized displacement/30 (3), retrace c (3), and away-dot using normalized XY (1).
Invalid anchor coordinates/SINR and away-dot are zero; reset displacement/retrace are zero.
The available current proposal b is a separate three-vector. Both learned arms get x, b and z.

T: `tanh(Linear(108,32)) → GRU(32,32)` on x; concatenate the current hidden output, b and z
(48 values), then `Linear(48,32) → tanh → Linear(32,1)` for the Bernoulli logit. G copies
that entire T path and adds a private residual: `tanh(Linear(108,32)) → GRU(32,32)` on the
same raw x; concatenate residual hidden output, raw x, b and z (156 values), then
`Linear(156,32) → tanh → Linear(32,1)`. Add the residual logit to the copied T-path logit.
Each final scalar projection starts with zero weights/bias; other layers use PyTorch defaults
under the recorded private initialization stream. Shared T-path and critic initial values match
across T/G; all states begin at zero. Setting G's residual output to zero recovers the entire T
class. C/F are available limiting constant gate policies, not exactly finite sigmoid endpoints.

Use the existing independent centralized `Critic` (136→128→128→1, tanh), with fresh matching
initial values for T/G. Inputs are existing predecision `critic_features(state,last,remaining=0)`.
Reuse native undiscounted return-to-go with no terminal bootstrap. No value normalization or
reward shaping is added. Two complete episodes form each rollout; 256 rollouts/arm; four full
rollout Adam updates each. Recurrent optimization chunks have length 32, starting from recorded
detached collection states. Store the raw inputs, z, proposals, choices, opportunity masks and
old log probabilities needed to evaluate that same collected decision.

PPO uses per-agent Bernoulli log-probability ratios on genuine opportunities, clip [0.8,1.2],
the team return-minus-recorded-value advantage normalized over all primitive rollout rows,
and the same all-primitive-row denominator as `clipped_policy_loss(..., velocity_mask=mask)`.
Sum eligible agent terms per row; mask every ineligible gate term, including entropy. The frozen
base factor cancels from the gate ratio. Loss is policy + 0.5 mean squared value error − 0.01
gate entropy; gradient norm clip 0.5. Adam lr=3e-4, betas=(0.9,0.999), eps=1e-8,
weight_decay=0, amsgrad/foreach/fused=False. Reuse accepted helpers where their meanings match.
Sparse opportunities do not change the denominator or add an exposure prerequisite.

## 4. Primary, units, result reading and predictions

Native `S = sum_t r_team[t]`; `J = S/256`, unchanged. The inherited quarter-unit condition
is **0.25 S = 0.0009765625 J**. The separate absolute **MEI is 0.01 J = 2.56 S**: about one
percentage point of the bounded native team score is a useful preliminary investment scale.
No tuned same-information upper-minus-baseline headroom record exists on this host. Old DENSE
and hover evidence is reused as context; current C/F use the exact base but gate-induced actions
and new gate training do not match a tuned reusable baseline package.

Final-only evaluation: the same 32 fresh joint reset identities for T/G/C/F, each with separate
declared action streams. Publish all episode S/J and primary paired **T−C** and **T−F** means
separately, plus `min(mean(T−C), mean(T−F)) = mean(T) − max(mean(C),mean(F))` as the transparent
summary. This is not an episode-wise oracle. Publish mandatory T−G, G−C, G−F and all arm means.
Each fixed contrast gets sample-SD/√32 conditional SE from the 32 paired episode differences;
do not attach a naive selected-max SE to the summary. Joint episodes are the units, not UAVs,
time steps or independently trained policies. One training instance cannot estimate training-seed
population uncertainty.
Retain all 1,024 training-episode S/J outcomes and rollout update/exposure records as well as the
128 final evaluation outcomes. Final checkpoints are T and G only; no checkpoint selection follows.

Reading rule (apply separately to each declared contrast, keeping the actual signed number):
**UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**. Separately report
whether each primary exceeds 0.25 S. Both primary UPs support a meaningful preliminary learned
correction signal; any favorable T−G adds only finite-budget structured-package evidence. A T−G
gain cannot rescue a T loss to C or F. If G contains the gain, recommend describing a learned
correction package. Positive sub-MEI results remain positive; WITHIN is not equivalence. Opposite
native signs remain adverse even if link or gate statistics improve. Full outcomes and uncertainty
inform the next unallocated recommendation; no branch automatically launches another instance.

Prospective DM predictions, recorded before implementation or output: T−C **+0.002 J**, T−F
**+0.004 J**, T−G **−0.001 J**; thus a small positive primary summary, inside MEI. Subjective
probabilities: both primary means positive 0.55; both above MEI 0.20; T−G above MEI 0.15.
Confidence is low because opportunity frequency, handoff cost and gate optimization are unknown.
Score signed/point predictions on the retained panel; these probabilities are not estimated data.
Owner prediction: **not taken (unattended)** unless an actual prediction reply arrives.

How the result will be interpreted: above-MEI gains over both fixed rules would motivate one
new independent training instance; inside-MEI effects would favor a narrower follow-up only if
the all-arm pattern and actual gate exposure justify it; native losses would argue against the
unchanged structured package. All are recommendations after intake, without successor allocation.

## 5. Exposure, dominant work and complete budget

Exactly two learned fits ×512×256 steps plus four final panels ×32×256 steps = **294,912 team
steps**, 2,048 Adam calls, 512 two-episode rollouts, 1,152 explicit scored resets and 128 final
evaluation episodes. Four environment constructors have their own unscored initialization resets;
report them separately. No old learner is replayed. Train and final evaluation are the only native
interactions. The facts file freezes master 8901 and disjoint initialization/environment/action
stream laws; T/G match common initialization and training reset identities, with private action RNGs.

Collection/evaluation has 1,474,560 base agent forwards and at most 1,392,640 learned-gate agent
forwards. Current-anchor matching across T/G/F is at most 28,672,000 coordinate pairs. Conservatively
checking the newly selected anchor against other current visible rows for ambiguity adds at most
another 28,672,000 pairs: **57,344,000 total pair comparisons**, a clarified intrinsic bookkeeping
factor rather than an added experimental panel. Optimizer recurrent replay, backward passes,
critic work and G's extra path are additional real work; these forward counts are not total FLOPs.
There is no nested policy/trajectory search, global identity table or support census.

Machine exposure statement: each arm has 1,024 possible nonzero gate/critic Adam updates at 3e-4;
the facts file computes the scalar same-sign displacement example without running a learner.
It is a capacity-to-move illustration, not actual gradients or a guarantee of opportunities.
Record actual opportunities, apply/retrace choices, distinguishable proposed/retrace commands,
gate-specific initial norm/displacement and critic displacement. A zero-initial projection has
absolute displacement, not an invented relative norm. Critic movement cannot substitute for gate
learning; independently trustworthy returns may remain reportable if gate exposure is sparse.

One scientific process; T then G fits/evaluates, then C and F final evaluations; no parallel arms.
Torch CPU FP32, one intra-op/inter-op thread; native NumPy geometry remains as implemented.
Primary route is configured `wsl_4070`, exact committed source and detached `agent-task`, with
fresh actual-node admission joined to the runner by `&&`. No device/precision migration or local
fallback is allocated. Host-specific superiority and cross-platform bit equality are non-goals.

Complete learned-arm cap **1,800 s**; complete logical study cap **3,600 s**, including required
focused checks, imports/initialization, training, final T/G/C/F evaluation, output publication and
actual process exit. Record shared/startup/trailing work honestly; it is not free or hidden in a
preceding A. Required focused checks have an additional **300 s aggregate** cap. Use existing
deadline/OS facilities; no restart machinery. Historical P75 353.71/368.12 s are reference costs,
not a new runtime forecast. Unknown unit cost remains unknown; no calibration invocation is added.
For accounting, charge required check wall, shared startup, C/F evaluation and trailing publication/
exit to the whole study and conservatively to each learned arm; add that arm's own initialization,
fit, final evaluation and checkpoint publication. Do not charge the other learned fit to an arm.
Study bill is focused-check wall plus complete scientific-process wall; record actual elapsed
process wall separately from that logical bill and from human authoring/wait time.

## 6. Engineering ownership, acceptance and stop

Engineering-scope §4: **none needed**. Scientific exposure/counts and loading the fixed input
do not add resource telemetry or recovery orchestration. New non-test source ≤2,000 lines; single
runner ≤600; orchestration share is a review signal. CM owns implementation and the full technical
batch in `experiments/candidates/acvc/native_link_loss_b01/`, matching tests,
`scripts/run_acvc_native_link_loss_b01.py`, a simple committed launch command if needed, and this
object's technical evidence. Runtime artifacts stay under
`temp/directions/acvc/exp/native_link_loss_b01_8901_p78_20260909/` on the executing checkout.
Native env, shared UCOPE/MGTAP modules and fixed DENSE checkpoint are read-only dependencies.
DM owns this card, prospective facts, owner record, scientific intake/brief/audit. Serialize the
shared index and any overlapping evidence edits; preserve unrelated work.

Independent semantic review is required for information/identity, actual-command recurrence,
gate-only credit and stored proposal, RNG separation, G containment/common initialization and
the primary/paired unit calculation. One focused synthetic changed-path suite covers those risks,
including zero-relative-position nonpadding, empty/saturated/ambiguous/reset skips, actual versus
commanded displacement, gate mask/gradients, and primary rule boundaries. Tests must not create
native UAV episodes or a cost pilot. Reuse trustworthy unchanged checks; corrections address a
concrete gap. Keep synthetic outputs distinct from the scientific run and clean only owned scratch.

Commit and push exact inputs before checks requiring remote source or scientific launch. CM is
the sole observer through terminal collection and technical acceptance; notify DM/Root of an
accepted handle without asking them to poll. Fresh admission precedes scientific roots, RNG,
models and optimizers. On uncertain supervisor acceptance reconcile that handle; never duplicate.
At failure/cap/dependency conflict retain actual logs, partial outputs and counts, stop the sole
allocation, and return its concrete dependent limitation. A failure is not scientific polarity.
Focused code repair before a scientific acceptance may continue within this engineering budget;
a new scientific attempt is unallocated. DM then takes every outcome in and returns to Root.

## 7. Decisions this card produces

Object-tier options: (a) freeze the above small heads, private streams, comparisons and single
allocated batch; (b) add tuning, a preliminary measurement or an extra instance; (c) defer the
conforming allocation for another planning vote. Recommend and execute **(a)**, implementing the
proper node's selected question within Root's P78 cap.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Execution allocation is
Root's explicit P78 instruction, not an invented owner reply. Record the P2 new-card item and audit
row with an empty owner column. Clean-boundary owner reviews were empty before freeze; apply any
later relevant instruction at the next clean boundary. No DIRECTION performance update occurs
until scientific intake, and no B consumption state is created.
P2 new-card item: `docs/research/portfolio/owner/inbox/2026-09-09/20260909-acvc-003.json`.
