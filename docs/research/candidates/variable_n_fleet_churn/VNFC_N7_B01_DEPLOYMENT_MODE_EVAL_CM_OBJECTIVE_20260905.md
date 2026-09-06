# CM objective: VNFC N7 B01 deployment-mode evaluation entry

Issued by the Claude Code research hub (Root and DM for `variable_n_fleet_churn`), 2026-09-05.
Science card: `docs/research/candidates/variable_n_fleet_churn/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_SCIENCE_CARD_20260905.md`.
Read-only map used to write this objective: the hub's scout of the B01 module on 2026-09-05
(facts repeated below where they bind the work). Selected by `PRO_FINAL`
(`VNFC_B01_TWO_SEED_CONVERGENCE_INTAKE_20260905.md`); this objective changes no science.

## Class and claim

`B/EXPLORE`, fixed-policy evaluation extension. Zero training, zero optimizer steps, zero new
learners. The claim the result can support: the paired `SAMPLE − GREEDY` `R_fail_60` difference
for each of the four saved B01 final policies on one fresh shared 64-episode panel, with BCRH as
the native reference. Nothing more (card, last section).

## Protected semantics (must not change)

- The B01 host, N7 roster, six post-loss decisions, 240 ticks, 120 s post-loss process, public
  observations, canonical entity/role mapping, legal masks, fixed-occupant override, four-token
  grammar, CPU float64, one compute thread (`torch.set_num_threads(1)` and the four thread
  environment variables), native service/demand definitions, complete terminal.
- The two decoding branches of the shared forward in
  `experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py`: greedy is
  `uniforms is None` (masked max, opaque-rank tie-break); sampling is the inverse-CDF branch with
  one uniform per token. Use them as they are. No temperature, top-k, mixture, multiple draws,
  best-of, or per-world mode choice.
- Loaded parameters are used unchanged. `optimizer_state` is never loaded. No `initialize` draw
  replaces a checkpoint.
- Every existing B01 invocation (`scripts/run_vnfc_n7_direct_b01.py`, both profiles) keeps
  byte-identical behavior. Any addition to the B01 module is optional-argument only, default
  equal to today's behavior.

## Inputs (frozen evidence)

Four checkpoints written by the B01 runner's `checkpoint()`:

| Record | Files (local, under `C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/<record>/checkpoints/`) | Expected |
| --- | --- | --- |
| `b01_formal_20260905_02` | `MAPR_final.pt`, `DIRECT_final.pt` | 2,168,441 and 3,607,517 bytes, `round == 64` |
| `b01_seed02_20260905_01` | `MAPR_final.pt`, `DIRECT_final.pt` | same sizes, different bytes, `round == 64` |

Record their SHA256 in the implementation record and pass the digests to the launch as declared
frozen-input digests. Remote copies exist in the accepted tasks' exact-source cwds on `wsl_4070`
(`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_02` and
`/home/wu/hmasd-worktrees/vnfc_b01_seed02_33e08f440_01`, under the run's output root); prefer
staging the four local files by `scp` to `/home/wu/hmasd-inputs/<request>/` at the recorded
digests over relying on the remote copies, and verify digests on the node.

## Panel and RNG (card)

Namespace `VNFC-N7-B01-DEPLOYMENT-MODE-20260905`, world master `2026090505`, action master
`2026090506`. Panel: `learning.worlds(2026090505, namespace, "evaluation", 64)` gives 32 per
failed zone through the existing zone split. Disjointness from B01 follows from the new
namespace and masters; state this in the record, do not add a census. `SAMPLE` uniforms come
from a dedicated stream, for example `learning.rng(2026090506, namespace, f"eval-actions/{record}/{arm}")`,
with coordinates that name record, arm, world, epoch and token and a domain string distinct from
the training `training/action` domain. `GREEDY` consumes no draws. Paired worlds across all
eight cells and BCRH.

## Work and cost bound

`8 cells × 64 episodes + 64 BCRH = 576 episodes`, `3,072` learned decisions, `384` BCRH calls,
`138,240` native ticks. Complete invocation cap **180 s wall** on the executing node, from process
start through publication and readback, including the native shared-library build. Reusable
timing: about 1.1 to 1.4 s per 64-episode greedy evaluation, 37.7 to 46.4 s per BCRH pass.
Report actual wall and peak RSS; missing telemetry marks the run `resources_unmeasured` and does
not invalidate it. If the complete path cannot fit, return the concrete gap.

## Deliverables and owned paths

1. `scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py`: one argparse entry with the card
   defaults fixed (`--out`, `--launch-sha`, `--checkpoint-root` or four explicit checkpoint
   paths with their expected SHA256, `--profile {formal,engineering-check}` where the check
   profile uses a 2-episode panel and check masters `2026090595`/`2026090596`). It imports the
   B01 module directly and never calls `experiment.run`. It sets the same thread environment as
   the B01 entry before importing torch.
2. Minimal additions inside `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`:
   for example an `evaluation_uniforms` (or similarly named) optional argument on `rollout` that
   supplies uniforms with `training=False`; a `load_checkpoint(path, arm)` helper that builds
   exact-shape finite float64 CPU placeholders, calls `load_state_dict`, sets
   `residual_observation` for DIRECT the way `initialize` does, checks `round`, parameter count
   and the declared SHA256; a small readout for the policy × mode grid (paired means per stratum
   `all/zone1/zone2`, the contrasts listed in the card). Do not modify `experiment.run`,
   `readout`, `checkpoint`, `bcrh`, `worlds` or `native` semantics.
3. Output root: `evaluation_episodes.json` (one row per cell × episode, with `record`, `arm`,
   `mode`, `zone`, `world`, all `terminal_metrics` fields, flags, `recovery_observations_20s`),
   `bcrh_episodes.json`, `summary.json` (config, checkpoint digests, actual counts, exposure line
   with zero updates and loaded parameter counts, the grid readout, wall and peak RSS), `run.log`.
   JSON written and read back as the B01 module does.
4. `tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/test_deployment_mode_eval.py`:
   focused check on a check-profile output root (pattern of the existing `test_output.py`), plus
   direct unit checks that do not need the native library: placeholder construction and
   `load_state_dict` round-trip on a synthetic float64 state; `GREEDY` equals the B01 forward's
   `uniforms=None` output and `SAMPLE` respects masks for a constant-uniform tensor (the R09
   `test_training.py` pattern).
5. Direction record `docs/research/candidates/variable_n_fleet_churn/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_CM_RECORD_20260905.md`:
   what was added (A/D line counts by path), the checkpoint digests, the exact focused-check
   command and its result, the frozen formal launch command for `wsl_4070` (preflight joined by
   `&&` to the runner under `agent-task`), and the cost projection from the reusable timing.

Engineering Scope Spec §4 additions: none. Budgets: ordinary. No pool, retry, repeated smoke,
registry, telemetry beyond wall and peak RSS, root-cause work on the historical HMAC/SIGSEGV
events, or historical replay.

## Verification the CM performs before returning

- Focused test file passes locally with the main environment interpreter
  (`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q <test file>`); tests that
  need the Linux native library are skipped locally with a clear reason and listed for the
  remote check.
- The engineering-check profile is not run locally (native build is Linux-only). Prepare its
  exact remote command; the hub will have the operator run it on `wsl_4070` before the formal
  launch, and the CM reads its output root afterwards.

## Stop rule and return

Stop and return to the hub, with the concrete fact, if: a checkpoint's digest or `round` does not
match; the placeholder or DIRECT reconstruction cannot be made without touching R09/R02 files;
the sampling branch cannot be reached without changing training behavior; or the projection
exceeds the cap. Return: the worktree branch and commits (pushed), the A/D counts, the digest
table, the focused-check output, the frozen remote check and formal commands, and any semantic
question. Do not launch anything.

## Git

Work in the assigned worktree and branch only. Stage by explicit path and commit by pathspec;
never `git add -A`, stash, reset or rewrite history. Commit message ends with the runtime's
trailers and `scope: none`. Push the branch after each commit.
