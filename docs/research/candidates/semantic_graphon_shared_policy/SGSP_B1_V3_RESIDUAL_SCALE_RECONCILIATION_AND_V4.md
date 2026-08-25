# SGSP B1 revision-03 residual-scale reconciliation and revision 04

```text
direction=semantic_graphon_shared_policy
predecessor_revision=SGSP-B1-SCIENCE-20260813-03_PRO_CLOSED
successor_revision=SGSP-B1-SCIENCE-20260813-04
owner=EM_semantic_graphon_shared_policy
trigger=Root_portfolio_causal_claim_concern
scientific_activity_started=false
registered_stochastic_object_materialized=false
owner_choice=ADD_EQUAL_WIDTH_ALT_CENTER_AND_ANCHOR_ACTION_CUT
mathematical_closure=revision_04_PREPARED_NOT_SENT_SAME_CONVERSATION
cm_release=withheld
same_direction_cm_final_ambiguity_audit=NONE
```

## Decision

The narrow revision-03 prose ceiling was honest but not decision-complete. It
said graphon correctness was not separated from generic shrinkage or
conditioning, while its successful branch still promoted a fixed graphon
family and activated a second surface. A result compatible with nothing more
than the `0.25` versus `2` optimization-geometry difference cannot justify that
branch. The smallest repair is option (b): add one equal-width wrong-center
control and one anchor-only action cut.

## Frozen correction

`ALT-CENTER` uses

```text
W_ALT=[[0.2,1],[1,0.2]]
residual_scale=0.25
gamma_initialization=all_binary64_zero
```

It shares SGSP's common initialization bitwise, role/message inputs, four
output-relevant residual parameters, module shapes, optimizer, worlds, action
tapes, support, communication, useful operations, storage, and final-checkpoint
rule. Its coefficient multiset equals SGSP's while same-role and cross-role
locations are exchanged.

The log-edge Jacobian formula is identical for SGSP and ALT:

```text
d log(omega_bb') / d gamma_bb' = 0.25 sech^2(gamma_bb').
```

At zero residual, the raw-edge Jacobian entries are `0.25*W_bb'`. Their
multisets and norms match under the fixed same/cross-cell permutation, but they
are not indexwise equal. Indexwise nonidentity is the center treatment, not a
hidden mismatch. Realized Jacobians after independent learning need not remain
equal and are not claimed to do so.

The SGSP-only `CENTER-SWAP` replay replaces `W` by `W_ALT` in both `D` and `M`
on the same held-out `OPPOSED` worlds while keeping learned gamma at its true
role-pair index, sender/receiver roles, messages, target/reward, parameters,
row order, and action tape fixed. It differs from sender reassociation after
learning because reassociation also moves sender-block membership relative to
gamma. Revision 04 registers both cuts rather than treating them as aliases.

## Identification gained and ceiling retained

A qualifying revision-04 result must beat both the wider `EDGE-PE` family and
the equal-width `ALT-CENTER`, pass semantic reassociation, and pass the
anchor-only return/action cut. This excludes generic global residual width and
initial log-Jacobian scale as sufficient explanations relative to the frozen
wrong center.

It still does not prove a universally correct graphon. `W_ALT` is one
disassortative alternative and the physical target was deliberately generated
from `W`; target-table alignment or cell-specific numerical preconditioning
remains inseparable from correctness on this toy. The claim is therefore
relative to these exact centers and held-out roster cells only.

## Final prepublication ambiguity closure

The same-direction CM's read-only audit found three older literal gaps and one
inert handle detail before any stochastic materialization. Revision 04 freezes
them rather than leaving them to implementation choice:

- canonical base rows are deterministic lexicographic `(role,slot)`; there is
  no stochastic base row order;
- the nominal handle is the deterministic equality-only complete
  world/member-address record and is never a draw or policy input;
- evaluation uses exactly one separately addressed permutation uniformly
  conditioned on nonidentity, reused across every applicable arm and cut;
- training update `t` and local cell index `e` use global counter episode
  `16*(t-1)+e`, so all 7,680 training worlds per cell have distinct addresses;
  and
- an interaction authorizes a successor only when its matching `GE` or `GA`
  two-sided availability flag holds; otherwise it is failed availability; and
- the mechanism-failure branch requires both matched two-sided flags, both cut
  flags, and both SGSP-material labels, but not anonymous-positive availability.

These choices affect reproducibility and branch authorization but no observed
object selected them. They are included in the complete unsent revision 04 and
therefore in its same-conversation Pro rereview. After the exact branch-6
predicate was made literal, the paired CM's final read-only reread returned
`NONE`: no remaining science-definition ambiguity capable of changing a
stochastic object, checkpoint, legal action, endpoint, headroom flag, interval,
causal gate, branch, deletion/revisit rule, or maximum claim.

## Unchanged object and authority

The roster sizes, DGP, physical target, action/reward, shared parameterization,
counter dependence, 16 seeds, 256 evaluation worlds, optimizer, material
margin, existing thresholds, finite-toy complexity ceiling, activity boundary,
and UAV nonclaims remain unchanged. The new arm, contrasts, cut, headroom flags,
atomic fields, branches, and second-surface retention rule are frozen before
activity.

Revision 04 requires same-conversation ChatGPT External Pro `CLOSED` plus owner
intake. No construction, stochastic materialization, test, compute, or
production is authorized.
