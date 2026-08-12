# VNFC-B3 v6 preactivity bank infeasibility and v7 prospective revision

Owner: `direction:variable-n-fleet-churn` Explorer Manager  
Treatment family: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Non-instantiable revision: `SP-RDA-MATH-CLOSURE-20260812-06`  
New prospective revision: `SP-RDA-MATH-CLOSURE-20260812-07`  
Scientific activity: not started  

## Owner conclusion

V6 cannot instantiate its first required training bank. This is a prospective
panel-law infeasibility, not evidence about learned bids, SP-RDA value, variable-N
robustness, or the treatment family. No optimizer step, evaluation, treatment
metric, or outcome exists. CM must not change the matrices, numerical tolerance,
or shared-history rule and must not launch v6.

The family remains scientifically promising because the high-information causal
cut survives: whether one shared, permutation-equivariant bidder adds material
held-out-N value beyond ZERO, comparative advantage, and the history/handoff-aware
fixed priority through the same sparse reward-blind allocator. The failure is in
asking one physical history to be individually near-optimal under four crossed
capability variants whose optima conflict. It does not test that learned-versus-
fixed question.

I retain the family under the smallest complete prospective repair. V7 keeps the
four matrices, one history shared across all four variants, and the numerical
`0.02` tolerance. It changes only the benchmark: histories are within `0.02` of
the best attainable shared minimax-regret compromise, rather than within `0.02`
of four mutually incompatible individual optima. This changes the target panel
and claim ceiling and therefore supersedes the v6 Pro closure for production.

## Accepted CM preactivity evidence

CM's deterministic zero-metric proof probe reported, for the first registered
seed/schedule `(1601, training, 6->9)`:

- raw indices `0,...,95`: zero of 96 passed v6 call 5;
- all 96 became certifiably infeasible immediately after the four individual
  `S_star` computations when required to share one history satisfying every
  `S_pre^v>=S_star^v-0.02` constraint;
- 480 feasibility-only calls completed in 0.79 seconds;
- independent enumeration of all `4^6` histories for raw index zero found zero
  shared feasible histories; and
- the best common margin for raw index zero was `-0.04905`, so the incompatibility
  exceeds the registered `0.02` per-variant slack.

These facts establish an empty first training bank and impossibility of reaching
the first optimizer step under unchanged v6. They do not establish that later v7
KEEP/SWITCH qualifications or full banks will succeed; that remains prospective
construction evidence for CM after mathematical closure.

## Exact v7 certificate delta

Retain each variant's pre-service optimum

`S_star^v=max_p S_pre^v(p)`.

For one history shared across all four variants define

`Delta(p)=max_v(S_star^v-S_pre^v(p))`

and

`Delta_star=min_p Delta(p)`.

The shared history admissibility law becomes

`Delta(p)<=Delta_star+0.02`,

equivalently

`S_pre^v(p)>=S_star^v-Delta_star-0.02` for every `v`.

A minimizer of `Delta` always makes the admissible set nonempty. The repair does
not guarantee that a distinct SWITCH history satisfying every later physical-
return condition exists; bank incompleteness remains a registered preactivity
outcome rather than permission to relax or top up.

The fixed solver order becomes 25 logical calls per raw base:

1. calls 1–4: the four individual `S_star^v` values;
2. call 5: `Delta_star`;
3. calls 6–7: maximize the all-kept minimum return under the shared-regret bound,
   then mixed-radix-rank tie-break to obtain `p_KEEP`;
4. calls 8–9: minimize survivor retained coverage for a distinct admissible
   history, then rank tie-break to obtain `p_SWITCH`; and
5. calls 10–25: the same sixteen `R/K` ceiling/kept calculations.

All post-history treatment, comparator, observation, action, PPO, allocator,
panel, inference, activity, Stage-1/Stage-2 gate, scaling, and no-rescue definitions
remain exactly v6. The raw cap remains 5,120, derived-variant cap 20,480, and
retained ceiling count 6,144; the maximum logical certificate-call ledger changes
from 122,880 to 128,000. CM must reproject the complete v7 resource envelope after
Pro closure.

## Claim effect and strongest alternative

The primary arm contrasts are unchanged, but their target distribution is now
explicitly conditioned on histories selected as the best shared minimax-regret
compromise across four capability variants. A positive result cannot claim that
those histories are individually near-optimal in any variant or representative of
an operational pre-churn allocator. It supports only learned-bid value conditional
on this robust-compromise history law.

This strengthens the alternative that a learned advantage may exploit a
constructed compromise-history distribution rather than transferable roster
composition. ZERO/FROZEN/HANDOFF/PERMUTE, fixed mass, KEEP/SWITCH, RC headroom,
and sparse operation gates still distinguish learned bid value from fixed
priorities within that target law; they do not eliminate history-distribution
specificity.

## CM and production consequence

The literal Pro `CLOSED` ruling on v6 remains valid only for v6 and is now
superseded for production because the panel law changed. CM must terminate v6 at
preactivity infeasibility, preserve its zero-metric proof, and make no generator,
matrix, tolerance, sharing, threshold, or retry change. No v6 production command
is authorized.

V7 must receive a full same-conversation ChatGPT Pro ruling before any renewed CM
conformance or construction. Per Root scheduling, its frozen requester remains
unsent until the CRTO Pro request is terminal and Root separately releases the
Agentify slot. Only v7 `CLOSED` plus this owner's intake can permit Root to relay
the exact v7 card to CM. Gemini remains terminal no-turn/no-evidence and is neither
a closure source nor a retry path.
