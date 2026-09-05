# CRTO RAW full-cycle readout B02 intake

Date: 2026-09-04 PDT (remote completion 2026-09-05 UTC). Object: `CRTO-RAW-CYCLE-READOUT-B02`.
Disposition: **accept `B02-CYCLE-COMPETENCE-NOT-STABILIZED`**, B/EXPLORE, one seed and one
exposed finite panel. Do not adopt this mean readout as a competent comparator from this result.

## What this intake checked

Read the frozen B02 card against CM's E0, independent technical-review return and complete
204,158-byte result. Source `2b667289603b0f7b82508119b902090ddb841728` and E0/full summary
`77affdfed159e9b538dbb786e4a66bb3ee4392a9` are pushed on `cm-crto-b02-20260904`. No historical
source or evidence changed. The equivalent new training loop changes only helper qualification
and the carded 600-second monitor; source comparison and review establish engineering conformance.

I independently parsed all 64 exact B01 card population members, checked split/event/onset/side,
namespace/addresses, fixed cost and elapsed time, and recomputed each side from the recorded native
advantage. All 48 TRAIN and 16 EVAL members agree. I checked all five snapshot populations, legal
predicted scores, initial scales, ending/window exposure and all information/thread/count fields.
For every one of 96 readout rows, I recomputed the ascending FP64 mean from the recorded FP32
snapshot scores, legal action and first-printed ties, signed native labels, oracle, exact indicator
and oracle-minus-selected regret. Mean-score disagreement is exactly zero; native scores/regrets,
side aggregates, paired differences, competence, aggregate and branch agree within absolute 1e-12.
No learner state, new environment rollout, checkpoint or evaluation was created by this intake.

The manual recomputation receipt is under this DM worktree's
`temp/directions/commitment_residual_triggered_options/exp/raw_cycle_readout_b02_20260904/dm_recompute.json`.
The full durable data are `CRTO_RAW_CYCLE_READOUT_B02_RESULT_20260904.json`; the authoritative
raw/task/receipt paths and complete exposure table are in the CM E0 beside it. Legal G16 retains
its finite signed domain. The earlier A01 sign predicate is not copied into this result.

The one accepted task `crto_raw_cycle_b02_2b667289_01` ran on `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/crto-b02-2b667289`, with `python -X faulthandler`, CPU FP32 and one
thread. Fresh adjacent admission at 00:03:41.594468Z observed physical/effective availability
12,931,575,808 bytes. The complete invocation ended at 00:05:11Z, exit 0, 90 seconds, under
600. Runner wall 86.52683217800222 seconds is explicitly before publication; peak RSS is
1,286,844,416 bytes. **Usage per this valid result: 90 supervisor machine-seconds, charged once**
for the two readouts' shared training. No resource telemetry gap exists.

Counts: 128 predictor tapes; 32,256 materialized examples; 100 predictor updates and 12,800
processed examples; 38,464 environment transitions; 3,520 common-future branch steps; RAW
257 updates and 8,224 processed examples; five snapshots, 80 network forward rows, 96 scored
decisions and 16 unique EVAL rows. Every snapshot displacement is finite and positive; the final
L2/initial-L2 is 0.136428218836403 and Linf/initial-Linf is 0.913744698073908. Residual and
deranged learner/evaluation counts are all zero. Shared prefixes are not counted as three learners.

At this clean boundary the shared Root checkout's `item.py reviews --json` returned `[]`;
today's review contains only the already answered unrelated Portfolio item, yesterday's review
is absent and the CRTO ledger owner column contains no new instruction. No owner prediction reply.
Tracker's direct terminal notice was acknowledged and routine observation stopped; no run remains.

## Direct observation and the bound it imposes

R is equal-side native regret; D is ordinary endpoint R minus cycle-mean R. Both sides always
have eight rows. Competence still needs at least six exact actions and mean regret <=0.005 per side.

| ending | readout | KEEP exact | KEEP regret | REPLAN exact | REPLAN regret | R | competent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 255 | ENDPOINT | 6/8 | 0.003754710220270765 | 6/8 | 0.0038081499511370583 | 0.0037814300857039115 | yes |
| 255 | CYCLE | 6/8 | 0.003754710220270765 | 5/8 | 0.0052316106205794015 | 0.004493160420425083 | no |
| 256 | ENDPOINT | 8/8 | 0 | 4/8 | 0.0066464623737892345 | 0.0033232311868946172 | no |
| 256 | CYCLE | 6/8 | 0.003754710220270765 | 5/8 | 0.0052316106205794015 | 0.004493160420425083 | no |
| 257 | ENDPOINT | 7/8 | 0.0018989339045047543 | 4/8 | 0.0066464623737892345 | 0.004272698139146994 | no |
| 257 | CYCLE | 6/8 | 0.003754710220270765 | 5/8 | 0.0052316106205794015 | 0.004493160420425083 | no |

The cycle readout's complete 16-action vector is identical at all three endings, a direct local
readout-stability fact. But all three readouts miss the REPLAN exact-count and mean-regret
thresholds. Thus `S(CYCLE)=false`, `S(ENDPOINT)=false`. The three D values are
`[-0.0007117303347211716, -0.001169929233530466, -0.00022046228127808876]` and
`D_bar=-0.0007007072831765755`. Every paired change is adverse but inside the 0.0025 MEI;
no material-regret-loss branch or above-MEI benefit is observed.

## Card rule applied verbatim

1. **`B02-MATERIAL-REGRET-LOSS`**: any `D(U)<-delta`. The mean readout has a material cost at
   a declared ending; do not adopt it as the comparator readout from this result.
2. **`B02-CYCLE-COMPETENCE-STABILIZED`**: `S(CYCLE)` and not `S(ENDPOINT)`, with every
   `D(U)>=-delta`. The readout stabilizes the declared competence predicate across this cycle
   without a material paired regret cost; this is not a causal order or residual result.
3. **`B02-BOTH-READOUTS-COMPETENT`**: `S(CYCLE)` and `S(ENDPOINT)`, with every `D(U)>=-delta`.
   Both readouts are competent throughout this cycle; stabilization by averaging is unnecessary
   here. Retain the signed regret vector, including any material gain.
4. **`B02-CYCLE-COMPETENCE-NOT-STABILIZED`**: not `S(CYCLE)`, with every `D(U)>=-delta`.
   The mean readout does not meet the full-cycle competence target. Retain all partial, null and
   adverse observations; this rejects only this readout/window/seed target.

Branch 1 is false because no D is below -0.0025. Branches 2 and 3 are false because S(CYCLE)
is false. Branch 4 is true. This is a complete valid B negative for the full-cycle competence
target, not an invalid run, C consumption, a closed family or a negative residual mechanism result.

## Reading, predictions and owner flags

The strongest support for the bounded negative is direct failure at all three predeclared endings:
averaging loses one exact REPLAN action relative to the already competent phase-0 endpoint and
does not improve any endpoint's aggregate regret. It cannot supply the desired comparator.
The strongest counterpoint to a broader anti-averaging claim is the identical action vector at
all three endings and REPLAN improvement over endpoints 256/257; averaging does remove this
local action variation but at a side tradeoff that fails the competence target. A small opposite-sign
aggregate difference is not evidence of a material cost under this card's MEI.

The DM predicted branch 4 with every difference inside MEI; that prediction is supported.
Owner prediction: `not taken (unattended)`. There is no independent-seed or held-out readout
evidence, no tuned headroom baseline, and no residual arm. The result establishes neither causal
cyclic-order value nor a general RAW limitation. Seed/predictor/panel variation and the relation
between batch composition, score smoothing and native side thresholds remain live.

No section-4 machinery or section-5 budget breach was found: 323 research lines, 38 runner lines,
91/323 orchestration (28.17%). The new actual-size offline scoring/publication profile passed;
the historical A01 publication-test gap remains historical, and its native crash remains unresolved.
The earlier A02 technical branch and A03 existing-data reading retain their identities.

## Decisions this intake produces

### Decision 1 — accept the valid bounded result (object tier, technical)

Options: **(a)** accept branch 4 after independent recomputation; **(b)** quarantine solely because
the target did not improve; **(c)** promote unchanged action choices to comparator competence.
Recommendation and selection: **(a)**. The card's measurements and engineering contract are
complete, and the declared branch is unambiguous. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a)**. Reversible on a subsequently reproduced source/evidence defect.

### Decision 2 — do not adopt this averaging readout (object tier, selection)

Options: **(a)** drop this local mean readout as the next competent comparator candidate and
preserve its full result; **(b)** repeat unchanged averaging on seed 0; **(c)** call the phase-0
endpoint an independently selected competent comparator or reopen residual comparisons now.
Recommendation and selection: **(a)**. The target fails at every ending; unchanged repetition
does not address a new uncertainty, and neither of the alternatives supplies independent competence.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**. This drops only the tested
readout candidate, not the accepted balanced family or RAW/residual mechanism. No family closure,
recast, C promotion, Pro node, lifecycle or priority change is taken here.

## Next discriminator and clean return

The next useful discriminator is a separately declared B order intervention against the unchanged
RAW path: does balanced KEEP/REPLAN exposure per minibatch change competent native actions,
not merely predict phase? CM's separate read-only source check found that B01 sorts TRAIN by
`row.key.canonical` (source slot then episode), while original `SELECTED_ROWS` retains each
declared KEEP/REPLAN pair. Pair identity is its original declaration position plus both source
addresses; event/onset alone is not unique and cannot be used to invent new pairs.

Interleaving the original 24 TRAIN pairs, taking 16 pairs per batch, would give 16 KEEP and 16
REPLAN examples per update and each row twice per three updates. This is a labelled TRAIN-order
intervention, not extra observation information. Its per-row accumulated exposure matches the
ordinary order exactly only at multiples of three updates; intermediate prefixes can contain
different rows despite equal total example counts. A small next B card can use a fixed endpoint
such as 258 for its matched-row primary contrast against the already competent ordinary phase-0
readout, while reporting a full nearby cycle descriptively with this prefix limitation. No order
causality is inferred from A03/B02 or this source fact.

This intake does not freeze or launch that successor, increase seeds, tune a checkpoint or open
residual arms. All current runtime work is terminal and recoverable; Root owns integration and
the shared ledger, and no Portfolio recommendation is made by this direction-local return.

## Append-ready audit rows for Root

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T17:13:48-07:00 | `commitment_residual_triggered_options` | object | technical | (a) accept independently recomputed B02 branch; (b) quarantine for no improvement; (c) promote action stability to competence | (a) accept B02-CYCLE-COMPETENCE-NOT-STABILIZED | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-022.json` | none | |
| 2026-09-04T17:13:49-07:00 | `commitment_residual_triggered_options` | object | selection | (a) do not adopt tested mean readout; (b) unchanged seed-0 repetition; (c) select exposed endpoint or reopen residual arms | (a) drop only this local mean-readout comparator candidate | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-023.json` | none | |
| 2026-09-04T17:13:50-07:00 | `commitment_residual_triggered_options` | object | technical | reading-agreed; reading-disputed | B02 Chinese brief; DM prediction supported; owner not taken | yes | `DM_INTAKE` | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-024.json` | none | |
