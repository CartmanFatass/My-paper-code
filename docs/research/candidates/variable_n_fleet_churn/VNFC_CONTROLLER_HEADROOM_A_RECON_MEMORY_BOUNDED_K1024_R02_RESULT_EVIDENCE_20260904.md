# VNFC memory-bounded K=1024 controller-headroom R02 — result evidence

- Direction: `variable_n_fleet_churn`
- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02`
- Evidence class / claim ceiling: **A/RECON**, one finite sixteen-world controller-headroom fact
- Frozen card: `VNFC_CONTROLLER_HEADROOM_A_RECON_MEMORY_BOUNDED_K1024_R02_SCIENCE_CARD_20260904.md`
- Direction authority: `PRO_FINAL / OPEN_MEMORY_BOUNDED_K1024`
- Launch SHA: `6bd4e37d88e8e7c17cead3c233d20017db964ef8`
- Remote task: `vnfc-mb1024-r02-6bd4e37d-20260904-02` on `wsl_4070`
- Runtime summary:
  `temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/remote_attempt_02_result/summary.json`
- Summary SHA-256: `935d46a903d535a425263dd6215b2e873a82ac7b8d091bbc9c653aaad0c79ccb`
- Published branch: **`MB1024-D / BOUNDED_SEARCH_REMAINS_UNRESOLVED`**

## 1. Bounded result

On the unchanged first-primary R02 sixteen-world `heldout-N7` panel, the exact memory-bounded
full-tape `K=1024` search does not add a new lower-bound witness above the accepted `K=256`, exact
PERSIST, and BCRH tuple. Aggregate mean headroom remains `L=7/960=0.007291667`; zone 1 remains
`L=0`; zone 2 remains `L=7/480=0.014583333`. The unchanged upper-bound means remain
`U=3299/4800`, `183/320`, and `3853/4800` for the aggregate, zone 1, and zone 2.

K=1024 does expose one real width effect: in zone 1, row 5 it raises the accepted K=256 endpoint
from `24/80` to `34/80`, a difference of `1/8`. That endpoint only reaches the exact PERSIST and
BCRH endpoint `34/80`, so it does not increase `L`. The already known zone-2 row-3 witness remains
the sole individual material world: `28/120` versus BCRH/PERSIST `14/120`, hence `L=7/60`.

All three required lower-bound means are below `0.10`. The frozen rule therefore maps the complete
valid result to **`MB1024-D / BOUNDED_SEARCH_REMAINS_UNRESOLVED`**.

This is a direct measurement fact about the named panel, native host, BCRH/PERSIST implementations,
accepted K=256 witness, and K=1024 full-tape search. It does not establish BCRH optimality, absent
physical headroom, learner competence, or MAPR value. It is not an arbitrary-N, repeated-churn,
transfer, safety, flight, deployment, C, or Portfolio result.

## 2. Remote launch and engineering conformance

CM repaired the pre-result Linux build surface at `ce80bc1436be9c1997949e4f9f47cb77240146fd`:
the unchanged owned C++ translation unit builds as a `.so`, the two frozen uint64 intrinsics have
exact GCC implementations, and Linux peak RSS uses `getrusage` in bytes. Independent review found
no material issue. The result runner's CLI, schema, search ordering, native arithmetic, RNG,
comparators, and result rule did not change. The final Linux configured-interpreter focused pass at
the launch surface was `18 passed, 2 skipped, 1 warning in 8.91 s`; the two skips are historical
MSVC-only interactive cross-checks, while the K=1024 `.so`, full toy, selector, RSS, branch, and
world-byte tests ran on Linux.

The prebuilt analysis library was 187,376 bytes with SHA-256
`47d96d83ac83000463c3c4609f8276e14679165b7eb0312550711e3313d3d765`. The exact accepted K=256
witness was present with SHA-256
`3bdff4a303218438c38c7d73534894e6bfc3a2e5acd385952c4fdee73db882fc`.

Immediately before attempt-02, the detached remote worktree was clean at the launch SHA; the new
task, preflight receipt, and result root did not exist; attempt-01 was terminal; and no process
targeted the runner. The single `agent-task` payload was:

```text
cd /home/wu/hmasd-worktrees/vnfc-mb1024-r02-ce80bc14-20260904-01 &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory
  --out .../controller_headroom_mb1024_r02/remote_attempt_02_preflight.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_controller_headroom.py
  --output-root .../controller_headroom_mb1024_r02/remote_attempt_02_result
  --preflight-receipt .../controller_headroom_mb1024_r02/remote_attempt_02_preflight.json
  --launch-sha 6bd4e37d88e8e7c17cead3c233d20017db964ef8
  --seed 2026090311 --beam-width 1024 --max-wall-seconds 2700
```

The authoritative task handle is `vnfc-mb1024-r02-6bd4e37d-20260904-02`, wrapper PID `19240`.
It reached terminal `finished`, exit code `0`, after 21 task seconds. No send was repeated. The
request-specific result root was copied only after terminal status; local and remote hashes match.

The fresh admission in that same task records:

| field | observed |
| --- | ---: |
| captured / assessed | `2026-09-04T14:23:41.724557Z` / `14:23:41.724912Z` |
| physical available | `12,885,045,248` bytes |
| effective available | `12,885,045,248` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |
| receipt SHA-256 | `58ede1161122c7c2d205c33826edb8b544ade0798c16833f49fa1f7cd7013471` |

The earlier task `vnfc-mb1024-r02-cccecffd-20260904-01` is permanently quarantined as
`PACKAGING_FAILURE / MB1024-INCOMPLETE`: its sparse checkout omitted the K=256 witness and it
failed before the first native world call. Its failure was reproduced, separately recorded, and
has no scientific polarity or object consumption.

## 3. Frozen assignment and validity

The runner regenerated exactly the carded namespace
`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/2026090311`, purpose `heldout-N7`,
zones 1 and 2, rows 0 through 7. It used the unchanged BCRH, exact persistent class, accepted K=256
witness, and fixed-capacity K=1024 reducer. The complete exogenous tape was available only to the
search/reference paths; BCRH retained its causal current-information law.

All 16 worlds report:

- `measurement_complete=true`; terminal, safety, and exclusivity validity;
- exact endpoint unit-interval and `0 <= L <= H <= U` ordering;
- K=1024 non-regression against accepted K=256;
- selector conformance, dynamic capacities at most 1,024, and live nodes at most `2K+1=2049`;
- BCRH scorer/checker/independent-enumerator agreement for all 96 decisions and 63,313 candidates,
  with exact candidate records;
- exact PERSIST/sensitivity-maximum agreement; and
- positive OS RSS and the strict resource bound.

There is no learner: parameters, initialisations, optimizer steps, training transitions,
checkpoints, and checkpoint selections are zero. Parameter displacement against initialisation
scale is not applicable.

## 4. Per-world observations

Fractions are exact native failed-zone delivered/demand endpoints. `DeltaK` is K=1024 minus the
accepted K=256 endpoint. `L` still takes the maximum over K=1024, accepted K=256, PERSIST, and
BCRH, so a width effect that merely reaches PERSIST does not create controller headroom.

| zone | row | failed rank | BCRH | PERSIST | K=256 | K=1024 | DeltaK | L | U | expansions | live high | replacements |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 5 | 24/60 | 24/60 | 7/30 | 14/60 | 0 | 0 | 3/5 | 192,845 | 1,610 | 1,024 |
| 1 | 1 | 1 | 24/60 | 24/60 | 2/5 | 24/60 | 0 | 0 | 3/5 | 201,662 | 2,049 | 1,025 |
| 1 | 2 | 5 | 24/80 | 24/80 | 3/10 | 24/80 | 0 | 0 | 7/10 | 227,910 | 2,049 | 1,413 |
| 1 | 3 | 5 | 24/60 | 24/60 | 2/5 | 24/60 | 0 | 0 | 3/5 | 205,114 | 2,049 | 1,025 |
| 1 | 4 | 1 | 34/80 | 34/80 | 17/40 | 34/80 | 0 | 0 | 23/40 | 269,099 | 1,798 | 1,233 |
| 1 | 5 | 5 | 34/80 | 34/80 | 3/10 | 34/80 | 1/8 | 0 | 23/40 | 260,294 | 2,049 | 1,759 |
| 1 | 6 | 1 | 54/80 | 54/80 | 27/40 | 54/80 | 0 | 0 | 13/40 | 227,257 | 2,049 | 714 |
| 1 | 7 | 1 | 24/60 | 24/60 | 2/5 | 24/60 | 0 | 0 | 3/5 | 122,462 | 1,192 | 777 |
| 2 | 0 | 1 | 14/120 | 14/120 | 7/60 | 14/120 | 0 | 0 | 53/60 | 162,995 | 1,850 | 1 |
| 2 | 1 | 1 | 14/100 | 14/100 | 7/50 | 14/100 | 0 | 0 | 43/50 | 254,491 | 1,965 | 2 |
| 2 | 2 | 5 | 14/100 | 14/100 | 7/50 | 14/100 | 0 | 0 | 43/50 | 209,063 | 2,049 | 0 |
| 2 | 3 | 1 | 14/120 | 14/120 | 7/30 | 28/120 | 0 | 7/60 | 53/60 | 172,227 | 1,223 | 2 |
| 2 | 4 | 1 | 14/100 | 14/100 | 7/50 | 14/100 | 0 | 0 | 43/50 | 102,813 | 1,223 | 1 |
| 2 | 5 | 5 | 14/60 | 14/60 | 7/30 | 14/60 | 0 | 0 | 23/30 | 209,063 | 2,049 | 0 |
| 2 | 6 | 1 | 14/80 | 14/80 | 7/40 | 14/80 | 0 | 0 | 33/40 | 271,689 | 2,049 | 1 |
| 2 | 7 | 5 | 31/60 | 31/60 | 31/60 | 31/60 | 0 | 0 | 29/60 | 609,655 | 2,049 | 1,014 |

## 5. Cost and resource record

| quantity | actual |
| --- | ---: |
| BCRH decision calls / scored candidates | `96 / 63,313` |
| K=1024 beam expansions / native ticks | `3,698,639 / 73,972,780` |
| persistent candidates / native ticks | `16,149 / 968,940` |
| terminal-completion native ticks | `1,920` |
| result wall | `18.210753208 s` |
| task wall | `21 s` |
| peak RSS | `635,392,000` bytes |
| max dynamic search-owned bytes | `1,122,852` bytes |
| conservative fixed allowance | `31,585` bytes |
| peak RSS plus fixed allowance | `635,423,585` bytes |
| max live nodes | `2,049` |

All actual work is below the prospective bounds. The top-level RSS is positive; every world is
strictly below 2 GiB after the conservative fixed allowance; and the result is not
`resources_unmeasured`.

## 6. Frozen rule applied verbatim

The card says:

1. `MB1024-A` iff aggregate, zone-1, and zone-2 lower-bound means are each at least `0.10`.
2. `MB1024-D` for every other complete valid result.
3. Any missing validity/resource/non-regression condition is `MB1024-INCOMPLETE` and has no science.

I independently recomputed the exact means from all sixteen per-world `L` fractions:

```text
aggregate = 7/960
zone 1   = 0
zone 2   = 7/480
```

Each is below `1/10`, all validity conditions pass, and `ZONE_LOCALIZED_WITNESS=false` because no
zone mean reaches the margin. The result is therefore **`MB1024-D / BOUNDED_SEARCH_REMAINS_UNRESOLVED`**.

## 7. Predictions on record

The DM predicted `MB1024-D` with moderate confidence. That prediction is borne out. Width did
recover one K=256-pruned zone-1 endpoint, but it did not create any new lower-bound headroom above
the exact comparator tuple. Owner prediction: `not taken (unattended)`.

## 8. Limits and strongest readings

No deviation from the valid attempt's frozen population, seed, width, comparator, tie, endpoint,
resource, exposure, cap, or branch semantics was identified. The two preceding platform/packaging
defects were resolved or quarantined before the valid attempt and are not scientific observations.

Strongest support for a width-limited predecessor is zone-1 row 5: K=1024 improves K=256 by `1/8`.
Strongest contradiction to the proposed panel-wide opportunity is that the improvement only reaches
PERSIST/BCRH, the witnessed lower-bound vector is unchanged from K=256, and zone 1 remains exactly
zero. The surviving alternative is not another width: the bounded beam's cumulative-service rank,
the current host/population, or `R_fail_60` estimand may leave the unknown optimum unidentified.
The exact physical upper bounds remain wide.

Per the frozen card, the bounded search family now returns to
`em:variable_n_fleet_churn:convergence` for `RECAST_HOST_OR_ESTIMAND`. This result does not authorize
MAPR, another K, or any local direction/lifecycle decision.

