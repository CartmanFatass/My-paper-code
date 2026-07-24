# Review brief: the G20 credit rule is inert, and its repair is yours to authorize

```text
round=20260724_g20_credit_rule_zero_fixed_point
branch=untied-k
repository=CartmanFatass/My-paper-code
semantic_author=project_manager
scientific_authority=external_pro
code_design_authority=project_manager_orchestrator
round_kind=focused_protected_semantics_repair
predecessor_round=20260724_untied_k_direction_bootstrap
```

## Continuity note

The orchestrator conversation that carried the bootstrap round has been
succeeded; the role, authority split and branch registration are unchanged. Read
`code_design_authority=project_manager_orchestrator` as the same seat the
previous round called `fable_orchestrator`.

## Why this round exists

The P2 candidate you made eligible was designed, frozen, and built. The
implementation is faithful and its focused suite passes. Before the bounded
screen was authorized, the implementation lap surfaced — and the orchestrator
then established by derivation and numerically — that the frozen credit rule has
an **exact fixed point at zero**. It cannot move the residual it is supposed to
train, under any `Q_slow`, any seed, or any budget.

The screen was therefore **withheld rather than run**. Had it run it would have
reported `NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20` deterministically,
which under your pre-registered mapping would have read as evidence against
member-resolved delayed credit while in fact testing nothing about it. That is
the failure mode the result-interpretation table exists to prevent, so the run
was stopped rather than reported.

No compute was spent and no iteration consumed.

## What this round is, and is not

This is **not** a request to re-litigate P2, the centering result, or your
pre-registered outcome mapping. None of them were tested and none are
challenged. The centering half of the design is proven exact by the focused
suite and is untouched by the finding.

It is a request for one scientific authorization and two scoping judgments,
because what has to change to make the candidate testable is **credit** — a
protected semantic. Under the split now in force you decide **whether** the
credit quantity changes and to what; the orchestrator decides **how** it is
built. The orchestrator has a concrete repair to propose and is explicitly not
adopting it unilaterally.

## Boundary of this round

You are asked for a scientific decision on the credit quantity and the scope of
its consequences. You are not asked for:

- an implementation plan, file list, or function signature;
- authorization for any nonformal or formal compute;
- a re-derivation of the timing–credit identifiability result, which stands.

A legitimate answer includes rejecting the proposed repair, naming a different
credit quantity, or ruling that the anchor-preserving construction should be
abandoned rather than repaired.

## What the orchestrator has already decided, code-side

Stated so you are not asked to ratify engineering:

- the built package is accepted as faithful to the frozen design and is
  committed at `stage_commit`;
- the bounded screen is withheld until the credit rule is decided;
- the defect is pinned by an explicitly commented test so that any future change
  to it is visible in the diff either way.
