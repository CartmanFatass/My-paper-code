# CM objective: DISH-RENEWAL-BOUNDARY-A02-CORRECTION (2026-09-06)

Card: `DISH_RENEWAL_BOUNDARY_A02_CORRECTION_SCIENCE_CARD_20260906.md` (frozen; read fully).
Route: Grok Build headless (`.claude/skills/hmasd-grok-cm/SKILL.md`), then `hmasd-reviewer`
(Opus) and the hub review; hub commits by pathspec. The implementer makes no scientific
choice; every rule below comes from the card and the Pro decision it applies.

## Objective

1. Correct the ordinary decision boundary so that `observation["renew"]` returned by the
   ordinary `NativeBatch` paths equals `[current lane countdown == 0]`, and expose the raw
   completed-transition flag under `observation["renew_completed"]`.
2. Extend the A01 measurement entry into an A02 entry that records both flags, the projected
   expectation and the incorporation checks, and runs the same two windows.
3. One consolidated focused regression test for the boundary and its consumers.

## Owned paths

- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`:
  ONLY the ordinary `NativeBatch` observation construction (`observe` at ~548, `reset_selected`
  at ~552, `step` at ~701, `rollout` at ~746, and any helper they share). Do not touch
  `_decode_step_outputs`, `complete_b01_tick`, the prepared/B01 paths, ctypes structures, the
  build code or the other `NativeBatch`-like class whose `observe` sits at ~515 unless it is the
  same ordinary class (state the finding).
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py`:
  only if a consumer needs the raw flag separately (expected: no code change; `step_rows` line
  311 and fragments 506–508 already consume `observation["renew"]`). If you change nothing,
  say so with the line references.
- `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a02.py`
  (new): import and reuse `renewal_boundary_a01.py` helpers (`project_command`,
  `native_admission`, `b02_master`, `verify_checkpoint`, window plan); add to each row
  `policy_renew` (consumed, corrected), `renew_completed` (raw), `pre_countdown`,
  `held_before`, `emitted`, `projected_expected` (= `project_command(held_before, emitted)`),
  `held_after`, `incorporated_as_projected` (float64 equality within 1e-9 when admission),
  `value_equal_to_held`, `prepare`, `commit`, `cas_applied`, `owner`, `service`,
  `energy_increment`, `terminal`; `reduce_rows` producing the counts named in card §3; summary
  keys `object = "DISH-RENEWAL-BOUNDARY-A02-CORRECTION"`, checkpoint sha, parameter norm
  before/after, per-window and overall counts, wall, peak RSS.
- `scripts/run_dish_renewal_boundary_a02.py` (new; same CLI shape as
  `run_dish_renewal_boundary_a01.py`: `--checkpoint --checkpoint-sha256 --out --launch-sha
  --profile {formal,check}`, Win32 peak RSS via psapi, `resources_unmeasured` where not
  measured).
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a02.py`
  (new): ONE consolidated test module: (a) synthetic boundary fixture: for a small fake state
  with countdowns `[0, 3, 0]` the ordinary observation reports `renew = [1, 0, 1]` and
  `renew_completed` equals the raw output flag; (b) reset with phase 0 exposes `renew = 1`,
  phase 4 exposes 0; (c) repeated `observe()` does not advance tick or countdown; (d) the
  collector fragment fields `renew`/`prepare_mask`/`commit_mask` equal the corrected flag for a
  two-tick synthetic fragment (reuse the existing B02 test fixtures for model construction if
  any; count and report any backward or model construction the test performs); (e)
  `reduce_rows` on a hand-written 4-tick row set yields the expected counts; (f) source parses.
  Do not add a smoke that runs the real windows.
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A02_CORRECTION_CM_RECORD_20260906.md`
  (new): what changed with file:line, the reviewer questions you want answered, tests and
  results, the cost law with the A01 measurements as reference, and the frozen remote `check`
  and `formal` commands with `WT` and `LAUNCH_SHA` placeholders (same shape as the A01 CM
  record; external `timeout` 120 s; `admit-memory && python scripts/run_dish_renewal_boundary_a02.py …`).

## Protected

Native source and build; ABI structures; prepared and B01 paths; source-clone semantics;
`study.py`; reward, energy, terminal, ownership, certificate and passive-label laws; the
checkpoint and normalization; RNG addressing; `renewal_boundary_a01.py` (import it, do not
edit it); the existing tests `test_package.py` and `test_renewal_boundary_a01.py` must keep
passing unchanged.

## Checks

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider
--basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/renewal-boundary-a02-grok
tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`.
You MAY run the `check` profile locally once (window 1, 4 ticks) with the local checkpoint
copy at `C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt`
(verify sha256 first); record its wall. Do NOT run `formal`.

## Acceptance (hub and reviewer)

Ordinary observations report the current-countdown permission per lane; raw flag preserved
under the new key; prepared/B01/clone paths byte-identical in behaviour; consumers unchanged
or justified; tests green; A01 tests green; line budgets met; no new scope-spec §4 item.
Reviewer questions: is the ordinary class the only one changed; does `reset_selected` for a
phase-zero lane expose 1; does any other consumer of `observation["renew"]` exist in
`experiments/candidates/degraded_incumbent_shadow_handover*/` that now changes meaning
unintentionally (grep and list).
