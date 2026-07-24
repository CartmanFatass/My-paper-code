# External Review Pipeline

How to decide what goes outward and how to write the question. **Transport
mechanics and the round layout are not here** — they are in
`.claude/skills/hmasd-review-round/SKILL.md` and
`docs/external-review/README.md`, which are authoritative. This file would
otherwise become a second, drifting copy of them.

## What external review is for

External Pro is the **scientific** authority. It adjudicates estimands, causal
claims, comparator design, result contracts, portfolio weighting and route
selection, and under the recorded authority split it owns the scientific
decision itself.

Its GitHub connector access exists so those judgments are informed by what the
code actually does. It is a context channel, not a request to audit the
implementation.

## The dividing question

Does the answer change **what should be measured or claimed** — external — or
**whether the code does what the plan says** — internal?

Code correctness is internal. The orchestrator writes the plan and freezes the
evidence contract; `hmasd-verifier` produces runtime evidence and
`hmasd-reviewer` audits the diff against the plan before any commit touching
protected semantics.

Do not send an implementation audit outward. It spends the scientific
reviewer's attention on work owned here, and it is slower than the internal
pass — the internal review has already caught latent defects in a
formally-authorized-only path that the full acceptance suite never reached.

A question may legitimately reference implementation detail. "Does your estimand
require both branches to consume one shared RNG stream" is scientific even
though the answer determines code, because the decision being asked for is
scientific.

## Writing the question

1. **Route to code, not to prose.** Give exact paths and function anchors and
   instruct the reviewer to verify against source. A summary carries its
   author's errors into the review; a claim stated in the question has already
   been checked once by someone with an interest in it being true.
2. **Mark provenance.** Repository fact, external evidence and orchestrator
   inference are three different things and must be labelled as such. An
   unmarked inference reads as an established result and gets inherited as one.
3. **Declare confidence.** Name which paths were verified by reading and which
   only by passing tests, and point the reviewer at the latter first.
4. **State the frozen inputs.** Adopted route, seeds, thresholds, budgets and
   deliberately deleted legacy code are inputs, not review surface. Say so, or
   the reviewer re-litigates settled decisions.
5. **Ask for one decision, not a survey**, and give the required response
   sections.
6. **Treat measured evidence in the question as claims to falsify**, and say so.
7. **Do not defend the framing.** Say explicitly that discarding the question's
   structure is a legitimate answer.

## Rules that survive the round

- **Archive the raw verbatim.** A naturally completed response is valid
  evidence even when its content has gaps. Transmission artifacts such as
  mangled LaTeX are preserved as received and noted, never repaired.
- **Correct the record when the reviewer corrects us.** If the question
  contained an error, append the correction rather than editing the claim away.
- **No threshold change after a result is observed.** A pre-registration repair
  before any run is legitimate; the same edit afterwards is a rescue.
- **Receiving a response changes nothing by itself.** The scientific decision is
  External Pro's and the code-side consequence is the orchestrator's, recorded
  in the round's reconciliation and, when it changes the contract, in
  `IMPLEMENTATION_PLAN.md` at its own commit.
