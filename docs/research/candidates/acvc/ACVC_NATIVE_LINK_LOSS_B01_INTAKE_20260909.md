# ACVC-NATIVE-LINK-LOSS-B01 — P78 scientific intake

Date: 2026-09-09. **Valid complete B/EXPLORE; mixed native result.** T improves over C and G,
but loses to fixed retrace F. This is one matched training instance, master 8901, with 32 paired final joint episodes.
The primary stronger-fixed summary is **−0.0290806349 J**.
It establishes neither repeatability across training instances nor superiority to the strongest
fixed control. The sole P78 comparison is complete; no scientific allocation remains.

## 1. What I checked against the card

The prospective authority is [card §§1–7](ACVC_NATIVE_LINK_LOSS_B01_SCIENCE_CARD_20260909.md)
at `7ec1849b739cc51f55dee41878da980b8f245b4d`, under Root's explicit P78 allocation and the
accepted [complete Convergence response](pro_packets/20260909_native_link_loss_convergence/archive/RESPONSE.md)
at `2d914ab8b6238b2eb76bb07b90972945a23f7a68`. Evidence-spec §§4, 11.4, 11.7 and 11.8 control.
The exact scientific source is `f429021166eefa9ee6d9b275ac8c91f1b13a8f28`; accepted-handle
record is `a648c0c02`; the complete CM return is `60359f70da4af88831bd0940b4e6ebaeb10dfc81`.

I read the [E0 technical evidence](ACVC_NATIVE_LINK_LOSS_B01_RESULT_EVIDENCE_20260909.md)
against the frozen card, the published summary and all episode/update records, and the
admission, collection and process-exit receipts. Focused source inspection covered coordinate
binding, actual-command feedback, sampled-proposal retention, recurrent gate likelihood and
masking, and report formulas. The independent semantic review and 11 focused synthetic checks
cover the information/identity, credit, private RNG and G-containment boundaries. Its requested
nonzero recurrent-chunk test was repaired and passed. I accepted that focused evidence without
repeating the suite or invoking a native environment, model, evaluator or additional episode.

Read-only arithmetic over the collected bytes is retained in
[dm_analysis.json](native_link_loss_b01_p78_20260909/dm_analysis.json). It checked unique
arm/phase/episode identities, the frozen paired reset ranges, every episode's 256 steps and
`S=256J`, the complete update count, published means/SEs and all reading labels. The DM verified
the summary and episode-file digests against collection acceptance; CM verified all six remote
scientific files against their collected copies. The primary measurements agree to the published
precision. No source/card mismatch or reward, information, comparison, training or measurement
defect was found.

| Required quantity | Observed |
|---|---:|
| New training instances per learned arm | 1 (matched T/G, master 8901) |
| Training episodes | 1,024 (512 T, 512 G), all retained |
| Final episodes | 128 (32 each T/G/C/F), all retained |
| Team steps | 294,912 |
| Explicit scored resets | 1,152 |
| Constructors / additional unscored constructor resets | 4 / 4 |
| Two-episode rollouts / Adam calls | 512 / 2,048 |
| Base agent forwards / learned-gate collection forwards | 1,474,560 / 1,392,640 |

T/G training reset identities are 890101000–890101511. All four final panels use
890102000–890102031 with their declared separate action streams. The [all-outcome episode
file](native_link_loss_b01_p78_20260909/episodes.jsonl) and [rollout records](native_link_loss_b01_p78_20260909/updates.jsonl)
preserve every outcome. Common initialization and reset identities match; T/G are a matched pair,
not two independent replications of a treatment effect.

The scientific-tools run summarizer was applied to the two learned endpoints in
[independent_training_endpoints.csv](native_link_loss_b01_p78_20260909/independent_training_endpoints.csv),
paired against G. Its [run-level output](native_link_loss_b01_p78_20260909/run_level_summary.json)
correctly reports n=1 and undefined training-population SD for each arm and their difference.
C/F are fixed controls and were not entered as additional trained runs. The episode SEs below
are separate conditional measurements; UAVs, primitive steps and optimizer calls do not enlarge n.

## 2. Verbatim reading rule and complete native result

Card §4:

> Reading rule (apply separately to each declared contrast, keeping the actual signed number):
> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**. Separately report
> whether each primary exceeds 0.25 S. Both primary UPs support a meaningful preliminary learned
> correction signal; any favorable T−G adds only finite-budget structured-package evidence. A T−G
> gain cannot rescue a T loss to C or F. If G contains the gain, recommend describing a learned
> correction package. Positive sub-MEI results remain positive; WITHIN is not equivalence. Opposite
> native signs remain adverse even if link or gate statistics improve. Full outcomes and uncertainty
> inform the next unallocated recommendation; no branch automatically launches another instance.

Units remain native episode sum `S` and mean `J=S/256`. The inherited `0.25 S` equals
`0.0009765625 J`; the card's independent MEI is `0.01 J = 2.56 S`.

| Arm | Mean J | Mean S |
|---|---:|---:|
| T: structured learned gate | 0.2344827282 | 60.02757842 |
| G: containing generic learned gate | 0.1975140229 | 50.56358987 |
| C: always apply frozen proposal | 0.1673014978 | 42.82918345 |
| F: always retrace on opportunity | 0.2635633631 | 67.47222096 |

| Declared contrast | Mean difference J | Conditional SE J | Mean difference S | Card reading | >0.25 S |
|---|---:|---:|---:|---|---|
| T−C, primary | +0.0671812303 | 0.0115352194 | +17.1983950 | UP | yes |
| T−F, primary | −0.0290806349 | 0.0105070125 | −7.4446425 | DOWN | no |
| T−G | +0.0369687053 | 0.0111757440 | +9.4639885 | UP | yes |
| G−C | +0.0302125251 | 0.0128636323 | +7.7344064 | UP | yes |
| G−F | −0.0660493402 | 0.0106243579 | −16.9086311 | DOWN | no |

The primary summary is `min(mean(T−C),mean(T−F)) = −0.0290806349 J`, because F has the
larger fixed-panel mean. It has no selected-max SE and is not an episode-wise oracle. Each
reported SE is the sample SD of 32 paired joint-episode differences divided by sqrt(32),
conditional on this one fitted pair and fixed base. UP/DOWN are the prospectively defined
effect-size readings, not statistical significance or training-population conclusions.

One additional **outcome-informed descriptive comparison**, F−C=+0.0962618653 J
(conditional SE 0.0115855474), makes the observed strength of the fixed retrace control explicit.
It uses existing episodes, changes no primary or reading rule and is not a new selected endpoint.
T−C and T−G are actual native gains; T−F and G−F are actual native losses. None is replaced by
a local cue statistic, and the T−G gain does not rescue the failed stronger-fixed comparison.

## 3. Learner exposure and bounded mechanism reading

| Arm / phase | Eligible choices | Retraces | Retraces / eligible choices |
|---|---:|---:|---:|
| T / training | 51,834 | 31,421 | 60.62% |
| T / final | 3,338 | 2,447 | 73.31% |
| G / training | 50,076 | 27,085 | 54.09% |
| G / final | 2,629 | 1,276 | 48.54% |
| F / final | 3,670 | 3,670 | 100% |

Training opportunities were 7.91% of T's and 7.64% of G's 655,360 agent decisions; the full
primitive-row PPO denominator remained unchanged. Every recorded optimizer update had nonzero
eligible rows. All eligible proposed/retrace commands were distinguishable. T's gate moved
2.8876708 in parameter norm (relative 0.3087580); G's moved 1.9953898 (relative 0.1512762).
Zero-initial scalar projections moved by absolute norms 0.2287203 for T and 0.0513526/0.0459827
for G's common/residual paths. These are gate-specific measurements, separate from critic movement.
C performs no anchor matching, so its zero opportunity counter means **not measured**.

This rules out absent gate updates, absent eligible choices and zero total gate movement as
descriptions of this attempt. It does not establish successful optimization or identify why F won.
The F>T>G>C panel ordering is descriptive; eligible-event and retrace fractions arise on different
arm trajectories and cannot establish a monotone causal dose-response curve.

The surviving event-to-action chain is joint motion and interference → loss of an acting UAV's
own observed link → a bound private opportunity to apply or retrace its realized displacement →
new joint geometry/assignment → unchanged native reward. It uses one preceding observed coordinate,
private state and actual sent-command feedback, with fixed membership and primitive-time credit.
The strongest new support is T's above-MEI native gain over C and G, together with F's large gain
over C. The strongest new contradiction is that **both learned gates lose to F** despite genuine
learner exposure. Own-link loss can still represent a beneficial teammate handoff, and retrace
does not restore teammates' geometry. Neither the cue's causal contribution, memory necessity,
F's optimality nor G's optimization failure was isolated by these arms.

For the unexpected T−G gain alongside T−F loss, the question-driven literature route reuses
the verified local evidence in [P68 intake §3](ACVC_NATIVE_REENTRY_P68_INTAKE_20260908.md):
DACOM's fixed timing/kinematic controls (`MARL-0006.json`, pp.4–6, including entries 186–188,
227, 255, 264 and 286) and CoDe's history/comparator grounding (`MARL-0066.json`, pp.3–6).
That recorded real-corpus retrieval supports retaining competent fixed and same-information
history controls; it supplies no diagnosis of this new UAV effect. The current Convergence
response's containment discussion also distinguishes functional inclusion from finite-budget
optimization. The P78 native comparisons determine this intake; no novelty or literature-based
performance verdict is inferred, and no new retrieval or implementation burden is added.

## 4. Prediction check and owner instructions

| Prospective DM point prediction J | Observed J | Signed prediction |
|---|---:|---|
| T−C +0.002 | +0.0671812303 | correct |
| T−F +0.004 | −0.0290806349 | incorrect |
| T−G −0.001 | +0.0369687053 | incorrect |

One of three predicted signs matched. The expected small positive primary summary was wrong:
the observed summary is DOWN. Both-primary-positive (p=0.55) and both-primary-UP (p=0.20)
events were false; T−G-UP (p=0.15) was true. The analysis retains point errors and single-event
probability scores as prediction bookkeeping, not a calibration study. Owner prediction:
**not taken (unattended)**; no prediction reply was present.

The clean-boundary owner review command returned no unapplied instructions in both the direction
checkout and main on 2026-09-09. There was no new review to apply or mark answered. Existing
owner entry `continue-low-priority (20260904-acvc-009)` in
[the 2026-09-05 audit, line 20](../../portfolio/audit/2026-09-05.md) remains applied.
R02/R03 boundaries, recasts 2 and lowest sequencing remain; Portfolio lifecycle/priority and formal
UAV-validation status are unchanged. The [Chinese owner brief](../../portfolio/owner/briefs/acvc/2026-09-09_native_link_loss_b01.md)
reports the valid result; the next-choice close call is the only new P2 owner item from this intake.

## 5. Receipts, complete work and engineering boundary

The sole accepted remote handle was `acvc-p78-native-link-loss-8901-f42902116`, on configured
`wsl_4070` / `hmasd-wsl-node`, exact source worktree `/home/wu/hmasd-worktrees/acvc-p78-f42902116`.
Fresh joined actual-node admission measured physical/effective available memory of
15,630,286,848 bytes before the runner. The staged frozen DENSE/8201 checkpoint matched
`f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
CM alone observed and collected the accepted process. It exited 0 at 2026-09-09T11:12:13Z;
the terminal supervisor receipt records completion and no live process remains.

| Machine work, including required checks and actual process exit | Seconds |
|---|---:|
| All focused checks, including the repaired check | 14.2369735 |
| Complete scientific process | 359.17 |
| Complete logical study bill | **373.4069735** |
| Complete T arm, including charged shared work | **199.8208294** |
| Complete G arm, including charged shared work | **215.5117409** |

The 300 s check, 1,800 s per-arm and 3,600 s study caps all pass. Shared checks/startup/C/F/
publication/exit are charged conservatively to both arm bills as specified; the other learned
fit is not charged to an arm. The scientific process includes trailing publication before actual
exit. The serial machine critical path and sum of the declared invocation walls are 373.4069735 s;
human authoring/waiting and network staging are separate. Peak RSS was 552,292 KiB. Aggregate CPU
work and scratch high-water are unmeasured and no dependent claim is made. Actual execution was
CPU/FP32, Torch intra/inter-op 1, on the declared node.

Engineering-scope §4 additions: **none**. Accepted new non-test source is 469 lines, including
a 149-line runner and minimal launch shell; no §5 budget breach occurred. A prelaunch synthetic
publication check needed its owned scratch parent created before passing; its work is included.
Runtime policy rejected cleanup of
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/test/p78_publication_20260909`
with the stated error **`rejected: blocked by policy`** for `Remove-Item -LiteralPath <that path>
-Recurse -Force`. CM retains cleanup ownership and has not bypassed or repeated the rejection.
The retained scratch is a technical cleanup limitation, not native evidence or scientific polarity.

Before launch, a non-login remote source fetch failed without scientific exposure; the configured
login route fetched and verified the exact source. The remote tracking-reference collision between
`origin/codex/acvc` and historical `origin/codex/acvc/next-object-20260904` was retained for Root's
normal reconciliation. It did not change the verified source or produce a second scientific run.

The complete local runtime copy is
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/exp/native_link_loss_b01_8901_p78_20260909`.
T/G final checkpoints were checked by CM for arm/master, finite tensors and 11,425/26,306 gate
parameters. [Collection acceptance](native_link_loss_b01_p78_20260909/collection_acceptance.json)
records their hashes and the remote-to-local copy checks. Root owns accepted integration and
remote execution-worktree reclamation after preserving these verified bytes. The shared direction
authoring checkout remains the designated checkout. No accepted attempt was retried or resumed.

## 6. Decisions this intake produces

**Object-tier acceptance.** Options: (a) accept a valid complete mixed B with every contrast;
(b) quarantine for a concrete integrity defect; (c) describe T−G as overall success. Recommend
and select **(a)**: the trustworthy native primary includes a loss to F, with no technical gap
requiring quarantine. Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.
This does not consume a C object, close the object family or change a Portfolio disposition.
The sole allocated scientific submission is complete, and none remains.

**Object-tier next recommendation, unallocated.** Options: (a) recommend one fresh matched T/G
training instance with unchanged C/F controls, heads, budget and reading rule; (b) recommend no
further unchanged learned-gate comparison after this adverse stronger-fixed result; (c) tune or
expand exposure now. Recommend and select **(a), advice only**. The next observation should decide
whether the T−F disadvantage and T−G gain recur under fresh independent training randomness.
It must retain every outcome; no requirement that the new instance improve is imposed.

This is a **close call** with (b). The card says native losses argue against the unchanged package,
and F's observed advantage supplies that argument. A single fitted pair nevertheless leaves
training variability unmeasured, while T−C and T−G show large native effects and the accepted
implementation completed in 373.41 billed seconds. One unchanged fresh pair can change the
finite-budget recommendation without adding tuning or a causal prerequisite. This justification
does not turn the current T−F loss into a success or alter the frozen reading rule.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a), record the next recommendation
only; no successor card, master, code, run or Pro Send is allocated or created here**. The same
prospective work would be two 512×256 fits plus four 32×256 final panels: 294,912 team steps,
2,048 Adam calls, 512 rollouts, 1,152 scored resets and four constructor resets. Base/gate forward
bounds and intrinsic coordinate work remain card §5; recurrent replay/backward/critic work and
G's extra path remain additional real work. The measured 373.4069735 s is a cost reference, not
a guaranteed forecast; proposed complete caps stay 1,800 s per learned arm and 3,600 s overall.
There is no nested candidate search, extra panel or cost pilot. Root retains capacity and
allocation decisions, including existing lowest sequencing; no Portfolio action is taken here.

Both automatic decisions are in [the audit ledger](../../portfolio/audit/2026-09-09.md), at
`acvc-native-link-loss-b01-p78-acceptance-20260909` and
`acvc-native-link-loss-b01-p78-next-20260909`. The next recommendation is exposed through
the Chinese [decision packet](ACVC_NATIVE_LINK_LOSS_B01_NEXT_OWNER_PACKET_20260909.json)
and CLI-created [close-call item 004](../../portfolio/owner/inbox/2026-09-09/20260909-acvc-004.json). Publishing it does not wait
for an owner reply. Accepted mechanism-level science is updated in [DIRECTION.md](DIRECTION.md).

Owner-packet recommendation, verbatim:

> 建议记录一次原样T/G新训练配对作为下一项尚未分配的观察，保留强固定回退F与所有原生结果。这与停止原样学习投入难以明显区分，标记close-call；现在不创建新卡、主随机种子、代码、运行或Pro请求。

## 7. Claim ceiling, surviving alternatives and return

Direct observation: this fixed-base, one-instance native panel favors T over C/G and F over
T/G. Scientific inference: learning selective retrace has not beaten the competent fixed rule
under this budget. The finite-budget T−G gain remains reportable, with functional containment
compatible with unequal finite optimization. Engineering conformance establishes usable data,
not mechanism value. This is direction-local advice; integration/capacity remain Root's work.
Historical R02 positive legal-history value and R03's finite-host negative retain their original
units and authority, and neither is pooled with the new native returns.

The fixed DENSE/8201 base was selected with both old outcomes known; there is one new matched
training instance, conditional episode uncertainty, no tuned current-host headroom record, and no unique
memory/anchor causal identification. These bound the conclusion. The strongest contrary native
evidence, F's advantage over both learners, is preserved as the next comparison's central control.

Return to Root: accept/integrate the prospective card, exact source, accepted-handle and terminal
evidence commits plus this intake; close P78 tracking with the complete measured bill; preserve
the raw dependency and collected outputs for normal reclamation. The next scientific discriminator
is the unchanged fresh matched instance recommended above, subject to separate allocation.
