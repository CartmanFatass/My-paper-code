# B13 P80 technical source acceptance and execution

The selected intact 136→128→133→1 ordinary body is constructed before the
128×5 zero gate in GATED-V. Actual critic counts are 35467/34827, actor 32264.
Private extra rows/biases and zero extra output weights agree between independent
arm copies. Older default bindings are preserved. Final-only evaluation now
uses four independent train/evaluation environments without a 512 panel.
Checkpoint metadata records the actual architecture and 768 training episodes.

Designated checkout: C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906,
codex/direction-vsp_c1, initially clean at 0886e5ea4b18816d9f7750f81134aa3d8307fd12.
Owned source: native_hold_value_b01/{critic,study}.py and the new B13 runner;
new B13 tests and this evidence. UCOPE, native environment, WideCritic and
normalization dependencies have no diff from the bound starting source.
Engineering scope §4: none per card §5; 62 added production lines, 35 runner lines.

## Focused acceptance

[Exact check receipt](VSPC1_NATIVE_HOLD_VALUE_B13_SOURCE_CHECKS_20260909.json):
34 passed, exit 0; pytest 3.56s, whole 4.2679593s within the 300s total budget.
New B13 binding, actual FP32 critic construction/counts/private RNG/zero-gate
numerical agreement and nonzero gate gradient checks; stubbed full 768 schedule,
four constructors, two final checkpoints, frozen moments, complete and partial
primary/H publication. Existing B05 critic, B08 schedule and B10 endpoint/deadline
checks establish relevant legacy defaults and continuous cap behavior. The actual
critic test constructs models but no native environment or fit; schedule tests
use fakes. No scientific native step, fit or evaluation occurred in these checks.
The existing disabled-cacheprovider cache_dir warning is retained.

Independent reviewer review_b10_boundary inspected the changed factory, private
initialization, parameter independence, final-panel isolation, moments, metadata,
primary/H dependencies and caps: no material finding and no required repair.
Reviewer ran no tests or native code; runtime/publication conformance still needs
terminal artifacts. The complete diff was inspected after review; no source change
followed review. New test scratch was resolved and removed by its creator; absent
at completion. Historical P76 scratch remains creator-owned after its recorded
policy rejection; no repeated rejected cleanup or bypass.

## Cost and publication coverage

Card §5 projects each arm from 196608 training steps, 1536 Adam, 384 moment
merges, 8192 learned evaluation steps and one endpoint publication; GATED pays
startup and MLP also pays 8192 H steps and pair readback/exit. Prior complete
pair walls 475.85/507.29/504.91s inform planning beneath 1800s per complete arm
and 3600s whole. New-width component costs and aggregate CPU remain unknown;
no new cost probe. Stubbed final-only publication and readback exercise the
affected post-learner path, including missing H versus damaged learned primary.
Existing actual final checkpoint collection supplies credible unchanged-path
coverage. Engineering checks establish conformance, not performance.

CM continues the one allocated accepted remote submission through exact committed
source and literal-wrapper binding, fresh joined actual-node admission, sole
observation and all-outcome collection. CPU FP32, one process/numerical thread;
no retry, resume, extra evaluation or successor. DM owns scientific intake and
Root owns completed remote-worktree reclamation.

## Frozen execution binding

Source SHA `23ebb0f5e22286d9ea77a145f980bedacc32d9da`. Literal LF wrapper: `scripts/run_vspc1_native_hold_value_b13_p80.sh`, SHA256 `f7b02dce93d632e7263303291953cbec63f82ad098e272ef39514738c30f0df9`.

```bash
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b13-8601-23ebb0f5e222 &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b13_8601_23ebb0f5e222_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b13.py --seed 8601 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b13_8601_23ebb0f5e222
'
```

Node hmasd-wsl-node; supervisor handle `vspc1_hold_value_b13_8601_23ebb0f5e222`.
Exact submission argv:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b13_8601_23ebb0f5e222 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b13_8601_23ebb0f5e222.sh
```

Whole wrapper includes startup/admission through H/publication/readback/exit.
The single accepted submission consumes the allowance, including a prelearner failure.

## Accepted submission

Accepted 2026-09-09T12:49:54Z on hmasd-wsl-node, handle
`vspc1_hold_value_b13_8601_23ebb0f5e222`, PID 3052500, detached tmux supervisor.
Wrapper commit `83b6e2f8c28cbf5e9925252c31057446cce3362e`.
[Staging evidence](VSPC1_NATIVE_HOLD_VALUE_B13_P80_STAGING_EVIDENCE_20260909.json)
retains exact source/payload digests and readback, detached clean HEAD, interpreter,
prior handle/output/admission absence and exact submission argv. All 14 hashes matched.
Actual-node adjacent admission passed at 12:49:54.754938Z; both physical/effective
available memory were 15323074560 bytes. Admission is not runtime peak evidence.
Raw receipts: `temp/directions/vsp_c1/engineering/native_hold_value_b13_p80/`.
CM `/root/dm_vspc1_p49_value_question/cm_am_vspc1_hold_value_b01` is sole observer
through terminal collection. One accepted submission spent; zero remain.

## Terminal technical acceptance

Finished 2026-09-09T12:57:52Z, exit 0 and inactive tmux. COMPLETE, no limits or
cap breach; complete publication readback. Artifact-only checks PASS in 1.960493s,
six matching remote/local hashes. Actual 417792 steps, 3072 Adam, 96 evaluations,
four constructors, two final768 checkpoints and correct 35467/34827 critic counts.
Whole 477.99s; conservative arm bounds 267.959493/231.922549s. Peak RSS
544.7109375 MiB, aggregate CPU unmeasured. [E0](VSPC1_NATIVE_HOLD_VALUE_B13_RESULT_EVIDENCE_20260909.md)
retains the DOWN point region, all native/H means and conditional errors, all losses
and limits. One accepted submission spent; zero remain. Sole observation complete.
Editing/index returns to DM at the final committed boundary; Root owns remote
checkout reclamation. Historical P76 scratch blocker remains creator-owned.

Published evidence readback passed: 96 evaluation rows, three 32-row contrasts, six hashes, matching payload and terminal receipt. All 14 bound runtime surfaces remain byte-content equivalent to scientific SHA 23ebb0f5e22286d9ea77a145f980bedacc32d9da; no runtime source edit followed launch.
