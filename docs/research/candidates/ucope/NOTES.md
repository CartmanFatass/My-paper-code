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
