# Goal-conditioned entity aggregation

Direction: `goal_conditioned_entity_aggregation`.
Direct DM: current task `01a0c7e4-e1aa-7460-a6bb-43db5c1b0898`, host `local`.
Authoring checkout: `/home/fires/.codex/worktrees/query-aggregation-sept22/hmasd-wsl`.
Branch: `codex/goal-conditioned-aggregation-20260922`.
Pro: new Jev question when authored; private account identifiers stay in local transport state.

## 2026-09-22 — Owner activation and inherited explanation

Owner selected literature opportunity 3 for research and assigned this session as one direct DM,
with separate new Astra/max DMs for opportunities 1 and 6. Initialization ends cross-DM
communication; this DM proceeds, observes accepted operations and publishes its own evidence independently.
The global pause is lifted; Claude FSD remains owner-paused and G33 frozen.
The starting proposal is [plan 3](../../designs/LITERATURE_RESEARCH_PLAN_20260922.md#plan-3).
No fit, Pro Send or result-bearing operation has been accepted at this entry.

### Current evidence and its use

Published main `5113f4917` supplies current RESEARCH topics 3/4/5/6 and the count DM's B02 result.
The old local-observation dense recipe remains archived: original versus dense terminal J45
was .458426 versus .202254, with 95.51 versus 185.94 runner minutes, one training instance per arm.
All three prewritten panel means were adverse to dense. Its [NOTES](../local_observation_encoding/NOTES.md)
and complete closure Pro answer distinguish a failed package from a causal verdict about attention,
pooling or all representations. This new direction inherits that negative observation and selection history.
It does not rename the same dense package or count a new architecture as independent replication.

Shared understanding changes the proposed comparison: ordinary methods are legitimate competitors;
finite training can favor one information organization without proving representation-class superiority;
complete service and compute matter more than attention maps or proxy losses. The count direction's
B02 confirms that bounded deployment changes frozen trajectories and service; historical raw-action
scores cannot be direct controls for new bounded training. Every proposed new arm will use the same
explicit raw-Gaussian scoring / coordinate-clipped environment execution contract.

### Working hypothesis and strongest alternative

At the low-level actor the current held individual skill z is already legally available. Allowing z to
choose which observed user/peer features are aggregated could improve finite joint learning compared with adding
z only after information is compressed. This is a hypothesis about a particular training regime,
not a claim that a new attention operator has been invented. A competent ordinary per-entity MLP
conditioned on (entity, ego, z) with mean/max pooling may already provide the useful inductive bias;
additional attention may add optimization cost without native benefit. The higher-level decision cannot
condition on a not-yet-chosen skill. No extra identity, absent-slot mask or privileged entity state is allowed.

Proposed main discriminator: otherwise matched lightweight attention arms E (z in query before pool)
and L (the same z projection added after pool), with ordinary conditioned pooling P and original MLP+FiLM O.
All retain the original post-base FiLM and recurrent policy path. Predict actual z-dependent aggregation
in E and, if useful, improved final native service relative to L; a changed attention map alone is insufficient.
E beating L but not P favors ordinary conditioned pooling as the useful solution. No O gain or excessive
cost weakens the whole package. Removing the query z at evaluation is only a dependence diagnostic and
can be out of distribution; it cannot by itself prove learned skill semantics.

### Proposed cost and next decision

The design offers four arms × one training block × 360k environment transitions = four fits / 1.44M
train steps, with 45 rollouts × 16 lanes × 500 steps, PPO 15 epochs, high-level batch 1280.
Three fixed panels at rollouts 15/30/45 × 32 worlds × 500 × four arms cost 192k evaluation steps;
one E terminal query-z ablation costs another 16k, total 208k. These are proposed, not accepted inputs.
The final endpoint is native J45 and service components; no best-checkpoint selection. One block is
exploratory, and worlds/checkpoints are not additional independent training runs. Fresh seeds, exact
network dimensions and wall-cost measurement will be declared after the scientific design is selected.

Next: a focused Pro question on whether the E/L/P/O comparison can resolve a worthwhile live distinction
under inherited adverse evidence, and whether a smaller comparison would change the same decision.
Prior LOE closure advice did not evaluate this z-position question or the corrected action law; a new
premise/comparator consultation is therefore material under constitution section 5. No confirmation,
automatic rescue sweep, toy-pass gate or further fit is selected by this entry.

## Pro question 2026-09-22 skill-query-position-first-comparison

Conversation: new; Jev private account details remain only in local transport state.

Question: Given the adverse old dense-encoder package and the absence of an established
aggregation bottleneck, is the proposed skill-before-pooling versus skill-after-pooling
comparison a worthwhile next finite-learning experiment? Criticize E/L/P/O below and recommend
the smallest real comparison that would change the investment decision. This is a premise and
key-comparator consultation, not a request to approve a fit or invent a new mechanism story.

Owner instruction: start literature directions 1, 3 and 6, with this direct DM owning 3;
initialization is complete and cross-DM communication has ended. Research is authorized,
global pause lifted, Claude FSD still paused, G33 still frozen. No new experiment has started.

Standing and decision:

- The old `local_observation_encoding` recipe remains archived. Its two 360k fits, one
  training instance per arm, gave ORIGINAL/DENSE J45 .458426/.202254 and connected users
  31.939438/13.415938, with fit-body walls 95.51/185.94 min on the shared WSL node. Dense
  had lower panel-mean J at all three prewritten times. The complete prior Pro answer and
  DM closure distinguish a poor package investment from a causal result about attention or
  a population-level ranking; no bottleneck, normalization failure or deficient capacity was
  identified. That advice did not consider the current held-skill query or corrected action law.
- The new reason is a legal intervention on conditional information compression: z is available
  before the low-level action, but the current actor does `base(obs) -> FiLM(z) -> GRU`.
  A finite summary independent of z may be harder to use for skill-relevant entity selection
  than a z-conditioned summary. This is a conjecture, not an observed deficiency or a theorem
  that FiLM cannot express the useful policy. Skill labels have no verified service semantics.
- The strongest ordinary alternative is nonlinear per-entity conditioning followed by ordinary
  pooling, with no attention. The strongest negative explanation is that the current task and
  learned skills offer no useful z-dependent selection, or that additional structure harms
  finite optimization. A same-information complete package can improve without supporting a
  general mechanism claim. There is no requirement to manufacture a successor if its expected
  information is not worth the full learning cost.

Actual interface and proposed intervention:

`R_Actor.forward` and `evaluate_actions` in `hmasd/networks.py` both have the current held
individual `agent_skill`; `HMASDAgent.step` chooses/retains it before taking the primitive
action. Rollout PPO reevaluation uses the saved skill sequence. Boundary actions use the newly
chosen z; other actions use the held z. We do not put a not-yet-selected skill in a high-level
encoder. Actor input remains the actual 104-dimensional local observation with 20 user and
10 peer slots, self/time features, current legal z and existing GRU history. Rank/zero padding
remain observable slot conventions, not persistent identities or an extra validity mask.
No extra global state, future label, team skill Z or communication enters the actor.

Four proposed arms use exactly the same environment, high-level policy/critic information,
refresh clock, reward, recurrent reset, normalizers, intrinsic objective and joint-learning
budgets. No frozen actor or offline-only probe replaces joint learning.

| Arm | Proposed actor base, followed by the unchanged FiLM(z) and GRU |
| --- | --- |
| O | Current MLP; freshly trained with the new common execution contract. |
| L | Shared-within-type entity embedding, ego/time query q, separate user/peer single-query attention pools. For each type t, p_t = A_t(q,H_t) + U z. |
| E | The same trainable components and dimensions as L, moving the same z projection before pooling: p_t = A_t(q + U z,H_t). |
| P | Ordinary nonlinear per-entity MLP receiving (entity, ego, z), separate mean+max pooling for user and peer types, then the common output dimension. |

For L/E propose token/query/pool width 64 and four attention heads; concatenate the two pools
and ego representation and project to the actual actor hidden size 256 (`configs/config_1.py`).
Use the same norms, projections, rank handling and initialization rules in L/E. There is no
full token-to-token self-attention block. U is active in both L and E; no dummy parameters
are added for matching. P gets a competent similar-capacity ordinary specification, O retains
its actual baseline. Report actual effective parameter counts and full compute; do not claim
exact parameter/optimization equivalence or search architecture/hyperparameter combinations.
The L/E position contrast also changes gradient routing and inductive bias, so attribution must
not be stronger than that intervention. If these formulas conceal a more important confound,
state it and offer a concrete minimal correction rather than demanding an exhaustive factorial.

Action execution is a common new contract, not another experimental factor. The old S1
collector/evaluator passed raw Gaussian actions to the environment despite a declared Box;
the environment multiplied these by max_speed and clipped positions. Count B02's frozen
raw/clip comparison changed all 288 world trajectories at the first action and improved
per-N mean service of both packages, while some worlds/policies lost. It does not identify
the historical training-exposure contribution. We will not repeat that direction's B03.
All new arms here sample u from the same original Normal and execute `clip(u.copy(),-1,1)`;
buffer/actions/old log-prob retain raw u, PPO evaluates that same u, and rewards/transitions
come from the executed trajectory. Deterministic evaluation executes `clip(mu,-1,1)`.
Keep the original Gaussian initialization and entropy treatment, with no tanh, logstd cap or
simultaneous entropy retuning. Raw entropy is not executed-action entropy. The Box bounds
coordinates, not Euclidean speed. Old raw-action scores/walls are historical context, not
direct new-arm controls. Record raw excursions and executed saturation in every new arm.

Predictions and limits:

1. If conditioning before compression helps in this regime, E should improve the fixed native
   endpoint over L; ordinary P and original O test whether that difference buys useful package
   value. E beating L but not P favors the simpler conditioned-pooling solution. E/P not
   improving O weakens the package investment. A changed attention map alone is not success.
2. One terminal E evaluation sets only the query branch U z to zero while FiLM still gets the
   true z. Predicted intermediate consequence is a change in executed actions, not merely raw
   actions that clipping erases; predicted native consequence is loss of useful return. This
   intervention can be out of distribution and can only indicate branch dependence. It does
   not identify correct semantic entity selection. If this 16k-step diagnostic cannot change
   the live judgment, recommend dropping or replacing it and explain the discriminator.
3. One new training block per arm is exploratory. A failure to win is not equivalence or
   representation-class falsification; a positive difference is not a stable training ranking.
   Fixed reset worlds/checkpoints are nested observations, not training replication. No
   best checkpoint, automatic rescue search, confirmation, or added seeds is selected here.

Prospective cost: S1, N=6, k=10, 50 static uniformly distributed users, free-space channel,
six team and individual skills. Each proposed fit is 45 rollouts x 16 lanes x 500 transitions
= 360k, PPO 15 epochs and high-level batch 1280, all five learner components actually updated.
Four arms x one block = 4 fits / 1.44M training transitions. Panels at rollouts 15/30/45,
32 fixed evaluation worlds x 500 transitions per arm = 192k evaluation transitions, plus
16k E query-off = 208k total. Main endpoint is J45 = N x scalar episode return / 500, together
with connected coverage, quality and altitude cost (not battery expenditure). Seeds will be
fresh and specified before accepting a batch. Width/rate/pooling sweeps are not planned.
Use wsl_4070 first with actual-node admission; proposed CPU FP32/four threads follows the
existing comparison. New-arm wall time is unknown; old measured times are only context.
Any alternative recommendation must count full fits, training steps and important evaluation
or nested work. A small interface/gradient correctness check is useful, but no positive toy
or prerequisite learnability fit is required. Later confirmation would be a separate fixed
claim and 3-5 fresh independent training seeds per arm, not a relabeling of this exploration.

Primary-source bridge (known operations, not evidence of HMASD benefit):

- Tiny-Attention, EMNLP 2022, section 2.1 and Appendix A: a trainable small cross-position
  attention adapter inside a frozen pretrained LM is a known operation. Our jointly trained
  MARL actor, latent z and changing teammates are a different setting. Its language-task
  gains do not predict our return. https://aclanthology.org/2022.emnlp-main.444/
- Set Transformer, ICML 2019, section 3.2 equation 11, Table 1 and Table 4: learned-seed
  attention pooling is known; ordinary max pooling is better on its max-regression example,
  and ordinary pooling can outperform PMA in a point-cloud setting. Its seed is not our
  runtime held skill; conditioning it is our proposed bridge. https://proceedings.mlr.press/v97/lee19d.html
- Deep Sets, NeurIPS 2017, section 3.1: shared element transforms with ordinary invariant
  aggregation give the simpler architecture family. Supplying our legal ego/z to that transform
  is an application, not a theorem established by the paper about MARL learning.
  https://papers.neurips.cc/paper_files/paper/2017/hash/f22e4747da1aa27e363d86d40ff442fe-Abstract.html

Local primary passages and corresponding MyLib readings were checked while authoring. They
are not assumed accessible to you; use the official sources if a consequential analogy needs
verification. No claimed unpublished novelty, model agreement or literature analogy counts as
new empirical replication. Optional RPG/PORTAL references in the design are not required to
answer this question; their missing external appendices remain missing.

Context (paths below resolve at the actual full source_sha supplied in the transport message,
unless an explicit different scientific input SHA is given):

- Governance: `docs/project/OPERATING_CONSTITUTION.md`, sections 1-5, 7-8, for exploration,
  independent DM authority, fits as cost, advisory Pro, no extra approval gates and scientific
  minimums; current owner instruction above governs this newly selected direction.
- Method: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Explore an idea, Update the working
  explanation, Simple-model and literature bridges, Comparators and MARL information,
  Statistics, Cost and exposure and Pro. Use these to distinguish a useful finite-learning
  experiment from a mechanism proof or mandatory diagnostic programme.
- Engineering feasibility only: `.agents/skills/hmasd-research-engineering/SKILL.md`, its
  L0/check/review/execution method; `hmasd/networks.py` R_Actor.forward/evaluate_actions,
  `hmasd/agent.py` HMASDAgent.step and update_discoverer_from_rollout, `configs/config_1.py`,
  `scripts/run_fsd_baseline_interruption_b01.py` collect_training/evaluate_panel, and
  `envs/pettingzoo/uav_env.py` step/_get_observation_vectorized for disputed interface facts.
- Shared background: `docs/research/RESEARCH.md`, topics 3/4/5/6 and this direction's row.
  The current distinction between actual action law, finite learning and inference units
  actively motivates the common bounded-action contract and ordinary P/O controls; it is
  revisable evidence, not an instruction to agree with a prior scientific conclusion.
- Standing: this notebook's owner-activation entry; `docs/research/designs/LITERATURE_RESEARCH_PLAN_20260922.md`
  plan 3 for the inherited proposal, which is not an already accepted experiment.
- Contrary evidence and prior Pro: `docs/research/candidates/local_observation_encoding/NOTES.md`,
  the B01 complete adverse package observation, `Pro question 2026-09-22 dense-recipe-stop`
  and DM archive decision; both `runs/local_observation_encoding/b01_original_s92101/summary.json`
  and `runs/local_observation_encoding/b01_dense_s92101/summary.json` for original outputs.
  The old experimental encoder/runner live at scientific input
  `efe7d61e82b2c0aed7a634bbb2e22d7cc47430a3`, paths
  `experiments/candidates/local_observation_encoding/encoder.py` and `b01.py`, not on current
  main. Read these only if needed to judge whether this is actually a different comparison;
  do not apply the new action contract retrospectively to old results.
- Action-law evidence: `docs/research/candidates/agent_count_generalization/NOTES.md`,
  `2026-09-22 — B02 complete: bounded deployment preserves the package advantage`, and
  `runs/agent_count_generalization/s1_action_law_b02_probe/summary.json` if raw support is needed.
  That direction retains its own producer/operation ownership; this consultation is not its review.

Constraints: advise only; no training or experiment launch. Read the question and reasoning
sources at the immutable source_sha. Write only into the currently empty `### Answer` below,
on branch `codex/goal-conditioned-aggregation-20260922`, at this exact NOTES path. Fetch the
latest target file before editing and use its actual blob SHA; preserve the question and every
other byte. Stop on overlapping edits. On successful write, report the actual commit; if
GitHub writeback fails, return the complete substantive answer in chat, not merely a receipt,
SHA, link or status. Private Jev account names and conversation URLs must not be written here.

Return: a focused scientific assessment in Chinese: what the existing evidence strengthens,
weakens or leaves untouched; the strongest objection to the proposed intervention and what
observation would discriminate it; the smallest useful next comparison and its fit/non-fit
cost, or why no worthwhile comparison is currently selected. Explain what each plausible
result would change without treating no significant difference as equivalence. Correct source
bridges or interface errors where consequential; state material unread gaps. A simple-model
argument is optional if it clarifies the disputed compression step, and must name omitted
joint-learning, decentralized-information and latent-skill coupling. Return
`MATERIAL_DISSENT: yes/no` with the substantive reason. No prescribed candidate count,
new architecture, exhaustive prerequisite analysis or approval requirement is requested.

### Answer
