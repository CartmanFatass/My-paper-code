# Remote compute handoff — D7.S part B episode budget

Written 2026-07-26. Branch `untied-k`. Everything referenced here is committed and
pushed. Read `AGENTS.md` first, then this file.

**Why this exists.** The local machine is CPU-only and the run that carries the
result needs an episode budget it cannot reach in reasonable wall-clock. The
science is frozen, the instrument is repaired and verified, and what remains is
arithmetic that needs more cores. Nothing in this document asks for a decision.

## The one thing to run

```bash
python scripts/audit_d7_s_persistence_margin.py \
  --episodes 64 --horizon 1500 --stage S3 --n-uavs 8 \
  --topology-seed 20260725 \
  --initial-energies "0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90" \
  --out logs/nonformal_d7_s_persistence_margin_<date>_ci_h1500_ep64
```

`--topology-seed 20260725` is **not optional and must not be changed.** Every
number already recorded was measured at that seed, and the environment draws its
ground-BS and charging-station layout from an unseeded RNG at construction (see
*Traps*), so a different seed silently produces an incomparable topology.

Runtime is roughly linear in `episodes x horizon x n_uavs`. Locally, 4 episodes at
H=1500 took about 82 minutes on 16 cores with contention. 64 episodes is therefore
a long job — hours, not minutes. It parallelizes trivially across episodes if you
want to shard it; see *Sharding* below.

CPU only. No GPU is used or wanted anywhere in this audit. No training happens —
this is an evaluation-only constructive control, no policy, no checkpoint.

### Environment

```text
python      the repo's usual env; locally C:\Users\fires\.conda\envs\hmasd-amd-cpu
deps        numpy only, for this script
entry       scripts/audit_d7_s_persistence_margin.py
tests       pytest tests/audit_d7_s_persistence_margin_test.py     (13 pass)
```

Run the tests first. If any fail, stop and report — do not run the sweep against a
failing harness.

## Why 64 episodes

Because 4 was not enough and the data now says by how much.

At 4 episodes the normalizer `B_H` is statistically indistinguishable from zero at
both short horizons, so every normalized margin there is uninformative:

| H | `B_H` point | `B_H` 95% CI | `norm_stable` CI | sign stable |
|---:|---:|---|---|---|
| 139 | −1.514 | −3.76 .. +1.79 | −115 .. +1945 | no |
| 450 | +10.149 | −26.6 .. +46.9 | −16.8 .. +14.6 | no |

Back-solving from those standard errors, `B_H` at H=450 needs on the order of **52
episodes** before its interval excludes zero. H=1500 has a much larger `B_H`
(63.53 at 4 episodes) so it may need fewer, but its variance is not yet measured.
64 is chosen to be above the H=450 requirement rather than tuned to H=1500's
unknown one, because an underpowered re-run costs another full night.

**Do not treat 64 as established.** The finished run now writes `per_episode` arm
returns into the result JSON precisely so required-n can be recomputed from it
without re-running. If the H=1500 interval still straddles its threshold, compute
the needed n from those per-episode values and run that.

## How to read the output

`<out>/d7_s_persistence_margin.json`. Read it in this order, and stop at the first
failure:

1. **`arms_all_equal`** must be `false`, and **`probe_qos_saturation_fraction`**
   should be well under 1.0. A saturated instrument separated no arm at all once
   already, and that is what these two exist to catch.
2. **`energy_diagnostics[*].charge_steps`** must be non-zero at H=1500. If it is
   zero, energy never bound and the run measured an energy-inert regime under an
   energy-enabled label. `dock_events` is trustworthy again as of commit `c138d5d`;
   before that it was pinned to zero by an aliasing bug.
3. **`b_h`** must be clearly positive, and **`intervals.b_h`** must exclude zero.
   If it does not, nothing normalized by it means anything, whatever the margins
   say.
4. **`intervals.normalized_stable.ratio_sign_stable`** must be `true`. When false,
   the denominator changed sign across bootstrap resamples and the interval is
   meaningless however narrow it prints.
5. Only then read **`normalized.stable`** against its `-0.10` ceiling, with
   `intervals.normalized_stable`.

### Read the stable margin only

`normalized.flex` and anything derived from it is **not the estimand** and must not
be reported. The frozen design defines the `set_flex` arm as "that service UAV
re-decides each check", which is exactly what `constructive` already does for every
UAV, so the two arms are the same arm — confirmed by grep (no `set_flex` branch
exists) and numerically (`U*_flex == constructive − keep_flex` at every horizon).

That makes `U*_flex / B_H = (constructive − keep_flex) / (constructive − null)`:
the treatment arm and its own normalizer share a term, which `D0` forbids.

This matters more than a footnote, because **at H=1500 on 4 episodes the gate fired
`PERSISTENCE_NECESSARY_SOURCE`** — the headline the whole D7.S line is chasing —
and it fired on that degenerate arm. If the 64-episode run fires it again, it is
still not claimable. Correcting the arm is a protected-semantics change and belongs
to External Pro, not to whoever runs this job.

## What is settled — do not re-derive

- **The instrument is reproducible as of commit `847fd8a`.** Two processes with
  identical arguments return byte-identical `arm_means`, `b_h`, saturation and
  energy diagnostics. Verified again across days: the 2026-07-26 H=139 and H=450
  runs reproduced 2026-07-25's exactly.
- **Exchange always costs.** `U*_stable` is negative at all three horizons (−50.3,
  −60.6, −9.4). An earlier `+21.18` at H=1500 was a topology artifact, and the
  amortization-plus-charge-logistics story invented to explain it is retracted.
- **Energy binds only at H=1500.** `charge_steps` is exactly 0.0 at H=139 and
  H=450, and 678.5 at H=1500. The energy duty window is ~1500 steps because
  time-to-first-dock (~1071 steps) dominates the ~403 s charge duration; `D0`'s
  earlier `~400-500` figure counted the charge alone and was wrong.
- **`H` is per mechanism, not per source.** Scenario 7 carries two windows —
  exchange ~139 steps, energy ~1500 — and one `H` misprices whichever it was not
  derived from.
- **The gate stays on point estimates.** Thresholds were frozen as point
  conditions; re-specifying them as interval conditions after seeing output would
  renegotiate a frozen threshold. The intervals are diagnostics.

## Traps that already cost runs

- **The environment ignores its seed for topology.** `ground_bs_positions` and
  `charging_station_positions` are drawn at *construction* from `np_random` before
  any seed exists (`scenario_base.py:650-666` under `randomize_bs`, and
  `scenario7_energy_aware.py:313`), and `reset(seed=)` never regenerates them. Two
  constructions differed by 2125 m and 1487 m; the same arm on three fresh envs
  spread 17 %. Seeding the *global* RNG first does **not** help — the draw is off
  `np_random`. `build_env` now pins it from `--topology-seed`. This silently
  destroyed a three-point horizon sweep before anyone looked at it.
  **This is wider than this audit** and likely affects other experiments in the
  repo; it has not been assessed beyond D7.S.
- **`reset(seed=)` does not clear everything.** Eight attributes survive it,
  including `user_pause_times`, `last_global_sync_step` and
  `previous_connections_snapshot`. The first run on an env starts pristine and
  every later one starts used, so whichever arm ran first was privileged — and it
  was always `constructive`, the arm `B_H` is built from. Hence a fresh env per
  arm.
- **An impossible pair of diagnostics is a bug, not a finding.** `charge_steps` of
  647.5 alongside `dock_events` of 0.0 was numpy aliasing: `np.asarray` on a
  matching dtype returns the *same object*, so the rising-edge test compared a
  buffer against itself.
- **A point estimate near its threshold is not a result.** H=450's `−5.974` looked
  like a comfortable clear and its interval spans `−16.8 .. +14.6`.

## Sharding, if you want it

Episodes are independent and seeded as `seed = --seed + 100000 + i`. To shard,
run disjoint episode ranges and pool the `per_episode` arrays afterwards. There is
no `--episode-offset` flag today, so sharding needs either a small patch adding one
or separate `--seed` values chosen so the ranges do not overlap. Pool by
concatenating `per_episode` and recomputing the means, `B_H` and the bootstrap —
**do not average the normalized margins across shards**, since a ratio of means is
not the mean of ratios.

## Bring the results back

Commit the whole `logs/<run-id>/` directory — `d7_s_persistence_margin.json` and
`audit_stdout.log` — and push. Nothing else needs to move; the analysis reads only
that JSON.

## State of play

```text
harness            repaired, verified, 13 tests
H=139  ep4         complete, B_H indistinguishable from zero
H=450  ep4         complete, B_H indistinguishable from zero
H=1500 ep4         complete, gate fired but on a degenerate arm
H=1500 ep12        STARTED LOCALLY, KILLED INCOMPLETE, no JSON written
H=1500 ep64        <- the job in this handoff
```

Then one External Pro round carrying four coupled items: the `set_flex`
realization, `Delta` being absent from the instrument (D0 freezes it at one check
interval; the keep arms hold for the whole window), the absence of any `H` where
margin and normalizer are both well behaved, and the seed-ignoring topology.

`D8` stays blocked in every branch until part B resolves.
