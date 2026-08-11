# HMASD Code Context Guide

This reference helps the Code Project Manager and bounded code children rebuild
the smallest sufficient understanding for a code task. It is loaded only when a
task needs nontrivial code scoping or cross-module orientation.

It grants no authority, changes no review or verification trigger, and is not
an admission checklist. Natural-language judgment remains primary. Exact paths,
contracts, tests, and tool output are factual anchors after the task is
understood.

## 1. The operating model

A model has no durable project memory. A long-lived repository therefore cannot
depend on one session remembering earlier discussions. It must make the relevant
understanding reconstructible from:

- the current user goal and assignment;
- the stable project map;
- the owning module and its immediate interfaces;
- direct producers and consumers;
- protected semantics implicated by the change;
- the smallest evidence that can expose a wrong implementation.

The goal is not to load the whole repository. The goal is to compile a
task-specific context slice.

```text
user intent
    -> task model
    -> project-map orientation when needed
    -> owning module
    -> direct semantic dependencies and consumers
    -> implementation
    -> risk-sized evidence
```

Good module boundaries compress context. When a consumer relies only on a
stable interface and invariant, the child does not need the producer's complete
implementation.

## 2. Choose a context depth

These levels are judgment aids, not automatic gates. Begin with the smallest
plausible level and expand when live evidence exposes a direct dependency or
protected semantic.

### Local context

Typical work:

- a pure helper or parser defect;
- a localized validation or formatting issue;
- a direction-local diagnostic;
- an isolated test correction whose behavior is already clear.

Usually read:

- the target symbol;
- its direct caller or call site;
- the focused test or smallest reproducer;
- the assignment.

Do not load project history, unrelated designs, broad archives, or the full
project map merely because they are available.

### Coupled context

Typical work:

- a shared interface or state shape;
- storage, batching, caching, or reset behavior;
- a collector/runner connection;
- a helper used by multiple live consumers;
- a behavior-preserving modularization.

Add:

- the relevant section of `docs/project/PROJECT_MAP.md`;
- the state or responsibility owner;
- direct producers and consumers;
- the smallest shared-contract tests;
- checkpoint or artifact code only when the changed value crosses that
  boundary.

The important question is not only “what does this module import?” but “what
property do its consumers assume?”

### Load-bearing context

Use this level when the task may change any of the following:

- environment/source or visible information;
- external or intrinsic reward;
- probability support, factorization, or stored log-probability;
- gradient, detach, optimizer ownership, initialization, or update exposure;
- RNG stream ownership or consumption order;
- masks, clocks, recurrent state, lifecycle, replay, or credit;
- checkpoint meaning, artifact schema, phase connection, or result branch;
- a claim-bearing symbol bound by a design or `CODE_SCIENCE_INDEX.md`.

Add the exact assignment-named design, the live code-science binding, the
relevant runner and artifact/reload boundary, and the focused tests that reject
a plausible wrong mechanism. Runtime facts are loaded only when the assignment
needs them.

A load-bearing task is not automatically a formal experiment or an external
review. Existing project triggers still decide those actions.

## 3. Bounded reconnaissance

Before a nontrivial implementation, form a plain-language task model. The
following questions help the model notice missing context; they are not required
headings and no artifact must be generated merely to answer them.

- What user-visible or scientific outcome is this task meant to preserve or
  change?
- Which module owns that behavior or state?
- What is that module explicitly not responsible for?
- Which direct consumers rely on its ordering, probability, lifecycle, schema,
  or provenance?
- Is each dependency an ordinary runtime call, shared state, artifact contract,
  scientific lineage, or authority boundary?
- Which internal choices are reversible engineering details?
- What is the smallest wrong implementation the evidence must reject?

Stop reconnaissance when the task model is sufficient to select a bounded
implementation and its risk-sized evidence. Do not keep reading history in
search of absolute certainty.

## 4. Scope discovery without scope drift

The expected path set is a starting hypothesis, not permission to hide a real
dependency and not an invitation to clean nearby code.

When the task appears to require an additional path, ask:

> Would the requested outcome be incorrect or incomplete without changing this
> path?

If the answer is yes:

- identify the observed dependency;
- explain why the original scope is incomplete;
- update the affected plan branch and path ownership intentionally;
- preserve all unrelated work;
- continue when the added change is inside existing authority and frozen
  semantics.

This is a necessary consequential change, not a generic blocker.

If the answer is no:

- record the observation only when useful;
- leave the path unchanged;
- do not rename, move, abstract, reformat, or modernize it in this task.

This is opportunistic refactoring.

Escalate only when the new path requires missing authority or a material
outcome-changing scientific choice. An unspecified reversible implementation
detail is decided locally.

## 5. The parent is a context compiler

The Code Project Manager does not merely forward the user sentence. It turns
the user goal and bounded reconnaissance into a self-contained natural-language
assignment.

A useful child brief explains:

- why the task exists now;
- what behavior or failure matters;
- how the named modules jointly realize that behavior;
- what decision is already frozen;
- what must remain true;
- what is explicitly outside the task;
- what evidence will demonstrate completion.

Exact paths and commands follow as anchors. They do not replace the explanation.

Do not delegate through unresolved references such as:

- “follow the plan above”;
- “fix this part”;
- “continue the previous change”;
- “use the result I just found.”

Material parent-side discoveries from repository reads, tests, or tool output
must be summarized into the assignment. Forked turns are background context and
never supply additional authority or substitute for the brief. Fork defaults
remain defined by `AGENTS.md` and the applicable role charter; do not duplicate
them here.

Keep child assignments short and self-contained. This guide remains focused on
code context and does not depend on a separate assignment-writing framework.

## 6. Child autonomy and return

A bounded child reads the assignment, its role, the named files, and only the
immediate interfaces needed to complete the work.

The child uses ordinary reversible engineering judgment. Before returning a
blockage it distinguishes:

- a missing authority or material outcome choice;
- a genuinely required path amendment;
- an ordinary local implementation decision;
- a retryable tool or test failure;
- an incomplete observation that bounded reconnaissance can resolve.

The child result begins with its conclusion in natural language:

- what it found or changed;
- why that result satisfies the task;
- which cross-module effect it checked;
- what uncertainty or residual risk remains.

Exact changed paths, commands, and results follow as a compact factual tail. A
mechanical envelope alone is insufficient.

## 7. Expand context only along a reason

Expand the read set only when a concrete edge appears:

- a direct producer or consumer;
- a state owner;
- an artifact or checkpoint boundary;
- a protected semantic;
- a scientific-lineage dependency;
- a test that expresses the relevant contract.

Do not preload unrelated workstreams, all generation modules, every external
review, or the complete research ledger.

If repeated local work cannot be understood without reading a large fraction of
the repository, treat that as possible architecture debt. The first response is
not another workflow rule. Consider whether state ownership, responsibility, or
the public interface is unclear.

Create a stable module note only for a genuinely shared, load-bearing surface
when repeated work shows that the interface cannot be reconstructed cheaply
from code and tests. Do not create a repository-wide module registry.

## 8. Prose, scripts, and mechanical checks

Use prose for:

- purpose and responsibility;
- tradeoffs and proportionality;
- when to expand context;
- how to distinguish necessary scope from opportunistic work;
- what a result means.

Use scripts for facts that are deterministic and repeatedly checked, such as:

- path and symbol existence;
- schema parsing;
- exact command exit status;
- workspace boundaries;
- artifact inventory and reload.

A script may enforce an already-decided boundary. It must not decide whether a
brief, design, research argument, or implementation is semantically sufficient.
Mechanical output informs the owning role; it does not become another
acceptance owner.

Do not add a context checker, module registry, mandatory impact form, or new
BLOCKED state for this guide.

## 9. Maintenance

Update this reference only when repeated real tasks show that the context
selection model itself is wrong or materially incomplete.

Do not add one-off incident details, task IDs, current model names, current
generation numbers, or temporary tool workarounds. Concrete recurring defects
belong in the existing workflow incident route; ordinary successful use creates
no record.
