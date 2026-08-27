---
name: code-review
description: "Use only when a top-level HMASD CM or Root must review a bounded code diff since a fixed point along two independent axes: repository Standards and the accepted Spec."
---

# HMASD Two-Axis Code Review

Only a top-level HMASD CM or Root may invoke this skill. Never use this skill
for EM scientific review, and never invoke it from a leaf. EM review belongs to
Research Critic and Agentify external review, not code-diff review.

Review the diff between `HEAD` and one fixed point along two axes:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

The top-level caller spawns exactly two direct `hmasd-reviewer` leaves in
parallel: one Standards axis and one Spec axis. Use the registered
`hmasd-reviewer` role for both. Suggested task names are `std_sx_<task>` and
`spec_sx_<task>`. These are evidence leaves, not approval gates. They return
only to the spawning CM or Root.

## Process

### 1. Pin the fixed point

Use the assignment's frozen base when present. Otherwise use the fixed point
explicitly supplied by the user or caller. If neither exists, resolve the
merge-base of the current candidate and its recorded integration branch; stop
only if that identity is materially ambiguous.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two parallel sub-agents.

### 2. Identify the spec source

Look for the accepted spec, in this order:

1. Exact authority/spec refs in the CM assignment.
2. A path explicitly supplied by the user or caller.
3. The matching direction authority or tracked project spec named by the
   assignment.
4. If no spec exists, the Spec leaf reports `NO_SPEC_AVAILABLE`; it does not
   invent requirements or fetch an unrelated issue tracker.

### 3. Identify the standards sources

Start with the applicable `AGENTS.md`, then any bounded repository standards
named by it, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`. Do not turn
historical design notes into current standards.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn the two direct reviewer leaves in parallel

Each leaf prompt must say: "Perform the assigned axis directly. Never invoke
`code-review`; never spawn or delegate another agent; return only to the
spawning CM or Root." Do not ask either leaf to coordinate, rerank the other
axis, contact another top-level task, or perform Git actions.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, the Spec leaf returns only `NO_SPEC_AVAILABLE` plus the
exact sources it checked.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
