# Contract grill: proposed archetype set and gate structure

```text
status=RETIRED_AS_A_MECHANISM -- casebook content survives
retired=2026-07-25
retired_by=user
superseded_by=docs/project/WORKFLOW_SIMPLIFICATION.md
ruling=docs/external-review/rounds/20260725_contract_grill_design/21_PRO_OPEN_RAW.md
```

**Retired as a mechanism.** See `WORKFLOW_SIMPLIFICATION.md`. The casebook
survives in `.claude/skills/hmasd-contract-grill/SKILL.md`; the gates,
certificates and validation tiers below do not.

Kept only so they are not re-proposed.

**This document is superseded in part.** The external ruling is
`CHANGES_REQUIRED`: the direction, the division of labour and the three-gate
split are all confirmed, but the mechanism may not close a gate or issue an
authoritative certificate until ten protected changes are incorporated and V2
passes.

Read the reconciliation before treating anything below as current. In particular
the archetype set gains a seventeenth entry and a separate Technique class, the
coverage matrix gains a row and broadens another, the decision ledger's single
ruling field is split three ways, gate closure becomes a mechanical predicate,
reader findings must reach the reviewer losslessly, and the reviewer retains a
mandatory unmediated read that this document wrongly treated as replaceable.

Until V2 passes the reader is **advisory**: it may generate questions, establish
facts, produce a coverage matrix and help assemble the review package. It may not
close Gate A, reduce the reviewer's independent read, issue a durable
certificate, or license implementation by having found nothing.

## Why this exists

On 2026-07-25 a frozen G20R2 contract entered implementation, roughly 5,700 lines
were built against it, and only then was the external reviewer asked whether the
contract was right. The ruling was `CHANGES_REQUIRED` with nine blockers. An
independent adversarial pass by a different model found ten unasked decisions.
**Nineteen findings landed after the code existed**, several invalidating it.

The failure was not implementation quality. Both arms of a controlled tier
comparison produced clean, well-tested code; raising the implementer to a
frontier model improved defect *detection* without improving *stopping*. The
failure was that protected scientific choices were never explicitly identified
before implementation.

The project's existing countermeasure is a five-question pre-freeze checklist in
`AGENTS.md`. It **passed** the contract that contained all nineteen findings. A
checklist asks what its author thought to ask.

## Division of labour proposed

| Role | Does | Does not |
|---|---|---|
| adversarial reader (`fable`) | discovers unasked decisions, establishes repository facts, traces control flow, constructs zero-compute counterexamples | rule on science, decide branch semantics, authorize experiments |
| external reviewer (Pro) | rules on protected semantics, defines smallest refuted unit, decides branch meaning | — |
| Project Manager | drafts, freezes, implements, verifies, integrates | decide protected semantics alone |

Rationale for using a non-Pro reader for discovery: the two readers had
**genuinely different blind spots** on the case above — overlap was roughly five
of nineteen. The fable reader alone found a `1e-8` authority tolerance that can
never fire against ~`1e-3` sampling noise, and eight bootstrap clusters that share
three underlying ledgers. Pro alone found that a suffix-noise slice clobbered
positions before the intervention index, so the audit's conditioning history was
never held fixed at all. Neither subsumes the other.

## Three defence lines

1. A wrong contract must not enter implementation.
2. A right contract must not be wrongly instantiated.
3. A right instantiation must not drift silently as the full shell grows.

| Gate | When | Reads | Prevents |
|---|---|---|---|
| **A** — contract semantics | before any implementation | contract, sources, predecessor code, proposed branch mapping | line 1 |
| **B-core** — realization conformance | after a proof-sized executable skeleton | the actual skeleton code | line 2 |
| **B-delta** — semantic increment | after full implementation | only the diff beyond the certified skeleton | line 3 |

The skeleton contains estimand calculators, data-role split, branch selector,
initialization and gradient path, paired replay, failure path, and result
serialization — no training or evaluation loop.

**B-delta is separate from the assembled-path exercise** because the exercise
proves reachability, not the absence of new protected semantics. A shell can add
evaluation weighting, requalification cadence, optimizer exposure, result
aggregation, branch precedence, a calibration split, comparator information, or
censoring rules with every path still reachable and the conclusion-bearing
quantity changed.

Certificates are versioned (`contract_version`, `decision_ledger_revision`,
`skeleton_binding_hash`, `gate_b_certificate_version`). Any change by the external
reviewer to a protected decision voids prior certificates and the assembled-path
exercise; the skeleton rebinds rather than being patched in place.

## The proposed archetype set

Twelve derived from the nineteen findings, four added by review to cover
project-level failure classes the twelve missed.

| # | Question archetype | Instance that produced it |
|---|---|---|
| 1 | Is the declared conditioning history actually held fixed? | a suffix-noise slice varied positions before the intervention index |
| 2 | Does the null estimate the same statistic the gate applies to? | a pairwise contrast null gating a K-action centered energy |
| 3 | Can FAIL be distinguished from UNRESOLVED? Where is the upper bound? | binary `passed = lcb > threshold`, no upper confidence bound |
| 4 | In which space is the comparison made, and is it the claim's space? | an action-space cosine standing in for residual-parameter alignment |
| 5 | Does the gate's validity window cover the run's duration? | one anchor qualification licensing 100 and 300 update blocks |
| 6 | Trace the code path emitting each registered branch — which is unreachable? | a phase-entry guard raising instead of emitting its registered branch |
| 7 | Is every quantity the contract calls registered actually registered? | a suffix replicate count called registered and registered nowhere |
| 8 | Is the measure frozen, or only the support? | active support frozen, history weighting left free |
| 9 | What supplies each contract symbol in code — is the equivalence stated? | a membership-state symbol supplied as a subset, equivalence undocumented |
| 10 | Is each threshold reachable given the estimator's own noise? | `1e-8` tolerance against ~`1e-3` sampling noise |
| 11 | Are the clustering units actually independent? | eight bootstrap clusters sharing three ledgers |
| 12 | What data does each gate see, and was that split registered? | one alignment statistic on four clusters, another on all eight |
| 13 | Can the mechanism leave its mandated initial state at all? | an exact-zero residual credited by ablating itself to zero — gradient identically zero |
| 14 | Is the information available at decision time, and does anything leak? | next state, future reward, ledger identity, slot shortcuts |
| 15 | Do comparators match on information, action support and optimization exposure? | extra optimizer steps or centralized information producing a false positive |
| 16 | Is intervention evidence being read as a natural-policy claim? | a forced-branch result transported to held-out natural execution |

Archetype 13 is included because a reachability question about thresholds does
not cover whether the learning dynamics have an absorbing state — the defect that
opened this entire line.

## Per-item output shape proposed

```text
Observed repository fact        (with the command or path establishing it)
Why it may change a registered quantity or branch
Question requiring external authority
Conditional follow-ups          (branches pre-walked)
Affected symbols / branches
```

## No completeness claims, in either direction

"Enumerate every decision" is not provable against real code. The adversarial
reader emits a **coverage matrix** and may claim only *"within the listed scope,
nothing further found"*. Matrix rows: conditioning history; support and measure;
estimator and null; confidence semantics; cluster independence; data roles;
parameter versus action space; policy-snapshot validity; initialization and
gradient reachability; branch reachability; comparator equivalence; leakage;
natural-policy transport.

## Decision ledger, per contract

| Field | Content |
|---|---|
| Decision ID | stable identifier |
| Protected object | estimand, threshold, branch, data split, policy snapshot |
| Alternatives | what was considered |
| External ruling | accepted / modified / rejected / open |
| Smallest consequence | what reversing it changes |
| Evidence paths | contract, code, source, counterexample |
| Implementation binding | concrete symbol or function |
| Re-review trigger | what change reopens it |

A standing task for the adversarial reader: find protected choices in contract or
code with **no ledger entry**.

## Validation plan for the mechanism itself

Three tiers, with all labels, scoring rules and acceptance thresholds frozen and
hash-bound **before the first run** — not before reading results, since wall time,
failure state and partial output leak result characteristics.

- **V1 — known-case regression** on the G20R2 contract at its pre-ruling commit,
  reported in three layers (*directly encoded* / *same archetype, unencoded
  instance* / *true holdout*) and split by which reader originally found each item.
- **V2 — historical out-of-distribution holdout** on older contracts not used to
  derive the archetypes. This is the minimum evidence that principles transfer
  rather than cases being recalled.
- **V3 — negative and metamorphic control**: a reviewed contract with no known
  defect, and preferably a metamorphic pair where a repaired snapshot differs
  from a defective one only in that defect.

Metrics frozen alongside: critical recall, holdout recall, precision, reviewer
burden, evidence-grounded rate, duplicate rate, authority-violation rate, novelty.

The mechanism stays `EXPERIMENTAL_WORKFLOW_GATE` until V2 passes. V1 proves
wiring; only V2 shows transfer.
