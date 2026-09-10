# RCLE B03 fresh1000 seed21 result evidence — 2026-09-10

**Technical acceptance: PASS; complete B/EXPLORE result.** The allocated fresh pair
and reference completed at source `806d378054774c5ab4f91d1acaba80292c660f67`.
[Card](RCLE_B03_FRESH1000_S21_SCIENCE_CARD_20260910.md) freeze `71b6ebbe1`,
[implementation/review/launch record](RCLE_B03_FRESH1000_S21_EXECUTION_20260910.md),
Portfolio PRO_FINAL A and Root's 2026-09-10 complete assignment supply its meaning.
This DM collected and accepted the technical result, then interprets it separately in
the [scientific intake](RCLE_B03_FRESH1000_S21_RESULT_INTAKE_20260910.md).
No extra initialization, fit, native probe, evaluation panel, retry or successor occurred.

## 1. Primary and complete native publication

| ACTIVE_CONTINUATION path | Init U | W1 U | W100 U | W1−W100 | Conditional SE | Reference U |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 0.6911458333 | 0.6907552083 | 0.2879964193 | 0.4027587891 | 0.0043809023 | 0.2483642578 |
| 12→8 | 0.7140869141 | 0.7104614258 | 0.3549316406 | 0.3555297852 | 0.0047544777 | 0.3107421875 |

The fixed equal-path Delta_U is **+0.379144287109375**, conditional SE
**0.0032325440196356403**, approximate conditional 95% interval
**[0.3728085008308891, 0.38548007338786083]**. W1/W100 primary U is
0.7006083170572917 / 0.3214640299479167. The relative reduction versus W1 is
54.1164410811%, or 15.165771484375 normalized unmet-demand ticks over the 40-tick window.

Same-scenario initialization gains are G_U_W1 **+0.0020080566406250043** and
G_U_W100 **+0.38115234374999996**. Both W100 paths exceed the .05 MEI; W1 gains remain
small on both. All 512 primary paired scenario differences favor W100, with worst
observed differences +0.2229167 and +0.109375 by path. These are evaluation observations
of one paired training instance, not 512 independent learned-policy replications.

Actual row arithmetic reproduced all emitted primary quantities. Each role has eight
cells with exactly 256 unique ordered indices 0–255. Distinct cell domains justify the
recorded combination of path SEs; no across-training-seed interval is estimated.

| Panel | Primary U | Primary Y | Primary tau | Primary F | Eight-cell U | Eight-cell Y |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Common init | 0.7026163737 | 0.2970568339 | 40 | 0.2837483724 | 0.7035680135 | 0.2966883977 |
| W1 final | 0.7006083171 | 0.2992490133 | 40 | 0.2816975911 | 0.7020182292 | 0.2983036041 |
| W100 final | 0.3214640299 | 0.6734364827 | 39.986328125 | 0.2557373047 | 0.3261683146 | 0.6694533030 |
| Reference | 0.2795532227 | null | 39.390625 | 0.2784179688 | 0.2867207845 | null |

Reference Y remains `ScriptedEpisodeResult has no Y; Y is null`, as prescribed. No
reference reward estimate is invented. U is post-event service; Y is the actual complete
64-tick reward. Both learned U and Y comparisons favor W100 in all eight cells.

| Cell | W1 U | W100 U | W100−W1 Y | W100−W1 tau | W100−W1 F | W100−reference U |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8→8 ACTIVE_CONTINUATION | .71319580 | .34587402 | +.35655212 | −.3359375 | −.03115234 | +.02419434 |
| 8→8 NEW_EPOCH | .71258545 | .36228027 | +.34543610 | −.2421875 | −.02856445 | +.02741699 |
| 12→12 ACTIVE_CONTINUATION | .68975423 | .28472493 | +.39700317 | 0 | −.02753906 | +.05002441 |
| 12→12 NEW_EPOCH | .69414876 | .30201823 | +.39131165 | −.08203125 | −.02900391 | +.04951986 |
| 8→12 ACTIVE_CONTINUATION | .69075521 | .28799642 | +.38079834 | −.02734375 | −.02272135 | +.03963216 |
| 8→12 NEW_EPOCH | .69007161 | .30148926 | +.37100728 | 0 | −.02441406 | +.04326172 |
| 12→8 ACTIVE_CONTINUATION | .71046143 | .35493164 | +.36757660 | 0 | −.02919922 | +.04418945 |
| 12→8 NEW_EPOCH | .71517334 | .37003174 | +.35951233 | −.24609375 | −.02329102 | +.03734131 |

All F means improve versus W1; the four final-roster-12 differences average
−0.0259195964. This does not rewrite old seed19's four adverse F differences or seed20's
mixed pattern. W100 still loses to the fixed reference on U in every cell; its primary
gap is +0.0419108073. The reference is neither a proven upper nor a tuned baseline;
H_A1 remains unidentified and no equivalence claim follows from this gap's size.

All 2,048 init and W1 recovery scores equal 40. W100 has 2,035/2,048 at 40 (99.3652%),
including 511/512 primary scenarios; its eight-cell tau mean is 39.88330078125.
Reference has 2,005/2,048 at 40 and mean 39.48828125. Tau is failure-coded at 40, not
uncensored recovery time. There is no same-scale reverse native tradeoff versus W1,
but this is not a useful general recovery result.

Full levels, all recomputed cell means, baselines, counts, native/source identity,
admissions, supervisor bytes and 23 verified retained-file hashes are in the
[result summary](RCLE_B03_FRESH1000_S21_RESULT_SUMMARY_20260910.json).
[SCENARIOS.csv](b03_fresh1000_s21_20260910/SCENARIOS.csv) retains all 8,192 rows;
[CURVES.json](b03_fresh1000_s21_20260910/CURVES.json) retains all 2,000 block records.
[Result figure](b03_fresh1000_s21_20260910/RESULT_VIEW.png) displays the retained training
curves and separately labels the fixed held-out endpoint; no intermediate panel was run.

## 2. Actual state, RNG, learner and output checks

All three summaries bind seed21, the reporting object
`RCLE-TBCFV-B03-ACTOR100-FRESH1000-S21`, source806d37805 and original namespace/block0.
Actual root is `f6a8584fe1948509b3501011e27178e8914f63fc794731e5d92b328415c7b6d8`;
block digest is `ce4b21d60e914cc5c8b872f4fcc3f5257be90aa300edd72aec924e1f54320330`.
The learned package is true FLEX-REKEY; reporting label and budget do not enter addresses.
Native source `18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819` and
artifact `5b918da7e23d7b65251fb20efcb6678e4a17e62538f6ebdedbda1d9e96221983` match all
three invocations and the retained S20 native identity. CPU FP64/thread1 and ABI remain.

Readback loaded checkpoint tensor dictionaries, with no model constructor. All 26,161
FP64 scalar values match within the fresh pair. The vectors differ from hash-verified
retained seed20: 25,440 components differ; unchanged components do not imply seed reuse.
Initial norm is 21.130979071752094. Independently measured final displacements are
W1 **0.7315465659977134**, W100 **4.412758384351883**, matching emitted values. Both final
dictionaries are finite FP64. No old checkpoint or fitted control was loaded by either fit.

All 1,000 block indices per arm are contiguous 0–999 and exactly match each flushed JSONL
record. Every block has 64 episodes/4,096 primitive ticks, eight cells × eight episodes,
one joint backward, a nonzero normalized parameter update, then the baseline update.
The maximum measured step-norm departure from .02 is 1.04e−17; summed path length is
19.999999999999662 per arm, distinct from net displacement. Reconstructing the .95/.05
baseline recurrence from eight zeros matches final vectors within 4.44e−16 / 6.66e−16.
There are 1,000 nonzero and zero zero-steps in each fit. W100's primary uses only this
new root's W1 panel, verified against the collected paired rows.

The source and preflight file readback match the frozen source. The prior source review
and two supplied fixture cases remain the proportional engineering checks; they were
not rerun. Actual collection/readback and primary arithmetic took 19.7625873s and
1.9542374s including the tensor import, with no scientific invocation. Historical
signal11 remains unresolved; a valid new run does not lift old quarantine or prove a cure.

## 3. Frozen reading rules applied verbatim

| Card observation | Card reading and recommendation | Observed application |
| --- | --- | --- |
| Delta_U≥.05 without a same-scale reverse native tradeoff | Local W100 service signal at this endpoint; retain absolute learning and reference outcomes, with no stable/causal claim. | Applies: Delta .3791, positive learning .3812, no reverse U/Y/tau/F mean tradeoff versus W1. |
| 0<Delta_U<.05 | Small local positive contrast; retain its exact magnitude and judge it alongside G_U and actual cost. | Does not apply: Delta exceeds .05. |
| Delta_U=0 or -.05<Delta_U<0 | No positive W100 contrast; retain zero/adverse value and conditional uncertainty. | Does not apply: both paths and aggregate are positive. |
| Delta_U≤-.05 or a material service/recovery loss | Counterexample to this fixed W100 law/budget; preserve all independent learning facts. | Does not apply versus W1. Reference losses remain separately reported. |
| abs(Delta_U)<.05 and either arm G_U≥.05 | Meaningful native learning without a same-scale law advantage; name every improving arm, not W100 superiority. | Does not apply: the contrast itself exceeds .05. |
| abs(Delta_U)<.05, both G_U<.05, recovery and reference deficit remain poor | End this pair and favor ending unchanged-law spending; return the recommendation to the proper decision tier. This does not erase a small positive value or close a family locally. | Does not apply: contrast and W100 learning exceed .05. The pair still ends as allocated. |
| Favorable Delta_U with W100 G_U≤0 | Report relative benefit with absolute deterioration; do not call it learning from initialization. | Does not apply: G_U_W100 is positive and large. |
| Opposite primary paths, U/tau tradeoff or intervals crossing interest scales | Mixed/undecided at the stated .05/tau4 scales; retain all paths and companions. | Does not apply: both paths positive, no reverse tau change versus W1, conditional interval entirely above .05. |
| Damaged training, information or primary | Report failure/counts and only intact narrower facts; no algorithmic polarity. | No observed dependent defect; complete trustworthy primary and exposure. |

These are the prospective 1,000-update branches. No historical 200-update rule or result
is rewritten. A/B objects have no consumption state. The scientific ceiling remains
one fresh matched training pair on this toy host at this fixed endpoint.

## 4. Counts, resources, time and retained scope

New training: 128,000 episodes / 8,192,000 primitive ticks / 2,000 joint backward-update
calls. Four panels add 8,192 episodes / 524,288 ticks. Total **136,192 episodes /
8,716,288 ticks / 2,000 calls**. Twelve model allocations comprise two fits and ten
untrained helpers. Each fit has 32,768,000 training agent-ticks and 8,192,000 claim
decisions; these are work counts, not independent learning instances. No selection
over checkpoints, candidate search, extra panel or replacement seed was performed.

Known B03 totals become **203,776 episodes / 13,041,664 ticks / 2,800 backward calls**,
plus the unchanged unknown old failed-W100 prefix bounded by 12,800 / 819,200 / 200.
Forty-two recorded scientific model allocations comprise seven started fits (one old
failure) and 35 helpers. Unknown prefix bounds are not measurements. Earlier 200-update
roots19/20 and this one 1,000-update root21 are not pooled as a same-endpoint population.

| Invocation | Actual-node admission UTC | Physical/effective available bytes | Complete wall seconds | Peak RSS KiB |
| --- | --- | ---: | ---: | ---: |
| W1 | 2026-09-10T16:57:55.134267Z | 15,205,617,664 | 389.18 | 593,716 |
| W100 | 2026-09-10T17:04:24.352215Z | 15,622,328,320 | 355.01 | 592,576 |
| Reference | 2026-09-10T17:10:19.403611Z | 15,600,209,920 | 2.70 | 428,896 |

All fresh admissions passed the same-node 4 GiB floors immediately before their runner.
All complete invocation times fit 600/600/30s. Sum invocation wall is **746.89s**;
the sequential chain, including admissions and publication, is **747.01s≤1250** and
is charged once. Supervisor PID3087467 finished exit0/tmuxfalse; its integer-duration
747s and exit2026-09-10T17:10:22Z agree at their precision. Monitor observed terminal
at17:10:40.9512461Z; Root resumed this same DM. No duplicate observation or execution.
Supervisor uptime later read during collection is not invocation wall time.

The complete 1,500s budget includes conservative prelaunch100s and a reserved postlaunch
150s for collection, analysis, publication and scoped closeout. Measured sequence plus
both conservative support quantities is **997.01s**, below that budget. This is a
conservative accounted charge, not a measurement that support actually used150s.
Individual collection/analysis timings are retained in the summary and analysis record;
closeout records its own actual work inside this same allowance. No allowance is reset
and no spare time authorizes another scientific invocation. Aggregate CPU and a common
whole-study calendar elapsed interval remain unmeasured. There is no §5 breach; directory
checks remain37.2665404/300s and no further test occurred.

Raw local result root is `temp/directions/roster_consistent_latent_exploration/exp/
b03-actor100-fresh1000-s21-20260910`; supervisor, transfer hashes, preparation and analysis
scripts remain under adjacent `fresh1000-s21-preparation/`. Exact remote worktree,
supervisor and source-only stage are the scoped closeout inventory in the execution
record. Preserve their complete bytes and source before removal; keep shared authoring,
native cache, old evidence and other scratch. Final preservation/removal facts are
appended to the scientific intake and existing closeout report, without another run.
