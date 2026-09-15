# Intake — FSD post-baseline-interruption direction decision (em:flexible_skill_duration:convergence)

Request `2026-09-15-fsd-post-baseline-interruption-convergence-01` (task `76af87097`, bound
handoff `c7e7c7c37`, references at `a8b0e332e` on `codex/fsd`). Author DM: the Claude hub
under the owner's 12:57 PDT scope instruction. Sent 2026-09-15 20:12Z, one accepted
submission (phase-1 record: the first call failed before any click, the retry clicked once and
returned a transient content-mismatch error, the observation call reconciled it with a real
provider message id). Response delivered at `codex/fsd 0712f85dfc5494db77142204837507b03b69086c`
("docs(fsd): deliver post-baseline interruption convergence review", 20:27:02Z):
[`archive/RESPONSE.md`](archive/RESPONSE.md) (blob `e667e0238`, 35,329 bytes, sha256
`adc67065…c0303`); Issue 10 delivery comment `5687625698` (20:28:01Z). Read from the immutable
commit; the response corresponds to this task (it cites TASK at `76af87097` and the packet
folder).

## Question posed

After the twelve-fit S object (SI1280_15 +.0098 J small_signed with a df = 3 interval
including zero; GAP_D −.045 and GAP_I −.035 with intervals including zero; six-block rollout-5
accumulation +.043 J), what is the direction decision: (A) conclude at the bounded claim, (B)
a tuned FLAT recipe sweep as a §11.7 headroom record, (C) more unchanged blocks, (D) a
thirty-rollout object, or an unlisted object?

## Formed decision

**A, `PRO_FINAL`: this exploration stage (declared recipes, host, fifteen-rollout budget) is
closed with the label `CLOSE_OBJECT`; no new object is selected; authentic D0 stays default;
the five-rollout limited optional I1280 scope (U, 2026-09-12) and the completed factorial's
original .01 J readings are unchanged.** Not "renewal is ineffective", not a stable FLAT win,
not equivalence, not a whole-direction closure; FSD ACTIVE/HIGH, slot and priority untouched.
The closing wording the node supplies for this intake:

> At the fixed fifteen-rollout endpoint over four independent training blocks, the high-batch
> I1280 − D1280 mean point estimate is small positive, `small_signed` under the .05 J
> importance rule; the block-level working-model interval includes zero and is not inside
> ±.05 J, so magnitude and direction remain insufficiently resolved. The D1280 − FLAT and
> I1280 − FLAT mean point estimates are negative and do not reach the card's stronger
> "negative gap with interval excluding zero" reading; they are untuned cross-information
> package gaps, not same-information headroom. The stage closes with every original
> observation retained and no automatic continuation by further unchanged blocks, a FLAT
> sweep or longer training. This establishes neither equivalence nor stable superiority or
> inferiority of any method.

Points the response fixes:

- **Corrections to the hub's intake and DIRECTION.md (applied below).** (1) "The renewal
  advantage is not maintained at fifteen rollouts" stands as a description of observed means,
  not as a decay law; no cross-panel interval was computed. (2) "FLAT is not below the
  package" is limited to the observed point estimates; both gaps' intervals include zero, so
  no non-inferiority, equivalence or stable advantage of FLAT is shown, and the private FLAT
  score gives no monotone guarantee for an untested central-input flat. (3) The hub's third
  inference ("within-trajectory movement dominates; block dispersion is not attributable to
  training seeds alone") is withdrawn as a variance decomposition: panels at different update
  positions are readings of different policies of one training process, the block SD cannot
  be split into a seed part and a trajectory-phase part from single-panel SEs, and the claim
  that more blocks would not help was not accepted. More independent blocks can improve the
  precision of the fixed fifteen-rollout contrast; they are not selected now because no
  choice currently needs that precision.
- Why not B: a three-setting one-fit FLAT sweep is a legitimate small development B, but a
  selected finite endpoint is not a certified reference and the private FLAT remains
  cross-information, so it cannot deliver §11.7 headroom; the untuned FLAT comparison on
  record already suffices to acknowledge the fifteen-rollout point gap. Why not C: valid but
  buys precision for a question no current decision depends on; the card makes a further
  tranche a Portfolio question. Why not D: a thirty-rollout comparison is a legitimate
  different-budget B, but "wait until movement stops" is not a defined endpoint and S already
  showed blocks not converging to a common ordering. Unlisted: direct fixed-k HMASD versus a
  central-input flat is a genuinely different same-information question, not shown to have
  higher net value now.
- Also fixed: the FLAT coordinator is still forward-called to assign the constant skill
  ("zero coordinator optimizer calls" is not "never called"); SI1280 is an implementation-
  path simple effect at fixed batch, not a pure timing effect; the factorial's MB/INT
  readings and the U five-pair differences keep their scope; the S object does not re-test
  U's package contrast (no D128 arm at fifteen rollouts).
- Authority boundary stated by the node: under spec §§8.1 and 11.9 a Direction Pro review
  is independent scientific review; a permanent family closure, PARK or slot decision is
  Portfolio's. "ACTIVE-idle" here means only that this question has no selected next object.
- Reopening facts: a real use that needs a choice among the existing recipes at a stated
  thirty-rollout budget; a same-information comparison with a defined legal execution
  interface, method definition and ordinary cost; or new legitimately obtained evidence or a
  reward/information/learner dependency fact that materially changes the reading. New
  independent blocks or another training length may be re-argued against a choice at that
  time; nothing is pre-booked or permanently forbidden.
- Costs: zero new scientific work in this round; the completed S counts and walls are
  restated at their measured scope (45,401.07 s under contention; the 24,000–30,000 s plan was
  not a cap).
- All twelve references read at `a8b0e332e`; no access gap.

## Conformance check (AGENTS §2)

The response decides the posed question at its declared class within the card, the Portfolio S
decision, evidence spec §§4, 7, 8.1, 11.4, 11.7–11.11 and the programme; it adds no lifecycle,
capacity, priority or specification change. No concrete conflict. Final for its node.

## Application

- Intake and DIRECTION.md wording corrected as listed; the Chinese brief's variance sentence
  corrected; card §9 carries the closing label. FSD ACTIVE-idle for this question with the
  reopening facts recorded in the direction handoff; no launch, no new object, no Portfolio
  question.
- Ledger row in `docs/research/portfolio/audit/2026-09-15.md`; P1 direction-decision owner
  item through `item.py` with the Chinese packet.
