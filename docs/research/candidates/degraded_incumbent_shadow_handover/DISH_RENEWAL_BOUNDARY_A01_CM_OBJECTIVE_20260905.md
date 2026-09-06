# CM objective: DISH-RENEWAL-BOUNDARY-A01 measurement entry

Issued by the Claude Code research hub (Root and DM for `degraded_incumbent_shadow_handover`),
2026-09-05. Science card: `DISH_RENEWAL_BOUNDARY_A01_SCIENCE_CARD_20260905.md` (read it first;
its sections 2, 4 and 7 bind this work). Selected by `PRO_FINAL`
(`DISH_POST_B02_CONVERGENCE_INTAKE_20260905.md`). This objective changes no science. The hub's
read-only scout map of the surface (2026-09-05) is summarized in card section 4; the line
references there are current on `main` at d34f06fb6.

## Class and claim

`A/RECON`, seedless. One retained controller configuration (seed-61 FORECAST_PACKAGE update-16
checkpoint), two fixed 32-tick windows on the unmodified B02 ordinary evaluation path. The result
can support only: per-tick agreement/disagreement counts between the policy-consumed `renew` and
the native command-admission predicate at the same tick, with the emitted and held command
records. Nothing about service, learning or other coordinates.

## Protected semantics (must not change)

- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/` (Python and native) is
  read-only: no field added to `_State`, `_StepOutput`, `_StepInput`, no exported function
  changed, no edit to `step_rows`, `_decode_step_outputs`, `NativeBatch`.
- `forecast_package_b02/study.py` and the B01 helpers it imports (`load_host`, `_reset_row`)
  are read-only; import them.
- Call order per tick exactly as `study.py:131-150`: `step_rows(observation, sampler=None,
  global_tick=tick, deterministic=True)` → `native.step(rows)` → `apply_native_promotion(...)`,
  starting from the reset observation `native.observe()`. No extra `observe()`/`step()` calls,
  no re-reset, no flag rewrite, no injected readiness/ownership/command. Measurement reads of
  native state happen between these calls and must not alter the sequence.
- Checkpoint loaded with `forecast_package=True`, original Welford stats from the checkpoint,
  `optimizer` never touched; fresh `RecurrentRolloutState.fresh("STRUCTURED", width=1)` per
  window; `torch.set_num_threads(1)`; FP32 policy, float64 native.
- Coordinates and windows exactly as the card's table; 32 ticks each from the reset (tick 0
  included), or fewer only if the native terminal fires earlier (then report the terminal cause
  and the live count).

## Inputs (frozen evidence)

- `checkpoint_update16.pt` of the FORECAST_PACKAGE arm, sha256
  `504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`. Known locations: remote
  `wsl_4070` under `/home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/`
  (per the B02 CM record) and possibly the local cache `temp/b02_transport/`. The runner takes
  the checkpoint path plus expected sha256 and refuses a mismatch. **Stop and return if the file
  cannot be found at that digest on either node**; do not train, synthesize or substitute.
- The B02 master and the two `EvaluationCoordinate` values are taken from `study.py` as the B02
  run used them (`study.py:204-216`); record the reset row and its phase.

## Measurement contract

For each live tick t in each window, one row with: `window`, `t`, policy-side
`observation["renew"]` (the value `step_rows` will consume) and observation tick; pre-step
`_State` copy fields `tick`, `countdown`, `k_active`, `k_epoch`, `owner`, `actuator_owner`,
`cas_applied`, held `a` vector; `native_admission = (pre-step countdown == 0)`; the emitted
`raw_action`, `prepare`, `commit` from the step rows; post-step `_State` fields `countdown`,
held `a`; the returned `renew`, `service`, energy increment, transfer/hard-event indicators,
`terminal`; `held_changed` (any element of `a` differs before/after) and, when it changed, the
element-wise difference between the new held vector and the emitted raw action at its actual
floating-point scale (native projects the raw action, so report the projected value too if the
projection is reachable without native changes; otherwise report raw versus held and say so).

Take the pre-step snapshot with `.copy()` (the state buffer is mutated in place). Tick 0 uses
the reset observation; its `renew` is expected to read 0 by construction (card section 4); do
not special-case it, record it.

Reduction per window and overall: the four decisive counts (native admission true with policy
renew false; policy renew true with native admission false; both true; both false), the count
of ticks where the held command changed, and for each admission tick the pair (emitted at that
tick, emitted at the previous tick, new held value). Parameter norm before and after each window
(expected equal).

## Deliverables and owned paths

1. `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a01.py`:
   the windowed driver (reuse `study.py` helpers by import), the row recorder and the reduction.
   No changes to existing modules.
2. `scripts/run_dish_renewal_boundary_a01.py`: argparse entry with card defaults fixed
   (`--checkpoint`, `--checkpoint-sha256`, `--out`, `--launch-sha`, `--profile {formal,check}`
   where `check` runs window 1 for 4 ticks only against the same checkpoint and is the one
   focused measurement-output check). Sets the same thread environment as `study.py` before
   importing torch. Writes `rows.json` (all rows), `summary.json` (config, checkpoint digest,
   reset rows and phases, live tick counts, decisive counts, held-change records, parameter
   norms, exposure line with zero training, wall and peak RSS), `run.log`.
3. `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py`:
   unit checks that need no native library (row schema and reduction arithmetic on synthetic
   rows; the admission predicate; that the driver calls `step_rows` with
   `sampler=None, deterministic=True` and never calls `observe()` twice per tick, via a stub
   batch), plus one check that reads a `check`-profile output root when
   `DISH_A01_CHECK_ROOT` is set.
4. `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A01_CM_RECORD_20260905.md`:
   what was added (A/D per path), the checkpoint location and digest verification, the exact
   focused-test command and result, the frozen `check` and `formal` commands for `wsl_4070`
   (preflight `&&` runner under `agent-task`), the cost projection against the 120 s bound from
   measured terms (B02's native build and evaluation timings are in its CM record; state which
   terms are reused and which are unknown), and the post-learner-path coverage line (not
   applicable: no learner runs).

Engineering Scope Spec §4 additions: none. Budgets: ordinary (the whole object is well under
600 lines). No retry, pool, registry, telemetry beyond wall and peak RSS, historical replay,
or repair of the reset-boundary `renew` behavior (observe it, do not fix it).

## Verification before returning

- Focused test file passes locally with
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q <file> -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/renewal-boundary-a01-cm`.
- The native extension builds under MSVC locally (`production_backend.py:346-388`); if the
  checkpoint bytes are available locally at the digest, you may run the `check` profile locally
  as the bounded focused check (it is not result-bearing: 4 ticks, window 1) and record its wall;
  otherwise prepare the remote `check` command and say so.
- Do not run the `formal` profile anywhere.

## Stop rule and return

Stop with the concrete fact if: the checkpoint is unavailable or its digest differs; the
measurement cannot be taken without editing R06 or `study.py`; the reset row's phase differs
from the card's expectation (report, do not correct; this alone does not stop the work, but
flag it); the projection exceeds 120 s. Return: worktree branch and pushed commits, A/D counts,
digest verification, focused-check output, the frozen commands, the projection, and any
semantic question. Do not launch anything result-bearing.

## Git

Assigned worktree and branch only; stage by explicit path, commit by pathspec; never
`git add -A`, stash, reset or rewrite history; runtime trailers and `scope: none`; push after
each commit.
