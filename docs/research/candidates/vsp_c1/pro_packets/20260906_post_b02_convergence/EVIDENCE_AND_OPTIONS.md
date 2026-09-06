# VSP-C1 post-B02 Convergence: evidence and options (DM proposal, 2026-09-06)

Claim under test in the K4 toy family: on a public fixed-partner plan with two exogenous periods
and a six-step native return, a factorized cross-period value parameterization (FACTOR) learns
faster or higher than a same-information generic network (GENERIC). Binding structure: the
representation of value across periods inside one learning controller; the partner is fixed and
public, so the toy reduces to a single-controller problem (r02 constraint, accepted).

Proposal only, for the existing `em:vsp_c1:convergence` node, written by the Claude research hub
as DM after the intake of `VSPC1-K4-FACTOR-VALUE-B02-BUDGET512`. Not a card, a launch or a
Portfolio action.

## What B02 measured (observation; card rule applied in the result intake)

- One fresh seed (3), two arms, 512 optimizer steps each with the B01 exploration prefix to 128
  and ε = 0.1 afterwards; 33 evaluation points; counts exact; zero trajectory-check violations;
  both invocations complete on `wsl_4070` at 90c730a09 in 2.66 s and 2.17 s outer wall.
- ΔJ_128 = +1/12 (FACTOR ahead at the original budget, equal to the declared MEI);
  ΔJ_512 = 0; D = ΔJ_512 − ΔJ_128 = −1/12; L_F = +1/12, L_G = +1/6.
- AUC(0:128) +0.0026, AUC(0:512) +0.0449, AUC(128:512) +0.0590, all FACTOR − GENERIC.
- Both arms end at J = 5/6, the host's declared analytic free-policy reference, with the same
  final context profile (p = 2 contexts at 1.0, p = 6 contexts at 2/3). FACTOR first touches 5/6
  at u = 208 and holds it from u = 400; GENERIC first touches at u = 432 and holds from u = 464.
- Reading-rule row 4 was first applicable: "128 point favourable, 512 shrinks to zero, GENERIC
  improves more late" → the automatic-extension path for this combination ends; neither
  equivalence nor negative transfer is shown. Row 6's fact (both at the reference) was recorded
  as the reason ΔJ_512 = 0 is a ceiling equality, not an overtaking; row 7's guard (endpoint and
  AUC disagree in sign) means no winner is declared from the AUC.
- Across the family: B01 seeds 0/1/2 endpoints at 128 were −1/24, +1/12, +1/12 (mean +0.0417);
  the seed-3 prefix adds +1/12 at 128 as a listed, unpooled fourth instance. Every result is a
  small, instance-sensitive parameterization signal; the one place it now has a clean native
  reading is time-to-reference on a toy whose reference both arms reach within 512 updates.

## Predictions scored

Pro (r02): "a seed-3 gap at 128 is more likely to shrink than reliably widen" — matched. DM: five
of six sub-predictions right; the wrong one expected the late-window AUC difference to be
smaller than the early one, and it was twenty times larger. Owner: not taken.

## Options the DM sees

1. **End the public-plan toy family at this boundary** (DM recommendation, offered for
   challenge). The toy has no endpoint room left to compare these parameterizations; the
   remaining difference (time to reference, one instance) is not a decision-relevant quantity
   for the K4 question. Keep the three B01 seeds, the B02 instance, the negative seed and the
   ceiling fact as recorded; K4 (cross-period value sharing) is not closed; no new object in this
   toy at any budget or seed count.
2. **A comparator-representation question on the same toy**: replace GENERIC with the tabular,
   fully-conditioned Q learner the B01 card named as a possible later discriminator, to test
   whether FACTOR's early advantage is an advantage over a weak network rather than a benefit of
   sharing. Cost: seconds per arm. The DM does not recommend it: on a ceiling-bound toy a stronger
   comparator can only shrink an advantage that is already zero at the endpoint.
3. **A new host with room above the current reference**, where cross-period sharing has a
   native consequence the six-step toy cannot show: more than two periods, a longer horizon
   with intermediate renewals, or a partner that adapts (non-public plan). If the node continues
   K4, this is the DM's candidate; it needs a described event → role → information → action/credit
   → learning → native consequence chain and its own cost, none of which is projected from the
   toy.
4. **Explicit recast** of K4's question. Not recommended by the DM: the source question (does a
   cross-period value structure help a renewal learner) is intact; only its first toy is spent.

## What the DM asks the node not to do

- Do not extend this combination to 1,024 or 2,048 updates, add a fourth B01 seed, repeat the
  B02 instance, or form a pooled four-seed mean (card section 2; row 4 consequence).
- Do not read ΔJ_512 = 0 as equivalence or as GENERIC overtaking; do not read the positive AUC
  windows as FACTOR "learning faster" in general (row 7).
- Do not change lifecycle or priority; that is a Portfolio matter.
