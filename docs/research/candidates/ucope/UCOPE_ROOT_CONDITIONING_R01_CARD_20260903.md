# UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01 — card

- Direction: `ucope`
- Object id: `UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01`
- Evidence class: **`B/EXPLORE`**
- Written: 2026-09-03, **before** any run of this object. Owner decision D.16 (commit `f56546867`),
  following the accepted competence object (compliance note D.15, commit `cd0276949`).
- Frozen by: this card. It awaits the owner's prediction (section 12) before launch.
- **Not run.**

## 1. Question

The competence object closed on branch `C-C — CEILING_COMPETENT_LEARNER_NOT`: with both stages
whitened at the ten-fold budget and `n = 81,920`, the exact two-stage solve was competent in 6 of 6
policies and the learner in 3 of 6. `C-C`'s own reading names the **root learner** as the binding
constraint — the one component this chain has only ever solved exactly. Two numbers from that run
point at it directly:

| Measured 2026-09-03 in the competence run | Value |
| --- | --- |
| Root design condition number `kappa` | **5014.086**, identical in all six policies |
| Tail design condition number `kappa` | 721.061 – 732.927 |
| Root `d_learned` inside `eps_L = 0.10` (whitened arm) | **2 of 6** |
| Tail `d_learned` inside `eps_L = 0.10` (whitened arm) | 5 of 6 |

The root design is roughly **seven times worse conditioned** than the tail, and the root parameters
are the ones that fail to arrive. Whitening was the remedy that worked on the tail.

**With the tail stage held fixed, does whitening the root design close the root learner's gap, and
does that reach competence?**

## 2. Claim ceiling

`B/EXPLORE`, on 3 seeds x 2 folds of one arm on one frozen eight-context host. This object cannot
establish acquisition polarity, COUNT/RAW polarity, stable superiority, a seed-population effect,
anything about `FT-XF-FLEX`, or anything about variable `k`, variable `N`, MARL/UAV, transfer,
safety, deployment, flight, energy or real-world QoS. It is a statement about the root stage of
these six policies under this criterion.

## 3. The fixed tail stage — **re-trained identically**, not handed over

All three arms share **one tail model per policy**, and that tail is the competence object's
`WHITENED-10X` tail: the whitened linear tail learner at `n = 81,920`, 1,600 updates, `lr 3e-3`,
batch 256, with the recovered raw coefficients.

**Decision: the tail is re-trained inside this object's own run, not read from the competence run's
coefficients.** Reasons, in order of weight:

1. **The competence run wrote no checkpoints.** That is deviation 3 of
   `UCOPE_COMPETENCE_WHITENED_R01_RESULT_EVIDENCE_20260903.md`: the runner evaluates once at the
   final root update and persists no model. Its `beta_tail` values exist only inside a **gitignored**
   run record under `temp/`. Binding a frozen object to an unversioned artifact in an ignored tree is
   exactly the dependency the evidence layer exists to prevent.
2. **Re-training is deterministic and therefore free of scientific cost.** Same frozen index law,
   same seeds, same folds, same `build_arm` initialisation, same unshuffled cyclic batch windows,
   `torch.use_deterministic_algorithms(True)`, one process, the same 4-thread cap: nothing in the
   tail path consumes RNG after initialisation.
3. **It converts the hand-off into a check.** Because re-training should reproduce the recorded
   vectors, the object can *verify* that its tail really is the competence run's tail instead of
   asserting it.

**Tail-reproduction integrity item (gating, §4).** The re-trained `beta_tail` must match the
competence run's recorded per-policy values to `max abs difference <= 1e-6`. The expected value is
exactly `0.0`; the tolerance admits float32 reduction-order noise and nothing more. A failure means
the tail stage is not the one this card names, so the object has not run its declared assignment and
**quarantines under §6.2** — it is not re-run with changes.

Recorded for the check, from
`temp/directions/ucope/exp/competence_whitened_r01_20260903/complete/run-record.json` (the
`WHITENED-10X` arm), the tail-determined quantities this object inherits unchanged:

| Policy | tail `d_learned` | `min_forced_PROBE_tail_agreement` |
| --- | --- | --- |
| seed 00 fold 0 | 0.095253 | 0.611559 |
| seed 00 fold 1 | 0.052249 | 0.611559 |
| seed 01 fold 0 | 0.034964 | 1.000000 |
| seed 01 fold 1 | 0.029579 | 1.000000 |
| seed 02 fold 0 | 0.183077 | 0.520727 |
| seed 02 fold 1 | 0.027485 | 1.000000 |

## 4. Arms — the root stage, three treatments of one design

All at `n = 81,920` tail rows and `163,840` root rows per policy, the three B1 seeds
`ucope-scout-r01-b1-fresh-{00,01,02}`, both group-disjoint folds, the frozen `FT-XF-BC`
initialisation, batch 256, `lr 3e-3`, and the ten-fold root budget **3,200 root updates**. The root
targets are the frozen package (`probe_primitive + max over K_TRAIN of Q_tail`) built once per policy
from the **fixed tail**, so all three arms are solving the *same* root problem and differ **only** in
how the root design is coordinatised.

1. **`RAW-ROOT-10X`** — the control: the published root path, no whitening, exactly as the competence
   object's root learner ran in its `RAW-10X` arm but now sitting on the whitened tail. *This
   combination — whitened tail, raw root — has not been run before, and it is where this object's new
   information is.*
2. **`WHITENED-ROOT-10X`** — the treatment: the root design whitened **from its own training rows
   only**, at float64, under the contract carried unchanged from the conditioning object —
   `max abs(L L^T - G) <= 1e-10` and `lambda_min(G) > 1e-6`, checked before any optimizer step
   exists. `G = Z^T Z / n = L L^T`, `Z~ = Z L^-T`, `beta~ = L^T beta`, and parameters are recovered to
   raw coordinates by `beta = solve(L^T, beta~)` before every reported statistic.
3. **`EXACT-ROOT-SOLVE`** — the ceiling: the root normal equations solved exactly **on the same
   targets**, i.e. on the fixed tail. Outcome-free reference, `d_learned = 0` by construction, no
   optimizer trajectory, excluded from the exposure line. Note this ceiling is **lower** than the
   competence object's `EXACT-SOLVE`, which solved *both* stages exactly: this one inherits the
   tail's residual by design, which is what makes it able to discriminate mechanism (ii)(a).

### The root whitening contract, with the numbers already measured

The competence run measured the root Gram in all six policies and got the **same** numbers every
time:

| Quantity | Contract | Measured 2026-09-03 (all six policies) |
| --- | --- | --- |
| `kappa(G_root)` | — | **5014.086** |
| `lambda_min(G_root)` | `> 1e-6` | **3.083845e-04** |
| `max abs(L L^T - G)` | `<= 1e-10` | **2.776e-17** |

The invariance across policies is structural, not a coincidence: the root design's rows are a fixed
multiset of the eight context vectors crossed with the behaviour strata, so at balanced `m` every
policy's root Gram is the same matrix, whichever fold it is built from. The predicted factorisation
error is `O(kappa * eps_fp64) ~ 5014 * 2.2e-16 ~ 1.1e-12`, and the observed `2.776e-17` is well
inside it. The contract is expected to pass comfortably; it is checked and recorded per policy
regardless, before any optimizer exists, because that is the gating item.

## 5. Differentiating measurement

Per arm and per policy:

- **The frozen competence predicate `C_even`**, unchanged and evaluated exactly as
  `evaluation.evaluate_policy` does: `all_scores_finite AND all_choices_unique AND
  exact_eight_context_oracle_root_vector AND max_expected_regret <= 1/50 AND
  min_forced_PROBE_tail_agreement >= 19/20`, on even held-out support `K_eval = {2,4,6,8}` at the
  final root update. **This is the branch statistic.** Its five components are reported separately.
- **The root-restricted predicate `C_root`** = `all_scores_finite AND all_choices_unique AND
  exact_eight_context_oracle_root_vector AND max_expected_regret <= 1/50` — `C_even` without the
  purely tail-determined agreement gate. Reported per arm per policy for the reason section 8 gives.
  **It is not the branch statistic under this card as frozen.**
- `d_learned_root = max abs(beta_root_arm - beta_root_star)` against `eps_L = 0.10`, where
  `beta_root_star` is the exact root solve **on this object's own targets** (the fixed tail's).
- `d_objective_root = max abs(beta_root_star - beta_root_star_exact_tail)`, where the second term is
  the exact root solve on targets built from the *exact* tail solve. This is the frozen measurement of
  **how far the learned tail's residual moves the root optimum** — the direct quantitative test of
  mechanism (ii)(a). It cannot differ between arms.
- Gradient ratios `g_learned / g_star` in raw coordinates for the two training arms, with
  `g_star = ` the infinity-norm gradient of this object's root objective at
  `beta_root_star_exact_tail`. Descriptive, deciding nothing, for the reason section 5 of the
  competence result gives.
- **The per-context breakdown, machine-generated and written into the run record** (the competence
  object had to recompute this after the fact): per context, the root action against the oracle
  action, the per-context expected regret, and the per-context forced-PROBE tail agreement, with the
  target context `LINKED-p17_20-c9_100` reported explicitly. Every `WHITENED-10X` competence failure
  bound at that context.
- One machine-generated **exposure line** over arms 1 and 2: per-coordinate displacement of the
  recovered raw **root** vector from the frozen root initialisation of the same seed and fold. The
  raw per-coordinate ceiling at this budget is `3,200 x 3e-3 = 9.6`.

## 6. Mechanisms

**(i) Root conditioning binds.** The root design's `kappa = 5014.086` is what stops the root
parameters arriving, exactly as the tail's `kappa ~ 726` did before whitening. Whitening the root
puts AdamW on an isotropic problem, the root vector arrives, and the root-side components of the
predicate come good where the raw root fails. Prediction under (i): `WHITENED-ROOT-10X` clears the
root-side components in substantially more policies than `RAW-ROOT-10X`, and reaches the ceiling.

**(ii) The root's failure at the target context is not conditioning.** Two named sub-mechanisms,
which this card's ceiling arm distinguishes:

- **(ii)(a) target-carrying.** The frozen root targets are built from the *learned* tail
  (`probe_primitive + max over K_TRAIN of Q_tail`), so wherever the tail's residual is large the
  targets themselves are wrong, and the root optimum computed on them is displaced. The target
  context is precisely where the tail's agreement collapses (`0.520727`–`0.611559`). Under (ii)(a) no
  root coordinate system helps, because the root is solving a displaced problem: **the exact root
  solve fails too**, and `d_objective_root` is large.
- **(ii)(b) the clip in whitened norm.** Whitening roughly doubled the clipping rate on both stages
  in the competence run (root: 1,054 of 19,200 whitened against 525 raw). If the gradient clip at
  norm `1.0` acting in whitened coordinates is what truncates the root trajectory, then the ceiling
  is clean and only the *learner* fails; `d_objective_root` is small and `d_learned_root` is not.

Prediction under (ii): the whitened root does **not** close the target context — under (a) neither
does the exact root solve; under (b) the exact root solve does and the learner does not.

## 7. Reading rule — written before data, branches ordered by effect size

Thresholds, all fixed here, all carried unchanged from the competence card. `C_even` is the frozen
predicate and introduces no new threshold. "Majority" is **at least 4 of 6** policies.
`eps_L = 0.10`. The branch statistic is `C_even` on the two named arms and the ceiling.

Branches, evaluated in this order; exactly one applies.

- **`R-A — WHITENED_ROOT_COMPETENT`.** `WHITENED-ROOT-10X` satisfies `C_even` in **all six**
  policies. Reading: mechanism (i) completely. Root conditioning was the whole remaining
  obstruction.
- **`R-B — WHITENED_ROOT_MAJORITY_CEILING_CLEAN`.** Not `R-A`, but `WHITENED-ROOT-10X` is competent
  in **at least four** of six **and** `EXACT-ROOT-SOLVE` is competent in all six. Reading: mechanism
  (i) substantially, with a residual the ceiling does not share.
- **`R-C — CEILING_COMPETENT_ROOT_LEARNER_NOT`.** `EXACT-ROOT-SOLVE` competent in all six,
  `WHITENED-ROOT-10X` competent in fewer than four. Reading: mechanism (ii)(b). The root *problem* is
  solvable on these targets and the root **learner** is the binding constraint; the clip in whitened
  norm and the unshuffled cyclic batch order are the named suspects.
- **`R-D — CEILING_NOT_COMPETENT`.** `EXACT-ROOT-SOLVE` is not competent in all six. Reading:
  mechanism (ii)(a) — the root problem as posed is not solvable to competence, because the targets
  built from the learned tail carry its residual. `d_objective_root` and the per-context breakdown say
  how far and where. This is a statement about the two-stage target construction, not about any root
  optimiser.
- **`R-E — UNCLEAR`.** Any other combination. Reading: report every number, name what is
  unexplained, propose no successor on the strength of an `R-E`.

Descriptive and deciding nothing: `C_root`, `d_learned_root`, `d_objective_root`, the gradient
ratios, the whitening numbers, the per-context breakdown, the exposure line, `RAW-ROOT-10X`'s
competence count, and any per-seed spread. At three seeds no arm-comparison polarity,
stable-superiority or seed-population claim is available, so `RAW-ROOT-10X` is a control and never a
comparator for a claim.

## 8. Structural note the owner should read before predicting — the rule above is degenerate

**This section changes nothing. Sections 4 to 7 are frozen exactly as decision D.16 specifies. It
records a property of that specification that is visible before the run and that the owner should
know when predicting or amending.**

`C_even`'s fifth component, `min_forced_PROBE_tail_agreement`, is computed from the **tail model
alone** — `evaluation.evaluate_policy` derives it from the tail scorer's selected periods, with no
reference to the root. This card fixes one tail for all three arms. Therefore:

1. **The agreement component is arm-invariant in this object.** Its six values are already known
   (section 3): `0.611559, 0.611559, 1.000000, 1.000000, 0.520727, 1.000000` against the gate
   `19/20 = 0.95`. Three of the six policies fail it before any root arm exists.
2. **No arm — including the ceiling — can satisfy `C_even` in more than 3 of 6 policies.**
3. Consequently `R-A` (6 of 6) and `R-B` (>= 4 of 6) are **unreachable by construction**, `R-C`
   requires a ceiling competent in all six and is therefore also unreachable, and **`R-D` fires with
   probability 1**, conditional only on the tail stage reproducing (section 3's gating check).

A second, milder point: `WHITENED-ROOT-10X` is whitened tail plus whitened root, which is exactly
the competence object's `WHITENED-10X` arm. Its `C_even` result is therefore already observed —
3 of 6, on policies `[false, false, true, true, false, true]`. That is not wasted: it makes arm 2 a
**bit-reproduction check** of the competence run, and a disagreement with those recorded flags would
be a reproducibility finding worth more than the branch. If arm 2's flags differ from
`[false, false, true, true, false, true]`, the rule is still applied as written, but the result
document must report the discrepancy as its headline and claim no mechanism.

**Where this object's information actually is**, under the frozen rule: in the contrast between
`RAW-ROOT-10X` (whitened tail, raw root — never run) and `WHITENED-ROOT-10X` (already observed at
3 of 6) on the root-side quantities — `C_root`, `d_learned_root`, the oracle root vector, the regret
gate, the per-context breakdown — and in `d_objective_root`, which measures mechanism (ii)(a)
quantitatively and is independent of the branch.

**A non-degenerate alternative, offered for the owner to freeze instead — not adopted here.** Replace
the branch statistic with `C_root` (section 5), keeping the branch names, the order, the majority
threshold of 4 of 6 and `eps_L` identical:

> `R'-A`: `WHITENED-ROOT-10X` satisfies `C_root` in all six. `R'-B`: not `R'-A`, but at least four of
> six and `EXACT-ROOT-SOLVE` satisfies `C_root` in all six. `R'-C`: `EXACT-ROOT-SOLVE` in all six and
> `WHITENED-ROOT-10X` in fewer than four. `R'-D`: `EXACT-ROOT-SOLVE` not in all six. `R'-E`: anything
> else.

`C_root` is arm-sensitive: on the competence run's whitened arm it would read 5 of 6 (only seed 02
fold 0 fails, on the oracle root vector and `max_regret = 0.033103`), so `R'-A` through `R'-D` are all
reachable and the rule discriminates the two mechanisms as intended. It also matches the object's
question, which is about the root stage.

**Adopting the alternative is a card amendment, to be made by the owner before the run**, after which
this object is launched under the amended card. It is **not** a change this card makes, and it is not
a change to be made after seeing data — an outcome-informed rewrite would be a different scientific
object. If the owner leaves the card as frozen, the object still runs, and the result document will
publish `R-D` together with the full explanation above and the root-side numbers that carry the
actual content.

## 9. Launch conditions (spec §11.4) and budget

Still gating: the central 4 GiB physical and effective memory admission immediately before the
workload; the §4 integrity items — group-disjoint folds, the odd-training / even-held-out
separation, no read of B1 or audit runtime rows, fresh counter-addressed data at the competence
card's index law (`i = OFFSET + j`, `OFFSET = 1,000,000`, `j = 0 .. 40,959`), **root whitening from
training rows only**, and **the tail-reproduction check of section 3 at `1e-6`**; the §5.2 nonzero
transition / update / evaluation counts reconciled exactly; and one machine-generated exposure line.
Recorded and never gating: working-tree cleanliness of the bound source inventory, the absence of a
dedicated A/RECON performance assessment, execution topology, resource telemetry (a failed
measurement sets `resources_unmeasured` and downgrades, never annuls), and the direction's own
acquisition and COUNT/RAW sequencing locks. Learner-side instrumentation failure quarantines under
§6.2.

**Budget: under 10 minutes**, on the measured cost of the competence run, which did strictly more
work — two tails and two roots per policy — in `110.970 s` wall. Here: `40,960 x 8 x 3 = 983,040`
episodes generated (about `70 s`); **one** tail per policy, `6 x 1,600 = 9,600` tail updates, shared
by all three arms; `2 x 6 x 3,200 = 38,400` root updates on the 7-parameter root model at batch 256;
six exact root solves, six exact-tail reference solves and the Cholesky factorisations in
milliseconds; 3 arms x 6 policies x 8 contexts exact evaluations with the frozen sampled diagnostic.
Outputs under `temp/directions/ucope/exp/root_conditioning_r01_<date>/`.

## 10. What each branch means for the direction, the locked acquisition question and the COUNT/RAW lock

The direction records `PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED` and
`COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE`. Under the section-11 recast those are **the direction's
own sequencing choice, recorded and not §11 gates**, and **this object opens neither of them.** What
each branch would place in front of the owner:

- **`R-A`** would satisfy the COUNT/RAW lock's stated precondition — competence exists on a learner.
  Whether to open the lock, and whether the acquisition evaluation is then registered as a separate
  named object on the competent policies, are owner decisions this card does not pre-empt. (Section 8:
  unreachable under this card as frozen.)
- **`R-B`** would leave the precondition partially met at best; a majority is not the ladder's
  `B_COMPETENT` rule and not a population claim. The honest next step would be the arm-to-ceiling gap.
  (Section 8: unreachable under this card as frozen.)
- **`R-C`** would keep both locks where they are and make the **root optimiser** — the clip in
  whitened norm and the unshuffled cyclic batch order — the direction's next named object. It would
  also establish that the two-stage target construction is sound. (Section 8: unreachable under this
  card as frozen.)
- **`R-D`** would keep both locks where they are and move the question to the **two-stage target
  construction**: the root is being asked to fit targets that carry the tail's residual, so the
  direction's next object would be about the tail's residual at the target context, or about a target
  package that does not propagate it. This connects directly to the margin-scaled falsifier the review
  holds in reserve.
- **`R-E`** would keep both locks where they are and propose nothing.

No branch supports `PARK`, promotion, retirement or a lifecycle change on its own.

## 11. Relationship to the objects already closed

| Object | Branch | What it fixed |
| --- | --- | --- |
| Training-target diagnostic R01 | `D1` | the tail objective is right; per-policy variance was the problem |
| Optimiser-and-conditioning R01 | `O-B` | tail conditioning is the dominant cause, budget secondary |
| Competence (whitened) R01 | `C-C` | with both handled, the ceiling is competent 6 of 6 and the learner 3 of 6; the learner binds |
| **This object** | — | which part of the **root** stage binds: its conditioning, its optimiser, or the targets it is given |

The whitening discriminator R01 is retired as `SUPERSEDED` (`DIRECTION.md`, 2026-09-03) and is not
part of this chain.

## 12. Prediction requested from the owner

Please pick one before the run.

- **Option (i) — root conditioning binds.** Whitening the root design closes the root learner's gap
  and the whitened root reaches competence where the raw root fails.
- **Option (ii) — the root's failure at the target context is not conditioning.** Either the frozen
  root targets built from the learned tail carry the tail's residual into that context, so not even
  the exact root solve closes it (sub-mechanism (a)), or the gradient clip acting in whitened norm
  truncates the root trajectory, so the ceiling is clean and only the learner fails (sub-mechanism
  (b)). Please say which sub-mechanism if you hold one.
- **Option "unclear".** Neither picture holds cleanly and `R-C`, `R-D` or `R-E` is the honest result.

Please also say, in the same reply, whether the card stands as frozen or whether the section 8
alternative (`C_root` as the branch statistic) is to be adopted as an amendment before launch.
