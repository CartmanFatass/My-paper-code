# UCOPE research notebook

## 2026-09-19 — owner-selected parallel feedback-renewal branch

The owner wants Codex and Claude to advance independently and selected: “Claude 继续当前
FSD；我从 VSP-03 / UCOPE 中独立推进一条 K 分支”. This Codex session selects **UCOPE** and
owns its feedback-renewal question end to end. Claude retains exclusive ownership of
`flexible_skill_duration`, its current learner investigation, notebook, code and accepted
operations. This is an owner-selected reopening of UCOPE, not a second writer for FSD.
The question here is whether an agent should KEEP an actual velocity command or END it
after receiving a fresh private observation, compared with fixed renewal and ordinary
every-tick feedback. It does not establish equivalence to FSD's learned skill interface.

Codex works directly as DM, using bounded advisers/engineering help where useful, on
`codex/ucope-feedback-renewal`. The prior FOLR work remains idle and preserved at
[`cd3b97ab7982ac5efec86eace09d33328be841fa`](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md).
There is no new FOLR fit or revived VSP-03, CRTO, SCDMP or VSP-C1 allocation. The direction
lead owns this notebook; shared-main integration remains with the actual integrator,
currently Claude, until an explicit handover. No change in this branch is evidence that
the live Claude session has read or adopted it. Result execution requires the published
canonical index and local canonical policy to carry the owner-selected UCOPE lead.

### Starting explanation and contrary evidence

The [2026-09-13 PARK record](PARK.md) and
[8901 result](UCOPE_REACTIVE_RENEWAL_B01_8901_RESULT_EVIDENCE_20260913.md) remain historical
evidence. In that one complete R/F/G instance, R−F was −0.0032978553 and R−G was
−0.0180632903. All three learned arms beat hover, and the R gate actually moved; the
feedback-renewal package nevertheless had no demonstrated development margin. Older
precommitted T/L losses and mixed F/G outcomes remain separate designs. Their fits are
not repetitions of R. No old checkpoint, stopped attempt or frozen reading is changed.

The useful surviving uncertainty is whether the R-versus-G ordering recurs across fresh
training histories. The old PARK explicitly retained another independent instance as
a legitimate alternative. The owner now selects an independently maintained K branch:
the concrete use decision is whether this implemented reactive-renewal family warrants
further method development, versus favoring ordinary feedback at this host and exposure.
This changes the investment question, not the evidence in favor of R. It does not imply
that management convenience creates an expected positive effect. Current expectation
remains that R will not consistently beat G; a contrary repeatable endpoint pattern
would change which mechanism deserves the next comparison.

### Prospective reactive-renewal B02: one finite replication batch

Select **six fresh fits**, R/F/G on each of two unscreened masters **8911 and 8912**.
Each fit trains **2,048 complete 256-tick episodes**, with 1,024 two-episode rollouts and
4,096 Adam updates. Each learned endpoint receives one 64-world sampled final panel;
hover H receives the same worlds with zero learning. No interim evaluation, selected
checkpoint, additional seed, tuning or automatic extension follows. These are two new
independent training blocks, not six independent effect estimates. The old 8901 result
remains development context and is not pooled into a new confirmation claim.

Reuse the scientific implementation in `reactive_renewal_b01` without changing its
environment, policy, recurrent replay, compound action likelihood or update law:

- Five fixed UAVs; the original native service objective and 256-tick task. J sums the
  five native rewards and divides by 256, with no new shaping or decision-rate scaling.
- R chooses KEEP/END after the fresh observation; commands persist at most two ticks.
  F draws physical duration 1 or 2 with fixed half/half probability at own expiry.
  G draws a fresh legal velocity every tick. All histories update on every primitive
  tick; the lawful actor/critic information, phase fields and differing R gate capacity
  remain exactly those in the old [contract](UCOPE_REACTIVE_RENEWAL_B01_CARD_20260913.md).
- CPU FP32, one Torch/BLAS thread per invocation, Adam 3e-4, four PPO epochs per rollout,
  entropy coefficient zero, raw gamma-one Monte Carlo returns and 32-tick recurrent
  chunks. KEEP receives its gate likelihood and full current/future return credit;
  the existing all-primitive-row denominator remains. No new optimizer interpretation.
- Preserve the old seed-address formula for each new master: common initialization
  and exogenous world labels within each block; distinct arm-owned training/action RNG
  streams; separate evaluation generators and reset histories, with zero updates.

The **primary practical comparison is R−G**, prospectively chosen for this new use
decision; the old R−F primary is not rewritten. R−F and F−G are necessary secondary
comparisons: if R and F improve similarly over G, that weakens a special reason to
learn feedback-based renewal. If R beats F but loses to G, it still does not provide
a practical advantage over the attained ordinary controller. Preserve H margins,
all final vectors and adverse episodes. Report both per-block contrasts and their
descriptive mean, distinguishing conditional world-panel noise from training variation.
The old 0.01 J scale is context for practical importance, not a new exploratory MEI
verdict or an equivalence rule.

If R has useful positive R−G and R−F contrasts in both new blocks, the family earns
consideration for a separately designed follow-up; this batch supplies no stable
superiority, component attribution or confirmation. Repeated R−G deficits strengthen
the case to stop this exact reactive package. Mixed or small outcomes retain uncertainty
without earning an automatic extra block. All readings preserve the old adverse 8901.
No result licenses a claim about arbitrary duration, agent count, FSD's current model,
physical deployment or a tuned optimum.

Total selected work: **12,288 training episodes / 3,145,728 training team steps /
24,576 Adam calls**, plus **512 evaluation episodes / 131,072 evaluation team steps**,
including H. Six fits are allocated in total, including failed started attempts. A
partial invocation retains its started arms and counts; unused arms do not authorize
an automatic replacement. This is a prospective replication for the recorded use
decision, not continuation or replenishment of the closed 8901 batch.
These are **six additional fits reopening the unchanged reactive design**; including
8901, this reactive R/F/G design will have nine training fits if all six complete.
Earlier T/L/F/G development exposure remains additional and is not erased by that count.

Use configured **local_linux**, independently of Claude's currently recorded
`wsl_4070` FSD operations. Two instance-owned processes may run concurrently only after
fresh actual-node admission; R/F/G execute sequentially within each instance. Historical
remote 8901 complete wall was 1,813.83 seconds for three fits; local cost is unknown and
that timing is not a promise or a CPU speedup claim. The node change is explicit, with
no bit-identity assumption. Record complete measured wall/CPU/RSS and support limitations.

### L0: current admission and publication for the unchanged science

Owned new paths: `experiments/candidates/ucope/reactive_renewal_b02/`,
`scripts/run_ucope_reactive_renewal_b02.py`, mirrored focused tests and this notebook.
Reuse the B01 implementation by import; preserve its historical sources and frozen
runner. The new entry fixes the two allowed masters and scientific exposure, requires
`scripts.hmasd_admission.require_admission` before creating output or scientific objects,
and checks any supplied launch SHA against admission. No fixture/bypass CLI is shipped.

Publication identifies this B02 note and admitted SHA, distinguishes the declared node
from actual-node evidence in the native launch manifest, and preserves fit-start evidence;
it preserves episode/update records and final checkpoints. The new summary marks
R−G as primary and removes the historical UP/WITHIN/DOWN label for this exploratory
object. Incomplete attempts cannot acquire a complete comparison. Reuse the existing
branch-density/KEEP-credit/replay tests and add focused admission-order, scope and
publication checks using synthetic fixtures. An independent Reviewer checks the new
execution/publication boundary; the DM accepts the diff and checks. No new core policy,
environment or learner changes are selected.

Current boundary: preparation only, **zero new scientific fits started**. The shared
index integration and engineering acceptance precede any launch; neither requires
Claude's FSD scientific result to finish.

### Independent scientific criticism and DM response

The existing ResearchCritic independently read the 8901 result and PARK record and
returned `MATERIAL_DISSENT: no` for the prospective replication. Its substantive
qualification is adopted: F must constrain further investment even with R−G primary;
G was best in one old instance, not established as universally best. A four-fit R/G
comparison would leave the simpler F explanation unanswered. The outcome branches above
therefore require useful margins over both comparisons for a strengthened development
case. Adviser agreement adds no empirical evidence or fit authority. The adverse active
8901 gate result and the full prior exposure remain part of the working explanation.

## 2026-09-19 — worktree preparation; owner defers integration

The owner explicitly replies: “你在worktree进行即可 后续我们根据需要合并”. Work continues
in this existing isolated checkout on `codex/ucope-feedback-renewal`; main and Claude's
checkout are not modified. [PR #27](https://github.com/CartmanFatass/My-paper-code/pull/27)
is a reviewable publication for later integration, not authority to merge it now.
No new task, standing Root layer or control-plane policy change is selected.

The bounded Implementer delivered the new adapter and runner without changing B01
scientific sources. Its B02 synthetic checks passed 9 tests in 1.10s; the retained
B01 likelihood/credit/replay suite passed 7 tests in 3.19s. The DM read the diff and
requested independent source review. The local scientific environment was read as
Python 3.10.20, NumPy 1.26.3 and Torch 2.7.0+cpu. This inspection is not a native fit.

Source review of the launch kernel and a read-only `parse_research_state` check confirm
the present execution dependency: this branch parses as UCOPE exploring / Codex DM,
while the canonical main index has no UCOPE Active row. Its actual parser response is
`direction 'ucope' must appear exactly once in the Active table`. The launch kernel
also compares canonical policy with published main. This was policy inspection only:
no launch was attempted, no admission or native fit was accepted, and no preflight
receipt was borrowed from another node. Formal B02 execution remains pending the
later control-state integration; no workaround or automatic merge is selected.

## 2026-09-19 — engineering accepted; owner authorizes main integration

The owner subsequently states: “你可以写入main 我通知claude即可”. This explicitly
authorizes this task's current main integration; it supersedes the earlier defer-merge
boundary for this change. The owner will coordinate with Claude. Publication or this
record does not claim that Claude has already read the new assignment. Integration
preserves Claude's FSD work and all accepted operation identities.

The independent Reviewer reports no material findings in the new B02 sources after
checking admission-before-effects, fixed scope, unchanged B01 science, source/node
provenance, incomplete-result handling, primary/secondary readings and fit accounting.
It reused the 9-pass B02 and 7-pass B01 evidence and ran `git diff --check`; it did not
run live admission or scientific work. The DM accepts the implementation and checks.
Synthetic verification does not establish native performance or a learning result.

Implementation timing fields name their measured scope: main-entry wall through the
inherited loop, inherited-loop process CPU and one-process peak RSS. Actual-node proof
comes from the native launch manifest, not a fabricated admission field. Missing full
exit/support telemetry limits cost claims rather than invalidating scientific data.
Before launch, zero B02 fits have started. The next authorized action is publication,
main/control-state integration and two admitted local_linux block invocations at the
published source, followed by collection and the prospective six-fit reading.

## 2026-09-19 — B02 block invocations admitted in the Codex worktree

PR #27 merged at `801184245a2466af73a92ddd364c2e56fda3bdf0`. The owner relayed Claude's
coordination: Claude withheld main pushes during this integration, retained ownership
of its canonical checkout/index, and would fast-forward it after the merge. Read-only
observation then found canonical main at `1880287803423a748a1b88f419cc492480406d80` with
the UCOPE exploring / Codex DM row. Codex only fast-forwarded its own author worktree;
it did not modify Claude's checkout/index or FSD source/operations.

Both original block invocations were accepted on `local_linux` at published scientific
source `21b7c9aeb8587a130402ec1d7c99c8fa9cfbb9cb`. Source snapshots keep active inputs
unchanged while this notebook advances. Native operation identities, SHA, source cwd,
author-worktree outputs, process identities and argv are in the runner-owned manifests:

- [master 8911 launch manifest](../../../../runs/ucope/reactive_renewal_b02_8911/launch-manifest.json),
  accepted 2026-09-20 02:04:48 UTC.
- [master 8912 launch manifest](../../../../runs/ucope/reactive_renewal_b02_8912/launch-manifest.json),
  accepted 2026-09-20 02:05:39 UTC.

Both fresh actual-node memory checks passed the configured 4 GiB physical/effective
floor (12,195,426,304 and 11,971,981,312 available bytes respectively); these are admission
facts, not peak training memory. The two independent invocations each execute R/F/G
sequentially. Six fits remain the whole allocation; process admission does not mean
all six arm fits have already started or completed. No score-based change is selected.
The existing bounded Monitor has been assigned both exact operation references; the
DM retains observation responsibility through actual adoption, and retains collection
and scientific reading throughout. Results will be read together after both invocations
are terminal. No successor or extra fit is allocated.

### Observation responsibility and pre-result interpretation

At 02:14:25 UTC the bounded Monitor returned a native snapshot confirming both exact
operations still running, accepted and identity-consistent, with no exit witnesses.
It reported R progress of 1536 episodes for 8911 and 1280 for 8912. A continuous
adoption message had not arrived, so the DM retained direct observation and narrowed
the helper task to that snapshot; the helper reconciled and aborted only its own
read-only observer sessions. Both scientific processes were untouched. The DM now
directly owns observation through completion as well as collection and reading.

A source comparison against 8901's `831b83c15` finds no change in the reused
`reactive_renewal_b01` or `uav_motion_prefix_b01` trees. The selected PettingZoo
environment/adapter and vectorized path are unchanged. The unrelated added libm
oracle in `uav_cpp_backend.py` is outside this selected backend. This supports the
declared unchanged-method replication; the explicit local-node/runtime change still
precludes a bit-identity claim.

Before reading any B02 scores, retain an important interpretation boundary. G's
ability to request a fresh velocity each tick does not make its implemented sampling
and learning package identical to R: G samples a tanh-Gaussian with clamped log standard
deviation, whereas R's KEEP copies an actual previous command and has a separately
trained gate. F also creates temporal persistence without learning that gate. Thus
R−G can reflect useful persistence, the induced action-noise pattern, representation
or finite learning; a gain is not automatically an information or termination-causality
result. R−F limits the practical reason to learn the added gate, while phase inputs,
capacity and learning differences still prevent unique component attribution. This
refinement changes no arm, endpoint, expected direction or stopping decision.

## 2026-09-19 — B02 complete: positive R−G, unresolved learned-gate increment

After the owner pointed out excessive direct polling, observation was transferred to
the sole bounded Monitor `ucope_b02_monitor`, which explicitly adopted both original
operation references. It reported arm transitions and terminal facts; the DM waited
for both terminal notices before reading either scientific panel. Both original
invocations exited zero with matching process witnesses and empty stderr. The Monitor
reported an empty active set. There was no restart, replacement fit or additional
evaluation. Published scientific source remains `21b7c9aeb8587a130402ec1d7c99c8fa9cfbb9cb`.

### Native observations and exposure

| Master | R | F | G | H | R−G, primary | R−F | F−G |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8911 | 0.2194721648 | 0.2256735644 | 0.2006274557 | 0.1484030494 | +0.0188447092 | −0.0062013995 | +0.0250461087 |
| 8912 | 0.1898158760 | 0.0394053595 | 0.1566775553 | 0.1651953028 | +0.0331383207 | +0.1504105165 | −0.1172721959 |

The two-block descriptive means are R−G **+0.0259915149**, R−F **+0.0721045585**,
and F−G **−0.0461130436**. The positive mean R−F is dominated by 8912; 8911 does
not show a learned-gate increment. These are two independent new training blocks,
not 128 independent training replications or a confirmation. Historical 8901's
R−G −0.0180632903 and R−F −0.0032978553 remain separate adverse context; it is
not pooled into a newly declared three-block result.

In 8911, the R−G world differences have 37 positive / 27 negative signs and R−F
has 30 / 34. In 8912, those counts are 47 / 17 and 64 / 0. F is below hover in
61 / 64 of 8912's worlds, versus 6 / 64 in 8911. This is broad poor performance
of this particular fitted F policy on its final panel, not one removable outlier
world. It does not establish that F is generally fragile. In 8912 G−H is also
slightly negative (−0.0085177475); R−H stays positive in both blocks (+0.0710691155,
+0.0246205732). All final vectors, including unfavorable rows, are retained.

Exactly six fresh fits completed. Each learned arm has 2048 training episodes,
524288 training team steps, 1024 rollouts, 4096 Adam calls and 64 fixed-policy
final evaluation episodes. The batch has 12288 training episodes / 3145728 training
team steps / 24576 Adam calls, plus 512 evaluation episodes / 131072 evaluation
team steps including H. All evaluation optimizer counts are zero. This completes
the whole prospective allocation; including historical 8901, this reactive R/F/G
design has nine fits, with older T/L development exposure still additional.

### DM verification, behavior and bounded post-hoc description

The DM checked both native summaries against the exact manifest source and master,
terminal witness and empty stderr. It independently read all 6400 episode rows and
3072 update rows per block: consecutive episode/rollout IDs, world-seed addresses,
256 steps per episode, four epochs per rollout, and all per-arm exposure counts
match. J reconstructs from each logged native reward sum divided by 256. All six
contrast vectors and four final arm means per block reproduce from the episode
records; JSON numerical values and all six checkpoint tensor sets are finite.
Checkpoint arm/master/horizon identities match. This was reading retained outputs,
with no scientific construction, policy evaluation or optimizer update.

All six common actors and critics moved from initialization. R's gate displacement
is 0.7909386754 / 1.4589626789 for 8911 / 8912; F's frozen gate displacement is
exactly zero in each. The runner reports zero evaluation parameter movement and
unchanged training generators in every learned arm. R's evaluation KEEP fraction
among eligible gates is 0.507231 / 0.334782; its held-command fraction among all
agent ticks is 0.335657 / 0.250085. F's corresponding held-tick fractions are
0.332739 / 0.333118. An active, changing gate is not proof that its state
conditioning supplied the return difference.

A bounded post-hoc reading of existing training logs found F8912's first/last
256-episode J means to be 0.1047965 / 0.1828324, followed by final-panel 0.0394054.
Its last two 32-episode training groups are 0.2175353 and 0.1015119, so some
late deterioration is visible before final evaluation. F8911's corresponding
last groups are 0.2517324 and 0.2408599. These selected summaries describe changing
training policies and worlds; they do not diagnose the cause, measure a matched
generalization gap, justify selecting an earlier checkpoint, or alter the sole-final
endpoint. Final F mean served connections are 13.4364 / 2.2061 and command norms
1.1326 / 1.3686. R's collector does not log these two fields, so no symmetric R/F
telemetry comparison is claimed. One local reading attempt initially assumed those
fields existed for R; the reader was corrected and the complete checks above passed.
The scientific runs and their records were unchanged.

### Recoverability and measured cost

- [8911 summary](../../../../runs/ucope/reactive_renewal_b02_8911/summary.json),
  [episodes](../../../../runs/ucope/reactive_renewal_b02_8911/episodes.jsonl),
  [updates](../../../../runs/ucope/reactive_renewal_b02_8911/updates.jsonl),
  [exit](../../../../runs/ucope/reactive_renewal_b02_8911/process-exit.json).
- [8912 summary](../../../../runs/ucope/reactive_renewal_b02_8912/summary.json),
  [episodes](../../../../runs/ucope/reactive_renewal_b02_8912/episodes.jsonl),
  [updates](../../../../runs/ucope/reactive_renewal_b02_8912/updates.jsonl),
  [exit](../../../../runs/ucope/reactive_renewal_b02_8912/process-exit.json).

Each run's `checkpoints-and-console.tar.gz` preserves its three native final `.pt`
files and stdout/stderr. Every archived member was compared byte-for-byte with its
original; the original local files and launch snapshots remain untouched. Archive
SHA256s are `d48ed47362edcfaa56d6fda9838a5d9b04c8a3b4dc3dab80f301583139725afc`
(8911, 759742 bytes) and
`5bea32a0c9e7fbbbb735b2016bc1713989238b3d00e6761be68358698097a6f4`
(8912, 760089 bytes). Extracting an archive in its run directory restores the native
checkpoint/console names; raw JSONL and summary records are published separately.

Runner-scoped wall is 2345.0049 / 2352.8686 seconds; inherited-loop single-process
CPU is 2343.2145 / 2351.5037 seconds. Single-process peak RSS is 353148 / 354032 KiB.
Native acceptance-to-exit wall is 2345.9588 / 2353.5758 seconds, ending at
2026-09-20 02:43:54.554926 / 02:44:52.894596 UTC. First acceptance to last exit
spans 2404.2985 seconds (40.07 minutes); the two measured runner walls sum to
4697.8736 seconds. These scopes differ. Preflight/launch preparation, engineering
and support time, and the simultaneous total memory peak remain unmeasured; the
maximum individual RSS is not the concurrent batch peak.

### Cumulative explanation and current decision

The two new positive R−G signs weaken the prospective pessimistic expectation and
strengthen retaining this complete R package as a candidate. They also weaken any
practical assumption that G is the settled winner. They do not overturn old 8901
or establish a training-population effect, adequate precision, arbitrary-duration
benefit or FSD's learned-skill claim.

R−F remains mixed and fails the stated favorable development pattern of useful
positive margins over both G and F in both new blocks. In particular, the aggregate
R−F mean must not hide F8912's poor policy. The respective contributions of state
conditioning, average persistence, action-noise distribution, capacity and finite
joint learning remain unresolved. The changed KEEP rate offers a concrete competing
explanation, not evidence that rate alone caused the advantage.

The independent ResearchCritic returned `MATERIAL_DISSENT: no` with the substantive
qualification that retaining R is weaker than crossing the prospective development
condition. The DM accepts that qualification. Current B02 is ended, with no seed
extension, retuned F replacement, selected earlier checkpoint or confirmation.
The next candidate question under consideration is whether state-conditioned renewal
adds use value beyond learning only an overall renewal rate under the same R timing.
It is not selected or funded by this result entry; any such new learning comparison
needs its own specific scientific reason and prospective exposure. Existing outputs
already suffice for the present mixed reading; another diagnostic is not owed.

## 2026-09-19 — selected B03: state-conditioned versus learned scalar renewal

### Scientific reason and development exposure

Select a new, finite direct learning comparison: can a learned scalar renewal rate
replace R's state-conditioned gate without giving up a useful native-return margin?
B02's two positive R−G observations make retaining some renewal package a live choice,
while its fixed half/half F does not answer whether an equally timed, learned global
rate is an adequate simpler alternative. This is a result-inspired simplification
and attribution follow-up, not an unexposed discovery or continuation of B02. The
old B02 favorable-development pattern remains unmet. The different observed KEEP
rates motivate a competing explanation but do not supply causal evidence for it.

The bounded Critic supports the limited decision value: the new comparison can change
which actual learning package is retained, provided the DM will simplify or stop
when R does not earn its complexity. It is not merely buying more R/F/G seeds. The
DM accepts the strongest qualification: changing the gate also changes parameter
count and its gradient into the actor backbone, so the result is a package comparison,
not isolated causality of current feedback. No additional diagnostic/control matrix
is selected. This entry explicitly costs **six new fits**, bringing the reactive
R/F/G and R/B development sequence to **fifteen related fits** including 8901 and B02;
older T/L development remains additional. No prior fit is refunded or erased.

### Fixed arms, exposure and reading

Use three unscreened fresh masters **8921, 8922, 8923**. Each invocation trains R then
B, each for **2048 complete 256-tick episodes / 1024 two-episode rollouts / 4096 Adam
calls**, and evaluates its sole final checkpoint on 64 sampled worlds. H evaluates
the same worlds with no fit. Both arms use the unchanged reactive forced-fresh,
eligible, KEEP/END law: KEEP copies the actual previous command, END draws a fresh
velocity, a held command lasts at most two ticks, and recurrence updates every tick.

- **R:** the existing learned `67→32→2` gate over recurrent features and the actual
  previous command, initialized half/half, with its existing actor-gradient path.
- **B:** two learned global logits, initially zero/half-half, shared across the five
  UAVs, worlds and eligible times within this one fit. Its KEEP/END probabilities
  never read observation, recurrent state, previous command or clock. It receives
  exactly the same eligible-row PPO gate credit, including final-tick current reward,
  and the same Adam/update law. Its velocity actor and centralized critic still
  receive all original lawful information and the same phase fields. Removing the
  gate-input gradient and 2240 gate parameters is part of this declared package.

Keep the actual UAV configuration/native J, CPU FP32, one Torch/BLAS thread, gamma-one
Monte Carlo return, raw value targets, entropy zero, clip .2, value coefficient .5,
gradient clip .5, Adam 3e-4 and four epochs unchanged. Reuse the reactive collector
and update for BOTH learned arms. No earlier source or frozen runner is edited.
Common velocity-actor and critic initialization is identical within each master;
optimizers and RNG streams are arm-owned. With base=master*100000, common initialization
is base+11, R gate initialization base+12, training worlds base+10000+episode, and
evaluation worlds base+20000+episode. R uses velocity/gate streams base+41/+42 in
training and base+70000+episode/+80000+episode in evaluation. B uses base+51/+52 and
base+90000+episode/+95000+episode. B's logits use deterministic zeros. Final evaluation
uses separate generators and zero updates, preserving training generators and weights.
No B probability is fitted to B02 evaluation data or supplied from its observed rates.

The primary is **R−B**, with all three within-master differences, their descriptive
mean/range, full world vectors, and R−H/B−H retained. Independent learning variation
is at the three training-block level. Conditional world-panel SEs are not uncertainty
over training instances. This is exploratory selection, with no significance/equivalence
label, new confirmation or automatic fourth seed. G/F are not rerun: this object
cannot establish that either selected package beats a fresh ordinary controller.

Prospective investment reading: useful positive R−B margins across all three blocks
would strengthen retaining the state-conditioned package for a later use comparison.
If B is competitive and R does not show a consistent useful margin, prefer the simpler
B package as the development candidate, without asserting equivalence. Mixed, small
or broadly poor results may leave neither selected for further fits. The existing
0.01 J scale is practical context, not a retrospective statistical verdict. Preserve
all block outcomes and hover deficits; no performance-based early stop, earlier
checkpoint selection, rate tuning, replacement, or automatic extension is allowed.

Whole B03 exposure: **6 fits / 12288 training episodes / 3145728 training team steps /
24576 Adam calls**, plus **576 evaluation episodes / 147456 evaluation team steps**
including three H panels. Total native team steps are **3293184**. Use `local_linux`
in up to three independently admitted instance-owned invocations, R/B sequential
within each. Fresh actual-node memory admission precedes each original launch. The
ordinary 6000-second invocation watchdog preserves incomplete attempts; B02's measured
timing is context, not a promised B03 rate. Each failed started arm consumes its fit.

### L0: bounded implementation and checks

Owned new source: `experiments/candidates/ucope/reactive_rate_b03/`,
`scripts/run_ucope_reactive_rate_b03.py`, and mirrored focused tests. The Implementer
owns those paths only; the DM owns this notebook, RESEARCH and acceptance. Add the
two-logit input-independent gate and a small R/B/H study binding. Reuse existing
environment, policy templates, reactive collector/update, native hover collection,
counter/publication helpers where correct; adapt exposure grouping locally because
the old helper assumes R's three-layer gate when `duration_conditioned` is true.
Preserve half/half initialization and exactly identical common parameters; do not
misreport dormant extra layers as scalar gate parameters. No global monkey-patching.

The runner fixes the three masters and exposure, requires admission before scientific
imports/effects, checks the admitted SHA, exposes no fixture/bypass CLI, and publishes
per-arm activity/fit accounting, movement, gate probabilities, final vectors, checkpoint
identity and scoped wall/CPU/RSS. Keep exact original admission/operation/exit artifacts
and preserve incomplete work without complete contrasts. The scientific tests use
synthetic environments in pytest-managed scratch: prove B's probability ignores input,
its eligible gate gets nonzero gradient while no gate gradient reaches the backbone,
KEEP/END replay and terminal credit remain valid, matched common initialization,
fixed scope/admission ordering, complete/incomplete counts and train/eval isolation.
Add an off-path synthetic R comparison to the existing implementation where useful;
do not run native UAV smoke fits. An independent Reviewer checks the new scientific
and execution boundary before DM acceptance/publication and original admission.

At selection there are **zero B03 fits started**. The original B02 remains complete
and unchanged. Claude retains FSD ownership and its running operations; this work
uses only the Codex author worktree/index and its own outputs.

### Simple-model reading of the scalar alternative

For a constant eligible KEEP probability q, each fresh command lasts one tick plus
a second tick with probability q. Its expected duration is 1+q, and in the long-run
renewal abstraction the held-tick fraction is q/(1+q). Thus q=.5 gives one-third held
ticks; a learned scalar explores more than F's single half/half setting. This is a
derivation from the declared timing, not an experimental result. Finite episodes
have reset/end effects, and the relation supplies no native-return prediction by
itself. It also does not make B identical to historical F: their policy phase inputs
and gate-learning laws differ. Within B03 those timing/phase rules are matched.

B still learns from return and advantage during training. Its restriction is that,
at an eligible execution decision, its probability does not condition on the local
state/history. R can condition that probability and sends its gate loss through the
recurrent feature path. This separates a potentially useful simpler learning choice
from claims that “any feedback” has been removed. The B03 outcome can guide package
selection even if it cannot uniquely identify the causal contribution of fresh
observations.

### B03 implementation and review accepted before execution

The Implementer delivered only the assigned new scalar helper, R/B/H study, admitted
runner and mirrored tests. The DM read their final source and focused checks. The
scalar has exactly two parameters, ignores input values, begins at half/half, and
receives eligible-row return credit through the unchanged reactive update. R's
construction matches the original and both arms share common initial parameters;
their generator ownership and the fixed seed addresses match this entry.

The final combined synthetic check reports **20 passed in 2.76s**: 13 B03 checks and
7 inherited reactive semantics checks. Compilation and diff checks passed; managed
test scratch cleaned normally. The independent Reviewer read the final files and
reported no material findings, including the admission/publication/failure boundary,
scalar gradient restriction, incomplete fit accounting and evaluation isolation.
It reused the final checks and did not run native admission, fits or an abrupt-process
termination test. These checks establish implementation evidence, not native efficacy.

The DM accepts the diff and review. No historical B01/B02 or FSD scientific source
changed. B03 still has zero started fits at this acceptance boundary. The next action
is exact-source publication followed by the three original admitted block invocations;
the Monitor will receive the accepted handles, and the DM will read all three final
panels together after terminal notices.

The DM's staged-file check then exposed four trailing blank EOF lines that the
earlier unstaged check did not include. They were removed in a follow-up publication
before any launch; executable semantics and the reviewed tests are unchanged. No
history rewrite or repeated synthetic/native work is needed for that whitespace fix.

### Three original B03 block invocations admitted

All three original invocations were admitted on `local_linux` at published source
`5101c921e7ba793b95ec7ffef3289114cb9b27b9`, with separate immutable source snapshots
and outputs in this Codex author worktree. Current canonical/published control policy
was observed at `a41dbb31e5806d0b7c3e8958b6e74396406aa5cd`; Claude's checkout/index and
FSD operations were untouched. Native identity, node, argv and source/output bindings
remain in these manifests rather than a separately maintained command record:

- [8921 manifest](../../../../runs/ucope/reactive_rate_b03_8921/launch-manifest.json),
  accepted 2026-09-20 03:14:11.510350 UTC.
- [8922 manifest](../../../../runs/ucope/reactive_rate_b03_8922/launch-manifest.json),
  accepted 2026-09-20 03:14:54.979489 UTC.
- [8923 manifest](../../../../runs/ucope/reactive_rate_b03_8923/launch-manifest.json),
  accepted 2026-09-20 03:15:22.282681 UTC.

The three fresh node preflights passed the 4 GiB available-memory floor, observing
12055461888 / 11731087360 / 11500441600 physical/effective available bytes. These are
admission observations, not experiment memory peaks. Each invocation runs R then B;
admitting three invocations does not claim all six arm fits have already begun.

The sole bounded Monitor explicitly acknowledged all three exact operation references
and owns read-only observation through their terminal witnesses. It reports actual
arm transitions, exceptions and completion, not routine episode-count increments.
The DM owns collection and the joint reading after all three are terminal. No B03
scientific score has been read, and no successor or replacement is allocated.

## 2026-09-19 — B03 complete: retain the simpler scalar package as a candidate

The Monitor returned valid terminal witnesses for all three original invocations:
COMPLETE, exit zero, empty stderr, 1097728 native team steps and 8192 Adam calls per
invocation. Its active set is empty. Only then did the DM read the three scientific
panels together. No restart, replacement, extra fit, checkpoint selection or additional
evaluation occurred. The executed source is
`5101c921e7ba793b95ec7ffef3289114cb9b27b9` throughout.

### Native result and interpretation

| Master | R | B | H | R−B, primary | B−H |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8921 | 0.1373240773 | 0.2061958493 | 0.1611799077 | −0.0688717720 | +0.0450159416 |
| 8922 | 0.2045608641 | 0.2307566494 | 0.1717527103 | −0.0261957853 | +0.0590039391 |
| 8923 | 0.1976960173 | 0.1857490713 | 0.1451625662 | +0.0119469460 | +0.0405865051 |

The descriptive mean R−B is **−0.0277068705**, range [−0.0688717720, +0.0119469460].
The third block is contrary evidence to a universal B advantage and remains visible.
R−B has 12/52, 21/43 and 36/28 positive/negative world differences respectively;
these are conditional panel descriptions, not additional training replications.
R8921 is below hover by −0.0238558304. B−H is positive in each block, with descriptive
mean +0.0482021286; this is a weak reference check, not a competent learned ordinary
controller comparison. Mean arm returns are R 0.1798603195, B 0.2075671900 and
H 0.1593650614. All individual outcomes and full final vectors remain published.

This follows the prospective simplification branch: **provisionally retain B as the
simpler development candidate**. R did not display a consistent useful increment
in this batch, so the evidence is insufficient to prioritize its more complex gate.
This is a bounded development choice, not proof that B is reliably superior or
equivalent across training instances, and not confirmation. The three new blocks
are not pooled with B02 or historical 8901 into an enlarged post-hoc result.

### The mechanism that was active, and what remains unknown

R has 68553 trainable actor/critic parameters and B 66313. All six common actors,
critics and gates moved. R gate displacements are 1.3041175604 / 1.0691225529 /
1.0823279619; B scalar displacements are 0.0332339108 / 0.0496865548 / 0.0344341621.
B's initial logit norm is zero, so its relative displacement is correctly undefined.
Its final KEEP probabilities are **0.488252 / 0.517560 / 0.487828**, verified from
the saved two-logit checkpoints. Their observed eligible KEEP fractions are
0.484159 / 0.518567 / 0.485003. R's corresponding observed fractions are
0.347514 / 0.469431 / 0.582243; no unrecorded mean R probability is inferred.

B therefore trained and operated, but its endpoint probabilities stayed close to
half/half. This does not establish that learning the rate supplied B's result,
that it was useless, or that freezing the rate at .5 would be equivalent. There
was no frozen-B arm under this timing. Historical F differs in phase representation
and training rules and cannot fill that missing comparison. The changed parameter
count and absence of a gate-to-backbone gradient in B also prevent attribution solely
to state conditioning. B's velocity actor still uses local feedback.

The broader update is that the tested state-conditioned gate package has not earned
priority over this simpler alternative at the selected exposure. The need for state
feedback in other renewal designs is untouched. B02's two positive R−G observations
remain real; this B03 result does not negate them. Equally, R−G from B02 plus B−R
here cannot establish B−G: G/F were not fitted on these blocks, and the policies and
worlds differ. Ordinary-feedback advantage and the benefit of rate learning remain
open questions, without an automatic new fit allocation.

The independent ResearchCritic returned `MATERIAL_DISSENT: no` for this provisional
choice and advised the precise wording “this batch did not show a consistent useful
increment,” rather than suggesting a reliable increment was proven absent. The DM
adopts that wording and its qualifications. Current B03 is ended. The direction
remains exploring, with B retained, no live operation and no selected successor or
confirmation. Existing evidence suffices for this investment decision; another
diagnostic, fixed-rate control or G comparison is not required merely to close it.

### Complete exposure, independent reconstruction and recovery

All six selected fits completed: 12288 training episodes / 3145728 training team
steps / 24576 Adam calls; 576 evaluation episodes / 147456 evaluation team steps,
including H. Total native team steps are 3293184. Evaluation used zero updates and
left all learned parameters and training RNG states unchanged. The reactive sequence
now contains fifteen related completed fits including 8901 and B02; the earlier T/L
work remains additional. These counts do not turn development exposure into independent
confirmation evidence.

The DM read all 12864 episode rows and 6144 update rows and checked consecutive IDs,
master/world-seed addresses, 256-step horizons, two-episode rollouts, four epochs and
4096 updates per learned arm. J reconstructs from native reward_sum/256. All nine
R−B/R−H/B−H final vectors, their means, and all R/B/H panels reproduce from the raw
episode records. All JSON numerical values and six checkpoint tensor sets are finite;
checkpoint object/arm/master/exposure identities and runner-recorded SHA256s match.
The published episode/update SHA256s also match the final native files. This was
retained-artifact reading only, with no new scientific execution.

Complete summary, episode/update JSONL, native acceptance/preflight and exit files
are retained under these original run directories:

- [8921 summary](../../../../runs/ucope/reactive_rate_b03_8921/summary.json).
- [8922 summary](../../../../runs/ucope/reactive_rate_b03_8922/summary.json).
- [8923 summary](../../../../runs/ucope/reactive_rate_b03_8923/summary.json).

Each directory's `checkpoints-and-console.tar.gz` preserves native `R_final.pt`,
`B_final.pt`, stdout and stderr. Every member was compared byte-for-byte with its
original; originals and admitted source snapshots remain untouched. Extracting the
archive in its run directory restores the native names. Archive identities are:

| Master | Bytes | Archive SHA256 |
| --- | ---: | --- |
| 8921 | 504027 | `5b3f332d98485eed30f65ae619e38a2a4a749bc510d1bab01fdf7db7f46194e2` |
| 8922 | 504090 | `758a41d3f521486e5e7f0c476d4d78f7029515057e4f0e5bf7fa0ab1ddfab94a` |
| 8923 | 503852 | `2aabf76b2ee00f12e4d8e0c124338212fd13aab1dcc07ade8e822c14d18787cc` |

### Measured cost

| Master | Runner-scoped wall s | Study-loop CPU s | Single-process peak RSS KiB | Native acceptance-to-exit s |
| --- | ---: | ---: | ---: | ---: |
| 8921 | 1673.8398 | 1672.5604 | 349512 | 1674.4235 |
| 8922 | 1652.6217 | 1651.3547 | 349164 | 1653.1457 |
| 8923 | 1657.5883 | 1656.2968 | 350724 | 1658.0749 |

The parallel first-acceptance-to-last-exit span is 1728.8473 seconds (28.81 minutes),
ending 2026-09-20 03:43:00.357607 UTC. Summed runner-scoped wall is 4984.0498 seconds
and summed study-loop CPU is 4980.2119 seconds. The individual RSS maximum is not
the simultaneous process total. Runner timing excludes final publication/exit;
CPU excludes parser/admission/import preparation. Complete preparation, engineering,
support and concurrent total memory remain unmeasured. Different arm counts and
concurrency preclude treating the shorter span than B02 as a method speedup.

## 2026-09-19 — owner continuation and selected B04: scalar renewal versus ordinary feedback

The owner clarified that closing one hypothesis must not end the direction's research
flow. UCOPE remains the Codex session's active K direction alongside Claude's independent
FSD work. The earlier idle wording described the end of B03, not an owner pause or an
investment decision against UCOPE. After each bounded result the DM will update the
working explanation and select a useful next observation, diagnosis, revision or source
question. This does not extend a completed batch or increase the credibility of a hypothesis.

### New question and inherited evidence

B03 provisionally retained the simpler B package over R: R minus B was −0.0688717720,
−0.0261957853 and +0.0119469460. The third block remains contrary evidence. B02's two
positive R minus G differences and historical 8901's negative R minus G difference remain
part of selection history. Neither those results nor B03 identifies B minus G on matched
fresh training blocks. This direct use comparison is the reason for B04, not an attempt
to add seeds until B03 becomes uniform.

**Question:** does the selected learned scalar-renewal package B outperform ordinary
per-tick feedback G under the inherited information and training budget? The prospective
prediction is a positive descriptive B−G difference if the package is useful here.
We expect actual KEEP exposure, movement of B's scalar gate and both arms' actors/critics;
these are execution/learning observations, not identifying evidence for a mechanism.

The strongest simpler explanation of a B advantage is altered action-noise persistence
and command copying, without any benefit from learning a renewal rate. B's phase feature
and policy-gradient exposure also differ from G. The study is explicitly a package
comparison; it cannot attribute an effect to state conditioning, rate learning or short
duration alone. B's velocity actor still uses local feedback. G is the inherited ordinary
feedback comparator under this fixed exposure, not an established optimum over tuned
ordinary controllers. Its actual learning and native performance will be inspected and
all valid adverse instances retained.

### Prospective exposure, information and outcome reading

- Object: `UCOPE_SCALAR_FEEDBACK_B04`; masters **8931, 8932, 8933**; two learned arms
  B and G per master, **six new fits total** on `local_linux`. B then G run sequentially
  inside each invocation; up to three independent invocations may run concurrently after
  separate fresh actual-node admission. There is no new R, F or fixed-rate B fit.
- Each arm trains **2048 episodes × 256 primitive steps**, in 1024 two-episode rollouts
  with four PPO epochs each: 4096 Adam calls per arm. Final sampled-policy evaluation is
  64 fresh shared exogenous worlds per arm, with a zero-fit hover H reference. Only the
  final checkpoint is evaluated; no intermediate selection, tuning or additional panel.
- The native five-UAV/50-user environment, reward and objective J (sum of five native
  rewards divided by 256), CPU FP32, one Torch/BLAS thread, model sizes and all learner
  settings remain as in B03 and historical G: gamma 1 raw Monte Carlo returns, global
  advantage normalization, agent-compound PPO ratios, clip .2, value coefficient .5,
  entropy 0, gradient clip .5, Adam .0003 and recurrent chunks of 32. Recurrent state
  updates every primitive tick and resets only at episode boundaries.
- B is exactly B03's zero-initialized two-logit input-independent KEEP/END gate and
  reactive collector/update. Forced-fresh becomes eligible; eligible KEEP copies the
  actual previous command and forces freshness next tick; eligible END samples a fresh
  command and stays eligible. Maximum hold remains two ticks; full return and final-tick
  gate credit remain. Its probability is learned independently in each fit, never set
  from earlier endpoint probabilities.
- G has no duration head, samples a fresh velocity each tick and uses the unchanged
  ordinary collector/update with `renewal=True`, support `(1,2)`, `agent_compound`,
  entropy 0 and no value moments. Both arms share initial common actor/critic bytes per
  master but have private model, optimizer and RNG state. Both see current local
  observations, previous actual command and their own phase; G's phase is zero, B's is
  its eligibility flag. The centralized critic receives the same state/command fields
  and each arm's own phase. No actor receives other agents' hidden information or future
  observations. Equal dimensions/exogenous information do not make phase representation
  or optimization exposure identical.
- With `base=100000*master`, common initialization is base+11; B's gate is deterministically
  zero. Training worlds are base+10000+episode and evaluation worlds base+20000+episode.
  B training velocity/gate offsets are 51/52 and evaluation offsets 90000/95000+episode;
  G uses 21/22 and 50000/60000+episode. Evaluation leaves training RNGs and learned weights
  unchanged and makes zero optimizer updates. H uses the same final world addresses.
- Primary: the complete **B−G** vector and mean in every block, then the descriptive
  mean/range across three independent training blocks. B−H and G−H are secondary reference
  checks. World rows are conditional panel observations, not more independent training
  instances. There is no significance/equivalence verdict or new categorical MEI threshold.
- Consistent useful positive differences strengthen keeping B as a development candidate;
  mixed/small differences leave practical use unresolved; repeated negative differences
  reduce B's priority and end this package's current investment. Poor native performance
  of both arms limits usefulness even when a relative difference is favorable. Every
  branch preserves all outcomes and selects the next scientific action rather than
  automatically appending seeds or closing UCOPE. No branch automatically confirms a claim.

There are fifteen completed related reactive fits before B04, plus older T/L development;
completion of these six would make **21 related fits**, not six unselected fits and not
confirmation. A failed started fit counts. A technical failure, partial panel or missing
telemetry is treated at its actual scope; no replacement is authorized by this allocation.
Each invocation has the inherited ordinary 6000-second watchdog; B03's roughly 29-minute
parallel span is a planning reference, not a resource or speed claim for B04.

The independent ResearchCritic returned `MATERIAL_DISSENT: no`: the direct same-batch B/G
comparison changes the development decision and is not a disguised B03 extension. The DM
adopts its cautions about package confounds, baseline tuning limits and conditional panels.
Adding a frozen-rate arm would reduce the main comparison to two training blocks and answer
the secondary attribution question first; that control is not selected here.

### L0 engineering scope

Deliver a fixed B/G/H study in `experiments/candidates/ucope/scalar_feedback_b04/`, an
admission-first `scripts/run_ucope_scalar_feedback_b04.py`, and focused tests under
`tests/experiments/candidates/ucope/scalar_feedback_b04/`. Reuse unchanged B03 ScalarGate,
the reactive collector/update for B and the ordinary collector/update for G/H. Do not edit
historical studies, common policies/learners, native environments, FSD paths or launch
infrastructure. The new study may reuse appropriate read-only publication helpers; do not
monkeypatch an earlier study's global scope or build a general experiment framework.

Preserve the scope above, incomplete-output handling and original terminal evidence. Save
raw episode/update JSONL, complete contrast panels, actual learning/evaluation counts,
parameter displacement by common actor/critic and B gate, B final logits/probabilities,
native checkpoint identity and SHA256, artifact hashes and honestly scoped wall/CPU/RSS.
Handle G's absent gate explicitly, without invented zero-logit probabilities or scalar
parameter groups. The CLI only admits the three selected masters and frozen scientific
exposure; any synthetic fixture stays internal and has no scientific launch flag.

Checks must protect dispatch to the correct collector/update, unchanged G semantics,
common initialization/private state, scalar learning/input independence, G's absent gate,
fixed scope, final-panel reconstruction, failure publication, evaluation isolation and
admission-before-effects. Reuse prior checks for unchanged code. Test scratch follows
tests/AGENTS.md. No native smoke fit is allocated. Independent engineering review precedes
DM acceptance, commit/push and guarded detached launch; Monitor adopts exact accepted handles.
Implementer owns only the three new code/test path groups above, no notebook or index edits,
no commit/push, native launch, Pro transport or child delegation.

### Owner-supplied temporal-alignment insight, adopted before B04 execution

The owner supplied the independent design/prototype
[`TEMPORAL_BEHAVIOR_STATE_ALIGNMENT_20260919.md` at 646ab539](https://github.com/CartmanFatass/My-paper-code/blob/646ab539d2a2ef689d0e4ee977f327f79cf2215b/docs/research/designs/TEMPORAL_BEHAVIOR_STATE_ALIGNMENT_20260919.md).
The DM read its complete, clean committed version in the temporal-alignment worktree,
including the later exact one-decision identification argument. This is advice and
synthetic/theoretical evidence, not a native result or a new authority over UCOPE.

Adopted clarification: G's innovations are sampled freshly each tick, but its actions are
not IID because their means depend on recurrent history, current observation and the
previous command. Copying a command in B changes temporal correlation, state visitation
and learning exposure. The document's two-step displacement-variance example gives a
possible explanation, not a UAV coverage or return prediction. B−G remains a useful
whole-package comparison, not evidence for clever renewal timing or necessary rate learning.

The one-decision covariance decomposition separates dependence on new observations and
retained information only under its fixed predecision distribution and common continuation.
Its counterexamples show that global exchange gaps can come from previous-command filtering
or can hide cancelling contributions. The identity does not extend by summing logged rows
through an altered full-horizon MARL trajectory. Therefore the proposed native calendar
exchange is not selected to answer the value of the newest observation. A frozen-calendar
substitution question remains distinct. No AR-noise arm, conditional-likelihood change,
new diagnostic panel or additional fit is introduced into B04.

The independent Critic read the supplied source and returned `MATERIAL_DISSENT: no`:
the insight tightens interpretation but does not displace B04's direct development question.
The DM retains the selected scope and all adverse/selection history. No B04 fit has started.

### Bounded continuation window explicitly authorized by the owner

After an automatic approval review rejected an unbounded recurring workflow, the owner
explicitly authorized a bounded one: 24 hours of 30-minute continuation in this task,
at most two new exploratory batches and twelve new fits including B04's six, with branch
publication and Jev Pro allowed, no main merge and no other direction launch. The accepted
window is **2026-09-20 04:06:07 UTC through 2026-09-21 04:06:07 UTC**. Any failed started
fit consumes this allowance. The scheduler prompt further limits each fit to 2048 episodes
of 256 steps and at most two focused Jev Pro questions in this window. A second batch is
not selected merely because capacity remains.

The native app accepted the active current-task heartbeat `ucope-24-12`. It must resume
saved progress and accepted handles, not recreate B04. At the time or fit boundary it
stops new result execution and reports; an explicit owner pause takes precedence. Native
in-flight operations and evidence are preserved. The initial rejection was not bypassed:
the accepted request is narrower and follows the owner's specific authorization. This
paragraph records the owner's execution boundary in the existing notebook, not a new
workflow registry or scientific claim.

The owner subsequently changed the heartbeat interval to **25 minutes** to reduce gaps
between continuations. The native app accepted that update; the same expiry, fit allowance,
direction and publication boundaries remain in force. No cache-lifetime guarantee is inferred.

### A timing-matched scalar bridge, zero native exposure

For the exact B eligibility law, take a constant KEEP probability q and independent,
zero-mean fresh commands of variance sigma squared, with no feedback, boundaries or
teammate coupling. Let h_t be the probability of a held command at tick t, with reset
h_0=0. Then h_t=q(1-h_(t-1))=q/(1+q) * (1-(-q)^t). A command can be copied only once,
so adjacent-command covariance is h_t*sigma squared and higher-lag covariance is zero.
For T ticks, displacement variance is sigma squared times
`T + 2*sum(h_t, t=1..T-1)`. At q=.5 and T=256 this is approximately **1.66493** times
the always-fresh variance, with 85.1111 expected held edges. Exact rational arithmetic
checked the recurrence against its closed-form sum. No native episode, checkpoint
evaluation or fit was used.

This maps the supplied temporal insight to B's actual forced-fresh law and supplies a
specific simpler explanation that remains compatible with a near-half scalar rate.
It is not a prediction of native state coverage or return: learned means, local feedback,
tanh commands, boundaries and coupled agents violate the simplified model. A positive
B04 package result would not by itself distinguish this temporal-noise path from learning
or phase effects.

### B04 engineering accepted before native execution

The Implementer delivered only the six new code/test files in the assigned scope. The DM
read the study differences from B03, the new runner and tests, and accepts the B/G dispatch,
absent-G-gate handling, fixed seed/exposure scope and publication contract. The unchanged
reactive B and ordinary G/H learning/evaluation paths remain recoverable at their original
source versions. No native smoke fit or diagnostic episode was used.

The focused synthetic check result is **32 passed in 3.26 seconds**: twelve new B04 checks,
thirteen B03 checks and seven reactive B01 checks. Compilation passed. An earlier combined
test collection encountered duplicate flat module names before executing tests; only the
new files were renamed to `test_b04_*`, after which the complete combination passed. The
DM's staged whitespace check, which also sees new files, then caught two trailing blank
EOF lines in test files and removed only those blank lines. This changes no executable
semantics and does not require repeated tests or review.

Independent read-only engineering review found no material issue in the final scientific
code, including inherited collector/learner calls, initialization/private RNG, information
and phase, evaluation isolation, checkpoint/hash identity, partial results and admission
ordering. It reused the focused check evidence. Actual native admission and forced-process
termination were not tested synthetically; those are limits of this engineering evidence.
The DM accepts the reviewed scope for exact-source publication and guarded native launch.
