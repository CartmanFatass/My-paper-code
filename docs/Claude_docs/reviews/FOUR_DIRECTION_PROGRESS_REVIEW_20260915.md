# Progress review: the four directions after the 2026-09-14 calibration

Date: 2026-09-15 (03:00 PDT). Author: Claude Code (Fable 5.1), at the owner's request. Read-only:
no experiment was run, no card or decision record was touched. Baseline for comparison: the
critical review and two-axis programme of 2026-09-14
(`FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md`,
`../plans/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md` with its evening addendum).

Sources read: every commit on `main` from 2026-09-14 00:00 to 2026-09-15 02:27 PDT (365 commits);
`PORTFOLIO.md`; the calibration, FSD-restart, TRDL-vacancy and pause decision records; evidence spec
§11.11; the audit ledgers for 09-13/14/15; the owner inbox counts; and for each of the four
directions the science card, result evidence, DM intake and owner-pause handoff of its latest
object. Reviewer arithmetic in §3.1 was recomputed from the published values.

---

## 1. Verdict in one page

Between the review landing (19:23 PDT on the 14th) and the completed pause (02:27 PDT on the
15th) the loop ran four directions for about seven hours, completed one bounded object in each,
and stopped cleanly at the owner's pause. Eighteen fresh training fits were launched and every one
was retained and read against its pre-registered rule. That is the disciplined behaviour the
review asked for, and the results are humbling in exactly the way replication is supposed to be:

| Direction | Object completed | Headline | What it did to the prior positive |
| --- | --- | --- | --- |
| FSD (untie k) | 2×2 interruption × batch, two independent blocks, eight fits | Interruption effect +0.049 J mean over four simple effects (3 of 4 positive); batch main effect −0.003 J; interaction −0.040 J in both blocks | Batch is not the explanation. The interruption signal survives but is still not resolved: primary I1280−D1280 was −0.026 and +0.085 J |
| ACVC | Learned proposer C vs flat recurrent MAPPO, one block, 4,096 episodes | C−MAPPO −0.011 J; F package−MAPPO +0.023 J, 22 of 64 adverse worlds | The learned proposer is at MAPPO level; only the fixed heuristic package beats MAPPO, by a small margin in one block |
| FOLR | Two fresh A−G blocks on Traffic Junction | (−5.83, −0.11), both negative | The old +5.30 positive did not recur. The direction's one positive is now best read as a draw |
| TRDL (new, off-axis) | B01 then independent B02 pair | B01 tail +0.035 J; B02 tail −0.002 J | The first pair's positive did not recur |

Three findings for the owner:

1. **The replication rule now works, and it is turning most single-pair positives into nulls or
   unresolved results.** This is the correct outcome; it confirms the review's §5.1 diagnosis that
   one-pair reads were noise-limited. FSD is the only direction whose signal survived a second
   block, and even there the two blocks disagree in sign.
2. **The headroom experiment (R1, revised order item 1) has still not been run on scenario 1.**
   The FSD DM produced a careful design note explaining why a plain MAPPO actor is not
   information-matched to the hierarchy, and proposed a "central-input flat" comparator; zero
   baseline fits were funded. ACVC's MAPPO block is the closest thing to R1 so far, on its
   cluster host, at one block.
3. **Every new object still trains at the early-budget regime** (FSD 40,000 steps, TRDL 512
   episodes) where absolute J is 0.1–0.45 against a reference of about 0.67. The addendum's
   power table was read and then set aside: FSD's card re-justified the 0.01 J minimum effect
   while noting it "does not become a power gate". At the measured SD of about 0.08 J the
   studies being run cannot resolve the effects they are looking for (§3.1).

The loop is executing well. What it is executing is still the old question set at the old
budget, with a replication step added. The next resume should change what runs, not how.

---

## 2. What the owner adopted from the 14 Sep plan, and what actually happened

The decision record `2026-09-14-two-axis-research-calibration.md` is explicit: the owner replied
"同意" to Codex's *corrected* four-point version of the plan, not to the draft wholesale.

| Plan item | Adopted? | What happened in the seven hours |
| --- | --- | --- |
| Same-host MAPPO / fixed-k HMASD baseline first (R1) | Yes, as priority 1 | Not run. ACVC ran a source assessment (A01) showing direct HMASD is not information-matched to its private actor, then one C vs MAPPO block on the cluster host. FSD DM wrote the scenario-1 baseline design; unfunded |
| FSD 2×2 attribution before any hazard sweep | Yes, as priority 2 | **Run in full**: two blocks × four arms. Result in §3 |
| Define Axis N (N-a / N-b / N-c) before choosing a benchmark | Yes, as priority 3 | Not started. FOLR spent its slot re-running its old A−G on Traffic Junction. VNFC was not re-opened |
| Consolidate by evidence relationship | Yes, as priority 4 | Not started; PORTFOLIO still lists 27 labels plus 5 parked |
| Restore FSD (R4/R5) | Yes, owner-direct at 20:33 | Done; FSD admitted as a fourth chain "without displacing" the other three |
| Archive 22 directions; five-seed gate; spec replacement; per-run owner approval; end unattended object selection | **No** | The three live DMs each recorded that they "rejected the addendum's unadopted universal approval, power/sample-size and estimator rules" |
| Variance-informed minimum effect (addendum correction 1) | Partly: §11.11 says "seed variation informs precision and study design" | FSD's card kept 0.01 J and chose n = 2 blocks "as a limited exploratory replication rather than a claim of adequate precision" |

Two things happened that the plan did not ask for. First, at 19:16 PDT, seven minutes before the
review was committed, Portfolio filled MGTAP's vacancy with **TRDL**, a distributional-critic
direction registered from the library on 09-12 and listed in the plan's archive table as off both
axes. It then received two Portfolio investments and four fits within four hours. Second, the
owner paused the loop twice (13:26 and again in the late evening); the second pause completed
cleanly with handoffs for all four directions.

---

## 3. Direction by direction

### 3.1 FSD: the 2×2 answered the batch question and sharpened the interruption question

Design and execution were exactly right: two independent blocks (seeds 772003, 772103), four arms
each, all eight fits pre-registered and retained, a verbatim reading rule, independent review
agreeing to 1e−12. The cost was 6,819 s of native wall on the CPU node.

| Contrast | Block 1 | Block 2 | Mean |
| --- | ---: | ---: | ---: |
| I1280 − D1280 (primary) | −0.026 | +0.085 | +0.029 |
| I128 − D128 | +0.003 | +0.135 | +0.069 |
| Batch main effect (MB) | +0.014 | −0.019 | −0.003 |
| Interaction | −0.030 | −0.050 | −0.040 |
| Package I1280 − D128 | +0.002 | +0.090 | +0.046 |

Readings the DM's intake states and this reviewer agrees with: batch size is not what produced
the earlier package gains (MB ≈ 0 with opposite signs); the interaction is negative in both
blocks, so interruption may help *more* at the small batch; the primary is above the card's
0.01 J but one block is adverse.

Reviewer arithmetic the loop's rules forbid it from doing, offered here as a descriptive pooling
across separately accepted objects, not as a new result:

| Set | n | Mean J | SD | 95% t-interval | Positive |
| --- | ---: | ---: | ---: | --- | ---: |
| Package I1280 − D128: five historical pairs + two new PKG values | 7 | +0.062 | 0.074 | [−0.007, +0.130] | 6/7 |
| Interruption simple effects in the 2×2 | 4 | +0.049 | 0.074 | [−0.069, +0.167] | 3/4 |

Seven package observations, six positive, mean +0.06 J, interval just touching zero. This is
the same picture as on 09-14 with two more points: *suggestive, not resolved*. The seed SD is
stable at about 0.075 J across both computations. Required paired sample sizes at 80% power,
α = 0.05, SD 0.08:

| Effect to detect | Pairs needed |
| ---: | ---: |
| 0.10 J | 7 |
| 0.06 J | 16 |
| 0.05 J | 22 |
| 0.03 J | 58 |
| 0.01 J | about 565 |

Two blocks per object at 0.01 J cannot end. The card's own text concedes this ("two blocks
provide early replication … not adequate power for a small interaction") and then runs it anyway,
because no rule stops it. Also unchanged: 40,000 training steps per fit, absolute J 0.31–0.45,
no MAPPO or fixed-k reference arm in the block. The DM's baseline note is good (it found that the
HMASD coordinator carries central information into the actor through the skill, so a plain
MAPPO actor is *less* informed, and proposed a central-input flat comparator), but it is a
design, not a run.

**What FSD should do next** (the DM's handoff lists three options and selects none):
- Drop the low-batch arms; MB ≈ 0 settles that. Run I1280 vs D1280 only.
- Raise the budget to the reference length or at least 3× (120,000 steps) so the comparison is
  between learners near competence, and record the learning curve at fixed checkpoints.
- Set the minimum effect at 0.05 J (the addendum's candidate) and commit to a sequential design:
  6 blocks now, read the interval, add 6 more only if unresolved. Sixteen pairs is the honest
  price of a 0.06 J effect at this SD.
- Put the central-input flat baseline in the same blocks as a third arm. That runs R1 and R5
  together on the same seeds, which is cheaper than two studies.

### 3.2 ACVC: a partial headroom answer; the learned proposer is at MAPPO level

A01 (zero exposure) established that direct fixed-k HMASD cannot be a same-information comparator
for ACVC's private-actor setting, and proposed ACVC vs flat recurrent MAPPO instead. Portfolio
funded one block (two fits, 4,096 episodes each, pinned `on-policy` code at `de66d7a`, bounded
tanh-Gaussian head added). Independent review before and after; costs 3,192 s.

| Package | J |
| --- | ---: |
| Learned proposer C | 0.322 |
| Fixed retrace package F | 0.357 |
| Own-dwell control | 0.345 |
| Flat recurrent MAPPO M | 0.334 |

C − M = −0.011 J, F − M = +0.023 J with 22/64 adverse worlds, F − own-dwell = +0.012 J (barely
past the 0.01 J band). The DM's pre-registered modal prediction was M above F (0.45); it did not
occur (Brier 0.665).

This is the first result in the repository with a maintained-code baseline on the same host at
equal exposure, and it partly closes the open question the addendum raised for ACVC ("does F−C
survive a competent C?"): at 4× the earlier budget C has climbed from 0.06–0.17 J to 0.32 J,
which is MAPPO level, and F is still +0.035 J above it. But it is one block and M is untuned. The
honest reading: the *heuristic* F adds about +0.02 to +0.03 J over either learned policy on this
host at this budget; nothing here says the learned proposer C is worth having.

ACVC remains off both axes. It should not receive further blocks unless the owner wants the F
heuristic itself, in which case one more block (with the same seeds for C, F, M) would say whether
+0.023 J is real. Otherwise its evidence tree is complete enough to be historical.

### 3.3 FOLR: replication resolved it, negatively

The card pre-registered two fresh A−G blocks (four fits, 11,218 s) with an ordered pattern rule.
Result (−5.83, −0.11): block 1 is strongly adverse to the augmented programme, block 2 is a
near-zero negative. With the earlier adaptive observations (A−Z −3.07, Z−G −4.44, replacement
BANK −4.83 and −6.64), the record now holds one positive A−G (+5.30) against six negatives across
related comparisons. The DM's intake says this "weakens reliance on the old isolated positive
without establishing stable G superiority", which is correct but understates it: the old positive
is best explained as a favourable draw. The Pro result review found no defect.

This is consistent with the 14 Sep review's §4: easy Traffic Junction at H = 20 does not require
persistent entity memory, so a null there is uninformative about the capability. FOLR has now
spent six blocks on that host. Its handoff says "next discriminator intentionally unselected";
the right selection is *no further Traffic Junction runs*. FOLR's question (keep vs reset survivor
state at roster change) belongs as the L3 ablation on whichever Axis N benchmark the owner picks
under N-a; that choice (calibration item 3) is the piece of work nobody has started.

### 3.4 TRDL: an off-axis direction that reproduced the one-pair pattern in miniature

TRDL was chosen by Portfolio to fill MGTAP's slot minutes before the review landed. It is a
32-quantile critic vs scalar critic comparison for lower-tail return on the five-UAV uniform host,
512 training episodes per arm, about 200–270 s per fit. Within one evening it went A01 (design) →
B01 (+0.035 J tail, above MEI) → Pro review → B02 investment → B02 (−0.002 J, inside band). Nine
audit rows, two Portfolio rounds, one Pro review, four fits. The DM's handoff correctly says B02
"weakens reliable retention of the unchanged Q32 recipe and favors scalar simplicity".

Three observations. It is off both axes (the plan's §C table put it in the archive group with
ACPS/CADC/CPCP/LCAC). It is trained to J ≈ 0.12–0.19, less than half of MAPPO's level on the
sibling cluster host, so the tail comparison is between two untrained policies. And it is the
cleanest demonstration yet of why one pair should never be read: B01's +0.035 J became B02's
−0.002 J with nothing changed but the seed. TRDL should be parked and its slot used for the Axis N
problem definition.

---

## 4. Process: what changed and what did not

**Changed for the better.** Pre-registered multi-block objects with ordered pattern rules (FOLR,
FSD); independent post-collection reviews recomputing every contrast; pinned external baseline
code (ACVC); explicit "not a power gate / not equivalence" language everywhere; the DM predictions
are being scored (ACVC's Brier 0.665 is an honest miss); clean pause handoffs with cleanup
receipts for all four directions. Nothing was rescued post hoc.

**Unchanged.**
- **Cadence.** 161 audit rows on 09-14 (67 `selection`, 92 `technical`), 42 new owner-inbox items
  that day, all `open`; the owner console has no review file after 2026-09-05. The loop still
  generates roughly one decision every four minutes and the owner's surfaces are write-only.
- **Budget regime.** Every fit is CPU FP32 at 1–4 threads on the WSL node; the 4070 sits idle by
  card design ("do not change to GPU for convenience"). The undertrained-learner problem (review
  §5.2) is partly a route choice: the cards choose a budget the CPU route can finish in minutes.
- **Minimum effect.** 0.01 J re-justified on every new UAV card; 1.0 return unit on Traffic
  Junction. §11.11's sentence that seed variation "informs precision and study design" has not yet
  changed a single card's n.
- **Direction count.** Four chains plus five parked plus 18 dormant labels. The owner admitted FSD
  as a fourth chain rather than swapping it for TRDL or ACVC. Two of the four live chains (ACVC,
  TRDL) are off both axes.
- **Axis N.** No work. The calibration's third item was the one that required an owner choice
  (N-a vs N-b), and the loop, correctly, did not choose for the owner. It needs that answer.

---

## 5. Recommendations for the resume

Stated as decisions for the owner. The loop will execute whichever are given.

1. **[DECIDE] Fund one combined FSD study instead of the three separate options in its
   handoff:** on scenario 1, three arms (central-input flat PPO, D1280, I1280), same seeds within
   a block, 3× the current budget (120,000 steps) with checkpoints every 20,000, six blocks now,
   minimum effect 0.05 J, sequential rule: read the 95% t-interval on I1280−D1280 at six blocks;
   add six more only if it straddles ±0.05 J. Cost about 6 × 3 × 3 × 1,000 s ≈ 15 CPU-hours, or
   an afternoon if the GPU route is allowed for this study. This runs R1 and R5 together.
2. **[DECIDE] Choose the Axis N formulation** (N-a within-episode change with joint training, or
   N-b train-N/test-N′). Until this is chosen FOLR and VNFC have no legal next object. Recommend
   N-a on the UAV host with UAV failure and replacement events, L0 first ("does a fixed-N masked
   MAPPO measurably degrade when joining events are added?"), FOLR's continuity question as the
   L3 ablation.
3. **[DECIDE] Park TRDL** (off-axis, B02 non-recurrence, undertrained regime) and **make ACVC
   historical** after its MAPPO block, with the F-heuristic observation recorded as the direction's
   closing evidence. Free those two slots for the Axis N chain and for the FSD study's baseline
   arm. Three live chains are enough; two would be better.
4. **[DECIDE] Set the scenario-1 minimum effect at 0.05 J and the Traffic Junction one at 2.0**
   (about one SD there), and instruct DMs that a card's n must be justified against the pilot SD
   on that host. This is the one §11.11 sentence that has not yet been applied.
5. **[DECIDE] Either use the console or retire it.** 42 unread items per day is not an
   intervention surface. If the owner will not reply, downgrade inbox items to the Chinese briefs
   only and stop generating P1/P2 items for ordinary results.
6. **Let the GPU route in for reference-length training.** The cards' CPU-FP32 restriction was
   written for bit-identity across hosts; a study that declares its own device and never compares
   across devices does not need it.

What not to change: the pre-registration, the ordered pattern rules, the retention of every fit,
the independent post-collection review, and the pause discipline. Those are working.

---

## 6. Answers to "how is it going"

The loop did what the calibration told it, in order, for the one item that needed no owner
choice (FSD attribution), and it did it well. It did not run the baseline experiment, because
every DM found a reason the baseline was not information-matched and stopped at a design note.
It did not start Axis N, because that needed the owner. It filled a free slot with an off-axis
direction and ran four fits on it. Three of four directions' prior positives failed to recur under
replication. FSD's signal is alive, unresolved, and still being tested at a budget and n that
cannot resolve it. The next step is the owner's: decisions 1 to 4 above.

---

## Addendum 2026-09-15 (03:15 PDT): further methodology and direction suggestions

Written in answer to the owner's follow-up question. These extend §5; nothing above is changed.

### Methodology

- **A/A calibration block on scenario 1.** Six D0 fits, identical recipe, different seeds, all
  pairwise differences. Measures the seed SD directly, checks the false-positive rate of the
  0.01 J rule, costs about one CPU-hour. Every UAV card then quotes that SD as a standing host
  fact and derives its n from it.
- **Pre-registered accumulation objects.** The rules forbid pooling across objects, so evidence
  never adds up (the seven FSD package observations in §3.1 are poolable only as reviewer
  arithmetic). Define an accumulation object: same host, recipe, arms and budget; a standing
  table to which each new block is appended and the interval updated. Pooling is legitimate
  when the entry rule was fixed in advance.
- **Learning curves, not only a final panel.** Evaluate at fixed step checkpoints on the same
  32 worlds. Gives an operational definition of competence (comparator curve has plateaued);
  a card run before plateau is labelled early-regime.
- **Factorial over sequential.** FOLR's A−G → A−Z → Z−G chased each last point; FSD's 2×2
  settled the batch question in one object. When two explanations survive, run the cross.
- **Audit selections only.** 92 of 161 rows on 09-14 were `technical`. Ledger and inbox carry
  selection rows; the Chinese brief is the only ordinary-result surface.
- **Owner-defaults file at resume.** Minimum effect per host, budget ceiling per object, device
  policy, the two axes and their benchmarks, answered once so the loop can run a week without
  waiting on the owner.
- **One UAV host.** Three directions used three UAV variants (scenario 1, cluster, uniform).
  Standardise on scenario 1 and port ACVC's reviewed MAPPO adapter (pinned `on-policy` at
  `de66d7a`, bounded tanh-Gaussian head, 585 lines) to it as the shared baseline, in place of
  the untested flat switch in `hmasd/baselines.py`.
- **Name the target paper.** Three figures: interruption gain on scenario 1 against flat and
  fixed-k baselines; gain versus hazard on the corridor; one external asynchronous benchmark.
  Every object maps to a figure or is declined.

### Active directions

- **FSD.** Reanalyse the existing eight fits for whether per-world gain correlates with the
  interruption count in that world (exploratory, free, first mechanism readout). Then the
  hazard prediction on the corridor, which has exact oracle margins; re-read the early-September
  corridor evidence first (not re-read in this session; the 09-05 park covered only the fixed-K2
  branch). Learned termination with a deliberation cost is the natural second treatment.
- **ACVC.** The remaining useful question is a curve: does F−C shrink as C trains past 4,096
  episodes? If it reaches zero the heuristic is a good prior and the direction closes cleanly.
  Otherwise historical.
- **FOLR.** No further Traffic Junction runs; keep-versus-reset becomes the L3 ablation on the
  Axis N benchmark once N-a/N-b is chosen.
- **TRDL.** Park. A tail question needs a host with real outcome variance and a competent scalar
  baseline; both are missing.
- **VNFC.** Re-open as the Axis N core under N-a: UAV failure and replacement events on
  scenario 1, L0 first with masked MAPPO on the shared adapter. Its earlier stops were
  engineering, not science.
