Claim: On two retained trained DENSE bases, fixed cue-triggered retrace may improve native return over always-apply and same-cue dwell, warranting a bounded reuse follow-up.
Binding MARL structure: (d) multi-agent partial observability: each UAV acts on its own link history while teammates' simultaneous motions alter interference and service; their parameters remain fixed during this evaluation.

# ACVC fixed retrace reuse E01 — prospective card

Date: 2026-09-09. **PROPOSED, NOT FROZEN; no scientific invocation allocated.**
Requested class: a named B/EXPLORE exception for fixed trained-policy execution-rule
exploration, pending `em:acvc:convergence`. Current empirical-spec §§5.2 and 11.4 require
nonzero new learner updates, which this zero-new-fit proposal deliberately does not have.
It cannot silently become A or C. Preparation is read-only A/RECON plus card authoring.

## 1. Question, authority and smallest useful observation

The owner synthesis §§3.6, 4 ACVC and 5.3, relayed by Root on 2026-09-09, selected preparation
of C/F/dwell on the two existing DENSE/8201 and DENSE/8202 checkpoints. Root's follow-up
specifically requests a same-node scoped exception/interpretation under AGENTS §4.7 if
feasible. This card is the concrete proposal for that answer, not a local rule exception.

Would the fixed F package merit further reuse work after comparison with applying every
proposal and with withholding motion under the same rule? The simpler explanation is that
rejecting an away-pointing proposal helps, with retracing no better than zero velocity.
Comparing F to dwell has direct decision value without retraining a selector, searching
controllers, enumerating support or diagnosing every cause. Token training would change
the selected fixed-asset question rather than resolve its evidence-class conflict.

The [P80 end](ACVC_NATIVE_LINK_LOSS_P80_CONVERGENCE_INTAKE_20260909.md) remains applied to
the instantiated T/G selector, unchanged heads/objective and 512-episode training budget.
This proposal selects no T/G restart, old-host rescue, direction closure, recast, C promotion
or formal UAV-validation entry. Root retains Portfolio sequencing; recasts 2 persists.

## 2. Fixed inputs and complete controller semantics

The two available checkpoint paths, accepted-record paths, byte counts and SHA256 values
are in [CM feasibility](ACVC_FIXED_RETRACE_REUSE_E01_FEASIBILITY_20260909.md#checkpoint-availability)
and its [machine facts](ACVC_FIXED_RETRACE_REUSE_E01_FEASIBILITY_FACTS_20260909.json).
They were read and hashed without deserializing models. The historical finite/FP32 acceptance
is provenance, not a fresh model-load check. No new fit, retuning, checkpoint or base selection
is proposed. DENSE/8201 was originally selected with both old outcomes visible. Adding the
other retained DENSE/8202 after these results leaves an outcome-informed, selection-conditional
two-base set; it is not two new independent treatment/control training pairs.

Reuse the B01 card §2 native host, observations and action contract: five fixed UAVs,
50 users, 256 primitive steps, native team reward, the accepted NativeGeometryActor with
frozen FP32 parameters and five private recurrent states. At every step, including a step
whose proposal is overridden, sample the learned proposal b using the existing ordered
five three-dimensional Normal draws, learned clamped log standard deviation and tanh.
No argmax, zero-hidden-every-step, independent replacement policy or deterministic proposer
is substituted. At episode reset, zero the five hidden states and previous-command features;
after each step feed back that arm's actual sent command. Each arm owns its trajectory.

| Arm | Executed velocity |
|---|---|
| C | Always the sampled proposal b. |
| F | On the accepted `Binding.observe(obs, b)` mask, the returned retrace command; otherwise b. |
| dwell | On the identical predicate evaluated on dwell's own history and sampled b, zero xyz velocity; otherwise b. |

The accepted predicate retains one prior lowest-SINR non-saturated user coordinate, uses
only unambiguous coordinate matches in private observations, detects loss of the UAV's own
eligibility, and requires b to point away. Empty/reset/ambiguous cases do not qualify.
F reverses the UAV's **prior actual realized displacement**, divided by the existing 30-unit
velocity scale and clipped to the legal range. The source of record is
`experiments/candidates/acvc/native_link_loss_b01/binding.py`; its predicate is unchanged.
Dwell uses the same predicate function, not F's event times, matched counts or recorded mask.
Its zero command and distinguishability are recorded as dwell, never mislabeled retrace.

The causal path is joint motion/interference -> one UAV's private own-link observation ->
its retained anchor and sampled proposal -> apply/retrace/dwell -> new joint geometry,
assignment and teammate observations -> native team return. Own-link loss may represent
a useful handoff; it is not a label for global service failure. All five policies evolve
their recurrent state in their own joint rollouts, with no optimizer or partner retraining.
Roster membership, episode horizon and primitive-time reward remain fixed; no join/leave,
replacement, censoring or semi-Markov mechanism is introduced.

## 3. Proposed sample, RNG and observables

Run one serial process: DENSE/8201 C, F, dwell, then DENSE/8202 C, F, dwell. Each panel has
64 prespecified final episodes, with no checkpoints/endpoints chosen after seeing scores.
Use proposed evaluation masters 8911 and 8912 respectively; they are seed namespaces, not
new training instances. For base namespace m and episode e=0..63, all three arms reset with
`m*100000 + 2000 + e`. The two bases have disjoint panels. This pairs initial-world seeds,
not later endogenous events, which can differ with the trajectory.

Preserve existing private action-stream law with arm indexes C=2, F=3, dwell=4:
proposal seed `m*100000 + 30000 + 100*a + e`. The same ordered Normal-draw law runs on
each arm's own recurrent state. No common action-noise coupling or gate sampling is added.
Base construction uses the existing isolated `m*100000+14` stream before loading the fixed
state; each environment constructor uses `m*100000+60+a`, with its unscored reset recorded.
The [prospective facts](ACVC_FIXED_RETRACE_REUSE_E01_PROSPECTIVE_FACTS_20260909.json) calculate
all ranges and check for overlap with retained ACVC episode reset keys. This is source-data
arithmetic, not RNG initialization or proof that distinct seeds yield distinct world states.

Primary observables, reported **separately for each base**, are mean paired final native
F-C and F-dwell differences in J. Secondary dwell-C is retained for the simpler explanation.
Each row records `S = sum of 256 native rewards` and `J = S/256`, base, arm, episode and
reset seed. Keep every one of the 384 S/J outcomes. Conditional uncertainty for each contrast
uses the 64 paired joint-episode differences: sample SD divided by sqrt(64). It concerns
the fixed base and declared reset/action sampling, not a training-seed population. Do not pool
128 worlds as 128 trained policies, select the better base, or use an aggregate as the primary.
Opportunity/intervention/distinguishability counts describe exposure; they are not eligibility
filters for excluding returns and are not additional success gates.

## 4. MEI, predictions and reading rule

MEI is **0.01 J = 2.56 S**, chosen as a useful one-percentage-point native mean-reward scale
for deciding whether this small reuse comparison merits further work, consistent with the
recent native ladder. The historical **0.25 S = 0.0009765625 J** remains the original
old-host threshold; it is not an E01 rescue criterion. The current native host has no tuned
same-information baseline/upper headroom record. F is an attained comparator, not an upper.

Proposed rule, applied independently to all four primary contrasts and both secondary ones:

> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**, retaining the sign.

This is a descriptive investment rule, not a significance, equivalence or population test.
If F exceeds both C and dwell on a base, that supports the fixed retrace package on that base
and may justify a bounded follow-up. F above C but within or below dwell leaves motion
suppression competitive and weakens a retrace-specific reuse investment. Inside-MEI results
leave little observed practical separation at this budget. An opposite sign weighs against
reuse on that base. Mixed bases bound portability and remain separate; a bounded follow-up
does not require all four signs positive. The next decision must use the whole pattern and
actual cost. No branch allocates a run or establishes history necessity, optimality, stable
superiority or a pure cue/retrace causal effect.

Prospective DM probabilities for the corresponding contrast being UP: 8201 F-C .80,
8202 F-C .65, 8201 F-dwell .50, 8202 F-dwell .50. These are judgments informed by old
F-C gains and the untested dwell alternative, not empirical probabilities. Score against
all four observed branches if this card is later frozen unchanged. Owner prediction: not
taken (unattended); check relevant reviews at the later clean boundary.

## 5. Exposure and complete cost proposal

Machine-generated counts and exposure are in the prospective facts. Future proposal:
**2 retained base fits; 0 new fits; 0 training episodes/steps/optimizer calls; 6 fixed panels;
384 scored episodes; 98,304 team steps; 491,520 base-agent forwards; 6 base loads and
environment constructors with 6 unscored constructor resets; no gate or critic construction.**
The retained DENSE phases each had 512 training episodes at 256 steps; their earlier REL/DENSE/H
collection totals are preserved separately, never billed as new E01 work. E01 intentionally
has zero parameter displacement and no optimizer capable of moving in its budget. That
explicit exposure line requires the requested named exception, not an assertion that §11.4
is already satisfied. Preparation/consultation adds zero scientific exposure.

Dominant algorithm work: 2 bases x3 arms x64x256x5 base-agent forwards; F/dwell add at most
2 bases x2 rules x64x256x5x20x2 = **13,107,200** coordinate-pair checks. There is no candidate
search, alternate-trajectory evaluation, backward pass, recurrent optimizer replay or solver.

CM's retained 32-episode C/F panel windows imply per-64-panel references of 10.526871886 s
for C and 12.841401330 s for F. Dwell uses the latter as an **unmeasured proxy**. Six panels
plus retained startup/publication/exit allowance yield 91.171740593 s. Adding a proposed
30 s total focused synthetic-check/readback allowance gives 121.171740593 s nominal complete
work. Proposed cap: **180 s for the whole logical invocation**, including required checks,
imports, all loads/constructors, all six panels, publication and actual process exit. It is
one invocation, not six separately renewable caps. Both projection and cap are proposals,
not an allocation or measured dwell throughput. Dwell trajectory, base 8202 throughput,
new output/check overhead and node contention remain unknown. No timing pilot is proposed.

## 6. Prospective implementation, execution and stop boundary

Use the existing checkout `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`.
The [CM implementation map](ACVC_FIXED_RETRACE_REUSE_E01_FEASIBILITY_20260909.md#minimal-prospective-implementation-map)
identifies the bounded change: fixed-only runner `scripts/run_acvc_fixed_retrace_reuse_e01.py`,
minimal dwell support in owned `model.py`/`learner.py`, and a small per-base contrast reducer
beside existing `report.py`. Reuse the accepted base loading/collector and unchanged binding;
do not force the T/G training runner through a zero-training path. Source changes require
the later frozen feasible card and actual CM assignment.

Engineering-scope §4: **none needed**. Existing checkpoint input, count outputs, resource
admission and detached task route require no added guard, manifest system, retry machinery,
parallel executor or telemetry framework. Future source remains under 2,000 new research
lines and 600 runner lines. One proportionate focused synthetic check covers dwell command,
unchanged F, actual-command feedback, stream identities and per-base S/J reduction, reusing
accepted unchanged checks. It is part of the proposed 30 s allowance, not allocated now.

Host is portable within the existing native CPU FP32, torch intra/inter-op thread 1 contract;
default route is `.codex/hmasd-compute.toml` remote-first wsl_4070. No GPU/dtype or host change
is proposed. A later launch uses exact committed/pushed source, the two evidence files at
their declared digests, a detached exact-SHA worktree and fresh on-node memory admission
joined to the runner. Existing observation handover applies; no new supervisor is built.

The current assignment stops at published prospective card, accepted read-only feasibility
and ready same-node Pro handoff. No source edit, scientific evaluation, model load, training,
test or profile is authorized here. A full formed decision and conflict intake must resolve
the explicit class/family question before the affected requirement is applied. Later source
acceptance and a scientific allocation remain separate actions. If a future allocated run
hits its cap or has a defect, preserve intact returns and partial work, limit only dependent
claims, and return without an automatic retry, extra world or successor.

## 7. Knowledge use and claim ceiling

Scientific-tools scientific-reading used FOUNDATIONS §§2–4 and 6 and the empirical topic's
randomness levels and method-versus-component comparison passages. Fixed parameters do not
make the recurrent sampled controller static or untrained; evaluations are conditional units;
joint trajectory feedback limits component attribution. These points determine the own-arm
mask/feedback rule and separate-base uncertainty above. Prior verified ACVC DACOM/CoDe retrieval
is reused only for competent same-information comparator reasoning, not as evidence that
dwell or retrace works here. No unresolved primary-source claim requires a new corpus search.

Ceiling if executed under a formed scoped exception: preliminary native execution-package
signal or counterexample on these two selected retained bases and the stated fresh panels.
F-versus-dwell compares complete closed-loop rules. It cannot isolate history necessity,
counterfactually matched cue events, learned-selector value, partner co-adaptation, tuned
headroom, stable training-population performance, optimality, transfer or whole-direction merit.
