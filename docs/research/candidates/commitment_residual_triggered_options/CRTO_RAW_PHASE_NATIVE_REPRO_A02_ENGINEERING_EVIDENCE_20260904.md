# CRTO RAW phase native-reproduction A02 engineering evidence

Date: 2026-09-04. Object: `CRTO-RAW-PHASE-NATIVE-REPRO-A02`, technical A/RECON.

**Conclusion: `A02-NO-FAULT-WITHIN-BOUND`, normal-completion endpoint.** The single declared
diagnostic completed with exit 0 after 85 supervisor seconds, before its external 90-second
bound. No signal-11 event or fault stack was printed. A complete runner summary was preserved
as technical evidence, not promoted to an A01 scientific result. The earlier R02 fault remains
unlocalized and unexplained; this observation does not establish full-path reliability.

## Frozen contract and scope

Authority: `CRTO_RAW_PHASE_NATIVE_REPRO_A02_SCIENCE_CARD_20260904.md`, committed and pushed
by the DM in `2b1cde8bd` before this invocation. The R02 E0/intake and A02 card were read in full.
The diagnostic asked whether the previously observed signal 11 recurs with a source stack.
Competing explanations remain a repeatable fault, timing/environment dependence, a signal
handler unable to print a stack, and nonrecurrence within the bounded diagnostic.

The local CM worktree/branch were reused:
`C:/Projects/HMASD-worktrees/cm-crto-resume-20260904`, `codex/cm-crto-resume-20260904`.
Only this evidence document changed. No source, dependency, card, intake, owner surface, or test
was edited. No additional smoke ran. Engineering-scope section 4 additions: **none**; zero new
research/runner/test lines. No source materialization, new interpreter, repair, retry, fallback,
checkpoint write/read, extra predictor fit, or separate RAW regeneration was performed.

Execution remained pinned to `wsl_4070` CPU, host `LAPTOP-U9TDKC8A`, and the existing detached
worktree `/home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02` at exact pushed source
`8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`. HEAD and empty porcelain were inspected before
launch and empty porcelain again after completion. This is the same source surface already
verified against Git blobs in the R02 recovery. No uncommitted source was transferred.

Read-only prelaunch runtime metadata confirmed `/home/wu/.venvs/hmasd/bin/python`, Python
3.10.21 built with Clang 22.1.3, NumPy 1.26.3, Torch 2.7.0+cu118. GNU timeout is coreutils 9.4.
CPU FP32, one computational thread, seed 0, fixed 48 TRAIN / 16 EVAL rows, namespaces,
predictor/RAW equations, Adam, cyclic example order, 264 updates, snapshot timing 252..264,
legal-action/G16/charge laws and information boundaries remained unchanged. Only the fresh
task/output identities, external timeout and `-X faulthandler` differ from R02. Fault reporting
changes signal handling and may affect timing; it does not establish a runtime-equivalence claim.

Per-arm cost line: one diagnostic arm, no sweep; the prior failure lasted 18 seconds and this
object has a fixed 90-second machine-time bound. The prior full-run 1304.1200061-second
projection is not this truncated diagnostic's cost forecast. Its already emitted prospective
exposure line was reused as the card directs. Stop: first termination or external bound;
no next invocation follows automatically. Resource envelope: one CPU learner, one computational
thread, expected peak RSS below 2 GiB, fresh physical/effective availability at least 4 GiB.

Post-learner publication coverage: the accepted toy E2E profile still does not cover the formal
publication path with real constants. This remains an open engineering item. This diagnostic
reached publication, but it is not an extension of the test profile and does not localize R02 as
a post-learner failure.

## Exact command and task observation

Task: `crto_raw_phase_native_repro_a02_8d1c5978_01`.
Remote task root: `/home/wu/.agent-tasks/crto_raw_phase_native_repro_a02_8d1c5978_01/`.
The task was authoritatively `not_found` before submission; exactly one launch was accepted.
DM and `/root/tracker_lxh_experiments` received the accepted handle immediately for status
adoption; CM retained direct script, stack and artifact inspection.

The complete inner command was frozen before submission:

```sh
cd /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01_admission.json && timeout --signal=KILL 90s /home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_crto_raw_phase_trace_a01.py run --seed 0 --admission-receipt temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01_admission.json --output-dir temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01 --execution-node wsl_4070
```

Transport used `subprocess.run(['ssh', 'hmasd-wsl-node', remote_command])`, with
`remote_command = '/usr/local/bin/agent-task run <task> ' + shlex.quote(command)` and
`command = 'bash -lc ' + shlex.quote(inner_command)`. Direct inspection of the generated
`runner.sh` established that the entire command, including adjacent preflight, timeout and
faulthandler, survived as one supervisor payload. The summary's reconstructed `exact_argv`
does not include interpreter `-X` options; the executed task script is the evidence for that flag.

| Fact | Direct observation |
| --- | --- |
| Source SHA | `8d1c597871b38edc7d5f139f34f5a3ce2941c7d0` |
| Supervisor / timeout / learner PID | 76515 / 76519 / 76531 |
| Start UTC | 2026-09-04T21:50:53Z |
| Admission assessed UTC | 2026-09-04T21:50:53.773859Z |
| Available physical / effective bytes | 12,920,348,672 / 12,920,348,672 |
| Admission | both 4-GiB floors passed, no failure reasons |
| End UTC | 2026-09-04T21:52:18Z |
| Terminal task | finished, exit 0, tmux inactive |
| Supervisor duration | 85 seconds |
| Runner invocation wall | 80.505860614001 seconds |
| RAW training / checkpoint evaluation wall | 14.019378483993933 / 0.05376777199853677 seconds |
| Peak RSS | 1,276,755,968 bytes, measured, below expected 2 GiB |
| Torch intra-op / inter-op threads | 1 / 1; all four declared thread environment values 1 |
| Timeout endpoint | not reached; normal completion |
| Fault stack text | none printed |
| Output | one 303,260-byte `summary.json` |

A live sample at approximately 38 seconds showed learner RSS 1,234,084 KiB; the summary's
peak-RSS value above is the complete-process measurement. No core file was found in the
worktree root. No crash artifact or earlier root was deleted.

## Printed work and branch limits

Unlike R02, this invocation printed measured counts: 128 predictor tapes, 32,256 generated
predictor examples, 100 predictor updates, 12,800 predictor processed examples, 38,464
environment transitions, 3,520 common-future branch steps, 264 RAW updates, 8,448 RAW
processed examples, 13 snapshots and 208 checkpoint-evaluation rows. TRUE/DERANGED update
and evaluation counts are all zero. These are technical execution counts, not a scientific
assessment of the trace or a claim about R02's unknown counts.

All 13 actual displacement records are present and finite/positive. At update 252 the reported
L2/initial-L2 and Linf/initial-Linf ratios are 0.13399672519322534 and 0.9036122085192626;
at update 264 they are 0.139926127270521 and 0.9272560264718904. All intermediate values are
preserved verbatim in the summary. No checkpoint-performance, competence, phase, or residual
interpretation is made here, and the summary's internal A01 fields do not override A02's ceiling.

Card branch 3 applies: **`A02-NO-FAULT-WITHIN-BOUND`** because the exact diagnostic path
completed normally before the bound and no signal-11 event occurred. Branches 1/2 require
recurrence and branch 4 requires an unestablished execution or another failure; neither is
observed. No failing source location was reproduced, so the descriptive one-location MEI was
not obtained. The earlier signal 11 remains unexplained; normal completion neither clears it
nor establishes that a future run will be reliable. A02 remains technical evidence only.

## Preserved bytes and handoff

Remote output root:
`/home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02/temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01/`.

Local byte-preserving copies:
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01_artifacts/`.
This contains the full summary and task log, executed script, admission, dependency metadata,
frozen launch command, acceptance text and remote digest output. No stack excerpt is omitted:
the complete log contains no fault stack.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| runner.sh | 1791 | `48b6d4e7bda5e12ab5b08458f7159d4e454029ab6acf4701c68b8a36b4bc676c` |
| task.log | 303983 | `1dc5ad5287a924b2105960a6714af5cad5c48e24d77bfbe494ac80cef8a24885` |
| admission.json | 504 | `da1513ac228662d89236080d936ae30772f92d4e337736065d6362395b36e3e5` |
| summary.json | 303260 | `0d9319231c55775568e1d374e2968741a4edc765ebdfd9067e4a9211845ab8f7` |

All four local copies match direct remote `sha256sum` observations. Checks were limited to
source/runtime/task identity, fresh admission, direct execution inspection, output/stack reading,
resource/count fields and byte-preserving copies. No tests or further learner processes were
launched. The diagnostic is terminal; DM owns intake and any next bounded decision.
