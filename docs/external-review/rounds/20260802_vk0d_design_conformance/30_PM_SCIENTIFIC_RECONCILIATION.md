# Reconciliation — 20260802_vk0d_design_conformance

Ruling: `21_PRO_OPEN_RAW.md` (CHANGES_REQUIRED) converged by
`22_PRO_CONVERGENCE.md` (one blocker) and `22_PRO_CONVERGENCE_2.md`
(**CONFORMS**), stage commit `85e5f1e9491097af01dbc477d068bb83f85386bd`.

## What was decided

Touchpoint 2 of workflow 8. The three-arm V-K0D comparison is retained and
now fully frozen: PRIMARY = anonymous relative-OTHER encoding (identity
removal ONLY — the populated SELF block was rejected as an unmatched
second intervention), AR loop retained, canonical training serialization;
CONTROL = existing roster, counter-based uniform-per-completed-check
serialization; REFERENCE = existing roster, canonical, bound as a strict
no-op reproduction control with exact canonical model/optimizer digest
equality to the valid V-K0B bundles (no tolerance, no behavioral
equivalence, no post-hoc rule). Amendments A-VD-1..8 entered verbatim in
VK0D_REALIZATION_DECISION_LEDGER.md (commits 9c1c1ced, b01f6312): the
order-draw contract (one draw per completed high-check sequence,
counter-based identity, committed-row storage, PPO reuse, schedule digest
regenerated independently), the complete finite conjugacy panel with
explicit swap(x), a deliberate absolute-ID negative witness and
per-checkpoint rechecks, matched model/optimizer opportunity (same-seed
identical initial trainable bytes across arms), the five-state arm
vocabulary with seven-step comparison precedence, and shared vs arm-local
invalidity stamping.

## Where I was corrected

Four substantive corrections: the SELF block would have confounded the
treatment (two interventions in one arm); the PRIMARY's training order was
unstated and had to be canonical for causal separability; my "natural
fresh-policy anchors" gate population was not an exact structural support
(a defect on an unvisited roster would survive); and "information-
lossless" was wrong wording — the encoder deliberately deletes the
absolute-label shortcut, and that deletion is the treatment. Also
corrected: conjugacy is P01(a0,a1|x)=P10(a1,a0|swap(x)), never same-state
serialization invariance; RNG-stream isolation does not imply cross-arm
trajectory identity.

## Next action

Proof-sized implementation skeleton + Gate-B realization-conformance
package demonstrating the ruling's nine witnesses (encoder shape
invariance, complete conjugacy PASS, negative-witness rejection, schedule
reconstruction, PPO order reuse, same-seed initial equality,
reference-digest reproduction, locality branch witnesses, result-status
witnesses); then exposure-matched training of the three arms, the frozen
bank evaluation under both orders, touchpoint 3, ITERATION_38.
