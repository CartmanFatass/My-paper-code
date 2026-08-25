# VQFP-FERL r02 defect-resolution map

```text
owner=direction:voronoi_quadrature_field_policy
from_revision=VQFP-FERL-SCIENCE-20260821-01
to_revision=VQFP-FERL-SCIENCE-20260821-02
accepted_pro_defects=14
resolution_form=one_complete_replacement_composite
r01_modified=false
```

Normative r02 artifacts:

- `VQFP_FERL_R02_SCIENCE_CARD_20260821.md`
- `VQFP_FERL_R02_GENERATOR_ANALYZER_MANIFEST_20260821.md`

## Exact resolution table

| # | Accepted r01 defect | Frozen r02 resolution | Normative location |
|---|---|---|---|
| 1 | `t=0` previous actions undefined | Every own and present-neighbor previous SENSE/RELAY share is exactly zero at `t=0`; absent records are numeric zero plus boundary bit one. | Card “Actor information boundary”; manifest §§3–4 |
| 2 | Tick-32 plume transition ambiguous | Independent `F_1,F_2`; current field uses `mu(t)`; the sign multiplier applies only to the `32->33` transition; a stateful one-crossing elastic recurrence updates both center and persistent velocity. | Card “Action-independent plume-front recurrence”; manifest §3 |
| 3 | Seed `U/R` aggregation unspecified | `U_seed` and `R_seed` are equal-weight arithmetic means of the 128 episode ratios; raw components remain stored. | Card “Exact direct endpoints”; manifest §9 |
| 4 | `D90` event and quantile non-single-valued | Integer-tick membership only; two immediately preceding ticks outside; entry-tick coverage included; exact delay/censor cap; pooled normalized delays; nearest rank at `ceil(.90*M)`; continuous unoccupied crossings create no event. | Card “Complete discovery-delay analyzer”; manifest §§3,9 |
| 5 | Analytic tie-break incomplete | Among all exact global minimizers choose the lexicographically largest vector in physical-rank order `(s_1,r_1,...,s_N,r_N)`. | Card “ANALYTIC-ONE-STEP”; manifest §1 |
| 6 | Reassociation mixes closed loop and frozen history | One closed-loop cyclic intervention: even episodes shift `+1`, odd `-1`; substitute every present own/neighbor factor/residual length; keep exogenous tapes and true service cells; recursively update actions, backlog, previous actions and GRU; intact/intervention share action uniforms. | Card “REASSOCIATED-MEASURE”; manifest §8 |
| 7 | Allocation support statistic undefined | `a_i=pi_iS+pi_iR`, `d=max a-min a`; pool exactly 8,192 ticks; integer thresholds 4,096 dispersion ticks and 6,554 joint mode-support ticks; arm/cell requires 20 of 24 seeds. | Card “Allocation/action support”; manifest §10 |
| 8 | Competence intervals incomplete and `R<.90` ambiguous | Preserve the 84 claim contrasts inside a 180-statistic master family; add the 48 missing learned/equal contrasts, 24 `C_A`, and 24 `Q_A=.90-R_A`; one Bonferroni Student critical value covers all 180. Competence requires lower `C>0`, proof of endpoint non-harm and lower `Q>0`. The comparison count is corrected to seven. | Card “Simultaneous inference” and prerequisite 5; manifest §11 |
| 9 | Secondary opportunity predicate unclear | In every held-out cell the simultaneous lower endpoint for analytic/equal `U` exceeds `.08`, and the simultaneous lower endpoint for at least one of `D90/R` exceeds its material margin. | Card prerequisite 2 |
| 10 | Materiality/non-harm/quantifiers ambiguous | Globally define `MAT`, `HARM`, `NH`, `EQ` from exact interval endpoints; define reverse intervals; spell out comparator sets, every-cell clauses and same-`N*`/both-layout conjunctions in every branch. | Card “Simultaneous inference” and result map; manifest §12 |
| 11 | FERL harm branch unreachable after competence | Move established FERL target harm ahead of competence. It requires strict `HARM`, not failure to prove non-harm; later competence failure makes no harm claim. | Card prerequisites 4–5 and result branches 4–5 |
| 12 | Opposing held-out effects resolved only by branch order | Add `HETEROGENEOUS_FERL_FREE_EFFECTS` before directional value branches; require favored-arm primary-U non-harm in every other held-out cell; make retain/delete implications cell-specific. | Card branches 7–9 |
| 13 | Nonqualifying mechanism controls mislabeled generic | A generic-without-specificity branch now requires complete practical equivalence of FERL/FREE and all three measure-specificity controls. Otherwise positive allocation routes to `ALLOCATION_VALUE_WITH_MEASURE_SPECIFICITY_UNRESOLVED` with no automatic deletion. | Card branches 11–12 |
| 14 | One-parameterization claim mismatches 24 trained seeds | Claim is explicitly a simultaneous mean seed-level training-procedure effect; each seed yields one shared-across-agents/rosters parameterization; no selected-checkpoint or every-run claim. | Card “Maximum claim and nonclaims” |

## Additional visible completeness choices

These do not change the core treatment or comparator. They remove implementation-
dependent degrees of freedom that could otherwise reintroduce scientific
ambiguity:

- a complete seven-coordinate length-free actor content vector, boundary
  encoding, two-layer shared content encoder, neighbor-message sum, GRU
  equations, base/residual tensor map and literal multiplier containment;
- identical initial common tensors across all three learned arms, exact-zero
  residual outputs and one Xavier-uniform initialization law;
- one centralized current-truth critic map that cannot feed actor execution;
- exact recurrent PPO loss, advantage standardization, complete-episode
  minibatches, optimizer-step count and explicit absence of hidden
  normalization, clipping or auxiliary losses;
- an address-based random-tape/coupling law with common exogenous tapes,
  independent learned-arm action streams and identical intact/reassociated
  action uniforms; and
- an atomic complete-panel definition containing all raw event, support and
  inference vectors.

## Preserved core and visible science-bearing changes

Preserved unchanged in meaning: fixed `E_total=0.20`; one shared policy across
variable `N`; training `N={4,8}`; held-out `N={6,12}`; FERL hard `log(v)` factor;
strict-containing FREE residual; NO-MEASURE, EQUAL, analytic and reassociation
control roles; `U/D90/R`; 24 seed blocks; 600 PPO updates; 128 evaluation
episodes/cell; original 84 claim contrasts; material margins; pre-activity
boundary; and finite 1-D claim ceiling.

Visible science-bearing changes required for closure are the exact generator/
analyzer choices above, the 180-member simultaneous master family, the moved
harm adjudication, the heterogeneous-effects branch, strengthened generic-
specificity exclusion and mean-procedure claim language. No empirical evidence
motivated or tuned any choice.

## Completion meaning

This map is descriptive provenance. Mathematical closure still requires the
saved-conversation ChatGPT Pro to return `CLOSED` on the complete r02 composite,
followed by EM intake. The map itself authorizes no provider turn, Gemini, CM,
activity, code, coordinate, compute or Git action.
