# SGSP RG2Z RSCF r01 28-family support-slack non-revision clarification

```text
document_kind=owner_authored_nonrevision_science_clarification
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-LOW-WORK-TARGET-BOUND-PHYSICAL-PRIOR-VALUE-DEFINITION
exact_revision=SGSP-RG2Z-RSCF-SCIENCE-20260821-01
owner=EM_semantic_graphon_shared_policy
em_task=/root/em_sgsp_rscf_r01
source_cm_clarification_marker=ROOT_CM_TO_PORTFOLIO_SGSP_RSCF_R01_GATE_B_SCIENCE_CLARIFICATION_20260821
clarification_conclusion=UNIQUELY_RECOVERABLE_FROM_FROZEN_R01_AND_R03_TEXT
science_revision_created=false
science_bearing_change=false
pro_disposition=EXISTING_SAME_CONVERSATION_CLOSED_REMAINS_VALID
new_provider_turn_required=false
scientific_activity_started=false
empirical_coordinates_bound=false
```

## Conclusion

The twelve held-out support-slack rows are uniquely recoverable from the
frozen source text. No result, coordinate, threshold choice or CM inference is
needed, and no successor revision is warranted.

The key source fact is that r03 does not merely name the two composite minima.
Its Section 6.4 explicitly defines all six per-seed component slacks and the
common interiority function. R01 Section 8 explicitly retains "the six r03
per-seed answerability slacks at each held-out size," replaces only the two
registered composite minima `A_s(6),A_s(21)` by those twelve individual rows,
and fixes the 28-quantity two-sided family. R01 Sections 9-10 then fix the
positive sign convention, lower-interval direction and branch precedence.

Exact revision `SGSP-RG2Z-RSCF-SCIENCE-20260821-01` therefore remains the
controlling object. This clarification is a literal expansion of already
incorporated definitions, not a change to treatment, comparator, observable,
margin, multiplicity, result law, activity boundary or claim ceiling.

## Source-composition rule

Read the frozen sources in this exact order:

1. r03 Section 6.4 supplies the per-seed formulas, domains, common function
   `h`, probability-floor support calculation and six margins.
2. r01 Section 8 retains those per-seed formulas, removes only the composite
   minima from the registered family, registers each held-out row separately,
   and changes the simultaneous family from 18 to 28 quantities.
3. r01 Section 9 groups the twelve rows into component-support and direct-
   support prerequisites and requires their simultaneous lower endpoints to
   exceed zero.
4. r01 Section 10 supplies structural-invalidity and result-branch precedence.

R01 does not redefine the six per-seed functions because it incorporates them
by exact reference. R03's former registration of `A_s(N)` as a composite
minimum is the only part replaced. Neither CM nor an analyzer may invent a new
slack, reverse a sign, substitute an observed contrast, or keep the composite
minimum as an inferential row.

## Exact primitive domains and common function

For each independent training-seed block `s` and held-out roster
`N in {6,21}`, use:

```text
TRAINED_ARMS={PHY-TRUST,EDGE-FLEX}
h(x;delta)=min(x,1-x)-delta, for bounded mean x in [0,1]
delta_R=0.04
delta_C=0.03
delta_Z=0.02
delta_cutR=0.05
delta_TV=0.08
delta_I=0.03
```

`UNIFORM-LEGAL` is excluded from every support-slack domain. It appears only
in the separate seen-size competence contrasts `e_s(9),e_s(15)`.

The primitive seed-level means retain their r03 meanings:

- `J_s^{A,int}(m)` is the intact mean return for trained arm `A` at roster
  `m`;
- `J_s^{A,rot}(N)` is the rotated-cut mean return for trained arm `A` at
  held-out roster `N`;
- `T_s,z^{A,int}(N)` is the intact timely-delivery mean for zone
  `z in {WEST,EAST}` and trained arm `A` at held-out roster `N`; and
- `p_h` is the intact `PHY-TRUST` legal-action distribution at registered
  predecision history `h`, with `m_h` legal actions and legal-uniform floor
  `ell_h=0.04/m_h`.

## Exact twelve per-seed support slacks

For each `s` and each `N in {6,21}`, compute exactly:

```text
A_dir_s(N)
  = min over A in TRAINED_ARMS of
      h(J_s^{A,int}(N); delta_R)

A_interaction_s(N)
  = min over A in TRAINED_ARMS and m in {N,9,15} of
      h(J_s^{A,int}(m); delta_C)

A_zone_s(N)
  = min over A in TRAINED_ARMS and z in {WEST,EAST} of
      h(T_s,z^{A,int}(N); delta_Z)

A_cut_s(N)
  = min over c in {int,rot} of
      h(J_s^{PHY,c}(N); delta_cutR)

A_atten_s(N)
  = min over A in TRAINED_ARMS and c in {int,rot} of
      h(J_s^{A,c}(N); delta_I)

TV_sup(p_h)
  = 1-(m_h-1)*ell_h-min over legal a in A_h of p_h(a)

A_TV_s(N)
  = mean over registered held-out-N intact-PHY histories (e,t,i) of
      TV_sup(p_{e,t,i}) - delta_TV
```

These definitions imply twelve distinct seed-level series:

```text
component support:
  A_cut_s(6), A_atten_s(6), A_TV_s(6)
  A_cut_s(21), A_atten_s(21), A_TV_s(21)

direct support:
  A_dir_s(6), A_interaction_s(6), A_zone_s(6)
  A_dir_s(21), A_interaction_s(21), A_zone_s(21)
```

Three distinctions are mandatory:

- `A_interaction_s(N)` is the retained r03 interiority minimum over the
  underlying intact arm returns at `{N,9,15}`. It is not a slack computed from
  the observed interaction contrast `c_s(N)`.
- `A_cut_s(N)` is the retained interiority minimum of the intact and rotated
  `PHY-TRUST` returns. It is not a slack computed from `C_s^{PHY}(N)`.
- `A_atten_s(N)` is the retained interiority minimum across both trained arms
  and both cut conditions. It is not a slack computed from the differential
  attenuation contrast `I_s(N)`.

The former composite

```text
A_s(N)=min(A_dir_s(N),A_interaction_s(N),A_zone_s(N),
           A_cut_s(N),A_atten_s(N),A_TV_s(N))
```

is not one of the 28 registered quantities, is not an inferential substitute
for the twelve rows and does not gate any r01 branch.

## Sign convention and simultaneous intervals

Every slack is oriented so that larger is more interior/more supported:

- `h(x;delta)>0` means the underlying bounded mean is more than `delta` away
  from both 0 and 1;
- `A_TV_s(N)>0` means the intact treatment's legal-simplex support permits TV
  exceeding `delta_TV` on average; and
- a negative or zero seed value is not itself a scientific branch. Inference
  is across the 24 independent seed blocks.

For every one of the 28 registered seed-level quantities `q_s`, use the paired
seed-block Student-`t` interval:

```text
number_of_seed_blocks=24
degrees_of_freedom=23
per_quantity_two_sided_error=0.05/28
lower_q=mean_s(q_s)-t_{23,1-(0.05/28)/2}*sd_s(q_s)/sqrt(24)
upper_q=mean_s(q_s)+t_{23,1-(0.05/28)/2}*sd_s(q_s)/sqrt(24)
```

Thus each interval is two-sided, while each support prerequisite uses its
simultaneous **lower** endpoint. There is no one-sided interval substitution,
upper-endpoint support gate, sign reversal, per-seed pass count, post-result
component selection or composite-minimum interval.

The complete family remains exactly:

```text
4  d(N), N=9,15,6,21
2  e(N), N=9,15
2  c(N), N=6,21
2  z(N), N=6,21
6  C_PHY(N), V(N), I(N), N=6,21
6  A_cut(N), A_atten(N), A_TV(N), N=6,21
6  A_dir(N), A_interaction(N), A_zone(N), N=6,21
--
28 quantities
```

All 28 intervals and every predicate are reported regardless of which branch
applies.

## Exact prerequisite and branch precedence

Apply the frozen r01 law without modification:

1. Structural invalidity, including incomplete Q/seed evidence, origin or arm
   mismatch, factual-return identity failure, open-loop/factual-future replay,
   branch-salted randomness, parameter drift, gradient/leakage, unmatched
   work/information/optimizer/checkpoint, failed containment or nonfinite
   values, yields no scientific relation.
2. If structurally valid, evaluate all three prerequisite categories even when
   more than one fails:
   - component support requires the lower endpoints of `A_cut`, `A_atten` and
     `A_TV` to exceed zero at both `N=6` and `N=21`;
   - comparator competence requires both seen-size `e(N)` lower endpoints to
     exceed `0.08` and both seen-size `d(N)` intervals to lie wholly within
     `[-0.04,+0.04]`; and
   - direct support requires the lower endpoints of `A_dir`,
     `A_interaction` and `A_zone` to exceed zero at both held-out sizes.
   Any failed prerequisite category yields `NONIDENTIFIED`; report every
   failed category and predicate. No retain/delete conclusion follows.
3. If every prerequisite passes but any component-attribution lower endpoint
   fails its frozen threshold (`C_PHY>0.05`, `V>0.08`, `I>0.03` at both
   held-out sizes), do not retain the fixed prior for this exact package.
   Report every failed component predicate and do not claim mechanism absence.
4. Select `RETAIN_PHYSICAL_PRIOR_COLDSTART` only when every prerequisite,
   every component-attribution threshold and every direct-value threshold
   passes at both held-out sizes.
5. If every prerequisite and component-attribution threshold passes but the
   direct-value conjunction fails (`d>0.04`, `c>0.03`, `z>0.02` at both
   held-out sizes), do not retain the fixed prior for this exact package and
   report every failed direct, interaction and worst-basin predicate.

Because branch 3 precedes branch 5, a component-attribution failure determines
the nonretention branch even if direct-value predicates also fail; nevertheless
all 28 intervals and all predicates remain visible. For any competent,
answerable nonretention branch, add `PRACTICAL_EQUIVALENCE` only when both
held-out `d(N)` intervals lie wholly inside `[-0.04,+0.04]`, and add
`EDGE_MATERIALLY_SUPERIOR` only when both held-out `d(N)` upper endpoints are
below `-0.04`. A nonpositive gate alone proves none of those labels, harm,
component absence or universal prior failure.

## Why the existing Pro closure remains valid

The same-conversation ChatGPT External Pro disposition remains `CLOSED` for
exact revision `SGSP-RG2Z-RSCF-SCIENCE-20260821-01` with zero science-bearing
defects, and the existing EM intake remains accepted.

No new Pro turn is required because this clarification adds no formula or
decision rule. The closed r01 text already did all four necessary semantic
operations: it retained the r03 per-seed slack definitions, replaced only the
two composite registered minima, enumerated the twelve rows in the 28-family,
and fixed lower-endpoint prerequisite/branch behavior. This artifact merely
places those non-adjacent frozen clauses next to one another for an analyzer
consumer. A provider rereview would be required only if a formula, domain,
margin, multiplicity rule, gate, branch, activity boundary or claim were
changed; none is changed here.

## CM continuation and analyzer dependency surface

The selected runner-and-Gate-B construction stage remains scientifically
unchanged. After Portfolio relays this artifact through Operational Root, the
same-direction CM may continue all previously authorized independent work:

- exact accepted Gate-A host/ABI reuse, fail-closed loader/cache and technical
  repair only under the existing source-identity rules;
- production-complete prefix-state carriage, arm-independent selector
  generation, immutable snapshots, factual policy/autograd, stopped all-action
  native targets and ABI transfer;
- literal `PHY-TRUST`-within-`EDGE-FLEX` matching, result-blind batching,
  compact audits/certificates and no raw Q/branch traces;
- atomic non-evaluable frontier/checkpoint/resume and TEST-only evaluation
  consumer plumbing; and
- full-chain result-blind timing, CPU/RSS/scratch/storage and `1|2|4`-worker
  cost characterization that does not depend on scientific values.

The exact analyzer dependency surface is now limited to:

1. compute the six formulas above separately at `N=6` and `N=21` from their
   named seed-level primitive inputs;
2. register the twelve series individually, not the two composite minima;
3. construct all 28 paired two-sided intervals with error `0.05/28`;
4. apply the three prerequisite categories and branch precedence above; and
5. report all intervals and predicates without result selection.

CM may implement and technically test that analyzer only with deterministic
synthetic TEST inputs under the existing Gate-B envelope. No formula-dependent
runner work needs a new scientific revision or new provider review.

## Activity boundary and prohibitions

This clarification is static and preactivity. It materializes no scientific
master, selector, numeric seed, coordinate, initialization, task event,
detection, packet, action uniform, branch, Q entry, policy output, model,
checkpoint, rollout, endpoint or result. Existing accepted Gate-A facts remain
unchanged.

The runner/Gate-B stage must continue to use unmistakable deterministic
TEST-only identities. It authorizes no production scientific identity, model
initialization, real training/evaluation, inferential row, empirical result or
lease. It also authorizes no threshold change, formula substitution,
composite-minimum inference, result-dependent selection, r03/CCA source or
result reuse, Gate-A redesign, GPU, second surface, UAV, deployment or flight.

This EM contacts no CM and performs no code, test, canonical/reconciliation or
Git write. Portfolio and Operational Root retain the exact two-Root relay and
application authorities.

## Exact cross-root clarification packet

```text
PORTFOLIO_EM_TO_ROOT_CM_CLARIFICATION
marker=PORTFOLIO_EM_TO_ROOT_CM_SGSP_RSCF_R01_28_SLACKS_NONREVISION_CLARIFICATION_20260821
direction_id=semantic_graphon_shared_policy
exact_object_revision=SGSP-LOW-WORK-TARGET-BOUND-PHYSICAL-PRIOR-VALUE-DEFINITION / SGSP-RG2Z-RSCF-SCIENCE-20260821-01
em_owner=/root/em_sgsp_rscf_r01
clarification_artifact=docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_RSCF_R01_28_FAMILY_SUPPORT_SLACKS_NONREVISION_CLARIFICATION_20260821.md
conclusion=All twelve support-slack formulas, signs, two-sided intervals, lower-endpoint gates and branch precedence are uniquely determined by frozen r03 Section 6.4 plus r01 Sections 8-10; this is a non-revision clarification.
pro_disposition=Existing same-conversation ChatGPT External Pro CLOSED for SGSP-RG2Z-RSCF-SCIENCE-20260821-01 remains valid; no new provider turn or EM closure intake is required.
cm_continuation=Resume the existing runner-and-Gate-B construction envelope unchanged. Independent runner work continues; formula-dependent analyzer work must implement exactly the twelve per-seed rows, 28 two-sided intervals and branch law in this artifact using TEST-only inputs.
analyzer_fence=Do not infer new formulas, substitute A_s(N), reverse signs, use one-sided intervals, select components/results or change margins, multiplicity, prerequisites or branches.
activity_boundary=No scientific identity, coordinate, initialization, model, episode, checkpoint, rollout, endpoint, result or empirical lease; deterministic TEST-only construction and conformance only.
return_boundary=Return the originally requested technically accepted runner plus Gate-B full-chain/cost artifact, or the exact science/object change, material cost/resource expansion or semantic impossibility. This clarification creates no separate runtime/status return.
does_not_authorize=No empirical activity, lease, threshold or treatment change, r03/CCA reuse, Gate-A redesign, GPU, second surface, UAV/deployment/flight, provider turn, user contact, canonical/reconciliation write or Git action.
```

The minimum Root action is to relay this exact artifact unchanged to the
existing same-direction CM and preserve revision `SGSP-RG2Z-RSCF-SCIENCE-
20260821-01` in the active runner/Gate-B envelope. Root need not request a new
science card, Pro turn, Gate-A action, empirical identity or lease.

## Exact source pointers

- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_R03_DEFINITION_SCIENCE_CARD.md`
- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_ROLE_SAMPLED_CF_R01_SCIENCE_CARD.md`
- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_ROLE_SAMPLED_CF_R01_CHATGPT_EXTERNAL_PRO_CLOSED_INTAKE.md`
- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_RSCF_R01_GATE_A_CONSTRUCTION_EM_HANDOFF_20260821.md`
- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_RSCF_R01_GATE_A_ACCEPTANCE_EM_INTAKE_20260821.md`
- `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_RSCF_R01_RUNNER_GATE_B_CONSTRUCTION_EM_HANDOFF_20260821.md`
