# Proposal: a Pro-first research loop

```text
status=RETIRED
retired=2026-07-25
retired_by=user
superseded_by=docs/project/WORKFLOW_SIMPLIFICATION.md
```

**Retired without ever being adopted.** The user replaced it with a two-point
model: review the scientific idea, and confirm implementation detail choices with
External Pro before building. Nothing else.

What survives from this document is its one correct observation — that external
review is the scarce resource and the loop should be arranged around it. What is
retired is the apparatus it proposed for that: three gates, certificates,
validation tiers. Those measured the mechanism rather than the science.

Kept as a record of what was tried, so it is not re-proposed. Read
`WORKFLOW_SIMPLIFICATION.md` instead.

---

*Original proposal follows.*

On acceptance this **replaces** that section rather than joining it. Two
descriptions of one loop is the failure this project has already paid for.

## What changes, in one sentence

Today's step 3 reads "**if** external science is needed" — Pro as an occasional
escalation. Pro is instead the resource the loop is built around, consulted on
demand and at three distinct points, because domain judgement is what this
project is short of and implementation capacity is not.

## The evidence for that claim

All six defects in the G20R2 contract were scientific and every one was mine:
the zero fixed point, identification confused with effect size, a resolution
floor that turned out policy-dependent, a null degenerate under common random
numbers, structural zeros from reward saturation, and an expectation taken off
its own support. Meanwhile both arms of the tier test wrote clean, well-tested
code, and raising the implementer to a frontier model improved defect *detection*
without improving *stopping*.

The code is long but shallow, except in a few short places where it is very deep.

## Three grills, not one

We have only ever used the third. Each asks a different kind of question and each
fires at a different point.

| Grill | Fires | Asks | Failure it prevents |
|---|---|---|---|
| **Contract** | before a design is frozen | does this measure what it claims? | building a faithful implementation of a broken design |
| **Technique** | before a numerical method is trusted | is this the right realization of the method? | a subtly wrong estimator that passes every test |
| **Result** | after evidence exists | what does this number license? | over- or under-claiming from a valid measurement |

The **technique** grill is new and is the one this project most conspicuously
lacks. `paired_replay_return` realizes common random numbers by algebraically
solving for the noise that reproduces a probe action under a tanh-squashed
Gaussian with prefix-dependent routing. The contract says only "paired replay
with common random numbers". If that realization is subtly wrong, every
identification number is wrong, every test still passes, and a contract grill
cannot see it. Pro can answer whether the method is right; I cannot.

Note what this does *not* cover: whether the code implements the method Pro
blessed. That is caught only by an audit that executes and measures, which is why
`hmasd-reviewer` holds a real interpreter. **Grilling protects the science;
measurement protects the realization.** Neither substitutes for the other.

## When to fire one — a predicate, not a judgement of importance

Fire a grill when **both** hold:

1. reversing the choice would change a registered quantity, a gate outcome, or a
   result branch; **and**
2. I cannot settle it from the code, the frozen contract, or a derivation.

If only (1) holds it is mine to decide and record. If only (2) holds it is a free
engineering choice and picking one is enough. Neither is a reason to spend a
round.

Everything else — layout, factoring, naming, test construction, seeds that no
result depends on — stays with Project Manager and is never sent.

## Pro is a serial resource, and the loop is arranged around that

One conversation, one question at a time, 15-18 minutes of reasoning per turn
plus fragile browser transport. Rounds cannot be parallelized. Three
consequences, all mechanical:

- **Batch into one turn, as a conditional tree.** Branches pre-walked, so one
  reply traverses dependencies an iterative interview would have taken many turns
  to find.
- **Never idle during a Pro turn.** While Pro reasons, build the parts that do
  not depend on the ruling, run the audits, verify the harness. A blocked loop
  during a 15-minute think is 15 minutes thrown away.
- **Never curtail.** Pro is authoritative after full reasoning and not before —
  the curtailed round produced two load-bearing conclusions Pro itself retracted.

## The cycle

1. **User** sets the goal and the protected/formal authority.
2. **Project Manager** selects the smallest bounded action.
3. **Contract.** Where the action needs a frozen design, write it, then run the
   pre-freeze check and author the contract grill. Run the **grill-the-grill**
   pass — which decision here is being made without being asked about — before
   sending. Send, and while Pro reasons, do work that does not depend on the
   ruling.
4. **Reconcile** the archived reply code-side. Where a code choice is entailed by
   a scientific decision, Pro governs and Project Manager implements.
5. **Build** through bounded registered children. Children leave work in the tree
   and run no Git. Tests are instrument calibration, not behaviour specification:
   a test earns its place if failing it would mean the produced number is wrong.
6. **Technique grill** where the package realizes a numerical method whose
   correctness is a domain question rather than a coding one.
7. **Audit.** `hmasd-reviewer`, two verdicts never merged — conformance and
   protected semantics — with claims measured rather than read.
8. **Exercise the path before trusting it.** No conclusion-bearing run is
   launched on a code path that has never executed end to end. A trivial-scale
   smoke that writes nothing under `logs/` comes first.
9. **Freeze** the evidence contract, confirm it is inside current user authority,
   and spawn one `hmasd-experiment-operator` with the complete immutable
   assignment.
10. **Result grill** where the reading is a scientific judgement rather than a
    branch lookup.
11. **Record** the smallest supported CDC update, then `docs/report/ITERATION_<n>.md`
    in Chinese. The report is mandatory but is not review, approval, or evidence.
12. **Integrate** Git and select the next in-authority action.

Steps 3, 6 and 10 are the same mechanism pointed at different objects. Any of
them may fire more than once, or not at all, per the predicate above.

No child launches a successor. Automatic continuation belongs only to Project
Manager, and its re-entry is driven by `/loop`.

## Failure modes this must not become

| Risk | What stops it |
|---|---|
| grilling everything until the loop is Pro-latency-bound | the two-part predicate; batching; working during Pro's turn |
| deferring decisions that are mine, to avoid owning them | the authority boundary — layout, factoring, naming, tests are never sent |
| the grill-the-grill pass becoming ceremony | it must return findings or state plainly that it found none; a pass that always approves is a gate that cannot fail |
| a second loop description drifting from this one | this replaces the `AGENTS.md` section outright |

## What this does not fix

Question authoring becomes the bottleneck, and it moves there silently. Pro rules
only on what is put in front of it, so an unasked question fails exactly as an
unexecuted rule does. The grill-the-grill pass is a mitigation, not a solution —
it is one adversarial reader, subject to the same blind spots as any single pass.
This should be watched rather than assumed solved.
