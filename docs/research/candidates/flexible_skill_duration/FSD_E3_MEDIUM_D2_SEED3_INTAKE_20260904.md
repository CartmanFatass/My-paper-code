# FSD E3 medium D2 seed 3 — DM intake and next fixed cell

Intake boundary: 2026-09-05T00:41:25Z (2026-09-04 PDT). Tier: **object**.
Result: `FSD_E3_MEDIUM_D2_SEED3_RESULT_EVIDENCE_20260904.md`.

## Disposition and what I checked

**Accept `medium_d2_seed3` attempt 01 as a valid complete B/EXPLORE cell.** E3 is 12/18
valid, zero running and six never launched at intake. One historical quarantined attempt
remains separate. This incomplete B study has no aggregate result branch or consumption state.

I checked the unchanged card and prospective continuation intake against CM's original command,
terminal collection return and staged summary/evaluation/path bytes. Exact source SHA is
`31bfecd79fc0f708546786ee26dfd8faa9e85dfb`; the accepted source preserves medium D2/seed 3,
CPU/four-thread, cost/caps, RNG/tapes, checkpoint, normalizer-copy and evaluation semantics.
The accepted CM terminal receipt is pushed at `6b0669394eec563e286b61833879e52847be3f41`.

- **Actual work:** 20/20 rollouts, 128,000 transitions, 320 training episodes, 3,584 evaluations
  and 22,575 actual optimizer steps across five positively updated groups. All first/final
  exposure lines are present; minimum final ratio is `0.05824783929347061`.
- **Technical evidence:** CM checked all 20 learner/path records, both regions, four ordered
  episode-return inputs, complete E3 publication, finite checkpoint/optimizer states and the
  inherited RNG/normalizer schema. Ten remote/staged/canonical hashes agree; canonical copy
  was made only after absence was checked. Earlier roots and the quarantine remain untouched.
- **Direct arithmetic:** I recomputed all four single-cell evaluation means and sample-based
  standard errors. Final mean `0.35348229980468726` and standard error `0.000670192216097249`
  match publication exactly. All episode IDs are ordered and all returns finite. I read the
  cumulative two-region path; I did not compute paired gain or a cross-cell result.
- **Receipt and costs:** initial remote physical/effective availability each `15,432,294,400`
  bytes passed both 4 GiB floors. Runner wall `2525.5407063739985 s` and retained supervisor
  duration `2603 s` are below the original 4.63 h projection and 8 h cap. Later supervisor
  uptime is not experiment duration. RSS and peak scratch stay unmeasured without invalidation.
- **Observation recovery:** tracker notified the initial SSH timeout, then directly reported
  terminal status. DM acknowledged both events and resumed the same CM for collection. No
  second observer, duplicate learner, new receipt or experiment mutation was created.
- **Rule applied verbatim:** “Do not apply the frozen E3 result rule until all 18 required
  invocations are validly complete.” There are 12; no card branch is selected.
- **Owner surfaces:** both DM and Root-integration `item.py reviews --json` returned `[]`;
  today's only review was already answered, yesterday's file absent, FSD audit owner columns
  empty. Owner E3 prediction remains `not taken (unattended)`; the DM prediction remains
  `E3-H0-NO-ADVANTAGE`, unscored until the complete study.

## Observation that bounds the result and owner flags

This is a single medium-row treatment observation under the declared transition budget. It
establishes complete learning/evaluation exposure and available native path data. Equal
transition budgets do not imply equal optimizer counts; the actual counts remain explicit.
It establishes no paired superiority, large-row event-path verdict, seed stability or transfer.

Strongest support remains E2's controllable durations and now-complete medium evidence. Strongest
contradiction remains E2 `NEITHER`, weak event alignment and seed dependence. Useful renewal
under large hazard contrast, noisy policy gaps, optimizer variation and team interference
remain live until the card's full reading. No mechanism-level `DIRECTION.md` update is warranted.

Flags: resource peaks unmeasured; valid-cell measured machine charge `2525.5407063739985 s`;
no code/scope budget breach, new publication gap, close call, critic dissent, recast, Portfolio
recommendation or lifecycle action. The resolved observation interruption has no scientific
polarity. The result and its plain-language owner brief preserve that boundary.

## Decisions this intake produces

### Decision 1 — accept the completed treatment cell

- **(a)** Accept the complete cell as the twelfth valid B observation and preserve the full-study rule.
- **(b)** Defer this cell's validity until all 18 exist despite its complete required outputs.

Recommendation: **(a)**. Technical conformance and every carded observation are present; the
aggregate rule limits interpretation rather than individual-cell validity.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
`OWNER_DELEGATED`; kind `technical`; reversible yes; owner flag `none`.

### Decision 2 — continue the already-selected next cell

- **(a)** Launch exactly `large_d0_seed1` with unchanged accepted source/card and fresh remote
  admission, then hand its accepted handle directly to the shared tracker.
- **(b)** Hold the unchanged next cell despite the current explicit automatic-research instruction.

Recommendation: **(a)**. The current owner resume and prior continuation selection already fix
this sequence. No outcome is used to change the treatment, comparator, seed set or budget.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
`OWNER_DELEGATED`; kind `selection`; reversible yes; owner flag `none`.

## Meaning-complete next invocation and recovery

Next cell: `large_d0_seed1`, the next existing E3 matrix entry, not a new card. Host hazards
`(0.02,0.20)`, `Delta=1.0`, fixed six entities/three per region, `K=2`, `Z=4`, `H=400`,
Bernoulli `rho=0`, no probe/coupling. D0 uses exact best `k=5`, infinite individual/team costs,
both caps 5 and age off; its future paired D2 keeps `c=0.25` and caps 40/400.

Keep seed 1, four-thread CPU, current precision/RNG/checkpoint/tapes and normalizer/evaluator
semantics; 20 rollouts/16 lanes/400 steps, 128,000 transitions/320 episodes; evaluations
512/512/512/2,048 at rollouts 5/10/15/20, chunk 512. The original first/final per-network
float64 displacement ratios, 20 learner/two-region path records, per-episode evaluation inputs,
summary/receipt and final checkpoint remain required. The prior exposure line remains the E2
ratios `0.04826/0.05293`; each new cell emits its own measurements. No GPU substitution.

Per-cell cost law:
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s` (1.68 h), below the **8 h** cap.
Stop at 20 rollouts, first nonfinite learner loss/return, or first completed rollout after 8 h.
No changed budget or extra suite. The three future D2 cells retain 4.63 h conservative projections;
cost is per arm, and concurrency never divides it. Missing resource telemetry follows the
existing rule, whereas missing required learner instrumentation remains incomplete.

Headroom remains the A1 census: large registered structural gap `0.27121898399999966` between
the public upper `0.8902749999999997` and exact fixed-clock reference `0.619056016`. The trained
large D0 row is not yet observed; this required cell begins filling it without a duplicate
headroom run. The existing ladder continues without retrospective MEI/card changes.

CM owns only its per-cell run/technical record and ignored staging; no new source, scope-section-4
machinery, tests, data or external effects are requested. Use exact committed/pushed launch
bytes, configured remote-first `wsl_4070`, an exact-SHA detached worktree and existing supervisor.
Immediately join this invocation's fresh destination-node memory admission to its exact runner
with `&&`, requiring both 4 GiB floors. Inspect whether the new task/root already exists before
one send; any uncertain accepted handle is recovered rather than duplicated.

Responsible DM `/root/dm_amx_fsd_continue` keeps science; CM
`/root/dm_amx_fsd_continue/cm_am_fsd_continue` keeps launch/technical collection. On acceptance,
DM hands the exact node/task/SHA/cwd/output/receipt/log and bound directly to
`/root/tracker_tl_experiments`. Tracker owns routine observation and directly wakes this DM at
terminal; DM acknowledges and resumes the same CM. Test or process success establishes no
scientific branch. Remaining order after this next cell: large D2 seed 1, D0/D2 seed 2, D0/D2 seed 3.

All counts, outputs and raw locators of the completed medium treatment are preserved in its
result/CM documents. Audit additions and CLI owner items are recorded below for Root integration;
Root alone edits Portfolio/shared audit.

## Owner items and audit additions for Root

CLI items: technical decision `20260904-fsd-006`, next-cell selection `20260904-fsd-007`,
brief `20260904-fsd-008`, all under `docs/research/portfolio/owner/inbox/2026-09-04/`.
Chinese brief: `docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-04_E3_medium_d2_seed3.md`.
Ledger anchor: `docs/research/portfolio/audit/2026-09-04.md#fsd-e3-medium-d2-seed3-terminal-20260904`.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T00:41:25Z | `flexible_skill_duration` | object | technical | (a) accept complete cell retaining full-study rule; (b) defer cell validity until 18 exist | (a) valid `medium_d2_seed3`; E3 12/18, no aggregate branch | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-006.json` | none | |
| 2026-09-05T00:41:25Z | `flexible_skill_duration` | object | selection | (a) launch unchanged next `large_d0_seed1` with fresh remote admission; (b) hold despite current resume | (a) next original fixed-clock cell, direct tracker handoff | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a); current owner resume `OWNER_DIRECT` | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-007.json` | none | |
| 2026-09-05T00:41:25Z | `flexible_skill_duration` | object | technical | reading-agreed; reading-disputed | publish valid-cell Chinese brief; owner reading not auto-applied | yes | `VALID_RESULT_INTAKE` | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-008.json` | none | |
