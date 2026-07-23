# ASYNC_COMMITMENT_ROSTER_G3

Status: information gate passed; exact structural source retained as nonformal;
no trainable or formal contract exists.

## Provenance and independence

Formal G2 is permanently closed as `TEAM_REC_SUFFICIENT_HANDOFF_G2` at source
commit `9a72dc6a0f776aa3e6dfa96d86f5265f12717ace`. Its result is recorded in
`docs/research/cdc/EVIDENCE_NOTES/20260723_CROSS_LIFECYCLE_HANDOFF_G2_FORMAL_RESULT.md`.
G3 does not rename, retune or rerun G2.

G2 used one global bit and was exactly reducible to persistent team recurrence.
G3 changes the scientific object: a variable-cardinality unordered roster of
lifecycle-owned commitments is edited asynchronously, and external utility
depends on complementarity among retained and newly selected commitments.

## Bounded source gate

The gate is deterministic, exhaustive, zero-training and `formal=false`.
There are four task-generic primitive commitment labels `{0,1,2,3}`. A state
contains two, three or four anonymous active lifecycles. Exactly one lifecycle
is the editor at an opportunity; every other lifecycle retains its standing
commitment. JOIN starts without a commitment and must edit before acting,
temporary absence freezes its lifecycle-owned commitment, rejoin restores it,
and terminal LEAVE deletes it. Physical slots are packing coordinates only.

The external source utility after the edit is the fraction of active
commitments that are unique. This is a benchmark return, not intrinsic reward
or shaping. Exhaustive cases balance active count, editor slot, standing-roster
permutation, JOIN versus RENEW, temporary absence/rejoin, terminal replacement
and same/cross-slot reuse.

The actor-visible editor context contains only the anonymous current event and
an unordered representation supplied by the tested mechanism. It never
contains physical identity, a named role, future schedule, remaining lifetime
or utility. The centralized audit may inspect the exact roster.

## Constructive policies and nulls

- `ROSTER_EDITOR` reads the actual unordered standing roster and selects the
  smallest absent label. It must attain utility 1.0 in every exhaustive case.
- `TEAM_REC_ORACLE` reconstructs the exact same roster from the public event
  history and must also attain 1.0. It is the strongest simpler explanation and
  prevents the gate from claiming EHC superiority.
- `INDEPENDENT_EDITOR` has the same edit opportunity but no standing-roster
  input. Its exact balanced utility must match the analytically enumerated null
  and remain below 1.0 for every active-count stratum.
- `SHUFFLED_ROSTER` receives a case-mated but incorrect standing roster. It must
  not equal the constructive utility.

Standing commitment records are event/lifecycle scoped and use no trainable
parameters. The gate does not instantiate PPO, gradients, reward learning or a
primitive-logit adapter.

## Exact intervention

From one pre-edit snapshot, replace exactly one retained commitment with a
different legal label while keeping membership, editor fields, physical
packing and every future event fixed. `ROSTER_EDITOR` must change its selected
commitment whenever the smallest missing label changes. Replaying the original
choice under the intervened roster must lose utility relative to the adapted
choice. This is a roster-to-edit-to-value consequence, not an instantaneous
mark/logit diagnostic.

## Result contract

The runner writes exactly one of:

1. `INVALID_ASYNC_ROSTER_INFORMATION_GATE_G3` for any schema, balance,
   anonymity, lifecycle ownership, finite/exact metric or intervention failure;
2. `PASS_ASYNC_ROSTER_INFORMATION_GATE_G3` only when both constructive policies
   attain 1.0, every null matches its enumerated expectation, all lifecycle
   ownership checks pass and the roster intervention changes choice and value;
3. `FAIL_ASYNC_ROSTER_INFORMATION_GATE_G3` for every other valid result.

A pass establishes only an executable source and comparator boundary. It does
not show that a learned roster representation outperforms TEAM_REC, adopt EHC,
or consume a conclusion-bearing iteration.

## Successor boundary after a pass

Only after the information gate passes may Project Manager decide whether a
small learned comparison is the cheapest separator. Any later contract must
compare a permutation-equivariant roster-conditioned editor against matched
TEAM_REC and independent/no-roster controls, freeze held-out active-count and
lifetime transport, use label-invariant natural mediation, and retain
first-match access before mechanism interpretation.

## Accepted gate result

The exact artifact
`logs/nonformal_async_commitment_roster_g3_20260723_pm1/result.json` passed all
18,400 cases from source commit
`b5b67853a2012dd6957e30ad1a6d05d16dff02fe`. Both constructive policies attain
1.0; all null strata remain below 1.0; lifecycle ownership, anonymity,
permutation balance and roster-only intervention pass. Five focused tests pass.

The uniqueness fraction is a structural gate metric only. It is not a legal
formal objective because label diversity need not produce useful behavior.
`USEFUL_EFFECT_ROSTER_G3_EXECUTABLE_DEFINITION` must instead bind each standing
commitment to a realized service effect and external demand served, including
demand states where duplicate effects are optimal. The information gate is not
rerun or relabeled.
