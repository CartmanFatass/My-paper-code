Continuing ordinary G from update 128 to fixed update 512 may change its sampled native utility relative to fixed readiness on the public shared-service task.
Binding structure: temporal abstraction / termination at fixed N=2; an eight-tick shared-slot submission changes the partner's feasible opportunities and remaining team return.

# VSP03 B06 — three fresh continuous512 fits with fixed 128/512 panels

**B/EXPLORE, scientifically selected and frozen; the complete implementation and
three-fit batch is now allocated by Root.** Convergence selected option (a) in the complete
[response](pro_packets/20260909_continuous512_convergence/archive/RESPONSE.md)
at **`5af9c448879bba3129df32e07a788839658f8a4f`**. Root's 2026-09-09 intake
assignment explicitly authorizes freezing this card and returning a ready CM
proposal, with no fit allocated. [Decision intake](VSP03_CONTINUOUS512_CONVERGENCE_INTAKE_20260909.md)
records application and the close call. **Recasts: 1.**

Allocation update: Root's [2026-09-09 synthesis-execution decision, final VSP03
section](https://github.com/CartmanFatass/My-paper-code/blob/be3061829b0465054f6007a27d8167c541c71fba/docs/research/portfolio/decisions/2026-09-09-synthesis-execution.md#vsp03-selected-b06-now-explicitly-allocated)
now assigns the original DM/CM implementation, focused checks within the existing
cumulative 300 s directory allowance, required independent semantic review,
exactly one detached invocation per named fit, and complete intake. Main audit
row 172 records that allocation. No extra source-approval step, test-budget reset
or scientific-validation allowance is added. All scientific definitions and
failure/stop bounds below remain frozen; statements about no allocation at the
earlier freeze describe that historical boundary. No invocation has started at
this allocation update.

## 1. Question, selection and preserved pauses

Does continuing the same real training process from 128 to 512 updates change
the native comparison enough to reconsider ordinary greedy G against R0 and R?
The primary is **fixed update-512 greedy G minus R0**. The explanatory contrast
is the within-fit 128→512 change. The extra budget includes 384 new training
batches, optimizer updates and partner co-adaptation; it does not isolate pure
optimization on fixed data or prove that update 128 was undertrained.

This is an outcome-informed new budget question, with its three fresh fits and
fixed endpoints specified before their results. The old independent update-128
append sequence remains paused, including its unselected seed-8 alternative.
N1 and T/initialization pauses remain. This finite re-entry opens only this
three-fit package within the accepted shared-service mechanism. It is not a
second recast, a reopening of all ordinary-G work or a Portfolio disposition.
Old seeds 5/6/7 remain a separate mixed-128 record; seed 4 remains discovery.

One continuous fit would be a legal local B observation. Three are the owner's
specified bounded candidate, adopted by Convergence to observe the budget
question on three learning paths. Three are not a minimum evidence quota, a
requirement to obtain three successful runs or evidence of stable superiority.

## 2. Environment, information, learner and comparison

Reuse [P76 card §§2–3](VSP03_B05_P76_SCIENCE_CARD_20260909.md), frozen at
`3eda7ac6dd9d1f888ccff7799d5616e0eb19867f`, and its accepted source at
`32ce8a7355b86bee64956e3d24b76d01c31a8d77`. The
[CM feasibility record](VSP03_CONTINUOUS512_CM_FEASIBILITY_20260909.md) identifies
the b01 objective, b02 model/world/rollout/rules and b03 loop entry points.

Two fixed controller/job identities own one job each, with public offset
opportunity clocks. Both targets evolve all 40 primitive transitions. Occupied
targets leave with probability 1/(d+4); absent targets return with probability
1/2. An accepted one-shot SUBMIT occupies the sole slot for eight transitions,
including on failure. Release/completion precedes the next decision. Forced
waits have no gradient row. Target absence/return is not entity or roster churn;
pending means the job has not yet submitted, as in the accepted source.

Actor and critic see the same 14 public own/partner event, readiness and clock
features, without future tapes or hidden success information. Both controllers
co-adapt one shared G during learning and freeze it for evaluation. Valid actions
receive actual remaining team return through t=40, subtracting already accrued
reward: gamma=1 and zero terminal bootstrap. Native utility is the two jobs'
`200*success - 10*attempt - waiting_ticks` sum divided by 400. Submission changes
the partner's slot access, opportunities and native outcome. Public centralized
scheduling remains a surviving interpretation, without an isolated MARL cause.

Keep the generic **2,083-parameter** model: actor/direct 1,570 and critic 513;
current initialization; Adam lr=0.001, betas=(0.9,0.999), eps=1e-8; unchanged
actor/critic objective. No clipping, normalization, replay or extra epochs.
Each 128-episode batch receives one real backward call and Adam step. Keep the
global entropy coefficient **`0.01*max(0,(64-update)/63)`**, zero from update 64
through 512. Do not stretch or restart it with the new training horizon.

Keep **one model and one Adam instance for updates 1…512**. After the update-128
panel continue at 129, without reseeding, reinitializing, reloading or resetting
optimizer state. R0 submits on a legal opportunity when own b=1. R adds the
existing yield to a pending, currently ready, strictly older partner with a
future opportunity, submitting on age ties. Greedy G submits iff **logit>0**,
continuing on ties. The two fixed rules are unchanged same-information controls,
neither tuned nor upper references. Stochastic G remains a separate mode.

## 3. Fresh fits, randomness, fixed panels and retained outputs

Fit keys are **10801 / 10802 / 10803**; Torch initialization keys are
**50801 / 50802 / 50803**; G arm is 1. No old weights, optimizer, worlds or RNG
state load. World tapes use PCG64 with SeedSequence
`[302,fit,split,episode,target]`, 40 uniforms per target; phase uses
`[302,fit,split,episode,2]`. Train split 100 has episodes 0…65535; update u begins
at `(u-1)*128`. Eval split 200 has worlds 0…1023. Fit keys separate all three
initializations and data generations. Train and evaluation address spaces differ.

Action tapes use `[303,fit,split,mode,1,episode]`, 17 calendar-position uniforms.
Training mode 0/split 100 and stochastic evaluation mode 1/split 200 differ.
Within each fit, both endpoints use the **same 1,024 evaluation worlds, phase
and stochastic action tapes**. This intentional pairing never feeds learning.
Greedy G and rules consume no action tape. Independence follows the generation
design, not the spelling of the keys. This freeze constructs no numeric RNG.

Immediately after completed Adam steps **128 and 512**, evaluate **greedy G,
stochastic G, R0 and R once each, on 1,024 worlds per mode**. Use fresh environment
arrays and no gradients. Evaluation cannot change parameters, optimizer state,
training RNG or update index. The reused MLP has no dropout, batchnorm or recurrent
state. Execute and count both rule panels even though their paired-world outcomes
are deterministic. No panel selects a checkpoint, tunes, stops or adapts learning.

Retain checkpoint-keyed native rows, four absolute means and all five contrasts
(greedy−R0, greedy−R, stochastic−R0, stochastic−R, stochastic−greedy), conditional
paired-world SD/SE, success/attempt/waiting and original opportunity/blocking
accounting. Retain 512 stochastic training-curve rows per complete fit, actual
decision/gradient/forward counts and initial, first-step, 128 and 512 parameter
scale/displacement. Curves are training returns, not 512 held-out evaluations.

Save exactly the two selected 128/512 weight snapshots, serializing detached
tensors at their actual boundaries. Do not hold a live state_dict until after
further learning, overwrite the 128 panel, construct another model for snapshots
or add optimizer/resume/all-intermediate checkpoints. A partial fit retains only
the artifacts and counts actually produced.

## 4. Primary, paired budget contrast and reading rule

For fit i, endpoint u and world e, define
`d(i,u,e)=J(G greedy,i,u,e)-J(R0,i,u,e)` and
`D(i,u)=mean_e d(i,u,e)`. The per-fit primary is **D(i,512)**. Report every
complete primary separately. Only with all three complete 512 endpoints report
the selected three-fit arithmetic mean and descriptive sample SD (ddof=1).
All other contrasts and four absolute means remain visible at both endpoints.

For the explanatory change use **`b(i,e)=d(i,512,e)-d(i,128,e)`** and
**`Q(i)=mean_e b(i,e)=D(i,512)-D(i,128)`**. Compute conditional SD directly from
these paired b values with ddof=1; **SE=SD/32**. The two panels are dependent;
summing their SE variances as if independent is incorrect. R0 cancels
algebraically on identical worlds, but retain its actual panels. No bootstrap,
extra worlds or new statistical service is needed. No variance-reduction amount
is promised. Report the three Q values and any descriptive aggregate as such.

The independent training unit is one continuous fit: three units, not six
checkpoints or 24 mode panels. World uncertainty describes fixed policies and
the specified action randomness. Across-fit SD also contains evaluation noise;
it is not pure training variance. Do not pool old 128 results into this package,
select a best checkpoint/fit or relabel this exploration as confirmatory.

**Reading rule:** final 512 greedy G above both R0 and R supports the sampled
longer-budget controller; above R0 but below R supports only the R0 comparison.
Positive Q with native accounting supports budget-sensitive improvement along
these paths, even when 512 still loses to rules. An endpoint gain with small or
negative Q supports that endpoint without showing that continuation produced it.
Flat, adverse or mixed Q does not establish convergence, policy-class limits or
optimizer failure. Inside-MEI values retain their signs and sizes. A zero/adverse
final primary favors readiness for that sampled comparison. Stochastic losses
limit a greedy gain to its declared mode. Preserve every outcome and failure;
neither all-positive fits nor a significance test gates the reading.

If 512 is missing, retain the reason, actual counts and trustworthy 128 panel.
Do not substitute 128, zero or another checkpoint, or count missingness as a
scientific negative. Other complete 512 endpoints remain reportable; any subset
summary declares actual n and does not masquerade as the three-fit mean or assume
random missingness. If only 128 is untrustworthy, retain a trustworthy 512 endpoint
but mark Q and its dependent interpretation missing. This creates no replacement
or three-success requirement.

Claim ceiling: sampled finite-budget native performance of these learned
controllers, not stable superiority/inferiority/equivalence, a unique MARL cause,
exact optimum, initialization value, asymptotic convergence or C/UAV/deployment.
No result automatically authorizes more fits, 2048 updates, diagnostics or a
family disposition; the next direction choice follows all-outcome intake.

## 5. MEI, headroom, prediction and interpretation

MEI is **0.02 absolute native utility**, equivalent to eight total waiting ticks
divided by 400. This interpretable scale avoids unstable relative ratios and is
not an equivalence, validity or follow-up gate. **Tuned current-N2 headroom is
absent, not zero.** The reused R0/R observations match information, action and
world law; rules require no learning budget and supply no tuned upper.

Frozen low-confidence prediction: **`abs(mean_i D(i,512))<=0.02`**. It predicts
the complete three-fit mean's magnitude, not positive signs, monotonic learning
or every fit's absolute magnitude. Score only if that mean is available; otherwise
record unscored with the missing facts. Owner prediction: **not taken
(unattended)** at freeze; score a relevant later reply at intake if one exists.

A beyond-MEI final gain over both rules, especially with positive Q, would
strengthen a concrete bounded follow-up proposal. Small or mixed effects retain
their measured evidence; adverse final points favor readiness for this package.
DM then identifies the remaining question, without automatic escalation. The
strongest contrary case is that competent readiness is sufficient and more
training buys only small, uncertain or adverse native tradeoffs. Both old small
gains and the larger seed-5 loss remain; choosing this close call does not prove
that longer training is better or that the old pause was erroneous.

## 6. Work, cost, execution boundary and stop

[Selected counts](VSP03_B06_CONTINUOUS512_COUNTS_20260909.json) retain the
machine-generated configuration arithmetic and the CM's source-aware cost law.

| Work | Per fit | Three fits |
| --- | ---: | ---: |
| New models / real backward calls / Adam steps | 1 / 512 / 512 | 3 / 1,536 / 1,536 |
| Training episodes: 512×128 | 65,536 | 196,608 |
| Evaluation episodes: 2×4×1,024 | 8,192 | 24,576 |
| Total episodes | 73,728 | 221,184 |
| Training team ticks / target transitions | 2,621,440 / 5,242,880 | 7,864,320 / 15,728,640 |
| Evaluation team ticks / target transitions | 327,680 / 655,360 | 983,040 / 1,966,080 |
| **Total team ticks / target transitions** | **2,949,120 / 5,898,240** | **8,847,360 / 17,694,720** |
| Rollout model batch-call upper | 8,772 | 26,316 |

The dominant factors are 3×512×128×40×2 training work and
3×2×4×1,024×40×2 evaluation work. The model-call bound excludes objective/critic/
backward; rules make no model calls. Actual eligible/gradient rows depend on
behavior and are reported, not filled to a quota. Added scientific-validation
models/episodes/updates/evaluations are 0/0/0/0. No search or nested solver exists.

Complete cost includes admission/import/startup, initialization, 512 training
batches, two four-mode panels, snapshots/readback/publication, actual exit and
descendant termination. Retained P67/P76 complete wall is 3.253184/4.191728 s;
unit CPU is 3.278770/3.500596 s. Fourfold complete-path projection is
**13.012736–16.766912 s per fit; 39.038208–50.300736 s summed for three**.
Training increases 4×, panels 2× and total ticks 3.6×. This is a planning
extrapolation, neither a measured upper nor a statistical interval or guarantee.
Future runtime, resource use, learner movement, return and unmeasured authoring/
collection work remain unknown.

Each complete fit has a **60 s cap**, measured from the earliest manager start,
including admission through actual exit and descendants. Reuse the single-origin
adapter: **work 50 s, cleanup 58 s, hard kill 59 s**, all within 60 s. Align the
driver to that same work clock; no inherited 120 s limit or reset at 128.
**180 s is the sum of three complete-fit caps**, not study elapsed or a new
global deadline. Record study elapsed and summed invocation wall separately.

When Root allocates implementation/execution, use three separately detached
exact-SHA invocations on **remote-first wsl_4070, CPU float32, one compute thread;
float64 worlds**, following current `.codex/hmasd-compute.toml`. Each fit requires
fresh same-node physical/effective memory admission ≥4 GiB immediately before
scientific construction, in the exact `agent-task` command joined by `&&`.
Commit and push source before launch; do not stage uncommitted runnable bytes.

The eventual finite batch permits **at most one accepted invocation per named
fit**, all three planned regardless of return signs. Completion, refusal,
failure or timeout ends that fit's allocation: no retry, replacement, resume,
fallback, extra evaluation, calibration pilot or fourth fit. A concrete shared
defect affecting reward, information, comparison, learning or primary measurement
pauses dependent launches for repair/allocation reconciliation. Preserve trusted
partials and unaffected evidence. No fit is allocated by this freeze.

## 7. Engineering scope, acceptance and next owner

**ENGINEERING_SCOPE_SPEC §4 needed:** reuse the existing task-local deadline/
termination adapter for **complete per-fit wall ≤60 s including publication and
descendants**. No other §4 machinery is needed. Keep 2,000 new non-test lines per
attempt, 600 per runner and the existing cumulative five-minute research-directory
test allowance (runner smoke excluded). The 30% orchestration share is a review
signal. This object grants no new test allowance or validation invocation.

Use a thin new continuous driver, preserving old frozen runners and accepted
environment/reward/information/rule/lifecycle evidence. Future proportionate
acceptance focuses on continuous model/Adam/global update state, nonmutating
evaluation, private addresses/common panels, primary and Q output, immediate
snapshot bytes and the one 60 s clock. Required independent scientific-code
review remains with CM. No test, smoke or profiling invocation occurs here.

The existing adapter's raw technical object label `VSP03_B04` may remain as the
declared inherited envelope; B06 card, fit key, exact command and unique outputs
identify the science, as in the accepted P76 reuse. Do not rewrite old receipts
or add identity machinery. New run roots, handles, launch SHA and admission
receipts will be recorded by CM at actual allocation; none exists at freeze.

The selected source/knowledge use is unchanged from
[candidate §7](VSP03_CONTINUOUS512_CANDIDATE_SCIENCE_CARD_20260909.md#7-engineering-scope-and-conceptual-use):
FOUNDATIONS §§3–6 and empirical topic distinguish fit from checkpoint, fixed
endpoint from selected maximum, and finite training from representational or
convergence claims. Reuse P74's relevant local literature; no new mechanism,
comparator or novelty claim demands a new search. Evidence-spec §§4, 5.2,
11.4 and 11.7–11.10 governs the claim, without extra launch conditions.

Reuse checkout `C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907`, branch
`codex/pro-vsp03-shared-service-convergence-20260906`, and the original CM.
[Ready CM proposal](VSP03_B06_CONTINUOUS512_CM_PROPOSAL_20260909.md) names future
ownership and acceptance. Root owns finite allocation and integration; CM owns
implementation, collection and technical acceptance; the configured independent
monitor adopts actual accepted handles; DM owns all-outcome scientific intake.
The exact next discriminator is this selected three-fit, two-panel comparison.
