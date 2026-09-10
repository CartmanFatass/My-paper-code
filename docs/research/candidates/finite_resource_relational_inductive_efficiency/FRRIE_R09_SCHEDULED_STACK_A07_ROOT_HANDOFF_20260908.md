# FRRIE R09 scheduled-stack A07 Root handoff — 2026-09-08

Static acceptance is complete; **zero scientific, fixture or target-import
invocations** occurred. DM next binds this command in the
[A07 card](FRRIE_R09_SCHEDULED_STACK_A07_SCIENCE_CARD_20260908.md); Root then
owns the sole P35 detached dispatch and same-handle observation.
Authority: card §§1–4 at `f361193548f9fb48fb472fa0ef8861af1e97c283`, P35 at
main `cf51c2d2ee8b7920e15a724bfce942bd3a0cc03c`, evidence-spec §§4,11.8.6–7.

Preparation started tracked-clean at that card revision in the existing
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`.
Only this handoff is authored. Source/tests/old inputs and DM's owner packet
remain untouched; no child was created. Comparison enrollment has ended.

## 1. Bound source, runtime and observation input

| Binding | Value |
| --- | --- |
| Scientific/preflight source | `43eec21e9584c83e5e8d940402d7e4570b454e59` |
| Helper/stdin source | `30643b7359b35c6e9d5751147d0999bc629a966d` |
| Base A06 literal | Sole sh fence at `fc279590ecd88aa3cc2d5c10348453b7dcd4e9fe` |
| Node / host / supervisor | `hmasd-wsl-node` / `LAPTOP-U9TDKC8A` / `/usr/local/bin/agent-task` |
| Fresh handle | `frrie-a07-scheduled-stack-p35-43eec21e` |
| Fresh detached cwd | `/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e` at original 43ee |
| Existing interpreter | `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python` |
| Runtime | P22 system CPython 3.12.3/GCC 13.3.0; all 23 retained pins including NumPy 1.26.3/Torch 2.7.0+cu118 |
| Output relative to cwd | `temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_scheduled_stack_p35` |
| Scheduled/fatal stderr | `/home/wu/.agent-tasks/frrie-a07-scheduled-stack-p35-43eec21e/task.log` |
| Optional capture / learner files | Fresh output's `summary.json` / `learner/` |

The new pdb arming argument, excluding shell quotation marks and with no trailing
newline, is exactly:

`!__import__('faulthandler').dump_traceback_later(60, repeat=False, exit=False)`

It is **78 UTF-8 bytes**, SHA256
**`e3dbb75b2d11897a949c8b925d2999dc39922db21a6c566a4e281ca7b09842ca`**.
One `-c` carries it immediately before `-c continue`. It imports the existing
stdlib facility without assigning a target local/global and selects one watchdog,
at most one report, no repeat and no exit. Reporting is configured for 60s after
the initial-stop call; this is not a measured emission timestamp. The nominal 55s
margin to TERM 115s also pays admission/interpreter/pdb startup before arming.
A late/missing report never extends the original 120s cap.

Reuse the existing staged A05 inputs outside the scientific tree:

| Staged path | Source at 30643b7 | Bytes / SHA256 |
| --- | --- | --- |
| `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py` | `experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/capture.py` | 11464 / `0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8` |
| `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt` | `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt` | 173 / `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0` |

The standalone exec then q/EOF input, helper namespace/schema, A05 environment
variable names and heredoc delimiter remain unchanged. Reuse the accepted A05
fixture and staged-input evidence linked by [A06 handoff](FRRIE_R09_FATAL_CALLPATH_A06_ROOT_HANDOFF_20260908.md).
No fixture, smoke, cost pilot, installation or target import was repeated.

## 2. Sole Root command

After DM commits/pushes exact binding, Root supplies supervisor argv
`/usr/local/bin/agent-task`, `run`, `frrie-a07-scheduled-stack-p35-43eec21e`,
then this entire literal as **one argument** on the configured node. Root creates
the fresh detached original-source cwd. Original native build/load is inside the
chain; do not reuse P22/A05/A06 native artifacts. The supervisor provides its
handle directory for the time receipt.

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

Extract the sole sh fence from this document's published Git blob and remove only
the single LF between final `FRRIE_A05` and the closing fence. The command is
**1287 UTF-8 bytes, zero CR bytes**, SHA256
**`8ed56ed4489b0d211355f74a1e91a07f9ae8ac1efc43cecf77c824a5fc56e51c`**.

Original admission&&program, root 3, full 128 paired-update/checkpoint/uniform/roster
schedule, LR 0.003/beta boxes, RNG, CPU FP32/original FP64 reductions and
Torch 1/four-worker/native 32 remain fixed. The existing fatal flag persists.
Fresh actual-node physical/effective available memory must pass the original 4GiB
preflight immediately before program entry. Admission, startup/imports/native
build, initialization/evaluation/training, one scheduled report, fatal/exception
reporting, publication and termination share TERM 115s + at most 5s grace = 120s.
No early learner cutoff, additional sample, timer reset, retry or fallback follows.

## 3. Static acceptance and pinned ordering

The A06 Git-blob literal is 1200 bytes with accepted SHA256
`67f598644882f596ecbfbced2454003c69c9a04cb153a6f62b23079e00bf72e3`.
Exactly these replacements produce A07, and reversing them gives byte equality:

| Change | Count |
| --- | ---: |
| A06 handle `frrie-a06-fatal-callpath-p31-43eec21e` → fresh A07 handle | 2 (time path/cwd) |
| `exp/a06_fatal_callpath_p31` → `exp/a07_scheduled_stack_p35` | 1 |
| `-m pdb -c continue` → `-m pdb -c "<exact arming argument from §1>" -c continue` | 1 |

AST parsing of the expression after `!` confirms exactly the call to
`__import__('faulthandler').dump_traceback_later`, positional 60 and keyword
`repeat=False, exit=False`; no target assignment exists. Static shell tokenization
confirms one arming argv token before `-c continue` after `-X faulthandler -m pdb`.
Both outer text and isolated heredoc supplied on stdin to
`ssh hmasd-wsl-node /bin/bash --noprofile --norc -n` return 0, empty stdout/stderr.
No supplied command was executed. Committed helper/stdin bytes at 30643b7 match
§1 and the starting HEAD blobs. The published document's literal readback matches
the checked bytes.

Read-only inspection used the selected venv's `pyvenv.cfg` (home `/usr/bin`,
version 3.12.3), `/usr/lib/python3.12/pdb.py` and its direct cmd/bdb boundaries:

- `pdb.py` lines 1925–1950: option order becomes `commands`; one `Pdb` instance
  extends `rcLines` once before its run/restart loop.
- `_run`, lines 1720–1739, waits for the target main file; `user_line`, lines 321–329,
  enters interaction at its first positive line event, before executing that line.
  `bdb.py` lines 105–120 supplies the line-dispatch boundary.
- `setup`, lines 290–307, transfers `rcLines` into `cmdqueue` and clears `rcLines`.
  `interaction`, lines 411–427, invokes that setup and the command loop.
- `cmd.py` lines 116–141 consumes `cmdqueue.pop(0)` before stdin. The arming command
  is consumed first, then continue; neither remains queued for a later exception
  or restart prompt. `pdb.default`, lines 436–460, strips `!` and executes the
  expression; it does not return a truthy stop value for this call.

This establishes the intended static initial-stop ordering and single consumption.
It does not demonstrate actual arming/report emission. Pdb also reads rc files
before startup commands: the current `/home/wu/.pdbrc` is absent and original 43ee
contains no root `.pdbrc`. No rc input was added or changed. Original module
resolution and startup happen before the initial target stop and remain charged
to the cap. Later no-second-body behavior reuses the accepted A05 fixture and
must still be read from actual terminal evidence; the standard restart notice
alone is not a second traversal.

Receipts under the direction checkout's
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_preparation_p35/`
are `command.sh`, `arming_argument.txt`, `static_acceptance.json` and
`pinned_stdlib_sections.txt`. DM's existing `owner_packet.json` is preserved.

## 4. Cost, coverage and terminal route

Per-arm cost context: one seedless A chain, maximum 120s invocation-wall sum and
execution critical path. Reuse A06's 118.40s as a complete-wall anchor, not a
completion/progress forecast. Per-arm timing, aggregate CPU, scratch and complete
descendant RSS remain unknown. The original exposure ceilings in card §3 are
unchanged; actual work remains unknown until output establishes it.

Post-learner coverage is the accepted A05 capture recipe plus static changed-input
acceptance here; it is not a check of full learner publication. The scheduled
channel has not been executed during preparation. A usable scheduled report may
remain informative after subsequent timeout, under card §2; one snapshot locates
a caller and does not prove permanent hang, progress rate or a causal writer.
Preserve scheduled header/main caller/other threads separately from fatal reports,
Python exception, helper errors and learner output. Supervisor exit 0 alone does
not prove original completion.

Root alone dispatches/observes the accepted handle. On terminal receipt reuse this
CM for E0, then DM applies card §2 and publishes intake/brief/audit. Every terminal
boundary ends the allocation; no timer rearm, second sample, repair, setup,
extension, fallback, new seed or full B is allocated. Uncertain acceptance is
reconciled against the same handle, never a relaunch.

Engineering scope §4 addition is exactly card §4's **one bounded watchdog thread
and at most one scheduled stack report**, reusing existing fatal/exception
facilities. No new source, runner, framework or recurring monitor is added.

scope: one bounded watchdog thread and scheduled stack report per A07 card section 4
