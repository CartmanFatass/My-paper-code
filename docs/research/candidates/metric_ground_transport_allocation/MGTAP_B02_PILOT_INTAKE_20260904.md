# MGTAP B02 cost pilot — DM intake

Date: 2026-09-04. Class: **B/EXPLORE development**. Direction:
`metric_ground_transport_allocation`; DM `/root/dm_amx_n5_allocation`.
Card: `MGTAP_B02_CURVES_SCIENCE_CARD_20260904.md`, commit `22ae3de13`.
Pilot launch SHA: `f3595bfe3e90024f3b31eb8a82910304b90543d3`.

## What I checked

I read the CM's `MGTAP_B02_TECHNICAL_EVIDENCE_20260904.md` and
`MGTAP_B02_PILOT_RESULT_EVIDENCE_20260904.md` (evidence commit `cb86c6419`), the collected
pilot `summary.json` (also preserved as `MGTAP_B02_PILOT_SUMMARY_20260904.json`),
the node-local `admission.json`, and the two learner traces including their first
and last rows. I compared mode, seed, arms, N, dtype, device, thread count,
optimizer, update/evaluation budgets and cost formula with the card. The
independent review reported no material semantic finding; nine focused checks
passed locally and nine passed remotely in 4.69 seconds before the pilot.

The accepted task was `mgtap_b02_pilot_1907_f3595bfe` on `wsl_4070`, cwd
`/home/wu/hmasd-worktrees/mgtap_b02_20260904`. The output root is that cwd plus
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907`.
The local collection is the same relative path in
`C:/Projects/HMASD-worktrees/cm-n5-b02-20260904`. The supervisor log and exit
witness are under `/home/wu/.agent-tasks/mgtap_b02_pilot_1907_f3595bfe/`.
CM directly observed terminal exit 0 at `2026-09-04T22:42:12Z`; the tracker
handoff was acknowledged as terminal before adoption. No duplicate launch occurred.

Admission at `2026-09-04T22:42:10.331246Z` measured physical and effective
available memory of 15,403,864,064 bytes, above the 4-GiB floor. Both arms completed
16 updates, 1,536 training allocation transitions and 9,216 training agent steps;
each evaluated 1,536 two-epoch episodes, 3,072 allocation decisions and 18,432
agent steps at exactly 0 and 16. There are 16 learner trace rows per arm, no
missing checkpoint or learner measurement, and no main-seed observation.

The first parameter displacements were METRIC 0.01736978019 and FREE 0.01740489533.
At update 16 the distances from initialization were 0.21775812482 and
0.20307325464; cumulative paths were 0.24608940592 and 0.23858756545. This
directly confirms nonzero learner motion without supplying an efficacy claim.

## Pilot observations and cost rule applied verbatim

Both arms started at native return 0.24670138889. At update 16, METRIC returned
0.27808702257 and FREE 0.27406955295. The +0.00401746962 difference is a
one-seed development observation, excluded from the three-seed main estimand.
The deterministic matched population oracle is 0.66875 at both N=4 and N=8.
The untuned 16-update FREE-oracle gap does not establish a tuned host headroom record.

The card's cost law is **`P_A=2*3*(256*u_A+17*e_A)`**, with a **300-second cap
per arm over all three main seeds**. The runner measured:

| Arm | u: seconds/update | e: seconds/full N4/8 evaluation | P: seconds/all three main seeds |
| --- | ---: | ---: | ---: |
| METRIC | 0.007148870814 | 0.004888009498 | 11.4792425385 |
| FREE | 0.003733942001 | 0.004117850498 | 6.1553556643 |

Both projections are below 300; no budget or arm is changed. Shared setup/oracle
cost was 0.0649809940 seconds. Pilot runner wall was 0.7667597880 seconds;
supervisor duration was 2 seconds, separately reported. Peak RSS was 482,607,104
bytes. The first METRIC update included a 0.05724943-second warm-up, and METRIC
ran first; the resulting cost difference is a scheduling measurement, not a
causal algorithm compute-efficiency comparison. Full arm walls, 0.6318547110
and 0.0686737050 seconds, include unequal startup overhead.

The card's main result branches require the complete three-seed 17-point panel;
that panel does not yet exist, so no main scientific branch is applied. The
pilot is valid B-development data and prices the unchanged planned invocation.
Test success and process exit are engineering evidence only. No section-4
machinery was added; reported research size 375 lines, runner 167, orchestration
approximately 28%, with no section-5 breach. The toy smoke reaches publication;
the full main grid and main oracle-input CLI have not yet been exercised together
at runtime and remain the next engineering observation.

## Prediction check and bounded reading

The main DM prediction remains on record and unscored. The owner's prediction
is **not taken (unattended)**; both local and Root integration owner-review
surfaces contained no new applicable instruction at this boundary. The pilot's
small positive endpoint difference does not score the AUC prediction.

Strongest support: the real inherited learner moves, both arms' native returns
increase, and measured cost is far inside the declared cap. Strongest caution:
only one 16-update development seed was observed; there is no main AUC or tuned
baseline. Generic conditioning/effective step size remains a live explanation.
Both stopped C objects retain their terminal nonidentification meanings.

## Decisions this intake produces

### 1. Accept pilot development evidence — object tier

Options: (a) accept the complete pilot and its cost projection at the development
ceiling; (b) quarantine or repeat a conforming pilot; (c) label its endpoint
difference as the main result. Recommendation: **(a)**. The carded counts and
measurements exist; neither repetition nor promotion follows from these data.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Provenance `OWNER_DELEGATED`; reversible; kind `technical`; owner flag `none`.

### 2. Execute the unchanged fixed main panel — object tier

Options: (a) run main seeds 203, 211 and 223 at 256 updates under the existing
card, each newly admitted on the same remote node; (b) stop this round after
pilot cost alone. Recommendation: **(a)**. The current frozen comparison is
complete enough to answer its B question and its measured projections fit the
cap by a large margin. The owner explicitly permitted completion of this fixed
panel within the safe end-of-round drain; no arm, budget, parameter or new round
is authorized. Reuse the pilot oracle read-only outside the learner and accumulate
setup against the same 60-second total cap. Each seed retains its 100-second
per-arm limit and fresh adjacent node-local admission.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Provenance `OWNER_DELEGATED`, with owner-direct drain boundary relayed by Root;
reversible; kind `selection`; owner flag `none`. No direction/Portfolio action.

After the fixed panel, take it in and stop the round. If a dependency or technical
failure stops B02, preserve a reviewed clean boundary instead of starting a fresh
repair/attempt loop. No successor card, expanded sweep or old-C repeat follows.
