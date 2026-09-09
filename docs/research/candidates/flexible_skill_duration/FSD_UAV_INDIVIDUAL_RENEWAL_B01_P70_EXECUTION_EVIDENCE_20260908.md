# FSD UAV B01 P70 execution evidence

Allocation: [P70 handoff §§1–5](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_EXECUTION_HANDOFF_20260908.md), card §9; committed input aa60809c3e9517290af1c1d89e49cb0ea007f974 and delegated choice bc4e0acf786e41697824f1cb077091b74827be67. Accepted source ca36e2f941d6c4d4e996a9bd919378af44ea0e93. CM alone observes and collects; DM owns science and Root relay. No new coding/comparison assignment.

## Fixed input and execution binding

Authoring: C:/Projects/HMASD-worktrees/codex-fsd, codex/fsd, clean start bc4e0acf786e41697824f1cb077091b74827be67. Execution: configured wsl_4070 through hmasd-wsl-node; detached cwd `/home/wu/hmasd-worktrees/fsd-uav-b01-p70-ca36e2f94`; interpreter `/home/wu/.venvs/hmasd/bin/python`. CPU4/FP32 and all frozen seeds/counts remain. Scientific roots relative to cwd: `temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0` and `I`. I reads that original D0 summary.

Literal input scripts: [D0.sh](uav_individual_renewal_b01_p70_20260908/D0.sh), [I.sh](uav_individual_renewal_b01_p70_20260908/I.sh). Remote staging `/home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908`. Each script joins canonical on-node fresh admit-memory directly to the runner with `&&`; initial admission receipts remain outside scientific roots. No source guards, retry logic, new telemetry or scope §4 machinery.

| Input | LF-byte SHA256 |
| --- | --- |
| D0.sh | a3507311a795fc122cf0559b8196f62f35a982a6b672e3414da65fa2ca38b390 |
| I.sh | b4ac40a2b58b9a9e11d037d72e80d6e23461d6470f02c716faea9f1d04a331db |

Literal supervisor commands (one accepted submission per arm, sequential terminal boundaries):

```text
/usr/local/bin/agent-task run fsd_uav_b01_p70_D0_ca36e2f94 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908/D0_process_time.txt /usr/bin/timeout --signal=KILL 3600s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908/D0.sh'
/usr/local/bin/agent-task run fsd_uav_b01_p70_I_ca36e2f94 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908/I_process_time.txt /usr/bin/timeout --signal=KILL 18000s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908/I.sh'
```

Outer timeout covers the complete script from admission through imports/model setup, learning, final own evaluator and closed-file pair publication, KILL at the original cap with zero grace. External time/RSS/aggregate CPU records sit in staging. Supervisor roots `/home/wu/.agent-tasks/<handle>/` retain runner.sh, task.log, status, pid, start_time and exit_code. Submission acceptance, memory admission and scientific work are separate facts. Unknown acceptance is reconciled only by the same handle; no retry, resume, extra seed/arm/evaluation or pilot.

Per-arm cost projection: existing historical scenarios D0 1617.82s and I 16178.2s, within original 3600/18000s caps, sum21600s. Work remains five16×500 updates and one32×500 final endpoint per arm. These scenarios are not measured current rates. Complete study critical path, summed wall and aggregate CPU remain separate observations. Post-learner publication coverage reuses P69's fake complete D0/I main plus partial/incomplete-pair checks; no fixture, suite, smoke or profile is repeated.

## Staging and acceptance facts

Pending exact-source/actual-file verification, staged digest/LF/syntax check and first submission. The literal input scripts and this record are committed/pushed before scientific submission. Raw control receipts will be collected under `temp/directions/flexible_skill_duration/exp/uav_b01_p70_control_20260908`; scientific output remains in the separate fixed root. Old blocked P69 scratch is untouched.

Before D0: input commit ac520c229 was pushed. Configured network-shell fetch succeeded; an earlier non-login fetch stalled and was terminated before source setup or submission. Detached checkout is exact ca36e2f941d6c4d4e996a9bd919378af44ea0e93, clean, with sparse checkout disabled. Actual bytes of all2109 tracked Python files match their committed blob hashes; every named required helper/config/agent/environment path is present. Installed metadata: Python3.10.21, NumPy1.26.3, Torch2.7.0+cu118, Gymnasium1.0.0, PettingZoo1.24.3, SciPy1.15.2, SB3 2.6.0. No scientific imports or constructors were run by verification. D0/I scripts438/542 bytes, zero CR, matching digests above and bash-n exit0. Interpreter/time/timeout/supervisor executable. Both proposed handle roots and scientific parent absent. Detailed raw record: control `source_verification.json`. Submission remains pending at this recorded boundary.
