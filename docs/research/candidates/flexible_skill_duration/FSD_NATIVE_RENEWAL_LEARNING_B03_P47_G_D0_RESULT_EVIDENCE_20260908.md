# FSD B03 P47 terminal collection: G and D0

Technical acceptance of the two completed arms, collected on2026-09-08 from
`hmasd-wsl-node` under the [P47 bound route](FSD_NATIVE_RENEWAL_LEARNING_B03_P47_ROOT_HANDOFF_20260908.md).
No H terminal artifact was supplied for this collection; no H−D0 polarity or
three-policy completion is asserted. DM owns scientific intake.

Raw byte copies and computed readback checks are under
[native_renewal_learning_b03_p47_20260908/collected](native_renewal_learning_b03_p47_20260908/collected/).
Each G/D0 folder holds the original summary, admission, full supervisor task.log,
runner.sh, status, exit_code, pid, start_time and complete-command time/RSS file.
The remote D0 learner_logs/evaluation_logs directories contain no files; SCP's
nonrecursive wildcard reported these empty directories as not regular files,
but copied all existing regular files. No log content was omitted.

## Terminal and resource facts

| Arm/handle suffix | Supervisor | Complete wall | Complete peak RSS | Cap |
| --- | --- | ---: | ---: | ---: |
| G: `fsd_native_b03_p47_G_f09aa00ba` | finished / exit0 | 2.47s | 458008KiB | 60s |
| D0: `fsd_native_b03_p47_D0_f09aa00ba` | finished / exit0 | 462.10s | 1361948KiB | 1200s |

Full handles are those in the table. Remote cwd is
`/home/wu/hmasd-worktrees/fsd-native-renewal-b03-p47-f09aa00ba`; final read-only Git
inspection returned exact HEAD `f09aa00ba0e6f7c709af188b61be6ff8e7e6bc96` and an
empty status. Scientific artifacts are its
`temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/{G,D0}`.
Supervisor roots are `/home/wu/.agent-tasks/<handle>/`; external time files are
`/home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/{G,D0}_process_time.txt`.

Both immediately adjacent admissions passed physical/effective floors4GiB:
G15648698368 bytes, D015639928832 bytes, measured through `/proc/meminfo`.
Separate external complete-command timers cover the bound shell/admission/import/
learning/evaluation/publication chain. Runner prepublication clocks are
G2.0303997159935534s and D0436.20912062202115s; task.log postpublication clocks
are2.0307489169645123s and436.210413992987s. These narrower runner clocks do not
replace complete wall. The artifact's external-clock field remains null; this
collection preserves the external measurement separately, without rewriting it.
No CPU work measurement was collected and no aggregate CPU value is inferred.

## Readback and acceptance

[Computed collection checks](native_renewal_learning_b03_p47_20260908/collected/G_D0_collection_checks.json)
passed over all stored numerical values, identities, counts and endpoint arrays.
Both summaries declare B03, accepted source, training770403/evaluation770404,
CPU4 and FP64 host/reward, final completed boundary and no failure. D0's seed is
770403/learner FP32; G seed is null with no learner. Host records match the card
and each other. Each final endpoint has IDs0–31,400 valid reward steps and32
terminal episodes; full/post returns match recorded sums divided by400/399.
Role counts/rates/loss arithmetic is consistent. All numerical JSON values are
finite; D0's only declared infinite costs are the metadata strings `Infinity`.

G: zero models/training/optimizer calls,400 greedy batches,12800 scoring steps.
D0: two models/one training start, no checkpoint load, five complete learning
rows over IDs0–79,32000 training transitions,80 training episodes and12800 scoring
steps. There are2000 training/400 evaluation agent batches. Actual optimizer
calls are coordinator750, discoverer actor18000, critic18000, team discriminator75,
individual discriminator300; all evaluation optimizer counts are zero. Every
row's cumulative optimizer count equals previous count plus its recorded delta.
First/final finite initialization-relative displacements are retained in the raw
summary and collection checks; no displacement threshold is imposed.

D0 metadata has mode d2, k/individual/team caps5/5/5, age off, high-level buffer1280
and batch128. Its numeric infinity constructor/evaluator path is established by
the accepted source and fake checks, not reconstructed from metadata alone.
Every training row has internal/applied renewal7680/7680, with individual/team
segment min/max5; final evaluation has matching internal/applied480 per episode
(full) and474 (post). These aggregates corroborate the accepted sampled-mask
wiring. They are not a saved per-step action/storage trace or an independent
RNG replay, neither of which this collection manufactures.

Raw full/post endpoint means for handoff: G .89078125/.8905075187969925;
D0 .38263020833333333/.3835891812865497. No comparison was assembled here and
no weakness/competence threshold was applied. Each completed arm is technically
readable within its own complete cap; the full card awaits H's own published pair.

No source changes, research invocation, retry, extra evaluation, post-cap fill,
new resource admission or production-root mutation occurred. Collection uses SCP
and local standard-library JSON/arithmetic only. Scope§4 additions:none.
Root continues the already supplied H route and sends its terminal facts to this
same CM; DM then performs original all-outcome intake from the published pair.
