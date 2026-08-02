# V-K0C realization design conformance check

Touchpoint 2 of workflow 7. One question: **does the completed code design
in `docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md` conform to
the V-K0C evidence semantics you froze in round
`20260801_vk0b_valid_rerun_result`?** Zero experiments have run in this
workflow. Discarding this question's structure is a legitimate answer.

## Variable-k relevance

V-K0C localizes where the decisive reversed-serialization competence
failure enters the R30 carrier — the finding that currently blocks every
further variable-k comparison.

## Frozen inputs (not review surface)

- Your V-K0C sections 1–9 verbatim (checkpoint set, 2,688 anchors, both
  occupancy strata, order-conjugacy positive control, exact enumeration,
  TV + task-consequence quantities at δ=0.5, exact trajectory propagation,
  fresh-initialization control, inference hierarchy, factorized A–E record,
  conditional portfolio).
- Code facts, scout-mapped and PM-spot-checked at this round's
  `stage_commit`: the policy's per-agent context is pure and deterministic
  (`_token_context` → keep_logit + masked skill logits; the same-label
  mask underflows to exactly zero softmax mass); `act_sequence` mutates
  working state in place per token, which is the autoregressive
  conditional structure itself; the V-K0B driver's from-reset replay,
  fingerprint, seed-derivation and oracle-invocation machinery are
  importable functions; the env clock is action-independent (documented
  and exploited by the existing oracle-invocation path); the low level is
  a stateless fixed table and the config's low-level path is feedforward.

## The design, in one paragraph (full detail in the ledger)

VC-D1 adds one pure public `token_distribution` method (explicit working
state in, normalized keep/skill probabilities out; no RNG, no buffers) and
refactors `act_sequence`'s working-state advance into a shared helper both
paths call, so enumeration and sampling cannot drift. VC-D2 restores each
of the 2,688 anchors by the existing from-reset natural-prefix replay
verified byte-exactly against the stored V-K0B fingerprint (mismatch =
invalidity, never a dropped anchor); at each anchor both orders'
16-outcome joint distributions are enumerated purely, and the prescribed-
assignment positive control forces both agents under each order for every
legal final assignment with executed 5-step windows. VC-D3 realizes the
exact episode propagation as memoized finite-state occupancy pushforward
(the toy's complete high-level state is (signs, check, joint skills, ages,
mask)), with policy inputs rebuilt exactly as the natural driver builds
them and the stored factual V-K0B rows reproduced as a validity condition.
VC-D5 realizes the fresh control as two independent same-seed
constructions with required parameter-hash equality. VC-D6 splits driver
and analyzer, with the ruled invalidity conditions and Factors A–E, the
existing bootstrap hierarchy and frozen seed, and row-recomputable
summaries.

## Points where the design interprets the ruling (flagged)

1. **Analytic propagation vs executed replay.** Your §5 orders "exact
   state-probability propagation, not Monte Carlo token sampling". VC-D3
   propagates occupancy analytically over the finite high-level state
   (rebuilding policy inputs from reconstructed env + roster), while the
   positive control and the factual-row reproduction execute real env
   steps. If §5 instead requires physically replaying every branch, the
   16^8 path tree makes that infeasible and the design would need your
   correction.
2. **Enumeration normalization.** Probabilities are taken from the
   policy's own factorization (sigmoid × masked softmax); the validity
   condition "mass sums to one" is asserted within 1e-9 with the raw sum
   recorded, then renormalized only for reporting. Flagged in case exact
   unnormalized sums are themselves evidence you want preserved (they are
   recorded either way).
3. **Anchor deduplication.** "Deduplicate the two focal-agent rows
   belonging to one check" is realized as one anchor per (seed, episode,
   check) — 2,688 = 6×64×7 — with both agents' quantities computed at
   that single anchor.

## Required response sections

1. `CONFORMANCE` — CONFORMS, or the exact ledger items that deviate.
2. `INTERPRETATIONS` — accept/correct the three flagged readings.
3. `CONVERGENCE_DECISION` — your closing decision for this touchpoint.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260801_vk0b_valid_rerun_result/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/r30_fixed_clock.py`
- `scripts/audit_vk0b_r30_access.py`
- `scripts/audit_vk0a_source_urgency_oracle.py`
- `ha_ctse_process/standalone_agent.py`
