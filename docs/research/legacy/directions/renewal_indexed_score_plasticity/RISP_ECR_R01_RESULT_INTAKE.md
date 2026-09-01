# RISP-ECR revision-01 exact-certificate result intake

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-ECR-R01
spec_schema=RISP-ECR-R01-SPEC-V1
result_schema=RISP-ECR-R01-COMPLETE-RESULT-V1
complete_census=true
technical_acceptance=true
result_status=CERTIFIED_RENEWAL_INDEXED_BAYES_WITNESS
scientific_disposition=EXACT_EVENT_AND_DURATION_ORDER_ACTION_RELEVANCE_CERTIFIED
registered_rerun_authorized=false
learned_successor_authorized=false
```

## Conclusion

The complete registered four-history census certifies the exact fixed-host witness. `RAW_HISTORY_BAYES`
and `FULL_BAYES_K` agree rowwise in posterior, unique action, and value. With the same final
`(LEFT,+,4)` packet and next `k=4`, changing only the older ACK changes the next Bayes action from
`CENTER` to `LEFT`. With the same ordered actions/ACKs, final `(LEFT,+,8)` packet, current time, and
next `k=4`, changing completed-duration order from `[4,4,12,8]` to `[4,12,4,8]` changes the next
Bayes action from `LEFT` to `CENTER`.

All registered histories have positive exact reachability mass, every controller action is unique,
all clock/utility/endpoint checks reconcile, and the GMP/MSVC native path equals the independent
exact reference on every row. Every recorded acceptance predicate is true.

## Exact comparator separation

The coarsened controllers lose native value exactly where their views collapse opposite Bayes
actions:

| Twin population | Controller | Equal-weight regret |
| --- | --- | ---: |
| prior-history ACK twin | `LAST_ACK_BAYES` | `73401104971125/272847556550656` |
| prior-history ACK twin | `LAST_ACK_G` | `73401104971125/272847556550656` |
| duration-order twin | `FULL_BAYES_K_ERASED` | `192318334346022512147468038785375/14619768228815627885315182344200192` |
| duration-order twin | `LAST_ACK_BAYES` | `192318334346022512147468038785375/14619768228815627885315182344200192` |
| duration-order twin | `LAST_ACK_G` | `192318334346022512147468038785375/14619768228815627885315182344200192` |

`LAST_ACK_G` chooses `LEFT` on all four registered rows and therefore misses the `CENTER` side of
both twin populations. The result identifies event-conditioned Bayesian recurrence and duration
order, not a privileged learned `G` initialization.

## Claim ceiling

The maximum positive claim is exact fixed-host evidence that older public outcome history and
completed-duration order change the next native action and value beyond duration-erased and
last-ACK views. The certificate establishes existence on the frozen equal-weight reachable twins;
it does not establish natural prevalence, learned advantage, initialization benefit, arbitrary
`k`, coordination, variable population, UAV transfer, safety, or deployment value. The exact
controller is a zero-learning oracle, so this result supplies no finite-resource learnability or
optimization conclusion.

## Direction recommendation and next discriminator

Direction-local recommendation to Root: close RISP-ECR-R01 as a successful complete object and park
standalone RISP rather than rerun it or immediately fund a learned panel. APFI is not needed to
rescue this host because the exact low-order Bayes control already crosses native action boundaries.

The next scientifically nonredundant question is witness-independent prevalence: under a
prospectively frozen distribution over duration schedules and reachable public histories, what
exact probability mass and expected regret lie on decision points where full Bayes differs from
duration-erased or last-ACK control? The distribution and any materiality floor must be frozen
before enumeration. Material prevalence would make one separately frozen finite-resource
approximation comparison eligible; negligible prevalence would close standalone RISP while
retaining this certificate as a constructive theorem/control.

## Evidence locator

- Complete result: `temp/directions/renewal_indexed_score_plasticity/exp/r01_registered_20260830_result/RISP_ECR_R01_COMPLETE.json`
- Runtime: `3.671888899989426` seconds; peak RSS: `25,137,152` bytes; one CPU thread; zero scientific RNG draws.
