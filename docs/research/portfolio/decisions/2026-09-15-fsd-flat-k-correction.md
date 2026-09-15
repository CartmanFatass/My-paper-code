# FSD baseline × interruption B01 — FLAT k correction

**PRO_FINAL / OWNER_DELEGATED: option 1, FLAT stays at `k = 10`.** Full response
`a4daca15fbf02158eb30cde1c1a0e33dd570fdce` (5,591 bytes) is archived at
`codex/fsd 8d76569178340434ae973e43d46685a114688fb1` in
[the correction packet](../pro_packets/20260915_fsd_flat_k_correction/archive/RESPONSE.md);
[the author intake](../pro_packets/20260915_fsd_flat_k_correction/INTAKE.md) finds no concrete
scope or specification conflict. Delivered 2026-09-15 12:55Z; Issue #22 comment `5680531714`.

The four purchased FLAT originals of the S allocation
([decision of 11:25Z](../pro_packets/20260915_fsd_baseline_interruption_investment/INTAKE.md))
proceed one per block at launch source `dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`, built as
`off → mappo → k = 10`: single constant skill, coordinator and discriminators never updated,
only the discoverer actor and critic learn. The decisive reason is matching the discoverer
gradient-truncation law across arms; the earlier "not runnable" explanation was wrong and is
withdrawn. The switch's own `k = rollout_length + 1` is superseded for this object only.

`GAP_D = J15(D1280) − J15(FLAT_k10)` and `GAP_I = J15(I1280) − J15(FLAT_k10)` keep their
arithmetic, carry no MEI, and are untuned cross-information package gaps, never §11.7 headroom.
D1280/I1280 fits, the rollout-15 SI1280 primary (.05 J importance reading, separate uncertainty
reporting), four blocks, fifteen rollouts, three H500 panels and the 4 + 2 rollout-5
accumulation are untouched and not rescored.

Only the FLAT recipe wording changes. No k sweep, ablation, pilot, replacement, retry, extra
panel, extension, grant, specification exception, lifecycle, priority or peer change follows;
FSD remains ACTIVE/HIGH in the same slot. The DM (Claude hub) launches the FLAT fits directly
as independent work and records them in the evidence folder's `EXECUTION.md`; no Root
ratification is needed.
