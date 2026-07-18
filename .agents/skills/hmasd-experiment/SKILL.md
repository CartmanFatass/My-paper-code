---
name: hmasd-experiment
description: Use only when an authorized HMASD action creates or mutates an experiment contract, package, launch, Terra Medium monitor subagent, failed runtime stage, analysis-only repair, or terminal closure. Do not use for a one-time status read, interpretation of a closed result, or read-only failure location. Completed code never implies training authority.
---

# HMASD Experiment

Read `docs/project/CURRENT_WORK.md`,
`docs/project/ALGORITHM_PRINCIPLES.md`, the owning contract in
`docs/project/ExpRecord.md`, and
`references/experiment-protocol.md`. If the lifecycle creates or changes
executable MARL code, also read
`docs/project/MARL_ENGINEERING_PRINCIPLES.md`.

## Prepare and Launch

Name the authorized class exactly: code test, engineering smoke, formal
experiment, or scale training. Do not expand it.

Before a conclusion-bearing launch, require the owning contract to fix the
causal edge, comparator, metrics, thresholds, nulls, seeds, environment and
optimizer budgets, outcome branches, prohibited changes, expected wall clock,
placement, and status authority. New or changed executable code also requires
one completed controller review under the engineering principles.

Use the registered CUDA/parallel topology and one timestamped
`logs/<run-id>/` root. Keep staging and final payloads inside that root and
publish payload and terminal status atomically. Do not silently change device,
parallelism, host, budget, or algorithm.

## Monitor, Repair, and Close

Create the single Terra Medium monitor and apply its deadline exactly as defined
in `references/experiment-protocol.md`. The protocol exclusively owns monitor
prompt, wait behavior, terminal payload, and retry limit; do not restate or
invent another monitoring workflow.

At terminal delivery, the controller verifies the registered status once and
reads only the registered result or direct error. Repair only the failed stage.
Never retrain when analysis-only repair suffices, and never rescue a scientific
failure.

Apply the existing result branch, update `ExpRecord.md` once, update
`CURRENT_WORK.md` only if the live objective or autonomy state changes, and
create one terminal result/disposition Git boundary.
