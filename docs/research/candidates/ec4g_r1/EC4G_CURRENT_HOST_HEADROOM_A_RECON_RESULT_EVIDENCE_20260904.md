# EC4G current-host headroom evidence census R01 — result evidence

- Object: `EC4G-A-RECON-CURRENT-HOST-HEADROOM-CENSUS-R01`
- Evidence class: **A/RECON**
- Card:
  `docs/research/candidates/ec4g_r1/EC4G_CURRENT_HOST_HEADROOM_A_RECON_SCIENCE_CARD_20260904.md`
- Observation completed: `2026-09-04T07:06:09-07:00`
- Repository HEAD inspected: `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`
- Validity: **VALID_COMPLETE_READ_ONLY_A_RECON**
- Result branch: **HC-N / HEADROOM_NOT_IDENTIFIED**
- Result-bearing invocations: `0`

## 1. Rule applied verbatim

> Use `HC-X / NO_OBSERVATION` only if the named tracked bytes cannot be read, the current host
> cannot be identified from current authority plus retained source, or the evidence inspection is
> incomplete.
>
> Use `HC-N / HEADROOM_NOT_IDENTIFIED` if the host is identified but the upper, the technically
> valid explicitly tuned generic baseline, or their host/information/population/evaluation
> compatibility is absent. Emit each missing status and set `J_upper = null`, `J_generic = null`,
> and `Delta_H = null`.
>
> Use `HC-M / RAW_HEADROOM_MEASURED` only when both valid values and all compatibility fields are
> present. Emit the two direct raw values, their units, and `Delta_H = J_upper - J_generic` without
> applying any unratified MEI or closure share.

All named bytes were readable and the current host was identifiable, so HC-X does not apply. The
accepted upper-reference slot and technically valid explicitly tuned generic-baseline slot are both
unfilled. HC-N therefore applies before any subtraction.

## 2. Evidence inventory and receipts

Primary inventory: 11 tracked paths, read once.

| evidence | receipt or directly read field | use |
| --- | --- | --- |
| `DIRECTION.md` | Git blob `40e136712712a3c0a495ee9fc990e92f76cf9604` | current scientific position and provenance boundary |
| `CODE_SCIENCE_INDEX.md` | registered A1/A2/A3 descriptions | older binding/census evidence; no native-return headroom |
| `EC4G_A5_CODE_SCIENCE_INDEX.md` | Git blob `f83753bd88b8db608565e3f912079621e71c5b67` | retained `D_RER3=1/4`, explicitly non-value |
| `EC4G_A5_PORTABLE_SOURCE_BOUND_TWO_PHASE_EXECUTION_CENSUS_RESULT.json` | retained A5 result | structural map/program census only |
| `EC4G_B1_CODE_SCIENCE_INDEX.md` | Git blob `24beea600d49f66c7bd4e607ff1df42acb7bcbe0` | B1 acceptance boundary and invalid publication branch |
| `EC4G_B1_LEAVE_RECEIPT_CONTENT_LEARNING_DISCRIMINATOR_RESULT.json` | Git blob `9a1a9a2b836b52be05ccfa44c1e8fc99416f873f`; file SHA-256 `4e0608ce4257a5338b3c57d2be3721f33b6b239657fdfde9c630e975c2c18065` | retained manifest, raw fields, invalid branch |
| `EC4G_RER3_COMPLETE_CONTRACT_V1.json` | `epistemic_status = finite oracle fixture truth, not empirical measurement` | excludes the fixture from the upper slot |
| `experiments/candidates/ec4g_r1/leave_receipt_content_learning_discriminator.py` | Git blob `d59704e14c836e055c56f25de6708edff10677f6` at both B1 source revision and current HEAD | exact current-host definition |
| `scripts/run_ec4g_b1_leave_receipt_content_learning_discriminator.py` | byte-diff empty between B1 source revision and current HEAD | runner/provenance context only |
| `docs/research/portfolio/PORTFOLIO.md` | current row names repaired B1 activity aggregation and continuation of dynamic receipt-content learning | identifies current object family; no science imported |
| `docs/research/portfolio/decisions/2026-09-01-empirical-standard-full-direction-reaudit.md` | current B family names Direct-tau, RAW, shuffled, and blinded controls | shows RAW is planned as a control, not a retained valid upper/baseline result |

Two contrary, different-population provenance paths were also read:
`docs/research/legacy/directions/dual_epoch_receipt_survival/DIRECTION.md` and
`DEARS_ONLINE_CARRIER_VALUE_GATE_R01.md`. They were not admitted as either EC4G term.

No untracked file, temporary run root, error log, or repaired in-memory value was used.

## 3. Direct observations

### 3.1 Current host is identified

`current_host_status = IDENTIFIED`.

The current source defines `FourStepRelayHost`: four transitions, one `a2` leave event, one probe
opportunity, `q0/q1`, seven receipt/physical/sham arms, two surviving terminal actions, and native
reward `1[all executed bits equal z] - .02*1[physical probe]`. The source blob is unchanged between
the registered B1 revision and current HEAD.

### 3.2 Accepted upper headroom reference is absent

`upper_reference_status = ABSENT_AS_ACCEPTED_HEADROOM_REFERENCE`.

The retained RER3 contract calls its table a finite oracle fixture rather than an empirical
measurement. A5 reports `D_RER3=1/4` from one unequal leave program pair, but records zero
environment, evaluation, model-fit, or learner activity and explicitly disclaims reward or return
value. B1 source contains an `analytic_counterexample()` fixture and a constructive
representability certificate; neither is named, evaluated, or accepted as `RAW-BAYES-EXACT` or as
a headroom upper on the autonomous population. No retained direction evidence publishes a valid
`J_upper` under the card's information and population boundary.

### 3.3 Technically valid explicitly tuned generic baseline is absent

`tuned_generic_baseline_status = ABSENT`.

The B1 manifest contains exactly one fixed learner configuration:

- shared GRU/A2C, hidden size 32;
- Adam learning rate `0.003`;
- entropy coefficient `0.01`, value coefficient `0.5`, gradient cap `1.0`;
- 128 updates and 1,792 training episodes per replica;
- eight outer seeds and two pre-gate-identical treatment replicas.

It contains no configuration roster, hyperparameter comparison, tuning objective, selection rule,
or selected-from-many baseline. Initial-to-final parameter displacement relative to initialization
scale is not published as a baseline field.

More importantly, the retained result branch is
`B1_ACTIVITY_OR_EVALUATION_PANEL_INCOMPLETE`; its own metric field is
`activity_complete=false`. The B1 index records that the code result is not accepted because the
activity aggregation omits the treatment-level registered-full count. A hypothetical one-line
mechanical correction is not a valid fresh observation and was not applied.

### 3.4 Compatibility and raw gap

Because both required values are absent:

| field | result |
| --- | --- |
| `compatibility_status` | `NOT_EVALUABLE_REQUIRED_TERMS_ABSENT` |
| `J_upper` | `null` |
| `J_generic` | `null` |
| `Delta_H` | `null` |
| units | native return per B1 episode, if later validly measured |

No percentage, sign, MEI comparison, or closure share was computed.

## 4. Forbidden substitutes retained as contrary observations

The invalid B1 artifact contains raw `delta_j=-0.007578125000000359`, top-level
`registered_paired_fulls=1`, and nonzero learner/evaluation counts. That scalar compares EC4G and
Direct-tau autonomous gates after the fixed learner; it is neither upper-minus-generic headroom nor
a valid scientific result from the incomplete publication. It was read only to verify why it must
not be substituted.

A5's `D_RER3=1/4` is the strongest structural support that receipt-content gating can change the
compiled leave program on the frozen three-cell fixture. Its explicit contradiction is that the
same artifact has no return evaluation and disclaims value; it cannot populate either headroom
term.

DEARS provides the strongest surviving simpler explanation on a different host: an exact
same-information primitive-history controller can reproduce the gated rule, and the retained-bit
advantage is a stipulated cache-versus-reacquisition fact rather than representation or MARL value.
This limits enthusiasm for EC4G but does not transfer a number or polarity to the B1 host.

## 5. Counts, exposure, resources, and deviations

| quantity | count/status |
| --- | ---: |
| primary tracked evidence paths inspected | 11 |
| contrary provenance paths inspected | 2 |
| result-bearing invocations | 0 |
| environment transitions / episodes | 0 / 0 |
| learner / trainer / optimizer calls | 0 / 0 / 0 |
| parameter initializations / displacements | 0 / 0 |
| checkpoints / model selections | 0 / 0 |
| RNG draws | 0 |
| result roots / side effects outside these documents | 0 |
| resource preflight | not applicable; no result-bearing invocation |
| resource telemetry | not applicable |
| section 4 engineering-scope machinery added | none |
| section 5 budget breach | none |
| deviations from card | none |

The evidence inspection was performed on the local control plane because it was a short read-only
document audit. It did not create scientific state, so remote result routing and memory admission
were not invoked.

## 6. Bounded reading

The only positive A/RECON claim is that the current B1 host is identifiable from unchanged tracked
source. The headroom gap itself is not identified because no accepted upper and no valid explicitly
tuned generic baseline are on record. `Delta_H=null` is an evidence-availability fact, not an
algorithm result or a zero-headroom finding.

For the Portfolio-wide A1 aggregate, the exact row is:

| direction | current host | binding MARL structure | upper | tuned generic baseline | raw gap | branch | result-bearing usage |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `ec4g_r1` | B1 `FourStepRelayHost` | `NONE_IDENTIFIED`; receipt-content information flow on a single-leave host | absent as accepted headroom reference | absent; B1 is fixed and invalid | `null` | `HC-N / HEADROOM_NOT_IDENTIFIED` | 0 |
