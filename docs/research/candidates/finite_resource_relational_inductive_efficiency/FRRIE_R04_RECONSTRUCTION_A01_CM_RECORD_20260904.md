# FRRIE r04 reconstruction A01 CM record — 2026-09-04

Status: `ACCEPTED / RUNNING / TRACKER_ADOPTED`. No terminal or scientific result is claimed.

Authority: `FRRIE_R04_RECONSTRUCTION_A01_SCIENCE_CARD_20260904.md`, frozen and pushed in
`43a67cb1be0b06c02859e6dcf024d9f4495fc602`. This is one A/RECON diagnostic, not scientific
attempt 05, a resume of r04, or a repair. The original failed artifacts remain untouched.

## Implementation and protected boundary

Launch source: `b41a6ba779e514937e35c9b0c1dbc69a50ec68d5`, committed and pushed on
`codex/impl-lmx-frrie-pdb-fixture-20260904` and `codex/cm-frrie-r04-diagnosis-20260904`.
CM integrated the frozen card and inspected the exact two-file addition: six lines in the
non-collected stdlib fixture `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r04_reconstruction_a01/pdb_lifecycle_fixture.py`
and nine fixed commands in `FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt`.
No production source changed. The entire FRRIE source directory and R02 runner have an empty
diff against r04 source `732cc2b2299821a58d644e202c4b95c392932447`, checked locally and on the
actual diagnostic checkout. There are no helper functions, callbacks, source patches or new
research orchestration. The card explicitly names exception-state telemetry beyond wall/RSS;
the debugger input is an existing-tool invocation, not a new research framework.

The full recorded production chain remains: evaluation tapes, fresh native build, uniform
evaluation, paired initialization and initial tight projection, checkpoint-0 evaluation,
original training tapes/collector/RSCF/Adam/evaluation order, maximum 128 updates. Preserve
literal root `2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`, label
`FRRIE-B02-CONTACT-BLOCK-001`, seed 1, CPU FP32, both arms/boxes, RNG addresses, native actions,
recurrent state, ordering, work and original integrity checks. No old native artifact or model
is reused. The new worktree was clean before launch.

## One stdlib lifecycle verification

Node `wsl_4070`, interpreter `/home/wu/.venvs/hmasd/bin/python` (recorded Python 3.10).
Exact-SHA cwd `/home/wu/hmasd-worktrees/frrie-a01-check-b41a6ba7`.
Supervisor task `frrie_a01_pdb_check_b41a6ba7` started 2026-09-05T00:04:32Z and ended
00:04:33Z, exit 0, one supervisor second. This was the one new verification of two necessary
termination branches; it created no scientific root, RNG, native environment or model.

After `python scripts/hmasd_resource_preflight.py admit-memory --out <check-cwd>/temp/directions/finite_resource_relational_inductive_efficiency/test/a01_pdb_boundary/admission.json`,
the task ran the following command once for `exception` and once for `normal`, in that order,
joined by `&&`, redirecting each log to the same boundary directory as `<mode>.log`:

```sh
timeout 15s /home/wu/.venvs/hmasd/bin/python -m pdb -c continue tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r04_reconstruction_a01/pdb_lifecycle_fixture.py <mode> < docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt
```

Both logs contain exactly one standalone `BODY_ENTERED` and `TRACE None`. Exception mode
retains `RuntimeError: BOUNDARY_TOY`; normal mode retains `SystemExit` status 0. Fixed `q`/EOF
stops debugger re-entry before the first `import sys` statement; neither mode times out or
executes a second body. Missing r04-specific locals produce expected debugger errors in these
toy frames. Admission at 00:04:33.026266Z measured physical/effective availability each
11,846,438,912 bytes, exceeding 4,294,967,296 bytes. Raw logs and receipt remain in that check
directory; supervisor evidence remains `/home/wu/.agent-tasks/frrie_a01_pdb_check_b41a6ba7/`.
This establishes debugger lifecycle behavior, not failure cause or learner conformance.

## Exact accepted diagnostic invocation

Pinned node `wsl_4070`, SSH `hmasd-wsl-node`; CPU FP32 / configured Python 3.10 / Linux native.
Detached cwd `/home/wu/hmasd-worktrees/frrie-r04-a01-b41a6ba7`, exact launch SHA above.

```sh
/usr/local/bin/agent-task run frrie_r04_reconstruction_a01_b41a6ba7 'cd /home/wu/hmasd-worktrees/frrie-r04-a01-b41a6ba7 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-r04-a01-b41a6ba7/temp/directions/finite_resource_relational_inductive_efficiency/technical/a01_admission.json && timeout --signal=TERM --kill-after=5s 1800s /home/wu/.venvs/hmasd/bin/python -m pdb -c continue scripts/run_frrie_b01_contact_r02.py --output-root /home/wu/hmasd-worktrees/frrie-r04-a01-b41a6ba7/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_r04_reconstruction_a01/production --admission-receipt /home/wu/hmasd-worktrees/frrie-r04-a01-b41a6ba7/temp/directions/finite_resource_relational_inductive_efficiency/technical/a01_admission.json --seed 1 < docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt'
```

Task accepted at **2026-09-05T00:05:30Z**, supervisor PID **111201**, start epoch **1788566730**.
At eight supervisor seconds: `running`, `exit_code=null`, `tmux_active=true`.
Fresh node admission at 00:05:30.402022Z measured physical/effective availability each
**12,857,679,872 bytes**, both above 4 GiB. This is admission, not measured runtime peak RSS.
Supervisor log and terminal witness: `/home/wu/.agent-tasks/frrie_r04_reconstruction_a01_b41a6ba7/`.
Output and admission paths are literal in the command above.

Stop at first exception, natural fixed-128 completion, or TERM after 1,800 seconds with up to
five seconds kill grace. Maximum launcher boundary 1,805 seconds. No automatic second
invocation, retry or resume. `pdb` temporarily changes SIGINT handling; deadline uses TERM.
The debugger can exit 0 after an original exception: supervisor success is never learner
success. Matching-signature capture requires the mapped field/address/counter data; a different
failure requires its traceback and reached boundary. Natural completion is not upgraded to B.

## Cost, coverage and recoverable observation ownership

Historical failure cost is 733 seconds, not a per-update or full-run projection. One diagnostic,
not a sweep; cap 1,805 seconds total and therefore at most that much per arm. Underlying work
law remains 655,360 native slots per learned arm, 1,316,864 including both arms/shared uniform.
Machine-generated maximum exposure from the frozen card:
`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`.
These are configured maxima, not observed completed work. Formal-sized publication coverage
remains an open engineering item; this verification tests only debugger lifecycle.

Dedicated tracker `/root/tracker_tl_experiments` explicitly acknowledged adoption of this task,
SHA and diagnostic-only boundary. It owns routine observations and terminal notification to
DM `/root/dm_amx_frrie_continue` and CM
`/root/dm_amx_frrie_continue/cm_am_frrie_r04_diagnosis`. CM has released routine polling and
retains terminal evidence collection/technical acceptance. A changed observer never authorizes
a duplicate launch. DM owns interpretation and any later diagnostic selection.

Preparation notes: the routine child returned exactly the assigned files after a scheduling
delay and one interrupted/reused agent turn; no experiment was interrupted. Direct non-login
remote Git preparation made no progress and was terminated; configured `zsh -lic` completed
fetch/checkout. These are control-plane observations, not failure diagnoses or result polarity.
