# P67 question intake: internal individual renewal on the native UAV action path

Proposed claim: individual skill renewal between fixed team boundaries may change early native UAV performance beyond the same observation-reactive actor at a fixed skill clock.
Binding MARL structure: (b) temporal abstraction or termination; other UAVs change local service geometry and jointly learned behavior under partial actor observations.

## 1. Decision and current authority

**Recommend submitting this distinct prospective B question to the existing
Convergence node.** This intake selects question preparation, not a new object,
family opening, numerical seed, implementation, training allocation or UAV entry.
The [P67 resume command](../../portfolio/handoffs/2026-09-08-research-resume.md)
authorizes one concrete re-entry assessment and a proper-node question if justified.
Root's native assignment limits this batch to existing-evidence preparation.

The complete [P52 response](pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md)
at `fda33aabbd7579b3bc9183a5e684493d55fea07d`, its
[intake](pro_packets/20260908_post_b03_convergence/CONVERGENCE_INTAKE.md), and current
[DIRECTION](DIRECTION.md) remain binding: the tested supplied-public-mask learning
extension ended, the ordinary N6/K2 public-cue corridor policy-gap family is
paused, and neither selected a successor. The owner lifted a global execution
pause; that did not reverse either scientific boundary. P52 expressly left a
later different concrete question possible without reserving it.

Authoring checkout is `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`,
clean source/input `fbe5e67b96f8b390751635fe9c826910c8b3f0a4`. Current P67, AGENTS,
ROOT_OPERATIONS and relevant evidence-spec sections were read. A later main
`071a29c40eb9d313213f840617016ffeb93070df` has no changed applicable rule surface.
No FSD source or historical evidence is edited. Root owns main and Portfolio;
there is no separate Portfolio-session dependency. Scientific-reading v3 is
unimplemented and creates no gate. Owner pending reviews returned `[]`.

## 2. What changes, and what the source actually establishes

The candidate changes the **tested action/learning question**, not just a host
label. Corridor H replaces a physical lease-renewal mask with a public event
rule while leaving its internal skill/credit clock distinct. The proposed UAV
intervention instead changes actual individual internal skill selection; there
is no copied public flag, service lease actuator or supplied renewal schedule.
Team decisions stay on the same ten-step clock in both arms. Individual policy
gaps can cause earlier internal decisions only in the prospective treatment.

The following are direct source observations at the input revision, not an
observed advantage or proof that the trigger tracks a useful event:

| Source / relevant range | Established path and limitation |
| --- | --- |
| `hmasd/agent.py`, `_batched_assign_skills_d2` around2330–2540 | Every non-reset primitive step evaluates held skills using normalized full state, current observation batch and held causal-prefix skills. A team gap/cap resamples everyone; otherwise the individual gap/cap selects each agent. Infinite team cost with cap10 keeps the team schedule fixed. |
| `hmasd/agent.py`, `_batched_select_action` around2897–2980 and `step` around3042–3133 | Each primitive step feeds current local observation, the selected individual skill and actor GRU state to the movement actor. Hidden state persists across skill changes and resets on environment completion. A held skill does **not** freeze velocity or withhold new observations. |
| `scripts/run_flexible_skill_duration_e0.py`, `_make_config`, `_make_envs`, `Evaluator` | A real learner/evaluator path exists for scenario1, six UAVs/fifty users, latent team/individual counts6, fixed k10, FP32 learner, environment arrays retained in FP64. The existing CLI only accepts off/d0: it is not a runnable finite-cost experiment. |
| `envs/pettingzoo/uav_env.py`, `step`265–351 and observations382–435 | Each normalized velocity updates a fixed UAV's position; channel/connections/reward and bounded local position/SINR observations are recomputed. All agents receive observations every primitive step. There is no asynchronous observation-arrival interface or join/leave event here. |
| `envs/pettingzoo/scenario1.py`, reward80–125 and step171–197 | Native team reward is .7coverage + .3quality − altitude penalty. Movement changes service and interference; the environment's connection assignment is an existing common rule, not a policy oracle supplied to one arm. |
| `envs/pettingzoo/env_adapter.py`, step248–274 | The environment gives each UAV team reward/6, and the adapter averages those rewards. Its scalar is team reward/6; multiplying the episode sum by6/500 reports mean primitive native team reward without changing training rewards. |

Concrete chain: own/partner motion changes service geometry → fixed UAV
identity owns its internal skill and continuous action → coordinator sees the
same current centralized state/observation information in both arms, while each
actor sees its own partial observation → an individual held-skill logit gap
can resample that agent's skill before the common team boundary → the same
recurrent actor changes its skill-conditioned velocity distribution → native
coverage/quality/altitude reward and subsequent own learning data may change.
The low-level actor may already compensate completely; gaps may be noisy or
disrupt useful skills. Those are the strongest legal-null alternatives.

Population is fixed throughout an episode. User positions are sampled by the
unchanged reset law; partner motion is endogenous, and partners co-adapt during
training. No membership, identity, censoring, observation clock or primitive
time law changes. Retain the existing D2 variable-segment credit, discount and
terminal handling; differing segment/update/normalizer exposure is part of this
package comparison, not a pure timing or matched-compute estimand.

## 3. Prospective comparison for the node to accept or reject

This is a proposal, **not a frozen card or allocation**. Option A would open
only one scenario1 native internal-individual-renewal B question. Proposed I:
`d2`, individual cost.25, team cost+infinity, individual/team caps10, age off.
Proposed D0: the same D2 path, both costs+infinity, both caps10, age off.
Both use the ordinary six-skill recurrent learner, current reactive actor and
same information. Team boundaries and maximum individual hold are common;
I adds only within-interval individual gap decisions. This uses an existing
configuration capability, not a new termination head. No threshold sweep,
duration menu, added communication or population change is proposed.

Use the unchanged scenario1 free-space/uniform-reset host with six fixed UAVs,
fifty fixed users and H500. One new matched training pair, five16×500 rollouts
per learner, and one final32-episode endpoint per arm would give a direct early
learning comparison. Each arm owns its model, evaluator, RNG, normalizers,
trajectories and optimizer state; pair initialization/exogenous master schedules
prospectively. Numerical keys remain unassigned. No checkpoints are selected,
no prior E0 return is reused as a comparator and no extra evaluator/seed is
reserved. The learner sees the original scalar reward throughout.

Proposed primary: I−D0 in mean native team reward per primitive step,
`6 * episode_adapter_return / 500`, averaged over the fixed final episodes.
Report unscaled adapter episode returns too. Proposed MEI is **.01 absolute
native team-reward units per step**: one percentage point on the host's weighted
service/quality scale, avoiding a denominator-sensitive relative threshold.
It equals5 team-reward points, or5/6 adapter-return points, per H500 episode.
The objective still includes the native altitude cost; this is not a coverage-only
score. The headroom record for a tuned same-information scenario1 baseline is
absent and is not made a prerequisite.

Above+.01 would provide one local early-learning signal for this internal UAV
renewal package; inside inclusive±.01 would be small/resolution-limited; below
−.01 would oppose this candidate at this budget. Every branch retains actual
renewal/optimizer exposure and every failure/outcome, then ends one intake with
no automatic successor. One matched training pair cannot estimate training-seed
population uncertainty. Neither temporal causality, stable superiority, learned
termination, optimal clock, H transfer nor real-world UAV performance follows.
The node can decline this proposal on decision value; it need not manufacture a
replacement or require an unrequested stronger evidence class.

D0 is the strongest directly available same-learner, same-information fixed-clock
null for this marginal question: its actor also responds every step. It is not
the strongest possible UAV algorithm or a tuned optimum. The existing
[scenario1 baseline assembly](../../baselines/scenario_1/BASELINE_SET_RESULT_20260904.md)
supplies learner exposure/integrity and cost evidence only; its frozen E0 returns
cannot be ranked. Missing flat MAPPO/tuned-k coverage limits broad performance
claims and does not require a new baseline sweep before this B. That assembly's
older pilot/sweep recommendations are not current §11.8 launch requirements.

## 4. Work, cost and scope

[Machine-generated counts and cost](pro_packets/20260908_p67_uav_internal_renewal/EXPOSURE_AND_COST.json)
record **zero current scientific exposure**. For the prospective two-arm B:
2×1×5×16×500 =80000 training transitions,160 training episodes and10 update
stages; 2×32×500 =32000 evaluation steps,64 endpoint episodes. Total112000
environment steps and672000 agent observations; four model constructions/two
training starts;6000 learner/evaluator batched control calls. These are counts,
not independent empirical units or optimizer.step counts. There is no nested
candidate, trajectory search or added scientific validation panel.

Known coordinator work law: D0 has `M=16*500/10=800` joint boundary rows per
rollout; I retains800 team rows but may expose up to8000 joint decision rows and
48000 individual decision rows versus4800 at the fixed clock. Actual segment,
minibatch and optimizer work is data-dependent. Source counts do not prove a
wall-time bound.

Historical local CPU4 E0 D0 measured225.2s per rollout and2392.4s for ten
rollouts plus two8-episode evaluations. A deliberately explicit old-work
scenario for five rollouts and32 endpoint episodes is
`1.15*(5*225.2 + 2*(2392.4 - 10*225.2)) =1617.82s` for D0.
For I, multiplying **all** this projected work by the maximum10-fold decision-row
increase, including evaluation's potentially more frequent assignments, gives
`10*1617.82 =16178.2s`.
This intentionally loose stress scenario is not a measured current remote rate,
a verified upper bound, or a claim that every step costs ten times as much.
Current source/hardware and data-dependent work remain unknown; the high end
makes the cost of asking the question visible, rather than calling finite B cheap.

Illustrative complete invocation caps are3600s D0 and18000s I,21600s summed;
they cover initialization, learning, final evaluation and closed-file publication,
with no extra retry or time split. They are prospective bounds, not execution
authority. The node should compare this direct B's decision value with no new
object, and reduce/decline the question if its cost is not worthwhile rather than
insert a pilot, profile, support census or causal prerequisite. Any later selected
execution uses remote-first CPU4/FP32 and the declared environment arithmetic,
fresh memory admission, committed source and detached execution. Host hardware
is not the proposed estimand. No new engineering-scope §4 item is requested;
current work adds no research machinery or code, and a selected implementation
must reuse the existing learner/environment path within the ordinary budgets.

## 5. Evidence that changes the framing

The changed question was already possible in P44§4 but was not selected or
directly examined by P52. This assessment now checks the actual internal
skill→reactive actor→native reward boundary and fixes a marginal individual
interruption comparison with a common team clock. It is not another H/D0
corridor seed, a hidden extension of H or a claim of new source functionality.

Question-driven retrieval rechecked the available indexes: Inst-sci's formal
catalog contains190 real records; asynchronous/macro-action/termination/
option-critic/event-trigger terms returned six candidates. Only the relevant
ACAC source was expanded. My-lib's inspected collections entry and paper
registry expose two synthetic fixtures, excluded from scientific evidence;
no verified real-collection selection was found in those inspected entries.
This is bounded retrieval coverage, not a novelty or whole-library-absence verdict.

Jung et al., *Agent-Centric Actor-Critic for Asynchronous Multi-Agent
Reinforcement Learning*, ICML2025, [primary publication](https://proceedings.mlr.press/v267/jung25a.html),
was checked in `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json`, PDFpp2–3,
elements388–389,410,412. Metadata has official-title identity, gradeA and a
DOI-missing warning; PDFsha256
`f62052093281b72c2137e20a586f8eb964b54601aafd0b8e91ec922297e197f3`.
The publication page was read back on2026-09-09UTC. The source distinguishes
intra-option reaction, macro termination and decision-time observation
availability. **DM inference:** native reactive motion does not by itself make
internal renewal useless, but ACAC's sparse macro-observation/padding problem is
not instantiated by the inspected every-step observation path. Do not sell
this candidate as fixing stale asynchronous information or import ACAC's gains.
No new literature architecture, benchmark adapter or scientific result follows.

Preserve the complete B03 observation: H−D0+.3928645833333336, but
G−H+.1152864583333331; H's8662/68220 wrong-role choices remain. D0 was weak but
valid, with18000 actor/critic steps versus2250 for H. B01/B02 are separate H/C
pairs. Prior competent E3 losses and E4's public-null explanation remain strong
reasons to doubt useful policy gaps. These support only the existing package
claim; they do not predict positive UAV renewal performance. No old result is
rescored and no prediction reply is newly scored; owner prediction is not taken.

## 6. Decisions this intake produces

1. **Object/technical preparation.** Options: (a) publish one exact P67 proper-node
   question; (b) return no-ready-continuation; (c) locally reopen/run the old or
   proposed family. Recommend/select(a), because the actual action intervention,
   legal reactive null and finite native consequence can now be named. Option(c)
   exceeds this assignment. **Owner-delegated decision (unattended, 2026-09-03
   instruction): (a).** No scientific object is selected or allocated.
2. **Direction recommendation, not executed.** Options: (A) open only the proposed
   native individual-renewal B question with the bounded population/comparator;
   (B) no ready continuation, preserving both concluded corridor boundaries.
   DM recommends(A) for one real performance discriminator, with low confidence
   of a positive return and the reactive-actor null/cost explicitly visible.
   The proper Convergence node decides; it can reject this value judgment.
   A family opening or any recast label must be explicit in its formed response.

The selected question obeys evidence-spec§11.8.2 verbatim:

> Absence of improvement may also motivate a specifically justified new B change.

This is a preparation decision under P67 and the standing delegation, not a new
Pro exception or a reinterpretation of P52. An advisory P2 owner item records
the recommendation without claiming an owner reply or a formed direction choice.
No accepted mechanism science is added to DIRECTION before that choice exists.

## 7. Exact return and clean boundary

Prepare one GitHub-delivery request on the existing `codex/fsd` branch and
Issue10, bound to `em:flexible_skill_duration:convergence` and the current
provider conversation `6a9c2865-14a8-83e8-b556-e7f5836d9236`. The prior P52 request
is ARCHIVED with one Send and an accepted parent receipt; its short-chat
`scientific_decision_formed=false` transport field is not the complete GitHub
decision. The accepted P52 full response remains the scientific authority.

Root receives the new request ID, full HANDOFF commit/path, fixed TASK URL and
native return target `/root/dm_fsd_p47_resume` for exact dispatch by independent
Transport. DM sends no provider message. All new preparation commits are pushed;
the direction then waits at a clean boundary. A complete immutable response is
read and intaken by this DM when Root returns it. A blocker means no direction
decision; report it to Root with no local substitute or blind resend. Any later
card/CM/experiment work follows an explicit new allocation, not spent P52/P47
budgets. No source change, model, simulation, training, evaluation, profile,
replay, admission, result root or scientific invocation occurs in this batch.
