# UCOPE contextual paid acquisition R01 BELIEF result intake — 2026-08-31

## Disposition

```text
RESULT_FORMAT=UCOPE_CPA_COMPLETE_BELIEF_RESULT_V2
TECHNICAL_VALID=true
COMPLETE=true
FIXED_PANEL_DISPOSITION=STOP_FIXED_PANEL_COMPETENCE
COMPETENT_SEED_COUNT=0/10
COMPETENCE_PASS=false
ACQUISITION_ALL_FLIPS=false
ACQUISITION_PASS=false
REPRESENTATION_CONCLUSION=NONE
COUNT_RAW_ELIGIBLE=false
```

The immutable source is
`temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/result/belief-result.json`
(`2,924,419` bytes). The package result validator accepts it without opening checkpoint tensors.
It contains all ten result-eligible checkpoint records at `640/640` batches and updates, exactly
6,400 optimizer updates total, the complete production support record with minimum displayed count
`361>=256`, and complete held-out evaluation.

## First controlling branch

No contract, resource, support, checkpoint, resume, completeness, or score-uniqueness invalidity
precedes interpretation. The first failure is competence. Every seed fails all three substantive
competence predicates:

| Seed | Maximum regret | Minimum tail agreement | Root-vector summary |
| --- | ---: | ---: | --- |
| `00` | `0.0779428825` | `0.47927328125` | extra LINKED probes and target missed |
| `01` | `0.02143710125` | `0.52072671875` | target missed |
| `02` | `0.02143710125` | `0.52072671875` | target missed |
| `03` | `0.06143710125` | `0.52072671875` | target missed |
| `04` | `0.07412327125` | `0.52072671875` | three extra LINKED probes |
| `05` | `0.02143710125` | `0` | target missed |
| `06` | `0.07060866925` | `0.52072671875` | three extra LINKED probes |
| `07` | `0.02143710125` | `0` | target missed |
| `08` | `0.03310330375` | `0.52072671875` | two extra LINKED probes |
| `09` | `0.03171827125` | `0.611558515625` | one extra LINKED probe |

Every learned root vector differs from the oracle target-only PROBE vector, every maximum regret is
strictly above `0.02`, and every minimum forced-PROBE tail agreement is below `0.95`. Root and tail
choices are finite and unique in every seed, so ties are not the explanation.

## Interpretation and claim ceiling

All 80 downstream signed specificity margins are positive, with exact panel minimum
`12190847/800000000 = 0.01523855875`. This does not rescue the earlier competence branch. Positive
forced-PROBE value signs did not produce competent tail policies or correct endogenous contextual
probing.

The artifact ceiling is
`TEN_FIXED_SEED_SLOTS_FINITE_HOST_ONLY_NO_SEED_SUPERPOPULATION`. The realized supported statement is
only that this exact shared BELIEF fitted-Q learner and budget failed competence in every registered
seed despite complete support. The result does not establish that paid acquisition is valueless,
that BELIEF is generally unlearnable, or that COUNT and RAW are equivalent.

COUNT/RAW is ineligible because entry required both BELIEF competence and acquisition support. Do
not add episodes, replace or drop seeds, select checkpoints, retune, enlarge the budget, or rerun.

## Lifecycle recommendation and provenance

Root accepted the direction-level recommendation: close this exact contextual BELIEF v2 object and
move UCOPE from `ACTIVE/HIGH` to `PARKED/MEDIUM`. Reopen only for a new prospectively frozen
competence-first learner with an independently justified optimizer or representation change.

This result is distinct from historical R03. R03 terminated at support failure and supplied no
competence or acquisition polarity; contextual BELIEF v2 cleared support and then failed
competence. Neither object supplies COUNT/RAW polarity. The Portfolio snapshot remains Root-owned
and was not edited in this intake.
