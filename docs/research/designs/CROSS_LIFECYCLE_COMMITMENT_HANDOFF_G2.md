# CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2

Status: bounded information gate passed and Project Manager accepted; no formal
G2 contract is frozen yet.

## Provenance and correction

The exact `ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1` source is closed as
`ORDINARY_EXPLANATION_G1` at source commit
`de9a315b4969ee6920be08a3d911d559fe362f03`. Its evidence is recorded in
`docs/research/cdc/EVIDENCE_NOTES/20260723_ACCESS_POSITIVE_EHC_G1_FORMAL_RESULT.md`.
G1 is not imported, renamed, retuned or rerun here.

G1 retained a cue and acted on it within one member lifecycle. A per-member GRU
therefore supplied the whole useful memory. G2 asks a smaller structural
question: can a task-relevant bit remain available after the observing member
has terminally left and the acting successor begins with fresh member state?

## Claim boundary

G2 does not claim that event-held state is more expressive than every recurrent
network. A team-level recurrent state can emulate any finite event-held object.
The bounded gate must expose that simpler explanation rather than hiding it.

The gate distinguishes three facts:

1. fresh per-member recurrence cannot carry creator-only information across a
   terminal lifecycle handoff;
2. both a persistent team recurrence and an event-held team commitment can carry
   it constructively; and
3. changing the held commitment after the creator leaves changes the successor
   sequence and external utility.

Only a later trainable comparison may ask whether event-conditioned holding has
a learning or held-out robustness advantage over matched team recurrence. The
future strongest comparator is team recurrence, not the already-refuted
per-member G1 comparator.

## Minimal anonymous handoff source

Each exhaustive case contains a creator, a neutral survivor and a successor.
Physical slots are packing coordinates only and are never actor identity.

- A fair bit `b in {-1,+1}` is visible only to the creator at CREATE.
- The creator and survivor begin active.
- The creator terminally leaves after one or two active steps.
- For one gap step only the survivor remains active.
- An anonymous successor then joins with exact zero member-recurrent state and
  acts for two or four steps.
- The successor observation trace, membership history, physical packing and
  lifetime are independent of `b`; the survivor never observes `b` and has no
  communication action.
- Creator slot, successor slot, survivor slot, same-slot reuse, cross-slot
  transfer, creator lifetime and successor lifetime are exhaustively balanced.
- External utility is successor action accuracy for `b`. There is no intrinsic
  reward, shaping, learning or optimizer.

The commitment object is team/event scoped, not agent or physical-slot scoped.
CREATE stores the mark; terminal creator departure does not delete it; JOIN
exposes the same held object to the successor mechanism. This is the one new
algorithmic state-ownership proposal. It is generic to lifecycle events and does
not read task reward, named roles or persistent identities.

## Bounded policies and reduction

- `PER_MEMBER_REC`: the creator may store `b`, but terminal LEAVE destroys that
  state and successor JOIN starts at zero. Its best balanced successor utility
  is exactly `0.5`.
- `DUM`: receives the same CREATE/mark/handoff records but the held mark has no
  primitive-logit path. Its balanced utility is exactly `0.5`.
- `TEAM_REC`: a team recurrent state observes CREATE and survives membership
  churn. A constructive oracle attains utility `1.0`.
- `EHC`: the event-held mark survives the handoff and enters the primitive path
  through `base_logits + W_z(m*z)`. A constructive oracle attains utility `1.0`.
- `RANDOM_MARK`: an outcome-independent held mark attains utility `0.5`.

For every successor-visible trace `x`, the exhaustive case set contains one
`b=-1` and one `b=+1` case. Hence
`P(b=-1|x)=P(b=+1|x)=1/2`, and any policy whose only state is freshly initialized
successor recurrence has maximum expected accuracy `1/2`. This is the gate's
information proof; it is not an empirical threshold.

## Intervention

Snapshot immediately after terminal creator departure. Under common future
membership and action timing, replace only the held mark `z=b` with `z=-b`.
The EHC oracle must change every successor action, moving natural utility from
`1.0` to `0.0`. Team recurrence is retained as a simpler natural-capability
explanation and is not modified by this mark-only intervention.

## Exact bounded result

The nonformal runner always writes `formal=false` and one of:

1. `INVALID_HANDOFF_INFORMATION_GATE_G2` if schema, case balance, anonymity,
   lifecycle reset, state ownership or finite/exact metric invariants fail;
2. `PASS_HANDOFF_INFORMATION_GATE_G2` only when the per-member Bayes bound,
   PER_MEMBER_REC, DUM and RANDOM_MARK utilities equal `0.5`; TEAM_REC and EHC
   equal `1.0`; and the EHC mark-flip action-change and utility-drop equal `1.0`;
3. `FAIL_HANDOFF_INFORMATION_GATE_G2` for any other valid measurement.

This gate is deterministic, zero-training, nonformal and consumes zero
conclusion-bearing iterations. A pass establishes only an executable handoff
and comparator boundary. It does not support EHC adoption or authorize formal
iteration 3.

## Successor boundary

After a pass, freeze a separate trainable G2 evidence contract with:

- TEAM_REC as the strongest primary comparator;
- DUM as the link-null control and EHC as the treatment;
- primary `G_team = U_EHC - U_TEAM_REC` and secondary
  `G_link = U_EHC - U_DUM`;
- access before mechanism interpretation;
- event-held intervention, natural mediation and held-out churn/gap robustness;
- exact budgets, seeds, thresholds and first-match branches chosen before any
  conclusion-bearing run.

Until that later contract is frozen, formal compute is not launchable. Three
conclusion-bearing iterations remain.
