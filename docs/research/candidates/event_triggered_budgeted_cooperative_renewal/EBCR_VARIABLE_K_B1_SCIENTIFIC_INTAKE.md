# EBCR variable-k B1 scientific intake

Direction: `direction:event_triggered_budgeted_cooperative_renewal`  
Candidate: `CAND-EVENT-TRIGGERED-BUDGETED-COOPERATIVE-RENEWAL`  
Treatment: `EBCR-B1-VARIABLE-K-COOPERATIVE-RENEWAL-v1`  
Result: `docs/research/candidates/event_triggered_budgeted_cooperative_renewal/EBCR_VARIABLE_K_B1_RESULT.json`

## Conclusion and outcome branch

The exact B1 learned treatments do not support the project-level variable-`k`
claim. Validation selected `FIXED-4`. Both learned arms were worse than that
fixed policy on mean performance and worst-cell robustness, with every paired
95% interval entirely below zero:

| Contrast | Mean `P` [95% CI] | Mean `W` [95% CI] |
|---|---:|---:|
| `COORD - FIXED-BEST` | `-0.006067 [-0.009162,-0.002972]` | `-0.074744 [-0.084681,-0.064806]` |
| `LOCAL - FIXED-BEST` | `-0.076108 [-0.079178,-0.073037]` | `-0.129124 [-0.137283,-0.120966]` |

This is the registered branch in which neither adaptive arm nor the registered
`STAGE-ORACLE` beats the fixed comparator. It is not a near miss under the
positive benefit thresholds: the effects have the wrong sign. Do not repeat
B1, add seeds, tune a threshold, enlarge the PPO learner, or progress this
treatment to the continuous/UAV surface.

`COORD` nevertheless produced a large, precisely separated advantage over
`LOCAL`:

- `P`: `+0.070041 [0.064796,0.075285]`;
- `W`: `+0.054381 [0.045949,0.062813]`; and
- the registered ON-minus-OFF coupling interaction was
  `+0.005425 [0.001189,0.009660]`.

That supports a narrower descriptive conclusion: partner-bit access plus the
coordinated pending/execution protocol materially changed the learned closed-
loop bundle and mitigated the failure of the local learned hazard, with a
slightly larger advantage during joint changes. It does not support a useful
variable-`k` algorithm, event-aligned timing, or a positive same-information
joint-execution mechanism.

## Technical-result boundary

CM technically accepted one complete result: exit code zero, question-relevant
activity reached, all six registered seeds, `4,723,584` team ticks, one CPU
worker, and `924.866` wall seconds. Those facts are inputs to this scientific
interpretation, not rechecked here.

`actual_budgets.peak_rss_bytes=0` means peak RSS was not continuously measured
because `psutil` was absent; it is not a literal zero-memory observation. Live
samples of roughly `360--433 MiB` were below the `2 GiB` cap, but they are not a
peak guarantee. This is a technical resource-measurement limitation only. It
does not select an outcome branch or motivate another activity-started run.

## What B1 supports, contradicts, and leaves unidentified

### Variable-k mean performance

Contradicted for both registered learned arms. The required effect was a
positive 95% lower bound and mean improvement of at least `0.02`; `COORD` was
`0.006067` below `FIXED-4`, and `LOCAL` was `0.076108` below it. One policy was
indeed trained across duration regimes and produced varying realized periods,
but varying `k` is not valuable merely because it occurred. The required task-
performance benefit did not occur.

Descriptively, `COORD` exceeded `FIXED-4` in the two ID cells, both LONG cells,
and `MIXED_NOISY_OFF`, but lost in `MIXED_NOISY_ON` and both SHORT cells. Its
worst cell was `SHORT_ON`, where mean return was `0.341619` versus `0.416362`
for `FIXED-4`. This tempo-specific pattern explains why favorable cells do not
support the equally weighted registered estimand.

The nondeployable test-cell hindsight fixed-grid envelope had mean `P` about
`0.592692`, versus `0.555134` for validation-selected `FIXED-4`: `k=8` was
descriptively best in ID, LONG, and `MIXED_NOISY_OFF`; `k=16` in
`MIXED_NOISY_ON`; and `k=4` in SHORT. This shows cell-label-dependent fixed
period headroom, not information available to the deployed actor and not an
adaptive-policy result.

### Variable-k robustness

Contradicted for both arms. The required effect was a positive lower bound and
mean improvement of at least `0.03`; `COORD` was `0.074744` below `FIXED-4`
and `LOCAL` was `0.129124` below it on `W`. The hindsight fixed-grid envelope
improved mean seed-level `W` only descriptively, from about `0.416362` to
`0.420934`, far below the registered robustness margin and with access to the
test cell. There is no B1 robustness claim.

### Coordination

Supported only as a bundle-level contrast against `LOCAL`. `COORD` improved
both `P` and `W`, and the positive coupling interaction is consistent with the
partner channel being more useful when both latent requirements change.

The stronger cooperative-renewal claim is not supported because all of its
essential conditions fail or remain unidentified:

1. `COORD` did not satisfy either variable-`k` benefit statement.
2. The YOKED performance separation was only
   `+0.005557 [0.003035,0.008080]`, below the registered `0.01` mean margin;
   its robustness separation was
   `+0.004329 [-0.003033,0.011691]`.
3. Primary YOKED eligibility averaged `0.855469` and reached a minimum of
   `0.765625`, below the required `0.90` in every cell.
4. Complete all-control safety coverage was unavailable because some replay
   schedules were ineligible.

The pre-result Pro proof now fixes the interpretation ceiling. Under the
conjunctive packet reward and additive per-agent renewal cost, delaying an
earlier local renewal until the later local renewal cannot create positive
joint-change execution surplus: at the later execution time it is equivalent,
and any further wait is harmful. Thus `COORD-LOCAL` combines partner
information, changes to sampled requests, observation accumulation, readiness
synchronization, and the execution transducer. It is not a same-information
execution estimand.

### Timing and schedule controls

`COORD` strongly exceeded `COORD-SHUFFLE`:

- `P`: `+0.071328 [0.066486,0.076170]`;
- `W`: `+0.073944 [0.065540,0.082348]`.

SHUFFLE had 100% primary eligibility, so the exact observed schedules were
better than per-agent period permutations. But the permutation also changes
singleton-versus-simultaneous renewal packing and the relation of execution to
readiness. This contrast supports schedule organization, not uniquely task-
event alignment.

YOKED almost reproduced `COORD` performance on its eligible subset. Its small
`P` separation missed the registered effect margin, its `W` interval crossed
zero, and its eligibility condition failed. The missing rows were not random
proof of equivalence, so the control cannot establish a null. Taken together,
the timing evidence is non-identifying for event alignment and strongly
consistent with the frequency/period/readiness/packing alternative.

### Safety

Every actually complete safety arm/cell had emergency-immediate rate `1` and
zero cap violations. This supports the implemented unilateral emergency
override on the observed complete panel: no observed emergency waited for a
pair and no observed arm exceeded its renewal cap.

The result's 74 safety-failure records all denote incomplete SHUFFLE/YOKED
coverage caused by schedule ineligibility; none records a delayed observed
emergency or a cap violation. Therefore the correct conclusion is neither
"74 unsafe events" nor complete all-arm safety. Immediate override behavior is
supported for complete cells, while the registered across-all-controls safety
condition and the complete cooperative claim remain unavailable.

No toy result establishes hard UAV safety, flight-envelope safety, or safety
outside the injected single-event override.

### Hazard credit and optimization

Question-relevant learning activity was nonvacuous. Both learned arms completed
the registered PPO updates and emitted policy-eligible request records; the
failure is not an unstarted learner or a zero-request hazard.

Across seeds, training request rates remained roughly `0.46--0.57`, and
role-level hazard entropy remained close to the Bernoulli maximum
`ln(2) = 0.693`. The learned policies therefore remained high-entropy and
frequently requested renewal rather than becoming sharply selective. In the
primary panel, `LOCAL` had renewal downtime about `0.3210`, while `COORD` had
about `0.2149`; simultaneous-renewal rates were about `0.0327` and `0.1164`,
respectively. `COORD` also used slightly less mean renewal cost
(`0.8481` versus `0.9056`) while having slightly higher stale-tick rate
(`0.2688` versus `0.2649`). These diagnostics are consistent with request
packing and transducer-induced renewal suppression accounting for much of the
`COORD-LOCAL` advantage.

They do not distinguish a second-order credit barrier from an uninformative
target action or an insufficient observation statistic. B1 contains no
common-randomness `Q00,Q10,Q01,Q11` action-value table, no same-information
execution arm, and no allowed-information Bayes headroom object. A centralized
critic and ordinary request-time GAE did not produce a valuable adaptive arm,
but that fact alone neither proves nor refutes the proposed EGRCR credit route.

## Strongest surviving alternative explanation

The most economical explanation of all observed B1 contrasts is:

1. the hazards remained high-entropy frequent request generators;
2. the `COORD` transducer converted those requests into fewer occupied renewal
   ticks and more simultaneous events than `LOCAL`;
3. live partner readiness/request bits and native timing reduced nonready
   execution relative to shuffled or foreign schedules; and
4. these packing and information effects rescued much of `LOCAL`'s loss but
   did not beat the aggressive `FIXED-4` schedule, especially under SHORT
   phases.

This explanation needs no useful task-event detector, scarce-budget shadow
price, positive pure joint-execution surplus, or special credit routing. The
data do not eliminate better observation accumulation before majority skill
instantiation, partner invalidation as an extra sensor, or a real but too-small
event-alignment effect. They do eliminate the registered variable-`k` benefit
claim and leave those mechanisms unidentified rather than established.

The readiness shortcut identified before the result is not an explanation for
a nonexistent adaptive-over-fixed benefit. In fact, `FIXED-4` renewed while
ready less often and paid much more nonready-renewal cost than the adaptive
arms, yet still won. Readiness matching remains necessary in any future design,
but it cannot reverse the B1 conclusion post hoc.

The ordinary budget also did not establish scarce-resource allocation. Its cap
was large enough to admit `k=4`; the result cannot attribute behavior to a
learned token shadow price.

## Registered oracle and residual headroom

`STAGE-ORACLE` was worse than `FIXED-4` (`P=0.368138`, `W=0.137603`). Under the
registered card this joins the no-adaptive/no-oracle branch and forbids learner
enlargement.

It does not prove that the host lacks all variable-timing headroom. As fixed
before seeing B1, the earliest-boundary oracle can instantiate an old
majority-of-three skill immediately after a phase change. It is not a
content-aware upper bound. The hindsight fixed-grid envelope likewise shows
that different fixed periods suit different test cells, but it sees the hidden
cell identity. Hence the residual unknown is whether the actual decentralized
observation interface contains usable prospective information about the
renew-now advantage. That unknown cannot rescue B1 and is not a reason for
another full learner run.

## EGRCR consequence and highest-information next discriminator

There is no same-direction EBCR-B2 treatment or CM construction request from
this intake. The current EBCR coordinator and learned hazard have exhausted
their registered test, and a repeat or larger end-to-end learner would not
separate the surviving explanations.

The highest-information next discriminator belongs to the already separate
`direction:expressibility_gated_renewal_credit_relay`. B1 changes that
hypothesis in one essential way:

> `COORD-LOCAL > 0` cannot be used as evidence that the current pair-closing
> request has positive interaction value or that missing cross-record credit
> caused B1's project-level failure.

EGRCR must first establish, on a new prospectively defined microtoy and common
exogenous tape, all three links:

1. **target action value:** for a qualified ordered waiter/joiner event,
   the four-splice interaction
   `kappa=(Y11-Y10)-(Y01-Y00)` is nonzero with useful signed variation, and the
   waiter request changes bounded downstream utility;
2. **target expressibility/exposure:** the proposed update changes the intended
   waiter request probability on held-out states and that changed request is
   actually executed before the bounded consequence endpoint; and
3. **association-specific learning value:** intact later-joiner-to-true-waiter
   routing improves over both ordinary GAE and a conserved, optimizer-matched
   binding derangement, with the advantage disappearing under an independently
   yoked partner association.

If target action value fails, current pair-closing credit is scientifically
empty and the relay is deleted. If action value exists but target behavior
cannot change or reach the outcome, repair expressibility/exposure before any
binding claim. If intact routing does not beat ordinary GAE and the binding cut,
delete association-specific relay. Only all three positive links justify a new
end-to-end once-trained variable-`k` algorithm comparison; that later comparison
must use readiness-matched fixed/adaptive controls and cannot reuse B1's
`COORD-LOCAL` effect as evidence or a threshold.

The target mechanism should be a request that can advance a weak but compatible
partner decision or otherwise has demonstrated positive counterfactual value,
not the current protocol's mere delay of an earlier strong request for
simultaneity. This is a change in the EGRCR hypothesis target, not transferred
evidence or an EGRCR result.

Because the EGRCR scientific owner is already active, this EBCR owner does not
author a competing CM card. Root should relay the above B1 constraint to that
owner and await its independently frozen microtoy. No EBCR CM handoff is
prepared.

## Claim ceiling

The strongest supported positive statement is:

> In the registered constructed two-agent binary-skill exogenous-switch host,
> with the six final learned checkpoints and matched declared interaction and
> communication budgets, the complete partner-informed coordinated bundle
> materially outperformed the separately trained local learned bundle and its
> per-agent period-shuffled replay; its relative advantage was slightly larger
> in joint-change cells.

The strongest supported negative statement is:

> In the same finite host, seeds, training budget, PPO credit rule, feature set,
> renewal envelope, costs, and eight-cell panel, neither learned adaptive arm
> improved mean performance or worst-cell robustness over validation-selected
> `FIXED-4`; both were worse, and the registered earliest-event oracle was also
> worse.

B1 does not identify useful event timing, same-information cooperative
execution, task-evidence value beyond age/readiness/budget scheduling, a scarce-
budget mechanism, an EGRCR credit failure, or safety over incomplete replay
controls. It supports no continuous-control or UAV claim, no arbitrary skill
library or variable-`N` claim, and no conclusion about other adaptive-duration
mechanisms, corrected content-aware oracles, stronger observation summaries, or
prospectively different corroboration protocols.

## Exact Root portfolio relay

Root should remove the exact EBCR-B1 learned algorithm from further algorithm
investment and should not advance it to the UAV bridge. Retain only two bounded
research facts: the large coordination-bundle-versus-local separation and the
unresolved allowed-information/credit question. Do not treat either as project
value.

The only immediate answer-changing continuation is the separate EGRCR
expressibility/exposure/action-value gate described above. Reconsider an
end-to-end variable-`k` successor only if that gate and association-specific
learning test succeed, or if an independently motivated content-aware,
allowed-information headroom discriminator demonstrates usable renewal value.
Otherwise the revisit condition is not met.
