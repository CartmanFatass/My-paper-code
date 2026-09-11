# N3 DISH B01 C04 seed 29 — result evidence

Date: 2026-09-04. **B / EXPLORE**, valid complete seed observation. Two of three carded seeds
are complete; no aggregate `FTS-*` branch is issued and no source-effect estimate is identified.
Card and interpretation conventions remain `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`.

## Direct result and unchanged rule

Seed 29 completed the exact sixteen-row panel after 64 updates. Every row exhausted its 1,200-tick
prefix without a first-valid trigger: **0/16 triggers, 19,200 prefix ticks, 0 branch ticks**.
The card says: "A seed has **usable trigger support** when at least four of sixteen rows trigger
and the triggered set contains both packages." This seed fails that predicate.

The aggregate instruction is "Apply the following branches in order to three complete seed
summaries:". Only two are complete, so the aggregate rule is not applied early. The raw zero
COPY/SHADOW differences and true `shadow_nonharm` remain empty-support reducer defaults; they
are not equal sampled returns or observed nonharm. No conditional endpoint or branch receipt is
missing from this legitimate no-trigger path. This is not a source-value negative or N3 closure.

## Counts, exposure and independent reading

| Quantity | Observation |
| --- | ---: |
| Native training transitions / learner updates | 262,144 / 64 |
| Optimizer minibatch steps / checkpoint update | 2,048 / 64 |
| Model tensors / finite | 50 / all |
| Optimizer states / finite / step values | 36 / all / 2,048 |
| Actor / snapshot / critic Welford counts | 1,048,576 / 0 / 262,144 |
| Declared distinct panel tuples / triggered | 16 / 0 |
| Evaluation prefix / branch ticks | 19,200 / 0 |
| Initial / final parameter norm | 38.286447586375616 / 41.81658102299228 |
| Actual relative total L2 displacement | 0.419585027483137 |
| Raw maximum per-tensor displacement ratio | 1.0764195675299437e300 |

DM parsed the original JSON, independently reconstructed its two-package x two-schedule x two-speed
x two-slot tuple set and zero-trigger count, checked prefix exhaustion, and verified the tracked
summary equals the collected original bytes. CM loaded the existing checkpoint, checked finiteness
and counters and recomputed the final norm exactly. No new model, RNG master or learner run was
created by collection. Initial norm/displacement remain original runner observations; initial
checkpoint bytes were not separately published.

As for seed 11, the large finite per-tensor ratio is dominated by the code's denominator floor
`max(initial_tensor_norm,1e-300)` for initially zero biases. It is preserved as a descriptive
zero-reference diagnostic, not a meaningful relative percentage or a nonfinite learner state.
Total displacement is finite and nonzero. No post-result metric change was made.

## Receipts and resource use

- Source `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`; CPU/one Torch thread, carded precision/RNG.
- Node `wsl_4070`, cwd `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
- Task `dish_b01_c04_seed29_e0541d0c_a1`, PID 607075, exit 0.
- Start/terminal `2026-09-05T00:47:14Z` / `2026-09-05T01:04:11Z`; logged supervisor wall **1017 s**.
  Tracker's later uptime of 1104 s includes post-terminal time and is not the run duration.
- Runner wall **977.5005878610027 s**; peak RSS **628,461,568 bytes**; resources measured.
  Both wall measures are below the unchanged **1,474.544745605439 s** per-arm projection and
  **1,800 s** cap. The complete invocation is charged independently to each source arm.
- Fresh receipt at `2026-09-05T00:47:14.317386Z`: physical and effective available memory each
  **15,432,970,240 bytes**, floor **4,294,967,296**, all pass flags true.
- Receipt/output: cwd-relative `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed29_a1_admission.json`
  and `seed29_a1/`; receipt remains outside output.
- Original log/wrapper/status/exit witnesses remain under
  `/home/wu/.agent-tasks/dish_b01_c04_seed29_e0541d0c_a1/`.

CM collected the original JSON, **2,070,711-byte** checkpoint, log/wrapper and receipt under the
same relative root in `C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904`. Tracked raw summary
and collection record are `N3_DISH_B01_C04_SEED29_SUMMARY_20260904.json` and
`N3_DISH_B01_C04_SEED29_COLLECTION_20260904.md`, pushed at `da86d9126ebf15a87cd16bde68dbe623082b855c`.

## Validity, prediction and limits

Real learning, nonzero actual exposure, exact panel and checkpoint/summary publication are complete.
No scientific/numerical/RNG/checkpoint/side-effect deviation, section-4 addition or section-5 breach
was found. Full automated `_run` publication coverage remains open, although the real no-trigger
publication path has now completed twice; no triggered scientific branch has been observed.

This second no-trigger seed is consistent with the DM's original support prediction; final scoring
awaits the full seed set. The owner prediction remains **not taken (unattended)**. Tuned headroom
is absent and the five-tick MEI is not estimable without a source fork.

Strongest support is complete prefix exhaustion in two independently trained checkpoints despite
nonzero parameter movement. The limit against a source negative is complete non-exposure of the
source contrast; trigger competence and physical opportunity are still unidentified. Seed 47
continues unchanged, and all original seed observations remain visible. A/B have no consumption.
