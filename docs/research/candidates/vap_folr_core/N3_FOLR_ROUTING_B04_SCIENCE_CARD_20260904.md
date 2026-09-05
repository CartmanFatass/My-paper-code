Claim: On FOLR B3's replacement host, retaining the continuing owner's state while dropping departed-partner state may improve finite-budget native-return learning relative to a containing generic updater.
Binding MARL structure: (a) agent-count scaling or roster change; (d) other-agent non-stationarity or partial observability.

# N3 FOLR routing B04 — one state intervention

Date: 2026-09-04. Class: **B / EXPLORE**. Object: `N3-FOLR-ROUTING-B04`.
DM: `/root/dm_amx_n3_state_recovery`.
Science checkout: `C:/Projects/HMASD-worktrees/dm-n3-state-recovery-20260904`,
branch `codex/dm-n3-state-recovery-20260904`, starting commit
`36282159be22cf4a94aa59484de1e4df36343b9d`.

## 1. Question, authority, and claim ceiling

At a real q0-to-q1 replacement, does the typed event mask help an ordinary reward-trained
receiver learn to act on continuing-owner and new-partner information within a fixed budget?
The receiver is the continuing `owner_t@0` four-action policy, whose native reward is one
exactly when its action decodes `(s,n_new)`. The intervention is the event-state input mask,
not Adam history, source-controller handover, or the physical replacement rule.

The owner-adopted N3 agenda explicitly admits a small B object now:
`../../portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md` and
`../../../external-review/2026-09-04-two-line-consolidation-6pro/OWNER_FOLLOWUP_02_RESPONSE.md`
section N3. This is an object-tier continuation of the accepted FOLR typed/generic/reset
mechanism, not a recast or reopening of any stopped C family. B has no consumption state.

The ceiling is a preliminary three-seed, host-local learning-curve difference at the named
budget. It cannot establish representation necessity, generic incapacity, stable superiority,
general population scaling, long-horizon recovery, transfer, UAV value, or deployment safety.
There is no promotion or lifecycle decision in this card.

## 2. Source provenance and concrete reuse

Receiving object: B04. Reused asset: the unchanged callable B3 physical host and actor/writer
classes in `experiments/candidates/folr_core/partner_writer_stale_load_routing_host.py` and
`partner_writer_stale_load_routing.py`. This avoids rebuilding membership semantics or another
N3 host. The new comparison extends ordinary writer and receiver exposure and observes full
curves; it does not invoke the historical manifest/train/evaluate/validator orchestrator.

- FOLR's `DIRECTION.md`, B3 code-science index and current-host census A01 record upper return
  one, Phase R absent, and no tuned current-host generic baseline. The old Phase-P accuracy
  `0.94482421875` is near but below its historical gate. That result is preserved unchanged.
- FOLR B1's different two-transition host recorded KEEP about `0.852`, RESET `0.5`, and a
  simple latch about `0.970`. This is a contrary-control motivation, never B3 headroom.
- RCLE's `DIRECTION.md` retains finite-budget recovery after exact information-necessity
  claims closed. Its containing-null lesson motivates keeping GENERIC distinct from RESET;
  no RCLE result is pooled with B04 and no stopped RCLE family is reopened.
- DISH's first-trigger B01 remains without a scientific result; its C03 technical refusal
  and unaccepted implementation are not reused or interpreted here.
- VSP-02's current-host census records terminal greedy equality on a static roster and
  no membership-bound optimizer intervention. Adam carry/reset is absent from B04.

No compatible tuned host baseline package was identified. B1/B2 differ in host, observation,
action or information support. B04 will record a fixed-configuration generic result, not
mislabel it as a tuned headroom census.

## 3. Environment-to-consequence trace

1. The owner privately sees survivor bit `s`; q0 supplies obsolete bit `n_old`. Learned
   encoders form two owner channels and two obsolete-partner channels.
2. The existing host executes three primitive transitions and a real
   `TERMINAL_LEAVE(q0@0) + JOIN(q1@0)` transaction. Owner identity and epoch survive;
   q0's record terminates and clears, and q1 has a distinct entity identity.
3. q1's frozen ordinary reward-trained writer sees `n_new` and supplies its four-channel
   payload. The receiver gets that payload, never the target label as a policy input.
4. The mask selects old channel inputs to the common eight-input/four-hidden updater;
   its four-action readout produces the action whose native reward tests `(s,n_new)`.
5. REINFORCE from sampled external reward updates the owner encoder, obsolete encoder,
   event updater and action head. The q1 writer stays fixed during receiver training.

Every training and evaluation episode uses the real host's three transitions, transaction,
write, terminal action and reward. Public nuisance observations do not carry target bits.
The learner may use targets only through the host reward, never a direct-label loss.
Legal initial private cues remain available through the pre-event state path.

This fixed roster-size replacement has no survivor deletion, slot reuse, rejoin, censoring,
variable opportunity duration or semi-Markov discount choice. All episodes terminate at
three primitive transitions; native reward is terminal and undiscounted. Partner co-adaptation
is deliberately absent after the one writer-training stage. It cannot price recovery time
beyond the first post-replacement action.

## 4. Arms and strongest live nulls

All learned routing arms reuse `MatchedRoutedActor`, identical trainable names/shapes,
Xavier initialization, frozen writer state, Adam settings, data support and action-uniform tapes:

- **TYPED:** keep owner channels, zero obsolete-partner channels.
- **GENERIC:** retain both channel families. The existing containing class can represent
  the typed mapping by zeroing the obsolete-input columns. This is the strongest existing
  B3 trainable same-information comparator; achieved competence is measured, not assumed.
- **RESET:** zero both pre-event families. This is an **information-cut control**, not
  the same-information efficiency comparator. Its loss of `s` bounds reward at one half
  on balanced support; finite evaluation fluctuations do not become leak verdicts.

An evaluation-only **LATCH** control stores the legal initial `s` bit in owner state and
uses the same frozen q1 writer's own learned binary readout on its payload to choose
`2*s + sampled_new_bit`. It never receives a target at action time. Execute it on the
same B3 host and final evaluation support, encoding the retained bit into the host's two
owner-state channels. It uses a fixed simple controller, zero extra training and the
already-paid writer exposure; report these unequal optimization costs explicitly.
Its return is a competent simple same-information alternative to learning a routing readout,
not a fourth matched training arm. It bounds a claim that typed routing is necessary.

Live explanations: typed masking helps ignore stale inputs; generic optimization is already
adequate; both are limited by receiver readout learning or the writer; a simple legal latch
absorbs the apparent value. Writer accuracy and latch return are observed diagnostics, never
launch or routing-stage gates. No certified containment or oracle-retuning prerequisite applies.

## 5. Fixed budget, RNG, evaluation, and measurements

- Seeds: `96041, 96042, 96043`. One full invocation with all three seeds; no seed selection.
- CPU float32 PyTorch, Adam `lr=0.025`, betas `(0.9,0.999)`, eps `1e-8`, zero weight decay.
  Use ordinary REINFORCE `-mean(reward * log sampled_action_probability)` without entropy,
  critic, direct labels, auxiliary loss or a cached action. No optimizer reset intervention.
- Writer: 128 updates, 64 balanced binary episodes each; identical final writer copied into
  every learned routing arm for its seed. This outcome-informed B adaptation extends the
  historical 32-update writer budget and runs routing unconditionally afterward.
- Each routing arm: 128 updates of 64 episodes (32 CLEAN balanced over `(s,n_new)` and 32
  STALE_LOAD balanced over `(s,n_old,n_new)`). Fresh balanced tuples are shuffled per batch.
- Evaluate at updates `0,16,32,48,64,80,96,112,128`: 256 writer episodes per point; 256 per
  regime per routing arm per point. LATCH has one final 256-episode evaluation per regime.
- Train/evaluation streams are separate; data, initialization and sampled-action streams
  use explicit seed namespaces. Within a seed, routing arms share tuple order, initialization,
  and action uniforms (common random numbers). Evaluation tapes are fixed across curve points,
  separate from training, and shared across routing arms. No checkpoint/model selection.
  This new paired RNG law is a declared change from historical cross-arm disjoint B3 tapes.
- Final checkpoints only, using the learner's existing `torch.save` state facility; no resume
  path. Curves are evaluated in memory. Preserve model state and optimizer state at final.

Expected full counts: writer training `24,576` episodes / `384` updates; routing training
`73,728` episodes / `1,152` updates; total training `98,304` episodes / `1,536` updates.
Writer evaluation `6,912`; learned routing evaluation `41,472`; LATCH evaluation `1,536`.
Total `49,920` evaluated episodes, `148,224` complete episodes and `444,672` real primitive
transitions. Report actual policy calls by phase and role rather than call each WAIT a
learned decision. Report per-seed/arm counts and no unsupported pooled success statistic.

One summary contains the full sampled-return curves and expected rewarded-action probability
curves, seed-level final return and normalized trapezoid AUC (divide by 128), owner/new-bit
component accuracies, and mean action-kernel total variation under a final `n_old` flip.
Counterfactual kernel forwards are diagnostic, are counted separately, and create no extra
environment transition or learner update. Report writer curves, LATCH return, per-phase wall
time, peak RSS when available, parameter displacement, seed summaries and result rule.
Final evaluation rows retain regime, legal cues, action probabilities, sampled action and
host reward in a plain file so these summaries are inspectable. Training curves retain each
update's reward and loss. No byte-level kernel evidence or validation schema is needed.

## 6. MEI, estimand and reading rule

Primary per-seed quantity is STALE_LOAD sampled-native-return normalized AUC difference
`d_s = AUC_TYPED_s - AUC_GENERIC_s`; primary aggregate `d = mean(d_s)`.
MEI: absolute `0.05` normalized return-AUC units. Five percentage points across the training
budget is large enough to motivate a further tiny-host run and avoids a relative threshold
near early-learning chance. Report CLEAN AUC, final gaps and every individual seed alongside it.
Three seeds supply preliminary direction and heterogeneity, not a confidence claim.

For a complete valid result, apply the first matching branch verbatim:

1. `B04_TYPED_SIGNAL`: `d >= 0.05` and at least two seed differences are positive.
2. `B04_GENERIC_SIGNAL`: `d <= -0.05` and at least two seed differences are negative.
3. `B04_WITHIN_MEI`: `abs(d) < 0.05`.
4. `B04_HETEROGENEOUS`: otherwise.

Attach independent descriptive flags: `writer_weak` if mean final writer sampled accuracy
is below `0.90`; `simple_control_headroom` if mean final LATCH return exceeds the better
learned arm by at least `0.05` on STALE_LOAD; and the observed generic final return. These
flags never erase the routing contrast or classify a technical failure from error text.

How the result will be interpreted: an above-MEI typed signal suggests a finite-budget
optimization benefit at the mask, worth a further within-mechanism B discriminator. A gap
inside the MEI suggests little measured mask value at this exposure; competent generic
returns would strengthen that reading, while a strong latch and weak learners would keep
receiver learnability live. Opposite sign favors the generic package on this host. Mixed
seed signs leave an unstable signal. None closes N3, FOLR or an untested state-source family.
The next B rung must be named in intake; any different family is returned at direction tier.

DM prediction on record: `B04_WITHIN_MEI` is most likely, with GENERIC improving and the
simple LATCH reaching a high final return; a slower learned readout may leave more headroom
than typed masking removes. Strong contrary possibility: stale nuisance causes an early
typed AUC advantage even when final returns converge. Owner slot: **not taken (unattended)**.

## 7. Exposure line and machine-time bound

Machine-generated before any result invocation with Python arithmetic on the stated optimizer
and Xavier dimensions:

```text
updates_per_learner=128; Adam_lr=0.025; nominal_coordinate_path=3.2
writer_min_nonzero_Xavier_RMS=sqrt(2/6)=0.5773502691896257; nominal_ratio=5.542562584220408
router_min_nonzero_Xavier_RMS=sqrt(2/12)=0.408248290463863; nominal_ratio=7.8383671769061705
```

This is a nominal Adam learning-rate path relative to initialization scale, not a rigorous
realized displacement bound or evidence of useful learning. The summary also computes actual
`||theta_final-theta_initial||_2 / ||theta_initial||_2`, norms and update count in float64
for the writer and each routing learner. Biases start at zero; do not divide each bias by zero.

No hyperparameter or arm-selection sweep is planned. Conservatively treat each learned arm
as a cost arm: the runner reports its own train/evaluation wall per episode from its single
toy end-to-end check and projects the full three-seed writer and each routing arm using
`T_phase = train_episodes * seconds_per_train_episode + eval_episodes * seconds_per_eval_episode`.
Apply a **600-second cap per projected three-seed phase/arm**, charging the full shared writer
projection to each routing arm; total full invocation cap **2,400 seconds**. CM records the
machine-generated coefficients and projections in the engineering return before launch.
An arm over cap is not launched; return the measured projection for an object-tier smaller
budget choice. The existing supervisor may apply the whole-invocation wall cap; no new
scheduler, recovery, retry or kill/restart machinery is authorized.

## 8. Placement, scope and technical success

CPU float32 is fixed, host OS is portable between the configured local Windows and remote
Linux nodes; cross-node bit equality is not part of the estimand. Remote-first execution uses
`wsl_4070`, exact committed/pushed source, the configured interpreter and detached `agent-task`.
No CUDA conversion. Local fallback is allowed only before a remote process is accepted and
after a fresh local admission. Each full or technical learner invocation is preceded immediately
by its own node's `admit-memory` receipt (physical and effective available memory >=4 GiB).
Portable long tests use committed remote bytes. Ordinary short editing checks stay local.

New code owns only `experiments/candidates/vap_folr_core/n3_routing_b04/`, its mirrored tests,
and `scripts/run_folr_n3_routing_b04.py`. The B3 host/model source is read-only reuse. No core,
control-plane, AGENTS, Portfolio, RESEARCH_MAP, organization or other-direction edits.
Runtime output: `temp/directions/vap_folr_core/exp/n3_routing_b04_<attempt>/`.
No engineering-scope §4 machinery is added. Existing host DTO and digest computations remain
an inherited implementation detail; do not copy them into a new guard or validation layer.
Use one smoke reaching final publication and rule tests, within §5 size/time budgets.

Technical success establishes conformance, nonzero real activity, readable curves/summary and
resource/cost facts, not mechanism value. Missing resource telemetry is `resources_unmeasured`;
missing learner measurements quarantine the attempt. Reproduce a failing step over recorded
bytes before classifying it. Post-learner defects require an offline publication check on
existing evidence before a fresh attempt. No B calibration, theorem or Pro gate is introduced.

## 9. Object-tier selection

Options: (a) the fixed B04 host/mask continuation above; (b) repeat the already complete B3
read-only census; (c) build a joint N3 state-source/optimizer platform. Recommend and select (a):
it obtains the missing generic comparison on a real replacement host with one intervention,
while retaining the simpler latch and the information-cut control.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a). Provenance `OWNER_DELEGATED`.
Kind `selection`; owner flag `none`; reversible. The owner-item CLI writes decision, new-card
and first-ladder prediction items. Root receives the shared audit rows for integration.
