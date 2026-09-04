# VNFC controller-headroom A/RECON R01 — result evidence

- Direction: `variable_n_fleet_churn`
- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-R01`
- Evidence class: **A/RECON**
- Frozen card: `VNFC_CONTROLLER_HEADROOM_A_RECON_SCIENCE_CARD_20260904.md`
- Launch SHA: `7cddfa241019feaab7897ab793d603433ca38140`
- Runtime summary:
  `temp/directions/variable_n_fleet_churn/exp/controller_headroom_r01/attempt_01_result/summary.json`
- Summary SHA-256: `5687572B44574F2AB7FF4055B2789E431EEF05A6893002625198E2DA3E910831`
- Published branch: **`CH-D / HEADROOM_BRACKET_UNRESOLVED`**

## 1. Bounded result

On the first valid R02 primary seed's exact sixteen `heldout-N7` worlds, the deterministic
full-tape `K=256` search plus the exact persistent-command maximum witnesses very little failed-zone
service above `BCRH-PERSIST`: aggregate mean lower bound `L=7/960=0.007291667`, zone-1 mean
`L=0`, and zone-2 mean `L=7/480=0.014583333`. Only one of sixteen worlds has a positive witnessed
headroom lower bound.

The exact physical upper bound remains loose: aggregate mean `U=3299/4800=0.687291667`, zone-1
mean `U=183/320=0.571875`, and zone-2 mean `U=3853/4800=0.802708333`. Therefore neither the
material-headroom branch nor the no-material-headroom branch is established. The frozen rule maps
the complete result to **`CH-D / HEADROOM_BRACKET_UNRESOLVED`**.

This is a direct measurement fact about the named sixteen worlds, native host, BCRH implementation,
and `K=256` search. It is not evidence that BCRH is sufficient, that no better controller exists,
that a learner can exploit any headroom, or that MAPR needs or does not need a larger budget. It is
not an algorithm effect, a C result, arbitrary-`N`, repeated-churn, transfer, safety, flight, or
deployment evidence.

## 2. Launch and engineering conformance

The card and its pre-launch factual corrections were committed and pushed before the result run.
CM accepted the implementation at `7cddfa241`: 892 non-test research-code lines, a 180-line runner,
about 22.6 percent orchestration, and no unrequested machinery. The implementation's declared
create-once output-root refusal is recorded in that commit's scope trailer. The post-edit focused
test was `11 passed in 8.22 s`; the immediately pre-launch focused test was `11 passed in 7.59 s`.
No third focused test was run.

The fresh central admission immediately before launch records:

| field | observed |
| --- | ---: |
| captured / assessed | `2026-09-04T10:16:15.907765Z` / `10:16:15.945313Z` |
| physical available | `12,125,368,320` bytes |
| effective available | `12,125,368,320` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |
| receipt SHA-256 | `8E3C9796584B84AE220FB45AA34A968D9BB01287EC01E8F097B81D432C9798E2` |

The worktree was clean at the exact launch SHA, the result root did not exist, and no Python process
targeted the runner. One hidden detached process was accepted as PID `23784`; no second process was
started. Its exact command was:

```text
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe scripts\run_vnfc_controller_headroom.py --output-root C:\Projects\HMASD-worktrees\codex-vnfc-controller-headroom-20260904\temp\directions\variable_n_fleet_churn\exp\controller_headroom_r01\attempt_01_result --preflight-receipt C:\Projects\HMASD-worktrees\codex-vnfc-controller-headroom-20260904\temp\directions\variable_n_fleet_churn\exp\controller_headroom_r01\attempt_01_preflight.json --launch-sha 7cddfa241019feaab7897ab793d603433ca38140 --seed 2026090311 --beam-width 256 --max-wall-seconds 2700
```

The process terminated after publishing exactly one complete `summary.json`; stdout and stderr are
both empty. The detached Windows process object was not retained, so its exit code is unavailable.
No scientific conclusion depends on the exit code.

## 3. Frozen assignment and validity

The runner regenerated the actual first valid R02 primary population under namespace
`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/2026090311`, purpose
`heldout-N7`, zones 1 and 2, rows 0 through 7. It used the unchanged six-step BCRH comparator, the
exact full-tape persistent initial-command maximum, and the deterministic three-decision `K=256`
beam. Endpoints and selection froze after epoch 2 at sixty post-loss seconds; the two search paths
then used separately recorded lexicographically smallest legal terminal-completion suffixes.

All 16 worlds report:

- `measurement_complete=true` and native terminal completion;
- no safety or exclusivity violation;
- endpoint values in `[0,1]` and exact `0 <= L <= H <= U` ordering;
- agreement between BCRH scorer, checker, and independent legal-command enumerator at all 96
  decisions, with exact candidate-record digests;
- agreement of the separately enumerated persistent maximum with the native sensitivity maximum.

There is no learner: parameters, initialisations, optimizer steps, training transitions, and
checkpoints are all zero. Parameter displacement against initialisation scale is not applicable.

## 4. Per-world observations

Fractions below are the exact native failed-zone delivered/demand endpoint values. The witness is
the maximum used in `L`; a beam value below BCRH cannot lower the bound.

| zone | row | failed rank | BCRH | persistent max | K=256 beam | L | U | witness | beam expansions |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 0 | 5 | 24/60 | 24/60 | 14/60 | 0 | 3/5 | persistent | 55,402 |
| 1 | 1 | 1 | 24/60 | 24/60 | 24/60 | 0 | 3/5 | beam | 52,882 |
| 1 | 2 | 5 | 24/80 | 24/80 | 24/80 | 0 | 7/10 | beam | 56,373 |
| 1 | 3 | 5 | 24/60 | 24/60 | 24/60 | 0 | 3/5 | beam | 55,866 |
| 1 | 4 | 1 | 34/80 | 34/80 | 34/80 | 0 | 23/40 | beam | 65,428 |
| 1 | 5 | 5 | 34/80 | 34/80 | 24/80 | 0 | 23/40 | persistent | 56,730 |
| 1 | 6 | 1 | 54/80 | 54/80 | 54/80 | 0 | 13/40 | beam | 74,270 |
| 1 | 7 | 1 | 24/60 | 24/60 | 24/60 | 0 | 3/5 | beam | 48,984 |
| 2 | 0 | 1 | 14/120 | 14/120 | 14/120 | 0 | 53/60 | beam | 39,665 |
| 2 | 1 | 1 | 14/100 | 14/100 | 14/100 | 0 | 43/50 | beam | 58,732 |
| 2 | 2 | 5 | 14/100 | 14/100 | 14/100 | 0 | 43/50 | beam | 120,669 |
| 2 | 3 | 1 | 14/120 | 14/120 | 28/120 | 7/60 | 53/60 | beam | 64,097 |
| 2 | 4 | 1 | 14/100 | 14/100 | 14/100 | 0 | 43/50 | beam | 56,948 |
| 2 | 5 | 5 | 14/60 | 14/60 | 14/60 | 0 | 23/30 | beam | 120,669 |
| 2 | 6 | 1 | 14/80 | 14/80 | 14/80 | 0 | 33/40 | beam | 61,405 |
| 2 | 7 | 5 | 31/60 | 31/60 | 31/60 | 0 | 29/60 | beam | 166,235 |

The lone positive witness is zone 2, row 3, where the beam raises `R_fail_60` from `14/120` to
`28/120`, giving `L=7/60`. In all eight zone-1 worlds and seven of eight zone-2 worlds the strongest
observed comparator/search endpoint merely ties BCRH.

## 5. Cost and resource record

| quantity | actual |
| --- | ---: |
| BCRH decision calls / scored candidates | `96 / 63,313` |
| beam expansions / native ticks | `1,154,355 / 23,087,100` |
| persistent candidates / native ticks | `16,149 / 968,940` |
| terminal-completion native ticks | `1,920` |
| wall | `11.0595644 s` |
| peak RSS field | `0` |

Actual work is below every prospective operation bound. The Windows memory call returned zero,
which is not a meaningful RSS measurement; the result is therefore **`resources_unmeasured`**.
Under the standing telemetry rule this does not annul a non-resource claim. The scientific
endpoints, counts, and required validity measurements are complete.

## 6. Frozen rule applied verbatim

The card applies the following ordered branches:

1. `CH-A`: aggregate and both zone lower-bound means are each `>=0.10`.
2. `CH-B`: aggregate and both zone upper-bound means are each `<0.10`.
3. `CH-C`: one zone lower-bound mean is `>=0.10` and the other zone upper-bound mean is `<0.10`.
4. `CH-D`: every other complete valid result.

`CH-A` fails because `7/960`, `0`, and `7/480` are all below `0.10`. `CH-B` fails because
`3299/4800`, `183/320`, and `3853/4800` are all above `0.10`. `CH-C` fails because neither zone
has a lower-bound mean at or above `0.10`, and neither has an upper-bound mean below it. All worlds
are complete and valid, so the result is **`CH-D / HEADROOM_BRACKET_UNRESOLVED`**. `INCOMPLETE`
is not reached.

## 7. Predictions on record

The DM predicted `CH-A / MATERIAL_HEADROOM`. That prediction is not borne out: the declared search
establishes a material per-world improvement only once and no aggregate or zone lower-bound mean
reaches the margin. The result also does not establish the opposite prediction because every upper
bound remains well above the margin. Owner prediction: `not taken (unattended)`.

## 8. Deviations, limits, and strongest readings

No deviation from the frozen scientific assignment was identified. The R02 namespace, actual
`heldout-N7` purpose, seed, rows, width, tie law, sixty-second freeze, terminal suffix, comparators,
integer endpoints, rule, cap, and one-invocation stop match the card.

Strongest support for unused controller headroom: the zone-2 row-3 full-tape command path doubles
failed-zone delivery from `14/120` to `28/120`, proving that BCRH is not per-world optimal on the
entire panel.

Strongest contradiction: the exact persistent comparator and the `K=256` beam do not beat BCRH in
15 of 16 worlds, and zone 1 has zero witnessed lower-bound headroom. That observation bounds this
search, not the unknown optimum.

Surviving alternative: the beam is too narrow or its cumulative-delivery pruning misses delayed
benefit. The physical upper bound is intentionally exact but loose, so it cannot distinguish that
alternative from near-saturation. A wider prospectively carded search is the next discriminator;
this result itself provides no permission to change width or rerun R01.
