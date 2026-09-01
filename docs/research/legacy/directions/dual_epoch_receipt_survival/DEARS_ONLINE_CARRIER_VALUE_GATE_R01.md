# DEARS authenticated online carrier-value gate R01

Cycle: `2026-08-29.8-portfolio-dears-lineage-value-gate-01`

Scientific object: `DEARS-ONLINE-CARRIER-VALUE-R01`

Milestone: `HANDOFF_READY`

Review: `REVIEW_RESOLVED`

Portfolio authority: `9b131a5ced84b398da07e99807aa9c1163897102`

Integrated baseline: `1cc3e4c8b2726892b9e36f0134211e95be594af4`

## Why this is a fresh material cycle

B1 established that its deterministic fail-closed verifier summary was sufficient and much easier
for the frozen supervised GRU to decode than primitive raw history. It did not establish online
return value. The later VNFC-B2 package did not separate typed retention from reset or raw history,
and it did not identify the carrier mechanism because every learned package remained far below the
fresh-fact oracle and reset did not exercise its supported probe path. This cycle therefore asks a
new question: whether retained authenticated content itself changes an online service action and
return after giving reset a competent reacquisition policy, and whether any increment survives an
exact same-information raw-history controller. It does not repeat B1, VNFC-B2, or any retired
Orbit, EC4G, VAP/FOLR, VNFC, or VSP object.

## Frozen question and non-goals

Can authenticated fail-closed retention earn a material direct-return advantage over a reset
controller that optimally uses an explicitly supported reacquisition action, separately when owner
lineage and skill/lease lineage are the changed axis? If so, is that advantage specific to the
derived verifier summary, or is it reproduced exactly by a controller containing the same primitive
receipt and lineage history?

This cycle does not test a learned decoder, classifier, recurrent architecture, optimizer,
cryptography, arbitrary lineage depth, decentralized communication, population-scale variable-N,
adaptive skill duration, UAV transfer, or production safety. It cannot import positive evidence
from consolidated direction labels. A deterministic protocol-value result is not a learned
algorithm result.

## Public host, observational unit, and exposure clock

Each observational unit is one cloned post-change service world. Before the change, exactly one
receipt records a fair bit `b in {0,1}` and anchors the B1 owner and skill/lease lineages. The
receipt passes the B1 tag and authorized-issuer checks. The primitive history contains the receipt,
two owner updates, and two skill/lease updates in one of the six legal B1 interleavings. The final
owner and lease versions and final covering lease interval are fixed within a matched superblock.

There are two separately identified matched cell families:

- `OWNER`: skill/lease lineage is live; the owner lineage is either an exact live chain or has one
  designated unmatched predecessor edge while ending at the paired final owner version.
- `SKILL_LEASE`: owner lineage is live; the skill/lease lineage is either an exact gap-free live
  chain or has one designated unmatched predecessor edge or positive coverage gap while ending at
  the paired final lease version and interval.

The live and broken members share the receipt content, opaque values except the designated
unrelated predecessor, final snapshot, action support, public phases, event ordering, timestamps,
break-locus designation, and all non-lineage nuisance facts. Break edge, lease-break kind, legal
interleaving, receipt bit, and public phases are crossed prospectively. Owner and lease failures are
never pooled to manufacture a two-axis effect.

At post-change tick `t=0`, every controller sees the same public phase `z_0 in {0,1}`, final visible
snapshot, and action support `{SERVE_0, SERVE_1, PROBE}`. The snapshot contains neither `b`, a live
bit, a semantic-cell label, the correct action, nor any shortcut correlated with them. Direct
service is correct iff `m = b XOR z_0`: `SERVE_m` returns `+1`, the other service action returns
`-1`, and either terminates the world. `PROBE` consumes the current service opportunity, incurs a
physical scan cost `kappa=1/4`, and delays service one tick with a fixed delay penalty
`lambda=1/4`. At `t=1` it reveals the current bit, exposes the cloned public phase `z_1`, and permits
one service action. Optimal post-probe total return is therefore exactly
`1-kappa-lambda=1/2`. There is no wait action, service feedback, passive reveal, or other
reacquisition path.

The finite nuisance space is the Cartesian product of the two cell families, live/broken status,
`b`, `z_0`, `z_1`, six legal update interleavings, two edge designations, and, for the lease family,
reference-break versus coverage-gap designation. Algebra may discharge the gate pathwise; no
sampling or RNG is needed.

## Frozen controllers and information sets

`RULE-DUAL-RETAIN` applies the existing B1 verifier to the authenticated receipt and primitive
history. It exposes and uses the stored bit only when authentication, owner lineage, and
skill/lease lineage are all live. On a live history it serves `b XOR z_0`; on any bottom result it
probes. It may not use a stale or unauthenticated bit.

`RESET-ORACLE-REACQUIRE` deletes the pre-change receipt content at the change boundary. It observes
the complete final snapshot, public phase, action support, probe physics, and the known balanced
content law. It selects the return-maximizing supported policy exactly; it is not learned and cannot
fail through inactivity, exploration, optimization, or weak capacity.

`RAW-EXACT-RETAIN` receives the same primitive authentication facts, receipt content, owner-update
records, lease-update records, final versions, and public phases from which the B1 verifier is
computed, but receives no derived owner-live, lease-live, or joint-live bit. It may perform the same
finite deterministic equality, chronology, coverage, and final-version work as the verifier and
then choose among exactly the same actions. It is the containing controller for the mechanism-
specificity gate.

`SNAPSHOT-CONTENT-NULL` receives all final visible and non-lineage facts but neither the retained
content nor primitive receipt/lineage history. Because each snapshot is paired across both values
of `b`, its immediate direct-service policies face contradictory correct actions. It may use the
same optimal probe path as reset. This null separates a content-dependent service opportunity from
generic final-state predictability.

## Estimands, gates, and prospective interpretation

For family `f in {OWNER, SKILL_LEASE}`, let `J_a(f,+)` be exact expected return of controller `a`
over the crossed nuisance space in the live member, and `J_a(f,-)` the corresponding broken member.
The direct-persistence estimand is

`Delta_persist(f) = J_RULE-DUAL-RETAIN(f,+) - J_RESET-ORACLE-REACQUIRE(f,+)`.

Gate 1 requires, separately in both families, action-changing support under the paired `b`
intervention and `Delta_persist(f) >= 1/4`. A missing or smaller gap stops before any learned or CM
activity. Broken cells must also send the rule to `PROBE`; any stale service action invalidates the
object rather than counting as a negative treatment result.

Gate 2 is pathwise policy and return equality between `RULE-DUAL-RETAIN` and
`RAW-EXACT-RETAIN` over every finite history. If raw containment reproduces the rule, the maximum
result is deterministic authenticated persistence value over reset/reacquisition. There is then no
derived-summary, learned-abstraction, dual-lineage-algorithm, or representation advantage to test
in this cycle. Only a concrete finite-work distinction left after exact containment could justify a
later separately frozen learned comparison.

The content/snapshot null must have immediate service value zero under balanced `b` and optimal
total value `1/2` through probing. A snapshot-only direct advantage, an unpaired nuisance, an
unsupported reset action, information unavailable to one containing controller, or a change in
probe cost/delay invalidates scope.

## Competing explanations and predictions

- Direct persistence value predicts that both live families serve immediately and exceed competent
  reset by at least `1/4`, while broken families fail closed to the same probe value.
- Cheap or irrelevant reacquisition predicts no material live-family headroom after reset is made
  optimal.
- Generic final-state information predicts that the snapshot/content null can select the direct
  service action; paired content twins predict that it cannot.
- Summary-specific abstraction predicts a policy or return increment beyond an exact primitive-
  history controller. Deterministic containment predicts pathwise equality and confines the result
  to protocol persistence.
- Host leakage or lineage confounding predicts broken pairing, a nuisance-dependent correct action,
  or stale service in a broken cell; any such witness invalidates rather than supports the gate.

## Claim ceiling, resource bound, and stop rules

The initial claim ceiling is a finite public-host statement about one authentic B1-format receipt,
two-edge owner and lease histories, one post-change service opportunity, one supported probe, and
the exact cost/delay law above. It cannot establish a learned component, universal necessity of two
lineages, online MARL learning, general churn robustness, safety beyond the enumerated histories,
or UAV value.

The observation bound is one algebraic/pathwise audit of the frozen finite space, one neutral set of
independent result-blind research routes, and the mandatory fresh Pro Innovator and conclusion-blind
Pro Convergence operations. No training, empirical seed, or result command is authorized by this
freeze. CM is authorized only if a scientifically necessary observation survives that cannot be
answered read-only. Stop after Gate 1 if headroom is absent; stop after Gate 2 if exact containment
absorbs representation specificity; stop on any pairing, support, information, or fail-closed
violation. A changed reward, probe law, history, information set, or action support is a new
scientific object rather than a repair of this cycle.

## Synthesis-ready evidence

### Inputs and direct observations

The frozen object was attacked by independent result-blind construction, primary-source
containment, and MARL-principles routes, followed by one fresh GPT-5.6 Pro Innovator challenge. No
route received another route's output. All four routes independently derived the same live-cell
algebra and the same representation containment; the construction, principles, and Pro routes also
identified the same broken-cell objection.

Conditional crossing is exact: for every reset-visible state, including `z_0` and every nuisance
field, the two receipt-content twins require opposite immediate service actions. An immediate
`SERVE_0`, `SERVE_1`, or mixture therefore has expected return zero. `PROBE` returns exactly
`1-1/4-1/4=1/2` and is the unique optimal supported reset policy. The snapshot/content null has the
same immediate value zero and optimal value `1/2`.

In either labeled live-family slice, `RULE-DUAL-RETAIN` exposes `b`, serves `b XOR z_0`, and returns
`1`. Consequently

`Delta_persist(OWNER) = Delta_persist(SKILL_LEASE) = 1 - 1/2 = 1/2`.

Gate 1 clears its prospective `1/4` threshold in both slices, and paired `b` twins change the direct
service action. This is one common cache-versus-reacquisition value repeated under two labels, not
two independent or additive lineage-value effects: both live slices are the same conjunction
`authentication AND owner-live AND lease-live` with the same bit, reward, and probe physics.

The B1 verifier is a deterministic function `V(H)` of the primitive history `H`. Because
`RAW-EXACT-RETAIN` receives every primitive input and equal zero-time deterministic work, the
constructive policy `pi_RAW(H,z)=pi_RULE(V(H),z)` reproduces every rule action and return pathwise.
This discharges Gate 2 as exact information containment and leaves no derived-summary,
representation, decoder, learned-abstraction, or dual-lineage algorithm increment.

### Strongest surviving objection

The frozen reward declares the old receipt bit `b XOR z` correct even when owner or lease lineage is
broken. An unrestricted return-optimal raw controller that can read `b` should therefore ignore the
verifier in broken cells, serve immediately, and return `1`, while the fail-closed rule probes and
returns `1/2`. Thus pathwise rule/raw equality is a constructive conformance witness, not an
optimal-policy equality. The broken cells show that each tested predicate can trigger the stipulated
gate, but they do not show that gating protects current task return, safety, authentication value,
or lineage-specific semantic validity. Authentication is fixed live and is not intervened on.

This objection does not erase the live conditional cache lemma. It does prevent calling the result
authenticated fail-closed return value in general, separate owner-lineage or lease-lineage value,
or external task evidence. It also prevents interpreting a raw deviation as a surviving finite-work
representation question. The current object is not changed post hoc.

### Competent-null disposition and alternatives

- `RESET-ORACLE-REACQUIRE` is competent and exact; inactivity, exploration, weak learning, and
  optimizer exposure are eliminated.
- `SNAPSHOT-CONTENT-NULL` proves only that final generic state cannot select immediate service under
  the exact paired content fork. It removes more than content and is not a containing comparator.
- `RAW-EXACT-RETAIN` proves information containment by explicit verifier emulation. An unrestricted
  raw optimum is a separate counterexample to fail-closed task value in broken cells.
- The common risks are imposed reacquisition cost with zero retention/verification cost, conditional
  rather than merely marginal balance, hidden seed or paired-world leakage, host-specific one-bit
  sufficiency, and conflating hard protocol authorization with current task usefulness.

### Claim ceiling and next discriminator

The maximum current-cycle statement is:

> In the enumerated one-authentic-receipt, two-edge R01 host, retaining the bit conditional on the
> stipulated joint verifier acceptance gives immediate return `1`, while a controller forced to
> delete that bit optimally probes for return `1/2`. The same common-mode `1/2` cache advantage
> appears in both labeled live-family slices, the stipulated rule probes in each broken slice, and a
> same-information primitive-history controller can reproduce the rule exactly. This is a
> deterministic verifier-conditional retained-bit use and reacquisition-cost lemma only.

It does not identify authentication benefit, separate owner or lease value, fail-closed task or
safety benefit, representation advantage, learning, MARL, variable membership, variable lifetime,
arbitrary histories, UAV value, or deployment value.

Any next discriminator is a new material cycle, not a repair or continuation of R01. Its smallest
credible object is one matched live-versus-broken lineage pair. It distinguishes old receipt bit
`b_old` from current service bit `b_cur`, sets `b_cur=b_old` while the selected lineage remains
semantically current, and makes `b_cur` conditionally fresh after the break. `PROBE` reveals
`b_cur`. The four exact controls are gated retention, equal-content ungated old-bit use, an
unrestricted exact raw-history optimum, and the bit-deleted reset oracle. This is sufficient to test
whether fail-closed probing aligns with task semantics instead of a policy restriction. A full
owner-by-lease factorial, authentication-invalid cells, and explicit retention/verification costs
are needed only for broader dual-lineage, authentication, or net-value claims. Any learned
comparison would still require a separately measured finite memory, latency, or work distinction
after exact containment.

### Convergence disposition

Fresh conclusion-blind GPT-5.6 Pro Convergence agreed that the fully live `1/2` rule-versus-reset
gap is exact and survives the broken-cell objection. It also agreed that reset and snapshot null are
competent only for their narrow purposes, raw verifier emulation proves functional containment, no
implementation or learned comparison is needed, and the unrestricted raw optimum controls the
semantic claim ceiling.

The following objections are accepted:

- describe the result as verifier-conditional retained-bit use, not semantic conditional
  persistence, because the bit remains present and payoff-correct after a frozen break;
- describe OWNER and SKILL_LEASE as gate-coordinate sensitivity slices of one conjunction, not two
  independent value mechanisms;
- state that authentication is conditioned live, not causally valued;
- distinguish existence of a raw verifier emulator from equality of unrestricted optimal raw
  policies; and
- use the single semantically refreshed live/broken pair above as the smallest next discriminator.

No Convergence objection requires changing R01, reopening observation, or creating CM. The current
claim is narrowed rather than repaired. All unused suggestions are aggregate no-material-change at
this ceiling.

### Engineering and resource sufficiency

No CM was created and no writer transfer occurred. Algebra plus the unchanged deterministic B1
verifier are sufficient for the finite claim ceiling; an implementation or learned run would only
instantiate the frozen truth table and cannot resolve the broken-cell semantic objection. The cycle
used no training, empirical seeds, result command, checkpoint, RNG, or scientific compute.

Pro Innovator transport is `COMPLETE`: strict operation
`5993db47-847e-4b31-a772-5bfb3cf33f78` sent the exact 4,328-byte prompt once in provider conversation
`https://chatgpt.com/c/6a931a46-efb8-83e8-992b-5eb53f53c0fc` under visible `Pro` model evidence. The
13,273-byte naturally completed response is archived at
`temp/directions/dual_epoch_receipt_survival/exp/2026-08-29-lineage-value-gate-01/pro_innovator_response.md`
with SHA-256 `ac855af4200313d74c9dd8a738be934b4c618b452af47f7e666e5f085cbcde54`.

Pro Convergence transport is `COMPLETE`: strict operation
`668d35e4-8fe9-449b-856d-f57b30e8f4d1` sent the exact 5,378-byte prompt once in provider conversation
`https://chatgpt.com/c/6a931e5e-d15c-83e8-a0e3-56abfb1d2820` under visible `Pro` model evidence. The
14,565-byte naturally completed response is archived at
`temp/directions/dual_epoch_receipt_survival/exp/2026-08-29-lineage-value-gate-01/pro_convergence_response.md`
with SHA-256 `9ae6b314dd0636dc1c2473c1bbf8c9fe8b19130a9d3154d450861ce0293b51e0`.
Both mandatory Pro stages are resolved and no provider Effect remains live.

## Frozen evidence provenance

- `docs/research/candidates/dual_epoch_receipt_survival/DUAL_EPOCH_AUTHENTICATED_RECEIPT_SURVIVAL_SCIENCE_CARD.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_B1_SCIENTIFIC_INTAKE.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_PROJECT_ALIGNMENT_ADDENDUM.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_TYPED_LIFECYCLE_ONLINE_CHURN_DISCRIMINATOR.md`
- `docs/research/candidates/dual_epoch_receipt_survival/VNFC_B2_EXTERNAL_PRO_AUTHORITATIVE_RESULT_CLOSURE_INTAKE.md`
- `docs/research/candidates/dual_epoch_receipt_survival/VNFC_B2_SAME_DIRECTION_SCIENTIFIC_RESULT_INTAKE.md`
- `experiments/candidates/dual_epoch_receipt_survival/verifier.py` at the integrated baseline
