# Working Principles

Seven principles, kept deliberately short. They are epistemic rather than
technical: each one is about how a claim earns belief, not about what to build.

Concrete instances and measurements live in
`docs/project/EFFICIENCY_PRACTICES.md`. Scientific constraints live in
`docs/project/ALGORITHM_PRINCIPLES.md`. This file is the brief.

---

**1. Confidence is not evidence.**

Everyone in the loop asserts confidently and is wrong at a similar rate — the
controller, the external reviewer, the implementation reviewer, the implementer.
Being careful does not fix this. Making verification cheap and routine does. No
unverified number enters a decision.

**2. A guard that cannot fail is worse than no guard.**

An unfalsifiable protection converts an unknown risk into a false belief, and
false belief survives every later audit. Before trusting a guard, state what it
would catch; if nothing, delete it or fix it. Verify the load-bearing ones by
deliberately breaking the thing they protect.

**3. Every default and constant is an expired decision.**

Someone chose it once, under conditions that may no longer hold, and often
without measuring. Ask what it was calibrated against and whether that still
applies. A hard-coded refusal is not evidence that the alternative was
considered.

**4. Decompose along what can be independently verified.**

Not along what feels like one feature. Correctness and performance are separate
deliverables even when they touch the same code; entangling them produces work
that cannot be reviewed, and sometimes cannot be finished.

**5. Before registering a threshold, compute what a random policy scores.**

If an untrained or degenerate policy passes, the threshold is not a gate — it is
a formality that will later be mistaken for evidence. This is principle 2
applied to science instead of code.

**6. Distinguish a measurement artifact from a finding.**

Before concluding that a quantity is structurally zero, unreachable, or
impossible, confirm the apparatus could have expressed the opposite. An
instrument that cannot register the effect is not evidence of its absence.

**7. A repeatedly marginal bound is wrong.**

When the same quantity keeps landing near a threshold under unrelated
conditions, the threshold is misspecified rather than the measurement unlucky.
Bound the factors, not the derived sum that accumulates their error.

---

## Corollary for review

Review earns its cost through a shared falsifiable artifact, not through
authority. Route a reviewer to the code and the exact anchors, tell it which
claims are unverified, and invite it to falsify them. A reviewer handed a
summary can only inherit the author's errors — which is how three of our wrong
claims survived until someone read the source.

The same holds in reverse: a reviewer's finding is a claim, not a verdict. One
of ours was refuted in five seconds by mutation testing.
