The existing FSD source supports a bounded question about replacing the native renewal actuator while retaining the trained skill-conditioned actor; no intervention effect has been measured.
Binding MARL structure: temporal abstraction or termination.

# FSD P13 re-entry source preparation and intake

2026-09-07. **A/RECON source preparation complete; one unselected question returned.**
Assignment: `P13-FSD-REENTRY-SOURCE-QUESTION-01`, in
`docs/research/portfolio/handoffs/2026-09-07-p13-runtime-restore-and-next-questions.md`.
This prepares the existing re-entry criterion. It does not reopen the fixed-K2 family,
freeze a card, select a new family/recast, commission code, or authorize Transport or execution.
The branch remains paused under the post-E4 PRO_FINAL; whole-direction ACTIVE/HIGH is unchanged.

## 1. Reading rule, scope and evidence checked

The controlling re-entry rule in `FSD_POST_E4_CONVERGENCE_INTAKE_20260905.md` is:

> Re-open only on one actual-source/execution-supported same-host native-action or learning-path
> discriminator: identify the manipulated mask/skill/role variable, its downstream state and
> native consequence, and actual checkpoint/normalizer/policy-state handling if reused; show
> how contrasting outcomes would change the reading; specify the strongest same-information
> null, new estimand, exposure, per-arm cost and stop rule. Without evidence for native-role
> competence, keep the question at that narrower control/representation ceiling.

Applied with evidence spec sections 3, 4, 5.1, 11.4 and 11.8–11.9: source facts support a
question, not an algorithm effect. No exact policy-class maximum or causal census is needed.
Checked the current Portfolio row, DIRECTION's post-E4 boundary, the source ranges below,
one already-accepted E3 cell's manifest/checkpoint receipt, and its existing evaluator timings.
No environment/learner import, initialization, experiment, installation, source implementation,
threshold change, E3/E4 repeat, new Pro packet or Send occurred.

Authoring checkout: `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`, created clean
from committed main `088e5d9892fa10687d12f1770e7eec21122d5a3f`. No maintained FSD branch existed
locally or remotely. Historical `dm-fsd-e4-census-20260905` remains untouched, detached at
`56b6faddf6235099afaba3e108c9750868550203`, with its untracked post-E4 Pro packet directory.

## 2. Actual native-action and state path

All source references below are at preparation input `088e5d9892fa10687d12f1770e7eec21122d5a3f`.

| Directly read surface | Source observation and implication |
| --- | --- |
| `envs/relay_corridor/host.py:318–365,382–405` | A regional event changes the latent and epoch. Public flag, lagged cue, identity, lease freshness, segment age and held role enter the next observation. Membership and zone/region ownership stay fixed. |
| `hmasd/agent.py:2330–2469,2481–2595` | The held-skill gap/cap rule forms an agent mask and a separate team mask. Partial assignment changes held skill tokens, log probabilities, timers, ages and decision metadata **before** action selection. A team decision samples all agents. |
| `hmasd/networks.py:1030–1110` | Partial assignment decodes kept entities first and sampled entities second, with corresponding forced/sample policy terms. Changing a mask inside this operation changes the autoregressive context. |
| `hmasd/agent.py:2895–3032,3087–3138`; `hmasd/networks.py:1439–1465,1583–1595,1687–1693` | Each step runs the actor with the current individual skill, observation and per-agent recurrent state. Skill FiLM precedes the recurrent layer. The recurrent layer is enabled; new hidden states are carried forward. Team skill enters coordinator/critic paths, not a direct native role lookup. |
| `envs/relay_corridor/hmasd_driver.py:195–246`; `adapter.py:98–154` | After `agent.step`, the driver passes continuous actions plus `d2_sampled_mask` to the adapter. The adapter decodes each action vector by argmax and separately forwards the renewal mask. |
| `envs/relay_corridor/host.py:318–347` | Native service is `(~renew) & lease_fresh & role_correct`, and shared reward is Delta times its agent mean. Renewal costs this step's service, stamps the current epoch, stores the emitted role and resets lease age. **KEEP still scores the role emitted on this step**, not `host.held_role`. |
| `hmasd/agent.py:2114–2177`; driver `:234–246` | Learning segment closure, duration credit and replay metadata follow the internally sampled mask. An adapter-only mask replacement must not be represented as synchronized D2 learning. |
| `envs/relay_corridor/references.py:436–468` | At K2, `GreedyOnPublicState` derives the correct role from zone, public flag and lagged cue, renewing on a flag after reset. It requires no private latent input. |

Thus `env_agent_skills` and the host's `held_role` are distinct states. An adapter renewal
override has a real native effect, but does not retroactively resample skills or repair their
bookkeeping. Its feedback also changes future observations, internal D2 decisions and actor
hidden states. Holding **weights** fixed does not hold actions or endogenous trajectories fixed.
The manifest distinguishes four host zones (`Z=4`) from six team tokens (`n_Z=6`), two individual
skill tokens and a two-component native action. These are not interchangeable role labels.

## 3. The one prepared question

**For the accepted E3 large-row seed-2 final D2 policy, does replacing only its native renewal
actuator with public-flag renewal improve sampled native service, and how much role-realization
loss remains against the competent public-greedy controller on the same exogenous episodes?**

This is an outcome-informed, checkpoint-conditional **control/representation diagnostic**.
Large seed 2 is named because its cumulative event path was present despite a competent paired
loss; this selection is disclosed, not independent confirmation or a representative seed claim.
Keep the same N6, fixed entities/regions, K2, four zones, H400, hazards .02/.20, Delta1,
no probe/coupling/churn, actor/coordinator parameters and internal D2 costs .25/caps40/400.

The smallest proposed comparison has three policies; none is selected for execution here:

- **C, intact controller:** run the loaded policy normally, including its actual D2 mask.
- **H, actuator replacement:** run the same fixed policy normally, retain its internal skill
  decisions, ages, recurrence and metadata, but pass the regional public flag as the **host**
  renewal mask for t>0. Retain C's forced reset renewal at t=0. Feed the actual resulting host
  observations/states back into H's own controller. No learning/storage/update occurs.
- **G, competent containing null:** use the existing `GreedyOnPublicState` roles and renewal
  actions, with its own host/controller state on matching exogenous episodes. This deliberately
  bypasses the learned actor and tests whether its added machinery is needed for native service;
  G's competence is not credited to that actor. This is the accepted operational null, not a new
  formal theorem about learned policy-class containment.

Manipulated variable: only H's applied native renewal mask relative to C. Primary prospective
estimand is the mean paired episode difference `R_H - R_C`, with R the mean per-primitive-step
shared native reward. Report every episode, G's native return, `R_G - R_H`, and H's missed
service on eligible KEEP/fresh-lease steps due to a wrong emitted role. Pair on exogenous
episode keys, not on actions, latent controller state, or independent training seeds.

C and H share the t=0 convention. G's default no-renew reset earns the initial service step;
report full-horizon and t>0 comparisons separately. The possible reset contribution is
Delta/H = .0025, not a duration-policy benefit. A prospective descriptive MEI of .01 mean
reward (one percentage point of native service here) would make the planning scale larger
than that reset effect; it is not an E3 threshold retune or a frozen pass rule.

Contrasting outcomes would change the reading as follows:

- H improves C and approaches G on post-reset native service: the existing policy can realize
  competent roles on those changed trajectories; actuator timing is a concrete remaining lever.
  This could support a later in-mechanism re-entry question, not D2 learning value or superiority
  to G. No universal prerequisite positive result is created.
- H improves C but retains wrong-role service loss versus G: report the native gain and remaining
  realization deficit separately. Timing alone does not restore complete control competence.
- H is unchanged or worse than C, or remains far below G: this intervention does not support a
  timing-only continuation of the selected controller. Wrong-role observations can narrow the
  control ceiling, but cannot uniquely blame skill representation, recurrence, co-adaptation or
  optimizer exposure. A loss would not close another seed, threshold or the direction.

H is intentionally an actuator intervention. A proposal to synchronize a public mask with skill
assignment/credit would be a different question requiring its own authorized specification;
silently editing `step_data` at the adapter does not implement it.

## 4. Checkpoint, normalizer and policy-state limits

The specifically inspected existing evidence root is
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed2`.
Its manifest binds launch `6d64a95a1189523e39abb184ef284a574050b748`; selected checkpoint
`checkpoint_final.pt` is present, 64,782,527 bytes, and a direct file hash matches the accepted
SHA256 `2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89`.
Prior technical acceptance is
`docs/Claude_docs/experiments/FSD_E3_LARGE_D2_SEED2_REMOTE_RUN_20260905.md`, Terminal technical
acceptance. It checked finite float32 network tensors, optimizer contents, configuration and
coordinator/discoverer normalizers. This preparation did not deserialize or import that policy.

- Direct manifest facts: CPU/four threads; torch2.7.0+cu118/NumPy1.26.3 on the original Linux
  execution; `use_obsnorm=false`, `use_statenorm=false`, `use_valuenorm=true`. Do not invent an
  observation/state-normalizer portability defect when those transforms were disabled.
- `hmasd/agent.py:7143–7293` saves network/optimizer/configuration state and enabled normalizer
  mean/variance/count; it does **not** save a complete host, actor/critic lane hidden states,
  current skill/age dictionaries, open segments or all Python/NumPy/Torch RNG state. Its rollout
  sampler state is not a full trajectory snapshot. No mid-episode branch, training resume or
  historical action/logit replay is supported by these checkpoint facts.
- `load_model:7346–7664` uses the constructed configuration and non-strict network loading;
  absent enabled normalizers can retain initialization values with a warning. Successful return
  from that loader alone would not verify a scientifically equivalent evaluator. The E2 config
  class's importable pickle path must be preserved (`run_flexible_skill_duration_e2.py:165–172`).
- Existing evaluation uses a separate agent, weight and normalizer synchronization, `train(False)`,
  buffer clearing and `reset_env_state` per lane (`e2.py:456–508`). Resets invalidate skills,
  clear hidden states and ages (`agent.py:1559–1621`). The E3 evaluator uses reset host state and
  deterministic decisions (`e3.py:240–275`); it records episode returns, not a full action/logit/
  hidden-state tape. A future measurement must start complete fresh episodes in each policy.

Static Python AST comparison found exactly fourteen methods unchanged between the selected
launch and preparation input:
six HMASDAgent methods (assignment/action/step/reset/save/load), R_Actor.forward,
SkillDiscoverer.forward, host step/observations, adapter step, E2 sync/reset and E3 run.
This establishes those source facts' currentness, not all-dependency/runtime equivalence.
Remaining technical uncertainty is actual checkpoint-to-fresh-evaluator restoration on a
future execution node. Missing required state/configuration, non-strict key discrepancies or
failed primary output would stop that dependent measurement as a technical gap, not a negative.

## 5. Exposure, work and proposed stop boundary

Tool-produced current exposure: **0 new experiment invocations; 0 environment transitions;
0 learner initializations; 0 optimizer steps; 0 new evaluation episodes; 0 Pro Sends.**
One historical checkpoint was selected after seeing E3 results. Its prior 128,000 training
transitions and updates4350/9000/9000/300/1200 remain historical exposure, not new work.
Owner prediction: **not taken (unattended)**; no intervention prediction has been scored.

A concrete illustrative costing bound is one checkpoint, three policies, 32 paired episode
keys per policy, H400, N6 and one batch of32. It is preparation, not a frozen allocation.
Python arithmetic from the manifest and existing eval records gives:

| Dominant work | Proposed quantity |
| --- | ---: |
| Complete policy episodes / environment steps | 96 / 38,400 |
| Environment steps per policy | 12,800 |
| Total agent-step observations | 230,400 |
| Learned-controller environment steps in C and H | 25,600 |
| Batched `agent.step` calls in C and H | 800 |
| At most gap/assignment coordinator batch calls in C and H | 1,598 |
| Existing scripted reference calls in G | 400 |
| Checkpoint loads for two separately started learned policies | 2 |
| New training/optimizer work | 0 |

Each coordinator pass itself contains the fixed six-agent decoder sequence; this is not a
search over skill sequences, policies or future trajectories. Initialization/loading and
publication are part of each complete invocation. Added validation would be one focused
state-to-action/output check, not another scientific matrix or repeated smoke.

Historical final evaluation was563.180000862s for2048 episodes at batch512, or .274990235s per
episode. Linear scaling suggests8.7997s per learned32-episode arm; the older runner's .46s/episode
law gives14.72s. **Neither measures batch32 or includes a new standalone checkpoint load**;
actual initialization cost and G's standalone wall remain unknown. No claim of admitted cost
or speedup follows. A prospective complete cap of180s per policy (at most540s summed invocation
wall) would cover load/evaluate/publication and stop without retry, slicing, extra seeds or
threshold search. This cap is proposed for a later card, not permission to launch now.

Section11.9 comparison: even a two-arm, one-seed, one-rollout real B example at16 lanes/H400
has only12,800 training transitions before evaluation, versus25,600 learned-controller
evaluation transitions here, plus its nonzero optimizer work. Zero-learner work is therefore
not presumed cheap. This diagnostic's separate value is measuring an actuator intervention on
an already trained policy without changing its weights. If the next decision is simply new
learning performance, a minimal real B should be considered directly; this proposal must not
become a prerequisite. No extra cost experiment is proposed.

Host headroom remains as recorded at post-E4: no tuned generic renewal-host pair. The large-row
public null's recorded reference .890275 and selected policy's old .455985311 are distinct
historical quantities; their gap is not measured intervention headroom or a new gain.

## 6. Decisions this intake produces and return boundary

1. **Object-tier preparation:** (a) return the one source-supported actuator question with its
   limits; (b) yield with no candidate. Recommend and execute **(a)** because both the actual
   native lever and competent public null exist, and a specific accepted checkpoint is present.
   This does not select an experiment or reopen the family.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Needed direction authority, not exercised:** the existing
   `em:flexible_skill_duration:convergence` node would decide any re-entry/disposition. No local
   new-family/recast decision or Pro Send is implied. Portfolio owns any next bounded command;
   Root receives this completed preparation and integrates the named commit.

Engineering scope section4: **none needed for this preparation**. A future implementation,
only if selected, would be one research-only evaluator and one focused check reusing the
identified loader/reset/actor/adapter/reference paths; it needs no new core algorithm,
checkpoint-resume orchestration, registry, guard or diagnostic census. This is not a complete
CM spec or coding assignment. Any eventual complete spec must reach Root for the five-arm
comparison before coding. Current comparison exclusion, recorded once: pure source/intake
preparation, zero engineering assignment and zero duplicate scientific invocation.

Strongest support remains E3 smallseed2's competent positive and E2 duration control; strongest
contradiction remains the six competent medium/large losses and E4's public-null explanation.
The new source finding separates a controllable actuator from the learned role path; it does
not establish a positive effect or uniquely explain those historical outcomes.

Scientific-tools use was limited to source/currentness facts, existing artifact/timing reads
and executable count arithmetic. The accepted public-greedy source is reused for the null.
Bounded local-library index checks supplied no new source passage needed for this code-path
claim; generic temporal-abstraction metadata was not treated as mechanism evidence. My-lib's
documented synthetic fixtures were excluded; no real-collection search or broad literature
coverage is claimed. No new library, installation or external retrieval was needed.

Clean-boundary owner reviews returned `[]` in current main and this checkout; no FSD ledger
override was found. No owner response was invented. This ordinary preparation decision has
no separate P1/P2 item: no card freeze, direction verdict, close call or Portfolio proposal
was made. Audit: `docs/research/portfolio/audit/2026-09-07.md`. Chinese source-result brief:
`docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-07_P13_REENTRY_SOURCE.md`.
