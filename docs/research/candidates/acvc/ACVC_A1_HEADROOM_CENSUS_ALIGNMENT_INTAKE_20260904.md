# ACVC A1 headroom-census alignment intake

- Direction: **acvc**
- Tier: **object**
- Action source: **Root instruction 2026-09-04 applying MARL_EXPLORATION_GUIDANCE_20260904 §3 A1**
- Current object inspected: **ACVC-A-RECON-HISTORY-HEADROOM-CERTIFICATE-R02**
- A1 status: **NOT DONE / MINIMAL DIFFERENCE FOLLOW-UP FROZEN**
- Scientific launches caused by this intake: **0**

## Question checked

Does the current exact R02 history-headroom certificate already implement the A1 census quantity

> same host, same-information upper reference minus tuned generic baseline

so that ACVC may be marked A1 done after its result and its raw gap recorded without applying an
unapproved minimum-effect threshold?

## Direct contract comparison

| A1 requirement | R02 fact | Satisfied |
| --- | --- | --- |
| Same current host | R02 retains the unchanged twelve-opportunity uncertain/delayed R01 host. | yes |
| Upper reference uses the same receiver information | REGIME-ORACLE-ENVELOPE additionally observes the hidden episode regime. It is explicitly certificate-only extra information and cannot be a legal treatment or comparator. | **no** |
| Comparator is a tuned generic baseline | R02 compares against unchanged DET-CF, a competent fixed model-based rule. It is not a tuned generic learner or a prospectively selected generic baseline set. | **no** |
| No new learner inside the census | R02 has no learner. | yes |
| Raw gap can be reported without an MEI decision | R02 will report exact ΔL and ΔU, but neither is the required same-information-upper minus tuned-generic quantity. | **no** |

The legal HIST-1UPDATE-CF lower witness does use the receiver's allowed information, but the
provider decision deliberately defines it as a restricted lower certificate, not an upper
reference. Relabelling it as an upper reference would change the frozen meaning. The earlier
RAW-GRU result is a single fixed R01 learner configuration, not a tuned generic baseline set, and
R02 does not compare against it.

## Bounded conclusion

R02 does **not** satisfy the ratified A1 aggregation definition. Its eventual exact result remains
valid for its frozen HC question, but it cannot be entered as the A1 raw headroom gap. ACVC remains
A1 not done even after R02 completes unless a separate same-information/tuned-baseline census
result is accepted.

This alignment finding does not alter R02's treatment, DET-CF comparator, oracle certificate,
result branches, lifecycle, launch, or direction conclusion. It supplies no HC branch and no
scientific polarity.

The recommended 5% headroom floor and 25% mechanism-closure share remain unratified owner choices.
This intake applies neither threshold, emits no MEI classification, and authorizes no B object.

## Object-tier options and recommendation

Options:

1. Count R02 after completion using ΔU=JU−JD. This would treat privileged-regime oracle information
   as same information and DET-CF as a tuned generic baseline.
2. Count R02 after completion using ΔL=JL−JD. This would relabel a deliberately restricted lower
   witness as the upper reference and still treat DET-CF as tuned generic.
3. Do not count R02 as A1; preserve it unchanged and freeze the smallest separate A/RECON
   difference item requiring both a legal same-information upper reference and an independently
   frozen tuned generic baseline on the same host.

Recommendation: **(3)**. Options (1) and (2) silently change the information or comparator meaning
of a live frozen object. Option (3) is reversible, creates no run, and records exactly what the
Portfolio-wide census still lacks.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (3).**

The frozen follow-up item is
[ACVC_A1_SAME_INFORMATION_TUNED_BASELINE_GAP_A_RECON_FOLLOWUP_20260904.md](ACVC_A1_SAME_INFORMATION_TUNED_BASELINE_GAP_A_RECON_FOLLOWUP_20260904.md).
It is dependency-blocked and authorizes no implementation or result invocation.

## Portfolio aggregation fields

| field | value |
| --- | --- |
| direction_id | acvc |
| census_action | A1 |
| current_object_id | ACVC-A-RECON-HISTORY-HEADROOM-CERTIFICATE-R02 |
| current_object_same_host | true |
| current_upper_reference | REGIME-ORACLE-ENVELOPE |
| current_upper_reference_same_information | false |
| current_baseline | DET-CF |
| current_baseline_tuned_generic | false |
| current_result_can_supply_A1_raw_gap | false |
| A1_status | NOT_DONE |
| raw_gap | null |
| raw_gap_units | exact expected native episode return |
| MEI_5_percent_approved | false |
| mechanism_closure_25_percent_approved | false |
| threshold_classification | NOT_APPLIED |
| followup_id | ACVC-A1-SAME-INFORMATION-TUNED-BASELINE-GAP-A-RECON |
| followup_status | FROZEN_DEPENDENCY_BLOCKED |
| B_authorized | false |
| lifecycle_changed | false |
