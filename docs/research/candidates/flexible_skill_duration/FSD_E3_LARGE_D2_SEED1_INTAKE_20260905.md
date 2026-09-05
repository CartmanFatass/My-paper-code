# FSD E3 large D2 seed 1 — DM intake and unchanged continuation

Boundary: 2026-09-05T10:03:18Z. Tier: **object**. Evidence class: **B/EXPLORE**.
Result: `FSD_E3_LARGE_D2_SEED1_RESULT_EVIDENCE_20260905.md`.
Accepted CM terminal commit: `f190fa89d1ab6050177ce160eadf65f8c41be970`.

## Disposition and checks

**Accept `large_d2_seed1` attempt 01 as valid complete cell 14.** Current boundary is 14/18
valid, zero running, four never launched; one historical quarantine stays separate. Current
OWNER_DIRECT “继续自动推进任务” supersedes the former pause. Original remaining cells continue
without changing lifecycle, priority, scientific meaning or the original full-matrix rule.

1. Card/argv/source match unchanged `FSD-E3-HET-R01`: large D2 seed 1, hazards `(0.02,0.20)`,
   `Delta=1`, costs 0.25, caps 40/400, age off, CPU/four-thread, original 20/16/400 and
   evaluation schedule. Exact pushed launch SHA is `e6d049849f717b2aca98ab1bb77092e000cd06d9`.
2. Actual work is 20 rollouts, 128,000 transitions, 320 training episodes, 3,584 evaluation
   episodes and 24,060 optimizer steps across five positively updated groups. All five have
   finite first/final displacement; minimum final ratio is `0.05833616468318452`.
3. CM verified complete ordered learner/path/evaluation/publication streams, two regions,
   finite checkpoint and original receipt. All ten remote/staging/canonical hashes agree;
   existing evidence is preserved. Exit 0 alone is not the acceptance reason.
4. I independently read all four finite ordered episode arrays and recomputed means/standard
   errors. Final mean `0.47674519856770853` and SE `0.0008411905410491914` agree to rounding.
   I checked optimizer totals and cumulative regional path fields. High/low mean durations
   are `5.51066974728413/5.435167230470906`; gap rates `0.16773177083333332/0.17090364583333334`;
   high-region event precision is `0.495676070114425`. These are single-cell training inputs.
5. Immediate remote admission measured physical/effective availability each 15,434,289,152
   bytes, above 4 GiB. Runner wall 2795.3028715779947 s and retained supervisor duration
   2974 s are below the 4.63 h projection and 8 h cap. Resource peaks remain unmeasured.
6. Rule applied verbatim: **“Do not apply the frozen E3 result rule until all 18 required
   invocations are validly complete.”** Fourteen cells do not meet that condition. No paired
   gain/uncertainty, `Q`, row aggregate or E3 branch is read. DM prediction remains unscored.
7. Both DM and current integration owner-review CLI returned `[]`. Today's answered VNFC,
   FOLR and ACVC instructions concern other directions; yesterday's Root agree is answered.
   FSD audit owner columns are empty. No owner E3 prediction: `not taken (unattended)`.

The observation boundary is one fully measured treatment seed. It does not establish a stable
benefit, the complete large-row baseline set, generalization or a direction disposition.
Strongest support remains duration control/comparator readiness; strongest contradiction is
E2 `NEITHER`, weak alignment and seed dependence. Useful hazard-conditioned renewal, noisy
gaps, optimizer variation and team interference remain live. `DIRECTION.md` is unchanged.
The A1 census is the headroom record; no new MEI, tuning or headroom run is introduced into
this already-open ladder. Claim ceiling remains B on the declared corridor rows, no consumption.

Flags: cell machine charge 2795.3028715779947 s; `resources_unmeasured`; remote auto-gc warning
unresolved but exact bytes and this run succeeded. No source/scope budget breach, publication
coverage gap, repeated test, close call, critic dissent, recast or Portfolio recommendation.

## Decisions this intake produces

### Decision 1 — accept the complete cell

- **(a)** Accept cell 14 while retaining the full-matrix reading rule.
- **(b)** Defer individual validity despite complete required observations.

Recommendation **(a)**: complete counts, receipts and learner evidence support cell validity.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
`OWNER_DELEGATED`; kind `technical`; reversible yes; owner flag `none`.

### Decision 2 — continue the original next comparator seed

- **(a)** Run `large_d0_seed2` next, followed by the remaining original cells with per-cell intake.
- **(b)** Hold despite the current explicit owner resume and unchanged admitted card.

Recommendation **(a)**: complete the original comparison without using intermediate outcomes
to change arms, seeds, treatment, comparator or budget.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
`OWNER_DELEGATED`; kind `selection`; reversible yes; owner flag `none`.

## Meaning-complete next CM assignment

Reuse `/root/dm_amx_fsd_continue/cm_am_fsd_continue` and its own worktree. It is not alone;
preserve others' edits and all evidence roots. CM owns only this next invocation's launch/
collection and `docs/Claude_docs/experiments/FSD_E3_LARGE_D0_SEED2_REMOTE_RUN_20260905.md`,
plus ignored runtime/staging output. DM owns card/result/intake; Root owns shared audit and
Portfolio integration. No code or new engineering-scope section-4 item is required.

Run exactly **large D0 seed 2** under the same card: hazards `(0.02,0.20)`, `Delta=1`, six
pinned entities, three per region, `K=2`, `Z=4`, horizon 400, Bernoulli, `rho=0`, no probe or
coupling; exact-best fixed `k=5`, infinite individual/team interruption costs, both caps 5,
age off. Preserve observation/action/reward, all RNG/train/eval tapes, precision, recurrence,
optimizer, checkpoints, normalizer copying and evaluator RNG restoration. Native comparator
path is event -> flag/cue -> fixed renewal -> outage/fresh lease -> service -> shared return.
Fixed membership introduces no lifetime or censoring quantity.

CPU/four-thread device semantics remain pinned; host was prospectively Windows/Linux portable.
Read current integration `.codex/hmasd-compute.toml`; execute remote-first on configured
`wsl_4070`, exact committed/pushed prospective DM SHA in a detached worktree, shared Python,
one unique `agent-task`. Confirm no existing accepted matching cell before sending. Immediately
join destination `admit-memory --out <receipt>` with `&&` to the exact runner; both physical
and effective availability must be at least 4 GiB. Refusal creates no learner state. No CUDA,
local convenience fallback, migration or duplicate launch.

Unchanged work: 20 rollouts × 16 environments × 400 steps = 128,000 transitions/320 training
episodes; eval at 5/10/15/20 uses 512/512/512/2048 episodes, chunk 512, deterministic master
770003 with ordered keyed returns. Preserve first/final five-network float64 displacement,
positive actual optimizer counts, 20 learner/two-region path records, complete summary/manifest/
receipt and readable checkpoint. E2 exposure minima 0.04826/0.05293 establish prospective budget
motion; this cell must emit its own exposure. Missing resource peaks remain marked; missing
learner evidence is incomplete. Accepted publication coverage remains applicable to unchanged
source; do not repeat tests or add machinery. Failure interpretation requires reproduction.

Prospective D0 cost law: `M=16*400/5=1280`; cost coefficient uses `u=150`:
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s`, **1.68 h per arm**, below 8 h.
Stop at 20 rollouts, first nonfinite learner loss/return or first completed rollout after 8 h.
The cap is per invocation, not elapsed study time. Remaining D2 cells retain conservative
4.63 h projections. No additional exposure, tuning, new headroom object or source change.

Technical success establishes complete-cell conformance only. No paired `G/Q`, row aggregate,
prediction scoring or one of the five E3 branches before 18 valid cells. Continue in order:
`large_d0_seed2`, `large_d2_seed2`, `large_d0_seed3`, `large_d2_seed3`, with normal intake.
Original terminal handle `fsd_e3_large_d2_seed1_20260905_01` is closed for observation: tracker
terminal notice was directly ACKed; no restart or repeated reminder. Hand the next accepted
unique handle directly to `/root/tracker_tl_experiments` with node/SHA/cwd/receipt/log/output,
bound and reminder conditions. Its direct ACK transfers routine observation only; CM retains
terminal acceptance and DM all science. Missing tracker ACK never authorizes duplicate work.

No Pro or direction-tier decision is needed for these original cells. Any later Pro authoring
must read current integration Transport config and honor the fresh-6-Pro cutover; stale local
provider bindings are historical. Next scientific discriminator remains the original paired
return and regional event-path reading after all 18 valid cells.

## Owner items and audit additions for Root

CLI items: `docs/research/portfolio/owner/inbox/2026-09-05/20260905-fsd-002.json` (acceptance),
`20260905-fsd-003.json` (next selection), `20260905-fsd-004.json` (brief), in the same directory.
Chinese brief: `docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-05_E3_large_d2_seed1.md`.
Ledger anchor: `docs/research/portfolio/audit/2026-09-05.md#fsd-e3-large-d2-seed1-terminal-20260905`.
Root integrates the shared ledger; DM does not edit it concurrently.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T10:03:18Z | `flexible_skill_duration` | object | technical | (a) accept complete cell retaining full-matrix rule; (b) defer individual validity | (a) valid `large_d2_seed1`; E3 14/18, no aggregate branch | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-fsd-002.json` | none | |
| 2026-09-05T10:03:18Z | `flexible_skill_duration` | object | selection | (a) continue original remaining matrix; (b) hold despite current resume | (a) `large_d0_seed2` next with unchanged card and fresh per-invocation admission | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-fsd-003.json` | none | |
| 2026-09-05T10:03:18Z | `flexible_skill_duration` | object | technical | reading-agreed; reading-disputed | publish valid-cell Chinese brief; owner reading not auto-applied | yes | `VALID_RESULT_INTAKE` | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-fsd-004.json` | none | |
