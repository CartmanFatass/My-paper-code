# ACVC_MATCHED_PACKAGE_COMPARISON_B01 — DM intake (2026-09-16 03:45Z)

Object fixed by `em:acvc:convergence` (A with corrections, `PRO_FINAL`), funded by Portfolio G3
(`PRO_FINAL / OWNER_DELEGATED`). DM: the Claude Code hub under the owner's 12:57 PDT scope
instruction. E0: [ACVC_MATCHED_PACKAGE_COMPARISON_B01_RESULT_EVIDENCE_20260916.md](ACVC_MATCHED_PACKAGE_COMPARISON_B01_RESULT_EVIDENCE_20260916.md).
Owner brief (Chinese):
[briefs/acvc/2026-09-16_ACVC_MATCHED_PACKAGE_COMPARISON_B01.md](../../portfolio/owner/briefs/acvc/2026-09-16_ACVC_MATCHED_PACKAGE_COMPARISON_B01.md).

## What was checked

- Both handles finished with supervisor exit 0 and native exit 0 (C 03:32:56Z, M 03:34:11Z);
  nine files per arm collected with per-file sha256 equal to the remote `sha256sum` listing; task
  logs retained. `stderr.log` empty for both.
- Summaries: `status complete`, `fit_complete`, object `ACVC_MATCHED_PACKAGE_COMPARISON_B01`, arms
  C and M, master 28731, namespace 38731, launch sha `841e5c35b`, plans C 2,600 / M 1,200 (not
  caps), `limits []`, no error; M `upstream_sha de66d7a4b`.
- Counts as fixed: per arm 4,096 training episodes, 1,048,576 training ticks, 2,048 rollouts,
  8,192 minibatches; C 8,192 joint optimizer steps, M 8,192 + 8,192; one snapshot, three loads,
  192 evaluation episodes per arm; 2,195,456 scored ticks in all (the ceiling); nine constructors.
- Rows: 4,288 episode rows per arm, all 256 steps, finite S and J, terminated; identities on every
  row; every panel's reset seeds equal the common addresses `100000·38731 + 2000 + e`; update rows
  finite; parameter displacements finite.
- Reduction: the thin entry's `--mode reduce` over the two summaries (input provenance recorded):
  `eligible_fits` C and M true, P complete, six supports complete, identity residual 2.8e-17 J.
- Rule applied verbatim: P = −.014962985109475921 J < −.01 → **F_M_ABOVE_MEI** (24 / 40 / 0,
  conditional SE .010960). Supports: C−M DOWN, F(C)−C UP, F(M)−M WITHIN_MEI, F(C)−own-dwell(C) UP,
  F(M)−own-dwell(M) WITHIN_MEI, own-dwell(C)−own-dwell(M) DOWN.
- Predictions scored: P Brier .185 (modal forecast occurred); supports .135 / .065 / .485; owner
  slot not taken; review inbox empty.
- Preservation: both nine-file sets archived locally with digests (PRESERVATION.json); remote
  worktree and staging reclaimed after preservation (CLEANUP.json).

## Reading and limits (four boundaries)

- **Observation**: on this one matched block, F(M) attains an MEI-sized advantage over F(C)
  (P = −.0150 J, 40/64). **Inference** (bounded): the fixed mapping favours developing F(M)
  relative to F(C) on this block; the arithmetic context is a large C−M deficit (−.056 J) partly
  offset by F's large gain on C (+.046 J) and F's small gain on M (+.005 J, within band). The
  M-side wrapper shows no MEI-sized increment here (F(M)−M and F(M)−own-dwell(M) inside the band),
  so unwrapped M or dwell(M) is a reportable competing development option; no unique source of
  the advantage is identified.
- **Scientific result versus engineering conformance**: the object executed exactly as fixed
  (exposure at the ceiling, nine constructors, no retries); conformance does not add to the
  scientific claim.
- **Direction-local advice versus Portfolio action**: the result changes development advice inside
  ACVC; G3 ends with this intake; lifecycle, priority and slot are unchanged and not decided here.
- **Historical provenance versus current authority**: D1/D2, T_F,1/T_F,2 keep their labels; this
  block is displayed beside them without pooling; F(M)−M here (+.005 J within band) is a third
  per-instance M-side observation, not a pooled verdict.

Not established: stable superiority, a training-population mean, a discardable C or M, tuned
headroom, equivalence, a mechanism, C promotion, default or safety change, transfer or recurrence.

## Decisions this intake produces

Object tier (owner-delegated, unattended, 2026-09-03 instruction): accept the complete G3 block
and report the card-fixed reading, preserve both originals, reclaim the remote worktree and staging
after verified preservation. `Owner-delegated decision (unattended, 2026-09-03 instruction): accept.`
Ledger row 41 (technical).

Next object: G3 is consumed with this intake; no automatic successor, retry, third fit or extra
panel exists. The direction-tier question (independent result review and the next object or the
family/lifecycle recommendation) goes to `em:acvc:convergence`. Options the DM will pose: (A)
record the block, conclude the matched-package question at this one-block reading, and state
whether a defensible next object remains in ACVC or the lifecycle question returns to Portfolio
(DM recommendation: A; with F(M)−M within the band on two of three M-side instances and F(M)
above F(C) here, the practical case for maintaining either wrapper is now the open question, and
no in-scope bounded object answers it better than consolidation); (B) a second matched block
(recurrence of P; a new Portfolio investment); (C) an M-side development object without the
wrapper (unwrapped M or dwell(M) as the package; new investment); (D) another object. No launch is
authorised by this intake.
