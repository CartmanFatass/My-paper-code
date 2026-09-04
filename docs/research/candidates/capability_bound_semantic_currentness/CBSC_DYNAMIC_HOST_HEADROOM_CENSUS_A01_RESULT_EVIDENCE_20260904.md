# CBSC dynamic-host headroom census A01 — result evidence

- Object: `CBSC-DYNAMIC-HOST-HEADROOM-CENSUS-A01`
- Evidence class: **A/RECON**
- Card: `CBSC_DYNAMIC_HOST_HEADROOM_CENSUS_A01_SCIENCE_CARD_20260904.md`
- Corrected card commit: `1be81c2a16e268a8429a6a2d71f46847644363ff`
- Evidence state audited: `bff509952b5e616b08d665db96d8af23e26729b5`
- Completed: `2026-09-04T09:15:28-07:00`
- Validity: **VALID_COMPLETE_READ_ONLY_A_RECON**
- Result branch: **HC-M / CANDIDATE_ASSETS_MISMATCHED**
- Result-bearing invocations: `0`

No environment, learner, optimizer, evaluator, RNG master, checkpoint, scientific run root or
scientific process was created. This is a tracked-evidence availability observation, not an
algorithm-effect result.

## 1. Rule applied verbatim

The card's ordered rule was applied as follows:

1. `HC-X / EVIDENCE_INCOHERENT` only if a named tracked record is unreadable, contradictory, or
   cannot identify the current host/information/action boundary.
2. `HC-A / RAW_HEADROOM_MEASURED` only if both valid values are explicitly designated and matched
   on current host, information, action support, population, native-return units and evaluation
   exposure.
3. `HC-M / CANDIDATE_ASSETS_MISMATCHED` when apparent upper and/or generic candidates exist, but
   every possible pair fails at least one host, population, information, action, objective,
   validity, tuning or exposure match; all current-host numeric fields remain null.
4. `HC-B`, `HC-C`, and `HC-D` distinguish which current-host slot is absent only when the prior
   branches do not apply.

The corrected bound commit is readable and every named record has a coherent role, so HC-X does
not apply. There is no valid matched pair, so HC-A does not apply. Several apparent candidates
exist, but all fail the frozen compatibility requirements. HC-M is therefore the first matching
branch.

## 2. Evidence inventory and receipts

The 12 carded tracked paths were read once from the bound commit:

| evidence | Git blob | role |
| --- | --- | --- |
| `DIRECTION.md` | `f8efa3109103b3c52d9926c17d381b0824228776` | current host, accepted exact/LR01 boundaries, dynamic comparator design |
| `CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md` | `a00c1542c2ae7e6fc97d641fca873e4351dd5714` | valid old-host exact result and RAW containment |
| `CBSC_LR01_RESULT_INTAKE_20260831.md` | `af339c467b5e064423263d870a8331bc17ac7dad` | valid old-host fixed codec/optimizer result |
| `CBSC_OMRC_B01_INNOVATOR_INTAKE_20260901.md` | `246ce17921363d6c2777c6506072556be9c43e91` | selected dynamic host and one-controller boundary |
| `CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md` | `d4b89200f34d8bf2d75212197db4c2fcd0c0b557` | current B exposure and result boundary |
| `CBSC_OMRC_B01_DEFECT8_DECISION_INTAKE_20260904.md` | `8818f4a1f631d6fe66e09c7e772c6894160cd49b` | r01–r05 technical nonpolarity and strongest null |
| `CBSC_OMRC_B01_DEFECT8_TECHNICAL_CLOSURE_INTAKE_20260904.md` | `62301a3f3a597579ebf09087e4afae9d62207560` | engineering closure with no formal result |
| `PORTFOLIO.md` | `d99eb02d3c5e0c75556f09aba9fed71344d91f07` | lifecycle/current-object identity only |
| `RESEARCH_HANDOFF_20260903.md` | `1d10105fde7520c61efd9289bb3e208b323016f6` | attempt inventory and technical history only |
| `omrc_b01/host.py` | `c892a17d680e7f6ea3f511376b96ca3cda1c268f` | dynamic-host event/action/return implementation |
| `omrc_b01/contract.py` | `f3451f0f6cd225781649c2137b08a29b6b3ebff6` | current-host contract/configuration identity |
| `scripts/run_cbsc_omrc_b01_b1.py` | `fb0d24aa266f2729e6b3d5fa259c3a4ca927d92f` | runner identity only; not executed |

No untracked artifact, temporary result root, test artifact, error log, repaired in-memory value or
external direction baseline was admitted. The earlier non-object SHA transcription generated only
`fatal: not a tree object` before any evidence read; the card records its pre-inspection correction.

## 3. Direct observations

### 3.1 Current host and binding structure

`host_status = IDENTIFIED` for `CBSC-DYNAMIC-CACHE-2R-1C-v1`.

The current object is a 24-opportunity, two-receiver, one-controller POMDP. The single recurrent
policy acts under changing public OWNER, semantic, carrier-capability and receiver-body events. The
receivers, persistent slots and carriers are environment entities. Thus
`binding_marl_structure = NONE_IDENTIFIED_ONE_CONTROLLER_POMDP`; the live question is systems /
information flow under partial observation, not an observed multi-agent learner, credit-assignment,
roster-change or partner-co-adaptation bottleneck.

### 3.2 Apparent upper candidates

Two upper-like records were found; neither fills the current-host same-information slot.

1. **Exact `RAW_EXACT_OPTIMUM` on the old one-opportunity protocol.** The valid artifact contains
   6,144 worlds per arm, six arms and 36,864 rows. CBSC is rowwise identical to the unrestricted
   same-primitive RAW optimum. This is a valid upper/containment fact for that exact protocol, not
   for the dynamic 24-opportunity host. It publishes no matched dynamic-host `J_upper`.
2. **The dynamic host's immediate oracle action law.** Current authority states the unique action
   for active-valid, active-invalid and inactive states. The learner does not observe the latent
   validity reduction used to state that rule, and no retained accepted result integrates it over
   the current evaluation population as native return. It is a privileged design reference, not
   the same-information evaluated upper required by A01.

Therefore:

`upper_status = ABSENT_ON_CURRENT_HOST_AS_MATCHED_SAME_INFORMATION_RETURN`.

### 3.3 Apparent generic-baseline candidates

Two generic-like records were found; neither fills the current-host tuned-baseline slot.

1. **LR01 RAW.** `CBSC-LR01` is valid `UNRESOLVED`; four RAW competence blocks reached strict zero
   regret at 512 updates. But it is a full-information offline action-value assay on 24 fixed MAIN
   blocks of a one-opportunity synthetic protocol, using one fixed dense codec/optimizer package.
   It is neither the dynamic host nor a reported tuned `RAW-GRU` selection on its population.
2. **Dynamic `RAW-GRU`.** This is the correct containing same-information comparator family and
   receives the complete primitive stream. The B contract deliberately uses no arm-specific tuning
   and zero model-selection exposure. More importantly, attempts r01–r05 are technical failures;
   no valid current-host B1 result or held-out `J_generic` exists. The defect-8 profile is engineering
   evidence only and does not change this status.

Therefore:

`baseline_status = ABSENT_VALID_TUNED_CURRENT_HOST_RESULT`.

### 3.4 Compatibility and raw quantities

The apparent records fail multiple compatibility axes:

| axis | direct mismatch |
| --- | --- |
| host/population | exact factorial and LR01 use old one-opportunity finite panels; current host has 24 dynamic opportunities. |
| information/objective | LR01 executes exact full-Q offline contexts; current B is recurrent partial-observation PPO on native trajectories. |
| action/timing | old objects do not share the current preamble, event positions, forced `WAIT` timing and delayed settlement population. |
| exposure/evaluation | exact enumeration and LR01's 512-update fixed panel do not match dynamic B1's 48-update recurrent exposure and held-out tapes. |
| tuning/validity | current `RAW-GRU` has no valid result and no reported tuning selection; r01–r05 are technical failures. |

Current-host headroom fields are therefore:

| field | result |
| --- | --- |
| `compatibility_status` | `CANDIDATE_ASSETS_MISMATCHED` |
| `J_upper` | `null` |
| `J_generic` | `null` |
| `G_raw` | `null` |
| units | native return per dynamic-host episode, if later validly measured |

The closest retained raw gap is the old exact protocol's rowwise CBSC-minus-RAW residual of exactly
zero. It remains a representation-containment fact on that old host, not A01 headroom. The accepted
`5/8` capability/currentness/content contrasts, `5/16` OWNER contrast and `1/2` retained-content
contrast are mechanism contrasts against their registered controls, not upper-minus-tuned-generic
headroom. LR01's worst-block STRUCT-minus-RAW value `-0.07509358723958337` is likewise a different
finite-budget codec estimand.

## 4. Counts and result

| census quantity | count or value |
| --- | ---: |
| tracked carded paths read | `12` |
| current scientific hosts identified | `1` |
| apparent upper candidates classified | `2` |
| admissible current-host same-information upper returns | `0` |
| apparent generic candidates classified | `2` |
| valid explicitly tuned current-host generic returns | `0` |
| matched `(J_upper, J_generic)` pairs | `0` |
| computed current-host headroom values | `0` |
| valid current-host B1 scientific results | `0` |
| new seeds / episodes / transitions / updates / evaluations | `0 / 0 / 0 / 0 / 0` |

The first applicable branch is:

> **HC-M / CANDIDATE_ASSETS_MISMATCHED**

No MEI, percentage, sign, mechanism polarity, B admission, lifecycle mapping or cross-direction
fusion is applied.

## 5. Integrity, usage and deviations

- Scientific/numerical/RNG/checkpoint semantics: unchanged and read-only.
- New learner exposure and parameter displacement: zero; initialization scale and ratio `N/A`.
- Result's own compute: `0` result-bearing machine seconds; local control-plane document/Git
  inspection wall and peak RSS were not instrumented because no run exists.
- Accepted-attempt compute divided by valid results for this A01 object: `0 / 1 = 0`
  result-bearing machine seconds; node `local_windows`, device `N/A`.
- Resource admission and `resources_unmeasured`: not applicable; no scientific invocation or run
  exists.
- Sweep/per-arm projection: none.
- Engineering scope additions and section-5 budget breaches: none.
- Card deviations after the recorded pre-inspection locator correction: none.

## 6. Bounded reading

Direct observation: the repository has strong but non-composable older-host evidence and a correct
dynamic comparator design, yet no valid matched current-host upper/tuned-generic return pair.

Inference under the card definitions: current dynamic-host headroom is **not identified**. It is not
zero, negative, below an MEI, or evidence against the currentness mechanism. The strongest support
for the result is the explicit host/object mismatch plus the direct technical status of every
dynamic B1 attempt. The strongest contrary-looking fact is exact RAW containment on the old host;
it limits representation claims there but cannot supply either dynamic numeric term.

Claim ceiling: a tracked-evidence availability and compatibility fact at the bound state only. This
result cannot authorize a learner, B, `r06`, PARK, CLOSE, fusion, priority, investment, transfer or
deployment claim.
