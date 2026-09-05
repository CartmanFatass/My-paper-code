# DISH A01 — DM intake and source-admission follow-up

Date: 2026-09-05 PDT. DM `/root/dm_amx_n3_continue`; **A / RECON**.

## What I checked and the rule applied

Read original A01 summary and receipt, committed raw bytes and CM collection `a6ff9d748`.
Independently reconstructed ordered coordinates, original-reference counts, per-row clock
and absence measurements, zero new parameter movement, totals and row labels. E0 is
`DISH_PREFIX_TRIGGER_FUNNEL_A01_RESULT_EVIDENCE_20260905.md` and carries counts, receipts,
resource use, deviations and remaining engineering limits.

The complete-object rule requires all sixteen rows/measurements and reproduction of the
original no-trigger/prefix-count reference. All sixteen have 1,200 completed and inspected
ticks, with zero triggers. Therefore **A01-PREFIX-FUNNEL-OBSERVED** applies. The ordered
row rule finds live renewal, prepare and latch, then absence of snapshot delivery in
all sixteen: **PREPARATION_SUPPORT_GAP(snapshot_delivery)**. This is a measured exposure
gap, not a source-value result or causal diagnosis. B01 remains valid FTS-B0.

## Decisions this intake produces

### 1. Accept the complete A observation — object tier, technical

Options: (a) publish the complete path measurement with the absent-stage and one-checkpoint
limits; (b) call source value negative because downstream counts are zero; (c) discard the
diagnostic for not having a handover. Recommend/select **(a)**: the frozen diagnostic
assignment is complete, and the absent stages are its intended measurements.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Provenance `OWNER_DELEGATED`, reversible, owner flag `none`.

### 2. Qualify source admission before more learner work — object tier, selection

Options: (a) bounded source/spec mapping and one separately carded native point diagnostic
of ground-source visibility/admission; (b) increase learner
budget immediately; (c) alter physics or force a transfer now; (d) repeat the same A01 panel.
Recommend/select **(a)**. There are 2,234 prepare proposals and latch occupancy across
nearly the whole live prefix, but no common source, delivered snapshot or service. More
updates or altered handover logic would change the system before the upstream absence
has been qualified; repeating this unchanged checkpoint answers no new question.

Read-only inspection of the recorded native code supplies a concrete clue: ground source
height is zero, UAV height 90, and sampled clearance is tested against nonnegative terrain.
At the first ground-to-UAV sample the height is 90/128. This is a source/spec question,
not yet a dynamically reproduced defect classification or authority to change the host.
CM's read-only mapping found that code matches the inherited R05 host manifest sections
1–3 and R06 incorporation: the same zero ground height, 90-m UAV height and 5/8-m sampled
clearance appear in the definition. There is no implementation-versus-spec discrepancy
established. A blocked radio hop still includes Gaussian noise and is not mathematically
equivalent to impossible delivery. Current A01 artifacts contain no native per-tick margins.

Select exactly one normal-mode native prepared point: original seed 11, first original
coordinate, tick 0, no policy or checkpoint load, no completion tick. Existing typed
prepared physics suffices; no new ABI or forced link is needed. Prospective card
`DISH_GROUND_SOURCE_POINT_A02_SCIENCE_CARD_20260905.md` fixes this A/RECON measurement,
15-second projection / 60-second cap, zero learner exposure and fresh destination
admission. No input-height, clearance, radio, mask or source-law change is authorized.
The accepted source-selection family remains unchanged. A confirmed witness informs
the next decision about the host; it does not itself authorize a repair or recast.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Provenance `OWNER_DELEGATED`, reversible, owner flag `none`.

## Owner boundary, predictions and interpretation

The owner ratified the earlier N3 handover-source recommendation in review
`docs/research/portfolio/owner/reviews/2026-09-05.md#20260904-folr-010`, instruction
`ratified; integrate into PORTFOLIO.md`. Root applied it and CLI-marked the item answered
at `d5a6a2568`. It agrees with this existing path and adds no comparison, seed or physics
change. The original owner prediction slot remains not taken; no replacement prediction
is inferred from Portfolio ratification. DM's A01 preparation-support prediction matches.

Strongest support is absent common-source/delivery under actual preparation, full live
prefixes and exact reference reproduction. Strongest limitation is one checkpoint and
unexposed downstream comparisons. No early terminal padding explains these rows; six
rows also have no commit proposal, but the earlier absent stage still controls their
labels. Nothing shows that delivering a snapshot alone would make a handover beneficial.
The raw zero service is contextual, not tuned baseline headroom. No recast, family,
lifecycle, priority or Portfolio investment decision follows.

Full A01 publication is complete; nonzero intent/margin/CAS branches remain unobserved
on real evidence. No live N3 task remains, and the shared tracker has received terminal
ACK. Reviews returned `[]` again in current integration after Root's three applied replies.
CM owns the bounded point implementation/technical return; DM interprets its result.

## Append-ready shared audit rows

Root owns the ledger; append under `n3-prefix-a01-intake`. All four owner items were
created through `python -X utf8 tools/owner_console/item.py add`, not by hand.

| Time (PDT) | Direction | Tier | Kind | Options | Chosen | Reversible | Provenance | Evidence | Owner flag | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05 02:39:26 | degraded_incumbent_shadow_handover (N3) | object | technical | a accept complete A01 with exposure limits; b infer negative source value; c discard no-handover diagnostic | a | yes | OWNER_DELEGATED, 2026-09-03 instruction | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-002.json | none | |
| 2026-09-05 02:39:26 | degraded_incumbent_shadow_handover (N3) | object | selection | a one separately carded native ground-source point; b more learning; c changed physics/forced handover; d repeat A01 | a | yes | OWNER_DELEGATED, 2026-09-03 instruction | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-003.json | none | |

| 2026-09-05 02:39:26 | degraded_incumbent_shadow_handover (N3) | object | technical | reading-agreed; reading-disputed | valid-result brief published; no owner reading auto-applied | yes | DM_INTAKE | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-004.json | none | |
| 2026-09-05 02:39:26 | degraded_incumbent_shadow_handover (N3) | object | selection | accept; reject; revise | A02 card frozen; recommendation accept, asynchronous owner surface | yes | DM_CARD | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-005.json | none | |

Valid-result brief item `20260905-dish-004` points to
`docs/research/portfolio/owner/briefs/degraded_incumbent_shadow_handover/2026-09-05_prefix_funnel_a01.md`.
New-card item `20260905-dish-005` carries the Chinese A02 decision packet and all option
consequences. It adds no owner-wait gate. No duplicate ladder prediction item is created.
The owner review cited above was applied by Root at `d5a6a2568`; there is no remaining
unapplied N3 review at this boundary.
