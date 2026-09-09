# UCOPE renewable commitment B01 — implementation acceptance, 2026-09-08

## Binding and delivered source

The accepted implementation is **a453447cb011d50c6bb63ed7fc40180134a914b5**,
source tree `e2372f46fcf50ad10eddb04f3e30aafc288651b3`, pushed on `codex/ucope`.
Authoring checkout: `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`.
Starting checkout `5a7455c0f4745622e7dcadc8b96e607218b3a300` was clean; unrelated work was preserved.
Contract: [CM handoff](UCOPE_UAV_RENEWAL_COMMITMENT_B01_CM_HANDOFF_20260908.md)
and [science card §§2–7](UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md),
the latter frozen at `ec82119adb83044ac9eff346a4779d3aceffa334`.

The five changed production paths are existing `uav_motion_prefix_b01/{environment,policy,learner,study}.py`
and `scripts/run_ucope_uav_motion_prefix_b01.py`. The owned tests are expanded
`test_pair_plumbing.py` and new `test_renewal.py` in the mirrored directory.
Production adds 72/deletes 30 lines; tests add 158/delete 9; runner remains 54 lines.
Scope §4 additions: **none**, as card §6 fixes. No base environment or governance changed.
Most production additions are the requested selector/publication/count fields; their necessity
is card §§2,5,7, and independent review covers this orchestration share.

T samples velocity and conditional duration at each owner's own expiry. The same eligibility
mask controls sampling and stored PPO density. Held owners keep commands and consume no fresh
action draws; every actor and the critic retain primitive observations. Existing likelihood,
PPO objective/denominator, recurrence, initialization, optimizer and RNG laws remain in place.
A selected duration label survives administrative truncation. Suppression is counted after
executed held steps; censoring is counted only after executing the horizon step with a timer
still exceeding one. Partial attempts retain actual selections and steps. Added phase counts,
T−H and arm means are limited to `renewal_b01`; historical selectors retain their output laws.

## Focused execution and coverage

Exactly one affected-directory suite ran on `hmasd-wsl-node` at the committed source above:

```text
cwd=/home/wu/hmasd-worktrees/ucope-uav-renewal-b01-p69-check-20260908
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp /home/wu/hmasd-worktrees/ucope-uav-renewal-b01-p69-check-20260908/temp/directions/ucope/test/uav-renewal-b01-p69 tests/experiments/candidates/ucope/uav_motion_prefix_b01
```

Configured `agent-task` handle `ucope-uav-renewal-b01-p69-check-20260908` finished with
exit 0, PID 3018378, inactive tmux. **81 passed in 3.37s**; complete timed command **3.97s**,
peak RSS 526572KiB. Cumulative directory wall 3.97s is below 300s. The sole warning is the
existing `cache_dir` setting with the explicitly disabled pytest cache provider.

New checks exercise heterogeneous release times, all-held RNG/head exclusion, continued
recurrence and gradients through held observations, behavior/recomputed compound densities,
actual detached stored-command inputs in four real Adam epochs, t254/t255 labels and physical
truncation, and a deliberate last-step synthetic failure retaining selections without projected
suppression or censoring. A short real-learner synthetic pair publishes/readbacks native-sum
J values, three contrasts and conditional SEs, phase counts, config, T/G checkpoints and totals.
Expanded CLI plumbing checks original stream/reset laws, renewal labels and early wrong-master/
aggregate refusal. Existing tests cover the unchanged objective, initialization and gradients.
These are synthetic engineering checks; they establish no real-UAV return or performance claim.

Raw receipts, commands and terminal outputs are under this authoring checkout:
[check evidence](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/),
especially [task log](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/supervisor/task.log),
[exact wrapper](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/suite-launch.sh),
and [terminal source readback](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/terminal-readback.txt).
The remote checkout was clean at terminal readback. Creator-owned pytest scratch was removed
and absence checked. Only necessary technical receipts remain. Committed-object carrier packs
were removed locally/remotely after staging 179 missing objects (242913 bytes); no live
interpreter upgrade, implicit source fetch or uncommitted source staging occurred. Initial
remote object enumeration hit a zsh quoting error before staging or tests; quoting was repaired.

## Independent review and CM disposition

Existing independent reviewer `rv_ah_ucope_b02_credit` inspected the complete source/test diff
at `a453447cb011d50c6bb63ed7fc40180134a914b5` and the exact-source remote terminal receipt.
Final return: **no material findings or unresolved acceptance gaps; no repairs requested**.
The reviewer verified own-expiry sampling/density, held-owner exclusion, all-held primitive
processing and denominator, original horizon labels and actual partial counts, unchanged
historical routes/initialization/checkpoints, and the three-contrast publication path.
It independently confirmed 81 passing tests, exit 0, 3.97s full wall, scratch cleanup,
+72/−30 non-test lines, 54-line runner and no prohibited §4 additions. It ran no extra tests,
scientific invocation or edits. Its residual limitation is that synthetic conformance does not
establish UAV performance or full-run timing for increased renewal work. CM accepts this
technical evidence with that limit; no open correction remains.

## Cost, publication boundary and return

Per-arm cost projection: unchanged native step/update budgets plus the card's actual-renewal
head work; B04 timings are a same-loop reference, not measured renewable duration coefficients.
No new performance experiment was selected or performed. A real-invocation projection and any
concrete over-cap gap remain with the separately allocated execution plan under card §6.
Post-learner path coverage: the selected suite exercised the affected short synthetic learner,
checkpoint, episode/count and final-primary publication path. Real 7301 remains unexecuted.
Scientific invocations, independent smoke, profiling, replay, pilot and extra evaluation: **zero**.

CM returns accepted-source readiness to the assigning DM. DM records direction-local intake;
Root owns integration and any concrete subsequent execution allocation. This assignment does
not stage a scientific wrapper, take admission, create a 7301 output root or launch a pair.
Root owns removal of the remote engineering checkout after integration/archive, unless its
next concrete allocation establishes an immediate execution dependency; record that event
rather than retaining a full checkout as backup. The shared local authoring checkout remains
in use by the direction.
