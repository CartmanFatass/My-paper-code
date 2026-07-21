# External Review Pipeline

Standing form for external review as of 2026-07-21. This replaces the Codex
`rounds/` dispatch machinery for work owned by this session. The reviewer is
GPT-5.6 Pro, reached by the user directly through the GitHub connector.

## Boundary

```text
docs/external-review/gpt5_6_pro/<YYYYMMDD>_<topic>/
  QUESTION.md        the dispatched question, verbatim as sent
  RESPONSE_RAW.md    the reply, archived verbatim, never edited or summarized
  DISPOSITION.md     what was adopted, rejected or deferred, and why
```

A code review adds `REVIEW_ENTRY.md` (repo, branch, pinned commit, read order),
`CODE_MAP.md` (anchored locations plus a confidence declaration), and
`PACKAGE_MANIFEST.md`. `RESEARCH_BACKGROUND.md` is added when the reviewer needs
scientific framing to make the question well-posed.

Markdown under this tree is tracked through the `.gitignore` negation
`!docs/external-review/gpt5_6_pro/**/*.md`. Without it the bare `*.md` rule
silently refuses the whole package.

## Rules

1. **Push before dispatch.** The question pins a commit; that commit must be
   reachable from `My-paper-code/aggressive` or the reviewer reads nothing.
   Verify with `git ls-remote` rather than assuming.
2. **Pin a commit, not a branch.** The working tree moves during
   implementation. A pinned commit gives the reviewer a stable boundary.
3. **Route to code, not to prose.** Give exact paths and function anchors and
   instruct the reviewer to verify claims against the source. Summaries carry
   the author's errors into the review; a claim stated in the question has
   already been checked once by someone with an interest in it being true.
4. **Declare confidence.** Name which paths were verified by reading and which
   only by passing tests, and point the reviewer at the latter first.
5. **State the frozen inputs.** Adopted route, seeds, thresholds, budgets and
   deliberately deleted legacy code are inputs, not review surface. Say so, or
   the reviewer spends its effort re-litigating settled decisions.
6. **Archive the raw verbatim.** A naturally completed response is valid
   evidence even when its content has gaps. Transmission artifacts such as
   mangled LaTeX are preserved as received and noted, not repaired.
7. **Separate transport from adoption.** Receiving a response changes nothing.
   Scientific adoption is the user's, recorded in `DISPOSITION.md` and, when it
   changes the contract, in `IMPLEMENTATION_PLAN.md` at its own commit.
8. **Correct the record when the reviewer corrects us.** If the question
   contained an error, append the correction to `QUESTION.md` rather than
   editing the claim away.
9. **No threshold change after a result is observed.** A pre-registration
   repair before any run is legitimate; the same edit afterwards is a rescue.

## Question shape

State the pinned commit and the diff boundary. State what is frozen. Ask for
one decision, not a survey. Give the required response sections. For an
implementation audit, demand a single verdict token and an enumerated minimal
correction list, and say explicitly that style and refactoring are out of
scope.

Treat measured evidence in the question as claims to falsify, and say so.
