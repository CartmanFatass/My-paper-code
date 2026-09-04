# ACVC history headroom certificate R02 — result evidence

- Direction: `acvc`
- Object: `ACVC-A-RECON-HISTORY-HEADROOM-CERTIFICATE-R02`
- Evidence class and claim ceiling: **A/RECON**; an exact threshold certificate on the unchanged
  twelve-opportunity uncertain/delayed R01 host and unchanged harm envelope only
- Science card:
  [`ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_SCIENCE_CARD_20260904.md`](ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_SCIENCE_CARD_20260904.md)
- Complete machine result:
  [`ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESULT_20260904.json`](ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESULT_20260904.json)
- Fresh admission receipt:
  [`ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESOURCE_ADMISSION_20260904.json`](ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESOURCE_ADMISSION_20260904.json)
- Launch implementation commit: `3831a66da19788f549e39faeb8a898221186252a`
- Result: **`HC-D / CERTIFICATE_INTERVAL_UNRESOLVED`**

## E0 execution and integrity record

The prospectively required result-blind project-cost ran on `wsl_4070` from the exact pushed
implementation commit in a detached worktree. Authoritative task
`acvc_r02_cost_3831a66d_03` finished with exit `0`. Its one stdout JSON record reported
`7.25163762199918 s` wall and `20,115,456` bytes peak RSS, so the prospective multipliers gave
`21.754912866 s <= 120 s` and `40,230,912 bytes <= 1.5 GiB`. The synthetic path contained no
ACVC value, threshold, branch, or output root. It executed the fixed inventory: 48 latent atoms,
24 visible anchors, 864 lower scores, 3,312 witness scans, 2,701 dual candidate slots, and
194,472 upper action scores. The minimum synthetic lower and upper numerator and denominator
widths were all 512 bits. The retained supervisor log is
`/home/wu/.agent-tasks/acvc_r02_cost_3831a66d_03/task.log`; the cost command emitted no standalone
artifact.

The only actual scientific invocation was authoritative remote task
`acvc_r02_result_3831a66d_02`. Immediately before the runner, the same detached task ran the
required memory admission. The retained receipt recorded physical and effective available memory
of `12,913,889,280` bytes against the `4,294,967,296`-byte floor; both checks passed. The exact
logical argument vector embedded in the result was:

```text
scripts/run_acvc_history_headroom_certificate_r02.py result
--output-root /home/wu/hmasd-worktrees/acvc-r02-3831a66d/temp/directions/acvc/exp/history_headroom_certificate_r02_20260904/result_01
--admission-receipt /home/wu/hmasd-worktrees/acvc-r02-3831a66d/temp/directions/acvc/exp/history_headroom_certificate_r02_20260904/resource_admission_result_01.json
--launch-sha 3831a66da19788f549e39faeb8a898221186252a
```

The supervisor finished with exit `0`. The runner recorded `2.288506334 s` wall and
`19,333,120` bytes peak RSS, below the frozen `120 s` and `1.5 GiB` limits. The summary records
one CPU process and one computational thread, no RNG, exact `fractions.Fraction` arithmetic, zero
learner exposure, `complete=true`, and no integrity failure. The verified 139,878-byte source
summary has SHA-256 `6243e867eea3556a67aafebbf2f09640a0efa50d5d231ab0eff2c9ce52737b3b`; the verified 504-byte
source receipt has SHA-256 `37e8b497a87c170237884152af94e2b089e3da0720fd94efda9166cde06ee6ca`.
Local copyback, durable linked JSON, and remote bytes match exactly. The remote scientific log
remains at
`/home/wu/.agent-tasks/acvc_r02_result_3831a66d_02/task.log`.

## Direct exact observations

| quantity | exact rational | decimal |
| --- | ---: | ---: |
| `J_D`, unchanged exact `DET-CF` | `2088/625` | `3.3408` |
| `J_L`, legal `HIST-1UPDATE-CF` | `18916861/5625000` | `3.362997511111...` |
| `J_U`, certificate-only `REGIME-ORACLE-ENVELOPE` | `13365083/3671875` | `3.639852391489...` |
| `Delta_L = J_L - J_D` | `124861/5625000` | `0.022197511111...` |
| `Delta_U = J_U - J_D` | `1098083/3671875` | `0.299052391489...` |

Thus the exact interval obeys `Delta_L < 1/4 <= Delta_U`. The exact `J_D` is the carded host-law
value; the sampled R01 `DET-CF` mean remains provenance and was not substituted.

`HIST-1UPDATE-CF` was harm-compatible. Its unsafe-execution rate was
`3584107/25776000 = 0.139048223153...`, versus `445/2864 = 0.155377094972...` for `DET-CF`; its
clean-opportunity loss was `72897857/182040000 = 0.400449664909...`, versus
`639/1640 = 0.389634146341...`. The latter increase is about `0.010816`, below the frozen `0.05`
allowance, and unsafe execution decreased rather than consuming the `0.02` allowance.

The lower policy disagreed with `DET-CF` on exact opportunity mass
`819269/22500000 = 0.036411955556...`, or expected count
`819269/1875000 = 0.436943466667...` per episode. Its 12 aggregated disagreement rows cover all
132 positive-mass state/opportunity pairs and include every forced-`DET-CF` native Q advantage.
Their probability-weighted aggregate is positive and equals
`124861/5625000 = 0.022197511111...`.

The lexicographically first visible-history witness holds the later current context fixed at
`(b=0,q=9/10,d=1)`. After first history `(b=0,q=7/10,d=0,action=EXECUTE,y=0)`, with positive mass
`11/125`, the lower action is `EXECUTE`; after the otherwise matched visible history with `y=1`,
with positive mass `1/125`, it is `PROBE`. Hidden regime was never used for legal action, truth was
never inserted after VETO, and later outcomes never changed the frozen first-opportunity anchor.

The extra-information oracle was explicitly marked certificate-only and not a legal treatment.
Its 24-cell, 72-variable exact program had feasible primal and dual certificates. Their identical
per-opportunity objective was `13365083/44062500`; all complementary-slackness products were
exactly zero. All likelihood, policy-mass, and oracle-cell normalization checks were exact.
`J_U >= J_D` and the compatible lower value obeyed `J_L <= J_U`.

## Frozen rule application

The registered rule was applied once and in order:

1. `HC-X` does not apply: the calculation is complete, exact, legal-information preserving,
   admitted, resource-conforming, normalized, and fully certified, with no missing required field
   or integrity failure.
2. `HC-A` does not apply because `Delta_L = 124861/5625000 < 1/4`, even though the legal lower
   witness is compatible, changes an action at positive mass, and has positive forced-action
   advantage.
3. `HC-C` does not apply because `Delta_U = 1098083/3671875 >= 1/4`.
4. `HC-B` does not apply because the lower bound is below `1/4` and the lower policy is compatible
   with the envelope.
5. The complete remaining result is therefore **`HC-D / CERTIFICATE_INTERVAL_UNRESOLVED`**.

The machine mapping and the independent DM application agree. The authorized consequence is to
admit no learner and park at the exact engineering/scientific dependency. Re-entry requires
either a prospectively resource-admitted legal same-information lower certificate that clears
`1/4` with the registered witnesses, or a prospectively resource-admitted tighter exact upper
certificate below `1/4`.

## Bounded reading, support, and contradiction

Direct observation establishes a small but exact, harm-compatible history-conditioned value for
the fixed one-update legal policy: `0.022197511111...` native return above `DET-CF`, with an actual
visible-history action change and positive native consequence. This is the strongest support that
receiver-visible history is decision-relevant on the frozen host.

The same observation is also the strongest direct contradiction to a material lower-witness
claim: the gain is only about 8.9% of the registered `0.25` threshold. The strongest certified
upper remains `0.299052391489...`, so it is too loose to prove material compatible headroom
impossible. The interval therefore establishes neither material headroom nor its absence. It does
not authorize a learner, identify representation/optimization/credit failure, or change any
Portfolio lifecycle, priority, capacity, fusion, or investment decision.

The surviving alternatives remain: a stronger legal same-information history policy may clear
the threshold inside the harm envelope, or a tighter exact upper may place every compatible legal
policy below it. Extra learner budget, a predictive regime statistic, approximate evaluation,
threshold tuning, or a cap increase is not the next discriminator.

This result also does not complete guidance census A1. `REGIME-ORACLE-ENVELOPE` observes hidden
regime and is therefore not a same-information upper reference, while unchanged `DET-CF` is a
fixed competent comparator rather than a prospectively tuned generic baseline. No 5% or 25% MEI
threshold is applied to this result.

## Engineering conformance and deviations

The implementation commit is pushed on
`codex/cm/acvc-history-headroom-certificate-r02-20260904`. The focused suite passed 11 tests in
`2.62 s`; the independent final reviewer found no material issue. The change used four owned
paths, 1,491 non-test lines, a 69-line runner, and approximately 28.6% conservative orchestration.
It added none of the section-4 default-prohibited machinery and stayed within every section-5
budget; `scope: none` applies.

Before the accepted cost and result invocations, one uncommitted local full cost was marked
`DEVELOPMENT_ONLY / NON_ADMITTING`, cost task `_01` and scientific task `_01` received empty
commands, and cost task `_02` failed during a redundant Git fetch before cost execution. The empty
commands, fetch failure, and local development measurement created no scientific root or result
polarity. After authoritative absence checks, the accepted remote cost `_03` and scientific
invocation `_02` were the only executions used for evidence. No frozen scientific, numerical,
information, RNG, checkpoint, or side-effect semantic deviation was accepted.
