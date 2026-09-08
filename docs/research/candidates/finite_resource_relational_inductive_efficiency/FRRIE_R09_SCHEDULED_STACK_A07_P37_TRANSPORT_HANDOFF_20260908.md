# FRRIE A07 P37 command-transport handoff — 2026-09-08

Transport correction is statically accepted and staged; **zero original preflight
or scientific invocations** occurred in the failed P35 wrapper or this preparation.
P37 releases the still-unstarted single P35 scientific allocation after DM binds
this handoff. Root owns the corrected dispatch and same-handle observation.

Authority: [P37](../../portfolio/handoffs/2026-09-08-p37-frrie-a07-command-transport.md)
at main `20d03f7fd36af351894ccea51b2bf79512540554`,
[A07 card §§1–4,6](FRRIE_R09_SCHEDULED_STACK_A07_SCIENCE_CARD_20260908.md)
at `78e84d56a5106ea707c1e8dbb5451ae1c8d035e6`, and
[accepted payload](FRRIE_R09_SCHEDULED_STACK_A07_ROOT_HANDOFF_20260908.md)
at `66cd6cd6522d1bde426046907c31d5eb488e4b43`.
The existing `codex/frrie` checkout started tracked-clean at78e84d56a in
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`. Only this new handoff
is authored; DM's card/owner files, old inputs, source and evidence are preserved.

## 1. Failed wrapper and zero-exposure reconciliation

Read the named remote handle
`/home/wu/.agent-tasks/frrie-a07-scheduled-stack-p35-43eec21e` directly and retained
its six files. Its312-byte log states start and terminal at
2026-09-08T16:19:37+08:00 (08:19:37Z), duration0s, exit127; status is `failed`.
The error is `runner.sh: line 10: \: command not found`.
The actual1052-byte runner's execution line is `eval ' \\'`, redirected to its log.
It contains no time wrapper, preflight or Python payload. This establishes a
wrapper command failure before original preflight/science, rather than inferring
zero work merely from missing learner files. The transport layer's broader cause
is not needed to reconcile this observed malformed command.

The fixed original43ee cwd already exists at
`/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e`; its HEAD is
`43eec21e9584c83e5e8d940402d7e4570b454e59` and Git status is empty. The fixed
payload output root `temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_scheduled_stack_p35`
and fixed P35 supervisor `process-time.txt` are both absent. The new P37 supervisor
identity is also absent. Thus no current fixed-path evidence conflict was found.
The failed P35 log/status/runner/pid/start_time/exit_code stay untouched. The
corrected payload may create its previously absent time file there; that new
measurement belongs to the corrected P37 execution, not to the failed wrapper.

This is one failed supervisor attempt with zero original preflight/scientific
exposure. The corrected supervisor has not launched. P37 explicitly releases
only the original one scientific allocation; it adds no second sample or retry
of scientific work. An inconsistent later path/acceptance fact must be reconciled
before launch, without overwriting evidence or changing the payload.

## 2. Exact staged script and corrected supervisor argv

The accepted Git-blob sh fence was extracted using Python binary subprocess
output and `write_bytes`, removing only the single fence-separator LF as its
handoff specifies. `scp` staged the file, and a binary `scp` readback is identical.
No payload passed through PowerShell string quoting or a text pipeline.

Staged script: `/home/wu/hmasd-inputs/frrie-a07-scheduled-stack-p37/command.sh`.
The exact script is **1287 UTF-8/LF bytes, zero CR, no trailing LF**, SHA256
**`8ed56ed4489b0d211355f74a1e91a07f9ae8ac1efc43cecf77c824a5fc56e51c`**:

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/frrie-a07-scheduled-stack-p35-43eec21e/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 115s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc <<'FRRIE_A05'
set -euo pipefail
repo=/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e
out="$repo/temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_scheduled_stack_p35"
python=/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python
cd "$repo"
export PATH=/usr/bin:/bin:/home/wu/.local/bin:/usr/lib/wsl/lib
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export FRRIE_A05_HELPER=/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py
export FRRIE_A05_OUTPUT="$out"
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$out/learner_admission.json" && "$python" -X faulthandler -m pdb -c "!__import__('faulthandler').dump_traceback_later(60, repeat=False, exit=False)" -c continue -m scripts.run_frrie_b01_contact_r09 --output-root "$out/learner" --admission-receipt "$out/learner_admission.json" --seed 3 < /home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt
FRRIE_A05
```

Preserve every embedded P35 path, A05 variable/heredoc, original43ee source and306
helper/stdin binding. Arming remains the78-byte argument with SHA256
`e3dbb75b2d11897a949c8b925d2999dc39922db21a6c566a4e281ca7b09842ca`:
one initial-stop call,60s, repeat=False, exit=False before continue; same q/EOF.
Root3/P22 system312 runtime and23 pins/full128 schedule/RNG/FP32/FP64/native
profiles remain the accepted card's exact values. No new native artifact is
staged; its build remains inside the original chain.

Use new supervisor identity **`frrie-a07-scheduled-stack-p37-43eec21e`** on
`hmasd-wsl-node`. After DM exact binding is committed/pushed, Root supplies argv
`/usr/local/bin/agent-task`, `run`, that identity, then this short string as
**one argument**:

`/usr/bin/env -u BASH_ENV -u ENV /bin/bash --noprofile --norc /home/wu/hmasd-inputs/frrie-a07-scheduled-stack-p37/command.sh`

The short string is **123 UTF-8 bytes**, SHA256
**`c09c4db7060600a1a07a1bdbaac917de7dff281b84aa9bac7215dba37af30e2b`**.
It has no multiline payload, nested quotes or interpolation. Unsetting BASH_ENV
and ENV before the additional noninteractive Bash prevents an environment startup
file from changing that transport shell's behavior; `--noprofile --norc` alone
does not suppress BASH_ENV. The unchanged payload already unsets both for its
inner shell. No other environment/runtime/scientific amendment is introduced.

The new supervisor's log is
`/home/wu/.agent-tasks/frrie-a07-scheduled-stack-p37-43eec21e/task.log`.
The payload's time receipt stays under the old P35 supervisor directory, and its
scientific cwd/output stay under P35, exactly as shown above. Collection must
join those named paths while preserving the failed wrapper's original six files.
Do not dispatch the full multiline script body as a supervisor argument again.

## 3. Static checks, cap and remaining boundary

Local Git-blob extraction, staged binary roundtrip,1287-byte length, zero-CR and
SHA256 identity pass. The staged file parsed with
`/usr/bin/env -u BASH_ENV -u ENV /bin/bash --noprofile --norc -n /home/wu/hmasd-inputs/frrie-a07-scheduled-stack-p37/command.sh`,
exit0 and empty stdout/stderr. No script command was executed. A07's existing
arming AST/argv/pinned-pdb ordering, helper/stdin identity and A05 fixture evidence
remain applicable because the payload is byte-identical; no fixture/import/smoke,
cost pilot, timer or extra diagnostic ran during this correction.

The original TERM115s + at most5s grace =120s complete payload bound remains
unchanged and includes its adjacent original-source4GiB admission&&program,
imports/native build, original learning/evaluation, report and termination.
The added transport shell only reads/starts that payload and performs no setup or
scientific work. Root retains supervisor elapsed as well as timed payload wall;
transport overhead is not extra scientific budget or a cap reset. The accepted
one-chain cost ceiling and unknown actual work/aggregate CPU are unchanged.
Post-learner coverage remains the accepted A05 capture recipe and static A07
command checks, not a claim that full learner publication or a scheduled report
has succeeded.

Raw failed-supervisor copies, `preparation_path_readback.txt`, `command.sh`,
`staged_readback.sh`, `supervisor_command.txt`, and `static_acceptance.json` remain
under the direction checkout's
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_transport_p37/`.
No failed file or source was altered. DM next binds this exact correction; Root
then dispatches once and observes the new handle. This CM collects all resulting
scheduled/fatal/exception/output/terminal facts; DM applies A07's prospective
all-outcome rule. No second scientific invocation, rearm, extra sample, repair,
fallback, extended cap or full B is authorized.

This correction adds no engineering machinery; the selected watchdog/report
already belongs to A07. Comparison enrollment is complete and this is the same
transport correction, with no new code or child.

scope: none
