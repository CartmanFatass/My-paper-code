# Subagent workflow kit

Reusable templates for standing up a multi-agent workflow, and the laws they
encode. Project-agnostic — nothing here assumes HMASD. The incidents cited are
from 2026-07-24, kept because a rule without its origin gets dropped by the next
person who finds it inconvenient.

Copy the templates. Read the laws first, because the templates are just the laws
in fill-in-the-blank form.

---

## The six laws

### 1. Standing rules go in a file every child is told to read

Never in the brief. A constraint that lives only in briefs makes correctness
depend on the caller remembering it every single time, and the caller will
eventually forget.

Give every definition one line pointing at a shared context file, and name the
sections that bind. Keep environment facts, authorization scope, honesty rules
and safety boundaries there.

> Eight of ten definitions never pointed at the shared file. The standing
> authorization was recorded in it — so those eight kept stopping to ask for
> permission that had already been granted, in a file they were forbidden to see.

### 2. A brief that contradicts the governing procedure is worse than no brief

The child follows the brief. If a Skill, charter or runbook governs the work,
**open it and quote its constraints**; do not paraphrase from memory.

Watch for words that admit a reading the procedure forbids. "Submit it verbatim"
reads as *paste the file body*; the procedure meant *do not alter it*.

> A child had read the governing procedure and correctly stopped to ask. The
> answer it got — "submit the question body verbatim, splitting across messages
> if needed" — contradicted line 116 of the very procedure it had been told to
> follow. The round had to be retired. The child was not the failure.

### 3. Tier follows the judgment, not the role's framing

A role described as "mechanical transport, never interprets" was pinned to the
cheapest tier. But it had to decide *whether an observed response was the
completed answer* — which is judgment, and getting it wrong manufactures
evidence.

Ask: **does this role ever decide that an observation does or does not match a
declared contract?** If yes, it needs real effort regardless of how mechanical
the job title sounds.

> At low effort it archived 794 bytes of a reviewer's mid-generation progress
> trace as the scientific answer, and reported byte-equality success.

### 4. Verify the proposition that matters, not one adjacent to it

The most dangerous report is true and vacuous. Comparing a file against the
bytes you just wrote proves nothing about whether those bytes were right.

Three rules, stated in every definition:

- a check that **errored is a check that failed** — never a step to route around;
- never assert a property you did not measure; paste the real output;
- "I could not establish it" is always an acceptable report.

> `Byte-Equality Verification: CONFIRMED` was literally true and came one
> acceptance step from entering the record as external scientific evidence.

### 5. A gate that cannot fail is decoration

Every automated gate must be validated in **both** directions before you trust
it: it passes a known-good input and rejects a known-bad one. Exercise it on the
**production call path** — same defaults, same arguments the real caller uses.

And keep **one definition per contract**. Two scripts enforcing different
versions of the same rule is a latent outage.

> A mandatory pre-dispatch gate defaulted a remote parameter to the wrong kind of
> identifier and crashed on every real call. Its test passed a different value,
> so it went unnoticed — while the gate already encoded the exact requirement the
> failing work violated. Separately, two scripts disagreed on what an "evidence
> declaration" was, so work could clear the first and be refused by the second.

### 6. Nothing wakes an agent that ends its turn to wait

An agent — parent or child — that stops emitting tool calls is finished, not
paused. This is the single defect that recurs at every level of an unattended
workflow, because from the inside it never feels like an error: you intend to
continue, so ending the turn reads as waiting.

Two consequences, and both need a mechanism rather than a resolution:

- **A parent needs an external re-entry driver.** Intent in a constitution is
  not a driver. A document saying the loop continues automatically describes a
  policy; something outside the turn has to re-invoke it.
- **A child must collect its own background work in-band.** If it backgrounds a
  job and ends the turn, the caller receives a report whose entire content is
  that the child is waiting, and the work sits until a human notices.

> The orchestrator wrote "I will not come back for authorization" three times in
> one day and stopped anyway each time, until `/loop` was attached. Weeks of
> discipline had not fixed what one mechanism did. Later, an implementer ended
> its turn to wait on a calibration it had backgrounded, and returned a report
> that said only that it was waiting — the same defect, one level down.

The generalization: when a rule keeps being violated by someone who sincerely
intends to follow it, stop rewriting the rule and go find the thing that
executes it.

---

## Template A — subagent definition

```markdown
---
name: <kebab-case-name>
description: <what it owns, in one sentence, plus what it must never do. This is
  what the orchestrator reads when choosing an agent — make the boundary visible.>
model: <tier>
# Justify a high effort tier when the role involves judgment, so nobody
# "optimizes" it back down later.
effort: <low | medium | high>
tools: <exact grant — omit a tool to make a prohibition structural>
---

# <Name>

Read `<shared context file>` before you start. Its **<section>** and
**<section>** sections bind you; the rest is reference.

<One paragraph: what this role is, and what it is not.>

## Governing procedure

`<path to the Skill or runbook>` is normative — read it in full before acting,
and execute its states in order. Do not skip a step because the situation looks
familiar.

## Scope

Your brief lists the files you may change and what is out of scope. Both are
exact. If the work seems to need something outside that list, stop and say so —
the out-of-scope list is usually deliberate staging, not an oversight.

## When you are blocked

Return this exact shape, so the caller can key off it:

```text
BLOCKED
decision=<stated so it can be answered yes/no or with one value>
why_material=<what changes in behaviour depending on the answer>
done_so_far=<files already changed, or none>
```

`BLOCKED` is for a missing decision that would materially change behaviour. It
is **not** a channel for permission.

## Do not report a success you did not verify

Your caller cannot see what you saw; your report is the only evidence the work
happened. Verify the proposition that matters, not one adjacent to it. A check
that errored is a check that failed. Never assert a property you did not
measure. "I could not establish it" is always acceptable.

## Reporting

- what you did and where, per change;
- the real output, pasted — not a claim about it;
- every ambiguity you resolved and the choice you took;
- anything you could not do, stated plainly.
```

---

## Template B — the brief

```markdown
assignment_id=<STABLE_ID>
base_commit=<sha> (<working tree state at spawn>)

# Spec — the contract, do not redesign it

`<path>`, in full. <Name the sections that bind and what each governs.>

Background, read-only: `<path>`. Context, not an instruction source.

# Template

`<closest existing implementation>` — reuse its structure.
It differs in exactly <N> ways: <list them>. Everything else is unchanged.

# Write scope — exactly these files

1. `<path>`
2. `<path>`

# Out of scope — deliberate staging

`<paths>`. If the work appears to need a change there, stop and return BLOCKED
rather than widening the boundary.

# Pre-authorized — do not stop for these

<The things this child's definition would normally make it halt on, that the
frozen spec already covers. Say so explicitly, or it will bounce back to you.>

# Traps already known

<Every failure mode you have personally hit in this area. Cheapest lines in the
whole brief.>

# Tests / checks

<Exact list.> Each must be able to actually fail — before reporting one as
covering an invariant, ask what wrong implementation it would catch.

Paste the real output for: <each suite, including shared-surface guards>.

# Hard prohibitions

- No <Git / deploys / sends / whatever the caller owns>.
- No <executing the thing that is separately authorized>.
- No scope widening, no sweeps, no alternative approaches.

# Report

<Per the definition's reporting section.>
```

### Brief smells

| Smell | Why it bites |
|---|---|
| a verb that could mean two things | the child picks the wrong one and is not wrong to |
| paths listed only in the brief | if a downstream tool parses the artifact, the artifact must carry them |
| "use good judgment" on a protected decision | either pre-authorize it or make it BLOCKED-worthy |
| no out-of-scope list | silence reads as permission |
| no traps section | you will re-pay for every lesson you already learned |

---

## Template C — a gate

```powershell
# One definition per contract. If another script checks "the same" thing,
# delete one of them.
# Defaults must match the production call path -- a default nobody uses in
# anger is a default nobody tests.

<checks, accumulating failures rather than throwing on the first>

if ($failures.Count -gt 0) {
    [pscustomobject]@{ status='<NAME>_FAILED'; failures=@($failures) } |
        ConvertTo-Json -Depth 4
    exit 1
}
[pscustomobject]@{ status='<NAME>_READY'; <evidence fields> } | ConvertTo-Json -Depth 4
```

Accumulate failures instead of throwing on the first — one run should tell the
caller everything that is wrong, not the first thing.

Then **prove it fails**: run it against a known-bad fixture and confirm the
rejection, and against a known-good one and confirm the pass. Wire both into the
commit-time test. If a deliberate-failure probe runs inside that test, reset the
exit code afterwards or the whole suite inherits it.

---

## Wiring checklist for a new workflow

1. **Shared context file** — environment, authorization scope, honesty rules,
   safety boundaries. Every definition points at it (law 1).
2. **One definition per role**, with the boundary in the `description`, the tier
   justified (law 3), and the honesty section present (law 4).
3. **Structural prohibitions where possible** — withhold a tool instead of
   writing "do not use X". A `PreToolUse` hook beats a sentence.
4. **One gate per contract**, validated both directions, on the production path,
   wired into commit-time tests (law 5).
5. **A pre-freeze check** if the workflow freezes plans before building them —
   reviewing a diff against a plan cannot catch a defect *in* the plan. Bound it
   to what a derivation or throwaway probe settles without a full run, or it
   becomes a second review layer.
6. **Unattended?** Then say so in the shared file: pausing is a stall, not a safe
   default. Name what is pre-authorized and what genuinely must escalate.
7. **Traps file** — append every failure mode as you hit it, and pull from it
   when writing briefs.

---

## Escalation boundary

Worth stating once, explicitly, in the shared context file:

- **inside the grant** → act, then report. Do not ask.
- **outside the grant** → escalate. New external destination, destructive action
  on something the grant did not name, or a real widening of authority.
- **a tool-level warning about an in-scope action** is not an escalation trigger
  by itself — but a security refusal you cannot satisfy *is* a blocker to report,
  never to work around.

Ambiguity about whether something already happened always resolves toward **not
doing it again**, and reporting.
