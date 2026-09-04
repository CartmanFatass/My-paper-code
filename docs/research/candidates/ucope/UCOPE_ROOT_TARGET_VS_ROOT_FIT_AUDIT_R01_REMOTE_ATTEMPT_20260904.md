# UCOPE root target-versus-fit R01 — remote technical-attempt record

- Object: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Evidence class: `A/RECON`
- Frozen launch SHA: `997f49c3cbefffee88d83d7b7de750a078d1a1ca`
- Frozen input SHA-256: `1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676`
- Execution route: configured `wsl_4070` remote-first node
- Status at freeze: `ATTEMPT_01_TECHNICAL_SETUP_FAILURE / PRE_ADMISSION / NO_SCIENCE`
- Date: 2026-09-04 PDT

## Attempt 01 direct facts

The request-specific detached worktree materialized cleanly at the frozen launch SHA. The staged
retained summary was 1,273,684 bytes and matched the frozen digest. The supervisor accepted task
`ucope_root_target_fit_r01_997f49c3_01`, then terminated it with exit code 2 before resource
admission. Its result root and admission receipt remained absent.

The retained supervisor wrapper was 1,853 bytes with SHA-256
`5b80f0fc6f3b754e1d98c9d6dffc87dd900d34212e13746b17f97f49950de2ca`. Its recorded command was:

```text
eval '/bin/bash -lc cd /home/wu/hmasd-worktrees/ucope_root_target_fit_r01_997f49c3_01 && ...'
```

The task log directly observed Python resolving the first script below `/home/wu`, not the exact
worktree. No preflight, runner, RNG, reconstructed row, scientific output, or result branch was
created.

## Reproduction and classification

CM reproduced the recorded shell parsing without invoking preflight or scientific code:

```text
eval '/bin/bash -lc cd /tmp && pwd'
-> /bin/bash -lc cd /tmp
-> the inner shell receives only `cd`; `/tmp` is `$0`
-> the outer shell runs `pwd` in /home/wu
```

The supervisor flattens command arguments with `COMMAND="$*"` before emitting an `eval`. This lost
the intended `bash -lc` command-string boundary and left the remaining commands in the supervisor's
home directory. The reproduced classification is therefore **technical setup failure before
admission**, not an inference from stderr alone. It supplies no scientific polarity and does not
consume the A/RECON object's single result-bearing invocation.

## Decisions this record produces

### Decision 1 — disposition after reproduced pre-admission setup failure (object tier)

Options:

- **(a) Outcome-blind fresh technical attempt.** Keep the same object, launch SHA, frozen input,
  precision, RNG, comparator, counts, cost cap, result rule and relative output root. Use new
  request-specific task/worktree/input identifiers ending in `_02`; place one source-external
  `launch.sh` in that input root; let it enter the exact worktree and run the single remote
  `admit-memory && runner` sequence. Pass only `/bin/bash <absolute-launch-script>` to the
  supervisor so its argument flattening cannot alter shell operators.
- **(b) Park after attempt 01.** Preserve the technical record without seeking a result.
- **(c) Fall back locally or reuse task 01.** Both violate the current remote-first and
  no-duplicate boundaries and are inadmissible.

Recommendation: **(a)**. The defect is reproduced, outcome-blind, outside scientific code, and
repairable without changing the frozen assignment.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

## Attempt 02 frozen operational boundary

```text
task_id=ucope_root_target_fit_r01_997f49c3_02
worktree=/home/wu/hmasd-worktrees/ucope_root_target_fit_r01_997f49c3_02
input_root=/home/wu/hmasd-inputs/ucope_root_target_fit_r01_997f49c3_02
launch_script=/home/wu/hmasd-inputs/ucope_root_target_fit_r01_997f49c3_02/launch.sh
relative_result_root=temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904
```

The launch script is request-scoped runtime orchestration outside Git/source. It must contain one
literal remote resource admission joined to the exact runner by `&&`; it does not add a research
guard, scheduler, retry loop, lease or other object machinery. Before supervisor acceptance, the
operator verifies task 02, its worktree/input/result roots and the local result root are absent.
After terminal status, only task 02 is observed and only its request-specific result root is copied.
