# VNFC causal one-deviation R03 — prospective cost-accounting correction

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-CAUSAL-ONE-DEVIATION-R03`, A/RECON
- Decision tier: **object**, technical accounting within the unchanged 2,700-second cap
- Provenance: **`OWNER_DELEGATED`**
- Timing: before implementation, calibration, admission or result invocation
- Scope: **none**; no change to the treatment, comparator, causal class, population or result rule

## What I checked

CM identified an inconsistency between the frozen card's section 4 full-terminal continuation for
every legal candidate and its section 9 cost table. DM independently inspected the exact source
surface at base `5777c0e22`:

- `experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp:107` increments
  the interactive epoch and sets terminal only at epoch 6; each epoch has 20 native ticks.
- The same file at line 49 accumulates the failed-zone endpoint only while `post_time < 60`.
  Endpoint time and full native terminal time are therefore distinct.
- `experiments/candidates/variable_n_fleet_churn_headroom/native/headroom_backend.cpp:216`
  reconstructs six pre-loss epochs, or 120 ticks per world. Its `advance` at line 238 advances
  twenty ticks, and `run_bcrh` at line 292 executes all six post-loss epochs.
- `bpcr_general.hpp:75` runs both the scorer and independent checker/enumerator for BCRH and
  admits at most 1,961 commands. Timing only the scalar scorer would not time this comparator.

The archived Convergence-02 response itself requires the native episode to finish for every
candidate (line 138) while carrying the same incomplete cost table (lines 307–314). No failed run
is being diagnosed and no scientific observation is being classified: this is a prospective
arithmetic inconsistency visible in the record and source.

## Corrected single-arm cost law

Every candidate still runs from its epoch `d` to the 120-second native terminal under later BCRH.
Baseline replay can retain value copies of the native states at the three decision epochs;
those copies reproduce the identical BCRH prefix and do not introduce a new exposure or RNG draw.
The selected policy can reuse the same reconstructed post-loss initial state. With that ordinary
within-run reuse, the bounds are:

| quantity | complete bound |
| --- | ---: |
| fixed-world pre-loss reconstruction ticks | `16 * 120 = 1,920` |
| world-epoch-action continuations | `3 * 16 * 1,961 = 94,128` |
| candidate full-terminal native ticks | `16 * 1,961 * (120 + 100 + 80) = 9,412,800` |
| baseline plus selected-policy post-loss terminal ticks | `2 * 16 * 120 = 3,840` |
| total native ticks, including pre-loss | `9,418,560` |
| candidate later-BCRH calls | `16 * 1,961 * (5 + 4 + 3) = 376,512` |
| baseline plus selected-policy BCRH calls | `16 * (6 + 5) = 176` |
| total BCRH calls | `376,688` |
| BCRH candidate rows, each with the full comparator work | `376,688 * 1,961 = 738,685,168` |

The prospective projection used for the sole result is:

```text
T_projected =
    9,418,560 * t_tick
  + 738,685,168 * t_score
  + T_exact_solver
```

`t_score` measures the whole unchanged `grun_bcrh` wall time divided by its reported candidate
row count, including independent enumeration, checking, allocation and comparison. `t_tick`
must cover the native transition work; fixed setup, history grouping, action serialization and
any uncounted residual work must be conservatively included in the calibration overhead alongside
the exact solver, rather than silently dropped. The calibration reports the actual unit timings,
how its conservative bounds are obtained, solver state limits, and every overhead term.

The one permitted calibration remains result-blind and below 60 seconds. Solver overhead uses
bounded synthetic inputs and never the actual panel's candidate endpoint outcomes. If any native
operation is repeated instead of shared, CM adds its cost prospectively; it does not pretend the
table covers repeated prefix reconstruction. Actual run counts are reported alongside the bounds.

## Decisions this intake produces

Options:

- (a) Correct the omitted full-terminal and pre-loss work in the prospective cost projection,
  keeping the complete exact class and the 2,700-second machine-time cap unchanged.
- (b) Hold all implementation to seek an additional direction decision about the arithmetic.

Recommendation: **(a)**. Native terminal work is already required by the selected class. Counting
it correctly repairs an execution estimate and creates no new scientific object, arm, seed,
comparator, endpoint, policy support, stop rule or budget above the existing cap.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.

The original card and Pro archive are preserved. This addendum supersedes only their incomplete
operation-count estimates for execution planning. It does not override the direction node's
scientific choice or open another family. A projection at or above the cap returns
`BLOCKED_WALL_CAP`; no partial result or scientific polarity is produced. Any actual inability to
complete the exact finite optimizer is reported as the card's engineering feasibility blocker.

## Unchanged claim ceiling and next discriminator

All sixteen worlds, unchanged BCRH, complete causal histories, one globally fixed deviation epoch,
all legal candidate commands, full native terminal checks, exact rational endpoints, MEI `0.10`,
CI-X/CI-A/CI-B/CI-C ordering, zero learner exposure and the one-result-arm limit remain fixed.
The headroom observation is still absent. Next: implement the same object and measure this complete
cost law once under the card's result-blind calibration, with fresh actual-node memory admission.

## Append-ready audit row for Root

Owner item: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-016.json`.
Anchor: `vnfc-r03-cost-accounting-20260904`.

| 2026-09-05T01:31:00Z | variable_n_fleet_churn | object | technical | correct omitted full-terminal and pre-loss work within the existing cap; seek another direction round for arithmetic | use the complete prospective cost law without changing the exact scientific object or 2,700-second cap | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-016.json` | `none` | |
