---
name: hmasd-pm-round-metrics
description: Measure one complete HMASD Project Manager workflow as one model-and-effort sample. Use only in the persistent PM task to start and close local quality, token-cost, and elapsed-time measurement, append later attributable quality events, or summarize completed samples.
---

# HMASD PM Round Metrics

## Boundary

Use this Skill only in the persistent Project Manager task. It measures PM
operation; it grants no scientific, workflow-design, formal-compute, browser,
experiment, or additional code authority. Treat one complete PM workflow and
its direct downstream closure as one sample.

The bundled script reads only the current task row in Codex `state_5.sqlite` and
token/settings events in its rollout. It never reads message text. It writes
only the non-sensitive, Git-ignored local ledger:

```text
logs/pm-model-performance/ledger.jsonl
```

Deleting `logs/` or replacing the workspace deletes this history. Do not stage
or commit the ledger.

## Interpreter and script

Use the Python interpreter supplied by the Codex workspace dependency runtime;
the script uses only the standard library and does not require PyYAML.

```text
.agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py
```

Pass the live PM task ID explicitly as `--thread-id`. A session ID is an
address, not authority; this Skill never stores it in Git-tracked configuration.

## One complete workflow

At the beginning of every complete PM workflow, run exactly one `start`:

```powershell
python .agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py start --thread-id <live-pm-task-id>
```

Keep the returned `round_id` in the task context. Do not start a second round
for the same PM task while one is open.

After the workflow and its direct downstream work are complete, run exactly one
`close` as the final substantive tool action:

```powershell
python .agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py close --thread-id <live-pm-task-id> --contains-code-work true|false
```

The interval between those two commands is the measured wall-clock time. Do not
replace it with daily aggregation or active-time estimation. The script verifies
that one model and one reasoning effort remained active. On
`CONFIGURATION_CHANGED`, no valid sample is written; do not invent a mixed
configuration category.

## Quality events

`close` writes a final score of 100 when no attributable event is known. If a PM
responsibility defect is known then or discovered later, append it with:

```powershell
python .agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py add-event --round-id <round-id> --event-type <type> --incident-id <incident-id> --evidence <short-evidence> --code-related true|false
```

Allowed event types and fixed deductions are:

```text
post_acceptance_defect  20 each, correctness deduction capped at 40
downstream_rework       10 each, closure deduction capped at 25
workflow_violation      20 each, compliance deduction capped at 20
pm_caused_clarification  5 each, clarity deduction capped at 15
```

Every added event is mechanically `attributed_to_pm=true`, receives a unique
event ID and is appended rather than replacing history. Related events share an
`incident_id`. A problem found and corrected before PM acceptance is not a
quality event; its token and time costs already remain in the sample.

## Token price and summary

The script prices cumulative token deltas, never the sum of repeated
`last_token_usage` events. Cached input, cache writes, and reasoning output stay
separate; reasoning output is already part of output and is not charged twice.

The embedded user-supplied reference rates are USD per million tokens, effective
2026-07-26:

```text
model            input  cached  cache-write  output
gpt-5.6-sol       5.00    0.50        6.25    30.00
gpt-5.6-terra     2.50    0.25        3.125   15.00
gpt-5.6-luna      1.00    0.10        1.25     6.00
```

The current reference table has no second pricing tier. Unsupported models fail
closed instead of borrowing another model's price.

Run `summary` only when comparison is requested:

```powershell
python .agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py summary
```

Group only by `(model, reasoning_effort)`. Report sample count, median quality,
median USD cost, median wall-clock seconds, code-work sample count, and raw
quality-event counts with a separate code-related event breakdown. Do not add
task-difficulty normalization or infer scientific quality from experimental
outcomes.
