# VSPC1 B03 intake — pre-admission shell failure

The accepted supervisor task failed before admission and before the scientific
runner. The exact missing checkout is now staged. The selected scientific pair
remains unrun; its source, method, master8201, prediction and budget are unchanged.

## 1. What I checked and the rule applied

Root returned the failed accepted handle, then the same CM collected direct
[terminal/staging evidence](VSPC1_NATIVE_HOLD_VALUE_B03_CWD_CORRECTION_EVIDENCE_20260908.json)
and appended the correction to [technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B03_TECHNICAL_ACCEPTANCE_20260908.md#mechanical-cwd-correction-after-failed-supervisor-acceptance),
commit `698b8aeff26f2b9ae21d4cb8d1bf8a255b161d38`. I read the complete return:
supervisor status, full failed log and wrapper, absence of admission/output,
actual detached HEAD/clean state, required source files and unchanged script.
I compared these with [card §8](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md#8-accepted-source-and-sole-root-execution-binding)
and the original literal command. No source, test, model, admission or scientific
execution was repeated during this DM intake.

The card's dependency rule remains verbatim:

> A primary dependency is incomplete
>
> No dependent performance judgment; retain independently trustworthy counts/returns. Missing H alone leaves a trustworthy primary pair reportable with H-relative use unresolved.

Here no primary pair was generated at all. Under evidence-spec §11.8.7 this is a
launch-path fact, not a native-return observation or a negative mechanism result.
The applicable [ROOT_OPERATIONS supplied-command section](../../../project/ROOT_OPERATIONS.md#execute-the-supplied-launch-command)
states verbatim:

> Supervisor acceptance, admission and scientific execution are separate facts. If a command
> fails before admission, retain its exact failed identity and evidence; continue only the
> already-authorized correction after acceptance is reconciled. Never infer a scientific retry,
> changed source or extra allocation from a wrapper failure.

Root explicitly requested this bounded correction. It realizes the already
specified source staging before the first scientific invocation; it does not
relax the card's no-additional-scientific-retry boundary.

## 2. Observed failure and counts

Original handle: `vspc1_hold_value_b03_8201_7a8ed3aa5d25`, PID3009140, terminal
`failed`, exit1, tmux inactive. Its log records start and end at
`2026-09-09T06:40:46+08:00` and the exact error:

```text
/bin/bash: line 2: cd: /home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25: No such file or directory
```

Reported wrapper wall is `0.00s` and peak RSS `3200KiB`. The displayed rounded
zero is not a claim of zero machine work, and these are not learner resource
measurements. The later status field `uptime_seconds=392` is not a measured
scientific duration; the terminal log and enclosing command time identify this
immediate shell failure.

The unchanged shell uses `cd && admission && scientific_runner`. The first link
failed; CM also directly observed both admission and output paths absent.
Therefore admission invocations, scientific model/optimizer constructions,
native team steps, Adam calls and evaluations are all zero. No runtime count
artifact was produced; these zero-execution facts follow from the observed shell
boundary and its short-circuit order. There is no native endpoint, parameter
movement, moment update or primary value to interpret.

The original supervisor directory and its log/status/exit/runner files remain
preserved. The complete failed log is also retained in the existing B03 engineering
directory as `failed_task.log`, and in the committed evidence JSON. No evidence
root was deleted, and no historical result was reclassified.

## 3. Accepted mechanical correction

The same CM transferred committed Git objects using the existing bundle route
and created the exact detached cwd already required by the card. Direct readback
now shows HEAD **`7a8ed3aa5d25ded71164aa338749d09318124dcf`**, empty porcelain status,
detached HEAD, and the admission script, fixed runner and normalization module
present at:

`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`

The scientific script is unchanged at
`/home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh`.
Prior syntax/readback is reused; its recorded digest still matches. No source
substitution, source edit, recompilation/test, scientific payload or admission
was performed by CM. A stalled preliminary remote Git read was interrupted;
the completed bundle/staging facts, rather than that preliminary read, establish
the ready checkout. Scope §4 additions and new scientific exposure: none.

CM inspected the supervisor: reusing a finished name replaces some task metadata.
Use the fresh name `vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1`, directly observed
`not_found`, to retain the failed task intact. This changes only supervisor
identity. The script, source, master, data/RNG, output, admission path, method,
native observable and all original work/caps remain unchanged.

## 4. Decisions this intake produces

1. **Failure classification, object-tier technical.** Options: (a) retain an
   accepted shell failure before admission, with no scientific result;
   (b) label it a native failure or invalidate the accepted algorithm source.
   Recommend/select (a): the direct log, command order and absent roots establish
   the narrower boundary. Owner-delegated decision (unattended,2026-09-03
   instruction): (a), **OWNER_DELEGATED**.
2. **Mechanical continuation, object-tier technical.** Options: (a) accept the
   completed exact-source staging and submit the unchanged payload under the
   fresh supervisor name; (b) resubmit without staging/reconciliation;
   (c) change source/seed or allocate another scientific pair. Recommend/select
   (a), within Root's explicit correction and P60's original allocation.
   Owner-delegated decision (unattended,2026-09-03 instruction): (a),
   **OWNER_DELEGATED within P60**. This permits the first selected scientific
   invocation, not an additional training attempt or a new allowance.

The prospective WITHIN(.55) prediction remains unscored; owner prediction remains
not taken. No scientific interpretation, family/lifecycle/priority disposition,
formal UAV-entry decision, new card or extra owner item follows. Owner reviews
and relevant ledger overrides were empty at this boundary. Owner flag: none;
the operational failure and its resolved staging cause remain explicit.

## 5. Precise next action

Root integrates the CM correction and this DM intake/binding, then submits the
ready command once:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

The existing script performs fresh actual-node memory admission immediately
before scientific state. Output remains
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`;
admission remains its sibling `native_hold_value_b03_8201_7a8ed3aa5d25_admission.json`.
Keep CPU FP32/one process/one numerical thread,286720 native steps,2048 Adam,
96 evaluations,1800s/arm and3600s/complete pair. The first failed shell has no
scientific clock to resume or reset; its separate wrapper record is retained.

Root observes the newly accepted handle and returns terminal facts to the same
CM for collection, then this DM for scientific intake. The next discriminator
remains the original normalized GATED/full-MLP/H comparison. No additional arm,
seed, evaluation, H completion, source substitution or scientific retry is selected.
