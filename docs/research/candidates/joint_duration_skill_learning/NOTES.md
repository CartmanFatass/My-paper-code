# Joint duration and skill learning

## 2026-09-21 — Owner-selected independent study

Owner requested four concurrent directions, with the assigning task itself owning one and
three newly created independent DM tasks. This task owns this direction end to end.
After initialization the DMs do not communicate with one another. Evidence publication and
shared-background use follow the existing constitution; no Root acknowledgment is needed.
Owner's compute order: prefer configured remote WSL `wsl_4070`, then local computation only
with a recorded availability, resource or suitability reason. Preserve accepted handles and
use actual-node admission; four research tasks do not imply four simultaneous heavy fits.

### Question and inherited explanation

Can additional duration choices improve native Scenario1 service under finite learning,
and does an ordinary autoregressive duration distribution improve on a fully informed
factored duration distribution? All arms jointly learn high-level skills and low-level control.
This is the previously proposed new comparison, now selected by the owner's instruction.
It does not reopen Claude's paused `flexible_skill_duration` task, take over its notebook,
or continue the stopped high-level-label-credit/threshold/renewal rescue package.

The [published background at 455837f60](https://github.com/CartmanFatass/My-paper-code/blob/455837f60127cc31fbc5d802e19dfd79d0a2bfec/docs/research/RESEARCH.md)
sections 3–6 changes the design: use a competent fixed-clock arm, give both duration arms
the same lawful commitments/history/team latent/current joint skills, preserve closed-loop
primitive control, and compare native return and actual cost. Expressivity inclusion does
not guarantee strict improvement, and action-space size is not a sample-complexity ratio.
The [complete programme advice and decision](../../archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-whole-project-evidence-led-research-plan)
and [concept formation](../../archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)
cover this initial question; the DM must check applicability before reusing advice for a bound design.

FSD B13/B14 did not reverse the stopped package's judgment. B12's particular label-count
regression is not a bound on new joint skill learning. UCOPE's local suffix effects did not
establish useful complete return. These raise the cost of speculative rescue and are retained
as contrary evidence, not reset by the new directory. Sources: [FSD notebook](../flexible_skill_duration/NOTES.md)
and the [current UCOPE standing](../../RESEARCH.md#archived-investment-only-not-scientifically-disproved).

### First comparison and discriminating observations

- Same Scenario1 task and full HMASD: fixed k; informed factored durations; ordinary AR
  durations after the same joint skill-selection family. One difference between variable
  arms is conditioning on earlier sampled durations in the same eligible-member event.
- Share duration menu, cap, lawful information, ordinary commitment/history critic and
  update principles. Factored policies may coordinate deterministically and through latent
  variables. Single-member events provide no extra within-event joint sampling relation.
- Read full native J, prespecified learning-curve positions, native service components,
  actual decisions/updates, joint-event exposure, effective durations and compute. Low-level
  chunk length, nominal clock and cap truncation must not be silently conflated.
- An AR gain only over factored, while both lose to fixed k, does not justify extra
  complexity. Useful variable arms without a reliable AR increment favor the simpler arm.
  Duration correlation, entropy or local credit changes alone do not establish service gain.

### Initial work and scope

Map the active S1 training/evaluation path and existing duration sampling, replay and credit
semantics; then bind a minimal runnable comparison, scientific cost and meaningful endpoint.
Do not add a new encoder, predictive auxiliary, clock curriculum, new reward or fictional
fault/backhaul mechanism. Existing code/evidence is reusable; another active DM's new result
or module is not a dependency. Shared correctness repairs, when necessary, apply to all arms.

The DM owns this notebook, `experiments/candidates/joint_duration_skill_learning/`, its tests
and `runs/joint_duration_skill_learning/`; shared executable edits need existing independent
review. Declare exact arms, seeds, horizon, evaluation and planned fits before any result run.
Initialization starts **0 fits**, accepts no experiment or Pro Send, and is not an empirical
result. Continue through design, implementation, evidence reading and a supported next
investment/stop judgment using the existing methods; no automatic rescue sequence.

## 2026-09-21 — Direct DM initialization and the first implementation distinction

This task `01a0c348-428c-7f01-bd8b-121d69543032`, host `local`, now owns only this direction.
Its isolated authoring checkout is `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`,
branch `codex/joint-duration-learning-20260921`. The three other independent DM tasks have
their own recorded addresses and workspaces; initialization is complete and no further
cross-DM communication or monitoring is planned. Current runtime context for all four DMs
was read and verified as `gpt-6-astra` / `max` after correcting the three new tasks' initial
default medium setting. No experiment or Pro operation was restarted to change effort.

Refreshed published main `c91af2e5a` and read the unchanged relevant shared background and
the complete programme Pro Answer. The full-joint-learning question, fixed/factored/AR
comparison, strong-information requirement and outcome branches remain applicable; this
advice is reused for the question, not treated as a validated executable design. FSD's
03:43/03:52 B14 interpretation and rest entry were read directly: the proposed reversal
did not occur, the old label-credit route stopped, and no accepted FSD operation is inherited.

Read-only source inspection found a substantive implementation distinction. The existing
duration head is in `hmasd/ha_ctse.py` and requires the horizon/process/discrete-lifetime
path. The original full-HMASD S1 recipes use `SkillCoordinator` with those switches off;
`hmasd/baselines.py::_enable_ha_ctse` also changes the discovery/process objective. Therefore
turning on that family is not the promised single duration-parameterization intervention.
The HA-CTSE AR skill/editor path also emits duration logits in parallel, so its AR name
does not implement conditional duration sampling. The next binding must preserve the full
HMASD actor/discovery path and explicitly add the missing duration context/sampling and
matching reevaluation. A bounded Scout is checking the separate non-HA D2 scheduling path
before selecting the smallest implementation. This is a code fact, not a performance result.

The configured remote responded as `LAPTOP-U9TDKC8A`; the read-only observation showed
about 14 GiB available RAM and current canonical research control at `c91af2e5a`.
Use `wsl_4070` first for result computation and acquire fresh actual-node admission at launch.
No scientific run, new Pro Send or fit has yet been accepted; started fits remain 0.

## 2026-09-21 — D2 scheduling map and the decision needing advice

The bounded D2 follow-up resolves the distinction left open above. D1280/D0 is not simply
the ordinary off collector: `run_flexible_skill_duration_e0.py::_make_config("D0", ...)`
uses D2 with both logit-gap costs infinite, individual/team caps 10, age feature off; the
1280 variant changes coordinator batch size. `HMASDAgent::_batched_assign_skills_d2`
checks primitive-step ages, resamples the team at its cap and forces all members then;
between team decisions it can resample a subset. `SkillCoordinator::assign_partial_batch`
decodes kept members first and eligible members next in canonical order, forcing held tokens.
`evaluate_training_batch_ordered` replays that order and the stored eligibility masks.

Unlike the HA-CTSE lifetime path, D2 already maintains separate open agent and team credit
segments. Resampling, terminal closure and rollout flush have explicit elapsed-step semantics;
rewards are discounted inside a segment and the next value by gamma to its elapsed steps.
`update()` still performs original low-level/discoverer and discriminator learning. These
are reusable implementation assets, not evidence that a new duration head is useful.

The material open choice is how to add the common commitment context and the post-skill
duration policy without introducing an action-dependent baseline or miscrediting an AR
factor's influence on later sampled durations. Existing programme advice covers the three
learning packages but does not bind that actual loss/critic choice. A focused Pro consultation
will resolve this scientific design boundary before committing an implementation/batch.

## Pro question 2026-09-21 duration-sampling-and-credit

Conversation: new (WSL/Jev; private address remains in local operation state).

### Question

Choose the smallest scientifically sound full-HMASD comparison of fixed k, informed
factored durations and ordinary autoregressive durations on the existing Scenario1 path.
The immediate decision is the **common decision state, critic and policy-gradient target**
for a duration sampler added after joint skill selection. Is extending the existing D2
agent/team segment path adequate, or should the three arms share a different ordinary
event-based return/critic construction? Explain a concrete recommended construction and
the consequential alternative; do not invent another research direction or rescue module.

This direction is now explicitly selected in the owner's four-task assignment. Each DM
works independently after initialization. This task owns the new jointly trained duration
comparison; it does not restart Claude/FSD, its old credit rescue, or G33. Current model is
Astra max; result computation prefers remote WSL `wsl_4070`, then local only for a recorded
availability/resource/suitability reason. Advice is not an empirical result or approval.

### Standing and inherited evidence

The complete programme Answer/Decision in the dated RESEARCH archive already recommends
fixed/informed-factored/ordinary-AR duration learning and says to retain ordinary methods
when they absorb the gain. It does not validate a pre-existing duration implementation.
Background sections 3–6 establish that legal common context and a team latent can already
coordinate factored outputs; deterministic coordination is not exclusive to AR. When one
member is eligible there is no extra within-event cross-member sampling relation. More
duration choices do not guarantee better finite learning or imply a sample-complexity ratio.

FSD B13/B14 left the old high-level-label-credit package stopped. B14's primary checkpoint
effects were about +.019, +.016, -.019; they did not reverse the predeclared investment
judgment. B12's label-count regression is not a bound on new state-conditional joint skill
learning. UCOPE's real local suffix effects did not establish useful complete return.
No new positive result overturns those findings. All new arms here must jointly learn
skills and primitive control, and compete with a competent newly trained fixed-clock arm.

### Concrete current implementation facts

- The S1 reference uses 6 UAVs and 50 users, primitive closed-loop actor actions and the
  original hierarchy/discovery pipeline. D0 has k=10, both D2 logit-gap costs infinite and
  both individual/team caps 10; D1280 selects coordinator batch size 1280. It is not HA-CTSE.
- D2 has held team/joint skills, agent/team ages, partial resampling masks and stored decode
  order. Kept skill tokens precede eligible tokens; the same ordered law is reevaluated.
- D2 stores separate agent segments and a team segment. It accumulates discounted primitive
  rewards, closes at relevant resampling/terminal/rollout events and uses gamma^elapsed in
  bootstrap/GAE. Original actor and discriminator learning continues.
- The only current duration head is in HA-CTSE. Enabling that family also changes discovery
  and process objectives. Its AR label applies to skill/edit sampling; durations are emitted
  in parallel, without preceding sampled durations or held remaining-time context. Simply
  toggling it does not implement the requested comparison.
- Config k is also used for low-level recurrent training chunks. Execution duration must
  have its own state and must not silently change the low-level training chunk length.

### Proposed bounded design, open to material correction

Start with one fresh implementation of the full D2 learning family shared by all three arms,
preserving primitive actor/discovery training. At a team event sample the team latent and
all skills; at a member event hold the team latent and noneligible skills, sample eligible
skills using the same ordinary ordered coordinator. Only after the whole current joint
skill vector is defined do the eligible members sample durations.

Both duration arms receive identical lawful current central/joint observations already used
by the high-level policy, team latent, current joint skills, eligibility, held commitment
ages/deadlines and time to the common team cap. No new privileged observation or predictive
module is introduced. The factored arm samples durations independently conditional on that
full common context; AR additionally sees earlier sampled durations in canonical eligible
order. Store the actual order, eligibility, context and sampled choices for PPO reevaluation.

A concrete starting option is team cap 10, fixed arm k=10, and durations in primitive units
1..10, masked to the remaining time before the team cap. This keeps a fixed-10 policy
reachable, avoids duplicate nominal choices that all clip to the same actual duration and
isolates optional shorter individual commitments. It is explicitly **not** a test of every
longer-than-10 duration scheme. If that restriction makes the question poor value, explain
the specific alternative and its cost; do not infer opportunity from label counts or add
artificial synchronization/faults to favor AR.

The unresolved loss/critic alternatives are:

1. Extend D2's separate agent/team segments and common commitment-aware value inputs; train
   a duration factor using the corresponding legitimate return target and baseline. A
   duration prefix is available before that factor but later sampled durations depend on
   it. Identify precisely which sampled skills/latent/durations may enter each skill or
   duration baseline, and whether existing segment bootstraps need a different state.
2. Use one ordinary event-level team-return target and pre-action commitment/history value
   shared across arms for all actually sampled factors, with discounting to the next event.
   Explain what is lost/gained versus per-member closure, including irregular sampling,
   clipped PPO surrogates, event frequency and finite-learning variance.

Do not assume a COMA marginalization holding later AR durations fixed remains a legitimate
baseline; do not require a new causal-credit method. A simple lawful baseline is preferable
to a new module. Distinguish faithful sampling/replay, a useful approximate PPO objective,
and any stronger unbiased-policy-gradient claim. A package result need not identify the
cause as correlated exploration; marginal duration, optimization, capacity and occupancy
differences remain alternative explanations.

### Prospective cost and discriminating reading

This consultation and implementation inspection start 0 fits. The proposed first exploration
is 3 new training instances, one per arm, at 360,000 primitive team transitions each
(1,080,000 total training transitions), remote WSL preferred. This is a costed design option,
not an accepted batch or confirmation. The DM will bind seeds, evaluation population and
curve positions, exact horizon/config, compute and stopping before launch after reading advice.
There is no architecture grid, frozen-label prerequisite or requirement for a positive toy.
Ordinary correctness tests do not establish performance.

Read full native J, actual S1 service components, prespecified curve/endpoints and actual
data/update/compute cost. Log joint-event exposure and executed commitments to check whether
the proposed difference exists in use. AR beating only factored but losing to fixed does
not justify complexity; both variable arms beating fixed without useful AR increment favors
the simpler arm. Proxy-only changes weaken the proposal's native-use explanation. One seed
per arm is exploratory, not stable superiority, equivalence or a paper-grade claim.

### Context and source precedence

All paths below resolve at source_sha supplied in the actual message. Read only the named
relevant sections; no recursive archive preload is requested.

- Current governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1–5 and 8. Owner
  explicitly selected this new study; old FSD/Claude remains paused and G33 remains frozen.
- Current methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Explore / Comparators /
  Update the working explanation / Cost and exposure; `.agents/skills/hmasd-research-engineering/SKILL.md`,
  Core versus experimental / Checks and review. They are methods under the constitution.
- Shared background: `docs/research/RESEARCH.md`, topics 3–6 and the duration row of the
  current plan. These are revisable scientific judgments, not a requirement to agree.
- Existing advice: `docs/research/archive/2026-09-21/RESEARCH.md`, the duration subsection
  of the complete whole-project Answer/Decision and the complete MARL-concept Answer/Decision.
- Direct adverse evidence: `docs/research/candidates/flexible_skill_duration/NOTES.md`,
  2026-09-21 03:43/03:52 B14 reading and rest, plus its scoped B13/02:51 prior interpretation.
  Do not reinterpret the old claim endpoints or reuse old weights as new training replication.
- Code: `scripts/run_flexible_skill_duration_e0.py::_make_config`,
  `scripts/run_fsd_uav_individual_renewal_b01.py::make_config`;
  `hmasd/agent.py::_batched_assign_skills_d2`, `_d2_store_transition`,
  `_d2_flush_open_segments`, `update_coordinator_d2`, `update_discoverer_from_rollout`;
  `hmasd/networks.py::SkillCoordinator.assign_partial_batch`, `evaluate_training_batch_ordered`;
  `hmasd/utils.py::RolloutBuffer.compute_high_level_advantages_d2` and D2 storage/sampler;
  `hmasd/ha_ctse.py::HorizonSkillEditor` only for the identified existing-head mismatch.
  Function names are locators, not a claim that each implementation is correct.

### Requested answer and writing constraints

Recommend the least invasive useful comparison and give explicit conditioning/return/credit
semantics. Name the strongest material objection and the smallest observation or correctness
check that can discriminate it, including a native outcome rather than only duration
statistics. State which prior judgments are strengthened, weakened or unresolved, costs and
remaining uncertainty, and `MATERIAL_DISSENT: yes/no` for this proposed design. Do not turn
uncertainty into an invented probability, global impossibility or a new approval gate.

No training or edits outside the following empty `### Answer` subsection in this unique
question. Target branch: `codex/joint-duration-learning-20260921`. Read pinned sources for
reasoning, but fetch the latest target file and its actual blob SHA before writing. Preserve
all other bytes and stop on overlapping edits. Return the actual answer commit if written;
if writeback is unavailable, return the complete answer in chat, not only a receipt or link.

### Answer
