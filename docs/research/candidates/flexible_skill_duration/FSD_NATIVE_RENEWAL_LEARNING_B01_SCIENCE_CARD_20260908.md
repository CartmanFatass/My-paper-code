Claim: After five rollouts of fresh learning on the large K2 corridor, the public-flag applied-renewal control package may improve mean native return over internally applied D2 by more than .01.
Binding MARL structure: (b) temporal abstraction or termination; internal skill segments and physical leases can renew on different clocks while each learner sees its own multi-agent trajectory.

# FSD_NATIVE_RENEWAL_LEARNING_B01 — prospective B/EXPLORE

## 1. Authority, question and present boundary

This is the single early-learning question selected by PRO_FINAL, not a recast or a
whole-family reopening. The immutable decision is
[`RESPONSE.md`, sections 三–六](pro_packets/20260907_post_native_control_convergence/archive/RESPONSE.md)
at `eaff53a10b21383fb682f63bcf58782875599ff0`; its full intake is
[`CONVERGENCE_INTAKE.md`, sections 3–7](pro_packets/20260907_post_native_control_convergence/CONVERGENCE_INTAKE.md).
[P30](../../portfolio/handoffs/2026-09-07-p30-fsd-native-renewal-learning-spec.md)
authorizes this card and implementation specification only. No code implementation,
CM dispatch, scientific invocation or Pro Send is allocated by this preparation.
The prospective scientific definition is recorded before new results. B has no
confirmatory consumption state.

P34 implementation/readiness update (2026-09-08): the preparation-only coding
boundary above was superseded by the named P34 implementation assignment.
Reviewed source `b3f86bb28879db239b07291c39d93a1c494abe50` is integrated on main as
`0e731dbbd30ee6ec68f70f0d54e40a0dd3fc2c3f`. The 445-line runner and 18 passing
synthetic tests have technical acceptance, with both publication findings repaired.
See [technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B01_TECHNICAL_ACCEPTANCE_20260908.md)
and [P34 DM intake and exact next allocation need](FSD_NATIVE_RENEWAL_LEARNING_B01_P34_INTAKE_20260908.md).
No real model/host/learner/evaluation or Pro invocation has occurred. The scientific
definition, prediction and caps below are unchanged; runtime is still unallocated.

P38 allocation/binding update (2026-09-08): [P38](../../portfolio/handoffs/2026-09-08-p38-fsd-learning-b01-execution.md)
now allocates exactly one G/C/H panel on the unchanged reviewed source and keys.
The [published Root handoff](FSD_NATIVE_RENEWAL_LEARNING_B01_P38_ROOT_HANDOFF_20260908.md)
at `fef65041172d2a6e5de4c35c1b09d612b9d1f9ac` binds committed LF scripts, their
verified remote bytes, the fresh exact-source cwd and once-only handles. Root
launches/observes; the same CM collects every outcome and the DM completes intake.
The outer OS caps include admission through closed-file publication: G60s,
C900s,H900s; sum1860s. Actual acceptance and results follow Root's existing record.
CM preparation ended with zero new scientific exposure and absent handles/root;
transport/source checks and the reused P34 tests are not a learning result.

At this object-tier boundary the options are (a) accept the conforming binding
and execute the named P38 route, (b) return a concrete binding/integrity gap,
or (c) add another probe or readiness requirement. Recommend/select (a): direct
inspection of the published script literals and outer command confirms the
source, keys, argv, complete caps and failed-arm independence; CM supplies the
remote byte/cwd facts. No concrete gap was found. **Owner-delegated decision
(unattended, 2026-09-03 instruction): (a).** Owner reviews were empty in the
primary and direction checkouts; relevant audit owner cells remained empty.
No new P1/P2 item is due for this ordinary object decision. No fourth comparison,
retry, extra arm/seed/evaluation, cap increase, Pro Send or UAV change follows.

P38 result/intake update (2026-09-08): all three allocated arms completed within
their admission-inclusive caps. The [E0 result](FSD_NATIVE_RENEWAL_LEARNING_B01_RESULT_EVIDENCE_20260908.md)
and [scientific intake](FSD_NATIVE_RENEWAL_LEARNING_B01_INTAKE_20260908.md) accept
one valid B/EXPLORE pair in the above-MEI branch: full H−C+.49738281249999894,
conditional episode SE.00864640484198601; post+.49862938596491124. Full/post
G−H remain.021184895833334313/.0187317251461998. The claim is a native control-
package difference after fresh learning on this pair; the public rule was given,
and no stable training-seed, learned-renewal, D0 or UAV conclusion follows.
P38 is complete; B has no consumption state. The recorded next discriminator
advice is one independently trained pair under a separately issued preparation/
allocation, with all signs retained. No successor is frozen or launched here.

Question: does a fixed public applied-renewal rule retain a useful native return
difference after repeated real, from-scratch learning under that rule, against the
same internally defined D2 learner which applies its own sampled mask? The public
rule is supplied by the design; it is not a learned renewal policy. The primary
comparison is the total consequence of each training and deployment package.

The complete starting code is `ebce42e23e8a86b4e8d44f840441d166828fbe54` in
`C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`. It reconciles P30 main
inputs with accepted direction code, including the A01 runner. The companion
[CM specification](FSD_NATIVE_RENEWAL_LEARNING_B01_CM_SPEC_20260908.md) owns the
future implementation boundary. Existing A01, E3 and E4 rules and results retain
their original meanings. The contradictory blocker archives and one-Send receipt
remain under the P25 packet; this task does not resend or rebind that request.

## 2. Population, information, learner and comparator

Use `proposal_config("large")` on the existing Bernoulli corridor: N=6 fixed
entities, three per region, two regions, four host zones, K=2, H=400,
hazards=(.02,.20), Delta=1, rho=0. Entity/zone/region ownership is fixed; there is
no membership change, join/leave/rejoin, replacement, churn, probe, censoring or
E5 coupling. Continuous two-component actor actions become roles by the existing
argmax decode. Preserve the public flag/cue and current observation/state fields;
no future event tape, hidden role target or G supervision enters a learner.

Both learned arms use the full existing HMASD coordinator, recurrent actor/critic,
team and individual discriminators, with n_Z=6 team tokens, n_z=2 and action_dim=2.
Four host zones do not mean four team tokens. Both use internal D2 with c=c_Z=.25,
individual/team caps=40/400, interruption_delta=1 and age feature off. All other
networks, losses, intrinsic reward coefficients, gamma=.99, GAE lambda=.95,
PPO/optimizer schedules and default settings are the bound E3/E2 configuration.
Observation/state normalization remain off; ValueNorm remains on and arm-local.
CPU with four Torch threads, float32 learner and float64 host/shared reward apply
from construction through publication. GPU, precision and host searches are absent.

| Policy | Training | Applied renew in both collection and final evaluation |
| --- | --- | --- |
| C_train | One fresh real learner | Copy its authentic internal `d2_sampled_mask` to the host. |
| H_train | A separate fresh real learner | Run its own D2 and actor normally; at episode t=0 use normal forced-reset renewal, and at t>0 use the current public regional change flag for each entity. |
| G | None | Existing `GreedyOnPublicState` uses its legal public information on its own same-key host. |

H retains its actor's actual continuous actions. It does not insert G roles,
copy C trajectories or reset internal state when a public flag renews a lease.
Internal masks, sampled log probabilities, timers, decision metadata and segment
credit stay authentic. Only the applied host mask differs. Subsequent segment
counts and optimizer work may differ because H collects its own trajectory.
This is not claimed to implement a physical-lease termination gradient.

The event-to-native path is: exogenous regional event invalidates fixed entities'
leases → public flag/cue and this arm's actual observation/state → internal skill
decision and actor action → selected applied renew plus role in the host → this
arm's actual shared reward and next observation/state → real transition storage,
existing internal segment returns and updates → updated policy's next rollout.
Existing internal semi-Markov discounts and credit remain in the bound learner;
physical renewal never rewrites segment duration or creates an optimizer update.
Primitive scoring time is 400 steps per episode; post-reset opportunity reporting
uses 399 steps and each arm's own actual KEEP/fresh opportunities.

C is the matched package comparator, not a tuned strongest fixed-clock baseline.
G is the same-information public reference on this host, not a trained D0 arm.
No baseline tuning, policy maximum, exact support census, extra diagnostic panel
or unique causal account is needed for this B question.

## 3. Prospective RNG, training and endpoint selection

The paired training seed is **770203**: seed Python, NumPy and Torch separately at
each arm's start with that value; learner config seed and training-host master are
also 770203. Each arm starts from scratch with separate optimizer and normalizer
instances. The same construction sequence supplies paired initial parameters;
only initial randomness and the exogenous keys are paired. Subsequent learner
RNG, hidden state, actions, host state, data and updates belong to that arm.

Each arm completes exactly five rollouts × 16 lanes × 400 steps. Training episode
IDs are 0–15, 16–31, 32–47, 48–63 and 64–79 under master 770203; existing keyed
episode advancement is used. Record the IDs consumed, before reset advances them.
Store the real terminal transition first, then obtain both fresh reset observation
and fresh reset global state, resetting the appropriate lane's internal state.
No terminal-state/reset-observation mixture is permitted in the next policy input.
Resetting after the final terminal may prepare unused IDs 80–95; those are not
additional completed episodes or training exposure.

Perform the actual existing update after every rollout, then clear the buffers.
Five stages are not five `optimizer.step` calls. Report each rollout's native
return, actual optimizer calls by network, coordinator inference/segment counts
and parameter displacement relative to the arm's initialization; report initial
norms and at least the first and final displacement without thresholding success
on the amount of parameter movement.

Evaluate only the endpoint after the fifth update. The evaluation master is
**770204**, episode IDs **0–31**, shared by C_train, H_train and G. These are new
keys, distinct from training and the previously observed A01/E3 evaluation
masters. This numerical seed choice is prospective but the design is informed by
old outcomes; it is not independent confirmatory discovery.

Each trained arm constructs one independent 32-lane evaluator agent and copies
its own final active modules and enabled normalization state, including both
ValueNorm objects. Preserve learner Python/NumPy/Torch RNG around evaluator
construction, synchronization and evaluation. Set `train(False)`, deterministic
actions, no gradient or statistic updates, empty buffers and reset every lane.
Each policy has a separate fresh adapter/host; no state tapes are exchanged.
There are no old checkpoint loads, intermediate evaluation, checkpoint selection,
resume, distillation or automatic extension from one rollout to five.

## 4. Primary observable and secondary quantities

For policy p and each evaluation episode e, full native return is
`R[p,e] = sum(t=0..399) shared_reward[p,e,t] / 400`. The primary 32 paired values
are `d[e] = R[H_train,e] - R[C_train,e]`; retain all values, their mean and
`std(d, ddof=1) / sqrt(32)`. The independent training unit is **one trained pair**.
This SE measures evaluation noise conditional on that pair, not training-seed
uncertainty. Episodes, agents and five rollouts do not increase the training n.

Retain each policy's 32 full and post-reset `sum(t=1..399)/399` returns and all
H−C, G−H and G−C paired differences/means/SEs on each time basis. Keep signs and
small effects visible; do not pool old A01 values or infer a retention fraction
from its different trained artifact and keys.

From the actual step's `renew_mask`, `lease_fresh` and `role_correct`, define
`eligible = KEEP & lease_fresh`, `wrong = eligible & !role_correct`. For each
trained arm and episode report full/post eligible and wrong counts, conditional
`wrong/eligible` (NA/null when eligible=0), and post-reset reward-unit loss
`Delta * wrong_post / (399*N)`; full uses `400*N`. Also give pooled counts/rates
with the same zero-opportunity rule. The two arms' opportunity sets can differ;
do not compare conditional rates as if they used a fixed common population.
Count internal and applied renew separately, full and post-reset. Record actual
training internal/applied counts by rollout as well.

Report the observed G−H versus H wrong-role-loss correspondence as reward
accounting, allowing a visible residual if they differ. It is neither a required
zero residual nor a unique actor/credit diagnosis. No full action/logit/hidden
or per-step state archive is required.

## 5. MEI, headroom, interpretation and prediction

MEI is **.01 absolute mean native reward**: one percentage point of service when
Delta=1, above the .0025 scale of one reset step. It is descriptive, not a
significance/equivalence test, a universal investment threshold or an inherited
A01 branch. A tuned generic baseline/upper-reference headroom record is absent.
Existing E4 public-greedy references and A01 G shortfalls describe this host, but
do not supply such a tuned-learning headroom pair. No tuning is added here.

Reading rule, applied to a complete trustworthy five-rollout comparison:

| Observed full H−C mean | Reading and recommendation |
| --- | --- |
| Greater than +.01 | Report a local total-package gain above this MEI alongside SE, G gaps and role loss. It is a candidate for a separately decided bounded follow-up; do not launch it automatically. |
| Between −.01 and +.01, inclusive | Report the sign, magnitude, episode spread and conditional SE as a small or resolution-limited observation. Complete this object's intake; do not call equivalence or add episodes/seeds to seek a sign. |
| Less than −.01 | Report the opposite-sign early-learning result and preserve all outcomes. Do not extend this hybrid on the strength of A01 alone; it is not a theorem about every seed or longer budget. |
| Missing/damaged required learner or primary pair | No complete learning H−C polarity. Preserve trustworthy narrower arm/G/count facts, describe the dependency and return for a decision. |

Within any positive branch, large G−H or wrong-role losses remain a material
service shortfall. Above the MEI would support only this realizable difference
after fresh early learning; inside it would not settle equivalence; the opposite
sign would weaken using the old fixed-weight gain to justify this budget. None
identifies what fraction comes from the direct public rule, data distribution,
updates or learned competence. None establishes learned renewal, D2 mechanism
success, superiority to D0, convergence, stable seed-population advantage or UAV
transfer. Every branch ends with intake, not an automatic next seed, arm or budget.

DM prediction before execution: low-confidence H−C > .01, with a positive G−H
shortfall still present. Support is the old +.26935 native control gain, conditional
on a selected artifact. Contradictions are its .16403 G−H gap, H's higher wrong-role
loss/rate on its own altered opportunities, and six competent E3 learning losses.
No empirical prediction is scored yet; owner prediction: not taken (unattended).

P38 prediction score: the two prospective low-confidence directional predictions
agree with this pair (H−C>.01 and G−H>0). This is not a quantitative forecast hit
or independent confirmation. No owner prediction reply was present; the owner's
slot remains not taken (unattended). The pre-run prediction above is preserved.

## 6. Exposure, costs, resource route and stops

The machine-computed [exposure/cost record](FSD_NATIVE_RENEWAL_LEARNING_B01_EXPOSURE_AND_COST_20260908.json)
is the count source. Current preparation exposure is scientific invocations=0,
model constructions=0, checkpoint loads=0, training starts/transitions=0,
optimizer calls=0, evaluation episodes=0 and Pro Sends=0.

P38 actual exposure, separate from that preparation:3 scientific invocations,
2 training starts/4 total agent constructions,64000 stored training transitions,
160 training episodes,10 update stages,10860 network optimizer calls,96 endpoint
episodes/38400 scoring steps,102400 combined host steps and614400 agent
observations;0 loads/evaluator optimizer calls/new Pro Sends. Complete process
walls G2.47s,C371.89s,H333.89s sum708.25s; all caps/admissions passed. First/final
per-network displacement, raw32-entry primary vectors and receipts are linked
from the result;32 evaluation episodes do not change the one-training-pair unit.

| Prospective work | Quantity |
| --- | ---: |
| Learned arms × paired training seeds | 2 × 1 |
| Per learned arm training | 5 × 16 × 400 = 32,000 transitions; 80 episodes |
| Both arms training | 64,000 transitions; 160 episodes; 10 update stages |
| Final C/H/G evaluation | 3 × 32 × 400 = 38,400 scoring steps; 96 episodes |
| Training plus evaluation | 102,400 environment steps; 614,400 agent-step observations |
| Learner / independent evaluator agent constructions | 2 / 2, all charged; training starts remain 2 |
| Learned controller step batches / G batches | 4,800 / 400 |
| Complete invocation caps | C 900 s; H 900 s; G 60 s; summed 1,860 s |

Dominant algorithm work is those batched collection/evaluation calls plus actual
segment-dependent updates for six entities; no candidate/trajectory/controller
search multiplier is added. Native internal segment/optimizer counts remain
unknown until measured. Existing buffer sizes or k_max are not those counts.

The old per-arm planning law is `1.15 * [L*(64.6+.769*M_arm)+.46*E]`, L=5,E=32;
the effective new M is unmeasured. For **each** C/H arm the historical five-rollout
scale anchor is 505.86596735480975 s, not a verified new-route projection or a
completion guarantee. Historical G wall is .27 s, also only an anchor. The
prospective 900/900/60 s limits are the selected willingness-to-spend bounds.
Keep unknown work visible; do not add a cost probe, profile, A01 repeat or derive
M from k_max, nominal high-level buffer size or `rows_M` without justification.
This preparation projection did not allocate execution; P38 now allocates the
single panel above without changing this cost uncertainty or adding calibration.

Later allocated execution uses `.codex/hmasd-compute.toml` remote_first on the
enabled `wsl_4070` node, detached exact committed-SHA checkout and existing
`agent-task`. CPU/four-thread/precision semantics are pinned; physical machine is
not the estimand. Portability is declared before output; only the existing
no-accepted-remote-process/fresh-local-admission fallback is allowed. Each actual
invocation has immediate physical and effective memory >=4 GiB admission on its
execution node, joined to the runner by `&&`. Commit and push exact source first.

Every invocation cap includes admission, interpreter/import, configuration, all model and
optimizer construction, real collection/update, independent endpoint evaluator
and normalizer synchronization, required comparisons and publication. Nothing is
moved to an uncharged initialization, follow-on aggregation or validation run.
Normal execution stops after five updates plus one endpoint and publication, or
at the complete cap, a nonfinite learner/primary return, or a concrete defect in
reward, information, authentic updates or the primary comparison. Preserve
partial counts/logs/output. A cap hit never licenses a shorter complete result,
stitched resume, new seed, cap increase or automatic rerun. Missing one learned
arm prevents a complete H−C learning result; missing G limits reference claims
without erasing an independently trustworthy H−C. An adverse valid result is not
quarantined. Optional RSS gaps are `resources_unmeasured`, not scientific polarity.

## 7. Engineering and acceptance boundary

Engineering scope specification §4 items needed: **none**. Reuse the existing
learner, ordinary in-process batching, scientific update counters, normalizer
sync, RNG preservation and current detached execution/resource route. Add no
framework, retry/resume/checkpoint orchestration, manifest/currentness gate,
diagnostic matrix or additional telemetry system.

Future research code is limited to the new runner and its focused tests specified
in the companion CM document: <=600 new runner lines and <=2,000 new non-test
research lines. One synthetic suite checks the changed mask→storage→update,
terminal/reset, evaluator isolation and primary outputs, with an independent
source review of these scientifically consequential changes. No actual learner,
old checkpoint or scientific host panel is constructed during that engineering
verification assignment. Unchanged core code/checks are reused. Any scope or
budget breach is returned, not silently accepted or offset by moving wrappers.

Controlling evidence sections are §3–4, §5.2, §11.4, §11.7–11.9 of
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`. Only §11.4's common integrity,
nonzero real learner counts, resource admission and exposure line may hold a B
launch; this prospective preparation does not grant that launch allocation.
