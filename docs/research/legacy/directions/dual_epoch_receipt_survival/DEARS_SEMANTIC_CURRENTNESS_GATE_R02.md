# DEARS owner semantic-currentness gate R02

Cycle: `2026-08-29.8-portfolio-dears-semantic-currentness-02`

Scientific object: `DEARS-OWNER-SEMANTIC-CURRENTNESS-R02`

Milestone: `HANDOFF_READY`

Review: `REVIEW_RESOLVED`

Portfolio authority: `d7465b6ff509e062ff12a5ff54c3f0dccf20d8c9`

Integrated baseline: `26f9c20cc164c39cf1bf7bc5a0d843c55cf319e9`

## Fresh question and R01 boundary

R01 proved a finite live-cell retained-bit versus competent-reacquisition gap, and exact raw
containment removed any representation claim. Its broken-cell payoff nevertheless left the old
receipt content task-correct, so the unrestricted raw optimum correctly ignored the fail-closed
gate. R02 does not reuse or relabel an R01 prompt, operation, conversation, response, reward, or
result. R01 is provenance for one specific objection only.

The fresh question is whether an OWNER-lineage currentness predicate has native action and return
value when the old receipt content is correct exactly while its OWNER lineage is live and becomes
conditionally stale after an OWNER break. Authentication and SKILL_LEASE stay live. This cycle
asks only whether deterministic currentness-gated retention matches the unrestricted exact raw
optimum and separates from both competent bit-deleted reacquisition and equal-content ungated old-
bit use on this finite host.

## Public host, unit, clock, and coupled intervention

One observational unit is a post-change service world. One matched superblock contains an
`OWNER-LIVE` world and an `OWNER-BROKEN` world. Before the change, one authenticated B1-format
receipt stores `b_old in {0,1}`. The receipt authentication checks and the complete SKILL_LEASE
lineage are live in both worlds. The OWNER-LIVE history is an exact live chain. The OWNER-BROKEN
history has one prospectively designated unmatched predecessor edge while ending at the same
paired final owner version and visible snapshot.

The two worlds have the same `b_old`, receipt/authentication facts, SKILL_LEASE history, final
visible snapshot, action support, public phases, event ordering, timestamps, break locus, and all
non-OWNER nuisance facts. Only the designated OWNER edge and its stipulated semantic consequence
differ. The snapshot contains no old bit, current bit, correct action, live/broken label, or
correlated shortcut.

At the post-change service decision, the current payoff bit is `b_cur`. In `OWNER-LIVE`,
`b_cur=b_old`. In `OWNER-BROKEN`, `b_cur=b_fresh`, where `b_fresh` is a fair bit conditionally
independent of `b_old`, public phases, final snapshot, primitive history, and every other
controller-visible or nuisance fact. Exact enumeration crosses
`b_old in {0,1}`, `b_fresh in {0,1}`, `z_0 in {0,1}`, and `z_1 in {0,1}` within every legal fixed
nuisance stratum. `b_fresh` is ignored in the live world and used in the broken world. This is an
algebraic conditional cross, not a sampled RNG result.

At tick `t=0`, action support is exactly `{SERVE_0, SERVE_1, PROBE}`. Immediate service is correct
iff `m=b_cur XOR z_0`: `SERVE_m` returns `+1`, the other service action returns `-1`, and either
terminates. `PROBE` consumes the current opportunity, costs `kappa=1/4`, and delays service one
tick with penalty `lambda=1/4`. At `t=1` it reveals `b_cur`, exposes paired phase `z_1`, and permits
one correct service action, so optimal total probe return is exactly
`1-kappa-lambda=1/2`. There is no wait, passive reveal, feedback before termination, second probe,
or alternative reacquisition action.

## Frozen controllers and permitted work

`RULE-OWNER-CURRENT-RETAIN` receives the authenticated receipt and the primitive B1 history and
applies the deterministic fail-closed verifier. Because authentication and SKILL_LEASE are live,
its decision reduces to OWNER currentness: in `OWNER-LIVE` it immediately serves
`b_old XOR z_0`; in `OWNER-BROKEN` it probes. It never uses `b_old` after a bottom result.

`UNGATED-OLD-BIT-USE` receives the same retained `b_old`, public phases, and primitive facts but is
the fixed equal-content policy that immediately serves `b_old XOR z_0` in both cells. It is not an
optimizer and may not turn the observed break into a probe; permitting that would replace this
mechanism comparator with the unrestricted raw optimum.

`RAW-EXACT-OPTIMUM` receives every primitive authentication, receipt, OWNER, SKILL_LEASE, final-
snapshot, action-support, and public-phase fact available to the gated rule, including `b_old`, but
no derived OWNER-current or joint-live summary. It knows the frozen data-generating and payoff
laws, may perform every finite deterministic equality, chronology, predecessor, coverage, and
final-version operation used by the verifier at equal zero-time work, and chooses the return-
maximizing supported action. It is unrestricted within this information/action set.

`RESET-ORACLE-REACQUIRE` deletes `b_old` at the change boundary. It retains the complete primitive
authentication and lineage history, final snapshot, public phases, support, probe physics, and the
frozen conditional law. It chooses the exact return-maximizing supported policy and cannot fail
from inactivity, exploration, training, optimization, or capacity.

`SNAPSHOT-CONTENT-NULL` is an auxiliary content-opportunity null. It receives all final visible and
non-lineage facts but neither `b_old`, `b_cur`, nor primitive receipt/lineage history. Conditional
bit twins must make every blind immediate service policy worth zero and leave the same competent
probe value `1/2`. This null is not a containing comparator and cannot establish lineage value by
itself.

## Estimands, complete gate, and stop rules

For policy `a` and cell `c`, `J_a(c)` is the uniform arithmetic mean of terminal return over the
finite conditional cross within each complete fixed nuisance template after excluding the bit being
intervened on. The support audit records each controller-specific pre-action observation-
equivalence class, permitted actions, selected action, action-changing bit twin, and return in every
cell.

The candidate survives only if all of the following hold:

1. conditional support is complete: within every reset/null live pre-action observation-
   equivalence class, both `b_old` values have equal mass; within every complete broken pre-probe
   observation-equivalence class, including `b_old` and primitive OWNER history when observed, both
   `b_fresh` values have equal mass; and, for retained rule/raw live action support, `b_old` is
   crossed within an otherwise-fixed nuisance template that expressly excludes `b_old`, rather
   than being called one identical fully observed state;
2. `RULE-OWNER-CURRENT-RETAIN` and `RAW-EXACT-OPTIMUM` choose the same action and return in both
   cells, with no alternative raw-optimal action;
3. `J_RULE(OWNER-LIVE) > J_RESET(OWNER-LIVE)`;
4. `J_RULE(OWNER-BROKEN) > J_UNGATED(OWNER-BROKEN)`; and
5. the reset oracle and snapshot/content null use the optimal supported reacquisition policy rather
   than an inactive or weak learned baseline.

A support defect, unpaired nuisance, payoff ambiguity, shortcut, alternative raw-optimal action,
missing strict inequality, unequal information/work, or probe-law change stops before learning and
answers this bounded question negatively. A stale old-bit service by the gated rule after the
OWNER break invalidates the object. A changed reward, freshness law, lineage axis, authentication
state, SKILL_LEASE state, action support, or cost/delay law is a new scientific object.

## Predictions, alternatives, and claim ceiling

Semantic-currentness value predicts immediate old-bit service only in the live cell and probing
after the break. A merely restrictive gate predicts no advantage once compared with the
unrestricted raw optimum. Generic final-state predictability predicts nonzero blind snapshot
value. Cheap reacquisition predicts no live headroom. A semantically irrelevant OWNER break
predicts that `b_old` remains useful after the break, reproducing R01's objection. Hidden coupling
or only marginal balance predicts a conditional support failure.

Even a positive gate supports only deterministic OWNER semantic-currentness/protocol value for one
authenticated receipt, one OWNER break, one post-change opportunity, the stipulated conditional
freshness law, and the exact probe cost/delay. Exact raw containment precludes a derived-summary,
representation, decoder, learned abstraction, or algorithm advantage. The cycle cannot establish a
distinct SKILL_LEASE mechanism, dual-lineage or factorial value, authentication/security value,
MARL, variable population, arbitrary histories, UAV relevance, safety, or deployment value. It is
a gross-value result because retention and verification have zero charged cost.

If the complete gate survives, the decision impact is at most support for a separately authorized
narrow deterministic continuation; it does not itself authorize one. If the gap or raw optimality
fails, the semantic-currentness scope supports PARK or CLOSE consideration. Invalid evidence has
no lifecycle implication.

## Resource and evidence freeze

Exact enumeration or algebra is preferred. No learned activity, training, seed, checkpoint, result
command, or scientific compute is authorized by this freeze. A fresh Sol/high CM may be created
only if a scientifically necessary executable observation remains after the exact audit and Pro
Innovator synthesis. One independent result-blind research set, one fresh owner-authored GPT-5.6
Pro Innovator consultation, and one fresh conclusion-blind GPT-5.6 Pro Convergence consultation
bound the review. R01 provider artifacts are provenance only and cannot be current evidence.

Frozen references are the integrated Portfolio authority and refill decision, `DIRECTION.md`, and
`DEARS_ONLINE_CARRIER_VALUE_GATE_R01.md` at baseline `26f9c20c`. The R02 evidence note and its fresh
provider artifacts are the only new cycle-owned scientific records.

## Pre-synthesis wording repair

An independent principles audit identified that the initial Gate 1 shorthand required both
`b_old` values at one live "controller-visible state," even though retained rule/raw controllers
observe `b_old`. The host definition and frozen Innovator prompt already specified the intended
otherwise-fixed nuisance cross, but the shorthand could not literally define support for
controllers with different observation maps. Before synthesis, Gate 1 was therefore made explicit
in controller-specific observation-equivalence classes with uniform arithmetic weights.

This is a wording and estimand-notation repair within the same material cycle. It changes no world,
intervention, distribution, coupling, controller information, permitted work, action, payoff,
threshold, invalidator, claim ceiling, prompt, provider operation, or evidence budget. The repair
is itself reviewable at Convergence; if it cannot be accepted as equivalent to the already frozen
conditional cross, the candidate fails its support gate.

## Synthesis-ready evidence

### Independent routes and direct algebra

Three fresh result-blind routes attacked the frozen object without seeing one another or provider
output. The support/innovation route returned `CANDIDATE`; the comparator critic returned
`NO_MATERIAL_OBJECTION`; and the principles route returned `DEFECTS` solely because the original
support shorthand could not literally apply to controllers that observe different variables. That
definition defect produced the explicit pre-synthesis repair above. The principles route agreed
that the coupled host and action algebra otherwise close, while emphasizing that semantic refresh
is stipulated with the OWNER break rather than discovered from it.

For any known current bit, a policy assigning probabilities `q_c`, `q_w`, and `q_p` to correct
service, wrong service, and probe has return

`q_c - q_w + (1/2) q_p`,

which is uniquely maximized by correct immediate service. For any conditionally fair hidden current
bit, every pre-probe immediate service or mixture has value zero, while a policy probing with
probability `q_p` has value `(1/2) q_p`; `PROBE` is therefore uniquely optimal.

The complete controller disposition is:

| Controller | `OWNER-LIVE` action and return | `OWNER-BROKEN` action and return |
| --- | --- | --- |
| `RULE-OWNER-CURRENT-RETAIN` | `SERVE_(b_old XOR z_0)`; pathwise `1` | `PROBE`; pathwise total `1/2` |
| `UNGATED-OLD-BIT-USE` | `SERVE_(b_old XOR z_0)`; pathwise `1` | same service; `+1` if `b_fresh=b_old`, otherwise `-1`; exact mean `0` |
| `RAW-EXACT-OPTIMUM` | same unique action as the rule; `1` | same unique action as the rule; `1/2` |
| `RESET-ORACLE-REACQUIRE` | unique `PROBE`; `1/2` | unique `PROBE`; `1/2` |
| `SNAPSHOT-CONTENT-NULL` | unique `PROBE`; `1/2` | unique `PROBE`; `1/2` |

Support is stratumwise rather than marginal. In every reset/null live observation-equivalence class,
equal-mass `b_old` twins require opposite correct immediate actions. In every complete broken pre-
probe observation-equivalence class, including the observed `b_old` and primitive OWNER history,
equal-mass `b_fresh` twins require opposite correct service actions. Retained live controllers split
those old-bit twins into distinct observations and select the corresponding action. Crossing the
public phases exposes both service labels without changing value. No row index, pair identity,
generator state, cross-episode observation, or other shortcut is available.

All prospective gates therefore clear under the repaired equivalent support notation:

- rule/raw actions and returns are equal in both cells and uniquely return-optimal;
- the live rule/reset gap is `1 - 1/2 = 1/2`;
- the broken rule/ungated gap is `1/2 - 0 = 1/2` in conditional expected return; and
- reset and the content-deleted snapshot null are competent within their information sets.

The broken comparison is not pathwise dominance. On the half of fresh twins where
`b_fresh=b_old`, ungated use returns `1` and exceeds probing; on the other half it returns `-1`.
The gated decision is Bayes-optimal before observing fresh content because the fresh bit is exactly
conditionally fair.

### Raw containment and persistence-versus-representation decomposition

The constructive raw policy computes the same OWNER predecessor predicate from primitive history,
serves the phase-correct old bit while live, and probes after the break. Feasible emulation follows
from deterministic information containment. Optimal-policy equality follows separately from the
strict action values: correct service uniquely dominates probe in the live cell, and probe uniquely
dominates every immediate action in the broken cell. Unlike R01, raw optimization and fail-closed
emulation therefore coincide after the break.

This supports deterministic protocol-currentness alignment only. The derived summary adds no
information or permitted-work advantage, and the full B1 verifier is not uniquely identified: with
authentication and SKILL_LEASE fixed live, an equivalent direct OWNER-edge predicate suffices. No
representation, decoder, learned abstraction, or algorithm advantage remains, so no learned
comparison is admissible in this cycle.

### Competent-null disposition and alternative comparator

`RESET-ORACLE-REACQUIRE` is competent, exact, and bit-deleted. `SNAPSHOT-CONTENT-NULL` is explicitly
content-deleted as well as history-deleted; it proves only that generic final-state facts cannot
select immediate service and is diagnostically redundant with reset in return space. It does not
isolate OWNER-lineage information.

`UNGATED-OLD-BIT-USE` is a fixed stale-use mechanism comparator, not an optimizer. It is scientifically
useful only because `RAW-EXACT-OPTIMUM` separately supplies the containing competence control.
Fresh Pro Innovator identified a distinct content-retaining but OWNER-blind optimum. Under a newly
specified equal live/broken mixture, that information set has aggregate value `1/2` and a continuum
of optimal mixtures between old-bit use and probe, while the lineage-aware rule has aggregate value
`3/4`. That would yield an OWNER-information value of `1/4`, but the current cycle did not freeze an
aggregate cell-mixture estimand or that comparator. It is therefore retained as an alternative and
possible next discriminator, not added post hoc to the current claim.

### Strongest support, objection, and claim ceiling

The strongest support is exact: the same OWNER predicate that licenses immediate correct use in the
live cell uniquely sends an unrestricted raw optimum to the competent probe after a break, clearing
both strict `1/2` gaps with no raw-optimal tie. The R01 semantic defect is removed on the stipulated
host.

The strongest objection is external and causal: the host jointly assigns OWNER-edge validity and
the content law `b_cur=b_old` versus conditional freshness. It proves how a competent policy should
act under that law; it does not independently show that an OWNER break naturally causes semantic
staleness. The result is also gross value because retention and verification are free while probe
cost and delay total `1/2`. Other risks are unequal conditional weights, episode-order leakage,
hidden shortcuts, altered probe value, nonzero retention/verification cost, noisy probes, repeated
service, skewed fresh-content persistence, and conflating conditional expected improvement with
pathwise protection.

The accepted maximum claim is:

> In the equal-weight finite R02 host, conditional on one authenticated receipt, live
> authentication and SKILL_LEASE, the stipulated OWNER-dependent content law, free deterministic
> verification, and the exact one-probe payoff, the OWNER-currentness-gated rule is the unique
> unrestricted raw-information optimal first-action policy: it returns `1` by immediate old-bit use
> while OWNER lineage is live and `1/2` by probing after the stale-content OWNER break. It strictly
> exceeds bit-deleted reset by `1/2` in the live cell and fixed ungated old-bit use by `1/2` in
> conditional expected return after the break.

It cannot establish natural OWNER-break semantics, verifier necessity, a separate SKILL_LEASE or
dual-lineage mechanism, authentication/security value, learned representation, MARL, changing
population, arbitrary histories, UAV relevance, safety, or deployment value.

### CM sufficiency, next discriminator, and cost

No CM is scientifically necessary. The finite conditional cross, action values, optimizer, and
containment relation are closed by exact algebra; an implementation would only instantiate the
same truth table and cannot validate the stipulated semantic law. No training, seed, checkpoint,
result command, RNG draw, or scientific compute was used.

The smallest same-scope continuation is a separately frozen OWNER-only analytic robustness frontier
over broken-cell persistence `rho=P(b_cur=b_old | pre-probe information, OWNER-BROKEN)` and explicit
retention/verification cost. With the present probe value, an immediate action ties probe at
`rho=1/4` or `3/4` and probe is uniquely optimal for `1/4<rho<3/4`. A claim about OWNER-lineage
information itself would instead require the separately frozen content-retaining OWNER-blind
comparator and a fixed cross-cell mixture. Either remains exact-algebra cost: roughly one short EM
cycle, two mandatory Pro consultations, no CM, and no scientific compute.

### Fresh Pro Innovator facts

The GPT-5.6 Pro Innovator transport is `COMPLETE`. Strict operation
`b2d14e6e-d34c-437e-8bd0-fc648c2e97f8` sent the exact 4,942-byte prompt once in new provider
conversation `https://chatgpt.com/c/6a93292f-6214-83e8-96b6-bbe7de2df4a9` under visible `Pro` model
evidence. The 17,774-byte naturally completed response is archived at
`temp/directions/dual_epoch_receipt_survival/exp/2026-08-29-semantic-currentness-02/pro_innovator_response.md`
with SHA-256 `739cf67b39d98394b04a11e66d2a8c4c3012786eb0743e7b4c12ea3ccdfba8a1`.

### Convergence disposition and terminal judgment

Fresh conclusion-blind GPT-5.6 Pro Convergence returned a narrow pass. Every scientific objection
is dispositioned as follows:

- The original support sentence was ill-typed for retained controllers, but the explicit
  controller-specific observation-map repair is accepted as object-preserving. It is not treated as
  a literal defense of the defective sentence. The chronology is durable: scope freeze commit
  `8805e61f`, pre-synthesis wording-repair commit `f31cca65`, and synthesis commit `4d525969`.
- All required strict gates pass. The phase-correct live service and broken probe are unique raw
  optima; reset is competent and bit-deleted; and the snapshot/content null is competent only for
  its diagnostic no-shortcut role.
- The absent optimized content-retaining OWNER-blind comparator narrows rather than reverses the
  current result. Without a frozen cross-cell prior it blocks an aggregate OWNER-information-value
  claim. It does not alter the required cellwise rule/raw equality or the two strict comparisons.
- The broken rule/ungated gap is conditional expected improvement, not pathwise dominance or an
  external safety guarantee.
- The stipulated coupling of OWNER status and semantic refresh remains the controlling objection.
  The host proves the optimal response to that law and does not discover the law or identify the
  full verifier as necessary.
- Convergence could not find the R02 file at the pre-cycle integrated baseline `26f9c20c`. That is
  an archival observation, not a scientific contradiction: R02 was necessarily created after that
  baseline, and the ordered current-cycle commits above preserve its freeze and repair chronology.

The bounded R02 question is therefore answered positively at the narrow host-internal ceiling. R01's
specific raw-optimality objection is removed: after the stipulated OWNER break, even unrestricted
raw history makes old content conditionally uninformative and uniquely chooses the same probe as the
gate. Exact raw containment simultaneously leaves no learned or representation increment.

Decision impact: retain only a narrow deterministic OWNER-currentness/protocol question. A later
separately authorized robustness or comparator cycle may be worthwhile; learned, SKILL_LEASE,
dual-lineage, authentication/security, safety, and deployment work are not justified by R02.
Recommendation: `NARROW`.

### Fresh Pro Convergence facts

The GPT-5.6 Pro Convergence transport is `COMPLETE`. Strict operation
`8949f40b-a09b-4e6a-b540-16af6a2daeec` sent the exact 7,285-byte conclusion-blind prompt once in new
provider conversation `https://chatgpt.com/c/6a932d06-ddc8-83e8-8f0d-a63d0925019f` under visible
`Pro` model evidence. The 17,080-byte naturally completed response is archived at
`temp/directions/dual_epoch_receipt_survival/exp/2026-08-29-semantic-currentness-02/pro_convergence_response.md`
with SHA-256 `f1d6c6053832a69fb492afa8f1e80d1d6fb137920fb98f7c8718166a756f915f`.

Both Pro stages are complete and no provider Effect remains live. No CM was created, no writer
transfer occurred, and the EM remained the sole direction-visible writer. Current scientific cost
was three read-only research leaves, two mandatory Pro consultations, exact algebra, zero result
commands, zero training, and zero scientific compute. No lifecycle or capacity action is performed
by this evidence note.
