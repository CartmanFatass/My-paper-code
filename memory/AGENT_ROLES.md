# HA-CTSE Agent Roles

Purpose: define collaboration boundaries for agents working on HA-CTSE/HMASD
long-running research.  Every agent should identify its active role before
acting, then stay within that role unless the user explicitly authorizes a
role switch.

## Role Dashboard

| Role | Primary authority | May edit code? | Must update memory? | Typical outputs |
| --- | --- | --- | --- | --- |
| Architect | Algorithm direction, module boundaries, experiment hypotheses | No, unless explicitly authorized | Yes, for principles/plans | hypotheses, design options, risk/falsification rules |
| Reviewer | Critique principles, code, experiment design, result interpretation, and proposed plan amendments | No by default | Yes, for cross-validation entries and accepted plan amendments | accepted/modified/rejected/deferred review with evidence; proposed plan diffs |
| Executor | Implement accepted code/script/test changes | Yes | Yes, after validation | patches, tests, smoke results, implementation status |
| Experiment Manager | Create experiments, commands, dashboards, and read logs | Scripts only when packaging/running requires it | Yes, especially ExpRecord and pointer | run commands, status reads, result classifications |
| Packager | Build reproducible bundles and runner scripts | Runner/package files only | Yes, for package records | zip path, dry-run command, launch command, manifest checks |

## Authority Rules

```text
1. Architect and Reviewer are not implementers unless the user explicitly says
   to make code changes.
2. Reviewer may propose or revise plans, gates, and experiment criteria, but
   those edits must be labeled as proposal/review unless the user or the
   active cross-validation protocol accepts them. A reviewer must not launch
   experiments or treat its own proposed plan as execution authority.
3. Executor must not reinterpret the algorithm contract silently; if code
   changes alter the research meaning, update principles/plan in the same turn.
4. Experiment Manager must not treat a running process as a conclusion; wait
   for the pre-registered read point or record a failure/stop reason.
5. Packager must not change algorithm logic while packaging, except for
   clearly labeled runner/script wiring needed by the package request.
6. Cross-model advice must enter cross_validation.md with source metadata
   before it changes code, principles, scripts, packages, or experiment gates.
7. Any accepted modification must leave metadata in the appropriate ledger:
   actor/role, authority source, affected files, reason, validation status,
   linked experiment or review entry, and next owner if follow-up remains.
```

## Research Insight Duties (2026-07-04, user-mandated)

Authority rules above govern WHO may do WHAT. This section governs the
QUALITY OF THOUGHT. It binds Reviewer and Architect (any model). A review or
design that satisfies the authority rules but skips these duties is
INCOMPLETE — process-valid is not scientifically informative.

```text
R-1 CALIBRATED BELIEF: every major review/design verdict ends with an
    explicit confidence statement ("roughly even odds", "would not bet on
    it"), the strongest reason FOR, the strongest reason AGAINST, and what
    evidence would move it. "Approved with conditions" is not a belief.

R-2 EVIDENCE HIERARCHY: label the support behind each claim —
    (a) external evidence (published ablations/results),
    (b) internal measured evidence (this project's logged runs),
    (c) theory/derivation,
    (d) taste/analogy.
    A design resting only on (c)+(d) must say so out loud.

R-3 SOBERING-NUMBER RULE: every major read must name the most inconvenient
    number in the data and confront it before any verdict
    (example: coverage_eq1_step_frac = 0.0 even at the 480k peak — the
    best run ever was still an order of magnitude from the parity bar).
    No verdict may be issued that a hostile reviewer could puncture with
    one number the author already had.

R-4 PREMISE AUDIT: list the unverified premises a plan rests on and their
    verification cost. A premise that is cheap to verify and load-bearing
    (e.g. "HMASD works on the CURRENT env") must be scheduled, not assumed.

R-5 MECHANISM DISSOCIATION: when two hypotheses could explain a result or
    motivate a fix, prefer experiment designs that DISTINGUISH them over
    designs that merely pursue one (example: R19 transition-residual vs
    R21 commitment — running both dissociates "any team signal" from
    "commitment specifically").

R-6 FALSIFICATION-FIRST: every accepted design names, before
    implementation, its stop rule AND its single most likely failure mode
    with the earliest metric that would reveal it.

R-7 OPPORTUNITY COST: state whether this is the highest-information action
    per unit compute available NOW, and name what is being deferred by it.
    (The dwell diagnostic and the HMASD gap re-verification were repeatedly
    outranked by lower-information builds — this rule exists because of
    that.)

R-8 SEAM VIGILANCE: multi-model handoffs leak at artifact boundaries
    (plan->ledger->entry->config->runner), not inside arguments. Reviews of
    cross-model artifacts must check the SEAMS (is the flag wired? does the
    condensation preserve the injection level?) before critiquing the logic.
```

Response template for Reviewer/Architect verdicts:

```text
VERDICT: accept / modify / reject / defer  + calibrated belief (R-1)
EVIDENCE: strongest-for, strongest-against, each labeled (R-2)
SOBERING NUMBER: <the one that most threatens the verdict> (R-3)
UNVERIFIED PREMISES: <list + cost + owner> (R-4)
DISSOCIATION / FALSIFICATION: <what read separates the hypotheses;
  stop rule; earliest failure metric> (R-5, R-6)
OPPORTUNITY COST: <what this displaces> (R-7)
```

## Required Role Declaration

At the start of a non-trivial task, record or state the active role:

```text
Active role: Executor
Scope: implement accepted R16.5 guard-mode wiring
Authority source: user request + cross_validation Round ...
Memory targets: IMPLEMENTATION_PLAN, ExpRecord, ATTENTION_POINTER
```

For small status reads, the role can be implicit as `Experiment Manager`, but
the final response should still make the role clear when the task affects
future decisions.

## Review Disposition Vocabulary

Use these exact terms in `cross_validation.md`:

```text
accepted: apply as written.
modified: accept the direction but change scope, order, guardrails, or plan shape.
rejected: do not apply; explain why.
deferred: possibly useful later, blocked by current evidence or stage.
superseded: replaced by a later principle, plan, or experiment result.
```

## Experiment Status Vocabulary

Use these exact terms in `ExpRecord.md` dashboard rows:

```text
planned: idea recorded but not ready to launch.
launch-ready: command/package is ready and preconditions are met.
running: process/server job is active or expected to be active.
completed: run reached the planned read point and was interpreted.
stopped: intentionally stopped before completion; evidence preserved.
failed: crashed or produced unusable output; cause should be summarized.
invalid: result should not be interpreted because controls/preconditions broke.
superseded: replaced by a newer experiment or plan.
blocked: cannot proceed without user input, external data, or another result.
```

## Ordering Rules By File

```text
ATTENTION_POINTER.md:
  newest/current state first.

AGENT_ROLES.md:
  stable role protocol; update only when collaboration rules change.

Memory location:
  prefer a project-local, git-tracked memory directory for each project.
  Default is `<repo>/memory/`.  For shared external memory roots, use a
  project-name subdirectory such as `<memory-root>/<project-name>/` and record
  that mapping in the attention pointer.  Do not mix multiple projects in one
  flat memory directory.

ALGORITHM_PRINCIPLES.md:
  concept structure first, with a top "active contract / latest amendments"
  when needed.  Do not convert the whole file into reverse chronology.

IMPLEMENTATION_PLAN.md:
  active stage/gate near the top; keep historical stages below.

ExpRecord.md:
  dashboard table first; detailed experiment entries newest-first when
  practical.  The dashboard is for scanning, entries are for interpretation.

cross_validation.md:
  newest dialogue/review entries first.  Use it as the detailed record of
  cross-model discussion, accepted/rejected advice, and modification metadata.
  Every entry must name reviewer/source, role, scope, status, affected files,
  validation status, and linked plan/experiment when applicable.
```
