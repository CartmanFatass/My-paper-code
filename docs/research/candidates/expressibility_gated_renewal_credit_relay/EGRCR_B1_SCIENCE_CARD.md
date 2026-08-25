# Expressibility-Gated Renewal Credit Relay B1 science card

Owner: `direction:expressibility_gated_renewal_credit_relay` Explorer Manager  
Candidate: `CAND-EXPRESSIBILITY-GATED-RENEWAL-CREDIT-RELAY`  
Treatment: `EGRCR-B1-ORDERED-JOINER-WAITER-CREDIT-v1`

## Conclusion and classification

EGRCR is scientifically viable as a new, nonredundant **answer-changing
enabling experiment**. It is not yet a direct variable-`k` algorithm candidate.
The smallest useful experiment asks whether a waiter-specific counterfactual
effect, bound to the correct later joiner record, causes a better one-step
renewal-policy update than both ordinary GAE and an equal-marginal binding cut.
It does not ask whether an end-to-end policy already beats fixed `k`.

The experiment requires a new renewal host with a prospectively positive and
usefully varying same-information joint-execution surplus. The earlier waiter's
renewal must advance a compatible weak partner in the positive cell, and must
be neutral or harmful in a matched false-pair cell. Merely delaying an earlier
strong request so that two renewals occupy one tick is not an adequate target.

The frozen direction semantics are:

- the later joiner request is the source action;
- the older true waiter's changed immediate renewal, deployed action, and
  bounded utility are the target effect;
- the resulting waiter-effect label `kappa` is attached only to the **later
  joiner's stored request record**;
- the older waiter's ordinary GAE is untouched; and
- there is no zero-sum debit, no reverse relay, and no transfer of `kappa` onto
  the waiter record.

This explicitly rejects the alternative proposal to credit or debit the older
waiter record. It would test a different temporal-credit mechanism than the one
assigned here.

## Provenance boundary

The following sources supplied prospective primitives or warnings only:

- `event_triggered_budgeted_cooperative_renewal/EBCR_VARIABLE_K_SCIENCE_CARD.md`:
  a shared-policy variable-`k` setting, bounded pending requests, and ordinary
  joint GAE;
- `recct_lite/RECCT_SOURCE_TARGET_ASSOCIATION_CUT_EM_INTAKE.md`: an association
  cut is uninterpretable until the target update and target consequence are
  expressive; and
- `optimizer_entropy_exposure_boundary_relay/OEER_B1_SCIENTIFIC_INTAKE.md`:
  treatment branches must not differ in inherited optimizer history.

No source observation, threshold, acceptance, or authority is imported. EGRCR
uses a new host, local criteria, disjoint roots, and its own claim ceiling.

## Scientific question

In a two-agent bounded renewal window with a true compatible-pair cell and a
matched false-pair cell, does replacing the later joiner's already-tagged joint
reward component with the correctly associated waiter-interaction target cause
the shared renewal policy to allocate join requests more selectively and earn
more bounded task utility than:

1. ordinary full-reward GAE; and
2. the identical waiter-effect labels assigned to wrong, matched joiner
   records?

The association interpretation is available only if all three causal links are
observed independently:

`later request -> true waiter executes/changes action`,
`waiter change -> bounded utility`, and
`matched waiter target on the later record -> held-out later-request
probability -> actual renewal exposure`.

## New microhost: versioned cooperative handoff

Each opportunity is a replayable ten-tick two-agent block with ordered roles
`W` (older waiter) and `J` (later joiner). Roles alternate across blocks while
one linear Bernoulli actor is parameter-shared. The block is independent of
other blocks; all exogenous coordinates are paired across treatment arms and
counterfactual forks.

- Initial deployed option generations are `(g_W,g_J)=(0,0)`.
- At physical tick `t_w=2`, `W` samples an ordinary request. A sampled request
  stores a prepared generation-1 option and remains live through tick
  `e_w=t_w+4=6`.
- The later opportunity is `t_j=t_w+L`, with lag `L` balanced over `{1,2}`.
  Both agents are ready at `t_j`. A newly sampled request from `J` is legal and
  is the only event that can close this older window on that tick.
- The block type `S` is balanced between `JOINT` and `SOLO`. At `t_j`, the
  required generations become `(1,1)` for `JOINT` and `(0,1)` for `SOLO`.
  The requirement remains fixed through the outcome boundary. Thus advancing
  the waiter's prepared generation is useful in `JOINT` and a false-pair action
  in `SOLO`.
- `J` observes a local sign cue whose intended accuracy is approximately
  `0.90`, realized by a prospective finite schedule rather than an independent
  Bernoulli draw. Every 128-opportunity calibration or retained-confirmation
  root contains exactly 116 correct and 12 flipped joiner cues, hence realized
  accuracy `116/128=0.90625`; cue-flip state is never balanced 50/50. There are
  exactly 16 opportunities in each `(type,lag,ordered_role)` cell. Encode
  `b_S=1` for `JOINT` and zero for `SOLO`, `b_L=1` for lag two and zero for lag
  one, and `b_R=1` when physical agent 1 is `W`/agent 0 is `J` and zero for the
  reverse ordering. Within each registered root list, let `j` be the zero-based
  root ordinal and `q_r=j mod 2`. The four cells satisfying
  `b_S xor b_L xor b_R=q_r` have 14 correct and two flipped cues; the other four
  have 15 correct and one flipped. Within a cell, the one or two rows with the
  lowest predeclared `cue_flip` counter-key ranks are flipped. Thus each binary
  type, lag, and role level has exactly 58 correct and six flipped cues per root,
  and every joint cell has nine flips across the six calibration roots.
  Cue-flip positions and hazard-uniform positions use independent counter-key
  namespaces and rotate across roots. Each held-out 128-dyad panel applies the
  same `116/12` schedule separately to its 128 `JOINT` and 128 `SOLO`
  opportunities: each `(lag,ordered_role)` cell has 32 opportunities and the
  three lowest independent held-out cue-key ranks are flipped, leaving 29
  correct. The actor never observes `S`. `W` receives
  an independent fair sign cue, independent of type, lag, joiner-cue flip, and
  every suffix draw. The type, future requirement, counterfactual outcomes, and
  suffix identity are centralized training/evaluation facts only.
- If the joiner closes the window, both prepared options execute atomically at
  `t_j`. If an option is not executed at `t_j`, the joiner's identical prepared
  option executes locally at `t_j+1` and the waiter's identical prepared option
  executes on expiry at `e_w`. Prepared option contents are frozen at the
  pre-join snapshot in every fork; waiting never gains observations or changes
  the option.
- An execution occupies that role's task interface on its tick. On any tick
  with an execution, packet success is zero. Otherwise success is one exactly
  when deployed generations equal the required pair. Reward is
  `packet_success - 0.02 * number_executed`. The additive per-agent renewal cost
  is therefore identical after both prepared options have executed.
- The branch-independent outcome boundary is `B=e_w+2=8`. It contains the
  closure, both fallback deadlines, and two complete task-output opportunities
  after expiry. Report the number `X_e` of common non-forced waiter action
  opportunities between `t_j+1` and `B`; `X_e<2` is downstream non-exposure.
- Every block supplies two ordinary renewal tokens per agent, one actor call per
  agent per physical tick, and the same two request/readiness bits per agent per
  tick. There are no emergency or max-age events inside the causal window.

This host makes the same-information comparison explicit. Every fork uses the
same prepared options, observation history, readiness tape, physics, future
requirement, renewal tokens, per-agent costs, and boundary. Only immediate
execution membership changes. `JOINT` exposes positive complementarity from
advancing a compatible waiter; `SOLO` supplies an equally legal false-pair cell
in which advancing the waiter is not useful.

## Exact eligible causal edge and four-world target

An ordered pair `e=(W,t_w;J,t_j)` is eligible before the later action only when:

1. `W != J`, `t_w < t_j < e_w`, and the request sampled at `t_w` is still live;
2. exactly one older live waiter exists and no other request can close it;
3. `J` has a legal ordinary request with nondegenerate behavior propensity
   `0 < p_e < 1`, both roles are ready, and both have sufficient budget;
4. neither event is simultaneous, safety-forced, max-age-forced, expiring,
   budget-forced, or manufactured by the coordinator;
5. `do(A_J=1)` makes the true waiter execute at `t_j`, whereas
   `do(A_J=0)` leaves it pending beyond `t_j`; and
6. a deterministic pre-outcome rule assigns each request record and closure to
   at most one edge.

Same-tick requests, expiry-tick joins, ambiguous multiple closers, and any edge
whose no-request branch would execute the waiter at `t_j` are excluded.

From the identical pre-action snapshot, compute four legal forks `Y_e^{uv}`.
`u` indicates immediate execution of the joiner's prepared option and `v`
indicates immediate execution of the waiter's prepared option. Missing
executions occur at the fixed local deadlines above. `Y` is normalized reward
from `t_j` through `B`.

The natural coordinator maps `do(A_J=1)` to the `11` fork and
`do(A_J=0)` to the `00` fork. The `10` and `01` forks are centralized factorial
diagnostics used only to isolate the true waiter's interaction; neither creates
an execution-time action unavailable to the registered coordinator.

Define:

```text
self_e   = Y10 - Y00
waiter_e = Y11 - Y10
generic_waiter_e = Y01 - Y00
kappa_e  = (Y11 - Y10) - (Y01 - Y00)
```

`waiter_e` is the true waiter's marginal effect with the joiner held executed.
`kappa_e` subtracts the generic value of executing that waiter without the
joiner and is the only association-bearing relay label. It is intentionally an
ordered interaction, not a symmetric or Shapley allocation. The natural
coordinator effect `Y11-Y00` is reported but is never substituted for `kappa`.

## Independent expression and exposure gates

Calibration uses roots `[1009,1013,1019,1021,1031,1033]`, which never enter the
confirmatory update or evaluation. Each root supplies 128 scripted-ready-peer
opportunities, exactly 16 in each `(type,lag,ordered_role)` cell, with the
prospective 116-correct/12-flipped joiner-cue schedule above. The scripted peer
fixes only the presence and lag of the older request; it does not supply a
binding conclusion.

The following local gates are frozen before confirmatory roots:

1. **Source-to-target first stage.** In every structurally eligible
   opportunity, changing only the later request changes the true waiter's
   immediate execution from zero to one. At the first common post-event task
   opportunity `q_e`, its deployed generation/action must differ between
   `Y11` and `Y10`.
2. **Downstream target exposure.** Every opportunity has `X_e>=2` and a
   nonzero `waiter_e`. Across calibration roots, the mean `kappa` is at least
   `+0.10` in `JOINT` and at most `-0.10` in `SOLO`, with the corresponding
   paired 95% interval wholly on the declared side of zero. This is the local
   same-information surplus/false-pair check, not a transferred threshold.
3. **Joiner-record update expressibility.** On calibration-only cloned actors,
   the frozen action-conditioned relay advantage
   `c*(a_e-p_e)*tilde_kappa_e` applied to later-joiner records must change
   held-out joiner request selectivity between the two cue signs by at least
   `0.05` probability points with a paired 95% lower bound above zero. Under
   common hazard uniforms, the same update must change actual join choices in
   the predicted direction in at least `5%` of held-out opportunities.
4. **Cut support.** Every predeclared nuisance stratum contains balanced true
   waiter identities from both types, admits a fixed-point-free bijection, and
   the cut measurably changes the source-score/credit association. Unsupported
   singleton strata are reported and never self-mapped or relaxed after
   outcomes are seen.

Failure of any link stops before the confirmatory binding update and localizes
the missing link. Scripted-peer success alone is only consistent with an
expressive policy/output surface; it is not evidence about coadaptation,
ordinary GAE, or association-specific credit.

These are direction-level, disjoint-calibration gates. No confirmatory event is
selected, weighted, or discarded using its realized `kappa`, return, target
action, survival, or future readiness. An event-level outcome-derived training
gate would condition on a post-treatment mediator and is excluded. A later
deployable gate must be learned only from pre-action variables on disjoint data
and compared with an ungated intact arm; that is outside B1.

## Shared actor, behavior batch, and ordinary credit

The actor is a parameter-shared Bernoulli logistic policy. Its inputs are role
one-hot, local cue, normalized skill age, pending-present bit, lag, ordinary
budget remaining, task time, and the partner's previous-tick request/readiness
bits. The latter slots are present in all arms. No type, future suffix, fork
outcome, `kappa`, or gate result is an actor input.

Each confirmatory ancestor begins with all request logits at zero (`p=0.5`) and
seed-specific but paired critic state. A common fixed actor/critic snapshot
collects one frozen on-policy batch. Collection continues until every root has
128 eligible, nonoverlapping edges—exactly eight in each
`(type,lag,ordered_role,sampled_later_action)` cell—or reaches a hard cap of 512
blocks. Counter-keyed hazard uniforms, assigned only after structural
eligibility is known, give exactly 64 later requests and 64 no-requests while
retaining the registered behavior propensity `p_e=0.5`; they do not force an
off-policy action. All collected rows, not only realized joins, remain in the
batch. Failure to reach this support is non-identification, not evidence
against EGRCR.

Ordinary credit is undiscounted task return with `gamma=1`, GAE `lambda=0.95`,
and an identically zero, frozen value baseline. The zero baseline is part of the
scientific treatment, not a tunable implementation choice. All arms therefore
use identical ordinary GAE values and perform no critic learning during the
treatment update.

## Treatment and comparators

There are exactly three common-ancestor actor branches:

- `GAE`: ordinary normalized GAE on every actor record;
- `INTACT`: on each eligible later-joiner record, replace the exact tagged
  joint-handoff reward contribution already inside its GAE with the
  action-conditioned counterfactual advantage formed from the centered,
  scaled `kappa` of its actual older waiter; and
- `BINDING-CUT`: make the identical replacement, but use the `kappa` packet
  from another matched waiter's event under a precommitted bijection `pi(e)`.

All noneligible actor records are bit-identical across arms. The older waiter's
stored request record retains its ordinary GAE in every arm.

For exact double-count accounting, decompose every fork's per-tick reward by
the anchored two-factor identity
`r_uv=r_00+u(r_10-r_00)+v(r_01-r_00)+uv*h`, where
`h=(r_11-r_10)-(r_01-r_00)`. On a realized natural join, the later joiner's
ordinary GAE therefore contains a uniquely tagged discounted/GAE contribution
from `uv*h`; on a realized no-join it is zero. For eligible edge `e`, let
`a_e in {0,1}` be the sampled later action, let `p_e` be its stored behavior
probability before sampling, and let
`T_e=a_e*sum_l (gamma*lambda)^(l-t_j) h_{e,l}` be that exact tagged ordinary-GAE
contribution through the common boundary. `INTACT` and `BINDING-CUT` subtract
`T_e` once from the later record. No other packet-success or renewal-cost
component is removed.

For pre-action structural stratum `s`, calibration freezes
`tilde_kappa_e=kappa_e-m_s`, where `m_s` is the calibration mean. The stratum
contains roles, lag, readiness, ages, remaining budget, time offset, cue
magnitude, and behavior propensity, but excludes sampled action, type, cue
sign, and every outcome. Thus the same prospective center applies to both
sampled actions. For a fixed opportunity, `kappa_e` and `tilde_kappa_e` are
four-world labels from the common pre-action snapshot and do not depend on the
sampled action; only `(a_e-p_e)` supplies the two-action encoding. Calibration
also freezes a single positive scalar `c` so the calibration RMS of
`c*(a_e-p_e)*tilde_kappa_e` matches the RMS of `T_e` over the same eligible
records. A zero RMS on either side fails update expressibility before the
confirmatory binding update. For a raw later-record ordinary advantage
`A_e^GAE`, the frozen pre-normalization advantages are

```text
A_e^INTACT = A_e^GAE - T_e
             + c*(a_e-p_e)*tilde_kappa_e
A_e^CUT    = A_e^GAE - T_e
             + c*(a_e-p_e)*tilde_kappa_pi(e).
```

Thus a sampled request receives relay advantage
`+c*(1-p_e)*tilde_kappa`, while a sampled no-request receives
`-c*p_e*tilde_kappa`. Because
`grad log pi(a_e|x_e)=(a_e-p_e)*grad z_e`, the intact relay's conditional
expected score contribution is
`c*p_e*(1-p_e)*tilde_kappa_e*grad z_e`, rather than zero. `kappa`, `m_s`, `c`,
and every counterfactual outcome are detached training targets and never actor
inputs.

The same centering and scale are used by `INTACT` and `BINDING-CUT`. The cut
permutation is fixed-point-free, one-to-one, and made within strata defined
only by sampled later action, exact stored behavior probability, ordered roles,
lag, readiness, ages, remaining budget, time offset, cue magnitude (not sign),
and behavior-propensity band. It excludes return, `kappa`, credit sign, suffix
outcome, target action, and all future variables. The constructed balanced
blocks predeclare an opposite-type rotation inside each action/propensity
stratum, so every true waiter key changes while both the complete signed
`kappa` multiset and the complete action-conditioned relay-advantage multiset
are preserved exactly.

This is a replacement, not `GAE+kappa`. Each realized tagged joiner reward
contribution is removed once, and exactly one action-conditioned counterfactual
advantage is inserted for each eligible later record. The no-request term is
the counterfactual advantage for the sampled zero action, not a second reward
atom. Each edge, joiner record, waiter packet, and reward atom is used once;
overlapping windows are disallowed. The waiter keeps ordinary GAE because it is
a distinct earlier decision. There is no reverse credit and no zero-sum debit.

## Common-ancestor update and optimizer/work control

For each confirmation seed, clone actor parameters, critic parameters,
normalization state, batch, record order, random coordinates, and optimizer
state into all arms. B1 uses one full-batch actor update and no further
learning. Use the same fresh stateless normalized-SGD rule in every arm:

```text
g_a = full-batch policy-score gradient after arm-local zero-mean/unit-RMS
      advantage normalization
Delta_theta_a = delta * g_a / ||g_a||_2
```

The trust radius `delta` is chosen on calibration roots and frozen at the
largest value whose mean held-out Bernoulli KL is at most `0.02`; the same
`delta` is applied to every arm. A zero gradient fails update expressibility.
This makes inherited optimizer history identically empty and actor displacement
norm identical. Report realized KL, raw and normalized gradient norms,
parameter displacement, score-credit covariance, entropy, and clipping. A
successor that uses Adam must clone moments and step count as well; runtime
renewal never resets an optimizer.

Every arm performs the four-fork label calculations, dummy relay bookkeeping,
same number of actor/value calls, one batch pass, one gradient evaluation, and
one update. Thus extra advantage mass, gross step size, inherited optimizer
state, batch order, or extra work cannot explain `INTACT-BINDING-CUT`.

## Held-out native and yoked evaluation

Confirmation roots are `[17,31,47,61,79,97,109,127,149,167,191,211]` and are
the independent analysis units. Each updated arm is evaluated immediately,
without more learning, on 128 held-out matched dyads per root. A dyad contains
one `JOINT` and one `SOLO` opportunity in the same nuisance stratum and exactly
one joiner request token. The policy allocates that token to the larger of its
two request logits; a seed-fixed tie rule is shared. A separate common-uniform
Bernoulli panel reports whether probability changes create actual requests.

- `NATIVE` preserves each source history/cue with its real waiter and suffix.
- `YOKED` applies an independent, prospectively offset-balanced,
  fixed-point-free rotation of the complete requirement/reward suffix between
  matched blocks. It keeps source histories and logits fixed and preserves the
  full singleton/simultaneous execution mask, per-agent period multiset and
  counts, readiness tape, physics ticks, prepared-skill information time,
  renewal costs, lag, and budgets.

The update-cut permutation and evaluation-yoke permutation are independent. A
yoke is either exactly legal or the alignment estimand is unavailable; no
schedule is repaired after observing outcomes.

For root `r`, report normalized bounded utility `U[a,c]`, join-request
selectivity, actual request allocation, closure count, renewal count, period
histogram, packet success, execution downtime, and cue-stratified request
probability. Define:

```text
D_IG_N = U[INTACT,NATIVE] - U[GAE,NATIVE]
D_IC_N = U[INTACT,NATIVE] - U[CUT,NATIVE]
D_IG_Y = U[INTACT,YOKED]  - U[GAE,YOKED]
D_IC_Y = U[INTACT,YOKED]  - U[CUT,YOKED]
Psi_G  = D_IG_N - D_IG_Y
Psi_C  = D_IC_N - D_IC_Y
```

Aggregate events inside root first. Report paired means and two-sided 95%
Student-t intervals across the twelve roots.

Association-specific support requires all gates and support facts above, plus:

1. `INTACT` exceeds both `GAE` and `BINDING-CUT` on native request
   selectivity and native utility: each paired 95% lower bound is above zero
   and each mean utility effect is at least `0.05`;
2. both `Psi_G` and `Psi_C` have paired 95% lower bounds above zero and means at
   least `0.05`;
3. neither intact advantage remains materially positive after yoking: each
   yoked mean is below `0.025` and its 95% upper bound is below `0.05`;
4. the common-uniform panel shows the probability effect reaches actual join
   choices, while the fixed-token panel keeps request/renewal counts equal; and
5. no cap, mapping, work, clock, or optimizer-match fact is violated.

These `0.05` utility and `0.025` absence margins are local to a normalized
ten-tick host in which one packet opportunity changes utility materially. They
do not come from EBCR, RECCT, or OEER.

## Clocks and accounting

- Physical and task clocks advance one tick in every branch and arm.
- Pending age begins at the waiter's sampled request and advances only by
  physical ticks; expiry is always tick six.
- Skill age resets only on executed renewal, never on request emission.
- Prepared information is frozen before `t_j`; no fork receives additional
  observations.
- Credit is computed after `B` and attached retrospectively to the stored later
  request; no future fact enters execution-time observation.
- Actor calls, messages, transmitted bits, physics ticks, tokens, renewal
  costs, batch rows, label calculations, gradient calls, and updates are
  counted per arm.
- Forced events and overlapping causal windows are absent from B1; any observed
  occurrence invalidates that edge rather than silently changing it.

## Activity, completeness, and small budget

Question-relevant scientific activity begins when one calibration root has
produced legal paired `JOINT` and `SOLO` four-world outcome quartets plus the
waiter-action and exposure record. A process launch, generator contract check,
partial fork, actor forward pass, or fixed schedule alone is preactivity.

The binding question becomes exposed only after all calibration gates pass,
each confirmation root supplies 128 eligible edges, the full fixed-point-free
cut exists, and all three arms take their matched update. Complete
interpretation additionally requires both held-out contexts, the common-uniform
panel, all root-level observables, and resource/accounting facts. Missing
support is non-identification, not a negative EGRCR result.

Registered budget:

- 6 calibration roots x 128 opportunities;
- 12 confirmation roots, at most 512 collection blocks and exactly 128 retained
  eligible edges per supported root;
- 3 arms x 2 contexts x 128 held-out dyads per confirmation root;
- at most `1,000,000` two-agent physical ticks total, one CPU worker, 15 wall
  minutes, and 2 GiB peak RSS; and
- no restart, sweep, arm-specific tuning, seed replacement, threshold repair,
  or post-result enlargement.

A cap stop or unsupported stratum returns to CM as incomplete construction or
to this EM if the scientific support definition must change. It is not a null
result.

## Outcome map

- **All links and association criteria pass:** retain EGRCR as a candidate
  centralized training component and next test a learned pre-action gate plus
  learned `kappa` estimator inside a once-trained variable-`k` policy against
  fixed-`k` and ordinary-GAE adaptive baselines.
- **No positive/usefully varying `kappa`:** this host cannot test ordered relay;
  delete or redesign the joint-execution primitive before any learning test.
- **Later request does not change waiter execution/action:** no causal closure
  edge exists; repair the coordinator/event definition.
- **Waiter changes action but bounded utility does not:** the endpoint or
  exposure boundary is insensitive; do not interpret a binding cut.
- **The joiner target update does not change held-out request probability or
  actual requests:** the policy/update readout is non-expressive; repair the
  feature/head/update before retesting association.
- **`INTACT` and `CUT` change gradients and behavior equally:** target binding
  is unnecessary; generic counterfactual shaping or optimization explains the
  change.
- **`INTACT>CUT` but `INTACT` does not beat `GAE`:** the cut is harmful; there
  is no demonstrated value over the simpler learner.
- **Both `INTACT` and `CUT` beat `GAE`:** changed advantage distribution or
  generic low-variance labels remain sufficient; reject association-specific
  credit.
- **Native benefit persists under yoking:** request rate, cue preference,
  update geometry, or generic packing remains sufficient; do not claim true
  waiter binding.
- **Proximal selectivity separates but bounded utility does not:** credit reaches
  the policy but has no demonstrated task value at this boundary.
- **Benefit appears only through more requests, altered renewals, unequal
  update norm, or false-pair gains:** reject the ordered interaction account.

## Strongest alternative explanation

The relay label may simply be a denser or lower-variance surrogate for favorable
renewal contexts. It could change score-gradient covariance, request rate, or
update direction without conveying the older waiter's identity or causal
effect. Replacing rather than adding the tagged reward, preserving the signed
label multiset in the binding cut, matching update radius and work, requiring
improvement over ordinary GAE, and independently yoking the physical suffix are
all necessary to separate this explanation.

## Conditional relationship to EBCR B1

EGRCR does not wait for, modify, or reinterpret EBCR B1. The Root-relayed B1
facts are local to that direction:

- neither `COORD`, `LOCAL`, nor the registered `STAGE-ORACLE` beat `FIXED-4`,
  and no B1 repeat, successor, or UAV progression was supported;
- the `COORD` bundle beat `LOCAL`, but `YOKED` nearly reproduced it on an
  eligibility-selected subset whose reported mean/min eligibility were
  `0.855469/0.765625`, below B1's own 90%-in-every-cell condition;
- hazards remained near maximum Bernoulli entropy with request rates about
  `0.46-0.57`; and
- `COORD` reduced renewal downtime and increased simultaneous renewals without
  reducing stale rate.

Those facts neither establish positive `kappa` nor show relay-credit failure.
They make EGRCR unnecessary as a repair or successor to that exact B1 host,
because B1 did not establish exploitable variable timing even for its oracle
and did not identify a same-information ordered interaction. They leave this
independent new-host discriminator viable.

Counterfactually, EGRCR would receive stronger motivation from an EBCR-like
host if a matched oracle or adaptive arm established exploitable variable
timing, valid controls left an event-specific opportunity, and ordinary GAE
hazards remained nonselective. It would be weakened if the host lacked positive
and varying four-world `kappa`, or if ordinary GAE already learned selective
requests and survived valid timing controls. It would be unnecessary as an
algorithm repair if ordinary GAE already supported the full variable-`k`
performance/robustness and cooperation claims, or if no matched oracle showed
value in adaptive timing. None of these conditional statements transfers B1
evidence or thresholds.

## Exact Root-to-CM construction packet

If Root allocates the experiment, relay this packet unchanged in scientific
meaning:

```text
scope=direction:expressibility_gated_renewal_credit_relay
treatment=EGRCR-B1-ORDERED-JOINER-WAITER-CREDIT-v1
classification=answer-changing enabling experiment; not a direct variable-k claim
construct=new isolated versioned-handoff microhost, four-world labeler,
          scripted calibration gate, frozen common batch, GAE/INTACT/CUT
          one-update arms, independent legal suffix yoke, analyzer, and one
          train/evaluate/analyze entry point
source_action=later joiner request
target_effect=true older waiter's immediate renewal, first deployed action,
              and bounded utility
credit_destination=later joiner's stored request record only
waiter_credit=ordinary GAE unchanged; no debit and no relay onto waiter
cue_schedule=for every 128-opportunity calibration or retained-confirmation
             root, 116 correct and 12 flipped joiner cues (accuracy 0.90625),
             with 16 opportunities per (type,lag,ordered_role) cell; four
             cells satisfying b_type xor b_lag xor b_order=(zero-based root
             ordinal mod 2) use 14 correct/2 flipped and four use 15/1; choose
             flips by lowest prospective cue-key ranks; never balance cue-flip
             state 50/50
heldout_cues=within each 128-dyad panel, apply 116/12 separately to the 128
             JOINT and 128 SOLO opportunities, with 29/3 in each
             (lag,ordered_role) cell chosen by lowest held-out cue-key ranks
confirmation_actions=128 eligible later records per root, exactly eight per
                     (type,lag,ordered_role,sampled_action) cell; counter-keyed
                     on-policy uniforms yield 64 request and 64 no-request at
                     stored p_e=0.5
tagged_atom=T_e=a_e*sum_l (gamma*lambda)^(l-t_j) h_{e,l}, the realized tagged
            ordinary-GAE interaction contribution; T_e=0 for a_e=0
centering=tilde_kappa_e=kappa_e-m_s using disjoint-calibration means over the
          frozen pre-action structural stratum s; s excludes sampled action,
          type, cue sign, and outcomes, so one center serves both actions
later_record_formula=INTACT: A_GAE-T_e+c*(a_e-p_e)*tilde_kappa_e;
                     CUT: A_GAE-T_e+c*(a_e-p_e)*tilde_kappa_pi(e)
action_cases=request gets +c*(1-p_e)*tilde_kappa; no-request gets
             -c*p_e*tilde_kappa
replacement=remove T_e once and insert exactly one action-conditioned relay
            advantage on every eligible later record; preserve every other
            joiner GAE component and all older-waiter GAE
binding_cut=pi is fixed-point-free and one-to-one within exact sampled-action,
            propensity, and pre-action nuisance strata; it changes the true
            waiter key while preserving both the signed-kappa multiset and the
            action-conditioned relay-advantage multiset exactly
update_scale=freeze one positive c on calibration data by matching RMS of
             c*(a-p)*tilde_kappa to RMS of T; use the same c, arm-local
             advantage normalization, normalized-SGD trust radius, records,
             work, and displacement scale in INTACT and CUT; zero RMS fails
             update expressibility before confirmation
comparators=ordinary GAE and optimizer/work/label-multiset-matched binding cut
required_observables=all gates, four Y worlds, self/waiter/generic-waiter/kappa,
                     source-target first stage, action exposure X, joiner
                     probability/selectivity and common-uniform actions,
                     native/yoked utilities and interactions, counts, periods,
                     entropy, gradient norms, KL, displacement, clocks, work,
                     caps, anomalies, and activity witness
sequence=run calibration/contract surface first; only if all scientific gates
         pass, collect the common confirmation batch, take the three matched
         one-step updates, then evaluate NATIVE and independently YOKED panels
compute_cap=1,000,000 two-agent ticks; one CPU worker; 15 minutes; 2 GiB RSS
dependency=none on EBCR completion, code, host, thresholds, or result
return=whether question-relevant activity began; gate facts; whether the
       binding question was exposed; root-level effects; anomalies; remaining
       unknowns; no scientific interpretation by CM
```

CM owns source, tests, runner, environment, technical acceptance, and any
unchanged-science repair. This card authorizes no EM code, test, or run. A
deterministic contract check is not scientific evidence; the first production
execution should follow the two-stage sequence above once CM accepts its
construction.

## Toy-to-UAV bridge

The positive-cell handoff maps to a tracker and relay that must advance to a
compatible option generation after a target maneuver plus link-regime change.
The older waiter is an early tracker invalidation or weak-link replan request;
the later joiner is delayed confirmation from the relay, formation, or
connectivity agent. The pending window is a bounded termination/replan
handshake; readiness is the flight-envelope, separation, battery, or link
margin; atomic execution is a compatible waypoint/role/relay-option refresh.
The `SOLO` cell maps to a false or role-local invalidation for which advancing
the partner would create a transient incompatible plan.

The first UAV-facing surface is a continuous planar two-UAV tracking-relay
simulator with fixed low-level controllers, externally changed maneuver/link
durations, packet delivery, energy, separation, and replan latency. It must
freeze prepared options at handshake entry; compare atomic versus separate
execution with identical information, physics, per-agent costs, tokens,
messages, and optimizer history; and retain a legal suffix association cut.
Only after B1 supports the ordered learning edge should a learned pre-action
gate and learned counterfactual estimator be included in one shared policy
trained across duration regimes. That successor must beat matched fixed-`k`
and ordinary-GAE adaptive baselines on performance or robustness. No toy result
is UAV evidence.

## Claim ceiling

The strongest positive B1 claim is:

> In this constructed two-agent versioned-handoff host, after independently
> establishing a positive and varying same-information waiter interaction and
> both expression links, assigning the correctly matched waiter-effect target
> to the later joiner's stored request caused a more selective and useful
> one-step policy update than ordinary GAE and an equal-marginal wrong-waiter
> binding cut; the native advantage disappeared when the causal suffix
> association was independently yoked.

B1 cannot establish multi-update stability, learned counterfactual estimation,
a deployable expressibility gate, general PPO superiority, end-to-end
variable-`k` performance or robustness, superiority to fixed `k`, UAV value,
safety, continuous control, variable `N`, more than two agents, arbitrary
pending graphs, or general source-target credit. A null is limited to this
host, policy head, one-update radius, roots, budget, exposure boundary, and
criteria. A failed gate is a missing causal/readout link, not evidence that
ordered renewal credit is generally useless.
