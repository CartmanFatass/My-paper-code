# FRRIE contact-active R128 R02 R05 CM record — 2026-09-04

Status: `ACCEPTED / RUNNING / TRACKER_ADOPTED`. Terminal completion and scientific result are
not yet observed. This is the one newly authorized scientific R05 execution of the original
R02 object, not an upgrade of A01 or reuse of any prior execution state.

## Authority, acceptance and source

Original card: `FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md`.
Invocation supplement: `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_EXECUTION_ADDENDUM_20260904.md`.
DM pushed its selection in `701081f5c875a8190af23ee4884a8b0b0441fa3d`; CM integrated that and
the preceding historical handoff documentation, pushing each integration commit immediately.
Exact launch source is **`5e6d47f0cc05dfdf345bfe7f3f8661d1ffcf7ecc`**, pushed on
`codex/cm-frrie-r04-diagnosis-20260904`. Its entire FRRIE production source and original runner
have an empty diff against r04's `732cc2b2299821a58d644e202c4b95c392932447`, checked locally
and in the actual remote checkout. Source changes requested and made: **zero**.

Preserve literal root `2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`,
seed 1, label `FRRIE-B02-CONTACT-BLOCK-001`, CPU FP32/one Torch thread, 35,513 paired parameters,
initial five-coordinate tight projection, PHY box [-0.04,0.04] versus EDGE [-1.50,1.50],
native/RNG/action/recurrence/replay laws, full 128 RSCF/Adam updates and all original counts,
evaluations, curves and first-match scientific predicates. Comparator competence precedes
the original absolute MEI 0.005 arm-gap reading. No outcome-sensitive stop or rule change.

The unchanged nine-command pdb input is explicitly named by the R05 supplement for optional
exception-state telemetry; it introduces no extra B validity gate. Its existing lifecycle
verification established one body entry and no persistent tracing for both exception and
normal termination. No fixture, implementation, smoke or passing test was repeated for R05.
No new framework, helper, supervisor, retry, resume or checkpoint machinery was added.
All initial inputs/native build/model/optimizer/result state are recreated in the new checkout;
no A01/r04 state or native artifact is reused. Technical acceptance does not assert a repaired
r04 cause or any scientific result.

## Exact accepted invocation

Node: `wsl_4070`, SSH `hmasd-wsl-node`, configured Python 3.10 at
`/home/wu/.venvs/hmasd/bin/python`; CPU FP32 Linux native. No host/device/interpreter change.
New detached cwd: `/home/wu/hmasd-worktrees/frrie-contact-r02-r05-5e6d47f0`, clean before launch.

```sh
/usr/local/bin/agent-task run frrie_b01_contact_r02_5e6d47f0_05 'cd /home/wu/hmasd-worktrees/frrie-contact-r02-r05-5e6d47f0 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-contact-r02-r05-5e6d47f0/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r05_admission.json && timeout --signal=TERM --kill-after=5s 28795s /home/wu/.venvs/hmasd/bin/python -m pdb -c continue scripts/run_frrie_b01_contact_r02.py --output-root /home/wu/hmasd-worktrees/frrie-contact-r02-r05-5e6d47f0/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r05 --admission-receipt /home/wu/hmasd-worktrees/frrie-contact-r02-r05-5e6d47f0/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r05_admission.json --seed 1 < docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt'
```

Accepted **2026-09-05T00:53:58Z**, start epoch **1788569638**, supervisor PID **846702**.
At one supervisor second: `running`, `exit_code=null`, `tmux_active=true`.
Fresh actual-node admission at **00:53:58.408321Z** measured physical and effective availability
each **12,670,226,432 bytes**, both above 4,294,967,296 bytes, no failure reasons.
This is admission evidence, not runtime peak/resource conformance.

Supervisor log/terminal witnesses:
`/home/wu/.agent-tasks/frrie_b01_contact_r02_5e6d47f0_05/`.
Output root and admission are literal in the command above; expected publication is
`summary.json` in the new output root. The original runner retains its per-arm 14,400-second
limits. External TERM at 28,795 seconds plus at most five seconds kill grace respects the
28,800-second outer cap. No result-sensitive early stop, resume or automatic next invocation.
Pdb temporarily changes SIGINT handling; the external deadline uses TERM. Pdb may exit 0 after
an original exception; collection must read original termination and complete summary evidence.
Verified fixed q/EOF stops any post-terminal debugger re-entry before new script computation.

## Cost, exposure, coverage and observation handoff

No sweep. Work remains 630,784 training + 24,576 evaluation = 655,360 slots per learned arm;
both arms plus shared uniform total 1,316,864. Same-node A01 cost anchors at this identical work:
PHY 160.52530051894428 attributed seconds, EDGE 160.3020884220823; shared work is additional.
Whole-run anchors are 902.2496755629982 runner seconds and 927 supervisor seconds. These are
projections, not guaranteed timing or sums of independent costs. Each arm is below the original
four-hour cap; original eight-hour total cap remains. No arm is dropped.

Machine-generated exposure from the unchanged runner/card:
`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`.
These are configured exposure facts until terminal counts are collected. A01 exercised real
publication; formal-sized end-to-end test coverage remains unrecorded as an open engineering
item. It is not an additional B launch gate.

Dedicated tracker `/root/tracker_tl_experiments` explicitly ACKed adoption of this accepted task
and SHA. It owns routine observations and terminal/loss/bound notification to
DM `/root/dm_amx_frrie_continue` and CM
`/root/dm_amx_frrie_continue/cm_am_frrie_r04_diagnosis`. CM releases routine polling and retains
technical collection. DM retains scientific intake and all next-object selection. If transport
or observation is lost, retain this exact handle; do not infer failure or launch another run.
