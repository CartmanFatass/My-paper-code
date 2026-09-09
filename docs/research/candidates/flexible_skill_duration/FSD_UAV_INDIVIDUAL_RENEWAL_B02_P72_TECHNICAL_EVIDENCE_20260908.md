# FSD UAV B02 P72 technical evidence

## Source acceptance

The explicit B02 binding is implemented and technically accepted. Contract: [five-item handoff §§1–5](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_CM_HANDOFF_20260908.md) and [B02 card §§2–4](FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md). Authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`, clean start `42693cbdafb3143d012e2b78e160bedca439fff4`; complete starting science is unchanged from `52609ba8438836de9805014dc783e818010dcc06` / accepted B01 `ca36e2f941d6c4d4e996a9bd919378af44ea0e93`.

Shared runner `scripts/run_fsd_uav_individual_renewal_b01.py` now passes explicit keyword values through summary/manifest, training process RNG/private lanes/config, evaluator construction/RNG/private lanes/config, and pair expectations. New `scripts/run_fsd_uav_individual_renewal_b02.py` selects object/card B02 and training770603/evaluation780603. It forwards ordinary argv to the same loop. B01 defaults remain770503/780503 and retain their original identity after B02 runs. Selected card identity is checked alongside the existing selected object/seed checks, so two old card labels do not supply a B02 pairing. Launch SHA remains reported metadata, not an equality predicate.

No module constants are rebound; no loop, model, environment or configuration implementation is cloned. Existing training collection, actual actions/step metadata, raw rewards, terminal storage followed by reset of both inputs, updates/credit/normalizers, evaluator synchronization/RNG preservation and primary publication remain unchanged. Underlying learner/environment/config/E0/admission/platform helpers and original B01 fake tests are read-only and unchanged. Engineering scope §4: none per B02 card §4. Shared runner428 lines; thin wrapper16 lines; non-test diff +45/−25, comfortably within600/2000 budgets. New B02 tests124 lines.

## Focused checks

Exact combined affected command, once, on the fixed scientific Python:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/uav_b02_p72_binding_20260908 tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b02/test_binding.py
```

Observed output:

```text
..........................................                               [100%]
42 passed, 14 warnings in 7.67s
pytest_exit=0; complete_check_wall_seconds=8.9337842
syntax_exit=0; syntax_wall_seconds=0.0777327
```

All3 changed/new Python files passed in-memory `compile(source, path, 'exec')`, avoiding bytecode output. Combined check process wall9.0115169s <300s. `git diff --check` passed. Warnings are existing matplotlib/pyparsing deprecations. `PYTHONDONTWRITEBYTECODE=1` and disabled pytest cache kept generated artifacts within the exact invocation scratch. No suite rerun, real model/environment, source fixture, smoke, pilot or scientific invocation occurred.

The9 new cases exercise full fake B02 D0/I publication then full fake B01 D0/I in the same interpreter; actual Python/NumPy/Torch constructor draws and RNG preservation; private lane/config consumers; native6U/H arithmetic; selected object/card/seed and evaluator-lane expectations; changed document SHA remaining acceptable; and old B01 companion rejection while retaining the B02 own endpoint. Existing33 cases retain the original collector/config/reset/primary/failure coverage. The fake helper loads the identical shared source under its isolated test name; the B02 wrapper delegates to that fake seam. No production global rebinding follows.

## Independent review

Reused reviewer `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47/rv_ah_fsd_b03_p47` inspected only this changed RNG/binding/comparison boundary. **No material finding.** Its static comparison confirms only the six assigned definitions changed; collection/config/scaling/finite/publication helpers and the old B01 tests are unchanged. It verified explicit propagation, rejection of old companions, later B01 defaults, no loop clone or SHA predicate, scope and budgets. Reviewer inspected coverage and CM output without a test/model/host execution. Fake checks establish binding conformance; B02 native outcome and complete runtime remain unmeasured.

## Cost/publication coverage and next phase

Per-arm cost projection reuses same-method P70 complete walls D0471.89s / I1221.49s and historical scenarios1617.82s /16178.2s. Work stays five16×500 training rollouts and one32×500 final endpoint per arm; caps remain D03600/I18000/sum21600s. References are planning evidence, not guaranteed current bounds. No source fixture, pilot or multiplier change is required or added.

Post-learner publication coverage: the combined fake suite exercises complete new B02 D0/I publication and unchanged B01 publication afterward; damaged/old companions preserve own-arm facts. Later real collection will distinguish endpoint sampled counters from unmeasured duration statistics in empty evaluation storage buffers, and sum wall from critical path/aggregate CPU. No performance or treatment-activity acceptance threshold is introduced.

Future production argv, only after DM source acceptance, from the accepted-source detached remote checkout:

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b02.py --arm D0 --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/D0
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b02.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/D0/summary.json
```

DM source acceptance precedes scientific submission under this P72 handoff; existing P72 then authorizes one D0→I batch without another Root request. Literal cwd/source/handles/admission/payloads will be committed and staged before each submission. Fresh on-node physical/effective≥4GiB admission and outer3600/18000s caps include imports, learning and closed publication with zero grace/retry/resume. Same CM remains sole observer/collector; DM owns science/owner/audit/Root relay. P70 evidence and old blocked P69 scratch are untouched.

P72 scratch cleanup: after retaining check output above, the exact invocation directory was resolved under this checkout's direction test root. Automatic approval review rejected native PowerShell `Remove-Item -LiteralPath` for that exact P72 scratch with “blocked by policy”; no deletion occurred and no bypass followed. The ignored P72 scratch/checks.log remains. This housekeeping limitation does not alter source or fake-check acceptance. The separately blocked P69 scratch was never targeted.

## P72 exact execution binding

DM source acceptance was published at `f95ebcb037865bd0020dfc0e14b3e09302ba4562` before this phase. Accepted scientific source is exactly `08199a932671d9bacdbe4eb0bfebab38c37fca1f`. Configured node/interpreter/supervisor are unchanged from the handoff. Detached execution cwd `/home/wu/hmasd-worktrees/fsd-uav-b02-p72-08199a932` was created at that exact SHA with sparse checkout disabled. Actual source and staged LF syntax/digest checks follow before submission; no fake suite is repeated.

Literal inputs are the only explicitly tracked files under `temp/directions/flexible_skill_duration/exp/uav_b02_p72_control_20260908`: `D0.sh` and `I.sh`. Remaining control artifacts stay scoped/ignored. Remote staging `/home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908`. Scripts change to the exact cwd and join canonical fresh on-node admit-memory directly with `&&` to the exact B02 argv above. Admission receipts remain outside the scientific roots. Scientific outputs are the new B02 root; I reads only its original B02 D0 summary.

| LF input | SHA256 |
| --- | --- |
| D0.sh | bbb490d21391dc839c9a234d4651446398588f15616b50740bd9f2a6e39f40f8 |
| I.sh | c51de29af52b338b329d622e981d7df94ea90262d1b8ef2305c618d6f7f5f515 |

Literal supervisor payloads, sequential D0 then I after terminal collection; at most one accepted submission each:

```text
/usr/local/bin/agent-task run fsd_uav_b02_p72_D0_08199a932 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/D0_process_time.txt /usr/bin/timeout --signal=KILL 3600s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/D0.sh'
/usr/local/bin/agent-task run fsd_uav_b02_p72_I_08199a932 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/I_process_time.txt /usr/bin/timeout --signal=KILL 18000s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/I.sh'
```

Outer timeouts cover the whole script from adjacent admission through imports/setup/learning/own evaluation/closed pair publication, with KILL and zero grace. Time/RSS and minimal aggregate user+system CPU accounting remain outside scientific output roots. Supervisor directories `/home/wu/.agent-tasks/<handle>/` preserve actual command, log, status, PID/start and exit facts. Acceptance, fresh admission and scientific execution remain separate observations. Both handles are proposed, not accepted, at this input-binding boundary. No retry/resume, additional scientific endpoint, source repair or old-data rescue is allocated.
