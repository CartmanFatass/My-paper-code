# SCDMP Portfolio A1 headroom-equivalence intake (2026-09-04)

- Direction: `semigroup_consistent_duration_model_policy`
- Decision tier: object
- Guidance item: Portfolio exploration guidance A1 / P1
- Existing result audited: `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01`
- Finding: `A1_NOT_DONE — HEADROOM_UNMEASURED`
- Raw upper-reference minus tuned-baseline gap: **not observed**

## Authority and boundary

The owner directed a result-level equivalence audit instead of accepting the guidance table's
label. The controlling question is whether completed SCDMP A01 actually measured, on the same host
and with the same available information, the raw gap between a prospectively stated upper
reference and a tuned generic baseline.

The source guidance is
`docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md` at exact commit
`b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`. That document calls itself an alignment draft. Its
recommended 5% headroom and 25% closure-share MEIs are `[DECIDE]` items and have not been approved.
They are not thresholds, branch rules, launch gates or result interpretations here.

This object-tier audit is parallel to the direction-tier
`PRO_FINAL=ADMIT_ONE_PROSPECTIVE_A_RECON`. It cannot replace, narrow or broaden the admitted A02
decision, authorize B, or change Portfolio lifecycle.

## Evidence checked

The audit checked the frozen A01 card, valid E0 result, result intake and exact published tables.
A01 ran on the same `.92/.25` native host contemplated for D6, with six states, actions
`{0,10,12}`, durations `{7,13}`, balanced HR/RH twins and paired tapes. It executed no learner.

| required headroom element | what A01 actually contains | equivalence finding |
| --- | --- | --- |
| prospectively stated upper reference | A01 computes, after the complete finite panel, the best observed action value separately within each duration | not named or frozen as a headroom upper-reference policy |
| tuned generic baseline | zero models, training datasets, optimizer updates, AdamW steps and learner evaluations; no baseline config or checkpoint | absent |
| same host | exact `TAU_LEAK=.92`, `Z_LIMIT=.25` row | satisfied only for the A01 panel |
| same available information | candidate clocks share source bytes, public state and tapes, but no generic learner receives or acts on that information | cannot establish the required reference/baseline match |
| headroom estimand | `W`, `R7`, `R13`, and per-state `B7-B13` duration-action contrasts | different estimand |
| raw gap | no `J_upper`, no `J_generic`, no `J_upper-J_generic` | unavailable |

Even if the outcome-derived per-duration action maximum were treated as a finite-panel oracle, A01
still has no tuned generic baseline return to subtract. Its six `D_j` values (`-179` to `-197`)
are differences between duration-conditioned action maxima, not upper-reference headroom. They
cannot be relabelled or arithmetically converted into the missing gap.

## Observation and bounded reading

Direct observation: A01 is a complete action-relevance census with `W=2498`, `R7=0`, `R13=1`,
1,152 valid missions and zero learner activity. It establishes a finite one-sided native
duration-action pattern.

Inference: because the treatment/reference and generic baseline required by A1 were not both
present, A01 is not equivalent to the headroom measurement. The Portfolio A1 row for SCDMP is
therefore not done. No raw headroom gap exists in the evidence record.

This is neither a negative headroom result nor evidence that the generic baseline is close to the
upper reference. It is a measurement-identity finding. It creates no D6/D8 polarity and does not
alter A01's valid bounded reading.

## Decisions this intake produces

Object-tier options were:

1. **(a)** mark SCDMP A1 done by treating the completed action-relevance census as headroom;
2. **(b), recommended:** record A1 as not done and freeze only the minimal same-host,
   same-information headroom follow-up item, held non-executable until the exact upper-reference
   and tuned-generic-baseline assets are prospectively bound;
3. **(c)** insert the unapproved 5%/25% MEIs, restore the stopped B, or change lifecycle based on
   this audit.

**Owner-direct decision (2026-09-04 instruction): (b).** The selection is reversible before any
future headroom run. Option (a) is factually unsupported; option (c) exceeds authority.

The minimal follow-up is recorded in
`SCDMP_PORTFOLIO_A1_SAME_INFORMATION_HEADROOM_FOLLOWUP_FREEZE_20260904.md`. It is not a runnable
science card and launches nothing. A complete A/RECON card must later bind the exact comparator
assets, prospective evaluation population, RNG domains, budget, stop rule and finite branches
before CM or an experiment is authorized.

## Flags for Root and owner

- A1 status: `NOT_DONE / HEADROOM_UNMEASURED`.
- Raw gap: absent, not zero.
- MEI application: none; 5% and 25% remain unapproved recommendations.
- B authorization: none.
- Lifecycle/priority/investment: unchanged; Portfolio tier.
- A02: remains the controlling direction-tier next discriminator and proceeds independently.
