Claim: in this one matched public-lifecycle Traffic Junction training pair, RESET's final native return exceeded RETAIN's by 2.0021875, above the declared absolute MEI of 1.0.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-B01 scientific intake — 2026-09-09

**Valid completed B/EXPLORE; `RESET_ABOVE_MEI`.** This is a finite trained-system
observation, with one independent matched training pair. The allocated pair is finished;
no successor is allocated or launched. A B has no C-style consumption state.

## 1. What I checked and the authority applied

I read the [frozen card §§1–6](FOLR_PUBLIC_LIFECYCLE_B01_SCIENCE_CARD_20260909.md) at
`97eb1683ee2a19d56918b80e2e92ff939328aa7a` against CM's accepted
[paired summary](FOLR_PUBLIC_LIFECYCLE_B01_RESULT_SUMMARY_20260909.json),
[execution evidence](FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md) and
[engineering result](FOLR_PUBLIC_LIFECYCLE_B01_ENGINEERING_RESULT_20260909.md) at
`ab24bdd8c4bca48479b12abbe53285e858affbef`. Both arms used exact committed/pushed source
`387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358`. Pro selected the information scope; Root's
subsequent explicit allocation, reproduced in P78 intake §8.4 and its recovery facts,
authorized this finite execution. These are separate authorities.

My direct checks were the result/card mapping, complete counts, both destination admission
receipts, external time reports, all 32 final returns per arm and their recomputed means.
I read the runner's final-checkpoint/evaluation selection and collection's native reward-sum,
20-action/terminal-pass and primary-reading paths. The final vectors also match the collected
per-arm summaries. The [analysis facts](evidence/2026-09-09-folr-public-lifecycle-b01-intake-analysis.json)
record the accepted input digest and computed quantities.

For changed semantic implementation I relied on the independent review and CM's credible
focused checks: actual departure/refill identity, native reward/RNG and inactive-removal
side effects, common event information, fresh entrants, trip-consistent preceding actions,
pre-GRU survivor reset, and acting/online/target unroll parity. The review left no material
finding. A controlled all-masked query exercised finite gradients and parameter movement;
no numerical repair was introduced to explain this outcome. I did not rerun the CM suite,
train a probe or re-evaluate either checkpoint. Tests support engineering conformance;
the complete native returns supply the performance observation.

Evidence-spec §11.8.2 applies verbatim:

> One real execution with a trustworthy primary measurement and clear comparison meaning may support a
> bounded B follow-up. It need not first be statistically significant, replicated on several seeds,
> positive on every seed or mechanistically localized. This is an investment signal, not stable
> superiority.

All-age owner reviews were empty at this intake boundary. Root's prior main-branch traces
for items `20260909-folr-002` and `20260909-folr-003` were brought into this checkout from
`56e5b6b2f9d748713e73731496f412cca68165d3`, preserving their actual integrated ledger locations.

## 2. Rule, observation and prediction check

The card's rule is applied verbatim:

- `d >= 1.0`: `RETAIN_ABOVE_MEI`, a preliminary trained-system advantage at this configuration.
- `d <= -1.0`: `RESET_ABOVE_MEI`, the opposite-sign result, retained on the same terms.
- `-1.0 < d < 1.0`: `WITHIN_MEI`, no MEI-sized observed gap; not an equivalence statement.

Here `d = J_RETAIN - J_RESET = -2.0021875000000002`, so the second branch applies.
Absolute MEI 1.0 was frozen before implementation/results, on the native progress/collision
reward scale. Neither the MEI nor the endpoint is changed after seeing the result.

| Final greedy native returns | RETAIN | RESET |
| --- | ---: | ---: |
| All-32-episode mean | 2.104375 | 4.1065625 |
| Conditional episode sample SD | 6.888063 | 7.996783 |
| Minimum / maximum | -11.71 / 16.31 | -14.05 / 18.44 |
| Negative-return episodes, preserved | 14 / 32 | 8 / 32 |

The [endpoint CSV](evidence/2026-09-09-folr-public-lifecycle-b01-run-endpoints.csv) has
exactly one row per training arm. Running the scientific-tools `summarize_runs.py` with
`--paired --baseline RESET` yields the [run-level description](evidence/2026-09-09-folr-public-lifecycle-b01-run-analysis.json):
one paired difference and no estimable training-run SD. The 64 final rollouts are conditional
evaluation observations, not 64 independent learners. The common training seed 7801 pairs
initial randomness; the separate common final-evaluation seed is 107801. Policy-dependent
traffic/RNG paths are allowed to diverge, so episode index is not treated as an identical
exogenous event tape. No confidence or stable-population claim follows from the episode SDs.

The final checkpoint was selected in advance after 5,000 episodes/4,969 updates. There was
no periodic evaluation, best-checkpoint selection, repeat or omitted adverse outcome.
Training native-return means were -5.044872 for RETAIN and -5.225858 for RESET: RESET's
final advantage does not establish improved return throughout training. Those exploratory
training returns are not a competing primary or a headroom baseline.

**Prediction check:** the DM's recorded leading prediction was `WITHIN_MEI`; it missed the
observed branch. RESET's possible forgetting/learning-path benefit was an alternative on
the card, not the leading prediction. Owner prediction: **not taken (unattended)**.

## 3. Exposure, receipts and complete cost

| Quantity | RETAIN | RESET |
| --- | ---: | ---: |
| Training episodes / native ticks | 5,000 / 100,000 | 5,000 / 100,000 |
| RMSprop steps, trainable actor and mixer | 4,969 | 4,969 |
| Final evaluation episodes / native ticks | 32 / 640 | 32 / 640 |
| Training births / departures | 20,925 / 7,417 | 21,550 / 8,584 |
| Training survivor opportunities / resets | 45,511 / 0 | 46,929 / 46,929 |
| Final evaluation births / departures | 138 / 40 | 154 / 80 |
| Final evaluation survivor opportunities / resets | 304 / 0 | 337 / 337 |
| Complete invocation wall seconds | 770.69 | 746.89 |
| External peak RSS, KiB | 656,364 | 670,480 |

Birth/departure counts include terminal native events and exclude initial episode births.
Survivor opportunities require an actual next native action; terminal computational clears,
common entrant/episode clears and replayed rows are excluded. RESET's actual rule-application
counts equal its opportunities, including an already-zero incoming vector. Different event
totals arise on each learned policy's native path; event normalization is not substituted for
the full-episode reward. Exposure is nonzero in both training and final evaluation.

The whole pair has 200,000 real training ticks, 9,938 positive-lr RMSprop steps, 64 final
greedy evaluations/1,280 evaluation ticks, and 201,280 total native ticks. The card's computed
work remains 66,783,360 online-plus-target replay GRU row forwards plus 1,056,720 acting rows,
with terminal passes included computationally. These rows are not independent samples.
Per-arm nominal lr×steps is 2.4845, not measured parameter displacement.

Both exact invocations ran on `hmasd-wsl-node` in
`/home/wu/hmasd-worktrees/folr-public-lifecycle-b01-387a40f3`, CPU FP32 learner, native NumPy
environment arithmetic, Torch compute/interop threads 1/1. Recorded versions are Torch
2.7.0+cu118 and NumPy 1.26.3; the CUDA-enabled build does not mean a GPU learner ran.
Immediately preceding destination receipts passed physical/effective available-memory floors
of 4,294,967,296 bytes: RETAIN had 15,635,152,896 and RESET 15,634,956,288 available bytes.
Cgroup-specific fields are unavailable and remain null; ordinary memory/resource facts were
measured. CM's exact commands, original handles, start/exit times and artifact digests are
in execution evidence. Both supervisor exits are zero, and local/remote summary/checkpoint
digests agreed at collection. The owner interruption affected a wait only; the same detached
RESET handle was reconciled and collected without another launch.

Each complete external wall is below its 1,800s cap; sum **1,517.58s** is below 3,600s.
Aggregate reported user+system CPU is **1,518.71s**, a separate quantity. Supervisor first-start
to last-exit elapsed is **1,625s**, including inter-arm collection/admission sequencing and
rounded timestamps, excluding prior staging and later collection. Runner pre-publication
walls 729.723850s/704.480158s have a narrower boundary; they do not replace external time.
No cause is assigned to the boundary difference from timing alone.

New source is 753 non-test lines, including 101 runner lines, within 2,000/600. Only the
four card-named §4 event counters were added. Focused checks used 10.5991404s; CM's direct
artifact readbacks bring the supporting check/readback total to **13.4333944s**, below 300s.
No section-5 engineering budget was breached. For this selected execution window,
complete scientific wall plus those checks is **1,531.0133944s per one valid paired result**;
there were two admitted scientific invocations and zero failed scientific invocations.
Earlier direction history, source/review/staging/collection and DM intake cost are not
aggregated into that number. No new target exposure occurred during this analysis.

## 4. Bounded scientific reading and retained alternatives

The observed chain is native departure/activation → true continuing physical car ownership
→ same locally masked observation and public E/own-B actor cues → own trained survivor-state
rule before GRU → online/target recurrent Q-learning and partner co-adaptation → the complete
native reward sum. Entrants and same-step slot replacements begin fresh in both arms;
survivors keep current observation and trip-consistent preceding action. Primitive gamma,
fixed 20-step cooperative episodes and no terminal bootstrap are unchanged. There is no
claim about a new entity's optimizer state, semi-Markov duration or post-terminal control.

**Strongest support:** a trustworthy above-MEI native-return difference, equal declared
training/selection exposure and hundreds of actual final survivor-control opportunities.
The comparison is between policies trained under their own rules, not damage applied only
at evaluation to RETAIN-trained weights. It gives a preliminary RESET advantage on this
specific lifecycle-visible configuration.

**Strongest contradiction to a broader claim:** there is one training pair, wide conditional
rollout spread and lower RESET training-return mean. We cannot distinguish useful forgetting
from finite optimization/partner-learning paths or conditional evaluation variation. Nor does
one observed RESET advantage show that useful survivor history is absent or that retention is
generally harmful. The original retention-benefit rationale did not win this primary.

For the unexpected sign, I reused the verified question-driven corpus evidence in
[P68 §3](FOLR_P68_MULTISTEP_REENTRY_INTAKE_20260908.md#3-question-driven-library-evidence-and-what-it-changes)
and [P77 §2](FOLR_P77_CAMA_SURVIVOR_SOURCE_INTAKE_20260909.md#2-verified-source-to-consequence-path):
CAMA `MARL-0409`, page 3 elements 155–156 and Appendix G.2 pages 16–17 elements 497–507,
supports local GRU history and this multi-step traffic host; Sable `MARL-0485`, pages 2–3
elements 2235–2241 and page 33 elements 8722–8724, supports a competent history-using
alternative with episode resets. Neither compares this within-episode survivor intervention
or explains its RESET sign. The prior verified 190-record Inst-sci snapshot and exclusion of
My-lib synthetic fixtures remain the stated coverage; no current corpus expansion is claimed.
This evidence changes the interpretation by keeping generic history and reset timing distinct,
not by supplying a causal explanation for the new return gap. No new comparator is invented.

Tuned headroom remains absent on this information variant. B04 differs in observations,
actions, information and budget and is not a matching baseline. B04's positive/transient,
adverse-seed and within-MEI facts, P77's unchanged-interface no-ready result and historical
FOLR/DISH pauses remain intact. Claim ceiling: no typed-state novelty, strictly-self ancestry,
information necessity, mechanism localization, original-CAMA performance, stable superiority,
transfer, UAV validation or Portfolio disposition.

## 5. Decisions this intake produces

1. **Object tier, result acceptance.** Options: (a) accept the intact bounded
   `RESET_ABOVE_MEI` reading; (b) quarantine for a concrete primary/information defect;
   (c) discard the opposite sign. Recommend/select **(a)**: no such defect is present, and
   the frozen rule preserves either sign. **Owner-delegated decision (unattended,
   2026-09-03 instruction): (a).** Technical success alone is not the basis of this choice.
2. **Object tier, next-discriminator recommendation.** Options: (a) one new independent
   matched training pair with the same comparison and final evaluation; (b) no immediate
   follow-up; (c) expand into mechanism search, tuning or repeated evaluation of these weights.
   Recommend/select **(a) as direction-local scientific advice**, because the credible
   opposite-sign primary can justify the small independent-seed measurement under §11.8.2–3.
   It would distinguish a recurring finite-training signal from this single pair more directly
   than more rollouts of the same checkpoints. **Owner-delegated decision (unattended,
   2026-09-03 instruction): (a), recommendation only; no new allocation or launch.**
   A future frozen pair would retain every seed/sign; no all-positive requirement, tuning,
   exact upper or causal diagnosis is a prerequisite. Known work would again be two arms ×
   5,000 training episodes × 20 ticks and two × 4,969 updates, plus 32 final episodes/arm;
   B01's 1,517.58s is a same-workload point estimate, not an upper bound. Concrete new seed,
   cap and card would be fixed only within a new allocation. Root owns that capacity decision.
3. **Current execution boundary.** Return this completed pair and recommendation to Root for
   integration and its next allocation decision. No additional invocation is authorized here;
   no family is closed, parked or recast, no C is promoted/consumed and no priority/lifecycle
   change is made. No direction-tier Pro question is needed merely to intake this B result.

The [audit](../../portfolio/audit/2026-09-09.md) records the choices. They are ordinary object
decisions, so no separate P1/P2 item is manufactured. The existing new-card item is traced to
actual completion; its prior Root integration history is preserved. The
[Chinese owner brief](../../portfolio/owner/briefs/vap_folr_core/2026-09-09_public_lifecycle_b01.md)
reports the prediction miss, bounded sign and absence of a new allocation.
Owner flag for this intake: **none**; the earlier scope-selection close call remains in
its original item and audit row. No critic dissent is overruled.

Both scientific processes are terminal. All per-arm summaries, checkpoints, logs, time reports
and admission receipts are collected under the matching local `temp/directions/vap_folr_core/exp/`
roots. Root owns integration and remote detached-worktree reclamation after verified evidence
preservation. The shared direction authoring checkout remains the designated checkout.

Automatic approval review rejected CM's cleanup of its owned
`temp/directions/vap_folr_core/test/public_lifecycle_b01_check02` and `check03` directories:
`rejected: blocked by policy`. The directories remain, CM is the creating owner, and any later
cleanup requires a changed permitted runtime path; no bypass or repeated rejected action was
attempted. This non-scientific cleanup blocker does not damage the accepted primary.
