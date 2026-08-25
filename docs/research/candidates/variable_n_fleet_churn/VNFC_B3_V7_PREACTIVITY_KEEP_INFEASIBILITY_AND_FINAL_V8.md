# VNFC-B3 v7 preactivity KEEP infeasibility and final v8 panel-law attempt

Owner: `direction:variable-n-fleet-churn` Explorer Manager  
Treatment family: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Non-instantiable revision: `SP-RDA-MATH-CLOSURE-20260812-07`  
Final prospective panel revision: `SP-RDA-MATH-CLOSURE-20260812-08`  
Scientific activity: not started  

## Owner conclusion

Do not send v7 to Pro and do not launch it. V7 made shared robust-regret
admissibility nonempty and single-valued, but its first required training bank is
still empty because that admissible set is deterministically incompatible with
the registered KEEP physical-return meaning. This is panel-law infeasibility, not
a negative learned-bid or SP-RDA result.

One final single-axis repair is scientifically justified. V8 defines the physical
KEEP/SWITCH construction objective first and then minimizes worst pre-service
regret within each semantic objective's near-optimal class. It does not tune any
threshold to the proof values: it retains the existing `0.01` KEEP gap, `0.10`
SWITCH gap, `0.01` near-best kept-return class, and `0.02` regret slack. It also
replaces the numerically unsafe raw mixed-radix objective with an exact certified
prefix tie-break.

V8 is frozen but is not yet eligible for External Pro. CM must first run the exact
full-bank certificate-only feasibility proof. If any bank is incomplete or the
proof cannot fit 90 minutes/2 GiB, the current B3 host/panel law ends: no v9,
threshold adjustment, matrix change, history unsharing, raw-cap expansion, or
semantic-objective rescue. The learned-bid/SP-RDA family remains a credible
hypothesis for a new host with naturally feasible lifecycle histories.

## Accepted v7 preactivity evidence

For `(1601, training, 6->9, raw 0..95)`:

- the v7 shared-regret law itself was feasible: every raw base had exactly four
  histories satisfying `Delta<=Delta_star+0.02`;
- zero of 96 raw bases qualified after the complete certificate routine because
  the selected KEEP history failed `R^v-K^v<=0.01`;
- 2,400 certificate-equivalent calls produced no treatment metric;
- for raw zero, none of the four admissible histories passed the KEEP gap across
  all variants; selected gaps were approximately
  `[0.07384,0.03566,0.04233,0.02986]`, each above `0.01`; and
- `Delta_star` over the 96 bases ranged from approximately `0.06347618` to
  `0.08128700`.

The facts show that “choose globally robust compromise, then ask for KEEP” is the
wrong ordering on this host. They do not justify raising `0.01` toward the
observed gaps. The mixed-radix note is also accepted: a raw base-4 integer rank
under a `1e-9` floating absolute dual-gap is not a reliable exact tie certificate.

## Exact v8 owner delta

Retain the individual pre-service values and define

`Delta(p)=max_v(S_star^v-S_pre^v(p))`.

For KEEP:

1. maximize the worst-variant all-survivors-kept return `t_K(p)` over locally
   feasible shared histories, obtaining `t_K_star`;
2. within `t_K(p)>=t_K_star-0.01`, minimize `Delta(p)` to obtain
   `Delta_K_star`; and
3. within `Delta(p)<=Delta_K_star+0.02`, select `p_KEEP` by exact prefix
   feasibility in ascending handle/task-code order.

For SWITCH:

1. among locally feasible histories different from `p_KEEP` on a survivor,
   minimize `q_W(p)=max_v Q^v(p)`, obtaining `q_W_star`;
2. within `q_W(p)<=q_W_star+1e-9`, minimize `Delta(p)` to obtain
   `Delta_S_star`; and
3. within `Delta(p)<=Delta_S_star+0.02`, select `p_SWITCH` by the same exact
   prefix law.

The unchanged final semantics require, for every variant,
`R(p_KEEP)-K(p_KEEP)<=0.01` and
`R(p_SWITCH)-K(p_SWITCH)>=0.10`, plus local role feasibility. Thus a bank cannot
pass merely because the lexicographic objectives exist.

For each tie-break, visit handles in ascending opaque rank and codes
`0,1,2,DUMMY=3`; fix the first certified-feasible code under all frozen scalar
constraints. Never optimize raw mixed-radix rank numerically. The routine uses 24
scalar/return solves plus at most `8|P|` prefix feasibility solves, hence at most
168 calls per raw base at `|P|<=18`, and at most 860,160 calls over the frozen
5,120 raw bases.

All matrices, seeds, schedules, raw laws/caps, one shared history per pair, later
observations/actions/PPO/SP-RDA/comparators, Stage-1/Stage-2 estimands, gates,
inference, scaling, and no-rescue definitions remain v6/v7. This is one panel-axis
correction, not a new learned treatment.

## Claim effect and portfolio disposition

A positive v8 result is conditional on two class-specific constructed history
laws: near-best worst-variant kept return for KEEP and minimum survivor retained
coverage for SWITCH, with pre-service regret minimized inside each class. It may
not claim that either history is individually pre-service optimal, produced by an
operational pre-churn allocator, or representative of deployed history.

The direction remains promising only because the central family-eliminating
question is intact and unanswered: does an agent-associated learned bid channel
beat reward-blind ZERO/FROZEN/HANDOFF priorities and cyclic reassociation at one
held-out N through the same sparse allocator? The strongest alternative remains
that HANDOFF or residual-demand arithmetic is sufficient, or that any learned
gain is specific to this constructed history distribution.

Portfolio rule: invest in v8 only through the bounded certificate proof. A full-
bank pass preserves the direction for same-conversation Pro closure and later CM
conformance. Any bank failure ends this host/panel line without judging the family;
reconsideration requires a genuinely new host whose lifecycle histories are
naturally feasible, not another certificate threshold or ordering change.

## Exact Root-to-CM consequence

CM may implement and run only the card's `Root-to-CM v8 pre-Pro certificate-
feasibility packet`. It must scan every training and conclusion bank and pass only
with at least 32/96 and 24/64 successes respectively, within 90 minutes/2 GiB and
the 860,160-call cap. It must run no network, arm, return panel, timing audit,
Stage 1, Stage 2, B1/B2 mutation, or Git action.

V7's frozen requester remains preserved but permanently unsent/superseded. No v8
Pro requester is prepared yet; that is intentional. Only after a complete v8 bank
pass and same-owner intake may this owner prepare a full v8 question for the
existing VNFC Pro conversation. CRTO retains the next Pro slot. Gemini remains
terminal no-turn/no-evidence and is not a review or rescue path.
