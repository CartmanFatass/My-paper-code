# FSD E3 large D0 seed 1 — DM intake and owner-directed drain

Boundary: 2026-09-05T01:51:19Z (2026-09-04 PDT). Tier: **object**.
Result: `FSD_E3_LARGE_D0_SEED1_RESULT_EVIDENCE_20260904.md`.
Accepted CM terminal receipt: `5c70f068d023f54a20f8d264a52163694280a411`.

## Disposition and current authority

**Accept `large_d0_seed1` attempt 01 as a valid complete B/EXPLORE comparator cell.** E3 is
13/18 valid, zero running and five never launched. The single historical quarantined attempt
remains separate. E3 is incomplete, with no aggregate branch or consumption state.

The owner's latest instruction is “这轮完毕后暂停即可”, relayed explicitly by Root: finish
this existing cell's collection/intake and stop before `large_d2_seed1` or any successor.
That current `OWNER_DIRECT` instruction supersedes earlier automatic continuation after this
cell. DM acknowledged it and cascaded it to the existing CM, which explicitly acknowledged.
No accepted run was interrupted. No new launch, admission, retry, repair or Pro is requested.
This is an execution drain, not a direction-family park, lifecycle or priority change.

## What I checked

1. **Card and command:** unchanged `FSD-E3-HET-R01`, large D0/seed 1, best `k=5`, infinite
   costs/both caps 5, CPU/four-thread, 20/16/400 budget and exact evaluation/RNG/checkpoint
   semantics against CM's recorded source/argv and staged summary. Exact launch/source is
   pushed `f42dcb7a76f6341d3552a27134ca674674b29718`.
2. **Actual learner work:** 20 rollouts, 128,000 transitions, 320 training episodes, 3,584
   evaluations and 148,500 actual optimizer steps across five positively updated groups.
   First/final exposure exists for every group; minimum final ratio `0.03338753931700782`.
3. **Artifacts:** CM checked full learner/evaluation/path/publication outputs, two regions,
   finite values, checkpoint and original receipt. Original, staging and canonical copies are
   retained with transfer evidence; no prior evidence was overwritten or checkpoint resumed.
4. **Direct arithmetic:** I independently read all four finite ordered evaluation arrays,
   recomputed means/standard errors, and checked actual optimizer totals and both regional
   path records. DM final mean `0.5481325276692713`, standard error `0.0005496801464339235`
   and D0/reference ratio `0.8854328421053117` match publication to rounding. This seed meets
   the card's descriptive `0.85` competence line; it does not supply an absent D2 observation.
5. **Native path:** segment length and deciles are 5 in both regions, with zero gap renewals;
   undefined event precision follows from its zero denominator. That is the fixed-clock
   comparator, not missing instrumentation or an event-driven treatment result.
6. **Admission and cost:** fresh remote receipt passed both 4 GiB floors with
   `15,042,007,040` bytes each. Runner wall `2837.5571884999954 s`, retained supervisor
   duration `2960 s`, both below 1.68 h projection/8 h cap. Later uptime is not run duration.
   Peak resource telemetry stays unmeasured without invalidation.
7. **Rule applied verbatim:** “Do not apply the frozen E3 result rule until all 18 required
   invocations are validly complete.” There are 13; no paired gain, `Q`, aggregate uncertainty
   or E3 branch is computed. Missing large pairs are not failed-competence pairs.
8. **Owner surfaces:** DM and integrated `item.py reviews --json` each returned `[]`; today's
   only owner review is already answered, yesterday absent, and FSD audit owner columns are
   empty. The current direct drain is separately applied above. No owner E3 prediction was
   received; it remains `not taken (unattended)`. DM prediction `E3-H0-NO-ADVANTAGE` is unscored.

## Observation boundary and flags

This result provides the first competent large-row fixed-clock comparator seed and its full
learning curve. It does not establish the other two D0 seeds' competence, a completed pair,
event-driven interruption benefit, stable seed behavior or transfer. The available headroom
record remains the A1 census and declared structural references; a complete trained large-row
baseline set is still missing. No new threshold or tuning run is introduced.

Strongest support is comparator readiness and the existing duration-control observation.
Strongest contrary evidence remains E2 `NEITHER`, weak event alignment and seed dependence.
Useful large-row renewal, noisy policy gaps, optimizer variation and team interference remain
live. Accepted mechanism-level `DIRECTION.md` science is unchanged.

Owner flags: measured valid-cell usage `2837.5571884999954 s`; resource peaks unmeasured;
remote Git auto-gc's earlier preparation warning is retained but its cause remains unresolved.
Exact source/worktree creation and this invocation succeeded. There is no new source/scope
budget breach, repeated test, missing publication coverage, close call, critic dissent, recast,
Portfolio recommendation or lifecycle action.

## Decisions this intake produces

### Decision 1 — accept the complete comparator cell

- **(a)** Accept this cell as the thirteenth valid B observation, retaining the full-matrix rule.
- **(b)** Defer individual-cell validity until the whole matrix exists despite complete outputs.

Recommendation: **(a)**. The required observations, receipt and technical conformance are
present; accepting one cell does not trigger the aggregate mechanism rule.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
`OWNER_DELEGATED`; kind `technical`; reversible yes; owner flag `none`.

### Owner-direct execution boundary

Execute the latest direct instruction: complete this intake and stop before `large_d2_seed1`.
Recommendation is to preserve this exact clean boundary. `OWNER_DIRECT`, kind `selection`,
reversible yes; no direction-tier park or Portfolio decision. The earlier queued continuation
is historical until a later explicit resume. No learner, task, preflight or root for a successor
is created by this closeout. The brief and decision are written through the owner-item CLI.

## Exact recovery handoff

Completed handle: `wsl_4070` / `fsd_e3_large_d0_seed1_20260904_01`, exit 0, tmux inactive,
terminal `2026-09-05T01:41:53Z`. Exact SHA, original remote/staging/canonical roots, receipt,
command and file hashes are in the result and CM record
`docs/Claude_docs/experiments/FSD_E3_LARGE_D0_SEED1_REMOTE_RUN_20260904.md`.
The dedicated tracker was directly ACKed at terminal; it stops repeated reminders and routine
polling of this historical handle. CM finishes with a clean pushed branch and no active child.

Pending unchanged order after a later explicit resume:
`large_d2_seed1`, `large_d0_seed2`, `large_d2_seed2`, `large_d0_seed3`, `large_d2_seed3`.
Next D2 keeps seed 1, large hazards `(0.02,0.20)`, `Delta=1`, `c=c_Z=0.25`, caps 40/400,
age off, CPU/four-thread, original 20/16/400 budget and 512/512/512/2048 evaluations. Its
conservative projection remains 4.63 h per invocation against the 8 h cap; D0 cells remain
1.68 h. Every future invocation needs its own fresh destination-node admission immediately
before exact committed/pushed bytes and one detached supervisor launch. None is admitted now.

No Pro round belongs to this drain. For any later Pro authoring, Root's current Transport
cutover requires reading the then-current integrated `.codex/hmasd-transport.toml` and
`docs/research/portfolio/decisions/2026-09-04-new-transport-fresh-6pro-conversations.md`;
old provider conversation IDs must not be reused. This science worktree's historical Transport
configuration is not the current execution authority.

All evidence and predictions remain preserved. The next scientific discriminator is still the
original paired-return and regional event-path reading after all 18 valid cells; the current
owner drain does not decide that result. Root owns shared audit/Portfolio integration; rows
and CLI item locators follow below.

## Owner items and audit additions for Root

CLI technical decision: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-009.json`.
CLI brief item: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-010.json`.
Chinese brief: `docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-04_E3_large_d0_seed1.md`.
Ledger anchor: `docs/research/portfolio/audit/2026-09-04.md#fsd-e3-large-d0-seed1-terminal-20260904`.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T01:51:19Z | `flexible_skill_duration` | object | technical | (a) accept complete comparator cell retaining full-matrix rule; (b) defer individual validity | (a) valid `large_d0_seed1`; E3 13/18, no aggregate branch | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-009.json` | none | |
| 2026-09-05T01:51:19Z | `flexible_skill_duration` | object | selection | latest direct owner instruction: finish current round then pause | finish existing-cell intake and stop before `large_d2_seed1`; five cells unlaunched | yes | `OWNER_DIRECT` — execution drain only | `docs/research/candidates/flexible_skill_duration/FSD_E3_LARGE_D0_SEED1_INTAKE_20260904.md` | none | |
| 2026-09-05T01:51:19Z | `flexible_skill_duration` | object | technical | reading-agreed; reading-disputed | publish valid-cell Chinese brief; owner reading not auto-applied | yes | `VALID_RESULT_INTAKE` | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-010.json` | none | |
