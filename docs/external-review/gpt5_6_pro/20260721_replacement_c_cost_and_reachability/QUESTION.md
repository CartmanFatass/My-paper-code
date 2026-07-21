# Replacement C: Measured Cost And A_KEEP Reachability

Sent to GPT-5.6 Pro on 2026-07-21, before any formal run. Two of the facts that
supported adopting Replacement C turn out to be wrong, and both are corrections
against us rather than in our favour.

Prior exchanges:
`docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/`
`docs/external-review/gpt5_6_pro/20260721_replacement_c_scope_followup/`

---

```
Use the GitHub connector on private repository CartmanFatass/My-paper-code,
branch `aggressive`, commit fe60b48. The adopted contract is in
docs/project/IMPLEMENTATION_PLAN.md, section "Natural event-decision
consequence".

STATUS. Replacements A, B and D are implemented, reviewed and committed.
Replacement C stage 1 (candidate mark retention) is committed. A sequential
single-pair fork engine is built and passes its decisive test: the branch
matching the naturally taken action reproduces the originally collected
continuation exactly, on 40 of 40 coordinates, under full outcome equality
including the whole 80-step reward trace. That engine is not yet committed
because an internal review returned MODIFY on two guard defects.

Two facts that supported adopting C are now measured and both are worse than
stated. We would rather reopen the decision than build on them.

CORRECTION 1 - COST. The "roughly 18 minutes when batched" figure in the
previous exchange was ours and it was wrong by about an order of magnitude.
Measured on the target hardware with the real engine:

  one fork pair, sequential, single environment   1.06 s mean (0.59-1.27 s,
                                                  linear in 160 - fork_step)
  ~2,000 opportunity pairs                        ~35 min
  full per-opportunity forking at the registered
  256 held-out episodes per replicate             ~10,300 forks per replicate
                                                  ~3 h per replicate
  the 32 KEEP + 32 RENEW fallback you specified   ~6 min total

Part of that is redundant work we can remove: the pre-fork prefix is currently
re-derived from step 0 for every fork on the same episode, about 40 times per
episode. Reconstructing each episode once and snapshotting at each fork step
removes that factor. Even so, full per-opportunity forking remains hours per
replicate, while your fallback quota is minutes and needs no batched engine at
all.

CORRECTION 2 - A_KEEP MAY BE UNREACHABLE BY CONSTRUCTION. Measured on the
initialized EHC arm over a 16-episode held-out collection:

  natural non-CREATE opportunities                645
  of which natural KEEP                           10   (~160 per 256-episode
                                                       replicate, against the
                                                       adopted support floor
                                                       of 128)
  A_KEEP on those 10                              exactly 0 on every one
  minimum primitive top1-top2 logit margin        1.8e-04
  W_z bias magnitude at initialization            too small to move any argmax

So at initialization the KEEP stratum is both thin and degenerate: the
commitment bias cannot change a single primitive action, so U(KEEP) and
U(RENEW(candidate)) are identical and A_KEEP is identically zero. We cannot
measure the trained margin distribution before training exists, so we cannot
tell you whether this survives training. But if it does, LCB(A_KEEP) > 0 is
unreachable regardless of whether the fork engine is correct, and the
COMMITMENT_SUPPORTED branch can never be reached.

QUESTIONS.

1. Given correction 2, is Replacement C still worth its cost on this benchmark?
   We are willing to build it; we are not willing to build it if the gate it
   feeds is structurally unreachable.

2. If A_KEEP is unreachable but A_RENEW is measurable, does a one-sided gate
   preserve your scientific intent? You required both directions specifically
   so that a random non-degenerate head could not pass by systematically
   selecting the better branch in only one direction. Does dropping the KEEP
   direction reintroduce exactly the failure mode C was designed to exclude,
   or is A_RENEW alone still informative?

3. Should the 32 KEEP + 32 RENEW quota become the primary registered form
   rather than the fallback? You framed full per-opportunity forking as the
   default and the quota as an operational concession, but the measured ratio
   is minutes against hours per replicate, and the quota already exceeds the
   adopted 128-row support floor. Note the thin KEEP stratum interacts with
   this: at ~160 natural KEEP rows per replicate we may not always have 32
   eligible KEEP rows in every replicate, which your own rule says makes the
   run BENCHMARK_NON_IDENTIFIABLE rather than repairable.

4. If C is dropped entirely, what do A, B, D and G together establish, and what
   claim must we then explicitly NOT make? Concretely: with G showing external
   value against the mechanism-matched DUM control, B showing policy-generated
   K spread, and D showing executable action-distribution dependence on the
   mark, what separates COMMITMENT_SUPPORTED from REPRESENTATION_ONLY without
   C, and is that separation honest enough to report? You previously wrote that
   K-spread alone is insufficient because a memoryless random head passes it,
   which is the argument that motivated C in the first place.

CONSTRAINT. No result has been observed. Thresholds, estimands and the adopted
A/B/D battery are frozen once the formal run starts. We are asking whether to
register C at all, not how to interpret a result.
```
