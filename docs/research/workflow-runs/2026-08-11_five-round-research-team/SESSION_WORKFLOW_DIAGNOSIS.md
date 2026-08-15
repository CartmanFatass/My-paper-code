# Research-team session workflow diagnosis

## Purpose

This is the maintained diagnosis record for the 2026-08-11 research-team
session. It exists so that context compaction does not force Root and the user
to rediscover the same workflow failures.

This document records what went wrong and the evidence behind that diagnosis.
It does **not** freeze future diagnosis or prohibit redesign. New findings
should update this document instead of creating another competing diagnosis.

The companion action document is
[`MINIMAL_CONTROL_PLANE_REPAIR_PLAN.md`](MINIMAL_CONTROL_PLANE_REPAIR_PLAN.md).

## Current pause state

- G53-B2, RECCT-B4, VSP06-B2R3, ACVC, and the VSP02 Pro archive were stopped at
  safe boundaries.
- No Python research or experiment process was running at the pause check.
- No new Pro send, click, retry, or control action was performed after pause.
- No commit or push was performed after pause.
- G53-B2 candidate `d019688f...` exists only in its isolated worktree. It was
  not run through readiness, integrated, or pushed.
- Existing worktrees and partial implementations were retained so later work
  can migrate rather than restart.

These are historical pause facts, not permanent prohibitions. Resumption is a
separate user decision.

## Executive diagnosis

The session did not primarily fail because the scientific ideas were weak or
because too little work ran in parallel. Root's optimization target drifted
from maximizing scientific discrimination per unit time to making every
intermediate step auditable at final-publication strength.

The research team therefore behaved like an evidence-governance team. It
spent excessive effort on identity, paths, hashes, receipts, fresh roots,
one-shot permissions, and archives instead of repeatedly completing the useful
cycle:

> formulate -> implement -> run -> interpret

## Evidence from the historical log

Source: `events.jsonl`, retained as a historical record with 244 events.

| Measure | Count |
|---|---:|
| Root events | 107 |
| Code Manager events | 66 |
| Explorer Manager events | 39 |
| Experiment Operator events | 6 |
| External Pro events | 3 |
| Publication/archive/ledger events | at least 43 |
| VSP02 correction/repair-chain events | 10 |
| VSP06 correction/repair-chain events | 25 |
| G52 correction/repair-chain events | 7 |

Root and CM account for about 71% of all events, while Experiment Operator
accounts for about 2.5%. Main loops crossed owners approximately 20-29 times.

Only VSP02-B4 completed the entire valid-experiment -> same-direction EM intake
-> Pro convergence chain. VSP02-B5R1 obtained a valid result but did not close
its external-review archive. Most other directions terminated with zero
scientific activity.

Parallelism existed, but it was high-WIP governance parallelism: several lanes
waited for Root to write files, perform Git actions, issue permissions, rename
objects, or publish checkpoints. It was not a high-throughput research
pipeline.

### Log-grounded confirmation

The diagnosis above is not reconstructed from chat memory. The following
sequences are present in the append-only event history:

| Event sequence | Logged fact | What it confirms |
|---|---|---|
| `evt-158 -> evt-163` | EOCIV moved from `READINESS_COMPLETE/CODE_ACCEPTED` to an episode-zero RSS binding terminal | readiness did not exercise the real resource ABI |
| `evt-164 -> evt-180` | G52 moved from `CODE_ACCEPTED` to a preactivity `cl`/Ninja launch error | engineering launch failure was downstream of formal acceptance work |
| `evt-177 -> evt-181 -> evt-216 -> evt-226` | VSP02-B5 first terminated on RSS binding, then B5R1 obtained a valid result and EM intake | the original terminal was repairable engineering failure, not negative science |
| `evt-175` | VSP06 consumed a no-retry Stage-2 namespace before producing scientific evidence | formal identity and one-shot controls were applied before useful observation |
| `evt-232` | G53-B1 ended at a launcher error with no scientific result | a technical terminal was being advanced as a workflow identity event |
| `evt-237 -> evt-239` | VSP02 Pro convergence transport failed and then opened an Agentify source-repair lane | scientific convergence was displaced by transport engineering |
| `evt-244` | Root published another round-ledger checkpoint while the session remained unresolved | Root was still serving the mechanical publication path |

The log also mechanically confirms 244 total events, including 107 Root, 66
CM, 39 EM, 6 Experiment Operator, and 3 Pro events. Those counts do not by
themselves prove causality, but the event sequences above establish the
control-flow failures described in this document.

### Logging was not the failure

The historical log is what made this diagnosis possible. Deleting it, replacing
it with only final success claims, or retaining so little detail that owner
actions and failed attempts cannot be reconstructed would remove
accountability and allow the same failures to be obscured.

The actual logging failures were different:

- mechanical hashes, byte counts, receipts, and publication checkpoints were
  recorded as if they were scientific progress;
- Root became the writer and publisher of other owners' routine engineering
  state;
- numerous low-information checkpoints obscured the smaller number of
  science-changing decisions and real execution attempts;
- the log was coupled to approvals and object renaming instead of remaining a
  passive factual record.

Therefore the repair must preserve an append-only audit trail while reducing
mechanical noise and removing log entries as admission gates. The existing
`events.jsonl` is immutable historical evidence. A successor log may start at
the workflow-repair boundary, but it supplements this file and never deletes,
squashes, or silently rewrites it.

## Confirmed failure modes

### 1. Control order was inverted

Controls appropriate near a final claim-bearing run were applied to ideas,
prototypes, and ordinary exploratory experiments:

- commit ancestry;
- complete path/hash maps;
- CRLF/LF byte identity;
- six-phase readiness;
- exact-once namespaces;
- preactivity no-retry rules;
- full public archival packages.

Scientific meaning was sometimes completed only after these controls. VSP06,
for example, accumulated implementation, byte-map, review, and readiness work
before the host dynamics, tensor schemas, initialization law, counts, and
evaluator caps were fully coherent.

The correct order is to establish what the experiment means before spending
effort on final artifact identity.

### 2. Preactivity engineering failures consumed scientific tickets

Examples included:

- G52 failures involving `cl`, Ninja, PowerShell, and fresh-root behavior;
- EOCIV and VSP02-B5 failures in the Windows RSS FFI before episode zero.

The no-retry rule did not prevent retries. It forced ordinary engineering
recovery to appear as new B5R1, B2, r2, or r3 scientific identities, causing
semantic drift.

An engineering failure before an observation relevant to the scientific
question exists is not a scientific result and should remain inside the same
CM treatment workflow.

### 3. Object levels were conflated

The workflow did not reliably separate:

- direction;
- hypothesis;
- treatment;
- implementation revision;
- execution attempt;
- scientific run;
- archive;
- portfolio round.

Consequences included the same VSP02 direction appearing in multiple loop
slots, README round assignments diverging from actual work, replacement loops
changing meaning, engineering repairs becoming new treatments, and historical
`FILTERED` labels being misread as scientific failure.

### 4. Readiness did not reproduce the real Operator path

Strict readiness substitutes failed to exercise the paths that later failed:

- MSVC/Ninja activation order;
- PowerShell native stderr behavior;
- Windows RSS ABI;
- wrapper/scientific-root interaction;
- the actual Operator command and environment transfer.

As a result, readiness could pass while the real launch failed before science.

### 5. Precision effort was allocated to the wrong objects

Large effort went into easily checked mechanics:

- SHA values;
- byte counts;
- paths and commits;
- receipts;
- line endings.

At the same time, scientifically important semantics remained inconsistent:

- G52 double-counted transitions;
- G53 described `39 = 1 + 38` inconsistently;
- VSP06 used conflicting 21/22 counter schemas;
- host dynamics were incomplete;
- comparator/evaluator activity exceeded frozen caps.

The problem was not merely excessive precision. It was precision applied to
files while scientific semantics remained under-specified.

Real experimental data must not be gated by default float64 bit equality.
Ordinary numerical calculations use appropriate tolerances, while training
claims use effects, variance, and behavior across seeds. Precision becomes a
workflow issue only when it actually changes stability, branching, or
interpretation.

### 6. Root became the mechanical control-plane bottleneck

Root accumulated work that belonged to the semantic owner:

- temporary readiness specifications;
- result copying and installation;
- handoff materialization;
- receipt and byte verification;
- session custody;
- checkpoint publication;
- workflow-log publication;
- Git operations and scheduling.

The large Root event count reflects excessive intervention. Root should spend
its attention on multi-direction scientific exploration, comparison,
prioritization, composition, and cross-owner relay—not act as a shared file
operator.

Git authority does not imply authorship of every tracked file. A file's
semantic owner should prepare its contents; Root only performs necessary final
integration/publication.

### 7. External Pro was used as a file verifier

Pro was shown raw/blob URLs, commits, hashes, byte counts, receipts, and other
transport metadata. This displaced the actual scientific questions:
identifiability, alternatives, claim ceilings, and valuable next
discriminators. Transport failure then became its own engineering project.

Pro-visible input should contain only the natural-language scientific question,
the GitHub repository, branch `aggressive`, and a few relevant repo-relative
paths.

## What the diagnosis does not mean

- Missing implementation is not scientific rejection.
- A missing native host changes engineering cost, not scientific value by
  itself.
- A technical terminal with no relevant observation is not evidence against a
  treatment or direction.
- Historical `FILTERED` labels do not establish direction retirement.
- Reviewer, Verifier, Scout, Git, logs, or archives do not create scientific
  validity.
- The conclusion is not that auditability has no value. It belongs at the
  consumer boundary where it is actually needed.

## Ownership diagnosis

The workflow must use semantic ownership:

| Object | Semantic owner |
|---|---|
| Scientific question, comparator, interpretation, next discriminator | EM |
| Source, tests, runner, environment, launcher, temporary files, retained result | CM |
| Command execution and whether a relevant observation began | Operator |
| Pro page operation and raw answer capture | Transport tool/script |
| Multi-direction exploration, comparison, slot allocation, cross-owner relay | Root |
| Necessary final Git integration/publication | Root |

If an owner cannot modify a file it semantically owns because of a role or tool
restriction, that is a workflow-permission defect. Root manually performing
the edit is not the long-term solution.

## Maintenance rule

When later analysis changes this diagnosis, edit this document in place:

- preserve confirmed historical facts;
- mark corrected conclusions explicitly;
- add new evidence only when it changes the diagnosis or repair choice;
- do not create another parallel “final diagnosis” document.

This is a memory aid, not an approval gate.

Every future material workflow diagnosis must cite the relevant log entries or
state explicitly that it is a new hypothesis not yet supported by the log.
