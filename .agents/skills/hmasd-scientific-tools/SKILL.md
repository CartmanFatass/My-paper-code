---
name: hmasd-scientific-tools
description: Use for HMASD literature retrieval, computed experiment counts, run-table analysis and plots, a concrete performance bottleneck, or choosing a MARL baseline/environment adapter. Supplies executable analysis and task-specific tool routing.
---

# HMASD scientific tools

Owner approved adoption batches 1 and 2 on 2026-09-05. Use tools to retrieve,
calculate and measure facts instead of repeatedly deriving them in prose. Select
only the mode needed now; this is not a launch checklist or new review layer.

- **DM/Root literature:** for a concrete mechanism, comparator, unexpected-result or
  related-work question, start with the two local libraries using
  [local-literature.md](references/local-literature.md). Search indexes first and
  verify decision-relevant claims in the source. Reuse relevant prior retrieval;
  routine implementation does not require another literature pass. For a specific
  coverage gap or current-information need, use official paper/code sources or the locally available
  `C:/Projects/HMASD-scientific-skills/.agents/skills/paper-lookup/SKILL.md` and its
  relevant database reference. Existing web/connector tools remain valid alternatives.
  Retrieve public queries, retain exact relevant excerpts/links, and distinguish
  metadata existence from support for a claim. Do not route to an additional LLM
  research service merely because an upstream skill recommends it.
- **DM counts:** compute expressions from actual configuration using Python/NumPy;
  report units and dominant multipliers. An update round is not optimizer.step;
  agent transitions are not independent episodes. Do not run a simulation just to
  count a known loop. Unknown unit time remains unknown.
- **Intake analysis:** use `scripts/summarize_runs.py` on selected endpoint scores
  already aggregated once per independent training run, task and arm. It emits
  descriptive summaries, complete paired differences and an optional point plot.
  Do not pass episode rows or repeated checkpoints as independent training seeds.
  For curves or different estimands use a short task-specific Pandas/SciPy/Matplotlib
  script instead. A tool's output does not choose the estimand or establish validity.
- **CM performance:** use existing timings first; if a concrete decision remains,
  scope a short torch.profiler window or torch.utils.benchmark call in the current
  engineering assignment. Preserve declared scientific semantics; separate profiling
  overhead/microbenchmarks from complete-run wall. No repeated mandatory profiling,
  service, or whole-history replay. Native opaque functions may need native sampling
  or phase timing; torch operator traces alone cannot explain their internals.
- **Baseline, graph or environment work:** read [adapters.md](references/adapters.md)
  only for that specific integration. Prefer existing fixed reference implementations
  before rewriting PPO, collectors, buffers or graph algorithms.

Use the existing execution node and interpreter appropriate to the task; installing
an analysis skill does not install its packages on another node. Optional dependencies
go into the selected task's isolated environment, with compatible versions recorded;
do not upgrade the live research interpreter. Frozen experiments keep their contracts.
New tools do not authorize new arms, altered reward/information or changed dtypes.

Keep compact tool-produced tables/timings and relevant source snippets in the normal
intake/engineering record. Root/DM/Pro judge scientific implications; reviewers name
concrete risks to actual measurements. Do not add generic power, normality, p-value,
exactness or all-seeds-positive prerequisites. One seed remains a local observation.

Example (from repository root, using the chosen analysis interpreter):

```text
python .agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py scores.csv --out temp/analysis/summary.json --baseline DIRECT --plot temp/analysis/runs.png
```

CSV columns: `task,seed,arm,score`. `score` is a finite, explicitly selected endpoint;
`seed` identifies the independent training instance and its justified pairing, not an
evaluation episode. Arm pairing is valid only when the study actually declares it.
