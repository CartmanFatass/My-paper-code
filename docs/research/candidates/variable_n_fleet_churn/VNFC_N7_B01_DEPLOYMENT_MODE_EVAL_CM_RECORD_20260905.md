# CM record: VNFC N7 B01 deployment-mode evaluation entry

Engineering record for the objective
`VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_CM_OBJECTIVE_20260905.md` and the card
`VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_SCIENCE_CARD_20260905.md`. It records what was implemented,
what was directly observed, the frozen inputs and the two frozen remote commands. It launches
nothing, accepts no result and interprets no science.

## What exists

One evaluation-only entry that loads the four saved B01 final policies, runs both deployment
modes for each on one shared panel, runs fixed BCRH-PERSIST once on the same panel, and publishes
the policy x mode grid. Zero training: no optimizer is constructed, no parameter is updated, and
`optimizer_state` is never loaded. Source commit `384cc6f0e222c843ca656fa78053887abcdacb10` on
branch `worktree-agent-a054882d4e62cb3f5`.

| Path | A | D | What |
| --- | ---: | ---: | --- |
| `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/learning.py` | 8 | 1 | one optional `evaluation_uniforms` argument on `rollout` (default `None`) and its per-epoch use when `training` is false; the deleted line is the reflowed `def` line |
| `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/deployment_mode.py` | 249 | 0 | new: placeholder construction, `load_checkpoint`, the evaluation action-draw supplier, the policy x mode readout, the B01 greedy replay and the run/publication driver |
| `scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py` | 50 | 0 | new argparse entry, card defaults fixed in `build_config`, thread environment set before torch import, never calls `experiment.run` |
| `tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/test_deployment_mode_eval.py` | 229 | 0 | new focused test file |
| total | 536 | 1 | runner 50 lines; no orchestration module |

Unchanged and read-only: `experiment.run`, `readout`, `checkpoint`, `bcrh`, `publish_json`,
`cost_projection`, `worlds`, `native.py`, every R09/R02 module and `scripts/run_vnfc_bpcr_*.py`.
`scripts/run_vnfc_n7_direct_b01.py` is untouched, and a test asserts by AST that the two existing
`learning.rollout` call sites in `experiment.py` still pass eight positional arguments and at most
`check_presentation`, so both existing B01 profiles keep byte-identical behavior.

Engineering Scope Spec §4 additions: none. `scope: none`.

## Frozen inputs: the four final checkpoints

Read directly from `C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/<record>/checkpoints/`
and loaded through the new `load_checkpoint`; every field below is observed, not assumed.

| Record | Arm | File | Bytes | SHA256 | round | Parameters |
| --- | --- | --- | ---: | --- | ---: | ---: |
| `b01_formal_20260905_02` | MAPR | `MAPR_final.pt` | 2,168,441 | `1b36ccb40cdfd9e91433ed3c73b656492130ce00bfd0ee1bd7ddfd320c312971` | 64 | 89,090 |
| `b01_formal_20260905_02` | DIRECT | `DIRECT_final.pt` | 3,607,517 | `326cb831b924ddc456931fdafa0cc1381eb956bb63a52d1b8c56a3054cd461d2` | 64 | 148,739 |
| `b01_seed02_20260905_01` | MAPR | `MAPR_final.pt` | 2,168,441 | `e8dd2494436b1c6831fc0c541e745747024c67755524e0b54a4ddc9cad15d098` | 64 | 89,090 |
| `b01_seed02_20260905_01` | DIRECT | `DIRECT_final.pt` | 3,607,517 | `6da2ae47ec8a33f5608844b9b3d496b65236d0dc165747858808c0136245e019` | 64 | 148,739 |

All four carry `arm`, `checkpoint="final"`, `dtype="float64"`, `device="cpu"`,
`presentation="R02 canonical opaque rank"`; every tensor is CPU binary64. Loading each one into
exact-shape zero placeholders and comparing tensor by tensor against the saved `model_state` gave
bitwise equality for all four, and `parameter_state` displacement against the loaded values is
exactly `0.0` after all eight cells (the runner raises if it is not). The digests are compiled
into `deployment_mode.CHECKPOINT_DIGESTS`, so a staged byte difference stops the run before any
world is built.

Fifth frozen input, engineering check only: the recorded B01 formal02 evaluation rows,
`docs/research/candidates/variable_n_fleet_churn/evidence/b01_formal_20260905_02/evaluation_episodes.json`,
SHA256 `a1136869549aa054c067325fed5589e9b55bbd00c3f76ebbc242850e0ca1c43f` (448 rows, 64 of them
MAPR/final). `docs/` is outside the node's sparse checkout, so it is staged like the checkpoints.

## Semantics as implemented

- Panel: `learning.worlds(2026090505, "VNFC-N7-B01-DEPLOYMENT-MODE-20260905", "evaluation", 64)`;
  observed split 32 zone-1 / 32 zone-2. Disjointness from every B01 panel follows from the new
  namespace and world master, which change the stream master itself
  (`sha256("HMASD/VNFC-N7-DIRECT-B01/<namespace>/<seed>/exogenous-worlds")`); no census was added.
  The same panel object is passed to all eight cells and to BCRH, so worlds are paired.
- `GREEDY` passes `uniforms=None` and consumes no action draw (observed `action_draws == 0` per
  greedy cell). `SAMPLE` supplies one uniform per token per episode to the same forward's
  inverse-CDF branch. Both use the shared R09 forward, its masks, the fixed-occupant override and
  the same softmax; the only difference is the final choice line, which is already in that file.
- Evaluation action stream: `learning.rng(2026090506, namespace, "eval-actions/<record>/<arm>")`,
  addressed with the existing coordinate mechanism at
  `purpose="<namespace>/eval-action/<record>/<arm>"`, `episode_row=world`,
  `physical_time=20*epoch`, `draw=token`, `failed_zone` from the fixture. It shares no master, no
  purpose and no coordinate with the training `actions/<arm>` stream.
- **One deviation to note.** The card asks for a "new domain string" for the evaluation draws.
  `experiments/candidates/variable_n_fleet_churn_bpcr_r09/rng.py` refuses any domain outside the
  closed `empirical_contract.DOMAIN_LABELS` tuple, and that R09 file is a read-only input, so no
  new label could be added without the modification the objective says must return to the hub
  first. The entry therefore uses the registered conclusion-family label
  `conclusion/cut-derangement` (`deployment_mode.EVALUATION_ACTION_DOMAIN`) as the separation tag.
  It is distinct from `training/action`, it is used nowhere in the B01 path, and stream
  independence is carried by the dedicated master and purpose rather than by the label. If the
  hub prefers a genuinely new label, that is an R09 edit and a return.
- Publication: `evaluation_episodes.json` (one row per cell x episode with `record`, `arm`,
  `mode`, `zone`, `world`, every `terminal_metrics` field, flags and `recovery_observations_20s`),
  `bcrh_episodes.json`, `summary.json` (config, checkpoint digests, per-cell counts, exposure line,
  the grid readout, timings, wall, peak RSS), all written and read back through the B01 module's
  own `publish_json`. `run.log` is the redirected stdout/stderr of the frozen command.
- Readout: 16 paired contrasts (4 `SAMPLE − GREEDY` per policy, 4 same-mode MAPR − DIRECT within a
  training seed, 8 policy-mode minus BCRH) with per-episode rows retained and `all/zone1/zone2`
  strata, plus 9 cell means. The B01 six-cell `readout` is untouched and unused here.

## Local verification

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/test_deployment_mode_eval.py \
  -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/variable_n_fleet_churn/test/deployment-mode-eval-cm
```

`7 passed, 1 skipped in 2.16s`; the whole directory (adding the existing `test_output.py`) gives
`7 passed, 2 skipped in 1.93s`. The skips are the two output-reading tests, which need an existing
check output root. What the passing tests establish: placeholder construction and
`load_state_dict` round-trip for both arms with digest and round refusal; the four declared
digests, byte sizes, rounds and parameter counts against the actual local checkpoint files; that
the greedy branch is the masked maximum and both branches stay inside the masked support and honor
a fixed occupant; that the evaluation uniform stream is addressed, reproducible, distinct across
record/arm/world/epoch/token and disjoint from a training-stream block at the same indices; that
`experiment.py`'s two rollout calls do not pass the new argument; and the paired arithmetic,
contrast count and strata of the grid readout. They cannot establish anything about the native
environment: the shared library is Linux-only, so no test here executes a native episode, BCRH
call or the complete entry.

Additionally observed off-test, as developer verification of the publication glue (stubbed
rollout and BCRH, real world generation, real checkpoint loading, real draws, real readout and
real JSON write/readback): 512 evaluation rows, 64 BCRH rows, 8 cells, 16 contrasts, 9 means,
3,072 policy joint decisions, 6,144 evaluation action draws, 138,240 native ticks - the card's
planned counts exactly. This is glue verification, not a native or scientific observation.

## Cost projection from the runner's own cost law

Units are the maximum observed values on the executing node from the accepted B01 technical
acceptances (formal02 `summary.json` timings, seed02 acceptance), plus two locally measured terms.

| Term | Source | Seconds |
| --- | --- | ---: |
| import, native build and setup | B01 formal02 `shared_setup` (import + build + initialization) | 9.803 |
| 64-world panel generation | B01 formal02 `evaluation_world_generation` 0.0578; local 0.0658 | 0.066 |
| four checkpoint loads | measured locally, 0.012-0.017 each | 0.100 |
| 8 evaluation cells x 64 episodes | max observed B01 evaluation cell 1.1518 (DIRECT) | 9.214 |
| 4 SAMPLE uniform blocks | measured locally, 0.0141 per cell (1,536 draws) | 0.056 |
| one 64-episode BCRH pass | max of 46.3771 (formal02) and 37.7467 (seed02) | 46.377 |
| publication and readback | B01 formal02 `publication` for a much larger payload | 0.318 |
| other measured bookkeeping | B01 formal02 `other_measured_overhead` | 0.454 |
| **projected complete invocation** | | **66.39** |

Cap 180 s, so the projection uses 37 percent of it and leaves 113.6 s. This is a single-arm
object, so the per-arm cap is the same 180 s. Charged against B01's 2,700 s cumulative formal
budget, 783.29 s spent: full use of the cap would give 963.29 s, the projection 849.68 s. The
engineering check is a non-target check chain in the B01 accounting sense and is projected at
about 13 s (setup 9.8 + 8 two-episode cells 0.29 + two-episode BCRH 1.45 + the 64-episode greedy
replay 1.21 + publication). Neither number is a guarantee; the native build and the node's
current load are not controlled by this projection.

## Frozen engineering check (run first, not a result)

Node `wsl_4070`; launch sha `384cc6f0e222c843ca656fa78053887abcdacb10`; portability boundary: the
native shared library builds on Linux only, so this and the formal invocation run on `wsl_4070`
and nowhere else; no local fallback exists for either.

Staging, once, before either invocation (paths are the local CM worktree copies; digests above):

```sh
ssh hmasd-wsl-node 'mkdir -p /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_formal_20260905_02/checkpoints /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_seed02_20260905_01/checkpoints'
scp C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/checkpoints/MAPR_final.pt   hmasd-wsl-node:/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_formal_20260905_02/checkpoints/MAPR_final.pt
scp C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/checkpoints/DIRECT_final.pt hmasd-wsl-node:/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_formal_20260905_02/checkpoints/DIRECT_final.pt
scp C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/b01_seed02_20260905_01/checkpoints/MAPR_final.pt   hmasd-wsl-node:/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_seed02_20260905_01/checkpoints/MAPR_final.pt
scp C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/b01_seed02_20260905_01/checkpoints/DIRECT_final.pt hmasd-wsl-node:/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_seed02_20260905_01/checkpoints/DIRECT_final.pt
scp C:/Projects/HMASD/docs/research/candidates/variable_n_fleet_churn/evidence/b01_formal_20260905_02/evaluation_episodes.json hmasd-wsl-node:/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_formal_20260905_02_evaluation_episodes.json
ssh hmasd-wsl-node 'cd /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905 && sha256sum b01_formal_20260905_02/checkpoints/*.pt b01_seed02_20260905_01/checkpoints/*.pt b01_formal_20260905_02_evaluation_episodes.json'
git -C /home/wu/projects/HMASD fetch origin && git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/vnfc_b01_depmode_384cc6f0e 384cc6f0e222c843ca656fa78053887abcdacb10
```

The five printed digests must equal the six-column table above before anything is launched.

One `agent-task` payload, task `vnfc_b01_depmode_check_384cc6f0e_20260905_01`:

```sh
cd /home/wu/hmasd-worktrees/vnfc_b01_depmode_384cc6f0e && mkdir -p temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/output && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/memory.json && /usr/bin/time -v -o temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/whole_time.txt timeout 120s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py --profile engineering-check --checkpoint-root /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905 --b01-reference /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/b01_formal_20260905_02_evaluation_episodes.json --launch-sha 384cc6f0e222c843ca656fa78053887abcdacb10 --out temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/output > temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/output/run.log 2>&1
```

- cwd `/home/wu/hmasd-worktrees/vnfc_b01_depmode_384cc6f0e`; output root
  `temp/directions/variable_n_fleet_churn/b01_depmode_check_20260905_01/output` inside it.
- Bound: `timeout 120s`, one compute thread, CPU binary64, 4 GiB physical and effective admission
  in the same payload immediately before the runner.
- What it checks, in one invocation: a 2-episode panel with check masters 2026090595/2026090596
  through all eight cells and BCRH; that `GREEDY` on the recorded B01 formal02 panel with the
  formal02 MAPR final policy reproduces all 64 recorded evaluation rows field for field
  (`R_fail_60`, `U_total`, `U_intact`, `J_ext`, the three endpoint pairs, both violation flags,
  `event_count`, `integrated_ticks`, `zone`); that `SAMPLE` consumes 48 declared draws per cell
  and `GREEDY` none; that the summary reports zero updates and zero parameter displacement.
- Stop condition: exit 0 with `b01_greedy_replay.compared_rows == 64` in `summary.json`. Any
  non-zero exit, any `AssertionError`, or a missing replay block stops here and returns to the hub;
  no automatic retry and no formal launch.
- Afterwards the CM reads the output root and runs
  `... -m pytest -q tests/.../test_deployment_mode_eval.py` with
  `VNFC_B01_DEPMODE_CHECK_ROOT=<output root>` to exercise the output-reading test.

## Frozen formal invocation (only after the check passes)

Task `vnfc_b01_depmode_formal_384cc6f0e_20260905_01`, same cwd, same staged inputs, same node:

```sh
cd /home/wu/hmasd-worktrees/vnfc_b01_depmode_384cc6f0e && mkdir -p temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/output && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/memory.json && /usr/bin/time -v -o temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/whole_time.txt timeout 180s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py --profile formal --checkpoint-root /home/wu/hmasd-inputs/vnfc_b01_depmode_20260905 --launch-sha 384cc6f0e222c843ca656fa78053887abcdacb10 --out temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/output > temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/output/run.log 2>&1
```

- Node `wsl_4070`, launch sha `384cc6f0e222c843ca656fa78053887abcdacb10`, cwd as above, output root
  `temp/directions/variable_n_fleet_churn/b01_depmode_formal_20260905_01/output`.
- Frozen inputs: the four checkpoints at the digests in the table, staged under
  `/home/wu/hmasd-inputs/vnfc_b01_depmode_20260905/`; the runner refuses a byte difference.
- Resource bound: `timeout 180s` (the card's complete cap), one compute thread, CPU binary64,
  fresh 4 GiB physical and effective admission joined by `&&` immediately before the runner.
- Stop condition: one invocation. Exit 0 with `within_wall_cap` true and the four primary
  contrast means present is the complete result; a non-zero exit, a timeout or a missing primary
  output is returned to the hub as an incomplete attempt. No retry, no partial cell set called a
  result, no second panel, no additional checkpoint.
- If the hub integrates this branch into `main` before launch, substitute the integrated commit
  whose source bytes are identical in both the `worktree add` and the two `--launch-sha` values;
  the currentness guard compares the declared source paths, not the commit identity.

## Limitations

Nothing native was executed anywhere in this task: no episode, no BCRH call, no complete
invocation. The projection reuses B01's measured units on the same node and adds two locally
measured terms; the native build time is inside B01's `shared_setup` term and is not separately
observed. Passing tests establish conformance of the changed pieces, not that the complete entry
runs, and certainly nothing scientific. The greedy-equality claim is only established when the
engineering check actually runs on `wsl_4070`.
